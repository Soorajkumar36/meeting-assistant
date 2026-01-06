import time
import requests
from typing import List, Optional

from app.transcription.asr import ASRInterface
from app.transcription.transcript_schema import Transcript, SpeakerSegment


class PyannoteCloudASR(ASRInterface):
    """
    ASR + Speaker diarization using pyannote Cloud API.
    """

    DIARIZE_URL = "https://api.pyannote.ai/v1/diarize"
    JOB_URL = "https://api.pyannote.ai/v1/jobs"

    def __init__(
        self,
        api_key: str,
        language: str = "en",
        poll_interval: int = 5,
        num_speakers: Optional[int] = None,
    ):
        if not api_key:
            raise RuntimeError("PYANNOTE_API_KEY is not set")

        self.api_key = api_key
        self.language = language
        self.poll_interval = poll_interval
        self.num_speakers = num_speakers

    def transcribe(self, audio_path: str, meeting_id: str) -> Transcript:
        job_id = self._submit_job(audio_path)
        output = self._wait_for_job(job_id)

        turns = output["turnLevelTranscription"]

        segments: List[SpeakerSegment] = []

        for turn in turns:
            segments.append(
                SpeakerSegment(
                    speaker_id=turn["speaker"],
                    start_time=turn["start"],
                    end_time=turn["end"],
                    text=turn["text"].strip(),
                    confidence=1.0,
                )
            )

        return Transcript(
            meeting_id=meeting_id,
            language=self.language,
            segments=segments,
        )

    def _submit_job(self, audio_url: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "url": audio_url,
            "transcription": True,
        }

        if self.num_speakers is not None:
            payload["numSpeakers"] = self.num_speakers

        response = requests.post(
            self.DIARIZE_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        return response.json()["jobId"]

    def _wait_for_job(self, job_id: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        while True:
            response = requests.get(
                f"{self.JOB_URL}/{job_id}",
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            status = data["status"]

            if status == "succeeded":
                return data["output"]

            if status in ("failed", "canceled"):
                raise RuntimeError(f"Pyannote job {status}")

            time.sleep(self.poll_interval)
