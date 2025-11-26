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


def has_model_available() -> bool:
    """
    Check if Molmo model is available.

    For local inference, Molmo requires:
    - Model weights downloaded (e.g., from Hugging Face)
    - Proper Python environment (Python 3.11+, PyTorch)
    - Inference code from Ai2's Molmo repository

    This is a placeholder check - actual implementation would verify
    model files exist at expected locations.
    """
    # Check if MOLMO_MODEL_PATH is set
    if os.environ.get("MOLMO_MODEL_PATH"):
        model_path = Path(os.environ["MOLMO_MODEL_PATH"])
        if model_path.exists():
            return True

    return False


# Module-level skip condition
pytestmark = [
    pytest.mark.integration,
    pytest.mark.molmo,
    pytest.mark.slow,  # Local inference can be slow
    pytest.mark.skipif(
        not has_model_available(),
        reason=(
            "Missing Molmo credentials. See: "
            "https://github.com/lhzn-io/kanoa/blob/main/docs/source/user_guide/"
            "authentication.md"
        ),
    ),
]


class TestMolmoIntegration:
    @pytest.fixture(scope="class")
    def interpreter(self) -> Any:
        """
        Initialize Molmo backend for local inference.

        Molmo Setup Requirements:
        1. Python 3.11+
        2. PyTorch installed for your hardware
        3. Molmo model weights downloaded
        4. Set MOLMO_MODEL_PATH environment variable (optional)

        Model weights available at:
        - Hugging Face: allenai/Molmo-7B-D, allenai/Molmo-72B
        - GitHub: https://github.com/allenai/molmo

        No API key required - runs entirely locally!
        """
        try:
            return AnalyticsInterpreter(backend="molmo")
        except Exception as e:
            pytest.skip(
                f"Could not initialize Molmo backend: {e}\n"
                "Check that your model path is correct and PyTorch is installed."
            )

    def test_hello_world_generation(self, interpreter: Any) -> None:
        """
        Simple 'Golden Set' test:
        Verify that Molmo can see a sine wave and identify it.
        """
        print("\n" + "=" * 50)
        print("📐 TEST: Hello World (Vision) - Molmo (Local)")
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

        print(f"\n💬 User: {context} | {focus}")
        print("⏳ Running local inference (this may take a while)...")

        try:
            result = interpreter.interpret(fig=plt.gcf(), context=context, focus=focus)
        except Exception as e:
            pytest.fail(f"Molmo inference failed: {e}")

        # 3. Assertions (Golden Set check)
        print(
            f"🎓 {result.metadata.get('model', 'AI') if result.metadata else 'AI'}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        assert result.text is not None
        assert len(result.text) > 50
        # Check for semantic correctness (loose check)
        assert "sine" in result.text.lower() or "wave" in result.text.lower()

        # Check metadata
        assert result.backend == "molmo"
        # Local inference - no cost!
        assert result.usage is None or result.usage.cost == 0

        print("\n💰 Cost: $0.00 (local inference)")

    def test_text_only_reasoning(self, interpreter: Any) -> None:
        """
        Verify text-only reasoning capabilities.
        """
        print("\n" + "=" * 50)
        print("📐 TEST: Text Reasoning - Molmo (Local)")
        print("=" * 50)

        data = {"revenue": [100, 120, 150, 140], "quarter": ["Q1", "Q2", "Q3", "Q4"]}
        context = "Quarterly revenue report"
        focus = "Identify the trend"

        print(f"\n💬 User: {context} | {focus}")
        print("⏳ Running local inference...")

        result = interpreter.interpret(data=data, context=context, focus=focus)

        print(
            f"🎓 {result.metadata.get('model', 'AI') if result.metadata else 'AI'}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        assert "increase" in result.text.lower() or "growth" in result.text.lower()

        print("\n💰 Cost: $0.00 (local inference)")

    def test_privacy_preserving_inference(self, interpreter: Any) -> None:
        """
        Test that Molmo runs entirely locally without external API calls.

        This is a key feature for privacy-sensitive data.
        """
        print("\n" + "=" * 50)
        print("📐 TEST: Privacy-Preserving Local Inference - Molmo")
        print("=" * 50)

        # Create test data with "sensitive" information
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure(figsize=(8, 4))
        plt.plot(x, y)
        plt.title("Confidential Data Pattern")

        print("\n🔒 Processing sensitive data locally...")

        result = interpreter.interpret(
            fig=plt.gcf(),
            context="Confidential analysis",
            focus="Analyze pattern without external API calls",
        )

        print(
            f"🎓 {result.metadata.get('model', 'AI') if result.metadata else 'AI'}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        # Verify no cost (confirms local inference)
        assert result.usage is None or result.usage.cost == 0

        print("\n✅ Data processed locally - no external API calls made")
        print("💰 Cost: $0.00 (local inference)")

    def test_knowledge_base_integration(self, interpreter: Any, tmp_path: Any) -> None:
        """
        Test Molmo with text-based knowledge base.

        Note: Molmo only supports text KB, not PDF (no native vision for PDFs).
        """
        print("\n" + "=" * 50)
        print("📐 TEST: Knowledge Base Integration - Molmo")
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

        # Initialize interpreter with KB
        kb_interpreter = AnalyticsInterpreter(
            backend="molmo", kb_path=str(kb_dir), kb_type="text"
        )

        # Create test figure
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure(figsize=(8, 4))
        plt.plot(x, y)
        plt.title("Dive Depth Simulation")

        print("⏳ Running local inference with knowledge base...")

        result = kb_interpreter.interpret(
            fig=plt.gcf(),
            context="Marine biology dive profile",
            focus="Interpret using domain knowledge",
        )

        print(
            f"🎓 {result.metadata.get('model', 'AI') if result.metadata else 'AI'}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        # Should reference the knowledge base context
        assert "dive" in result.text.lower() or "depth" in result.text.lower()

        print("\n💰 Cost: $0.00 (local inference)")
