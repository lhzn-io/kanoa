import os
from typing import Any, Dict, List, Optional, cast

import matplotlib.pyplot as plt
from anthropic import Anthropic

from ..core.types import InterpretationResult, UsageInfo
from .base import BaseBackend


class ClaudeBackend(BaseBackend):
    """
    Anthropic Claude backend implementation.

    Supports:
    - Claude 4.5 Sonnet (default)
    - Claude 4.5 Opus
    - Vision capabilities (interprets figures)
    - Text knowledge base integration
    """

    PRICING = {
        # Claude 4.5 models (latest, Nov 2025)
        "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
        "claude-opus-4-5-20251101": {"input": 5.00, "output": 25.00},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 3000,
        enable_caching: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, max_tokens, enable_caching)
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model

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
        """Interpret using Claude."""
        self.call_count += 1

        messages: List[Dict[str, Any]] = []
        content_blocks: List[Dict[str, Any]] = []

        # Add figure (Vision)
        if fig is not None:
            img_base64 = self._fig_to_base64(fig)
            content_blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64,
                    },
                }
            )

        # Add data
        if data is not None:
            data_text = self._data_to_text(data)
            content_blocks.append(
                {"type": "text", "text": f"Data to analyze:\n```\n{data_text}\n```"}
            )

        # Add prompt
        prompt = self._build_prompt(context, focus, kb_context, custom_prompt)
        content_blocks.append({"type": "text", "text": prompt})

        messages.append({"role": "user", "content": content_blocks})

        try:
            response = cast(Any, self.client.messages.create)(
                model=self.model, max_tokens=self.max_tokens, messages=messages
            )

            # Extract text from first content block (handle union type)
            first_block = response.content[0]
            interpretation = (
                first_block.text if hasattr(first_block, "text") else str(first_block)
            )
            usage = self._calculate_usage(response.usage)

            return InterpretationResult(
                text=interpretation,
                backend="claude",
                usage=usage,
                metadata={"model": self.model},
            )

        except Exception as e:
            return InterpretationResult(
                text=f"❌ **Error**: {str(e)}", backend="claude", usage=None
            )

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
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
        input_tokens = usage_data.input_tokens
        output_tokens = usage_data.output_tokens

        pricing = self.PRICING.get(self.model, {"input": 3.00, "output": 15.00})

        cost = (input_tokens / 1_000_000 * pricing["input"]) + (
            output_tokens / 1_000_000 * pricing["output"]
        )

        return UsageInfo(
            input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
        )
