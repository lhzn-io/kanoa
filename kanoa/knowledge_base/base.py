from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union


class BaseKnowledgeBase(ABC):
    """Abstract base class for knowledge bases."""

    def __init__(self, kb_path: Optional[Union[str, Path]] = None):
        self.kb_path = Path(kb_path) if kb_path else None

    @abstractmethod
    def get_context(self) -> str:
        """Get knowledge base context as string."""

    @abstractmethod
    def reload(self) -> None:
        """Reload knowledge base content."""
