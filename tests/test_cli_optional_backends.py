"""Test CLI behavior when optional backends are not installed."""

import sys
from io import StringIO
from unittest.mock import patch

import pytest


@pytest.mark.integration
def test_cli_help_without_gemini():
    """Test that --help works even when gemini backend is not installed."""
    # Mock the import to simulate gemini not being installed
    import builtins

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if "gemini_cache" in name:
            raise ImportError("google-genai not installed")
        return original_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=mock_import):
        # Reimport the CLI module to trigger the conditional import
        if "kanoa.cli" in sys.modules:
            del sys.modules["kanoa.cli"]

        from kanoa.cli import main

        # Capture stdout
        captured_output = StringIO()
        with patch("sys.stdout", captured_output), pytest.raises(SystemExit):
            main(["--help"])

        output = captured_output.getvalue()
        # Should show help without crashing
        assert "kanoa:" in output
        # Gemini command should NOT be present
        assert "gemini" not in output.lower() or "plugin" in output.lower()


@pytest.mark.integration
def test_cli_gemini_command_without_backend():
    """Test that using gemini command without backend shows helpful error."""
    import builtins

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if "gemini_cache" in name:
            raise ImportError("google-genai not installed")
        return original_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=mock_import):
        if "kanoa.cli" in sys.modules:
            del sys.modules["kanoa.cli"]

        from kanoa.cli import main

        # Try to use gemini command
        captured_stderr = StringIO()
        with patch("sys.stderr", captured_stderr), pytest.raises(SystemExit) as exc:
            main(["gemini", "cache", "list"])

        assert exc.value.code == 1
        error_output = captured_stderr.getvalue()
        assert "not installed" in error_output.lower()
        assert "pip install kanoa[gemini]" in error_output


def test_cli_help_shows_available_commands():
    """Simple unit test that CLI help works with available backends."""
    from kanoa.cli import main

    captured_output = StringIO()
    with patch("sys.stdout", captured_output), pytest.raises(SystemExit):
        main(["--help"])

    output = captured_output.getvalue()
    assert "kanoa:" in output
    assert "Command to run" in output or "positional arguments" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
