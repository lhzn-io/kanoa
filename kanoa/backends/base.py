from abc import ABC, abstractmethod
from typing import Any, Optional

import matplotlib.pyplot as plt

from ..converters.dataframe import data_to_text
from ..converters.figure import fig_to_base64
from ..core.types import InterpretationResult


class BaseBackend(ABC):
    """Abstract base class for AI backends."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = 3000,
        enable_caching: bool = True,
        **kwargs: Any,
    ):
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.enable_caching = enable_caching
        self.call_count = 0

    @abstractmethod
    def interpret(
        self,
        fig: Optional[plt.Figure],
        data: Optional[Any],
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
        **kwargs: Any,
    ) -> InterpretationResult:
        """
        Interpret analytical output.

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build prompt for the backend."""
        pass

    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64."""
        return fig_to_base64(fig)

    def _data_to_text(self, data: Any) -> str:
        """Convert data to text representation."""
        return data_to_text(data)
