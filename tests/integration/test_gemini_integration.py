import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pytest
from dotenv import load_dotenv

from kanoa.core.interpreter import AnalyticsInterpreter

from .conftest import get_auth_state, get_cost_tracker

# Load API keys from user config directory
config_dir = Path.home() / ".config" / "kanoa"
if (config_dir / ".env").exists():
    load_dotenv(config_dir / ".env")


def has_potential_credentials() -> bool:
    """
    Quick check if credentials might be available.

    This is a fast, non-blocking check that looks for credential files/env vars.
    It does NOT validate that credentials are working - that happens lazily
    when the first test actually runs.
    """
    # Check for API key
    if os.environ.get("GOOGLE_API_KEY"):
        return True

    # Check for service account key file
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True

    # Check for ADC credentials file (from gcloud auth application-default login)
    adc_path = (
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    )
    return adc_path.exists()


# Module-level skip - only skip if NO credentials exist at all
pytestmark = [
    pytest.mark.integration,
    pytest.mark.gemini,
    pytest.mark.skipif(
        not has_potential_credentials(),
        reason=(
            "No Gemini credentials found. See: "
            "https://github.com/lhzn-io/kanoa/blob/main/docs/source/user_guide/"
            "authentication.md"
        ),
    ),
]


def _is_auth_error(error_msg: str) -> bool:
    """Check if an error message indicates an authentication failure."""
    auth_keywords = ["401", "403", "auth", "credential", "permission", "token"]
    return any(kw in error_msg.lower() for kw in auth_keywords)


class TestGeminiIntegration:
    """Integration tests for Gemini backend (no caching)."""

    @pytest.fixture(scope="class")
    def interpreter(self) -> Any:
        """
        Initialize Gemini backend with lazy auth validation.

        If initialization fails due to auth issues, we mark the backend
        as failed so subsequent tests skip immediately.
        """
        auth_state = get_auth_state()

        # Check if we already know auth is broken
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Gemini auth previously failed: {error}")

        try:
            interp = AnalyticsInterpreter(backend="gemini", model="gemini-2.5-flash")
            auth_state.mark_auth_ok("gemini")
            return interp
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(
                    f"Gemini auth failed: {error_msg}\n"
                    "Try: gcloud auth application-default login"
                )
            else:
                # Non-auth error, let it fail normally
                pytest.fail(f"Could not initialize Gemini backend: {e}")

    def test_hello_world_generation(self, interpreter: Any) -> None:
        """
        Simple 'Golden Set' test:
        Verify that Gemini can see a sine wave and identify it.
        """
        auth_state = get_auth_state()
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Skipping due to previous auth failure: {error}")

        print("\n" + "=" * 50)
        print("[test] Hello World (Vision)")
        print("=" * 50)

        # 1. Create artifact
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure(figsize=(8, 4))
        plt.plot(x, y)
        plt.title("Test Sine Wave")

        # 2. Interpret
        context = "Verification test run"
        focus = "Identify the waveform shape"

        print(f"\n[user] {context} | {focus}")

        try:
            result = interpreter.interpret(fig=plt.gcf(), context=context, focus=focus)
        except Exception as e:
            error_msg = str(e)
            # Check if this is an auth error (could happen on first actual API call)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(f"Gemini auth failed on API call: {error_msg}")
            raise

        # 3. Assertions (Golden Set check)
        model_name = result.metadata.get("model", "AI") if result.metadata else "AI"
        print(f"[model] {model_name}: {result.text[:50].replace(chr(10), ' ')}...")

        assert result.text is not None
        assert len(result.text) > 50
        # Check for semantic correctness (loose check)
        assert "sine" in result.text.lower() or "sinusoidal" in result.text.lower()

        # Check metadata
        assert result.backend == "gemini"
        assert result.usage is not None
        # gemini-2.5-flash is free, so cost may be 0
        assert result.usage.input_tokens > 0

        # Record and print cost
        cost = result.usage.cost
        get_cost_tracker().record("test_hello_world_generation", cost)
        print(f"\n[cost] ${cost:.6f}")

    def test_text_only_reasoning(self, interpreter: Any) -> None:
        """
        Verify text-only reasoning capabilities.
        """
        auth_state = get_auth_state()
        error = auth_state.should_skip("gemini")
        if error:
            pytest.skip(f"Skipping due to previous auth failure: {error}")

        print("\n" + "=" * 50)
        print("[test] Text Reasoning")
        print("=" * 50)

        data = {
            "dissolved_oxygen": [6.5, 6.8, 7.2, 7.0],
            "site": ["Site A", "Site B", "Site C", "Site D"],
        }
        context = "Water quality monitoring report"
        focus = "Identify the trend"

        print(f"\n[user] {context} | {focus}")

        try:
            result = interpreter.interpret(data=data, context=context, focus=focus)
        except Exception as e:
            error_msg = str(e)
            if _is_auth_error(error_msg):
                auth_state.mark_auth_failed("gemini", error_msg)
                pytest.skip(f"Gemini auth failed on API call: {error_msg}")
            raise

        model_name = result.metadata.get("model", "AI") if result.metadata else "AI"
        print(f"[model] {model_name}: {result.text[:50].replace(chr(10), ' ')}...")

        assert "increase" in result.text.lower() or "growth" in result.text.lower()
        assert "Site C" in result.text

        # Record and print cost
        cost = result.usage.cost
        get_cost_tracker().record("test_text_only_reasoning", cost)
        print(f"\n[cost] ${cost:.6f}")
