import re
from typing import List

from app.transcription.transcript_schema import SpeakerSegment


FILLER_WORDS = ["uh", "um", "you know", "like", "ah"]


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    for filler in FILLER_WORDS:
        text = re.sub(rf"\b{filler}\b", "", text)

    return text.strip()


def build_speaker_text(segments: List[SpeakerSegment]) -> str:
    """
    Combines all segments for a speaker into a single clean text block.
    """
    texts = []
    for seg in segments:
        if seg.text.strip():
            texts.append(clean_text(seg.text))

    return " ".join(texts)
