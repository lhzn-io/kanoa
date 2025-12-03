from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pytest
from dotenv import load_dotenv

from kanoa.core.interpreter import AnalyticsInterpreter

from .conftest import get_cost_tracker

# Load API keys from user config directory
config_dir = Path.home() / ".config" / "kanoa"
if (config_dir / ".env").exists():
    load_dotenv(config_dir / ".env")


def has_vllm_server() -> bool:
    """Check if vLLM server is running on localhost:8000."""
    import urllib.error
    import urllib.request

    try:
        # Try to connect to the vLLM server
        with urllib.request.urlopen(
            "http://localhost:8000/v1/models", timeout=2
        ) as response:
            # Explicitly check status to satisfy mypy
            status_code: int = response.status
            return status_code == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


# Module-level skip condition
pytestmark = [
    pytest.mark.integration,
    pytest.mark.molmo,
    pytest.mark.skipif(
        not has_vllm_server(),
        reason=(
            "vLLM server not available on http://localhost:8000. "
            "Start server with: vllm serve allenai/Molmo-7B-D-0924"
        ),
    ),
]


class TestMolmoIntegration:
    """Integration tests for Molmo backend via vLLM."""

    @pytest.fixture(scope="class")
    def interpreter(self) -> Any:
        """
        Initialize Molmo backend via vLLM.

        Requires vLLM server running on http://localhost:8000.
        """
        try:
            return AnalyticsInterpreter(
                backend="openai",
                api_base="http://localhost:8000/v1",
                model="allenai/Molmo-7B-D-0924",
                api_key="EMPTY",  # pragma: allowlist secret
            )
        except Exception as e:
            pytest.skip(
                f"Could not initialize Molmo backend: {e}\n"
                "Ensure vLLM server is running on port 8000."
            )

    def test_hello_world_generation(self, interpreter: Any) -> None:
        """
        Simple 'Golden Set' test:
        Verify that Molmo can see a sine wave and identify it.
        """
        print("\n" + "=" * 50)
        print("[TEST] Hello World (Vision) - Molmo")
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

        print(f"\n[USER] {context} | {focus}")

        try:
            result = interpreter.interpret(fig=plt.gcf(), context=context, focus=focus)
        except Exception as e:
            pytest.fail(f"Molmo API call failed: {e}")

        # 3. Assertions (Golden Set check)
        model_name = result.metadata.get("model", "AI") if result.metadata else "AI"
        print(f"[AI] {model_name}: " f"{result.text[:50].replace(chr(10), ' ')}...")

        assert result.text is not None
        assert len(result.text) > 50
        # Check for semantic correctness (loose check)
        assert "sine" in result.text.lower() or "sinusoidal" in result.text.lower()

        # Check metadata
        assert result.backend == "openai"
        assert result.usage is not None
        assert result.usage.cost >= 0  # Local inference, cost is estimated

        # Record and print cost
        cost = result.usage.cost
        get_cost_tracker().record("test_hello_world_generation", cost)
        print(f"\n[COST] ${cost:.6f}")

    def test_text_only_reasoning(self, interpreter: Any) -> None:
        """
        Verify text-only reasoning capabilities.
        """
        print("\n" + "=" * 50)
        print("[TEST] Text Reasoning - Molmo")
        print("=" * 50)

        data = {"revenue": [100, 120, 150, 140], "quarter": ["Q1", "Q2", "Q3", "Q4"]}
        context = "Quarterly revenue report"
        focus = "Identify the trend"

        print(f"\n[USER] {context} | {focus}")

        try:
            result = interpreter.interpret(data=data, context=context, focus=focus)
        except Exception as e:
            pytest.fail(f"Molmo API call failed: {e}")

        model_name = result.metadata.get("model", "AI") if result.metadata else "AI"
        print(f"[AI] {model_name}: " f"{result.text[:50].replace(chr(10), ' ')}...")

        assert result.text is not None
        assert len(result.text) > 20
        # Molmo should be able to analyze the data trend
        assert "increase" in result.text.lower() or "growth" in result.text.lower()

        # Record and print cost
        cost = result.usage.cost
        get_cost_tracker().record("test_text_only_reasoning", cost)
        print(f"\n[COST] ${cost:.6f}")
