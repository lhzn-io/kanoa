from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import matplotlib.pyplot as plt
import pytest

from kanoa.core.types import InterpretationResult


class TestGitHubCopilotBackend:
    @pytest.fixture
    def mock_copilot_import(self) -> Any:
        """Mock the copilot import to avoid requiring the SDK."""
        # Create mock CopilotClient class
        mock_client_class = MagicMock()

        # Create mock client instance
        mock_client = MagicMock()
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()
        mock_client.create_session = AsyncMock()

        # Configure the mock class to return the mock client
        mock_client_class.return_value = mock_client

        # Create mock session
        mock_session = MagicMock()
        mock_session.send = AsyncMock()
        mock_session.destroy = AsyncMock()
        mock_session.on = MagicMock()

        # Configure create_session to return the mock session
        mock_client.create_session.return_value = mock_session

        # Mock the import
        with patch.dict(
            "sys.modules", {"copilot": MagicMock(CopilotClient=mock_client_class)}
        ):
            yield {
                "client_class": mock_client_class,
                "client": mock_client,
                "session": mock_session,
            }

    def test_initialization(self, mock_copilot_import: Any) -> None:
        """Test GitHubCopilotBackend initialization."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(model="gpt-5")
        assert backend.model == "gpt-5"
        assert backend.backend_name == "github-copilot"

    def test_initialization_custom_cli(self, mock_copilot_import: Any) -> None:
        """Test GitHubCopilotBackend initialization with custom CLI path."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(
            cli_path="/usr/local/bin/copilot",
            cli_url="localhost:8080",
            model="gpt-5",
        )
        assert backend.cli_path == "/usr/local/bin/copilot"
        assert backend.cli_url == "localhost:8080"

    def test_interpret_text_only(self, mock_copilot_import: Any) -> None:
        """Test interpretation with text data only."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(model="gpt-5")

        # Mock the async run to return a simple result
        with patch("kanoa.backends.github_copilot.asyncio.run") as mock_run:
            from kanoa.core.types import InterpretationChunk

            mock_run.return_value = {
                "chunks": [
                    InterpretationChunk(content="Interpretation result", type="text")
                ],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 20,
                },
            }

            result = backend.interpret_blocking(
                fig=None,
                data="Some data",
                context="Context",
                focus="Focus",
                kb_context=None,
                custom_prompt=None,
            )

            assert isinstance(result, InterpretationResult)
            assert "Interpretation result" in result.text
            assert result.backend == "github-copilot"
            assert result.usage is not None
            assert result.usage.input_tokens == 10
            assert result.usage.output_tokens == 20
            assert result.usage.cost >= 0.0

    def test_interpret_with_figure(self, mock_copilot_import: Any) -> None:
        """Test interpretation with a figure."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(model="gpt-5")

        with patch("kanoa.backends.github_copilot.asyncio.run") as mock_run:
            from kanoa.core.types import InterpretationChunk

            mock_run.return_value = {
                "chunks": [
                    InterpretationChunk(content="Figure interpretation", type="text")
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                },
            }

            fig = plt.figure()
            result = backend.interpret_blocking(
                fig=fig,
                data=None,
                context=None,
                focus=None,
                kb_context=None,
                custom_prompt=None,
            )

            assert isinstance(result, InterpretationResult)
            assert "Figure interpretation" in result.text
            assert result.usage is not None
            assert result.usage.input_tokens == 100
            assert result.usage.output_tokens == 50

    def test_interpret_with_custom_prompt(self, mock_copilot_import: Any) -> None:
        """Test interpretation with a custom prompt."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(model="gpt-5")

        with patch("kanoa.backends.github_copilot.asyncio.run") as mock_run:
            from kanoa.core.types import InterpretationChunk

            mock_run.return_value = {
                "chunks": [InterpretationChunk(content="Custom response", type="text")],
                "usage": {
                    "input_tokens": 15,
                    "output_tokens": 25,
                },
            }

            result = backend.interpret_blocking(
                fig=None,
                data=None,
                context=None,
                focus=None,
                kb_context=None,
                custom_prompt="Custom prompt",
            )

            assert isinstance(result, InterpretationResult)
            assert "Custom response" in result.text

    def test_backend_name_property(self, mock_copilot_import: Any) -> None:
        """Test backend_name property."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(model="gpt-5")
        assert backend.backend_name == "github-copilot"

    def test_cost_summary(self, mock_copilot_import: Any) -> None:
        """Test cost summary tracking."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend

        backend = GitHubCopilotBackend(model="gpt-5")

        with patch("kanoa.backends.github_copilot.asyncio.run") as mock_run:
            from kanoa.core.types import InterpretationChunk

            mock_run.return_value = {
                "chunks": [InterpretationChunk(content="Response", type="text")],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 20,
                },
            }

            backend.interpret_blocking(
                fig=None,
                data="test",
                context=None,
                focus=None,
                kb_context=None,
                custom_prompt=None,
            )

            summary = backend.get_cost_summary()
            assert summary["backend"] == "github-copilot"
            assert summary["total_calls"] == 1
            assert summary["total_tokens"]["input"] == 10
            assert summary["total_tokens"]["output"] == 20
            assert summary["total_cost_usd"] > 0

    def test_encode_kb(self, mock_copilot_import: Any) -> None:
        """Test knowledge base encoding."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend
        from kanoa.knowledge_base.manager import KnowledgeBaseManager

        backend = GitHubCopilotBackend(model="gpt-5")

        # Create a real mock that will pass isinstance check
        mock_kb = MagicMock(spec=KnowledgeBaseManager)
        mock_kb.get_text_content.return_value = "Knowledge base content"
        mock_kb.has_pdfs.return_value = False

        result = backend.encode_kb(mock_kb)
        assert result == "Knowledge base content"

    def test_encode_kb_with_pdfs(self, mock_copilot_import: Any) -> None:
        """Test knowledge base encoding with PDFs (should warn)."""
        from kanoa.backends.github_copilot import GitHubCopilotBackend
        from kanoa.knowledge_base.manager import KnowledgeBaseManager

        backend = GitHubCopilotBackend(model="gpt-5")

        mock_kb = MagicMock(spec=KnowledgeBaseManager)
        mock_kb.get_text_content.return_value = "Text content"
        mock_kb.has_pdfs.return_value = True

        with patch("kanoa.backends.github_copilot.ilog_warning") as mock_warning:
            result = backend.encode_kb(mock_kb)
            assert result == "Text content"
            mock_warning.assert_called_once()
