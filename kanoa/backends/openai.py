import os
from typing import Any, Optional

import matplotlib.pyplot as plt

from ..core.types import InterpretationResult, UsageInfo
from ..pricing import USER_CONFIG_PATH, get_model_pricing
from ..utils.logging import ilog_debug, ilog_info, ilog_warning
from .base import BaseBackend


class OpenAIBackend(BaseBackend):
    """
    OpenAI-compatible backend implementation.

    This backend connects to any OpenAI-compatible API endpoint, including:
    - OpenAI (GPT-4, GPT-3.5)
    - vLLM (Gemma 3, Molmo, Llama 3)
    - Azure OpenAI (via base_url)
    - LocalAI / Ollama

    Features:
    - Generic OpenAI-compatible interface
    - Configurable endpoint and model
    - Text and Vision interpretation (if model supports it)
    - Cost tracking based on token usage

    Example:
        >>> # Connect to local vLLM
        >>> backend = OpenAIBackend(
        ...     api_base="http://localhost:8000/v1",
        ...     model="google/gemma-3-12b-it"
        ... )

        >>> # Connect to OpenAI
        >>> backend = OpenAIBackend(
        ...     api_key="sk-...",
        ...     model="gpt-4-turbo"
        ... )
    """

    @property
    def backend_name(self) -> str:
        """Return the backend name."""
        return "openai"

    def __init__(
        self,
        api_base: Optional[str] = None,
        model: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        max_tokens: int = 3000,
        temperature: float = 0.7,
        verbose: int = 0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize OpenAI backend.

        Args:
            api_base: Base URL for API (optional, defaults to OpenAI's)
            model: Model name to use
            api_key: API key (defaults to OPENAI_API_KEY env var)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            verbose: Logging verbosity level (0=silent, 1=info, 2=debug)
            **kwargs: Additional arguments
        """
        super().__init__(api_key, max_tokens, **kwargs)

        from openai import OpenAI

        self.api_base = api_base
        self.model = model
        self.temperature = temperature
        self.verbose = verbose

        # Initialize OpenAI client
        # If api_base is None, OpenAI client defaults to official API
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", "EMPTY"),
            base_url=api_base,
        )

        if self.verbose >= 1:
            endpoint = api_base or "api.openai.com"
            ilog_info(f"Initialized with model: {self.model}", title="OpenAI")
            ilog_info(f"Endpoint: {endpoint}", title="OpenAI")

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
        Interpret using OpenAI-compatible model.

        Note: Vision support depends on the underlying model.
        """
        self.call_count += 1

        if self.verbose >= 1:
            ilog_info(f"Calling {self.model} (call #{self.call_count})", title="OpenAI")

        # Build prompt
        prompt = self._build_prompt(context, focus, kb_context, custom_prompt)

        # Prepare messages
        messages: list[dict[str, Any]] = []
        content: list[dict[str, Any]] = []

        # Add figure (Vision)
        if fig is not None:
            img_base64 = self._fig_to_base64(fig)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                }
            )
            if self.verbose >= 2:
                ilog_debug("Attached figure as base64 image", title="OpenAI")

        # Add data if provided
        if data is not None:
            data_text = self._data_to_text(data)
            prompt = f"Data to analyze:\n```\n{data_text}\n```\n\n{prompt}"
            if self.verbose >= 2:
                ilog_debug(f"Attached data ({len(data_text)} chars)", title="OpenAI")

        # Add prompt text
        content.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": content})

        if self.verbose >= 2:
            ilog_debug(f"Prompt length: {len(prompt)} chars", title="Request")
            if kb_context:
                ilog_debug(
                    f"Knowledge base context: {len(kb_context)} chars", title="Request"
                )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=self.max_tokens,
                temperature=kwargs.get("temperature", self.temperature),
            )

            # Extract response
            interpretation = response.choices[0].message.content or ""

            # Calculate usage
            usage = self._calculate_usage(response.usage) if response.usage else None

            if self.verbose >= 1 and usage:
                ilog_info(
                    f"Tokens: {usage.input_tokens} in / {usage.output_tokens} out "
                    f"(${usage.cost:.4f})",
                    title="OpenAI",
                )
            if self.verbose >= 2:
                ilog_debug(
                    f"Response length: {len(interpretation)} chars", title="Response"
                )

            return InterpretationResult(
                text=interpretation,
                backend="openai",
                usage=usage,
                metadata={
                    "model": self.model,
                    "api_base": self.api_base,
                },
            )

        except Exception as e:
            ilog_warning(f"API call failed: {e}", title="OpenAI")
            return InterpretationResult(
                text=f"❌ **Error**: {e!s}", backend="openai", usage=None
            )

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build vLLM-optimized prompt using centralized templates."""
        return self._build_prompt_from_templates(
            context, focus, kb_context, custom_prompt
        )

    def _calculate_usage(self, usage_data: Any) -> UsageInfo:
        """
        Calculate token usage and estimated cost.

        Note: Cost estimation for local models is approximate and based on
        computational cost rather than API pricing.
        """
        input_tokens = usage_data.prompt_tokens
        output_tokens = usage_data.completion_tokens

        # Get pricing for this model
        pricing = get_model_pricing("openai", self.model)

        if pricing:
            input_price = pricing.get("input_price", 0.0)
            output_price = pricing.get("output_price", 0.0)
            cost = (input_tokens / 1_000_000 * input_price) + (
                output_tokens / 1_000_000 * output_price
            )
        else:
            # For local models or unknown models, we assume zero cost
            cost = 0.0

            if not getattr(self, "_has_warned_pricing", False):
                ilog_warning(
                    f"No pricing found for model '{self.model}'. Cost reported as $0.0.\n"
                    f"To enable cost tracking, add pricing to: {USER_CONFIG_PATH}",
                    title="Pricing",
                )
                self._has_warned_pricing = True

        return UsageInfo(
            input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
        )

    def encode_kb(self, kb_manager: Any) -> Optional[str]:
        """
        Encode knowledge base for OpenAI/vLLM backend.

        Strategy:
        - Text: Concatenate into prompt
        - PDFs: Currently text only (conversion can be added)
        - Images: Currently text only (can be added via base64)

        Args:
            kb_manager: KnowledgeBaseManager instance

        Returns:
            Text context string for the prompt
        """
        # Import here to avoid circular dependency
        from ..knowledge_base.manager import KnowledgeBaseManager

        if not isinstance(kb_manager, KnowledgeBaseManager):
            return None

        # Get text content
        text_content = kb_manager.get_text_content()

        # Check for PDFs - warn user for now
        if kb_manager.has_pdfs():
            ilog_warning(
                "PDFs detected in knowledge base. "
                "PDF support for OpenAI/vLLM backends is coming in a future update. "
                "Text files will be used for now.",
                source="kanoa.backends.openai",
            )

        return text_content or None
