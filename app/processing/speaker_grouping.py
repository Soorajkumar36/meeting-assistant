from collections import defaultdict
from typing import Dict, List

from app.transcription.transcript_schema import Transcript, SpeakerSegment


def group_by_speaker(transcript: Transcript) -> Dict[str, List[SpeakerSegment]]:
    """
    Groups transcript segments by speaker_id.
    """
    grouped: Dict[str, List[SpeakerSegment]] = defaultdict(list)

    for segment in transcript.segments:
        grouped[segment.speaker_id].append(segment)

    return dict(grouped)
