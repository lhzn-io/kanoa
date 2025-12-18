from kanoa.core.types import UsageInfo
from kanoa.utils.notebook import (
    _STREAMING_COLORS,
    _format_styled_box,
    _get_style_colors,
    _prepare_interpretation_markdown,
)


def test_format_styled_box() -> None:
    text = "Test content"
    backend = "test-backend"
    footer = "Footer content"
    colors = _STREAMING_COLORS

    html = _format_styled_box(text, backend, footer, colors)

    assert "background: rgba(147, 112, 219, 0.1)" in html
    assert "test-backend" in html
    assert "Test content" in html
    assert "Footer content" in html
    assert "color: #9370DB" in html  # Title color


def test_prepare_interpretation_markdown() -> None:
    text = "Analysis result"
    backend = "gemini"
    model = "gemini-2.0-flash"
    usage = UsageInfo(input_tokens=100, output_tokens=50, cost=0.001)

    markdown = _prepare_interpretation_markdown(
        text=text,
        backend=backend,
        model=model,
        usage=usage,
        cached=False,
        cache_created=False,
    )

    assert "Analysis result" in markdown
    assert "gemini-2.0-flash" in markdown
    assert "100→50 tokens" in markdown
    assert "$0.0010" in markdown

    # Check colors (should be primary/ocean by default)
    colors = _get_style_colors("ai")
    assert f"background: {colors['bg']}" in markdown


def test_prepare_interpretation_markdown_cached() -> None:
    text = "Cached result"
    usage = UsageInfo(input_tokens=100, output_tokens=50, cost=0.001, cached_tokens=80)

    markdown = _prepare_interpretation_markdown(
        text=text, backend="gemini", usage=usage, cached=True, cache_created=False
    )

    assert "cached" in markdown
    assert "80 cached" in markdown
