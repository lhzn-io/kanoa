from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GroundingSource:
    """Source attribution for RAG-grounded responses.

    Attributes:
        uri: Source document URI (e.g., GCS path).
        score: Relevance score (0-1) from semantic retrieval.
        text: Excerpt from the source document.
        chunk_id: Unique identifier for the retrieved chunk.
    """

    uri: str
    score: float
    text: str
    chunk_id: Optional[str] = None


@dataclass
class CacheCreationResult:
    """Result from cache creation operation."""

    name: Optional[str]
    created: bool
    token_count: int = 0


@dataclass
class UsageInfo:
    """Token usage and cost information."""

    input_tokens: int
    output_tokens: int
    cost: float
    cached_tokens: Optional[int] = field(default=None)
    cache_created: bool = field(default=False)
    savings: Optional[float] = field(default=None)
    model: Optional[str] = field(default=None)
    tier: Optional[str] = field(default=None)

    @property
    def cache_savings(self) -> Optional[float]:
        """
        Calculate estimated cost savings from caching.

        Returns the savings amount if available.
        """
        return self.savings


@dataclass
class InterpretationResult:
    """Result from interpretation.

    Note: This class does NOT implement _repr_markdown_() by design.
    Display is handled explicitly via display_interpretation() when appropriate.
    This prevents double-display in streaming mode and makes display side-effects explicit.
    See docs/source/developer_guide/design_philosophy.md for rationale.
    """

    text: str
    backend: str
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
    grounding_sources: Optional[List[GroundingSource]] = None


@dataclass
class InterpretationChunk:
    """A chunk of streaming interpretation data."""

    content: str
    type: str  # "text", "status", "usage", "meta"
    is_final: bool = False
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
