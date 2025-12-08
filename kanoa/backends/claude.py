import os
from typing import Any, Dict, List, Optional, cast

import matplotlib.pyplot as plt
from anthropic import Anthropic

from ..core.token_guard import BaseTokenCounter
from ..core.types import InterpretationResult, UsageInfo
from ..pricing import get_model_pricing
from ..utils.logging import ilog_debug, ilog_info, ilog_warning
from .base import BaseBackend


class ClaudeTokenCounter(BaseTokenCounter):
    """Token counter for Anthropic Claude models."""

    def __init__(
        self,
        client: Any,
        model: str = "claude-sonnet-4-5",
        system: Optional[str] = None,
        verbose: int = 0,
    ):
        """
        Initialize Claude token counter.

        Args:
            client: anthropic.Anthropic instance
            model: Model name for token counting
            system: Optional system prompt (counted separately)
            verbose: Logging verbosity level (0=silent, 1=info, 2=debug)
        """
        self._client = client
        self._model = model
        self._system = system
        self.verbose = verbose

    @property
    def backend_name(self) -> str:
        return "claude"

    @property
    def model(self) -> str:
        return self._model

    def count_tokens(self, contents: Any) -> int:
        """
        Count tokens using Claude API.

        Args:
            contents: Messages to count (list of message dicts)
                Expected format: [{"role": "user", "content": "..."}]

        Returns:
            Token count
        """
        try:
            # Claude expects messages in specific format
            messages = self._normalize_messages(contents)

            kwargs: Dict[str, Any] = {
                "model": self._model,
                "messages": messages,
            }
            if self._system:
                kwargs["system"] = self._system

            result = self._client.messages.count_tokens(**kwargs)
            token_count = int(result.input_tokens)
            if self.verbose >= 2:
                ilog_debug(f"Token count: {token_count}", title="Claude")
            return token_count
        except Exception as e:
            ilog_warning(f"Token counting failed, using estimate: {e}", title="Claude")
            return self.estimate_tokens(contents)

    def _normalize_messages(self, contents: Any) -> List[Dict[str, Any]]:
        """Normalize contents to Claude message format."""
        if isinstance(contents, str):
            return [{"role": "user", "content": contents}]
        if isinstance(contents, list):
            # Already a list of messages
            if contents and isinstance(contents[0], dict) and "role" in contents[0]:
                return contents
            # List of strings - treat as user messages
            return [{"role": "user", "content": str(item)} for item in contents]
        return [{"role": "user", "content": str(contents)}]


class ClaudeBackend(BaseBackend):
    """
    Anthropic Claude backend implementation.

    Supports:
    - Claude 4.5 Sonnet (default)
    - Claude 4.5 Opus
    - Vision capabilities (interprets figures)
    - Text knowledge base integration
    """

    @property
    def backend_name(self) -> str:
        """Return the backend name."""
        return "claude"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 3000,
        enable_caching: bool = True,
        verbose: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, max_tokens, enable_caching, **kwargs)  # Pass kwargs
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.verbose = verbose

        if self.verbose >= 1:
            ilog_info(f"Initialized with model: {self.model}", title="Claude")

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

        if self.verbose >= 1:
            ilog_info(f"Calling {self.model} (call #{self.call_count})", title="Claude")

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
            if self.verbose >= 2:
                ilog_debug("Attached figure as base64 image", title="Claude")

        # Add data
        if data is not None:
            data_text = self._data_to_text(data)
            content_blocks.append(
                {"type": "text", "text": f"Data to analyze:\n```\n{data_text}\n```"}
            )
            if self.verbose >= 2:
                ilog_debug(f"Attached data ({len(data_text)} chars)", title="Claude")

        # Add prompt
        prompt = self._build_prompt(context, focus, kb_context, custom_prompt)
        content_blocks.append({"type": "text", "text": prompt})

        if self.verbose >= 2:
            ilog_debug(f"Prompt length: {len(prompt)} chars", title="Request")
            if kb_context:
                ilog_debug(
                    f"Knowledge base context: {len(kb_context)} chars", title="Request"
                )

        messages.append({"role": "user", "content": content_blocks})

        try:
            response = cast("Any", self.client.messages.create)(
                model=self.model, max_tokens=self.max_tokens, messages=messages
            )

            # Extract text from first content block (handle union type)
            first_block = response.content[0]
            interpretation = (
                first_block.text if hasattr(first_block, "text") else str(first_block)
            )
            usage = self._calculate_usage(response.usage)

            if self.verbose >= 1:
                ilog_info(
                    f"Tokens: {usage.input_tokens} in / {usage.output_tokens} out "
                    f"(${usage.cost:.4f})",
                    title="Claude",
                )
            if self.verbose >= 2:
                ilog_debug(
                    f"Response length: {len(interpretation)} chars", title="Response"
                )

            return InterpretationResult(
                text=interpretation,
                backend="claude",
                usage=usage,
                metadata={"model": self.model},
            )

        except Exception as e:
            ilog_warning(f"API call failed: {e}", title="Claude")
            return InterpretationResult(
                text=f"❌ **Error**: {e!s}", backend="claude", usage=None
            )
        finally:
            # Update shared cost tracking
            if "usage" in locals() and usage:
                self.total_tokens["input"] += usage.input_tokens
                self.total_tokens["output"] += usage.output_tokens
                self.total_cost += usage.cost

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build Claude-optimized prompt using centralized templates."""
        return self._build_prompt_from_templates(
            context, focus, kb_context, custom_prompt
        )

    def _calculate_usage(self, usage_data: Any) -> UsageInfo:
        input_tokens = usage_data.input_tokens
        output_tokens = usage_data.output_tokens

        pricing = get_model_pricing("claude", self.model)
        if not pricing:
            # Fallback default if pricing not found
            pricing = {"input_price": 3.00, "output_price": 15.00}

        cost = (input_tokens / 1_000_000 * pricing.get("input_price", 3.00)) + (
            output_tokens / 1_000_000 * pricing.get("output_price", 15.00)
        )

        return UsageInfo(
            input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
        )

    def encode_kb(self, kb_manager: Any) -> Optional[str]:
        """
        Encode knowledge base for Claude backend.

        Strategy:
        - Text: Concatenate into prompt
        - PDFs: Currently text only (native PDF support can be added)
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
                "Claude PDF support is coming in a future update. "
                "Text files will be used for now.",
                source="kanoa.backends.claude",
            )

        return text_content or None
