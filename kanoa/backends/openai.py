import os
from typing import Any, Optional, cast

import matplotlib.pyplot as plt

from ..core.types import InterpretationResult, UsageInfo
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

    def __init__(
        self,
        api_base: Optional[str] = None,
        model: str = "gpt-4-turbo",
        api_key: Optional[str] = None,
        max_tokens: int = 3000,
        temperature: float = 0.7,
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
            **kwargs: Additional arguments
        """
        super().__init__(api_key, max_tokens, **kwargs)

        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "OpenAI backend requires openai package. "
                "Install with: pip install -e .[openai]"
            ) from e

        self.api_base = api_base
        self.model = model
        self.temperature = temperature

        # Initialize OpenAI client
        # If api_base is None, OpenAI client defaults to official API
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", "EMPTY"),
            base_url=api_base,
        )

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

        # Add data if provided
        if data is not None:
            data_text = self._data_to_text(data)
            prompt = f"Data to analyze:\n```\n{data_text}\n```\n\n{prompt}"

        # Add prompt text
        content.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": content})

        try:
            from openai.types.chat import ChatCompletionMessageParam

            response = self.client.chat.completions.create(
                model=self.model,
                messages=cast(list[ChatCompletionMessageParam], messages),
                max_tokens=self.max_tokens,
                temperature=kwargs.get("temperature", self.temperature),
            )

            # Extract response
            interpretation = response.choices[0].message.content or ""

            # Calculate usage
            usage = self._calculate_usage(response.usage) if response.usage else None

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
            return InterpretationResult(
                text=f"❌ **Error**: {str(e)}", backend="openai", usage=None
            )

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build vLLM-optimized prompt."""
        if custom_prompt:
            return custom_prompt

        parts = []

        if kb_context:
            parts.append(
                f"""You are an expert data analyst with access to \
domain-specific knowledge.

# Knowledge Base

{kb_context}

Use this information to provide informed, technically accurate \
interpretations.
"""
            )

        parts.append(
            "Analyze this analytical output and provide a technical interpretation."
        )

        if context:
            parts.append(f"\n**Context**: {context}")

        if focus:
            parts.append(f"\n**Analysis Focus**: {focus}")

        parts.append(
            """

Provide:
1. **Summary**: What the output shows
2. **Key Observations**: Notable patterns and trends
3. **Technical Interpretation**: Insights based on domain knowledge
4. **Potential Issues**: Data quality concerns or anomalies
5. **Recommendations**: Suggestions for further analysis

Use markdown formatting. Be concise but technically precise.
"""
        )
        return "\n".join(parts)

    def _calculate_usage(self, usage_data: Any) -> UsageInfo:
        """
        Calculate token usage and estimated cost.

        Note: Cost estimation for local models is approximate and based on
        computational cost rather than API pricing.
        """
        input_tokens = usage_data.prompt_tokens
        output_tokens = usage_data.completion_tokens

        # For local models, we estimate cost based on token count
        # This is a rough approximation: $0.10 per 1M tokens (both input/output)
        # Users can override this by tracking their own infrastructure costs
        cost_per_million = 0.10
        cost = ((input_tokens + output_tokens) / 1_000_000) * cost_per_million

        return UsageInfo(
            input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
        )
