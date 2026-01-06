import json
from pathlib import Path
from typing import Any

from app.storage.interfaces import StorageInterface


class LocalJSONStorage(StorageInterface):
    """
    Local filesystem storage for JSON-serializable data.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: Any) -> None:
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, key: str) -> Any:
        path = self._resolve_path(key)

        if not path.exists():
            raise FileNotFoundError(f"No data found for key: {key}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_path(self, key: str) -> Path:
        """
        Converts logical key to file path.
        Example key: transcripts/meeting_id
        """
        return self.base_dir / f"{key}.json"
