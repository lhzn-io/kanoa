from typing import Any, cast
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import pytest

from kanoa.backends.claude import ClaudeBackend


class TestClaudeBackend:
    @pytest.fixture
    def mock_anthropic(self) -> Any:
        with patch("kanoa.backends.claude.Anthropic") as mock:
            yield mock

    def test_initialization(self, mock_anthropic: Any) -> None:
        backend = ClaudeBackend(api_key="test_key")
        mock_anthropic.assert_called_once_with(api_key="test_key")
        assert backend.model == "claude-sonnet-4-5-20250929"

    def test_interpret_text_only(self, mock_anthropic: Any) -> None:
        backend = ClaudeBackend(api_key="test_key")

        # Mock stream context manager
        mock_stream = MagicMock()
        mock_stream.text_stream = ["Claude", " interpretation"]

        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50

        mock_final_msg = MagicMock()
        mock_final_msg.usage = mock_usage
        mock_stream.get_final_message.return_value = mock_final_msg

        # Configure client.messages.stream to return context manager yielding mock_stream
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_stream
        mock_ctx.__exit__.return_value = None
        cast("Any", backend.client.messages.stream).return_value = mock_ctx

        result = backend.interpret_blocking(
            fig=None,
            data="Some data",
            context="Context",
            focus="Focus",
            kb_context=None,
            custom_prompt=None,
        )

        assert "Claude interpretation" in result.text
        assert result.backend == "claude"
        assert result.usage is not None
        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 50
        assert result.usage.cost > 0

    def test_interpret_with_figure(self, mock_anthropic: Any) -> None:
        backend = ClaudeBackend(api_key="test_key")

        mock_stream = MagicMock()
        mock_stream.text_stream = ["Figure", " interpretation"]

        mock_usage = MagicMock()
        mock_usage.input_tokens = 200
        mock_usage.output_tokens = 50

        mock_final_msg = MagicMock()
        mock_final_msg.usage = mock_usage
        mock_stream.get_final_message.return_value = mock_final_msg

        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_stream
        mock_ctx.__exit__.return_value = None
        cast("Any", backend.client.messages.stream).return_value = mock_ctx

        fig = plt.figure()
        result = backend.interpret_blocking(
            fig=fig,
            data=None,
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
        )

        assert "Figure interpretation" in result.text

        # Verify image was sent (stream call args)
        call_args = cast("Any", backend.client.messages.stream).call_args
        assert call_args is not None
        messages = call_args.kwargs["messages"]
        content = messages[0]["content"]
        assert any(block.get("type") == "image" for block in content)

    def test_error_handling(self, mock_anthropic: Any) -> None:
        backend = ClaudeBackend(api_key="test_key")
        cast("Any", backend.client.messages.stream).side_effect = Exception("API Error")

        result = backend.interpret_blocking(
            fig=None,
            data="test",
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
        )

        assert "Error" in result.text
        assert result.usage is None
