import base64
import hashlib
import os
import time
from typing import Any, Dict, List, Optional, cast

import matplotlib.pyplot as plt
from google import genai
from google.genai import types

from ..config import options
from ..core.token_guard import BaseTokenCounter, TokenCheckResult, TokenGuard
from ..core.types import CacheCreationResult, InterpretationResult, UsageInfo
from ..pricing import get_model_pricing
from ..utils.logging import ilog_debug, ilog_info, ilog_warning
from .base import BaseBackend


class GeminiTokenCounter(BaseTokenCounter):
    """Token counter for Google Gemini models."""

    def __init__(self, client: Any, model: str = "gemini-3-pro-preview"):
        """
        Initialize Gemini token counter.

        Args:
            client: google.genai.Client instance
            model: Model name for token counting
        """
        self._client = client
        self._model = model

    @property
    def backend_name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return self._model

    def count_tokens(self, contents: Any) -> int:
        """
        Count tokens using Gemini API.

        Args:
            contents: Content to count (text, list of Content objects, etc.)

        Returns:
            Token count
        """
        try:
            result = self._client.models.count_tokens(
                model=self._model,
                contents=contents,
            )
            return int(result.total_tokens)
        except Exception as e:
            ilog_warning(
                f"Gemini token counting failed, using estimate: {e}",
                source="kanoa.backends.gemini",
            )
            return self.estimate_tokens(contents)


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

    # Minimum token counts for context caching by model
    MIN_CACHE_TOKENS = {
        "gemini-3-pro-preview": 2048,
        "gemini-2.5-pro": 4096,
        "gemini-2.5-flash": 1024,
        "default": 1024,
    }

    @property
    def backend_name(self) -> str:
        """Return the backend name."""
        return "gemini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-pro-preview",
        max_tokens: int = 3000,
        enable_caching: bool = True,
        cache_ttl_seconds: int = 3600,
        thinking_level: str = "high",
        media_resolution: str = "medium",
        verbose: Optional[int] = None,
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
            verbose: Verbosity level (0=Silent, 1=Info, 2=Debug)
            **kwargs: Additional args (project, location for Vertex AI)
        """
        super().__init__(api_key, max_tokens, enable_caching)

        # Normalize verbosity
        _v = verbose if verbose is not None else options.verbose
        if _v is True:
            self.verbose = 1
        elif _v is False or _v is None:
            self.verbose = 0
        else:
            self.verbose = int(_v)

        ilog_info(
            f"Authenticating with Google Cloud (Model: {model})...",
            source="kanoa.backends.gemini",
            context={"model": model, "backend": "gemini"},
        )

        # Initialize client with support for both AI Studio and Vertex AI
        client_kwargs: Dict[str, Any] = {}
        self.is_vertex = False
        if api_key or os.environ.get("GOOGLE_API_KEY"):
            client_kwargs["api_key"] = api_key or os.environ.get("GOOGLE_API_KEY")
        else:
            # Fallback to Vertex AI if no API key (uses ADC)
            self.is_vertex = True
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
            Dict mapping filename to uploaded file object or inline data
        """
        ilog_info(
            f"Found {len(pdf_paths)} PDFs to process...",
            source="kanoa.backends.gemini",
            context={"pdf_count": len(pdf_paths)},
        )

        for pdf_path in pdf_paths:
            if pdf_path in self.uploaded_pdfs:
                ilog_info(
                    f"PDF already loaded: {pdf_path.name}",
                    source="kanoa.backends.gemini",
                    context={"file": str(pdf_path.name)},
                )
                continue

            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            ilog_info(
                f"Processing PDF: {pdf_path.name} ({file_size_mb:.2f} MB)",
                source="kanoa.backends.gemini",
                context={"file": str(pdf_path.name), "size_mb": round(file_size_mb, 2)},
            )

            # If using Vertex AI, skip File API and go straight to inline
            if self.is_vertex:
                ilog_info(
                    "Using inline transfer (Vertex AI)...",
                    source="kanoa.backends.gemini",
                )
                with open(pdf_path, "rb") as f:
                    data = f.read()
                self.uploaded_pdfs[pdf_path] = {
                    "mime_type": "application/pdf",
                    "data": data,
                    "inline": True,
                }
                continue

            try:
                ilog_info(
                    "Attempting upload via File API...",
                    source="kanoa.backends.gemini",
                )
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
                    ilog_info(
                        "Waiting for remote processing...",
                        source="kanoa.backends.gemini",
                    )
                    time.sleep(2)
                    if uploaded.name:
                        uploaded = self.client.files.get(name=uploaded.name)

                if uploaded.state == "ACTIVE":
                    ilog_info(
                        f"Upload complete: {uploaded.name}",
                        source="kanoa.backends.gemini",
                        context={"file_id": uploaded.name},
                    )
                    self.uploaded_pdfs[pdf_path] = uploaded

            except ValueError as e:
                if "Gemini Developer client" in str(e):
                    ilog_warning(
                        "AI Studio File API unavailable (Consumer). "
                        "Switching to Vertex AI inline strategy (Enterprise).",
                        title="File API Fallback",
                        source="kanoa.backends.gemini",
                    )
                    # Fallback for Vertex AI: Read file bytes for inline transfer
                    with open(pdf_path, "rb") as f:
                        data = f.read()
                    # Store as a simple object mimicking the needed interface
                    self.uploaded_pdfs[pdf_path] = {
                        "mime_type": "application/pdf",
                        "data": data,
                        "inline": True,
                    }
                    ilog_info(
                        f"Loaded {len(data)} bytes for inline transfer.",
                        source="kanoa.backends.gemini",
                        context={"bytes": len(data)},
                    )
                else:
                    raise e

        return self.uploaded_pdfs

    def check_kb_cost(self) -> Optional[TokenCheckResult]:
        """
        Check the cost/token count of the currently uploaded PDFs.

        Returns:
            TokenCheckResult with token count and estimated cost.
        """
        if not self.uploaded_pdfs:
            return None

        # Initialize TokenGuard with Gemini counter
        counter = GeminiTokenCounter(self.client, model=self.model)
        guard = TokenGuard(counter)

        # Prepare content for counting
        pdf_contents = []
        for pdf_file in self.uploaded_pdfs.values():
            if isinstance(pdf_file, dict) and pdf_file.get("inline"):
                # Handle inline data (Vertex AI fallback)
                part = types.Part.from_bytes(
                    data=pdf_file["data"], mime_type=pdf_file["mime_type"]
                )
            else:
                # Handle uploaded file (AI Studio)
                part = types.Part(
                    file_data=types.FileData(
                        file_uri=pdf_file.uri,
                        mime_type="application/pdf",
                    )
                )

            pdf_contents.append(
                types.Content(
                    role="user",
                    parts=[part],
                )
            )

        # Check tokens using the guard
        pricing = get_model_pricing("gemini", self.model)
        return guard.check(pdf_contents, pricing=pricing)

    def encode_kb(self, kb_manager: Any) -> Optional[str]:
        """
        Encode knowledge base for Gemini backend.

        Strategy:
        - PDFs: Upload via native File API (best quality)
        - Text: Concatenate into prompt
        - Images: Upload via File API

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

        # Upload PDFs if present
        pdf_paths = kb_manager.get_pdf_paths()
        if pdf_paths:
            self.load_pdfs(pdf_paths)

        # For now, return text content
        # PDFs are handled separately via uploaded_pdfs
        return text_content or None

    def _compute_cache_hash(self, kb_context: str) -> str:
        """Compute deterministic hash for KB context + uploaded PDFs."""
        # Start with KB context (text)
        hasher = hashlib.sha256(kb_context.encode())

        # Include PDF content hashes to detect any file changes
        if self.uploaded_pdfs:
            # Sort paths to ensure deterministic order
            sorted_paths = sorted(self.uploaded_pdfs.keys(), key=lambda p: p.name)

            for pdf_path in sorted_paths:
                try:
                    # Read file content to update hash
                    with open(pdf_path, "rb") as f:
                        # Read in chunks to handle large files efficiently
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                except OSError:
                    # Fallback: hash filename + size if file unreadable
                    try:
                        identifier = f"{pdf_path.name}:{pdf_path.stat().st_size}"
                    except OSError:
                        identifier = pdf_path.name
                    hasher.update(identifier.encode())

        return hasher.hexdigest()[:16]

    def get_cache_status(self, kb_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Check status of the context cache for the given KB content.

        Returns:
            Dict with keys: 'exists', 'name', 'hash', 'token_count', 'source'
        """
        if not kb_context:
            return {"exists": False, "reason": "No KB context provided"}

        content_hash = self._compute_cache_hash(kb_context)
        target_display_name = f"kanoa-kb-{content_hash}"

        # 1. Check in-memory
        if self._cached_content_name and self._cached_content_hash == content_hash:
            return {
                "exists": True,
                "source": "memory",
                "name": self._cached_content_name,
                "hash": content_hash,
                "token_count": self._cache_token_count,
            }

        # 2. Check server
        try:
            # List caches (returns iterator)
            for cache in self.client.caches.list():
                if getattr(cache, "display_name", "") == target_display_name:
                    tokens = 0
                    if hasattr(cache, "usage_metadata"):
                        tokens = getattr(cache.usage_metadata, "total_token_count", 0)

                    return {
                        "exists": True,
                        "source": "server",
                        "name": cache.name,
                        "hash": content_hash,
                        "token_count": tokens,
                        "expire_time": str(getattr(cache, "expire_time", "unknown")),
                    }
        except Exception as e:
            return {"exists": False, "error": str(e)}

        return {"exists": False, "hash": content_hash, "reason": "Not found"}

    def create_kb_cache(
        self,
        kb_context: str,
        system_instruction: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> CacheCreationResult:
        """
        Create or reuse a cached context for knowledge base content.

        This implements Gemini's explicit context caching feature, which
        provides 75% cost savings on cached tokens for subsequent requests.

        Args:
            kb_context: Knowledge base content to cache
            system_instruction: Optional system instruction to include
            display_name: Optional display name for the cache

        Returns:
            CacheCreationResult object containing:
            - name: Cache name if created/reused, None if caching disabled
            - created: True if cache was newly created (miss), False if reused (hit)
        """
        if not self.enable_caching:
            return CacheCreationResult(name=None, created=False, token_count=0)

        # Check minimum token threshold
        # Rough estimate: ~4 chars per token for English text
        estimated_tokens = len(kb_context) // 4
        min_tokens = self.MIN_CACHE_TOKENS.get(
            self.model, self.MIN_CACHE_TOKENS["default"]
        )

        # If we have PDFs, we assume the content is large enough for caching
        # (PDFs are usually > 2048 tokens)
        if estimated_tokens < min_tokens and not self.uploaded_pdfs:
            # Content too small for caching benefit
            ilog_info(
                f"Content too small for caching (~{estimated_tokens} tokens < {min_tokens})",
                source="kanoa.backends.gemini",
                context={
                    "estimated_tokens": estimated_tokens,
                    "min_tokens": min_tokens,
                },
            )
            return CacheCreationResult(name=None, created=False, token_count=0)

        # Compute content hash to detect changes (Text + PDFs)
        content_hash = self._compute_cache_hash(kb_context)
        target_display_name = display_name or f"kanoa-kb-{content_hash}"

        ilog_info(
            f"Checking context cache (Hash: {content_hash})",
            title="Cache Check",
            source="kanoa.backends.gemini",
            context={"hash": content_hash},
        )

        # 1. Check in-memory reference (fastest)
        if self._cached_content_name and self._cached_content_hash == content_hash:
            # Try to refresh TTL on existing cache
            try:
                ilog_info(
                    f"Cache hit (Memory)! Refreshing TTL for {self._cached_content_name}",
                    title="Cache Hit",
                    source="kanoa.backends.gemini",
                    context={
                        "cache_name": self._cached_content_name,
                        "source": "memory",
                    },
                )
                self.client.caches.update(
                    name=self._cached_content_name,
                    config=types.UpdateCachedContentConfig(
                        ttl=f"{self.cache_ttl_seconds}s"
                    ),
                )
                return CacheCreationResult(
                    name=self._cached_content_name,
                    created=False,
                    token_count=self._cache_token_count,
                )
            except Exception:
                # Cache expired or invalid, will recreate
                ilog_warning(
                    "Cache expired or invalid. Recreating...",
                    title="Cache Miss",
                    source="kanoa.backends.gemini",
                )
                self._cached_content_name = None

        # 2. Check server-side for existing cache (Resilient Caching)
        # This allows reusing cache across kernel restarts
        try:
            ilog_info(
                f"Checking server for existing cache: {target_display_name}...",
                source="kanoa.backends.gemini",
            )

            # List caches (returns iterator)
            # We iterate to find a match by display_name
            for cache in self.client.caches.list():
                if getattr(cache, "display_name", "") == target_display_name:
                    if not cache.name:
                        continue

                    ilog_info(
                        f"Cache hit (Server)! Recovered {cache.name}",
                        title="Cache Hit",
                        source="kanoa.backends.gemini",
                        context={"cache_name": cache.name, "source": "server"},
                    )

                    # Update TTL to keep it alive
                    self.client.caches.update(
                        name=cache.name,
                        config=types.UpdateCachedContentConfig(
                            ttl=f"{self.cache_ttl_seconds}s"
                        ),
                    )

                    # Update in-memory state
                    self._cached_content_name = cache.name
                    self._cached_content_hash = content_hash
                    if hasattr(cache, "usage_metadata"):
                        self._cache_token_count = getattr(
                            cache.usage_metadata, "total_token_count", 0
                        )

                    return CacheCreationResult(
                        name=cache.name,
                        created=False,
                        token_count=self._cache_token_count,
                    )
        except Exception as e:
            ilog_warning(
                f"Failed to check server caches: {e}",
                source="kanoa.backends.gemini",
                context={"error": str(e)},
            )

        # 3. Create new cache (if not found)
        # Build cache content - use cast for type compatibility
        cache_contents: List[types.Content] = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=kb_context)],
            )
        ]

        # Add uploaded PDFs to cache
        for pdf_file in self.uploaded_pdfs.values():
            if isinstance(pdf_file, dict) and pdf_file.get("inline"):
                # Handle inline data (Vertex AI fallback)
                part = types.Part.from_bytes(
                    data=pdf_file["data"], mime_type=pdf_file["mime_type"]
                )
            else:
                # Handle uploaded file (AI Studio)
                part = types.Part(
                    file_data=types.FileData(
                        file_uri=pdf_file.uri,
                        mime_type="application/pdf",
                    )
                )

            cache_contents.append(
                types.Content(
                    role="user",
                    parts=[part],
                )
            )

        # Create cache config
        # Cast contents to Any for SDK compatibility
        cache_config = types.CreateCachedContentConfig(
            display_name=target_display_name,
            contents=cast("Any", cache_contents),
            ttl=f"{self.cache_ttl_seconds}s",
        )

        if system_instruction:
            cache_config.system_instruction = system_instruction

        try:
            # Create the cached content
            # Note: Model must use explicit version for caching
            cache_model = self._get_cache_model_name()
            ilog_info(
                f"Creating new cache on {cache_model}...",
                source="kanoa.backends.gemini",
                context={"model": cache_model},
            )

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

            ilog_info(
                f"Cache created: {cache.name} ({self._cache_token_count:,} tokens)",
                title="✓ Cache Created",
                source="kanoa.backends.gemini",
                context={
                    "cache_name": cache.name,
                    "token_count": self._cache_token_count,
                },
            )

            return CacheCreationResult(
                name=cache.name, created=True, token_count=self._cache_token_count
            )

        except Exception as e:
            # Caching failed, fall back to non-cached
            ilog_warning(
                f"Context caching unavailable: {e}",
                source="kanoa.backends.gemini",
                context={"error": str(e)},
            )
            return CacheCreationResult(name=None, created=False, token_count=0)

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
        cache_created: bool = False
        if kb_context and self.enable_caching:
            cache_result = self.create_kb_cache(kb_context)
            cache_name = cache_result.name
            cache_created = cache_result.created

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
                if isinstance(pdf_file, dict) and pdf_file.get("inline"):
                    # Handle inline data (Vertex AI fallback)
                    part = types.Part.from_bytes(
                        data=pdf_file["data"], mime_type=pdf_file["mime_type"]
                    )
                else:
                    # Handle uploaded file (AI Studio)
                    part = types.Part(
                        file_data=types.FileData(
                            file_uri=pdf_file.uri, mime_type="application/pdf"
                        )
                    )

                content_parts.append(
                    types.Content(
                        role="user",
                        parts=[part],
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
            if self.verbose >= 1:
                ilog_info(f"Generating content with {self.model}...")

            # Build generation config
            generate_config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
            )

            # Use cached content if available
            if cache_name:
                if self.verbose >= 1:
                    ilog_info(f"Using cached context: {cache_name}", title="Cache")
                generate_config.cached_content = cache_name

            # Level 2: Full Request Logging
            if self.verbose >= 2:
                ilog_debug(f"Model: {self.model}", title="Request")
                ilog_debug(f"Config: {generate_config}")
                ilog_debug(f"Contents: {len(content_parts)} parts")
                for _i, content in enumerate(content_parts):
                    if not content.parts:
                        continue
                    for part in content.parts:
                        if part.text:
                            text_preview = part.text[:100].replace("\n", "\\n")
                            preview_msg = (
                                f'Text: "{text_preview}..."'
                                if len(part.text) > 100
                                else f'Text: "{text_preview}"'
                            )
                            ilog_debug(preview_msg)
                        elif part.inline_data and part.inline_data.data:
                            data_bytes = part.inline_data.data
                            data_len = len(data_bytes)
                            size_str = (
                                f"{data_len / (1024 * 1024):.2f} MB"
                                if data_len > 1024 * 1024
                                else f"{data_len / 1024:.2f} KB"
                            )
                            ilog_debug(
                                f"Blob: {part.inline_data.mime_type} | {size_str}"
                            )
                        elif part.file_data:
                            ilog_debug(
                                f"File: {part.file_data.file_uri} ({part.file_data.mime_type})"
                            )

            # Call API with retry logic for 429s
            max_retries = 3
            retry_delay = 2
            response = None
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=cast("Any", content_parts),
                        config=generate_config,
                    )
                    break  # Success
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    # Check for 429 Resource Exhausted
                    if (
                        "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
                    ) and attempt < max_retries:
                        if self.verbose:
                            print(
                                f"  ⚠️ Resource limit hit (429). Retrying in {retry_delay}s... ({attempt + 1}/{max_retries})"
                            )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    raise e  # Re-raise other errors or if retries exhausted

            if not response:
                raise last_error or Exception("Unknown error during generation")

            # Level 2: Full Response Logging
            if self.verbose >= 2:
                ilog_debug("Response received", title="Response")
                # Try to dump full JSON if available, else string repr
                try:
                    # Pydantic v2 style
                    response_json = response.model_dump_json(indent=2)
                    ilog_debug(f"Payload: {response_json[:500]}...")
                except AttributeError:
                    ilog_debug(f"Payload: {str(response)[:500]}...")

            # Extract text
            interpretation = response.text or ""

            # Calculate usage with cache awareness
            usage = self._calculate_usage(
                response, cache_name is not None, cache_created
            )

            if self.verbose >= 1 and usage:
                ilog_info(
                    f"Usage: {usage.input_tokens:,} in / {usage.output_tokens:,} out"
                )
                if usage.cached_tokens:
                    ilog_info(f"Cached tokens: {usage.cached_tokens:,}")

            return InterpretationResult(
                text=interpretation,
                backend="gemini",
                usage=usage,
                metadata={
                    "model": self.model,
                    "pdf_count": len(self.uploaded_pdfs),
                    "cache_used": cache_name is not None,
                    "cache_created": cache_created,
                    "cache_name": cache_name,
                },
            )

        except Exception as e:
            error_msg = f"❌ **Error**: {e!s}"
            return InterpretationResult(text=error_msg, backend="gemini", usage=None)

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
        self, response: Any, cache_used: bool = False, cache_created: bool = False
    ) -> Optional[UsageInfo]:
        """
        Calculate token usage and cost, accounting for cached tokens.

        Args:
            response: Gemini API response object
            cache_used: Whether context caching was used for this request
            cache_created: Whether the cache was newly created (vs reused)
        """
        # Extract token counts from response metadata
        usage_metadata = getattr(response, "usage_metadata", None)
        if not usage_metadata:
            return None

        input_tokens = getattr(usage_metadata, "prompt_token_count", None)
        output_tokens = getattr(usage_metadata, "candidates_token_count", None)

        # Handle missing token counts
        if input_tokens is None or output_tokens is None:
            return None

        # Check for cached tokens in response
        cached_tokens = getattr(usage_metadata, "cached_content_token_count", 0) or 0

        # Calculate non-cached input tokens
        non_cached_input = input_tokens - cached_tokens

        # Get pricing for this model
        pricing = get_model_pricing("gemini", self.model)
        if not pricing:
            # Fallback if no pricing found (e.g. unknown model)
            return UsageInfo(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=0.0,
                cached_tokens=cached_tokens if cached_tokens > 0 else None,
                cache_created=cache_created,
                savings=None,
            )

        # Determine pricing tier based on context length
        # Threshold is 128k tokens for most Gemini models (was 200k for 3.0 preview)
        # We'll use the 128k keys from pricing.json if available
        if input_tokens <= 128_000:
            input_price = pricing.get("input_price", 0.0)
            output_price = pricing.get("output_price", 0.0)
        else:
            input_price = pricing.get(
                "input_price_128k", pricing.get("input_price", 0.0)
            )
            output_price = pricing.get(
                "output_price_128k", pricing.get("output_price", 0.0)
            )

        # Calculate cost
        # Cached tokens are charged at reduced rate ONLY if it's a cache hit
        # If we just created the cache, we pay full price for processing
        savings = None
        if cached_tokens > 0 and not cache_created:
            cached_price = pricing.get("cached_input_price", 0.0)
            cached_cost = cached_tokens / 1_000_000 * cached_price
            non_cached_cost = non_cached_input / 1_000_000 * input_price
            input_cost = cached_cost + non_cached_cost

            # Calculate savings
            full_cost_for_cached = cached_tokens / 1_000_000 * input_price
            savings = full_cost_for_cached - cached_cost
        else:
            # Cache creation (miss) or no cache used -> full price
            input_cost = input_tokens / 1_000_000 * input_price

        output_cost = output_tokens / 1_000_000 * output_price
        total_cost = input_cost + output_cost

        return UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=total_cost,
            cached_tokens=cached_tokens if cached_tokens > 0 else None,
            cache_created=cache_created,
            savings=savings,
        )
