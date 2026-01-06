import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load .env file and override any existing environment variables
load_dotenv(override=True)


def _get_env(key: str, default: Optional[str] = None) -> str:
    return os.getenv(key, default)


def _get_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    return int(value)


def _get_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


# --------------------
# Audio config
# --------------------
@dataclass(frozen=True)
class AudioConfig:
    duration_seconds: int
    sample_rate: int
    channels: int
    storage_path: str


# --------------------
# ASR config
# --------------------
@dataclass(frozen=True)
class ASRConfig:
    model_name: str
    language: str
    device: str
    pyannote_api_key: str


# --------------------
# LLM config
# --------------------
@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str


# --------------------
# Security config
# --------------------
@dataclass(frozen=True)
class SecurityConfig:
    enable_redaction: bool
    retention_days: int


# --------------------
# App config (root)
# --------------------
@dataclass(frozen=True)
class AppConfig:
    audio: AudioConfig
    asr: ASRConfig
    llm: LLMConfig
    security: SecurityConfig


def load_config() -> AppConfig:
    """
    Loads application configuration from environment variables.
    """

    audio = AudioConfig(
        duration_seconds=_get_int("AUDIO_DURATION_SECONDS", 60),
        sample_rate=_get_int("AUDIO_SAMPLE_RATE", 16000),
        channels=_get_int("AUDIO_CHANNELS", 1),
        storage_path=_get_env("AUDIO_STORAGE_PATH", "data/raw_audio"),
    )

    asr = ASRConfig(
        model_name=_get_env("ASR_MODEL_NAME", "large-v3"),
        language=_get_env("ASR_LANGUAGE", "en"),
        device=_get_env("ASR_DEVICE", "auto"),
        pyannote_api_key=_get_env("PYANNOTE_API_KEY", ""),
    )

    llm = LLMConfig(
        provider=_get_env("LLM_PROVIDER", "dummy"),
        model=_get_env("LLM_MODEL", "llama3"),
    )

    security = SecurityConfig(
        enable_redaction=_get_bool("ENABLE_REDACTION", True),
        retention_days=_get_int("DATA_RETENTION_DAYS", 7),
    )

    return AppConfig(
        audio=audio,
        asr=asr,
        llm=llm,
        security=security,
    )
