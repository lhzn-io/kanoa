import subprocess
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


def has_copilot_cli() -> bool:
    """
    Check if GitHub Copilot CLI is installed and accessible.

    This checks if the 'copilot' command is available in PATH.
    """
    try:
        result = subprocess.run(
            ["copilot", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def has_gh_auth() -> bool:
    """
    Check if GitHub CLI is authenticated.

    This verifies that 'gh auth status' succeeds, which is required
    for the Copilot CLI to work.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def has_credentials() -> bool:
    """
    Check if GitHub Copilot credentials are available.

    Requires both:
    1. Copilot CLI installed
    2. GitHub CLI authenticated (gh auth login)
    """
    return has_copilot_cli() and has_gh_auth()


# Module-level skip condition
pytestmark = [
    pytest.mark.integration,
    pytest.mark.github_copilot,
    pytest.mark.skipif(
        not has_credentials(),
        reason=(
            "GitHub Copilot not configured. "
            "Install: gh extension install github/gh-copilot && gh auth login. "
            "See: https://github.com/lhzn-io/kanoa/blob/main/docs/source/user_guide/"
            "backends.md#github-copilot-sdk-github-copilot"
        ),
    ),
]


class TestGitHubCopilotIntegration:
    @pytest.fixture(scope="class")
    def interpreter(self) -> Any:
        """
        Initialize GitHub Copilot backend with GPT-5 model.

        Requires:
        - GitHub Copilot subscription (Individual, Business, or Enterprise)
        - Copilot CLI installed: gh extension install github/gh-copilot
        - GitHub CLI authenticated: gh auth login

        The backend uses the Copilot CLI via JSON-RPC.
        """
        try:
            return AnalyticsInterpreter(
                backend="github-copilot",
                model="gpt-5",
            )
        except Exception as e:
            pytest.skip(
                f"Could not initialize GitHub Copilot backend: {e}\n"
                "Ensure you have:\n"
                "1. Active GitHub Copilot subscription\n"
                "2. Copilot CLI installed (gh extension install github/gh-copilot)\n"
                "3. Authenticated with GitHub (gh auth login)"
            )

    def test_hello_world_generation(self, interpreter: Any) -> None:
        """
        Simple 'Golden Set' test:
        Verify that GitHub Copilot can interpret a sine wave plot.

        Note: Vision support in GitHub Copilot SDK is currently limited.
        This test focuses on text-based interpretation.
        """
        print("\n" + "=" * 50)
        print("[test] Hello World - GitHub Copilot")
        print("=" * 50)

        # 1. Create artifact
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure(figsize=(8, 4))
        plt.plot(x, y)
        plt.title("Test Sine Wave")

        # 2. Interpret (note: figure may have limited support in current SDK)
        context = "Verification test run with sine wave data"
        focus = "Identify the waveform pattern"

        print(f"\n[user] {context} | {focus}")

        try:
            result = interpreter.interpret(
                stream=False,
                fig=plt.gcf(),
                data={"x": x[:5].tolist(), "y": y[:5].tolist()},  # Sample data
                context=context,
                focus=focus,
            )
        except Exception as e:
            pytest.fail(f"GitHub Copilot API call failed: {e}")

        # 3. Assertions (Golden Set check)
        model_name = result.metadata.get("model", "AI") if result.metadata else "AI"
        print(f"[model] {model_name}: {result.text[:50].replace(chr(10), ' ')}...")

        assert result.text is not None
        assert len(result.text) > 50

        # Check metadata
        assert result.backend == "github-copilot"
        assert result.usage is not None
        assert result.usage.cost >= 0  # Cost may be covered by subscription

        print(f"\n[estimated cost] ${result.usage.cost:.6f}")
        print(
            "[note] Token counts are estimated. GitHub Copilot SDK "
            "doesn't expose actual token usage yet."
        )

    def test_text_only_reasoning(self, interpreter: Any) -> None:
        """
        Verify text-only reasoning capabilities.

        This is the recommended approach for GitHub Copilot SDK
        until vision support is fully implemented.
        """
        print("\n" + "=" * 50)
        print("[test] Text Reasoning - GitHub Copilot")
        print("=" * 50)

        data = {
            "temperature": [20.1, 21.5, 23.2, 22.8],
            "location": ["Site A", "Site B", "Site C", "Site D"],
        }
        context = "Temperature monitoring report"
        focus = "Identify the temperature trend"

        print(f"\n[user] {context} | {focus}")

        result = interpreter.interpret(
            stream=False, data=data, context=context, focus=focus
        )

        model_name = result.metadata.get("model", "AI") if result.metadata else "AI"
        print(f"[model] {model_name}: {result.text[:50].replace(chr(10), ' ')}...")

        assert result.text is not None
        assert len(result.text) > 20

        print(f"\n[estimated cost] ${result.usage.cost:.6f}")

    def test_streaming_response(self, interpreter: Any) -> None:
        """
        Verify streaming functionality works with GitHub Copilot.

        GitHub Copilot SDK supports real-time streaming responses.
        """
        print("\n" + "=" * 50)
        print("[test] Streaming Response - GitHub Copilot")
        print("=" * 50)

        data = {"values": [1, 2, 3, 4, 5]}
        context = "Simple data analysis"
        focus = "Describe the pattern"

        print(f"\n[user] {context} | {focus}")
        print("[model] ", end="", flush=True)

        chunks_received = 0
        full_text = []

        try:
            for chunk in interpreter.interpret(
                stream=True, data=data, context=context, focus=focus
            ):
                if chunk.type == "text":
                    print(chunk.content, end="", flush=True)
                    full_text.append(chunk.content)
                    chunks_received += 1
                elif chunk.type == "usage" and chunk.usage:
                    print(f"\n\n[estimated cost] ${chunk.usage.cost:.6f}")
                    print(f"[chunks received] {chunks_received}")

            # Assertions
            assert chunks_received > 0, "Should receive at least one text chunk"
            assert len(full_text) > 0, "Should have accumulated text"

            combined_text = "".join(full_text)
            assert len(combined_text) > 20, "Combined text should have substance"

        except Exception as e:
            pytest.fail(f"Streaming failed: {e}")

    def test_knowledge_base_integration(self, interpreter: Any, tmp_path: Any) -> None:
        """
        Test GitHub Copilot with text-based knowledge base.

        Note: GitHub Copilot SDK currently supports text files only.
        PDF support is not yet available.
        """
        print("\n" + "=" * 50)
        print("[test] Knowledge Base Integration - GitHub Copilot")
        print("=" * 50)

        # Create temporary knowledge base
        kb_dir = tmp_path / "kb"
        kb_dir.mkdir()
        kb_file = kb_dir / "context.md"
        kb_file.write_text(
            """# Domain Knowledge

This is test data for software performance analysis.
The values represent response times in milliseconds.
Acceptable range: 0-100ms.
"""
        )

        # Initialize interpreter with KB
        kb_interpreter = AnalyticsInterpreter(
            backend="github-copilot",
            model="gpt-5",
            kb_path=str(kb_dir),
            kb_type="text",
        )

        data = {"response_times_ms": [45, 52, 89, 120, 95]}

        result = kb_interpreter.interpret(
            stream=False,
            data=data,
            context="Performance monitoring data",
            focus="Interpret using domain knowledge about acceptable ranges",
        )

        print(
            f"[model] {result.metadata.get('model', 'AI') if result.metadata else 'AI'}: "
            f"{result.text[:50].replace(chr(10), ' ')}..."
        )

        # Should reference the knowledge base context
        assert result.text is not None
        assert len(result.text) > 50

        if result.usage:
            print(f"\n[estimated cost] ${result.usage.cost:.6f}")
