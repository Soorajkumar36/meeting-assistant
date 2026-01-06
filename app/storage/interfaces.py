from abc import ABC, abstractmethod
from typing import Any


class StorageInterface(ABC):
    """
    Abstract storage interface.
    """

    @abstractmethod
    def save(self, key: str, data: Any) -> None:
        """
        Persist data using a logical key.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, key: str) -> Any:
        """
        Load data for a given key.
        """
        raise NotImplementedError
