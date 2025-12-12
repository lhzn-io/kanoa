"""Knowledge base components for kanoa."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseKnowledgeBase
    from .vertex_rag import VertexRAGKnowledgeBase

__all__ = ["BaseKnowledgeBase", "VertexRAGKnowledgeBase"]
