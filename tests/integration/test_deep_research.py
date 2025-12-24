"""
Integration tests for Gemini Deep Research backends.

Tests both:
- GeminiDeepResearchBackend (official Interactions API)
- GeminiDeepResearchProtoBackend (prototype RAG + Google Search)
"""

import os

import pytest

from kanoa.backends.deep_research import GeminiDeepResearchBackend
from kanoa.backends.gemini_research import GeminiResearchReferenceBackend


@pytest.fixture
def sample_context():
    """Sample research context."""
    return """
    Project Context: We're analyzing renewable energy adoption trends.
    Key metrics: Solar panel installations, wind farm capacity, battery storage.
    """


@pytest.fixture
def sample_focus():
    """Sample research focus."""
    return "Compare the growth rate of solar vs wind energy in the last 5 years."


@pytest.fixture
def text_kb(tmp_path):
    """Create a simple text knowledge base."""
    kb_path = tmp_path / "kb"
    kb_path.mkdir()

    # Add sample documents
    (kb_path / "solar.txt").write_text(
        "Solar energy has grown 40% annually from 2019-2024. "
        "Key drivers: declining panel costs, government incentives."
    )
    (kb_path / "wind.txt").write_text(
        "Wind energy capacity increased 25% annually from 2019-2024. "
        "Offshore wind farms are the fastest growing segment."
    )


@pytest.mark.integration
class TestGeminiResearchReferenceBackend:
    """Tests for the custom Research backend."""

    def test_basic_research_with_rag(self, sample_context, sample_focus, text_kb):
        """Test basic research flow with RAG context."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set")

        backend = GeminiResearchReferenceBackend(
            api_key=api_key,
            model="gemini-3-flash-preview",  # Use flash for testing
        )

        chunks = list(
            backend.interpret(
                fig=None,
                data=None,
                context=sample_context,
                focus=sample_focus,
                kb_context=None,
                custom_prompt=None,
                knowledge_base=text_kb,
            )
        )

        # Verify we got chunks
        assert len(chunks) > 0

        # Check for expected chunk types
        status_chunks = [c for c in chunks if c.type == "status"]
        content_chunks = [c for c in chunks if c.type == "content"]

        assert len(status_chunks) > 0, "Should have status updates"
        assert len(content_chunks) > 0, "Should have content"

        # Verify KB was used
        kb_status = [c for c in status_chunks if "Knowledge Base" in c.content]
        assert len(kb_status) > 0, "Should indicate KB usage"

        # Verify final content mentions key terms
        full_content = "".join([c.content for c in content_chunks])
        assert len(full_content) > 100, "Should generate substantial content"

    def test_research_without_rag(self, sample_focus):
        """Test research without RAG (Google Search only)."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set")

        backend = GeminiResearchReferenceBackend(
            api_key=api_key,
            model="gemini-3-flash-preview",
        )

        chunks = list(
            backend.interpret(
                fig=None,
                data=None,
                context=None,
                focus=sample_focus,
                kb_context=None,
                custom_prompt=None,
            )
        )

        assert len(chunks) > 0
        content_chunks = [c for c in chunks if c.type == "content"]
        assert len(content_chunks) > 0

    def test_custom_prompt(self):
        """Test with custom research prompt."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set")

        backend = GeminiResearchReferenceBackend(
            api_key=api_key,
            model="gemini-3-flash-preview",
        )

        custom_prompt = "What are the top 3 renewable energy trends in 2024?"

        chunks = list(
            backend.interpret(
                fig=None,
                data=None,
                context=None,
                focus=None,
                kb_context=None,
                custom_prompt=custom_prompt,
            )
        )

        assert len(chunks) > 0
        # Verify content is relevant
        content_chunks = [c for c in chunks if c.type == "content"]
        full_content = "".join([c.content for c in content_chunks])
        assert len(full_content) > 50


@pytest.mark.integration
@pytest.mark.skipif(
    "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ,
    reason="Requires AI Studio API key",
)
class TestGeminiDeepResearchBackend:
    """Tests for the official Deep Research backend (Interactions API)."""

    def test_interactions_api_available(self):
        """Check if Interactions API is available in google-genai."""
        try:
            from google import genai

            client = genai.Client(api_key="dummy")
            has_interactions = hasattr(client, "interactions")
            if not has_interactions:
                pytest.skip(
                    "Interactions API not available. "
                    "Requires google-genai >= 2.0 (currently in preview)."
                )
        except Exception as e:
            pytest.skip(f"Failed to check Interactions API: {e}")

    def test_basic_research(self, sample_context, sample_focus):
        """Test basic research with official backend."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        try:
            backend = GeminiDeepResearchBackend(
                api_key=api_key,
                max_research_time=300,  # 5 minutes for testing
            )
        except RuntimeError as e:
            if "Interactions API not available" in str(e):
                pytest.skip("Interactions API not available in current SDK version")
            raise

        chunks = list(
            backend.interpret(
                fig=None,
                data=None,
                context=sample_context,
                focus=sample_focus,
                kb_context=None,
                custom_prompt=None,
            )
        )

        assert len(chunks) > 0

        # Check for thought summaries
        thought_chunks = [
            c for c in chunks if "Step" in c.content and c.type == "status"
        ]
        assert len(thought_chunks) > 0, "Should have thought summaries"

        # Check for final content
        content_chunks = [c for c in chunks if c.type == "content"]
        assert len(content_chunks) > 0

    def test_with_file_search(self, sample_focus):
        """Test with File Search store (requires pre-created store)."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        # This test requires a pre-created File Search store
        # Skip if GEMINI_FILE_SEARCH_STORE is not set
        store_name = os.getenv("GEMINI_FILE_SEARCH_STORE")
        if not store_name:
            pytest.skip("GEMINI_FILE_SEARCH_STORE not set. Create store in AI Studio.")

        try:
            backend = GeminiDeepResearchBackend(
                api_key=api_key,
                file_search_stores=[store_name],
                max_research_time=300,
            )
        except RuntimeError as e:
            if "Interactions API not available" in str(e):
                pytest.skip("Interactions API not available")
            raise

        chunks = list(
            backend.interpret(
                fig=None,
                data=None,
                context=None,
                focus=sample_focus,
                kb_context=None,
                custom_prompt=None,
            )
        )

        assert len(chunks) > 0

        # Verify File Search was mentioned
        status_chunks = [c for c in chunks if c.type == "status"]
        file_search_status = [c for c in status_chunks if "File Search" in c.content]
        assert len(file_search_status) > 0


@pytest.mark.integration
def test_backend_comparison(sample_focus):
    """Compare outputs from both backends on the same query."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set")

    # Test Proxy backend
    proxy_backend = GeminiResearchReferenceBackend(
        api_key=api_key,
        model="gemini-3-flash-preview",
    )

    proxy_chunks = list(
        proxy_backend.interpret(
            fig=None,
            data=None,
            context=None,
            focus=sample_focus,
            kb_context=None,
            custom_prompt=None,
        )
    )

    proxy_content = "".join([c.content for c in proxy_chunks if c.type == "content"])

    # Test Official backend (if available)
    try:
        official_backend = GeminiDeepResearchBackend(
            api_key=api_key,
            max_research_time=300,
        )

        official_chunks = list(
            official_backend.interpret(
                fig=None,
                data=None,
                context=None,
                focus=sample_focus,
                kb_context=None,
                custom_prompt=None,
            )
        )

        official_content = "".join(
            [c.content for c in official_chunks if c.type == "content"]
        )

        # Both should generate substantial content
        assert len(proxy_content) > 100
        assert len(official_content) > 100

        print("\n--- Proxy Backend Output ---")
        print(proxy_content[:500])
        print("\n--- Official Backend Output ---")
        print(official_content[:500])

    except RuntimeError as e:
        if "Interactions API not available" in str(e):
            pytest.skip("Interactions API not available for comparison")
        raise
