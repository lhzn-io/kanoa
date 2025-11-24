from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CostTracker:
    """Tracks token usage and costs."""

    total_tokens: Dict[str, int]
    total_cost: float

    def __init__(self) -> None:
        self.total_tokens = {"input": 0, "output": 0}
        self.total_cost = 0.0

    def update(self, input_tokens: int, output_tokens: int, cost: float) -> None:
        self.total_tokens["input"] += input_tokens
        self.total_tokens["output"] += output_tokens
        self.total_cost += cost

    def get_summary(self) -> Dict[str, Any]:
        return {"total_tokens": self.total_tokens, "total_cost_usd": self.total_cost}
