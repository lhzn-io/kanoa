from typing import Any


def data_to_text(data: Any) -> str:
    """Convert data to text representation.

    Handles DataFrames (pandas), dicts, and other objects.
    """
    # Try DataFrame methods
    if hasattr(data, "to_string"):
        # Check for to_markdown (pandas >= 1.0.0)
        if hasattr(data, "to_markdown"):
            try:
                return str(data.to_markdown())
            except ImportError:
                pass  # tabulate not installed
        return str(data.to_string())

    # Try dict/JSON
    if isinstance(data, dict):
        import json

        try:
            return json.dumps(data, indent=2, default=str)
        except TypeError:
            return str(data)

    # Fallback
    return str(data)
