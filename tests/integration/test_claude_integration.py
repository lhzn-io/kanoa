import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pytest
from dotenv import load_dotenv

from kanoa.core.interpreter import AnalyticsInterpreter

# Load API keys from user config directory
config_dir = Path.home() / ".config" / "kanoa"
if (config_dir / ".env").exists():
    load_dotenv(config_dir / ".env")


def has_credentials() -> bool:
    """Check if ANTHROPIC_API_KEY is set."""
    return os.environ.get("ANTHROPIC_API_KEY") is not None


# Module-level skip condition
pytestmark = [
    pytest.mark.integration,
    pytest.mark.claude,
    pytest.mark.skipif(
        not has_credentials(),
        reason=(
            "Missing Anthropic API key. See: "
            "https://github.com/lhzn-io/kanoa/blob/main/docs/source/user_guide/"
            "authentication.md"
        ),
    ),
]


class TestClaudeIntegration:
    @pytest.fixture(scope="class")
    def interpreter(self) -> Any:
        """
        Initialize Claude backend with Haiku model for cost-effective testing.

        Requires ANTHROPIC_API_KEY environment variable.
        Get your key at: https://console.anthropic.com/
        """
        try:
            return AnalyticsInterpreter(
                backend="claude", model="claude-haiku-4-5-20251022"
            )
        except Exception as e:
            pytest.skip(
                f"Could not initialize Claude backend: {e}\n"
                "Your API key may be invalid or expired."
            )

    def test_hello_world_generation(self, interpreter: Any) -> None:
        """
        Simple 'Golden Set' test:
        Verify that Claude can see a sine wave and identify it.
        """
        print("\n" + "=" * 50)
        print("[test] Hello World (Vision) - Claude")
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
            pytest.fail(f"Claude API call failed: {e}")

        # 3. Assertions (Golden Set check)
        print(
            f"[model] {result.metadata.get('model', 'AI')}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        assert result.text is not None
        assert len(result.text) > 50
        # Check for semantic correctness (loose check)
        assert "sine" in result.text.lower() or "sinusoidal" in result.text.lower()

        # Check metadata
        assert result.backend == "claude"
        assert result.usage is not None
        assert result.usage.cost > 0

        print(f"\n[cost] ${result.usage.cost:.6f}")

    def test_text_only_reasoning(self, interpreter: Any) -> None:
        """
        Verify text-only reasoning capabilities.
        """
        print("\n" + "=" * 50)
        print("[test] Text Reasoning - Claude")
        print("=" * 50)

        data = {
            "dissolved_oxygen": [6.5, 6.8, 7.2, 7.0],
            "site": ["Site A", "Site B", "Site C", "Site D"],
        }
        context = "Water quality monitoring report"
        focus = "Identify the trend"

        print(f"\n[user] {context} | {focus}")

        result = interpreter.interpret(data=data, context=context, focus=focus)

        print(
            f"[model] {result.metadata.get('model', 'AI')}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        assert "increase" in result.text.lower() or "growth" in result.text.lower()
        assert "Site C" in result.text

        print(f"\n[cost] ${result.usage.cost:.6f}")

    def test_knowledge_base_integration(self, interpreter: Any, tmp_path: Any) -> None:
        """
        Test Claude with text-based knowledge base.
        """
        print("\n" + "=" * 50)
        print("[test] Knowledge Base Integration - Claude")
        print("=" * 50)

        # Create temporary knowledge base
        kb_dir = tmp_path / "kb"
        kb_dir.mkdir()
        kb_file = kb_dir / "context.md"
        kb_file.write_text(
            """# Domain Knowledge

This is a test dataset for marine biology research.
The sine wave represents simulated dive depth over time.
"""
        )

        # Initialize interpreter with KB (using Haiku for cost savings)
        kb_interpreter = AnalyticsInterpreter(
            backend="claude",
            model="claude-haiku-4-5-20251022",
            kb_path=str(kb_dir),
            kb_type="text",
        )

        # Create test figure
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure(figsize=(8, 4))
        plt.plot(x, y)
        plt.title("Dive Depth Simulation")

        result = kb_interpreter.interpret(
            fig=plt.gcf(),
            context="Marine biology dive profile",
            focus="Interpret using domain knowledge",
        )

        print(
            f"[model] {result.metadata.get('model', 'AI') if result.metadata else 'AI'}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        # Should reference the knowledge base context
        assert "dive" in result.text.lower() or "depth" in result.text.lower()

        if result.usage:
            print(f"\n[cost] ${result.usage.cost:.6f}")
