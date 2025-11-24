from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kanoa.knowledge_base.pdf_kb import PDFKnowledgeBase
from kanoa.knowledge_base.text_kb import TextKnowledgeBase


class TestKnowledgeBase:
    @pytest.fixture
    def mock_path(self, tmp_path: Path) -> Path:
        d = tmp_path / "docs"
        d.mkdir()
        (d / "test.md").write_text("# Test\nContent")
        (d / "test.pdf").write_bytes(b"PDF content")
        return d

    def test_text_kb(self, mock_path: Path) -> None:
        kb = TextKnowledgeBase(kb_path=mock_path)
        context = kb.get_context()
        assert "# Test" in context
        assert "Content" in context

    def test_text_kb_content_init(self) -> None:
        kb = TextKnowledgeBase(kb_content="Direct content")
        assert kb.get_context() == "Direct content"

    def test_pdf_kb(self, mock_path: Path) -> None:
        mock_backend = MagicMock()
        kb = PDFKnowledgeBase(kb_path=mock_path, backend=mock_backend)

        context = kb.get_context()
        assert "Available PDF References" in context
        assert "test.pdf" in context

        # Verify upload called
        mock_backend.load_pdfs.assert_called_once()
        args = mock_backend.load_pdfs.call_args[0][0]
        assert len(args) == 1
        assert args[0].name == "test.pdf"

    def test_pdf_kb_reload(self, mock_path: Path) -> None:
        mock_backend = MagicMock()
        kb = PDFKnowledgeBase(kb_path=mock_path, backend=mock_backend)

        kb.get_context()
        mock_backend.load_pdfs.assert_called_once()

        kb.reload()
        kb.get_context()
        assert mock_backend.load_pdfs.call_count == 2
