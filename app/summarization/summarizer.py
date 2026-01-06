from typing import Dict, List

from app.summarization.llm_client import LLMClient
from app.summarization.prompts import (
    SPEAKER_SUMMARY_PROMPT,
    MEETING_SUMMARY_PROMPT,
)
from app.transcription.transcript_schema import (
    SpeakerSummary,
    MeetingSummary,
    Transcript,
)


class Summarizer:
    """
    Orchestrates meeting and speaker summarization.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def summarize_speakers(self, speaker_texts: Dict[str, str]) -> List[SpeakerSummary]:
        summaries: List[SpeakerSummary] = []

        for speaker_id, text in speaker_texts.items():
            prompt = SPEAKER_SUMMARY_PROMPT.format(text=text)
            response = self.llm.generate(prompt)

            summaries.append(
                SpeakerSummary(
                    speaker_id=speaker_id,
                    summary=response,
                    action_items=[],  # parsed later
                    decisions=[],  # parsed later
                )
            )

        return summaries

    def summarize_meeting(self, transcript: Transcript) -> MeetingSummary:
        full_text = " ".join(seg.text for seg in transcript.segments)

        prompt = MEETING_SUMMARY_PROMPT.format(text=full_text)
        response = self.llm.generate(prompt)

        return MeetingSummary(
            meeting_id=transcript.meeting_id,
            overview=response,
            key_topics=[],
            action_items=[],
        )
