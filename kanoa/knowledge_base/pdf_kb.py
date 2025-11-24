from pathlib import Path
from typing import Any, Optional, Union

from .base import BaseKnowledgeBase


class PDFKnowledgeBase(BaseKnowledgeBase):
    """PDF knowledge base (requires Gemini backend)."""

    def __init__(self, kb_path: Optional[Union[str, Path]], backend: Any):
        super().__init__(kb_path)
        self.backend = backend
        self._uploaded = False

    def get_context(self) -> str:
        """
        For PDF KB, context is handled by the backend (Gemini) via file uploads.
        This method might return a summary or list of files, but the actual content
        is passed to the model via file handles.
        """
        if not self._uploaded and self.kb_path:
            self._upload_pdfs()

        # Return a description of available PDFs for the system prompt
        if self.kb_path:
            pdfs = list(self.kb_path.glob("**/*.pdf"))
            return f"Available PDF References: {', '.join([p.name for p in pdfs])}"
        return ""

    def _upload_pdfs(self) -> None:
        if hasattr(self.backend, "load_pdfs") and self.kb_path:
            pdfs = list(self.kb_path.glob("**/*.pdf"))
            self.backend.load_pdfs(pdfs)
            self._uploaded = True

    def reload(self) -> None:
        self._uploaded = False
