"""Knowledge Base Manager for auto-detection and file categorization."""

from pathlib import Path
from typing import Optional, Union

from ..utils.logging import ilog_info, ilog_warning


class KnowledgeBaseManager:
    """
    Manages knowledge base content and categorizes files by type.

    Scans kb_path for all file types and provides content to backends
    in their requested format.
    """

    def __init__(
        self,
        kb_path: Optional[Union[str, Path]] = None,
        kb_content: Optional[str] = None,
    ):
        """
        Initialize knowledge base manager.

        Args:
            kb_path: Path to knowledge base directory
            kb_content: Pre-loaded knowledge base string (takes precedence)
        """
        self.kb_path = Path(kb_path) if kb_path else None
        self.kb_content = kb_content
        self._file_categories: Optional[dict[str, list[Path]]] = None

    def _categorize_files(self) -> dict[str, list[Path]]:
        """
        Scan kb_path and categorize files by type.

        Returns:
            Dict mapping file categories to lists of paths:
                - 'pdfs': PDF files
                - 'images': Image files (png, jpg, jpeg, gif, etc.)
                - 'text': Text/markdown files (md, txt)
                - 'code': Code files (py, js, etc.)
                - 'other': Other file types
        """
        if self._file_categories is not None:
            return self._file_categories

        categories: dict[str, list[Path]] = {
            "pdfs": [],
            "images": [],
            "text": [],
            "code": [],
            "other": [],
        }

        if not self.kb_path or not self.kb_path.exists():
            self._file_categories = categories
            return categories

        # Scan directory recursively
        for file_path in self.kb_path.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()

            if suffix == ".pdf":
                categories["pdfs"].append(file_path)
            elif suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
                categories["images"].append(file_path)
            elif suffix in {".md", ".txt", ".rst"}:
                categories["text"].append(file_path)
            elif suffix in {
                ".py",
                ".js",
                ".ts",
                ".java",
                ".c",
                ".cpp",
                ".h",
                ".go",
                ".rs",
            }:
                categories["code"].append(file_path)
            else:
                categories["other"].append(file_path)

        self._file_categories = categories

        # Log summary
        total_files = sum(len(files) for files in categories.values())
        if total_files > 0:
            ilog_info(
                f"Knowledge base scanned: {total_files} files "
                f"({len(categories['pdfs'])} PDFs, "
                f"{len(categories['text'])} text, "
                f"{len(categories['images'])} images)",
                source="kanoa.knowledge_base",
            )

        return categories

    def get_text_content(self) -> str:
        """
        Get text content from knowledge base.

        Returns concatenated content from all text/markdown files.
        If kb_content was provided at init, returns that instead.
        """
        if self.kb_content:
            return self.kb_content

        categories = self._categorize_files()
        text_files = categories["text"] + categories["code"]

        if not text_files:
            return ""

        content = []
        for file_path in text_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content.append(f"# {file_path.name}\n\n{f.read()}")
            except Exception as e:
                ilog_warning(
                    f"Error reading {file_path}: {e}",
                    source="kanoa.knowledge_base",
                    context={"file": str(file_path), "error": str(e)},
                )

        return "\n\n".join(content)

    def get_pdf_paths(self) -> list[Path]:
        """Get list of PDF file paths."""
        categories = self._categorize_files()
        return categories["pdfs"]

    def get_image_paths(self) -> list[Path]:
        """Get list of image file paths."""
        categories = self._categorize_files()
        return categories["images"]

    def has_pdfs(self) -> bool:
        """Check if knowledge base contains PDF files."""
        return len(self.get_pdf_paths()) > 0

    def has_images(self) -> bool:
        """Check if knowledge base contains image files."""
        return len(self.get_image_paths()) > 0

    def has_text(self) -> bool:
        """Check if knowledge base contains text content."""
        return bool(self.get_text_content())

    def reload(self) -> None:
        """Clear cache and force re-scan on next access."""
        self._file_categories = None
