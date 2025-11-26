from typing import Any, Optional

from ..core.types import InterpretationResult
from .base import BaseBackend


class AzureOpenAIBackend(BaseBackend):
    """
    Stub implementation for Azure OpenAI backend.

    This class serves as documentation for future implementation of Azure OpenAI
    support. It defines the expected interface and pricing structure but does not
    implement actual API calls.

    Configuration:
    - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
    - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
      (e.g., https://<resource>.openai.azure.com/)
    - AZURE_OPENAI_API_VERSION: API version (default: 2024-10-01-preview)

    Supported Models (GPT-5.1 Family):
    - gpt-5.1 (Standard Global)
    - gpt-5.1-chat
    - gpt-5.1-codex
    - gpt-5.1-codex-mini

    Community contributions to implement the actual API logic are welcome!
    """

    # Pricing (per 1M tokens) - Azure OpenAI Standard Global (Nov 2025)
    PRICING = {
        "gpt-5.1": {"input": 1.25, "output": 10.00},
        "gpt-5.1-chat": {"input": 1.25, "output": 10.00},
        "gpt-5.1-codex": {"input": 1.25, "output": 10.00},
        "gpt-5.1-codex-mini": {"input": 0.25, "output": 2.00},
        # Cached input is typically ~10% of base input price
        "cached_factor": 0.1,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5.1",
        max_tokens: int = 4000,
        enable_caching: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Azure OpenAI backend stub.

        Args:
            api_key: Azure OpenAI API key
            model: Model deployment name
            max_tokens: Maximum tokens to generate
            enable_caching: Whether to enable prompt caching
            **kwargs: Additional arguments
        """
        super().__init__(api_key, max_tokens, enable_caching)
        raise NotImplementedError(
            "Azure OpenAI backend is currently a stub. "
            "We welcome community contributions to implement this backend! "
            "See documentation for implementation details."
        )

    def interpret(
        self,
        fig: Optional[Any],
        data: Optional[Any],
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
        **kwargs: Any,
    ) -> InterpretationResult:
        """
        Interpret data using Azure OpenAI (Stub).

        Raises:
            NotImplementedError: Always raised as this is a stub.
        """
        raise NotImplementedError("Azure OpenAI backend is not yet implemented.")
