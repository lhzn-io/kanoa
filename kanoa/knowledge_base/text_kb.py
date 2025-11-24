from pathlib import Path
from typing import Optional, Union

from .base import BaseKnowledgeBase


class TextKnowledgeBase(BaseKnowledgeBase):
    """Markdown/Text file knowledge base."""

    def __init__(
        self,
        kb_path: Optional[Union[str, Path]] = None,
        kb_content: Optional[str] = None,
    ):
        super().__init__(kb_path)
        self.kb_content = kb_content
        self._cached_context: Optional[str] = None

    def get_context(self) -> str:
        if self.kb_content:
            return self.kb_content

        if self._cached_context:
            return self._cached_context

        if self.kb_path and self.kb_path.exists():
            # Load all .md and .txt files
            content = []
            for file_path in self.kb_path.glob("**/*"):
                if file_path.suffix in [".md", ".txt"]:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content.append(f"# {file_path.name}\n\n{f.read()}")
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

            self._cached_context = "\n\n".join(content)
            return self._cached_context

        return ""

    def reload(self) -> None:
        self._cached_context = None
