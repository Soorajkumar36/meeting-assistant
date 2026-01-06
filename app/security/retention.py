import time
from pathlib import Path
from typing import Iterable


def cleanup_directory(
    directory: str,
    max_age_days: int,
    allowed_extensions: Iterable[str] | None = None,
):
    """
    Deletes files older than max_age_days from a directory.

    Parameters:
    - directory: path to clean
    - max_age_days: retention window in days
    - allowed_extensions: optional whitelist (e.g. [".wav", ".json"])
    """

    base_path = Path(directory)

    if not base_path.exists() or not base_path.is_dir():
        return

    now = time.time()
    cutoff_time = now - (max_age_days * 86400)

    for file_path in base_path.iterdir():
        if not file_path.is_file():
            continue

        if allowed_extensions and file_path.suffix not in allowed_extensions:
            continue

        try:
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
        except Exception:
            # Never raise on retention cleanup
            pass


def enforce_retention_policy(
    raw_audio_dir: str,
    transcript_dir: str,
    summary_dir: str,
    retention_days: int,
):
    """
    Applies retention policy across all stored artifacts.
    """

    cleanup_directory(
        directory=raw_audio_dir,
        max_age_days=retention_days,
        allowed_extensions=[".wav", ".mp3", ".m4a", ".flac"],
    )

    cleanup_directory(
        directory=transcript_dir,
        max_age_days=retention_days,
        allowed_extensions=[".json"],
    )

    cleanup_directory(
        directory=summary_dir,
        max_age_days=retention_days,
        allowed_extensions=[".json", ".txt"],
    )
