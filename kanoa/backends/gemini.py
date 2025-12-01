import base64
import hashlib
import os
import time
from typing import Any, Dict, List, Optional, cast

import matplotlib.pyplot as plt
from google import genai
from google.genai import types

from ..core.types import InterpretationResult, UsageInfo
from .base import BaseBackend


class GeminiBackend(BaseBackend):
    """
    Google Gemini backend with native PDF support and context caching.

    Features:
    - Native multimodal PDF processing (sees figures, tables)
    - 1M token context window
    - Explicit context caching for cost optimization (10x savings on cached tokens)
    - File Search tool for RAG
    - Automatic cache management with configurable TTL
    """

    # Pricing (per 1M tokens) - Gemini 3.0 Pro (Preview)
    # Note: Google does not provide a public pricing API.
    # These values are manually maintained based on official documentation.
    PRICING = {
        "input_short": 2.00,  # <= 200K context
        "output_short": 12.00,
        "input_long": 4.00,  # > 200K context
        "output_long": 18.00,
        "cached_input": 0.50,  # Cached content input (75% cheaper)
        "cached_storage": 1.00,  # Per 1M tokens per hour
    }

    # Minimum token counts for context caching by model
    MIN_CACHE_TOKENS = {
        "gemini-3-pro-preview": 2048,
        "gemini-2.5-pro": 4096,
        "gemini-2.5-flash": 1024,
        "default": 1024,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-pro-preview",
        max_tokens: int = 3000,
        enable_caching: bool = True,
        cache_ttl_seconds: int = 3600,
        thinking_level: str = "high",
        media_resolution: str = "medium",
        **kwargs: Any,
    ):
        """
        Initialize Gemini backend.

        Args:
            api_key: Google AI API key (or set GOOGLE_API_KEY env var)
            model: Gemini model to use (default: gemini-3-pro-preview)
            max_tokens: Maximum tokens for response
            enable_caching: Enable explicit context caching for KB content
            cache_ttl_seconds: Cache time-to-live in seconds (default: 1 hour)
            thinking_level: Thinking level for thinking models
            media_resolution: Resolution for image/video processing
            **kwargs: Additional args (project, location for Vertex AI)
        """
        super().__init__(api_key, max_tokens, enable_caching)

        # Initialize client with support for both AI Studio and Vertex AI
        client_kwargs: Dict[str, Any] = {}
        if api_key or os.environ.get("GOOGLE_API_KEY"):
            client_kwargs["api_key"] = api_key or os.environ.get("GOOGLE_API_KEY")
        else:
            # Fallback to Vertex AI if no API key (uses ADC)
            client_kwargs["vertexai"] = True
            if "project" in kwargs:
                client_kwargs["project"] = kwargs["project"]
            if "location" in kwargs:
                client_kwargs["location"] = kwargs["location"]

        self.client = genai.Client(**client_kwargs)
        self.model = model
        self.cache_ttl_seconds = cache_ttl_seconds
        self.thinking_level = thinking_level
        self.media_resolution = media_resolution

        # PDF uploads storage
        self.uploaded_pdfs: Dict[Any, Any] = {}

        # Context caching state
        self._cached_content_name: Optional[str] = None
        self._cached_content_hash: Optional[str] = None
        self._cache_token_count: int = 0

    def load_pdfs(self, pdf_paths: list[Any]) -> dict[Any, Any]:
        """
        Upload PDFs to Gemini for native vision processing.

        Args:
            pdf_paths: List of paths to PDF files

        Returns:
            Dict mapping filename to uploaded file object
        """
        for pdf_path in pdf_paths:
            if pdf_path in self.uploaded_pdfs:
                continue

            with open(pdf_path, "rb") as f:
                uploaded = self.client.files.upload(
                    file=f,
                    config={
                        "mime_type": "application/pdf",
                        "display_name": pdf_path.name,
                    },
                )

            # Wait for processing
            while uploaded.state == "PROCESSING":
                time.sleep(2)
                if uploaded.name:
                    uploaded = self.client.files.get(name=uploaded.name)

            if uploaded.state == "ACTIVE":
                self.uploaded_pdfs[pdf_path] = uploaded

        return self.uploaded_pdfs

    def create_kb_cache(
        self,
        kb_context: str,
        system_instruction: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create or reuse a cached context for knowledge base content.

        This implements Gemini's explicit context caching feature, which
        provides 75% cost savings on cached tokens for subsequent requests.

        Args:
            kb_context: Knowledge base content to cache
            system_instruction: Optional system instruction to include
            display_name: Optional display name for the cache

        Returns:
            Cache name if created/reused, None if caching disabled or failed
        """
        if not self.enable_caching:
            return None

        # Check minimum token threshold
        # Rough estimate: ~4 chars per token for English text
        estimated_tokens = len(kb_context) // 4
        min_tokens = self.MIN_CACHE_TOKENS.get(
            self.model, self.MIN_CACHE_TOKENS["default"]
        )

        if estimated_tokens < min_tokens:
            # Content too small for caching benefit
            return None

        # Compute content hash to detect changes
        content_hash = hashlib.sha256(kb_context.encode()).hexdigest()[:16]

        # Reuse existing cache if content unchanged
        if self._cached_content_name and self._cached_content_hash == content_hash:
            # Try to refresh TTL on existing cache
            try:
                self.client.caches.update(
                    name=self._cached_content_name,
                    config=types.UpdateCachedContentConfig(
                        ttl=f"{self.cache_ttl_seconds}s"
                    ),
                )
                return self._cached_content_name
            except Exception:
                # Cache expired or invalid, will recreate
                self._cached_content_name = None

        # Build cache content - use cast for type compatibility
        cache_contents: List[types.Content] = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=kb_context)],
            )
        ]

        # Add uploaded PDFs to cache
        for pdf_file in self.uploaded_pdfs.values():
            cache_contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            file_data=types.FileData(
                                file_uri=pdf_file.uri,
                                mime_type="application/pdf",
                            )
                        )
                    ],
                )
            )

        # Create cache config
        # Cast contents to Any for SDK compatibility
        cache_config = types.CreateCachedContentConfig(
            display_name=display_name or f"kanoa-kb-{content_hash}",
            contents=cast(Any, cache_contents),
            ttl=f"{self.cache_ttl_seconds}s",
        )

        if system_instruction:
            cache_config.system_instruction = system_instruction

        try:
            # Create the cached content
            # Note: Model must use explicit version for caching
            cache_model = self._get_cache_model_name()
            cache = self.client.caches.create(
                model=cache_model,
                config=cache_config,
            )

            self._cached_content_name = cache.name
            self._cached_content_hash = content_hash

            # Store token count for cost calculation
            if hasattr(cache, "usage_metadata"):
                self._cache_token_count = getattr(
                    cache.usage_metadata, "total_token_count", 0
                )

            return cache.name

        except Exception as e:
            # Caching failed, fall back to non-cached
            print(f"⚠️ Context caching unavailable: {e}")
            return None

    def _get_cache_model_name(self) -> str:
        """
        Get the model name formatted for caching API.

        The caching API requires explicit model versions (e.g., gemini-2.0-flash-001).
        """
        # If model already has version suffix, use as-is
        if "-001" in self.model or "-002" in self.model:
            return f"models/{self.model}"

        # Map common model names to their cacheable versions
        model_mapping = {
            "gemini-3-pro-preview": "models/gemini-3-pro-preview",
            "gemini-2.5-pro": "models/gemini-2.5-pro-001",
            "gemini-2.5-flash": "models/gemini-2.5-flash-001",
            "gemini-2.0-flash": "models/gemini-2.0-flash-001",
        }

        return model_mapping.get(self.model, f"models/{self.model}")

    def clear_cache(self) -> None:
        """Delete the current cached context."""
        if self._cached_content_name:
            try:
                self.client.caches.delete(name=self._cached_content_name)
            except Exception:
                pass  # Cache may have already expired
            finally:
                self._cached_content_name = None
                self._cached_content_hash = None
                self._cache_token_count = 0

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
        Interpret using Gemini with optional context caching.

        When enable_caching is True and kb_context is provided, the KB
        content will be cached for subsequent requests, providing ~75%
        cost savings on cached tokens.
        """
        self.call_count += 1

        # Create or reuse KB cache if applicable
        cache_name: Optional[str] = None
        if kb_context and self.enable_caching:
            cache_name = self.create_kb_cache(kb_context)

        # Build content parts for the request
        content_parts = []

        # Add figure
        if fig is not None:
            img_data_str = self._fig_to_base64(fig)
            img_data = base64.b64decode(img_data_str)
            content_parts.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_bytes(data=img_data, mime_type="image/png")],
                )
            )

        # Add data
        if data is not None:
            data_text = self._data_to_text(data)
            content_parts.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=f"Data to analyze:\n```\n{data_text}\n```"
                        )
                    ],
                )
            )

        # Add PDFs if available and NOT using cache
        # (if using cache, PDFs are already in the cached content)
        if not cache_name:
            for pdf_file in self.uploaded_pdfs.values():
                content_parts.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                file_data=types.FileData(
                                    file_uri=pdf_file.uri, mime_type="application/pdf"
                                )
                            )
                        ],
                    )
                )

        # Build prompt (exclude KB context if using cache)
        prompt = self._build_prompt(
            context,
            focus,
            kb_context=None if cache_name else kb_context,
            custom_prompt=custom_prompt,
        )
        content_parts.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )

        # Call API
        try:
            # Build generation config
            generate_config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
            )

            # Use cached content if available
            if cache_name:
                generate_config.cached_content = cache_name

            response = self.client.models.generate_content(
                model=self.model,
                contents=cast(Any, content_parts),
                config=generate_config,
            )

            # Extract text
            interpretation = response.text or ""

            # Calculate usage with cache awareness
            usage = self._calculate_usage(response, cache_name is not None)

            # Add metadata
            interpretation += f"\n\n---\n*Generated by {self.model}*"
            if self.uploaded_pdfs:
                interpretation += f" *with {len(self.uploaded_pdfs)} PDF references*"
            if cache_name:
                interpretation += " *(KB cached)*"

            return InterpretationResult(
                text=interpretation,
                backend="gemini-3",
                usage=usage,
                metadata={
                    "model": self.model,
                    "pdf_count": len(self.uploaded_pdfs),
                    "cache_used": cache_name is not None,
                    "cache_name": cache_name,
                },
            )

        except Exception as e:
            error_msg = f"❌ **Error**: {str(e)}"
            return InterpretationResult(text=error_msg, backend="gemini-3", usage=None)

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build Gemini-optimized prompt."""
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

    def _calculate_usage(
        self, response: Any, cache_used: bool = False
    ) -> Optional[UsageInfo]:
        """
        Calculate token usage and cost, accounting for cached tokens.

        Args:
            response: Gemini API response object
            cache_used: Whether context caching was used for this request
        """
        # Extract token counts from response metadata
        usage_metadata = getattr(response, "usage_metadata", None)
        if not usage_metadata:
            return None

        input_tokens = usage_metadata.prompt_token_count
        output_tokens = usage_metadata.candidates_token_count

        # Check for cached tokens in response
        cached_tokens = getattr(usage_metadata, "cached_content_token_count", 0)

        # Calculate non-cached input tokens
        non_cached_input = input_tokens - cached_tokens

        # Determine pricing tier based on context length
        # Threshold is 200,000 tokens for Gemini 3.0 Pro
        if input_tokens <= 200_000:
            input_price = self.PRICING["input_short"]
            output_price = self.PRICING["output_short"]
        else:
            input_price = self.PRICING["input_long"]
            output_price = self.PRICING["output_long"]

        # Calculate cost
        # Cached tokens are charged at reduced rate
        if cached_tokens > 0:
            cached_cost = cached_tokens / 1_000_000 * self.PRICING["cached_input"]
            non_cached_cost = non_cached_input / 1_000_000 * input_price
            input_cost = cached_cost + non_cached_cost
        else:
            input_cost = input_tokens / 1_000_000 * input_price

        output_cost = output_tokens / 1_000_000 * output_price
        total_cost = input_cost + output_cost

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=total_cost,
            cached_tokens=cached_tokens if cached_tokens > 0 else None,
        )
