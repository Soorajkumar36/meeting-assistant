from abc import ABC, abstractmethod
from typing import List

from app.transcription.transcript_schema import SpeakerSegment
from app.summarization.llm_client import LLMClient


class Redactor(ABC):
    """
    Abstract interface for PII redaction.
    """

    @abstractmethod
    def redact_segments(self, segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        """
        Accepts diarized speaker segments and returns redacted segments.
        """
        raise NotImplementedError


class LLMRedactor(Redactor):
    """
    Context-aware PII redaction using an LLM.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def redact_segments(self, segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        redacted_segments: List[SpeakerSegment] = []

        for segment in segments:
            redacted_text = self._redact_text(segment.text)

            redacted_segments.append(
                SpeakerSegment(
                    speaker_id=segment.speaker_id,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    text=redacted_text,
                    confidence=segment.confidence,
                )
            )

        return redacted_segments

    def _redact_text(self, text: str) -> str:
        prompt = f"""
        You are a privacy-preserving redaction system.

        Task:
        - Remove or anonymize ALL personally identifiable information (PII).
        - This includes:
        - Person names
        - Email addresses
        - Phone numbers
        - Organization names
        - Locations
        - IDs or account numbers
        - Preserve the sentence meaning.
        - Replace sensitive entities with placeholders.

        Placeholders to use:
        [PERSON], [EMAIL], [PHONE], [ORG], [LOCATION], [ID]

        Text:
        {text}

        Return ONLY the redacted text.
        """

        response = self.llm.generate(prompt)
        return response.strip()
