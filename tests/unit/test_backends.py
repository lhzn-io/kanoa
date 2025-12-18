from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import pytest

from kanoa.backends.gemini import GeminiBackend
from kanoa.core.types import InterpretationResult


class TestGeminiBackend:
    @pytest.fixture
    def mock_genai(self) -> Any:
        with patch("kanoa.backends.gemini.genai") as mock:
            yield mock

    def test_initialization(self, mock_genai: Any) -> None:
        backend = GeminiBackend(api_key="test_key")
        assert backend.api_key == "test_key"
        mock_genai.Client.assert_called_once_with(api_key="test_key")

    def test_interpret_text_only(self, mock_genai: Any) -> None:
        backend = GeminiBackend(api_key="test_key")

        # Mock response stream
        mock_chunk = MagicMock()
        mock_chunk.text = "Interpretation result"
        mock_chunk.usage_metadata = MagicMock()
        mock_chunk.usage_metadata.prompt_token_count = 10
        mock_chunk.usage_metadata.candidates_token_count = 20
        mock_chunk.usage_metadata.cached_content_token_count = 0

        # Configure return_value to be an iterator
        cast("Any", backend.client.models.generate_content_stream).return_value = [
            mock_chunk
        ]

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
        assert result.backend == "gemini"
        assert result.usage is not None
        assert result.usage.input_tokens == 10
        assert result.usage.output_tokens == 20
        # gemini-2.5-flash is free tier in default pricing.json, so cost is 0.0
        # assert result.usage.cost > 0
        assert result.usage.cost >= 0.0

    def test_interpret_with_figure(self, mock_genai: Any) -> None:
        backend = GeminiBackend(api_key="test_key")

        # Mock response stream
        mock_chunk = MagicMock()
        mock_chunk.text = "Figure interpretation"
        mock_chunk.usage_metadata = MagicMock()
        mock_chunk.usage_metadata.prompt_token_count = 100
        mock_chunk.usage_metadata.candidates_token_count = 50
        mock_chunk.usage_metadata.cached_content_token_count = 0

        cast("Any", backend.client.models.generate_content_stream).return_value = [
            mock_chunk
        ]

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
        # Check that content parts included image
        call_args = cast("Any", backend.client.models.generate_content_stream).call_args
        assert call_args is not None
        # Inspect contents structure if needed, but basic call
        # verification is good for now

    def test_error_handling(self, mock_genai: Any) -> None:
        backend = GeminiBackend(api_key="test_key")
        cast(
            "Any", backend.client.models.generate_content_stream
        ).side_effect = Exception("API Error")

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

    def test_load_pdfs(self, mock_genai: Any, tmp_path: Path) -> None:
        backend = GeminiBackend(api_key="test_key")

        # Create dummy PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"PDF content")

        # Mock upload response
        mock_file = MagicMock()
        mock_file.name = "files/123"
        mock_file.state = "ACTIVE"
        mock_file.uri = "https://file_uri"

        cast("Any", backend.client.files.upload).return_value = mock_file
        cast("Any", backend.client.files.get).return_value = mock_file

        uploaded = backend.load_pdfs([pdf_path])

        assert len(uploaded) == 1
        assert uploaded[pdf_path] == mock_file
        cast("Any", backend.client.files.upload).assert_called_once()
