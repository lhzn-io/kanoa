"""AI backends for kanoa.

Backends are lazily imported to allow installation without all dependencies.
Install specific backends with:
    pip install kanoa[gemini]
    pip install kanoa[claude]
    pip install kanoa[openai]
    pip install kanoa[all]
"""

from typing import TYPE_CHECKING

from .base import BaseBackend

# Lazy imports for optional dependencies
if TYPE_CHECKING:
    from .claude import ClaudeBackend, ClaudeTokenCounter
    from .gemini import GeminiBackend, GeminiTokenCounter
    from .openai import OpenAIBackend


def __getattr__(name: str) -> type:
    """Lazy import backends to handle missing dependencies gracefully."""
    if name == "GeminiBackend":
        try:
            from .gemini import GeminiBackend

            return GeminiBackend
        except ImportError as e:
            raise ImportError(
                f"GeminiBackend requires google-genai. "
                f"Install with: pip install kanoa[gemini]\n"
                f"Original error: {e}"
            ) from e

    if name == "GeminiTokenCounter":
        try:
            from .gemini import GeminiTokenCounter

            return GeminiTokenCounter
        except ImportError as e:
            raise ImportError(
                f"GeminiTokenCounter requires google-genai. "
                f"Install with: pip install kanoa[gemini]\n"
                f"Original error: {e}"
            ) from e

    if name == "ClaudeBackend":
        try:
            from .claude import ClaudeBackend

            return ClaudeBackend
        except ImportError as e:
            raise ImportError(
                f"ClaudeBackend requires anthropic. "
                f"Install with: pip install kanoa[claude]\n"
                f"Original error: {e}"
            ) from e

    if name == "ClaudeTokenCounter":
        try:
            from .claude import ClaudeTokenCounter

            return ClaudeTokenCounter
        except ImportError as e:
            raise ImportError(
                f"ClaudeTokenCounter requires anthropic. "
                f"Install with: pip install kanoa[claude]\n"
                f"Original error: {e}"
            ) from e

    if name == "OpenAIBackend":
        try:
            from .openai import OpenAIBackend

            return OpenAIBackend
        except ImportError as e:
            raise ImportError(
                f"OpenAIBackend requires openai. "
                f"Install with: pip install kanoa[local]  # or kanoa[openai]\n"
                f"Original error: {e}"
            ) from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseBackend",
    "ClaudeBackend",
    "ClaudeTokenCounter",
    "GeminiBackend",
    "GeminiTokenCounter",
    "OpenAIBackend",
]
