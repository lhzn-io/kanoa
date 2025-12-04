from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import matplotlib.pyplot as plt

from ..converters.dataframe import data_to_text
from ..converters.figure import fig_to_base64
from ..core.types import InterpretationResult

if TYPE_CHECKING:
    from ..knowledge_base.manager import KnowledgeBaseManager


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

        # Cost tracking state (moved from Interpreter to allow sharing)
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}

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

    @abstractmethod
    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build prompt for the backend."""

    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64."""
        return fig_to_base64(fig)

    def _data_to_text(self, data: Any) -> str:
        """Convert data to text representation."""
        return data_to_text(data)

    def get_cost_summary(self) -> dict[str, Any]:
        """Get summary of token usage and costs."""
        return {
            "backend": self.backend_name,  # Abstract property
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "avg_cost_per_call": self.total_cost / max(self.call_count, 1),
        }

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Name of the backend."""

    def check_kb_cost(self) -> Any:
        """
        Check the cost/token count of the current knowledge base.

        Returns:
            TokenCheckResult or None if not supported.
        """
        return None

    def encode_kb(self, kb_manager: "KnowledgeBaseManager") -> Optional[str]:
        """
        Encode knowledge base content for this backend.

        Default implementation returns text content only.
        Backends can override to support PDFs, images, etc.

        Args:
            kb_manager: KnowledgeBaseManager instance

        Returns:
            Text context string for the prompt, or None if no content
        """
        return kb_manager.get_text_content() or None
