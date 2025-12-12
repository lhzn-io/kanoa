"""Abstract base class for knowledge base backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class BaseKnowledgeBase(ABC):
    """Abstract base class for knowledge base backends.

    This defines the interface for different knowledge base grounding strategies:
    - Local file-based (KnowledgeBaseManager)
    - Vertex AI RAG Engine (VertexRAGKnowledgeBase)
    - Future: Pinecone, Weaviate, custom vector DBs, etc.
    """

    @abstractmethod
    def retrieve(self, query: str) -> list[dict[str, Any]]:
        """Perform semantic retrieval over the knowledge base.

        Args:
            query: Natural language query for semantic search.

        Returns:
            List of retrieved chunks with metadata. Each dict must contain:
                - text: Chunk text content (str)
                - score: Relevance score 0-1 (float)
                - source_uri: URI of source document (str)
                - chunk_id: Unique chunk identifier (str, optional)

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        ...
