"""
Gemini Deep Research Agent backend (Official AI Studio API).

This backend wraps the official Interactions API `deep-research-pro-preview-12-2025`
agent, which supports:
- Multi-step web research
- GDrive document grounding (personal/Workspace)
- File Search tool integration
- Streaming thought summaries

⚠️ Requires google-genai >= 2.0 (with Interactions API support).
"""

from typing import Any, Iterator, Optional

import matplotlib.pyplot as plt

try:
    from google import genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from ..core.types import InterpretationChunk, UsageInfo
from ..pricing import get_model_pricing
from ..utils.logging import ilog_debug, ilog_info
from .base import BaseBackend


class GeminiDeepResearchBackend(BaseBackend):
    """
    Official Gemini Deep Research Agent backend (AI Studio).

    Uses the Interactions API to invoke the `deep-research-pro-preview-12-2025`
    agent for multi-step research tasks with web search and optional GDrive/File
    Search grounding.

    Best for:
    - Students/researchers with free-tier AI Studio accounts
    - Deep research queries requiring multi-step reasoning
    - Integration with personal GDrive documents

    Note: Enterprise/Vertex AI users should use GeminiDeepResearchProxyBackend.
    """

    @property
    def backend_name(self) -> str:
        return "gemini-deep-research"

    def __init__(
        self,
        api_key: Optional[str] = None,
        agent: str = "deep-research-pro-preview-12-2025",
        max_research_time: int = 1200,  # 20 minutes (max is 60)
        enable_thinking_summaries: bool = True,
        file_search_stores: Optional[list[str]] = None,
        **kwargs: Any,
    ):
        """
        Initialize Gemini Deep Research backend.

        Args:
            api_key: Google AI Studio API key (required).
            agent: Agent identifier (default: deep-research-pro-preview-12-2025).
            max_research_time: Maximum research time in seconds (default: 1200s / 20min).
            enable_thinking_summaries: Stream thought process updates.
            file_search_stores: List of File Search store names for RAG
                                (e.g., ['fileSearchStores/my-store']).
            **kwargs: Additional args passed to BaseBackend.
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "GeminiDeepResearchBackend requires google-genai >= 2.0 with "
                "Interactions API support. Install with: pip install 'google-genai>=2.0'"
            )

        super().__init__(api_key, max_tokens=0, enable_caching=False, **kwargs)
        self.agent = agent
        self.model = agent  # Store agent as model for pricing lookup
        self.max_research_time = max_research_time
        self.enable_thinking_summaries = enable_thinking_summaries
        self.file_search_stores = file_search_stores or []

        if not api_key:
            raise ValueError(
                "GeminiDeepResearchBackend requires an AI Studio API key. "
                "Vertex AI is not supported for the Interactions API. "
                "Get a free key at: https://aistudio.google.com/apikey"
            )

        self.client = genai.Client(api_key=api_key)

        # Verify interactions API is available
        if not hasattr(self.client, "interactions"):
            raise RuntimeError(
                "Interactions API not available in google-genai version. "
                "Please upgrade: pip install --upgrade google-genai"
            )

    def interpret(
        self,
        fig: Optional[plt.Figure] = None,
        data: Optional[Any] = None,
        context: Optional[str] = None,
        focus: Optional[str] = None,
        kb_context: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator["InterpretationChunk"]:
        """
        Execute Deep Research via Interactions API.

        Yields:
            InterpretationChunk: Status updates, thought summaries, and final results.
        """
        # 1. Status: Initializing
        ilog_debug(
            "Starting Gemini Deep Research interpretation", source="deep-research"
        )
        yield InterpretationChunk(
            type="status", content="🔍 Initializing Gemini Deep Research Agent..."
        )

        # 2. Build research prompt
        research_query = self._build_research_prompt(
            fig, data, context, focus, kb_context, custom_prompt
        )
        ilog_debug(
            f"Research query built: {research_query[:200]}",
            source="deep-research",
        )

        yield InterpretationChunk(
            type="status", content=f"📝 Research Query: {research_query[:100]}..."
        )

        # 3. Configure tools (File Search if provided)
        tools: list[dict[str, Any]] = []
        if self.file_search_stores:
            tools.append(
                {
                    "type": "file_search",
                    "file_search_store_names": self.file_search_stores,
                }
            )
            ilog_info(
                f"Configured File Search with {len(self.file_search_stores)} store(s)",
                source="deep-research",
            )
            yield InterpretationChunk(
                type="status",
                content=f"📚 Using {len(self.file_search_stores)} File Search store(s)",
            )

        # 4. Configure agent
        agent_config: dict[str, Any] = {"type": "deep-research"}
        if self.enable_thinking_summaries:
            agent_config["thinking_summaries"] = "auto"
        ilog_debug(
            f"Agent config: {agent_config}",
            source="deep-research",
        )

        # 5. Start research (streaming)
        ilog_info(
            "Starting google.genai Interactions API research", source="deep-research"
        )
        yield InterpretationChunk(type="status", content="🚀 Starting research...")

        try:
            # Use Any cast for experimental interactions API to avoid finicky Mypy issues
            client_any: Any = self.client
            stream = client_any.interactions.create(
                input=research_query,
                agent=self.agent,
                background=True,
                stream=True,
                agent_config=agent_config,
                tools=tools if tools else None,
            )

            interaction_id: Optional[str] = None
            thought_count = 0
            text_buffer = ""
            usage_metadata: Optional[Any] = None

            for chunk in stream:
                # Capture interaction ID
                if chunk.event_type == "interaction.start":
                    interaction_id = chunk.interaction.id
                    ilog_info(
                        f"Interaction started: {interaction_id}",
                        source="deep-research",
                    )
                    yield InterpretationChunk(
                        type="status",
                        content=f"✅ Research started (ID: {interaction_id})",
                    )

                # Thought summaries
                elif (
                    chunk.event_type == "content.delta"
                    and hasattr(chunk.delta, "type")
                    and chunk.delta.type == "thought_summary"
                ):
                    thought_count += 1
                    thought_text = chunk.delta.content.text

                    # Log preview at verbose=1, full text at verbose=2
                    ilog_info(
                        f"Step {thought_count}: {thought_text[:100]}...",
                        source="deep-research",
                    )
                    ilog_debug(
                        f"Step {thought_count} (full): {thought_text}",
                        source="deep-research",
                    )

                    yield InterpretationChunk(
                        type="status",
                        content=f"💭 Step {thought_count}: {thought_text}",
                    )

                # Text deltas (final report)
                elif (
                    chunk.event_type == "content.delta"
                    and hasattr(chunk.delta, "type")
                    and chunk.delta.type == "text"
                ):
                    text_buffer += chunk.delta.text
                    ilog_debug(
                        f"Received text delta: {len(chunk.delta.text)} chars",
                        source="deep-research",
                    )
                    yield InterpretationChunk(type="text", content=chunk.delta.text)

                # Completion
                elif chunk.event_type == "interaction.complete":
                    ilog_info(
                        f"Research complete. Final text: {len(text_buffer)} chars",
                        source="deep-research",
                    )
                    yield InterpretationChunk(
                        type="status", content="✅ Research complete!"
                    )
                    break

                # Error handling
                elif chunk.event_type == "error":
                    error_msg = (
                        chunk.error if hasattr(chunk, "error") else "Unknown error"
                    )
                    ilog_debug(
                        f"Research error: {error_msg}",
                        source="deep-research",
                    )
                    yield InterpretationChunk(
                        type="status", content=f"❌ Research failed: {error_msg}"
                    )
                    break

                # Capture usage metadata
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage_metadata = chunk.usage_metadata
                    ilog_debug(
                        "Captured usage metadata",
                        source="deep-research",
                    )

            # Calculate and yield usage after completion
            usage = None
            if usage_metadata:
                # Extract token counts from usage_metadata
                input_tokens = getattr(usage_metadata, "prompt_token_count", 0)
                output_tokens = getattr(usage_metadata, "candidates_token_count", 0)

                # Get pricing for this model
                pricing = get_model_pricing("gemini", self.model, tier="default")
                if pricing:
                    input_price = pricing.get("input_price", 0.0)
                    output_price = pricing.get("output_price", 0.0)

                    input_cost = input_tokens / 1_000_000 * input_price
                    output_cost = output_tokens / 1_000_000 * output_price
                    total_cost = input_cost + output_cost
                else:
                    # Fallback if no pricing found
                    total_cost = 0.0

                usage = UsageInfo(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=total_cost,
                    cached_tokens=0,
                    cache_created=False,
                    savings=0.0,
                    model=self.model,
                    tier="default",
                )

                ilog_info(
                    f"Usage: {input_tokens:,} in + {output_tokens:,} out = ${total_cost:.4f}",
                    source="deep-research",
                )

            # After loop, yield usage chunk
            yield InterpretationChunk(
                content="",
                type="usage",
                usage=usage,
            )

        except Exception as e:
            ilog_debug(
                f"Exception during research: {e!s}",
                source="deep-research",
            )
            yield InterpretationChunk(
                type="status", content=f"❌ Error during research: {e!s}"
            )
            raise

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build prompt for the backend (required by abstract base class)."""
        return self._build_prompt_from_templates(
            context, focus, kb_context, custom_prompt
        )

    def _build_research_prompt(
        self,
        fig: Optional[plt.Figure],
        data: Optional[Any],
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build research prompt from inputs."""
        if custom_prompt:
            return custom_prompt

        parts = []

        if context:
            parts.append(f"Context: {context}")

        if data is not None:
            parts.append(f"Data Summary: {str(data)[:500]}")

        if kb_context:
            parts.append(f"Background Knowledge:\n{kb_context}")

        if focus:
            parts.append(f"Research Focus: {focus}")
        else:
            parts.append("Research Focus: Analyze and explain the provided data.")

        return "\n\n".join(parts)
