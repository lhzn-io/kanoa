"""Tests for OpenAI backend."""

from unittest.mock import MagicMock, patch


def _create_mock_response(
    content: str = "Analysis result", has_usage: bool = True
) -> MagicMock:
    """Create a mock OpenAI response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    if has_usage:
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
    else:
        mock_response.usage = None
    return mock_response


class TestOpenAIBackend:
    """Test suite for OpenAI backend."""

    @patch("openai.OpenAI")
    def test_openai_initialization(self, mock_openai_class: MagicMock) -> None:
        """Test backend initialization with custom configuration."""
        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend(
            api_base="http://localhost:8000/v1",
            model="meta-llama/Llama-3.1-8B-Instruct",
            api_key="test-key",
        )

        assert backend.api_base == "http://localhost:8000/v1"
        assert backend.model == "meta-llama/Llama-3.1-8B-Instruct"
        assert backend.max_tokens == 3000
        mock_openai_class.assert_called_once_with(
            api_key="test-key", base_url="http://localhost:8000/v1"
        )

    @patch("openai.OpenAI")
    def test_openai_initialization_defaults(self, mock_openai_class: MagicMock) -> None:
        """Test backend initialization with default values."""
        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend()

        assert backend.api_base is None
        assert backend.model == "gpt-5-mini"
        mock_openai_class.assert_called_once()

    @patch("openai.OpenAI")
    def test_openai_interpret_text_only(self, mock_openai_class: MagicMock) -> None:
        """Test interpretation with text data only."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = _create_mock_response()

        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend()
        result = backend.interpret(
            fig=None,
            data={"key": "value"},
            context="test context",
            focus="test focus",
            kb_context=None,
            custom_prompt=None,
        )

        assert result.text == "Analysis result"
        assert result.backend == "openai"
        assert result.usage is not None
        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 50
        assert result.metadata is not None
        assert result.metadata["model"] == "gpt-5-mini"

        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs["max_tokens"] == 3000

    @patch("openai.OpenAI")
    def test_openai_interpret_with_figure(self, mock_openai_class: MagicMock) -> None:
        """Test interpretation with figure (vision support)."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = _create_mock_response(
            has_usage=False
        )

        import matplotlib.pyplot as plt

        from kanoa.backends.openai import OpenAIBackend

        # Create a mock figure
        fig = plt.figure()

        backend = OpenAIBackend()
        _ = backend.interpret(
            fig=fig,
            data=None,
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
        )

        # Verify image was included in messages
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        content = messages[0]["content"]
        assert any(item.get("type") == "image_url" for item in content)

        plt.close(fig)

    @patch("openai.OpenAI")
    def test_openai_interpret_with_kb_context(
        self, mock_openai_class: MagicMock
    ) -> None:
        """Test interpretation with knowledge base context."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = _create_mock_response(
            content="KB-informed analysis", has_usage=False
        )

        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend()
        _ = backend.interpret(
            fig=None,
            data=None,
            context=None,
            focus=None,
            kb_context="Domain-specific knowledge here",
            custom_prompt=None,
        )

        # Verify KB context was included in prompt
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        prompt = messages[0]["content"][0]["text"]
        assert "Knowledge Base" in prompt
        assert "Domain-specific knowledge here" in prompt

    @patch("openai.OpenAI")
    def test_openai_interpret_custom_prompt(self, mock_openai_class: MagicMock) -> None:
        """Test interpretation with custom prompt."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = _create_mock_response(
            content="Custom analysis", has_usage=False
        )

        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend()
        _ = backend.interpret(
            fig=None,
            data=None,
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt="Custom prompt text",
        )

        # Verify custom prompt was used
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        prompt = messages[0]["content"][0]["text"]
        assert prompt == "Custom prompt text"

    @patch("openai.OpenAI")
    def test_openai_interpret_error_handling(
        self, mock_openai_class: MagicMock
    ) -> None:
        """Test error handling when API call fails."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection error")

        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend()
        result = backend.interpret(
            fig=None,
            data=None,
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
        )

        assert "❌" in result.text
        assert "Error" in result.text
        assert "Connection error" in result.text
        assert result.backend == "openai"
        assert result.usage is None

    @patch("openai.OpenAI")
    def test_openai_temperature_override(self, mock_openai_class: MagicMock) -> None:
        """Test that temperature can be overridden in interpret call."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = _create_mock_response(
            content="Analysis", has_usage=False
        )

        from kanoa.backends.openai import OpenAIBackend

        backend = OpenAIBackend(temperature=0.5)
        _ = backend.interpret(
            fig=None,
            data=None,
            context=None,
            focus=None,
            kb_context=None,
            custom_prompt=None,
            temperature=0.9,  # Override
        )

        # Verify temperature was overridden
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.9
