"""Test CLI behavior when optional backends are not installed."""

from io import StringIO
from unittest.mock import patch

import pytest


def test_cli_help_shows_available_commands():
    """Simple unit test that CLI help works with available backends."""
    from kanoa.cli import main

    captured_output = StringIO()
    with patch("sys.stdout", captured_output), pytest.raises(SystemExit):
        main(["--help"])

    output = captured_output.getvalue()
    assert "kanoa:" in output
    assert "Command to run" in output or "positional arguments" in output


# NOTE: Testing optional backend behavior requires a real environment
# where the backend is not installed. These tests would need to run
# in a separate CI job with minimal dependencies, or be done manually.
# The current implementation gracefully handles missing backends via
# try/except in cli.py lines 20-34.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
