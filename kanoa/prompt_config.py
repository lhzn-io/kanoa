"""
Global prompt configuration loader.

This module provides functionality to load and manage prompt configurations
from YAML files, similar to the pricing configuration system.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .utils.prompts import PromptTemplates

# Default user config path
USER_CONFIG_PATH = Path.home() / ".config" / "kanoa" / "prompts.yaml"


def load_prompt_config(config_path: Optional[Path] = None) -> Optional[PromptTemplates]:
    """
    Load prompt configuration from YAML file.

    The configuration file should have the following structure:

    ```yaml
    system_prompt: |
        You are a senior data scientist with expertise in...

    user_prompt: |
        Analyze this data and provide:
        - Executive Summary
        - Key Findings

    # Per-backend customization (optional)
    backends:
      gemini:
        system_prompt: |
          You are a Google AI assistant...
      claude:
        user_prompt: |
          Provide concise analysis...
    ```

    Args:
        config_path: Path to YAML config file. If None, uses
            ~/.config/kanoa/prompts.yaml

    Returns:
        PromptTemplates instance with loaded configuration, or None if
        config file doesn't exist or is invalid.

    Example:
        >>> templates = load_prompt_config()
        >>> if templates:
        ...     print(templates.system_prompt)
    """
    # Use default path if not specified
    path = config_path or USER_CONFIG_PATH

    # Return None if file doesn't exist (not an error)
    if not path.exists():
        return None

    try:
        with open(path, "r") as f:
            config: Dict[str, Any] = yaml.safe_load(f)

        if not config:
            return None

        # Extract prompts
        system_prompt = config.get("system_prompt")
        user_prompt = config.get("user_prompt")

        # Extract backend overrides
        backend_overrides: Dict[str, Dict[str, str]] = {}
        if "backends" in config:
            backend_overrides = config["backends"]

        # Create PromptTemplates instance
        # Use defaults from DEFAULT_PROMPTS if not specified in config
        from .utils.prompts import DEFAULT_PROMPTS

        templates = PromptTemplates(
            system_prompt=system_prompt or DEFAULT_PROMPTS.system_prompt,
            user_prompt=user_prompt or DEFAULT_PROMPTS.user_prompt,
            backend_overrides=backend_overrides,
        )

        return templates

    except Exception:
        # Silently return None on parsing errors (similar to pricing.py)
        return None


def get_global_prompts() -> Optional[PromptTemplates]:
    """
    Get global prompt configuration.

    This is a convenience function that loads from the default user
    config path (~/.config/kanoa/prompts.yaml).

    Returns:
        PromptTemplates instance with global configuration, or None if
        no config file exists.

    Example:
        >>> prompts = get_global_prompts()
        >>> if prompts:
        ...     interp = AnalyticsInterpreter(
        ...         system_prompt=prompts.system_prompt
        ...     )
    """
    return load_prompt_config()
