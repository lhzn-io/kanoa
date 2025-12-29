from typing import Any, Iterator, Optional

import matplotlib.pyplot as plt
from google import genai
from google.genai import types

from ..backends.base import BaseBackend
from ..core.types import InterpretationChunk, UsageInfo
from ..knowledge_base.base import BaseKnowledgeBase
from ..pricing import get_model_pricing
from ..utils.logging import ilog_debug, ilog_info


class GeminiExampleCustomResearchBackend(BaseBackend):
    """
    Example Custom Research Backend (Vertex AI Only).

    A "white-box" reference implementation designed to demonstrate grounded research
    using Vertex AI's API. Unlike the official Gemini Deep Research agent (which is
    a black box), this backend explicitly orchestrates:
    1. Internal Knowledge Base Retrieval (RAG)
    2. Google Search Grounding (Vertex AI google_search API)
    3. Transparent Prompt Construction & Synthesis

    **Important**: This backend requires Vertex AI authentication (ADC) and uses
    the Vertex AI-specific `google_search` tool (not AI Studio's `google_search_retrieval`).

    Use this when you need full control over the research loop or
    strict adherence to internal knowledge before seeking external info.
    """

    @property
    def backend_name(self) -> str:
        return "gemini-example-custom-research"

    def __init__(
        self,
        project: str,
        location: str = "us-central1",
        model: str = "gemini-3-pro-preview",
        max_tokens: int = 3000,
        dynamic_threshold: float = 0.7,
        thinking_level: str = "HIGH",
        **kwargs: Any,
    ):
        """
        Initialize Gemini Example Custom Research backend (Vertex AI only).

        **Authentication**: This backend requires Google Cloud Application Default
        Credentials (ADC). Run `gcloud auth application-default login` first.

        Args:
            project: GCP Project ID (required).
            location: GCP location (default: us-central1).
            model: Gemini model to use (default: gemini-3-pro-preview).
            max_tokens: Maximum tokens for response.
            dynamic_threshold: Threshold for triggering Google Search (0.0-1.0).
            **kwargs: Additional args passed to BaseBackend.
        """
        super().__init__(
            api_key=None, max_tokens=max_tokens, enable_caching=False, **kwargs
        )
        self.model = model
        self.dynamic_threshold = dynamic_threshold
        self.project = project
        self.location = location
        self.thinking_level = thinking_level.upper()

        # Initialize Vertex AI client (ADC required)
        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
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
        Execute Research flow: RAG -> Prompt -> Search -> Generate.
        """
        # 1. Status: Initializing
        ilog_debug(
            "Starting Gemini Example Custom Research interpretation",
            source="gemini-example-custom-research",
        )
        yield InterpretationChunk(
            type="status", content="🔍 Initializing Example Custom Research Backend..."
        )

        # 2. RAG Retrieval
        rag_text = ""
        knowledge_base = kwargs.get("knowledge_base")

        if knowledge_base and isinstance(knowledge_base, BaseKnowledgeBase):
            query = focus or context or "Analyze the data"
            ilog_debug(
                f"Querying Knowledge Base: {query[:100]}",
                source="gemini-example-custom-research",
            )
            yield InterpretationChunk(
                type="status", content=f"📚 Querying Knowledge Base for: '{query}'..."
            )
            try:
                # Assuming retrieve returns list of dicts with 'text' key
                results = knowledge_base.retrieve(query)
                if results:
                    rag_text = "\n\n".join(
                        [
                            f"Source ({r.get('score', 0):.2f}): {r['text']}"
                            for r in results
                        ]
                    )
                    ilog_info(
                        f"Retrieved {len(results)} chunks from KB",
                        source="gemini-example-custom-research",
                    )
                    yield InterpretationChunk(
                        type="status",
                        content=f"✅ Retrieved {len(results)} chunks from KB.",
                    )
                else:
                    ilog_debug(
                        "No relevant info found in KB",
                        source="gemini-example-custom-research",
                    )
                    yield InterpretationChunk(
                        type="status", content="⚠️ No relevant info found in KB."
                    )
            except Exception as e:
                ilog_debug(f"RAG Error: {e}", source="gemini-example-custom-research")
                yield InterpretationChunk(type="status", content=f"❌ RAG Error: {e}")

        # Use provided kb_context if RAG didn't yield anything or wasn't used
        final_kb_context = rag_text if rag_text else kb_context

        # 3. Prompt Construction
        prompt = self._build_prompt(context, focus, final_kb_context, custom_prompt)
        ilog_debug(
            f"Prompt constructed: {len(prompt)} chars",
            source="gemini-example-custom-research",
        )

        # 4. Execution with Google Search
        ilog_info(
            "Starting Google Search & Synthesis",
            source="gemini-example-custom-research",
        )
        yield InterpretationChunk(
            type="status", content="🌐 Performing Google Search & Synthesis..."
        )

        # Configure Google Search Tool (Vertex AI API)
        # Note: Vertex AI uses `google_search`, not `google_search_retrieval`
        tools = [types.Tool(google_search=types.GoogleSearch())]

        # Configure Thinking and Search
        thinking_config = types.ThinkingConfig(
            thinking_level=getattr(
                types.ThinkingLevel, self.thinking_level, types.ThinkingLevel.HIGH
            )
        )

        generate_config = types.GenerateContentConfig(
            max_output_tokens=self.max_tokens,
            tools=tools,  # type: ignore[arg-type]
            thinking_config=thinking_config,
            system_instruction=self._get_system_instructions(
                bool(rag_text or kb_context)
            ),
        )

        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=generate_config,
            )

            text_buffer = ""
            usage_metadata = None

            for chunk in response_stream:
                if chunk.text:
                    text_buffer += chunk.text
                    ilog_debug(
                        f"Received text chunk: {len(chunk.text)} chars",
                        source="gemini-example-custom-research",
                    )
                    yield InterpretationChunk(type="text", content=chunk.text)

                # Capture usage metadata (usually in last chunk)
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage_metadata = chunk.usage_metadata

                # Handle grounding metadata if present
                if hasattr(chunk, "candidates") and chunk.candidates:
                    for candidate in chunk.candidates:
                        if (
                            hasattr(candidate, "grounding_metadata")
                            and candidate.grounding_metadata
                        ):
                            ilog_debug(
                                "Received grounding metadata",
                                source="gemini-example-custom-research",
                            )
                            # We might want to yield this as a special chunk or append to text
                            # For now, let's just log it or yield as meta
                            gm = candidate.grounding_metadata
                            if (
                                hasattr(gm, "search_entry_point")
                                and gm.search_entry_point
                            ):
                                yield InterpretationChunk(
                                    type="meta",
                                    content="",
                                    metadata={"grounding": str(gm)},
                                )

            ilog_info(
                f"Generation complete: {len(text_buffer)} chars",
                source="gemini-example-custom-research",
            )

            # Calculate and yield usage
            usage = None
            if usage_metadata:
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
                    source="gemini-example-research",
                )

            yield InterpretationChunk(
                content="",
                type="usage",
                usage=usage,
            )

        except Exception as e:
            ilog_debug(f"Generation error: {e}", source="gemini-example-research")
            yield InterpretationChunk(
                type="text", content=f"\n❌ Error during generation: {e}"
            )

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build the prompt for Research."""
        parts = []

        parts.append(
            "You are a Research Assistant. Your goal is to provide a comprehensive, fact-checked answer."
        )
        parts.append(
            "You have access to Google Search to verify information and find the latest data."
        )

        if context:
            parts.append(f"\nContext:\n{context}")

        if kb_context:
            parts.append(f"\nInternal Knowledge Base Context:\n{kb_context}")
            parts.append(
                "\nUse the Internal Knowledge Base Context as your primary source of truth for internal matters."
            )
            parts.append("Use Google Search to verify external facts or fill gaps.")

        if focus:
            parts.append(f"\nFocus on:\n{focus}")

        if custom_prompt:
            parts.append(f"\nInstructions:\n{custom_prompt}")
        else:
            parts.append(
                "\nInstructions:\nAnalyze the provided information. Use Google Search to verify key claims. Provide citations where possible."
            )

        return "\n".join(parts)

    def _get_system_instructions(self, has_kb: bool) -> str:
        """Get system instructions following Gemini 3 best practices."""
        instructions = [
            "Your knowledge cutoff date is January 2025.",
            "For time-sensitive user queries that require up-to-date information, you MUST follow the provided current time (date and year) when formulating search queries in tool calls. Remember it is 2025 this year.",
        ]

        if has_kb:
            instructions.append(
                "You are a strictly grounded assistant limited to the information provided in the Internal Knowledge Base Context. "
                "In your answers, rely **only** on the facts that are directly mentioned in that context. "
                "Treat the provided context as the absolute limit of truth; any facts or details that are not directly mentioned "
                "in the context must be considered completely unsupported unless you use the Google Search tool to verify external facts."
            )

        return " ".join(instructions)
