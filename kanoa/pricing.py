import json
from pathlib import Path
from typing import Any, Dict

# Default pricing file path relative to this module
DEFAULT_PRICING_PATH = Path(__file__).parent / "pricing.json"
USER_CONFIG_PATH = Path.home() / ".config" / "kanoa" / "pricing.json"


def load_pricing() -> Dict[str, Any]:
    """
    Load pricing configuration.

    Loads from the bundled pricing.json and optionally merges with
    a user override file at ~/.config/kanoa/pricing.json.
    """
    # Load default pricing
    if not DEFAULT_PRICING_PATH.exists():
        return {}

    with open(DEFAULT_PRICING_PATH, "r") as f:
        pricing: Dict[str, Any] = json.load(f)

    # Load user override if exists
    if USER_CONFIG_PATH.exists():
        try:
            with open(USER_CONFIG_PATH, "r") as f:
                user_pricing: Dict[str, Any] = json.load(f)
                _deep_update(pricing, user_pricing)
        except Exception:
            # Log warning but continue with defaults
            # TODO: Add proper logging here
            pass

    return pricing


def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
    """Recursively update dictionary."""
    for key, value in update_dict.items():
        if (
            isinstance(value, dict)
            and key in base_dict
            and isinstance(base_dict[key], dict)
        ):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value


def get_model_pricing(backend: str, model: str) -> Dict[str, float]:
    """
    Get pricing for a specific model.

    Args:
        backend: Backend name (vllm, gemini, claude, openai)
        model: Model identifier

    Returns:
        Dictionary with pricing details or empty dict if not found.
    """
    pricing = load_pricing()

    # Normalize backend name
    backend = backend.lower()

    if backend not in pricing:
        return {}

    backend_pricing: Dict[str, Any] = pricing[backend]

    # Direct match
    if model in backend_pricing:
        model_pricing: Dict[str, float] = backend_pricing[model]
        return model_pricing

    # Fallback or partial match could be implemented here if needed
    # For now, return empty dict to signal no pricing data
    return {}
