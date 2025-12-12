"""Vertex AI RAG Engine knowledge base integration.

This module provides integration with Google Cloud's Vertex AI RAG Engine for
semantic retrieval over large document collections stored in GCS.

Key Features:
- Automatic corpus creation and reuse by display_name
- GCS document import with configurable chunking
- Semantic retrieval with relevance scoring
- Cost-efficient alternative to context stuffing

Example:
    >>> from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase
    >>> rag_kb = VertexRAGKnowledgeBase(
    ...     project_id="my-research-project",
    ...     corpus_display_name="ml-papers",
    ...     chunk_size=512,
    ...     chunk_overlap=100,
    ... )
    >>> rag_kb.create_corpus()
    >>> rag_kb.import_files("gs://my-bucket/papers/")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseKnowledgeBase

if TYPE_CHECKING:
    from typing import Any


class VertexRAGKnowledgeBase(BaseKnowledgeBase):
    """Knowledge base backed by Vertex AI RAG Engine.

    This class manages RAG corpora for semantic retrieval over document collections
    stored in Google Cloud Storage (GCS). It handles corpus lifecycle, document
    import, and semantic search with grounding source attribution.

    Attributes:
        project_id: GCP project ID (required for billing transparency).
        location: GCP region (default: us-east1).
        corpus_display_name: Logical corpus identifier (required for multi-KB workflows).
        chunk_size: Document chunk size in tokens (default: 512).
        chunk_overlap: Overlap between chunks in tokens (default: 100).
        top_k: Number of chunks to retrieve per query (default: 5).
        similarity_threshold: Minimum similarity score (default: 0.7).
    """

    def __init__(
        self,
        project_id: str,
        corpus_display_name: str,
        location: str = "us-east1",
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> None:
        """Initialize Vertex RAG knowledge base.

        Args:
            project_id: GCP project ID. Must be specified explicitly for billing
                transparency. No defaults.
            corpus_display_name: Logical corpus identifier. Used for corpus reuse
                and multi-KB separation. Required.
            location: GCP region for Vertex AI resources. Default: us-east1.
            chunk_size: Document chunk size in tokens. Default: 512.
                - Academic papers: 512 (balanced)
                - Legal docs: 1024 (preserve context)
                - FAQ/short-form: 256 (precise retrieval)
            chunk_overlap: Overlap between chunks in tokens. Default: 100.
                Prevents concept splitting at boundaries.
            top_k: Number of chunks to retrieve per query. Default: 5.
            similarity_threshold: Minimum similarity score (0-1). Default: 0.7.
                Lower values retrieve more chunks (noisier), higher values are
                more selective (may miss relevant content).

        Raises:
            ImportError: If google-cloud-aiplatform is not installed.
        """
        # Validate required parameters
        if not project_id:
            msg = (
                "project_id is required for billing transparency. "
                "Specify your GCP project explicitly."
            )
            raise ValueError(msg)
        if not corpus_display_name:
            msg = (
                "corpus_display_name is required for multi-KB workflows. "
                "Use a descriptive name like 'ml-papers' or 'client-docs'."
            )
            raise ValueError(msg)

        self.project_id = project_id
        self.location = location
        self.corpus_display_name = corpus_display_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        # Lazy import to handle optional dependency
        try:
            import vertexai
            from vertexai import rag

            self._rag_module = rag
            self._vertexai_module = vertexai
        except ImportError as e:
            msg = (
                "google-cloud-aiplatform is required for Vertex AI RAG Engine. "
                "Install with: pip install kanoa[vertexai]"
            )
            raise ImportError(msg) from e

        # Initialize Vertex AI SDK
        self._vertexai_module.init(project=self.project_id, location=self.location)

        # Corpus resource name (set after create_corpus or reuse)
        self._corpus_name: str | None = None

    @property
    def corpus_name(self) -> str:
        """Get the corpus resource name.

        Returns:
            Corpus resource name in format:
            projects/{project_id}/locations/{location}/ragCorpora/{corpus_id}

        Raises:
            RuntimeError: If corpus not yet created. Call create_corpus() first.
        """
        if self._corpus_name is None:
            msg = (
                "Corpus not yet created. Call create_corpus() first, or use "
                "an existing corpus by setting corpus_name manually."
            )
            raise RuntimeError(msg)
        return self._corpus_name

    def create_corpus(self) -> str:
        """Create or reuse RAG corpus by display_name.

        This method checks if a corpus with the given display_name already exists
        in the project. If found, it reuses the existing corpus. Otherwise, it
        creates a new one.

        Returns:
            Corpus resource name.

        Raises:
            RuntimeError: If corpus creation fails.

        Example:
            >>> rag_kb = VertexRAGKnowledgeBase(
            ...     project_id="my-project",
            ...     corpus_display_name="research-papers"
            ... )
            >>> corpus_name = rag_kb.create_corpus()
            >>> print(corpus_name)
            projects/123456/locations/us-central1/ragCorpora/789012
        """
        # Check if corpus already exists
        try:
            corpora = self._rag_module.list_corpora()
            for corpus in corpora:
                if corpus.display_name == self.corpus_display_name:
                    corpus_name: str = str(corpus.name)
                    self._corpus_name = corpus_name
                    return corpus_name
        except Exception as e:
            msg = f"Failed to list existing corpora: {e}"
            raise RuntimeError(msg) from e

        # Create new corpus
        try:
            embedding_model_config = self._rag_module.RagEmbeddingModelConfig(
                vertex_prediction_endpoint=self._rag_module.VertexPredictionEndpoint(
                    publisher_model="publishers/google/models/text-embedding-005"
                )
            )

            new_corpus = self._rag_module.create_corpus(
                display_name=self.corpus_display_name,
                backend_config=self._rag_module.RagVectorDbConfig(
                    rag_embedding_model_config=embedding_model_config
                ),
            )

            corpus_name_new: str = str(new_corpus.name)
            self._corpus_name = corpus_name_new
            return corpus_name_new
        except Exception as e:
            msg = f"Failed to create corpus '{self.corpus_display_name}': {e}"
            raise RuntimeError(msg) from e

    def get_corpus(self) -> str:
        """Get existing RAG corpus by display_name.

        This method checks if a corpus with the given display_name already exists
        in the project. If found, it sets the corpus_name and returns it.
        If not found, it raises a RuntimeError.

        Returns:
            Corpus resource name.

        Raises:
            RuntimeError: If corpus not found or listing fails.
        """
        try:
            corpora = self._rag_module.list_corpora()
            for corpus in corpora:
                if corpus.display_name == self.corpus_display_name:
                    corpus_name: str = str(corpus.name)
                    self._corpus_name = corpus_name
                    return corpus_name

            raise RuntimeError(
                f"Corpus '{self.corpus_display_name}' not found in project '{self.project_id}'. "
                "Use create_corpus() to create it."
            )
        except Exception as e:
            msg = f"Failed to get corpus '{self.corpus_display_name}': {e}"
            raise RuntimeError(msg) from e

    def import_files(
        self,
        gcs_uri: str,
        max_embedding_requests_per_min: int = 1000,
    ) -> None:
        """Import documents from GCS into the corpus.

        This is an async operation. Import may take 2-5 minutes for 10 PDFs,
        or 20-30 minutes for 100+ files.

        Args:
            gcs_uri: GCS URI to import from. Can be:
                - Bucket path: gs://bucket/path/to/folder/
                - Single file: gs://bucket/path/to/file.pdf
                Must end with '/' for directory imports.
            max_embedding_requests_per_min: Rate limit for embedding generation.
                Default: 1000 (sufficient for most use cases).

        Raises:
            RuntimeError: If corpus not created or import fails.

        Example:
            >>> rag_kb.import_files("gs://my-bucket/papers/")
            >>> # Wait 2-5 minutes for import to complete
            >>> import time
            >>> time.sleep(180)
        """
        if self._corpus_name is None:
            msg = "Corpus not created. Call create_corpus() first."
            raise RuntimeError(msg)

        try:
            self._rag_module.import_files(
                self._corpus_name,
                [gcs_uri],
                transformation_config=self._rag_module.TransformationConfig(
                    chunking_config=self._rag_module.ChunkingConfig(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                    ),
                ),
                max_embedding_requests_per_min=max_embedding_requests_per_min,
            )
        except Exception as e:
            msg = f"Failed to import files from {gcs_uri}: {e}"
            raise RuntimeError(msg) from e

    def retrieve(self, query: str) -> list[dict[str, Any]]:
        """Perform semantic retrieval over the corpus.

        Args:
            query: Natural language query for semantic search.

        Returns:
            List of retrieved chunks with metadata. Each dict contains:
                - text: Chunk text content
                - score: Relevance score (0-1)
                - source_uri: GCS URI of source document
                - chunk_id: Unique chunk identifier

        Raises:
            RuntimeError: If corpus not created or retrieval fails.

        Example:
            >>> results = rag_kb.retrieve("machine learning interpretability")
            >>> for result in results:
            ...     print(f"{result['score']:.3f}: {result['text'][:100]}...")
            0.847: SHAP (SHapley Additive exPlanations) is a unified approach...
            0.821: We propose LIME, a novel explanation technique...
        """
        if self._corpus_name is None:
            msg = "Corpus not created. Call create_corpus() first."
            raise RuntimeError(msg)

        try:
            response = self._rag_module.retrieval_query(
                rag_resources=[
                    self._rag_module.RagResource(rag_corpus=self._corpus_name)
                ],
                text=query,
                rag_retrieval_config=self._rag_module.RagRetrievalConfig(
                    top_k=self.top_k,
                    filter=self._rag_module.Filter(
                        vector_distance_threshold=self.similarity_threshold
                    ),
                ),
            )

            # Format results
            results = []
            for context in response.contexts.contexts:
                result = {
                    "text": context.text,
                    "score": context.score,
                    "source_uri": (
                        context.source_uri if hasattr(context, "source_uri") else None
                    ),
                    "chunk_id": (
                        context.chunk_id if hasattr(context, "chunk_id") else None
                    ),
                }
                results.append(result)

            return results
        except Exception as e:
            msg = f"Failed to retrieve from corpus: {e}"
            raise RuntimeError(msg) from e

    def delete_corpus(self) -> None:
        """Delete the corpus and all associated data.

        Warning: This is irreversible. All imported documents and embeddings
        will be permanently deleted.

        Raises:
            RuntimeError: If corpus not created or deletion fails.

        Example:
            >>> rag_kb.delete_corpus()  # Cleanup after testing
        """
        if self._corpus_name is None:
            msg = "No corpus to delete. Call create_corpus() first."
            raise RuntimeError(msg)

        try:
            self._rag_module.delete_corpus(name=self._corpus_name)
            self._corpus_name = None
        except Exception as e:
            msg = f"Failed to delete corpus: {e}"
            raise RuntimeError(msg) from e
