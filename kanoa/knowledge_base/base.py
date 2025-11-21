"""
Base knowledge base class.
"""

from abc import ABC, abstractmethod
from typing import Optional

class BaseKnowledgeBase(ABC):
    """Abstract base class for knowledge bases."""
    
    @abstractmethod
    def get_context(self) -> str:
        pass
