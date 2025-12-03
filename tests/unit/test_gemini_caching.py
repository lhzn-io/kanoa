"""Tests for Gemini context caching functionality."""

from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from kanoa.backends.gemini import GeminiBackend
from kanoa.core.types import InterpretationResult


class TestGeminiContextCaching:
    """Tests for Gemini context caching."""

    @pytest.fixture
    def mock_genai(self) -> Any:
        with patch("kanoa.backends.gemini.genai") as mock_genai:
            with patch("kanoa.backends.gemini.types") as mock_types:
                # Make types work normally by returning MagicMocks
                mock_types.Content.return_value = MagicMock()
                mock_types.Part.from_text.return_value = MagicMock()
                mock_types.CreateCachedContentConfig.return_value = MagicMock()
                mock_types.UpdateCachedContentConfig.return_value = MagicMock()
                mock_types.GenerateContentConfig.return_value = MagicMock()
                yield mock_genai

    def test_cache_created_for_large_kb(self, mock_genai: Any) -> None:
        """Test that cache is created when KB content is large enough."""
        backend = GeminiBackend(api_key="test_key", enable_caching=True)

        # Mock cache creation with usage_metadata
        mock_cache = MagicMock()
        mock_cache.name = "caches/test-cache-123"
        mock_usage = MagicMock()
        mock_usage.total_token_count = 3000
        mock_cache.usage_metadata = mock_usage
        cast("Any", backend.client.caches.create).return_value = mock_cache
        cast("Any", backend.client.caches.list).return_value = []

        # KB content needs to be > 2048 tokens for gemini-3-pro-preview
        # (~4 chars per token, so ~8192 chars needed)
        large_kb = "Test content with some words. " * 400  # ~12000 chars, ~3000 tokens

        result = backend.create_kb_cache(large_kb)

        assert result.name == "caches/test-cache-123"
        assert result.created is True
        assert backend._cached_content_name == "caches/test-cache-123"
        cast("Any", backend.client.caches.create).assert_called_once()

    def test_cache_not_created_for_small_kb(self, mock_genai: Any) -> None:
        """Test that cache is not created when KB content is too small."""
        backend = GeminiBackend(api_key="test_key", enable_caching=True)

        # Small KB content (< 1024 tokens)
        small_kb = "Short content."

        result = backend.create_kb_cache(small_kb)

        assert result.name is None
        assert result.created is False
        cast("Any", backend.client.caches.create).assert_not_called()

    def test_cache_disabled(self, mock_genai: Any) -> None:
        """Test that caching is skipped when disabled."""
        backend = GeminiBackend(api_key="test_key", enable_caching=False)

        large_kb = "Test content. " * 500

        result = backend.create_kb_cache(large_kb)

        assert result.name is None
        assert result.created is False
        cast("Any", backend.client.caches.create).assert_not_called()

    def test_cache_reused_for_same_content(self, mock_genai: Any) -> None:
        """Test that cache is reused when content hash matches."""
        backend = GeminiBackend(api_key="test_key", enable_caching=True)

        # Mock cache creation with usage_metadata
        mock_cache = MagicMock()
        mock_cache.name = "caches/test-cache-123"
        mock_usage = MagicMock()
        mock_usage.total_token_count = 3000
        mock_cache.usage_metadata = mock_usage
        cast("Any", backend.client.caches.create).return_value = mock_cache
        cast("Any", backend.client.caches.list).return_value = []

        # Large enough for caching (> 2048 tokens for gemini-3-pro-preview)
        large_kb = "Test content with some words. " * 400

        # First call - creates cache
        result1 = backend.create_kb_cache(large_kb)
        assert result1.name == "caches/test-cache-123"
        assert result1.created is True
        assert cast("Any", backend.client.caches.create).call_count == 1

        # Second call with same content - reuses cache (updates TTL)
        result2 = backend.create_kb_cache(large_kb)
        assert result2.name == "caches/test-cache-123"
        assert result2.created is False
        # Cache should be updated, not created again
        assert cast("Any", backend.client.caches.create).call_count == 1
        cast("Any", backend.client.caches.update).assert_called()

    def test_cache_recreated_for_different_content(self, mock_genai: Any) -> None:
        """Test that cache is recreated when content changes."""
        backend = GeminiBackend(api_key="test_key", enable_caching=True)

        # Mock cache creation with usage_metadata
        mock_cache1 = MagicMock()
        mock_cache1.name = "caches/cache-1"
        mock_usage1 = MagicMock()
        mock_usage1.total_token_count = 3000
        mock_cache1.usage_metadata = mock_usage1

        mock_cache2 = MagicMock()
        mock_cache2.name = "caches/cache-2"
        mock_usage2 = MagicMock()
        mock_usage2.total_token_count = 3000
        mock_cache2.usage_metadata = mock_usage2

        cast("Any", backend.client.caches.create).side_effect = [
            mock_cache1,
            mock_cache2,
        ]
        cast("Any", backend.client.caches.list).return_value = []

        # Large enough for caching (> 2048 tokens for gemini-3-pro-preview)
        kb1 = "First content with some extra words here. " * 400
        kb2 = "Different content with other words here. " * 400

        # First call
        result1 = backend.create_kb_cache(kb1)
        assert result1.name == "caches/cache-1"
        assert result1.created is True

        # Simulate cache update failure (expired cache)
        cast("Any", backend.client.caches.update).side_effect = Exception(
            "Cache expired"
        )

        # Second call with different content
        result2 = backend.create_kb_cache(kb2)
        assert result2.name == "caches/cache-2"
        assert result2.created is True
        assert cast("Any", backend.client.caches.create).call_count == 2

    def test_clear_cache(self, mock_genai: Any) -> None:
        """Test cache deletion clears internal state."""
        backend = GeminiBackend(api_key="test_key", enable_caching=True)
        backend._cached_content_name = "caches/test-cache"
        backend._cached_content_hash = "abc123"
        backend._cache_token_count = 1000

        backend.clear_cache()

        # Verify cache state was cleared
        name_cleared = backend._cached_content_name is None
        hash_cleared = backend._cached_content_hash is None
        count_cleared = backend._cache_token_count == 0
        assert name_cleared
        assert hash_cleared
        assert count_cleared

    def test_interpret_uses_cache(self, mock_genai: Any) -> None:
        """Test that interpret() uses cached content when available."""
        backend = GeminiBackend(api_key="test_key", enable_caching=True)

        # Mock cache creation with usage_metadata
        mock_cache = MagicMock()
        mock_cache.name = "caches/kb-cache"
        mock_usage = MagicMock()
        mock_usage.total_token_count = 3000
        mock_cache.usage_metadata = mock_usage
        cast("Any", backend.client.caches.create).return_value = mock_cache
        cast("Any", backend.client.caches.list).return_value = []

        # Mock generate response
        mock_response = MagicMock()
        mock_response.text = "Cached interpretation"
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.cached_content_token_count = 80
        cast("Any", backend.client.models.generate_content).return_value = mock_response

        # Large enough for caching (> 2048 tokens for gemini-3-pro-preview)
        large_kb = "Knowledge base content with enough words. " * 400

        result = backend.interpret(
            fig=None,
            data="Test data",
            context=None,
            focus=None,
            kb_context=large_kb,
            custom_prompt=None,
        )

        assert isinstance(result, InterpretationResult)
        assert "Cached interpretation" in result.text
        assert result.metadata is not None
        assert result.metadata["cache_used"] is True
        assert result.metadata["cache_created"] is True  # First usage creates cache
        assert result.metadata["cache_name"] == "caches/kb-cache"

    def test_usage_with_cached_tokens(self, mock_genai: Any) -> None:
        """Test usage calculation includes cached token savings."""
        backend = GeminiBackend(api_key="test_key")

        mock_response = MagicMock()
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 10000
        mock_response.usage_metadata.candidates_token_count = 500
        mock_response.usage_metadata.cached_content_token_count = 8000

        # Scenario 1: Cache Hit (discounted)
        usage_hit = backend._calculate_usage(
            mock_response, cache_used=True, cache_created=False
        )

        assert usage_hit is not None
        assert usage_hit.input_tokens == 10000
        assert usage_hit.output_tokens == 500
        assert usage_hit.cached_tokens == 8000
        # Cost should be reduced due to cached tokens
        # 8000 cached @ $0.50/1M + 2000 non-cached @ $2.00/1M + 500 output @ $12/1M
        expected_cost_hit = (
            (8000 / 1_000_000 * 0.50)
            + (2000 / 1_000_000 * 2.00)
            + (500 / 1_000_000 * 12.00)
        )
        assert abs(usage_hit.cost - expected_cost_hit) < 0.0001

        # Scenario 2: Cache Creation (full price)
        usage_creation = backend._calculate_usage(
            mock_response, cache_used=True, cache_created=True
        )

        assert usage_creation is not None
        assert usage_creation.input_tokens == 10000
        assert usage_creation.cached_tokens == 8000
        # Cost should be FULL price for all input tokens
        # 10000 input @ $2.00/1M + 500 output @ $12/1M
        expected_cost_creation = (10000 / 1_000_000 * 2.00) + (500 / 1_000_000 * 12.00)
        assert abs(usage_creation.cost - expected_cost_creation) < 0.0001
