import asyncio
import os
import threading
from typing import Any, Dict, Iterator, List, Optional

import matplotlib.pyplot as plt

from ..core.types import InterpretationChunk, UsageInfo
from ..pricing import get_model_pricing
from ..utils.logging import ilog_debug, ilog_info, ilog_warning
from .base import BaseBackend


class _AsyncSessionManager:
    """
    Manages GitHub Copilot session in a background thread.

    Ensures prompt persistence (multi-turn chat) and compatibility
    with both script and Jupyter environments.
    """

    def __init__(
        self,
        cli_path: str,
        cli_url: Optional[str],
        model: str,
        streaming: bool,
        verbose: int,
        client_class: Any,
    ):
        self.cli_path = cli_path
        self.cli_url = cli_url
        self.model = model
        self.streaming = streaming
        self.verbose = verbose
        self._client_class = client_class

        # Threading state
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._client: Optional[Any] = None
        self._session: Optional[Any] = None
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="CopilotSessionThread"
        )
        self._ready = threading.Event()
        self._thread.start()

        # Wait for loop to be ready
        self._ready.wait(timeout=5.0)

    def _run_loop(self) -> None:
        """Run the asyncio loop in a background thread."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ready.set()
            self._loop.run_forever()
        except Exception as e:
            if self.verbose >= 1:
                ilog_warning(f"Background thread failed: {e}", title="GitHubCopilot")

    async def _ensure_session(self) -> Any:
        """Initialize client and session if needed."""
        if self._client is None:
            client_kwargs = {
                "cli_path": self.cli_path,
                "log_level": "debug" if self.verbose >= 2 else "info",
                "auto_start": True,
                "auto_restart": True,
            }
            if self.cli_url:
                client_kwargs["cli_url"] = self.cli_url

            self._client = self._client_class(options=client_kwargs)
            await self._client.start()

        if self._session is None:
            if self.verbose >= 1:
                ilog_info("Creating new session", title="GitHubCopilot")

            self._session = await self._client.create_session(
                {
                    "model": self.model,
                    "streaming": self.streaming,
                }
            )
        return self._session

    async def _process_message(self, prompt: str) -> Dict[str, Any]:
        """Process a message within the event loop."""
        try:
            session = await self._ensure_session()

            chunks: List[InterpretationChunk] = []
            full_text: List[str] = []
            done = asyncio.Event()

            def on_event(event: Any) -> None:
                """Handle events from Copilot session."""
                event_type = (
                    event.type.value
                    if hasattr(event.type, "value")
                    else str(event.type)
                )

                if event_type == "assistant.message_delta" and self.streaming:
                    delta = getattr(event.data, "delta_content", None) or ""
                    if delta:
                        chunks.append(InterpretationChunk(content=delta, type="text"))
                        full_text.append(delta)
                elif event_type == "assistant.message":
                    content = getattr(event.data, "content", "")
                    if not self.streaming:
                        chunks.append(InterpretationChunk(content=content, type="text"))
                        full_text.append(content)
                elif event_type == "session.idle":
                    done.set()

            # Register handler
            session.on(on_event)

            # Send prompt
            await session.send({"prompt": prompt})

            # Wait for completion
            try:
                await asyncio.wait_for(done.wait(), timeout=120.0)
            except asyncio.TimeoutError:
                ilog_warning("Session timeout after 120s", title="GitHubCopilot")

            # NOTE: Token estimation limitation
            # GitHub Copilot SDK doesn't currently expose token counts.
            text_length = sum(len(t) for t in full_text)
            estimated_input_tokens = len(prompt) // 4
            estimated_output_tokens = text_length // 4

            return {
                "chunks": chunks,
                "usage": {
                    "input_tokens": estimated_input_tokens,
                    "output_tokens": estimated_output_tokens,
                },
            }
        except Exception as e:
            # If session is broken, clear it so next call retries
            ilog_warning(f"Session error: {e}", title="GitHubCopilot")
            self._session = None
            raise

    async def _reset(self) -> None:
        """Reset the session to clear history."""
        if self._session:
            await self._session.destroy()
            self._session = None
        if self._client:
            await self._client.stop()
            self._client = None

    def send_message(self, prompt: str) -> Dict[str, Any]:
        """Submit message to background thread and wait for result."""
        if not self._loop:
            raise RuntimeError("Background loop not running")

        future = asyncio.run_coroutine_threadsafe(
            self._process_message(prompt), self._loop
        )
        return future.result()

    def reset(self) -> None:
        """Reset session and client."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._reset(), self._loop).result()


class GitHubCopilotBackend(BaseBackend):
    """
    GitHub Copilot SDK backend implementation.

    Supports:
    - GPT-5 and other GitHub Copilot models
    - Streaming responses
    - Vision capabilities (interprets figures)
    - Text knowledge base integration
    - Multi-turn conversation (chat history)
    """

    @property
    def backend_name(self) -> str:
        """Return the backend name."""
        return "github-copilot"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cli_path: Optional[str] = None,
        cli_url: Optional[str] = None,
        model: str = "gpt-5",
        max_tokens: int = 3000,
        enable_caching: bool = True,
        verbose: int = 0,
        streaming: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key, max_tokens, enable_caching, **kwargs)

        # Import here to provide clear error message if package not installed
        try:
            from copilot import (  # type: ignore[import-not-found]
                CopilotClient,
            )
        except ImportError as e:
            raise ImportError(
                "GitHubCopilotBackend requires github-copilot-sdk. "
                "Install with: pip install kanoa[github-copilot]\n"
                f"Original error: {e}"
            ) from e

        self.model = model
        self.verbose = verbose
        # Initialize session manager
        self._manager = _AsyncSessionManager(
            cli_path=cli_path or os.environ.get("COPILOT_CLI_PATH", "copilot"),
            cli_url=cli_url,
            model=model,
            streaming=streaming,
            verbose=verbose,
            client_class=CopilotClient,
        )

        if self.verbose >= 1:
            ilog_info(f"Initialized with model: {self.model}", title="GitHubCopilot")

    def reset_chat(self) -> None:
        """Clear conversation history and reset session."""
        if self.verbose >= 1:
            ilog_info("Resetting conversation history", title="GitHubCopilot")
        self._manager.reset()

    def interpret(
        self,
        fig: Optional[plt.Figure],
        data: Optional[Any],
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
        **kwargs: Any,
    ) -> Iterator[InterpretationChunk]:
        """Interpret using GitHub Copilot SDK (streaming)."""
        self.call_count += 1

        if self.verbose >= 1:
            ilog_info(
                f"Calling {self.model} (call #{self.call_count})", title="GitHubCopilot"
            )

        yield InterpretationChunk(
            content=f"Connecting to {self.model}...", type="status"
        )

        # Yield metadata
        yield InterpretationChunk(
            content="", type="meta", metadata={"model": self.model}
        )

        # Build content parts
        content_parts = []

        # Add figure if provided
        if fig is not None:
            # Note: GitHub Copilot SDK may not support image inputs directly
            # For now, we'll add a note about it
            # We convert to base64 but don't use it yet until SDK supports it
            _ = self._fig_to_base64(fig)  # Prepare for future vision support
            content_parts.append(
                "[Image provided - visual analysis may be limited in current SDK version]"
            )
            if self.verbose >= 2:
                ilog_debug("Figure attached (support pending)", title="GitHubCopilot")

        # Add data
        if data is not None:
            data_text = self._data_to_text(data)
            content_parts.append(f"Data to analyze:\n```\n{data_text}\n```")
            if self.verbose >= 2:
                ilog_debug(
                    f"Attached data ({len(data_text)} chars)", title="GitHubCopilot"
                )

        # Add prompt
        prompt = self._build_prompt(context, focus, kb_context, custom_prompt)
        content_parts.append(prompt)

        if self.verbose >= 2:
            ilog_debug(f"Prompt length: {len(prompt)} chars", title="Request")
            if kb_context:
                ilog_debug(
                    f"Knowledge base context: {len(kb_context)} chars", title="Request"
                )

        # Combine all parts
        full_prompt = "\n\n".join(content_parts)

        try:
            # Delegate to session manager running in background thread
            result = self._manager.send_message(full_prompt)

            # Yield accumulated text chunks
            for chunk in result["chunks"]:
                yield chunk

            # Calculate and yield usage
            usage = self._calculate_usage(result.get("usage", {}))

            if self.verbose >= 1:
                ilog_info(
                    f"Tokens: {usage.input_tokens} in / {usage.output_tokens} out "
                    f"(${usage.cost:.4f})",
                    title="GitHubCopilot",
                )

            # Update shared stats
            self.total_tokens["input"] += usage.input_tokens
            self.total_tokens["output"] += usage.output_tokens
            self.total_cost += usage.cost

            yield InterpretationChunk(
                content="", type="usage", is_final=True, usage=usage
            )

        except Exception as e:
            ilog_warning(f"API call failed: {e}", title="GitHubCopilot")
            yield InterpretationChunk(content=f"\n❌ Error: {e!s}", type="text")
            raise

    # _run_session method removed as logic is now in _AsyncSessionManager

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build GitHub Copilot-optimized prompt using centralized templates."""
        return self._build_prompt_from_templates(
            context, focus, kb_context, custom_prompt
        )

    def _calculate_usage(self, usage_data: dict[str, Any]) -> UsageInfo:
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)

        pricing = get_model_pricing("github-copilot", self.model)
        if not pricing:
            # Fallback: Use pricing from pricing.json for gpt-5 (1.25/10.00 per 1M tokens)
            # These match the values in pricing.json for github-copilot models
            pricing = {"input_price": 1.25, "output_price": 10.00}

        cost = (input_tokens / 1_000_000 * pricing.get("input_price", 1.25)) + (
            output_tokens / 1_000_000 * pricing.get("output_price", 10.00)
        )

        return UsageInfo(
            input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
        )

    def encode_kb(self, kb_manager: Any) -> Optional[str]:
        """
        Encode knowledge base for GitHub Copilot backend.

        Currently supports text content only.

        Args:
            kb_manager: KnowledgeBaseManager instance

        Returns:
            Text context string for the prompt
        """
        from ..knowledge_base.manager import KnowledgeBaseManager

        if not isinstance(kb_manager, KnowledgeBaseManager):
            return None

        # Get text content
        text_content = kb_manager.get_text_content()

        # Check for PDFs - warn user for now
        if kb_manager.has_pdfs():
            ilog_warning(
                "PDFs detected in knowledge base. "
                "GitHub Copilot SDK currently supports text only. "
                "Text files will be used.",
                source="kanoa.backends.github_copilot",
            )

        return text_content or None
