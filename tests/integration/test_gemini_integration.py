import os
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pytest

from kanoa.core.interpreter import AnalyticsInterpreter


# Check if we can run integration tests
def has_credentials():
    # Check for API key
    if os.environ.get("GOOGLE_API_KEY"):
        return True

    # Check for ADC (rudimentary check)
    # In a real scenario, we might try to instantiate credentials,
    # but for now we'll assume if the user runs integration tests they have set it up.
    # We can also check for the well-known ADC file, but that's OS specific.
    # Let's rely on the test failing gracefully or being skipped if we want to be
    # strict.
    # For now, we'll assume true if explicitly requested via marker,
    # but we can add a check to skip if init fails.
    return True


@pytest.mark.integration
@pytest.mark.gemini
class TestGeminiIntegration:
    @pytest.fixture(scope="class")
    def interpreter(self) -> Any:
        try:
            # Try to initialize with ADC or Env Var
            return AnalyticsInterpreter(backend="gemini-3")
        except Exception as e:
            pytest.skip(
                f"Skipping test: Could not initialize Gemini backend. Error: {e}"
            )

    def test_hello_world_generation(self, interpreter: Any) -> None:
        """
        Simple 'Golden Set' test:
        Verify that Gemini can see a sine wave and identify it.
        """
        print("\n" + "=" * 50)
        print("📐 TEST: Hello World (Vision)")
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

        print(f"\n� User: {context} | {focus}")

        try:
            result = interpreter.interpret(fig=plt.gcf(), context=context, focus=focus)
        except Exception as e:
            pytest.fail(f"Gemini API call failed: {e}")

        # 3. Assertions (Golden Set check)
        print(
            f"🎓 {result.metadata.get('model', 'AI')}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        assert result.text is not None
        assert len(result.text) > 50
        # Check for semantic correctness (loose check)
        assert "sine" in result.text.lower() or "sinusoidal" in result.text.lower()

        # Check metadata
        assert result.backend == "gemini-3"
        assert result.usage is not None
        assert result.usage.cost > 0

        print(f"\n💰 Cost: ${result.usage.cost:.6f}")

    def test_text_only_reasoning(self, interpreter: Any) -> None:
        """
        Verify text-only reasoning capabilities.
        """
        print("\n" + "=" * 50)
        print("📐 TEST: Text Reasoning")
        print("=" * 50)

        data = {"revenue": [100, 120, 150, 140], "quarter": ["Q1", "Q2", "Q3", "Q4"]}
        context = "Quarterly revenue report"
        focus = "Identify the trend"

        print(f"\n� User: {context} | {focus}")

        result = interpreter.interpret(data=data, context=context, focus=focus)

        print(
            f"🎓 {result.metadata.get('model', 'AI')}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        assert "increase" in result.text.lower() or "growth" in result.text.lower()
        assert "Q3" in result.text

        print(f"\n💰 Cost: ${result.usage.cost:.6f}")
