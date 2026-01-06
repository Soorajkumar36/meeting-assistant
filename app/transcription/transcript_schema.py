from dataclasses import dataclass
from typing import List, Optional


# -----------------------------
# Audio metadata
# -----------------------------
@dataclass(frozen=True)
class AudioMetadata:
    meeting_id: str
    source: str  # google_meet | teams | zoom | system
    sample_rate: int
    channels: int
    duration_seconds: float
    recorded_at: str  # ISO timestamp
    file_hash: str  # integrity check
    encryption: Optional[str] = None


# -----------------------------
# Core diarized speech unit
# -----------------------------
@dataclass(frozen=True)
class SpeakerSegment:
    speaker_id: str  # SPEAKER_1, SPEAKER_2
    start_time: float  # seconds
    end_time: float  # seconds
    text: str
    confidence: float  # 0.0 – 1.0


# -----------------------------
# Structured transcript
# -----------------------------
@dataclass(frozen=True)
class Transcript:
    meeting_id: str
    language: str
    segments: List[SpeakerSegment]


# -----------------------------
# Speaker identity mapping
# -----------------------------
@dataclass(frozen=True)
class SpeakerMapping:
    speaker_id: str  # SPEAKER_1
    display_name: Optional[str]  # Alice, Bob


# -----------------------------
# Per-speaker LLM output
# -----------------------------
@dataclass(frozen=True)
class SpeakerSummary:
    speaker_id: str
    summary: str
    action_items: List[str]
    decisions: List[str]


# -----------------------------
# Meeting-level LLM output
# -----------------------------
@dataclass(frozen=True)
class MeetingSummary:
    meeting_id: str
    overview: str
    key_topics: List[str]
    action_items: List[str]
