from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kanoa.core.interpreter import AnalyticsInterpreter
from kanoa.core.types import InterpretationResult


class TestInterpreterKB:
    def test_init_kb_auto_text(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("content")

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MagicMock(),
        ):
            interpreter = AnalyticsInterpreter(
                backend="gemini", kb_path=tmp_path, kb_type="auto"
            )
            assert interpreter.kb is not None
            assert interpreter.kb.__class__.__name__ == "TextKnowledgeBase"

    def test_init_kb_auto_pdf(self, tmp_path: Path) -> None:
        (tmp_path / "test.pdf").write_bytes(b"content")

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MagicMock(),
        ):
            interpreter = AnalyticsInterpreter(
                backend="gemini", kb_path=tmp_path, kb_type="auto"
            )
            assert interpreter.kb is not None
            assert interpreter.kb.__class__.__name__ == "PDFKnowledgeBase"

    def test_init_kb_pdf_wrong_backend(self, tmp_path: Path) -> None:
        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MagicMock(),
        ):
            with pytest.raises(ValueError, match="PDF knowledge base requires Gemini"):
                AnalyticsInterpreter(backend="claude", kb_path=tmp_path, kb_type="pdf")

    def test_kb_context_inclusion(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("KB Content")

        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        # Return a proper InterpretationResult instead of a MagicMock
        backend_instance.interpret.return_value = InterpretationResult(
            text="Test interpretation",
            backend="gemini",
            usage=None,
        )

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MockBackendClass,
        ):
            interpreter = AnalyticsInterpreter(
                backend="gemini", kb_path=tmp_path, kb_type="text"
            )
            interpreter.interpret(data="test", display_result=False)

            # Verify kb_context was passed to backend
            call_args = backend_instance.interpret.call_args
            assert "KB Content" in call_args.kwargs["kb_context"]
