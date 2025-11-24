from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class UsageInfo:
    """Token usage and cost information."""

    input_tokens: int
    output_tokens: int
    cost: float
    cached_tokens: int = 0


@dataclass
class InterpretationResult:
    """Result from interpretation."""

    text: str
    backend: str
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
