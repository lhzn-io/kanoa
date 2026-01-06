"""
Integration tests for Gemini Deep Research backends.

Tests both:
- GeminiDeepResearchBackend (official Interactions API)
- GeminiResearchReferenceBackend (prototype RAG + Google Search)
"""

import os

import pytest

from kanoa.backends.gemini_deep_research import GeminiDeepResearchBackend


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

    # Return a proper KB object following the pattern from test_example_custom_research.py
    from kanoa.knowledge_base.base import BaseKnowledgeBase

    class MockKB(BaseKnowledgeBase):
        def __init__(self, path):
            self.path = path

        def retrieve(self, query):
            return [
                {"text": f.read_text(), "score": 0.9} for f in self.path.glob("*.txt")
            ]

    return MockKB(kb_path)


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
