from abc import ABC, abstractmethod

from app.transcription.transcript_schema import Transcript


class ASRInterface(ABC):
    """
    Contract for speech-to-text + diarization.
    """

    @abstractmethod
    def transcribe(self, audio_path: str, meeting_id: str) -> Transcript:
        pass
