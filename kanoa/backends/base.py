"""
Base backend class.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
import matplotlib.pyplot as plt
from ..core.types import InterpretationResult

class BaseBackend(ABC):
    """Abstract base class for AI backends."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
    
    @abstractmethod
    def interpret(self, fig: Optional[plt.Figure], data: Optional[Any], **kwargs) -> InterpretationResult:
        pass
