"""Tests for KnowledgeBaseManager."""

from pathlib import Path

from kanoa.knowledge_base.manager import KnowledgeBaseManager


class TestKnowledgeBaseManager:
    """Test KnowledgeBaseManager functionality."""

    def test_text_content(self, tmp_path: Path) -> None:
        """Test reading text content from knowledge base."""
        (tmp_path / "test.md").write_text("# Test\n\nContent here")
        (tmp_path / "other.txt").write_text("More content")

        manager = KnowledgeBaseManager(kb_path=tmp_path)
        content = manager.get_text_content()

        assert "test.md" in content
        assert "Content here" in content
        assert "other.txt" in content
        assert "More content" in content

    def test_pdf_detection(self, tmp_path: Path) -> None:
        """Test PDF file detection."""
        (tmp_path / "test.pdf").write_bytes(b"PDF content")

        manager = KnowledgeBaseManager(kb_path=tmp_path)

        assert manager.has_pdfs()
        assert len(manager.get_pdf_paths()) == 1
        assert manager.get_pdf_paths()[0].name == "test.pdf"

    def test_image_detection(self, tmp_path: Path) -> None:
        """Test image file detection."""
        (tmp_path / "test.png").write_bytes(b"PNG data")
        (tmp_path / "other.jpg").write_bytes(b"JPG data")

        manager = KnowledgeBaseManager(kb_path=tmp_path)

        assert manager.has_images()
        assert len(manager.get_image_paths()) == 2

    def test_mixed_content(self, tmp_path: Path) -> None:
        """Test detection of mixed content types."""
        (tmp_path / "doc.md").write_text("Text content")
        (tmp_path / "report.pdf").write_bytes(b"PDF content")
        (tmp_path / "chart.png").write_bytes(b"PNG content")

        manager = KnowledgeBaseManager(kb_path=tmp_path)

        assert manager.has_text()
        assert manager.has_pdfs()
        assert manager.has_images()

    def test_kb_content_override(self, tmp_path: Path) -> None:
        """Test that kb_content overrides file reading."""
        (tmp_path / "test.md").write_text("File content")

        manager = KnowledgeBaseManager(kb_path=tmp_path, kb_content="Override content")

        content = manager.get_text_content()
        assert content == "Override content"
        assert "File content" not in content

    def test_reload(self, tmp_path: Path) -> None:
        """Test that reload clears cache."""
        file_path = tmp_path / "test.md"
        file_path.write_text("Initial content")

        manager = KnowledgeBaseManager(kb_path=tmp_path)

        # First read
        content1 = manager.get_text_content()
        assert "Initial content" in content1

        # Update file
        file_path.write_text("Updated content")

        # Read again (should still be cached)
        manager._categorize_files()  # Force categorization to cache

        # Reload and read
        manager.reload()
        content2 = manager.get_text_content()
        assert "Updated content" in content2

    def test_empty_kb(self, tmp_path: Path) -> None:
        """Test empty knowledge base."""
        manager = KnowledgeBaseManager(kb_path=tmp_path)

        assert not manager.has_text()
        assert not manager.has_pdfs()
        assert not manager.has_images()
        assert manager.get_text_content() == ""
