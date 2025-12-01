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

        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Claude interpretation")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        cast("Any", backend.client.messages.create).return_value = mock_response

        result = backend.interpret(
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

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Figure interpretation")]
        mock_response.usage.input_tokens = 200
        mock_response.usage.output_tokens = 50

        cast("Any", backend.client.messages.create).return_value = mock_response

        fig = plt.figure()
        result = backend.interpret(
            fig=fig,
            data=None,
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
        )

        assert "Figure interpretation" in result.text

        # Verify image was sent
        call_args = cast("Any", backend.client.messages.create).call_args
        assert call_args is not None
        messages = call_args.kwargs["messages"]
        content = messages[0]["content"]
        assert any(block.get("type") == "image" for block in content)

    def test_error_handling(self, mock_anthropic: Any) -> None:
        backend = ClaudeBackend(api_key="test_key")
        cast("Any", backend.client.messages.create).side_effect = Exception("API Error")

        result = backend.interpret(
            fig=None,
            data="test",
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
        )

        assert "Error" in result.text
        assert result.usage is None
