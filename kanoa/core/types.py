"""
Type definitions for Kanoa.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

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
