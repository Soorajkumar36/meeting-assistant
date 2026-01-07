from dataclasses import asdict

from app.config import load_config

from app.transcription.diarization import PyannoteCloudASR
from app.transcription.transcript_schema import Transcript

from app.processing.speaker_grouping import group_by_speaker
from app.processing.cleaner import build_speaker_text

from app.security.redaction import LLMRedactor

from app.summarization.summarizer import Summarizer
from app.summarization.llm_client import (
    DummyLLMClient,
    OllamaCloudClient,
)

from app.storage.local_store import LocalJSONStorage
from datetime import datetime
import uuid


# --------------------------------------------------
# LLM Factory
# --------------------------------------------------
def build_llm_client(config):
    if config.llm.provider == "ollama":
        return OllamaCloudClient(
            model=config.llm.model,
        )
    return DummyLLMClient()


# --------------------------------------------------
# Shared pipeline logic
# --------------------------------------------------
def _format_transcript_text(transcript: Transcript) -> str:
    lines = []
    for seg in transcript.segments:
        timestamp = f"{int(seg.start_time // 60)}:{int(seg.start_time % 60):02d}"
        lines.append(f"{seg.speaker_id} ({timestamp}): {seg.text}")
    return "\n".join(lines)


def _process_transcript(transcript: Transcript, meeting_id: str):
    config = load_config()
    storage = LocalJSONStorage(base_dir="data")
    llm_client = build_llm_client(config)

    # Redaction
    redactor = LLMRedactor(llm=llm_client)
    redacted_segments = redactor.redact_segments(transcript.segments)

    transcript = Transcript(
        meeting_id=meeting_id,
        language=transcript.language,
        segments=redacted_segments,
    )

    storage.save(
        key=f"transcripts/{meeting_id}",
        data=asdict(transcript),
    )

    grouped = group_by_speaker(transcript)
    speaker_texts = {
        speaker_id: build_speaker_text(segments)
        for speaker_id, segments in grouped.items()
    }

    summarizer = Summarizer(llm=llm_client, max_chunk_chars=4000)
    speaker_summaries = summarizer.summarize_speakers(speaker_texts)
    meeting_summary = summarizer.summarize_meeting(transcript)

    storage.save(
        key=f"summaries/meeting/{meeting_id}",
        data=asdict(meeting_summary),
    )

    for summary in speaker_summaries:
        storage.save(
            key=f"summaries/speaker/{meeting_id}/{summary.speaker_id}",
            data=asdict(summary),
        )

    transcript_text = _format_transcript_text(transcript)

    return meeting_summary, speaker_summaries, transcript_text


# --------------------------------------------------
# Pipeline entry: uploaded audio URL
# --------------------------------------------------
def run_pipeline_with_audio_url(
    audio_url: str,
    num_speakers: int,
):
    config = load_config()

    asr = PyannoteCloudASR(
        api_key=config.asr.pyannote_api_key,
        language=config.asr.language,
        num_speakers=num_speakers,
    )

    # generate a unique, traceable meeting_id (UTC timestamp + short UUID)

    now = datetime.utcnow().replace(microsecond=0).isoformat().replace(":", "-")
    meeting_id = f"meeting-{now}-{uuid.uuid4().hex[:8]}"
    transcript = asr.transcribe(audio_url, meeting_id)

    return _process_transcript(transcript, meeting_id)


# --------------------------------------------------
# CLI entry (optional)
# --------------------------------------------------
if __name__ == "__main__":
    print("Use API endpoint /upload-audio to run pipeline.")
