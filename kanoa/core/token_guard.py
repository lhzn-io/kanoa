"""
Token counting and cost guardrails for API calls.

This module provides pre-flight token counting and user-friendly guardrails
to prevent unexpected costs from large API requests.

Features:
- Pre-flight token counting before API calls
- Backend-agnostic design (protocol-based)
- Configurable thresholds for warnings, approval prompts, and hard limits
- Cost estimation based on current pricing
- Jupyter-friendly interactive approval
- Environment variable overrides for automation

Usage:
    from kanoa.backends.gemini import GeminiTokenCounter
    from kanoa.core.token_guard import TokenGuard

    # Create backend-specific counter
    counter = GeminiTokenCounter(client, model="gemini-3-pro-preview")

    # Wrap with guard
    guard = TokenGuard(counter)

    # Check before API call
    result = guard.check(contents, pricing=PRICING)

    if result.requires_approval and not result.approved:
        raise TokenLimitExceeded(result.message)

    # Proceed with API call...
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from ..config import options

# Default thresholds (tokens)
# Now controlled via kanoa.options
DEFAULT_WARN_THRESHOLD = 2048
DEFAULT_APPROVAL_THRESHOLD = 50_000
DEFAULT_REJECT_THRESHOLD = 200_000


# =============================================================================
# Token Counter Protocol & Base Class
# =============================================================================


class TokenCounter(Protocol):
    """Protocol for backend-agnostic token counting."""

    @property
    def backend_name(self) -> str:
        """Return the backend name (e.g., 'gemini', 'claude')."""
        ...

    @property
    def model(self) -> str:
        """Return the model name."""
        ...

    def count_tokens(self, contents: Any) -> int:
        """
        Count tokens for the given contents.

        Args:
            contents: Content to count (format varies by backend)

        Returns:
            Token count
        """
        ...

    def estimate_tokens(self, contents: Any) -> int:
        """
        Fallback estimation when API counting fails.

        Args:
            contents: Content to estimate

        Returns:
            Estimated token count
        """
        ...


class BaseTokenCounter(ABC):
    """Base class for token counters with shared functionality."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the backend name."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model name."""
        ...

    @abstractmethod
    def count_tokens(self, contents: Any) -> int:
        """Count tokens using the backend API."""
        ...

    def estimate_tokens(self, contents: Any) -> int:
        """Fallback token estimation based on content size (~4 chars per token)."""
        if isinstance(contents, str):
            return len(contents) // 4
        if isinstance(contents, list):
            total = 0
            for item in contents:
                if isinstance(item, str):
                    total += len(item) // 4
                elif isinstance(item, dict):
                    # Handle message dicts (Claude format)
                    content = item.get("content", "")
                    if isinstance(content, str):
                        total += len(content) // 4
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict):
                                text = part.get("text", "")
                                total += len(text) // 4
                elif hasattr(item, "parts"):
                    # Handle Gemini Content objects
                    for part in item.parts:
                        if hasattr(part, "text"):
                            total += len(part.text) // 4
            return total
        return 0


class FallbackTokenCounter(BaseTokenCounter):
    """Fallback counter that only uses estimation (no API calls)."""

    def __init__(self, backend_name: str = "unknown", model: str = "unknown"):
        self._backend_name = backend_name
        self._model = model

    @property
    def backend_name(self) -> str:
        return self._backend_name

    @property
    def model(self) -> str:
        return self._model

    def count_tokens(self, contents: Any) -> int:
        """Use estimation only (no API available)."""
        return self.estimate_tokens(contents)


# =============================================================================
# Token Guard Result & Exception
# =============================================================================


@dataclass
class TokenCheckResult:
    """Result of a token count check."""

    token_count: int
    estimated_cost: float
    level: str  # "ok", "warn", "approval", "reject"
    approved: bool
    message: str
    requires_approval: bool = False

    def __str__(self) -> str:
        return (
            f"TokenCheck: {self.token_count:,} tokens, "
            f"~${self.estimated_cost:.4f}, level={self.level}"
        )


class TokenLimitExceeded(Exception):
    """Raised when token count exceeds the reject threshold."""

    def __init__(self, token_count: int, limit: int, estimated_cost: float):
        self.token_count = token_count
        self.limit = limit
        self.estimated_cost = estimated_cost
        super().__init__(
            f"Token count ({token_count:,}) exceeds limit ({limit:,}). "
            f"Estimated cost: ${estimated_cost:.4f}. "
            f"Set KANOA_TOKEN_REJECT_THRESHOLD to increase limit."
        )


# =============================================================================
# Token Guard
# =============================================================================


class TokenGuard:
    """
    Pre-flight token counting and cost guardrails.

    Provides configurable thresholds for:
    - Warnings: Log a warning but proceed
    - Approval: Prompt user for confirmation (Jupyter-friendly)
    - Rejection: Hard limit that blocks the request

    All thresholds can be overridden via environment variables.
    """

    def __init__(
        self,
        counter: TokenCounter,
        warn_threshold: Optional[int] = None,
        approval_threshold: Optional[int] = None,
        reject_threshold: Optional[int] = None,
        auto_approve: bool = False,
    ):
        """
        Initialize TokenGuard.

        Args:
            counter: TokenCounter instance (backend-specific)
            warn_threshold: Token count to trigger warning (default: 10K)
            approval_threshold: Token count to require approval (default: 50K)
            reject_threshold: Token count to reject request (default: 200K)
            auto_approve: Skip interactive prompts (for automation)
        """
        self.counter = counter

        # Load thresholds from args, env vars, or kanoa.options
        self.warn_threshold = (
            warn_threshold
            or int(os.environ.get("KANOA_TOKEN_WARN_THRESHOLD", "0"))
            or options.token_warn_threshold
        )
        self.approval_threshold = (
            approval_threshold
            or int(os.environ.get("KANOA_TOKEN_APPROVAL_THRESHOLD", "0"))
            or options.token_approval_threshold
        )
        self.reject_threshold = (
            reject_threshold
            or int(os.environ.get("KANOA_TOKEN_REJECT_THRESHOLD", "0"))
            or options.token_reject_threshold
        )

        # Auto-approve can be set via env var or options
        self.auto_approve = (
            auto_approve
            or os.environ.get("KANOA_AUTO_APPROVE") == "1"
            or options.auto_approve
        )

    # Expose counter properties for convenience
    @property
    def backend_name(self) -> str:
        """Return the backend name from the counter."""
        return self.counter.backend_name

    @property
    def model(self) -> str:
        """Return the model name from the counter."""
        return self.counter.model

    def count_tokens(self, contents: Any) -> int:
        """
        Count tokens using the configured counter.

        Args:
            contents: Content to count (format varies by backend)

        Returns:
            Token count
        """
        return self.counter.count_tokens(contents)

    def estimate_cost(
        self,
        token_count: int,
        pricing: Dict[str, float],
        context_threshold: int = 200_000,
    ) -> float:
        """
        Estimate cost for input tokens based on pricing.

        Args:
            token_count: Number of input tokens
            pricing: Pricing dict with 'input_short', 'input_long' keys
            context_threshold: Threshold for short vs long context pricing

        Returns:
            Estimated cost in dollars
        """
        if token_count <= context_threshold:
            price_per_million = pricing.get("input_short", 2.00)
        else:
            price_per_million = pricing.get("input_long", 4.00)

        return token_count / 1_000_000 * price_per_million

    def check(
        self,
        contents: Any,
        pricing: Optional[Dict[str, float]] = None,
    ) -> TokenCheckResult:
        """
        Check token count and determine if request should proceed.

        Args:
            contents: Content to check
            pricing: Optional pricing dict for cost estimation

        Returns:
            TokenCheckResult with approval status and message
        """
        pricing = pricing or {"input_short": 2.00, "input_long": 4.00}

        # Count tokens
        token_count = self.count_tokens(contents)
        estimated_cost = self.estimate_cost(token_count, pricing)

        # Determine level
        if token_count >= self.reject_threshold:
            return TokenCheckResult(
                token_count=token_count,
                estimated_cost=estimated_cost,
                level="reject",
                approved=False,
                requires_approval=True,
                message=(
                    f"Request rejected: {token_count:,} tokens exceeds "
                    f"limit of {self.reject_threshold:,}. "
                    f"Estimated cost: ${estimated_cost:.4f}"
                ),
            )

        if token_count >= self.approval_threshold:
            # Need user approval
            if self.auto_approve:
                return TokenCheckResult(
                    token_count=token_count,
                    estimated_cost=estimated_cost,
                    level="approval",
                    approved=True,
                    requires_approval=False,
                    message=(
                        f"Large request auto-approved: {token_count:,} tokens, "
                        f"~${estimated_cost:.4f}"
                    ),
                )
            else:
                # Interactive approval
                approved = self._request_approval(token_count, estimated_cost)
                return TokenCheckResult(
                    token_count=token_count,
                    estimated_cost=estimated_cost,
                    level="approval",
                    approved=approved,
                    requires_approval=True,
                    message=(
                        f"Large request {'approved' if approved else 'denied'}: "
                        f"{token_count:,} tokens, ~${estimated_cost:.4f}"
                    ),
                )

        if token_count >= self.warn_threshold:
            return TokenCheckResult(
                token_count=token_count,
                estimated_cost=estimated_cost,
                level="warn",
                approved=True,
                requires_approval=False,
                message=f"{token_count:,} tokens, ~${estimated_cost:.4f}",
            )

        # OK - under all thresholds
        return TokenCheckResult(
            token_count=token_count,
            estimated_cost=estimated_cost,
            level="ok",
            approved=True,
            requires_approval=False,
            message=f"{token_count:,} tokens, ~${estimated_cost:.4f}",
        )

    def _request_approval(self, token_count: int, estimated_cost: float) -> bool:
        """
        Request user approval for large requests.

        Jupyter-friendly: uses input() which works in notebooks.

        Args:
            token_count: Number of tokens
            estimated_cost: Estimated cost in dollars

        Returns:
            True if approved, False otherwise
        """
        print("\n" + "=" * 60)
        print("LARGE TOKEN REQUEST - APPROVAL REQUIRED")
        print("=" * 60)
        print(f"   Token count:    {token_count:,}")
        print(f"   Estimated cost: ${estimated_cost:.4f}")
        print(f"   Approval limit: {self.approval_threshold:,} tokens")
        print("=" * 60)

        try:
            response = input("Proceed with this request? [y/N]: ").strip().lower()
            approved = response in ("y", "yes")
            if not approved:
                print("Request cancelled by user.")
            return approved
        except (EOFError, KeyboardInterrupt):
            print("\nRequest cancelled.")
            return False

    def guard(
        self,
        contents: Any,
        pricing: Optional[Dict[str, float]] = None,
    ) -> TokenCheckResult:
        """
        Check tokens and raise exception if rejected.

        Convenience method that combines check() with automatic rejection.

        Args:
            contents: Content to check
            pricing: Optional pricing dict

        Returns:
            TokenCheckResult if approved

        Raises:
            TokenLimitExceeded: If request exceeds reject threshold or user denies
        """
        result = self.check(contents, pricing)

        if result.level == "reject" or (
            result.requires_approval and not result.approved
        ):
            raise TokenLimitExceeded(
                result.token_count,
                (
                    self.reject_threshold
                    if result.level == "reject"
                    else self.approval_threshold
                ),
                result.estimated_cost,
            )

        # Log warning/info
        if result.level == "warn":
            print(result.message)

        return result


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Core classes
    "TokenGuard",
    "TokenCheckResult",
    "TokenLimitExceeded",
    # Protocol and base class
    "TokenCounter",
    "BaseTokenCounter",
    # Fallback counter (backend-agnostic)
    "FallbackTokenCounter",
    # Constants
    "DEFAULT_WARN_THRESHOLD",
    "DEFAULT_APPROVAL_THRESHOLD",
    "DEFAULT_REJECT_THRESHOLD",
]
