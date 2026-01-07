from typing import Dict, List, Optional

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

    def __init__(self, llm: LLMClient, max_chunk_chars: Optional[int] = 3000):
        self.llm = llm
        # approximate max characters per chunk to keep prompts within model context
        self.max_chunk_chars = max_chunk_chars or 3000

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of roughly `self.max_chunk_chars` characters.

        This is a simple, tokenizer-agnostic heuristic that splits on word
        boundaries to avoid breaking words in half.
        """
        if not text:
            return []

        words = text.split()
        chunks: List[str] = []
        cur: List[str] = []
        cur_len = 0

        for w in words:
            w_len = len(w) + 1  # account for space
            if cur_len + w_len > self.max_chunk_chars and cur:
                chunks.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
            else:
                cur.append(w)
                cur_len += w_len

        if cur:
            chunks.append(" ".join(cur))

        return chunks

    def summarize_speakers(self, speaker_texts: Dict[str, str]) -> List[SpeakerSummary]:
        summaries: List[SpeakerSummary] = []

        for speaker_id, text in speaker_texts.items():
            # If a speaker's text is very long, chunk and summarize hierarchically.
            chunks = self._chunk_text(text)

            if not chunks:
                response = ""
            elif len(chunks) == 1:
                prompt = SPEAKER_SUMMARY_PROMPT.format(text=chunks[0])
                response = self.llm.generate(prompt)
            else:
                # summarize each chunk
                chunk_summaries: List[str] = []
                for c in chunks:
                    p = SPEAKER_SUMMARY_PROMPT.format(text=c)
                    chunk_summaries.append(self.llm.generate(p))

                # combine chunk summaries and produce a final summary
                combined = "\n\n".join(chunk_summaries)
                final_prompt = SPEAKER_SUMMARY_PROMPT.format(text=combined)
                response = self.llm.generate(final_prompt)

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

        chunks = self._chunk_text(full_text)

        if not chunks:
            response = ""
        elif len(chunks) == 1:
            prompt = MEETING_SUMMARY_PROMPT.format(text=chunks[0])
            response = self.llm.generate(prompt)
        else:
            chunk_summaries: List[str] = []
            for c in chunks:
                p = MEETING_SUMMARY_PROMPT.format(text=c)
                chunk_summaries.append(self.llm.generate(p))

            combined = "\n\n".join(chunk_summaries)
            final_prompt = MEETING_SUMMARY_PROMPT.format(text=combined)
            response = self.llm.generate(final_prompt)

        return MeetingSummary(
            meeting_id=transcript.meeting_id,
            overview=response,
            key_topics=[],
            action_items=[],
        )
