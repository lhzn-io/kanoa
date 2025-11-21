"""
Base backend class.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import matplotlib.pyplot as plt

from ..core.types import InterpretationResult


class BaseBackend(ABC):
    """Abstract base class for AI backends."""

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.api_key = api_key

    @abstractmethod
    def interpret(
        self,
        fig: Optional[plt.Figure] = None,
        data: Optional[Any] = None,
        **kwargs: Any,
    ) -> InterpretationResult:
        pass
