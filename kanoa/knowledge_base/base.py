"""
Base knowledge base class.
"""

from abc import ABC, abstractmethod


class BaseKnowledgeBase(ABC):
    """Abstract base class for knowledge bases."""

    @abstractmethod
    def get_context(self) -> str:
        pass
