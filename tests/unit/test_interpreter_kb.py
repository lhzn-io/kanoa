from pathlib import Path
from unittest.mock import MagicMock, patch

from kanoa.core.interpreter import AnalyticsInterpreter
from kanoa.core.types import InterpretationResult


class TestInterpreterKB:
    def test_init_kb_auto_text(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("content")

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MagicMock(),
        ):
            interpreter = AnalyticsInterpreter(backend="gemini", kb_path=tmp_path)
            assert interpreter.kb is not None
            assert interpreter.kb.__class__.__name__ == "KnowledgeBaseManager"

    def test_init_kb_auto_pdf(self, tmp_path: Path) -> None:
        (tmp_path / "test.pdf").write_bytes(b"content")

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MagicMock(),
        ):
            interpreter = AnalyticsInterpreter(backend="gemini", kb_path=tmp_path)
            assert interpreter.kb is not None
            assert interpreter.kb.__class__.__name__ == "KnowledgeBaseManager"
            # Verify it detected the PDF
            assert interpreter.kb.has_pdfs()

    def test_kb_works_with_any_backend(self, tmp_path: Path) -> None:
        """Test that PDFs can be used with any backend (no more errors)."""
        (tmp_path / "test.pdf").write_bytes(b"content")

        with patch(
            "kanoa.core.interpreter._get_backend_class",
            return_value=MagicMock(),
        ):
            # This should not raise an error anymore
            interpreter = AnalyticsInterpreter(backend="claude", kb_path=tmp_path)
            assert interpreter.kb is not None

    def test_kb_context_inclusion(self, tmp_path: Path) -> None:
        (tmp_path / "test.md").write_text("KB Content")

        MockBackendClass = MagicMock()
        backend_instance = MockBackendClass.return_value
        # Mock encode_kb to return text content
        backend_instance.encode_kb.return_value = "# test.md\n\nKB Content"
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
            interpreter = AnalyticsInterpreter(backend="gemini", kb_path=tmp_path)
            interpreter.interpret(data="test", display_result=False)

            # Verify encode_kb was called
            assert backend_instance.encode_kb.called
            # Verify kb_context was passed to backend
            call_args = backend_instance.interpret.call_args
            assert "KB Content" in call_args.kwargs["kb_context"]
