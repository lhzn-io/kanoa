from typing import Any, Iterator, Optional

import matplotlib.pyplot as plt
from google import genai
from google.genai import types

from ..core.types import InterpretationChunk, UsageInfo
from ..knowledge_base.base import BaseKnowledgeBase
from ..pricing import get_model_pricing
from ..utils.logging import ilog_debug, ilog_info
from .base import BaseBackend


class GeminiResearchReferenceBackend(BaseBackend):
    """
    Gemini Research Reference Backend (Grounded Generation).

    A reference implementation of a research agent that combines:
    1. Internal Knowledge Base Retrieval (RAG)
    2. Google Search Grounding
    3. Synthesis

    This backend serves as an architectural reference for building custom,
    grounded agent workflows using the standard Gemini API. It is NOT the
    official Google Deep Research agent, but rather a demonstration of how
    to build similar capabilities using kanoa's components.

    Future Enhancements:
    - Iterative refinement loop (e.g., "critique and refine" cycle)
    - Budget-aware execution (stop when cost threshold reached)
    - Vetted source constraints (restrict search to specific domains)
    """

    @property
    def backend_name(self) -> str:
        return "gemini-research-reference"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-pro-preview",
        max_tokens: int = 3000,
        dynamic_threshold: float = 0.7,
        **kwargs: Any,
    ):
        """
        Initialize Gemini Research backend.

        Args:
            api_key: Google AI API key.
            model: Gemini model to use (default: gemini-3-pro-preview).
            max_tokens: Maximum tokens for response.
            dynamic_threshold: Threshold for triggering Google Search (0.0-1.0).
            **kwargs: Additional args passed to BaseBackend/Client.
        """
        super().__init__(api_key, max_tokens, enable_caching=False, **kwargs)
        self.model = model
        self.dynamic_threshold = dynamic_threshold

        # Initialize client
        client_kwargs: dict[str, Any] = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        else:
            client_kwargs["vertexai"] = True
            if "project" in kwargs:
                client_kwargs["project"] = kwargs["project"]
            if "location" in kwargs:
                client_kwargs["location"] = kwargs["location"]

        self.client = genai.Client(**client_kwargs)

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
            "Starting Gemini Research Reference interpretation",
            source="gemini-research-ref",
        )
        yield InterpretationChunk(
            type="status", content="🔍 Initializing Research Reference Backend..."
        )

        # 2. RAG Retrieval
        rag_text = ""
        knowledge_base = kwargs.get("knowledge_base")

        if knowledge_base and isinstance(knowledge_base, BaseKnowledgeBase):
            query = focus or context or "Analyze the data"
            ilog_debug(
                f"Querying Knowledge Base: {query[:100]}",
                source="gemini-research-ref",
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
                        source="gemini-research-ref",
                    )
                    yield InterpretationChunk(
                        type="status",
                        content=f"✅ Retrieved {len(results)} chunks from KB.",
                    )
                else:
                    ilog_debug(
                        "No relevant info found in KB", source="gemini-research-ref"
                    )
                    yield InterpretationChunk(
                        type="status", content="⚠️ No relevant info found in KB."
                    )
            except Exception as e:
                ilog_debug(f"RAG Error: {e}", source="gemini-research-ref")
                yield InterpretationChunk(type="status", content=f"❌ RAG Error: {e}")

        # Use provided kb_context if RAG didn't yield anything or wasn't used
        final_kb_context = rag_text if rag_text else kb_context

        # 3. Prompt Construction
        prompt = self._build_prompt(context, focus, final_kb_context, custom_prompt)
        ilog_debug(
            f"Prompt constructed: {len(prompt)} chars", source="gemini-research-ref"
        )

        # 4. Execution with Google Search
        ilog_info("Starting Google Search & Synthesis", source="gemini-research-ref")
        yield InterpretationChunk(
            type="status", content="🌐 Performing Google Search & Synthesis..."
        )

        # Configure Search Tool
        tools = [
            types.Tool(
                google_search_retrieval=types.GoogleSearchRetrieval(
                    dynamic_retrieval_config=types.DynamicRetrievalConfig(
                        mode="dynamic",  # type: ignore[arg-type]
                        dynamic_threshold=self.dynamic_threshold,
                    )
                )
            )
        ]

        generate_config = types.GenerateContentConfig(
            max_output_tokens=self.max_tokens,
            tools=tools,  # type: ignore[arg-type]
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
                        source="gemini-research-ref",
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
                                source="gemini-research-ref",
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
                source="gemini-research-ref",
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
                    source="gemini-research-ref",
                )

            yield InterpretationChunk(
                content="",
                type="usage",
                usage=usage,
            )

        except Exception as e:
            ilog_debug(f"Generation error: {e}", source="gemini-research-ref")
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
