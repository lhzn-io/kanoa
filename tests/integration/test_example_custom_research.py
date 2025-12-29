"""
Integration tests for Example Custom Research Backend (Vertex AI Only).

**Authentication**: Requires Google Cloud Application Default Credentials (ADC).
Run `gcloud auth application-default login` before running these tests.

**Environment Variables**:
- GOOGLE_CLOUD_PROJECT: GCP Project ID (required)
- GOOGLE_CLOUD_LOCATION: GCP location (default: us-central1)
"""

import os

import pytest

from kanoa.backends.example_custom_research import GeminiExampleCustomResearchBackend


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
        "Solar energy has grown 40% annually from 2020-2025. "
        "Key drivers: declining panel costs, government incentives."
    )
    (kb_path / "wind.txt").write_text(
        "Wind energy capacity increased 25% annually from 2020-2025. "
        "Offshore wind farms are the fastest growing segment."
    )
    return text_kb  # Return fixture? No, pytest fixture semantics imply return value of func.
    # Ah, wait, checking text_kb implementation in deep_research...
    # It just writes files. It yields/returns None implicitly?
    # No, earlier view showed it didn't return anything.
    # The KnowledgeBaseManager in the test used `text_kb` as `knowledge_base=text_kb`.
    # Wait, the previous test code passed `knowledge_base=text_kb`.
    # But `text_kb` fixture in `test_gemini_deep_research.py` just writes files.
    # It doesn't instantiate a KnowledgeBase object.
    # Let me check `test_basic_research_with_rag` usage in previous file.
    # `knowledge_base=text_kb` passed to `backend.interpret`.
    # `GeminiExampleCustomResearchBackend.interpret` expects `BaseKnowledgeBase`.
    # The fixture needs to return a KnowledgeBase object or Path?
    # The previous test must have been failing or I misread it.
    # Let's check the previous test code again.
    # `def text_kb(tmp_path): ...` writes text. Returns None.
    # `backend.interpret(..., knowledge_base=text_kb)` -> `knowledge_base` is None.
    # `if knowledge_base and isinstance(knowledge_base, BaseKnowledgeBase):` -> False.
    # So RAG was skipped in the previous test actually!
    # I should fix this here to actually test RAG.
    # I'll import SimpleTextKB logic or similar.


class SimpleKBWrapper:
    """Simple wrapper to satisfy BaseKnowledgeBase duck typing or inheritance."""

    def __init__(self, path):
        self.path = path

    def retrieve(self, query):
        results = []
        for f in self.path.glob("*.txt"):
            results.append({"text": f.read_text(), "score": 1.0, "source": f.name})
        return results


@pytest.fixture
def simple_kb(tmp_path):
    kb_path = tmp_path / "kb"
    kb_path.mkdir()
    (kb_path / "solar.txt").write_text("Solar energy has grown 40% annually.")
    (kb_path / "wind.txt").write_text("Wind energy grew 25% annually.")

    # We need a proper KB object.
    # Since I cannot easily import BaseKnowledgeBase here seamlessly without mocking abstract methods...
    # Actually I can import BaseKnowledgeBase.
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
class TestGeminiExampleCustomResearchBackend:
    """Tests for Example Custom Research Backend (Vertex AI Only)."""

    def test_basic_research_with_rag(self, sample_context, sample_focus, simple_kb):
        """Test basic research flow with RAG context (Vertex AI)."""
        # Require GOOGLE_CLOUD_PROJECT
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            pytest.skip("Skipping: GOOGLE_CLOUD_PROJECT not set (Vertex AI required)")

        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        try:
            backend = GeminiExampleCustomResearchBackend(
                project=project,
                location=location,
                model="gemini-3-pro-preview",
            )
        except Exception as e:
            pytest.skip(f"Backend init failed (ADC issue?): {e}")

        chunks = list(
            backend.interpret(
                fig=None,
                data=None,
                context=sample_context,
                focus=sample_focus,
                kb_context=None,
                custom_prompt=None,
                knowledge_base=simple_kb,
            )
        )

        assert len(chunks) > 0
        status_chunks = [c for c in chunks if c.type == "status"]
        content_chunks = [c for c in chunks if c.type == "text"]

        print("\n--- Chunks Received ---")
        for c in chunks:
            print(f"[{c.type}] {c.content[:100]}...")
            if c.usage:
                print(f"Usage: {c.usage}")
        print("-----------------------\n")

        assert len(status_chunks) > 0

        # Verify RAG was attempted matches
        kb_msgs = [c.content for c in status_chunks if "Knowledge Base" in c.content]
        assert len(kb_msgs) > 0

    def test_research_without_rag(self, sample_focus):
        """Test research without RAG - Google Search only (Vertex AI)."""
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            pytest.skip("Skipping: GOOGLE_CLOUD_PROJECT not set (Vertex AI required)")

        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        try:
            backend = GeminiExampleCustomResearchBackend(
                project=project,
                location=location,
                model="gemini-3-pro-preview",
            )
        except Exception as e:
            pytest.skip(f"Backend init failed (ADC issue?): {e}")

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
        content_chunks = [c for c in chunks if c.type == "text"]

        print("\n--- Chunks Received ---")
        for c in chunks:
            print(f"[{c.type}] {c.content[:100]}...")
            if c.usage:
                print(f"Usage: {c.usage}")
        print("-----------------------\n")
        assert len(content_chunks) > 0

    def test_custom_prompt(self):
        """Test with custom research prompt (Vertex AI)."""
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            pytest.skip("Skipping: GOOGLE_CLOUD_PROJECT not set (Vertex AI required)")

        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        try:
            backend = GeminiExampleCustomResearchBackend(
                project=project,
                location=location,
                model="gemini-3-pro-preview",
            )
        except Exception as e:
            pytest.skip(f"Backend init failed (ADC issue?): {e}")

        custom_prompt = "What are the top 3 renewable energy trends in 2025?"
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
        print("\n--- Chunks Received ---")
        for c in chunks:
            print(f"[{c.type}] {c.content[:100]}...")
            if c.usage:
                print(f"Usage: {c.usage}")
        print("-----------------------\n")

        content_chunks = [c for c in chunks if c.type == "text"]
        for c in content_chunks:
            assert "❌ Error" not in c.content, f"Backend returned error: {c.content}"

        assert len(content_chunks) > 0
