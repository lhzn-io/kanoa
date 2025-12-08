from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import matplotlib.pyplot as plt

from ..converters.dataframe import data_to_text
from ..converters.figure import fig_to_base64
from ..core.types import InterpretationResult
from ..utils.prompts import PromptTemplates

if TYPE_CHECKING:
    from ..knowledge_base.manager import KnowledgeBaseManager


class BaseBackend(ABC):
    """Abstract base class for AI backends."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = 3000,
        enable_caching: bool = True,
        prompt_templates: Optional[PromptTemplates] = None,
        **kwargs: Any,
    ):
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.enable_caching = enable_caching
        self.call_count = 0

        # Cost tracking state (moved from Interpreter to allow sharing)
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}

        # Prompt templates
        self.prompt_templates = prompt_templates or PromptTemplates()

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

    def _build_prompt_from_templates(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """
        Build prompt using centralized templates.

        This is a helper method that backends can use to build prompts
        from the centralized PromptTemplates.

        Args:
            context: User-provided context description
            focus: Specific focus areas for analysis
            kb_context: Knowledge base content
            custom_prompt: Full custom prompt (takes precedence)

        Returns:
            Complete prompt string
        """
        if custom_prompt:
            return custom_prompt

        parts = []

        # Build system instruction with KB context
        if kb_context:
            system_template = self.prompt_templates.get_system_prompt(self.backend_name)
            parts.append(system_template.format(kb_context=kb_context))

        # Build user prompt with context and focus
        user_template = self.prompt_templates.get_user_prompt(self.backend_name)

        # Build context block
        context_block = f"\n**Context**: {context}" if context else ""
        focus_block = f"\n**Analysis Focus**: {focus}" if focus else ""

        # For backward compatibility, we don't use string formatting if the template
        # doesn't have placeholders. Instead, we append context/focus separately.
        if "{context_block}" in user_template and "{focus_block}" in user_template:
            user_prompt = user_template.format(
                context_block=context_block, focus_block=focus_block
            )
        else:
            # Fallback for templates without placeholders
            user_prompt = user_template
            if context_block:
                user_prompt = user_prompt.replace(
                    "Analyze this analytical output",
                    f"Analyze this analytical output{context_block}",
                )
            if focus_block:
                user_prompt = user_prompt.replace(
                    "technical interpretation.",
                    f"technical interpretation.{focus_block}",
                )

        parts.append(user_prompt)

        return "\n".join(parts)

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
