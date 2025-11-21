"""Unit tests for converter functions."""

import base64
import re

import matplotlib.pyplot as plt
import pytest

from kanoa.utils.converters import fig_to_base64

# A regex to check if a string is valid base64
# This is a simple check, not a full validation
BASE64_REGEX = re.compile(
    r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"
)


def test_fig_to_base64() -> None:
    """Test that fig_to_base64 returns a valid base64 string."""
    # 1. Create a simple figure
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_title("Test Figure")

    # 2. Convert it to base64
    b64_string = fig_to_base64(fig)

    # 3. Assert the output is a valid base64 string
    assert isinstance(b64_string, str)
    assert len(b64_string) > 0
    assert BASE64_REGEX.match(b64_string)

    # 4. Optional: Decode and check if it's a PNG
    try:
        decoded = base64.b64decode(b64_string)
        # PNG files start with a specific 8-byte signature
        assert decoded.startswith(b"\x89PNG\r\n\x1a\n")
    except (ValueError, TypeError):
        pytest.fail("Base64 string could not be decoded.")
    finally:
        # Close the figure to free up memory
        plt.close(fig)
