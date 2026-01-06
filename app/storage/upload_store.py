from pathlib import Path
from fastapi import UploadFile
import shutil


class UploadStore:
    """
    Temporarily stores uploaded audio files
    and exposes them via a public URL.
    """

    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile) -> Path:
        file_path = self.base_dir / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return file_path
