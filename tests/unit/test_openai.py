from unittest.mock import MagicMock, patch

from kanoa.backends.openai import OpenAIBackend


@patch("openai.OpenAI")
def test_openai_initialization(mock_openai):
    """Test backend initialization with custom configuration."""
    backend = OpenAIBackend(
        api_base="http://localhost:8000/v1",
        model="meta-llama/Llama-3.1-8B-Instruct",
        api_key="test-key",
    )

    assert backend.api_base == "http://localhost:8000/v1"
    assert backend.model == "meta-llama/Llama-3.1-8B-Instruct"
    assert backend.max_tokens == 3000
    mock_openai.assert_called_once_with(
        api_key="test-key", base_url="http://localhost:8000/v1"
    )


@patch("openai.OpenAI")
def test_openai_initialization_defaults(mock_openai):
    """Test backend initialization with default values."""
    backend = OpenAIBackend()

    assert backend.api_base is None
    assert backend.model == "gpt-4-turbo"
    mock_openai.assert_called_once()


@patch("openai.OpenAI")
def test_openai_interpret_text_only(mock_openai):
    """Test interpretation with text data only."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Analysis result"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_client.chat.completions.create.return_value = mock_response

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
    assert result.metadata["model"] == "gpt-4-turbo"

    # Verify API call
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4-turbo"
    assert call_kwargs["max_tokens"] == 3000


@patch("openai.OpenAI")
def test_openai_interpret_with_figure(mock_openai):
    """Test interpretation with figure (vision support)."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Analysis result"
    mock_response.usage = None
    mock_client.chat.completions.create.return_value = mock_response

    # Create a mock figure
    import matplotlib.pyplot as plt

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
def test_openai_interpret_with_kb_context(mock_openai):
    """Test interpretation with knowledge base context."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "KB-informed analysis"
    mock_response.usage = None
    mock_client.chat.completions.create.return_value = mock_response

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
def test_openai_interpret_custom_prompt(mock_openai):
    """Test interpretation with custom prompt."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Custom analysis"
    mock_response.usage = None
    mock_client.chat.completions.create.return_value = mock_response

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
def test_openai_interpret_error_handling(mock_openai):
    """Test error handling when API call fails."""
    # Mock OpenAI client to raise exception
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Connection error")

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
def test_openai_temperature_override(mock_openai):
    """Test that temperature can be overridden in interpret call."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Analysis"
    mock_response.usage = None
    mock_client.chat.completions.create.return_value = mock_response

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
