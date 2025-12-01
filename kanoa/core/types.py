from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class UsageInfo:
    """Token usage and cost information."""

    input_tokens: int
    output_tokens: int
    cost: float
    cached_tokens: Optional[int] = field(default=None)

    @property
    def cache_savings(self) -> Optional[float]:
        """
        Calculate estimated cost savings from caching.

        Returns approximate savings based on 75% reduced rate for cached tokens.
        """
        if not self.cached_tokens:
            return None
        # Assuming ~$2/1M standard vs ~$0.50/1M cached
        full_price = self.cached_tokens / 1_000_000 * 2.00
        cached_price = self.cached_tokens / 1_000_000 * 0.50
        return full_price - cached_price


@dataclass
class InterpretationResult:
    """Result from interpretation."""

    text: str
    backend: str
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
