"""Tests for global prompt configuration."""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from kanoa.config import PromptConfig
from kanoa.prompt_config import get_global_prompts, load_prompt_config
from kanoa.utils.prompts import PromptTemplates


def test_load_prompt_config_nonexistent() -> None:
    """Test loading from non-existent config file."""
    result = load_prompt_config(Path("/nonexistent/prompts.yaml"))
    assert result is None


def test_load_prompt_config_basic() -> None:
    """Test loading basic prompt config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            """
system_prompt: |
  You are a financial analyst...

user_prompt: |
  Analyze this data...
"""
        )
        f.flush()
        config_path = Path(f.name)

    try:
        templates = load_prompt_config(config_path)
        assert templates is not None
        assert "financial analyst" in templates.system_prompt
        assert "Analyze this data" in templates.user_prompt
    finally:
        config_path.unlink()


def test_load_prompt_config_with_backend_overrides() -> None:
    """Test loading config with backend-specific overrides."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            """
system_prompt: |
  You are a data analyst...

backends:
  gemini:
    system_prompt: |
      You are a Google AI assistant...
  claude:
    user_prompt: |
      Be concise...
"""
        )
        f.flush()
        config_path = Path(f.name)

    try:
        templates = load_prompt_config(config_path)
        assert templates is not None
        assert "data analyst" in templates.system_prompt

        # Check backend overrides
        assert "gemini" in templates.backend_overrides
        assert "Google AI assistant" in templates.backend_overrides["gemini"]["system_prompt"]
        assert "claude" in templates.backend_overrides
        assert "Be concise" in templates.backend_overrides["claude"]["user_prompt"]
    finally:
        config_path.unlink()


def test_load_prompt_config_partial() -> None:
    """Test loading config with only some fields specified."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            """
user_prompt: |
  Provide detailed analysis...
"""
        )
        f.flush()
        config_path = Path(f.name)

    try:
        templates = load_prompt_config(config_path)
        assert templates is not None
        # user_prompt should be custom
        assert "detailed analysis" in templates.user_prompt
        # system_prompt should use default
        assert "expert data analyst" in templates.system_prompt.lower()
    finally:
        config_path.unlink()


def test_load_prompt_config_invalid_yaml() -> None:
    """Test loading invalid YAML returns None."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [[[")
        f.flush()
        config_path = Path(f.name)

    try:
        templates = load_prompt_config(config_path)
        assert templates is None
    finally:
        config_path.unlink()


def test_load_prompt_config_empty() -> None:
    """Test loading empty config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        f.flush()
        config_path = Path(f.name)

    try:
        templates = load_prompt_config(config_path)
        assert templates is None
    finally:
        config_path.unlink()


def test_get_global_prompts() -> None:
    """Test get_global_prompts() function."""
    # This will return None unless the user has a config file
    result = get_global_prompts()
    # Should not raise an error
    assert result is None or isinstance(result, PromptTemplates)


def test_prompt_config_lazy_loading() -> None:
    """Test PromptConfig lazy loads templates."""
    config = PromptConfig()
    assert config._loaded is False

    # Access templates triggers loading
    _ = config.templates
    assert config._loaded is True


def test_prompt_config_reload() -> None:
    """Test PromptConfig reload() method."""
    config = PromptConfig()

    # Trigger initial load
    _ = config.templates
    assert config._loaded is True

    # Reload should reset loaded flag
    config.reload()
    assert config._loaded is False

    # Next access should reload
    _ = config.templates
    assert config._loaded is True
