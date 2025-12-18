"""
Notebook utilities for consistent result display and formatting.

Provides functions for displaying analysis results with consistent formatting,
including styled info boxes for Jupyter notebooks.

Uses display(Markdown(...)) with HTML styling for theme-adaptive rendering
that works in both light and dark modes.

Color Palettes:
    Default palette uses ocean-inspired colors. Users can customize via:
    - set_color_palette(name) - Use a predefined palette
    - set_color_palette(custom_dict) - Use custom colors
    - Available palettes: "ocean" (default), "earth", "sunset", "monochrome"
"""

import re
from typing import Any, Dict, Optional, Tuple, Union

# Type alias for RGB color tuples
RGBColor = Tuple[int, int, int]

# Lazy imports for IPython - avoid import errors outside Jupyter
_ipython_available: Optional[bool] = None

# =============================================================================
# Color Palette System
# =============================================================================

# Ocean blue palette (default) - deeper navy-ocean tones
_PALETTE_OCEAN = {
    "primary": (2, 62, 138),  # Deep ocean blue (#023E8A)
    "info": (72, 149, 239),  # Lighter blue (#4895EF)
    "success": (56, 176, 0),  # Fresh green (#38B000)
    "warning": (255, 152, 0),  # Amber (#FF9800)
    "error": (244, 67, 54),  # Red (#F44336)
}

# Earth tones palette
_PALETTE_EARTH = {
    "primary": (121, 85, 72),  # Brown (#795548)
    "info": (96, 125, 139),  # Blue grey (#607D8B)
    "success": (104, 159, 56),  # Light green (#689F38)
    "warning": (255, 160, 0),  # Amber (#FFA000)
    "error": (198, 40, 40),  # Dark red (#C62828)
}

# Sunset palette
_PALETTE_SUNSET = {
    "primary": (233, 30, 99),  # Pink (#E91E63)
    "info": (156, 39, 176),  # Purple (#9C27B0)
    "success": (76, 175, 80),  # Green (#4CAF50)
    "warning": (255, 87, 34),  # Deep orange (#FF5722)
    "error": (244, 67, 54),  # Red (#F44336)
}

# Monochrome palette
_PALETTE_MONOCHROME = {
    "primary": (66, 66, 66),  # Dark grey (#424242)
    "info": (97, 97, 97),  # Grey (#616161)
    "success": (76, 76, 76),  # Darker grey (#4C4C4C)
    "warning": (117, 117, 117),  # Medium grey (#757575)
    "error": (33, 33, 33),  # Almost black (#212121)
}

_PALETTES = {
    "ocean": _PALETTE_OCEAN,
    "earth": _PALETTE_EARTH,
    "sunset": _PALETTE_SUNSET,
    "monochrome": _PALETTE_MONOCHROME,
}

# Streaming state colors (Lavender/Purple theme)
_STREAMING_COLORS = {
    "bg": "rgba(147, 112, 219, 0.1)",  # MediumPurple with low opacity
    "border": "rgba(147, 112, 219, 0.3)",  # Soft purple border
    "accent": "rgba(147, 112, 219, 0.8)",  # Medium purple accent
    "title": "#9370DB",  # MediumPurple title
}

# Current active palette (module-level state)
_current_palette: Dict[str, RGBColor] = _PALETTE_OCEAN.copy()


def set_color_palette(palette: Union[str, Dict[str, RGBColor]]) -> None:
    """
    Set the color palette for notebook display functions.

    Args:
        palette: Either a palette name ("ocean", "earth", "sunset", "monochrome")
                 or a custom dict with RGB tuples for keys:
                 "primary", "info", "success", "warning", "error"

    Example:
        >>> # Use predefined palette
        >>> set_color_palette("earth")

        >>> # Use custom colors (RGB tuples)
        >>> set_color_palette({
        ...     "primary": (0, 100, 150),
        ...     "info": (50, 150, 200),
        ...     "success": (0, 150, 100),
        ...     "warning": (255, 150, 0),
        ...     "error": (200, 50, 50),
        ... })

        >>> # ColorBrewer-inspired custom palette
        >>> set_color_palette({
        ...     "primary": (31, 120, 180),   # ColorBrewer Blue
        ...     "info": (106, 61, 154),      # ColorBrewer Purple
        ...     "success": (51, 160, 44),    # ColorBrewer Green
        ...     "warning": (255, 127, 0),    # ColorBrewer Orange
        ...     "error": (227, 26, 28),      # ColorBrewer Red
        ... })
    """
    global _current_palette

    if isinstance(palette, str):
        if palette not in _PALETTES:
            raise ValueError(
                f"Unknown palette: {palette}. Choose from: {list(_PALETTES.keys())}"
            )
        _current_palette = _PALETTES[palette].copy()
    elif isinstance(palette, dict):
        required_keys = {"primary", "info", "success", "warning", "error"}
        missing = required_keys - set(palette.keys())
        if missing:
            raise ValueError(f"Custom palette missing keys: {missing}")
        _current_palette = palette.copy()
    else:
        raise TypeError("palette must be a string or dict")


def get_color_palette() -> Dict[str, RGBColor]:
    """Get the current color palette as RGB tuples."""
    return _current_palette.copy()


def _rgb_to_rgba(rgb: RGBColor, alpha: float) -> str:
    """Convert RGB tuple to rgba() CSS string."""
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"


def _rgb_to_hex(rgb: RGBColor) -> str:
    """Convert RGB tuple to hex color string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _get_style_colors(style: str) -> Dict[str, str]:
    """Get CSS color values for a given style from current palette."""
    # Map style names to palette keys
    style_map = {
        "info": "info",
        "success": "success",
        "warning": "warning",
        "error": "error",
        "ai": "primary",  # AI interpretations use primary color
    }
    key = style_map.get(style, "info")
    rgb = _current_palette.get(key, _current_palette["info"])

    return {
        "bg": _rgb_to_rgba(rgb, 0.08),
        "border": _rgb_to_rgba(rgb, 0.3),
        "accent": _rgb_to_rgba(rgb, 0.8),
        "title": _rgb_to_hex(rgb),
    }


# =============================================================================
# Display Functions
# =============================================================================


def _check_ipython() -> bool:
    """Check if we're running in a Jupyter notebook environment."""
    global _ipython_available
    if _ipython_available is None:
        try:
            from IPython.core.getipython import get_ipython

            ipython = get_ipython()
            # Check if we're in a Jupyter kernel (not just terminal IPython)
            _ipython_available = ipython is not None and hasattr(ipython, "kernel")
        except ImportError:
            _ipython_available = False
    return _ipython_available


def _format_styled_box(
    text: str,
    backend: Optional[str],
    footer: str,
    colors: Dict[str, str],
) -> str:
    """Format content into a styled HTML box."""
    # Add title with backend name (monospace font)
    title_line = ""
    if backend:
        title_color = colors.get("title", "inherit")
        title_line = f"<div style=\"font-weight: 600; margin-bottom: 12px; opacity: 0.9; font-size: 1.1em; font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono', 'Source Code Pro', monospace; color: {title_color};\">{backend}</div>\n\n"

    return f"""
<div style="background: {colors["bg"]};
            border: 1px solid {colors["border"]};
            border-left: 4px solid {colors["accent"]};
            padding: 16px 20px;
            margin: 10px 0;
            border-radius: 8px;
            backdrop-filter: blur(5px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);">

{title_line}{text}{footer}

</div>
"""


def display_result(
    content: str,
    title: Optional[str] = None,
    style: str = "info",
) -> None:
    """
    Display formatted result with theme-adaptive styling in Jupyter notebooks.

    DEPRECATED: This function now delegates to the logging infrastructure.
    Consider using log_info(), log_success(), log_warning(), or log_error() directly.

    Args:
        content: The content to display (supports full markdown)
        title: Optional title/header for the result box
        style: Display style - "info", "success", "warning", "error", "ai"

    Example:
        >>> display_result("Analysis complete.", "Summary", "success")
        >>> display_result("Found anomalies.", "⚠️ Warning", "warning")
    """
    # Delegate to logging infrastructure for consistency
    from ..utils.logging import log_info, log_warning

    # Map style to appropriate log function
    # Note: We use log_info for most cases since the logging system
    # uses color configuration from kanoa.options
    if style == "error":
        from ..utils.logging import log_error

        log_error(content, title=title)
    elif style == "warning":
        log_warning(content, title=title)
    elif style == "success":
        # Success messages are just info with a different semantic meaning
        log_info(content, title=title)
    else:  # "info" or "ai" or any other
        log_info(content, title=title)


def _strip_generated_coda(text: str) -> str:
    """Strip redundant 'Generated by' coda from text if present."""

    # Match patterns like: ---\n*Generated by model-name* (with optional extras)
    pattern = r"\n\n---\n\*Generated by [^*]+\*.*$"
    return re.sub(pattern, "", text, flags=re.DOTALL)


def _normalize_latex_for_jupyter(text: str) -> str:
    """
    Normalize LaTeX/math notation in LLM output for Jupyter rendering.

    LLMs often produce inconsistent LaTeX that doesn't render well in Jupyter.
    This function fixes common patterns:

    1. Broken inline math: `$\\mu$g/L` -> `μg/L` (use Unicode for simple symbols)
    2. Escaped backslashes: `\\\\mu` -> `\\mu`
    3. Common Greek letters outside math mode: convert to Unicode
    4. Fix malformed dollar signs in units

    Args:
        text: Raw text from LLM response

    Returns:
        Text with normalized math notation for better Jupyter rendering
    """
    # Greek letter mapping (LaTeX -> Unicode)
    greek_map = {
        r"\alpha": "α",
        r"\beta": "β",
        r"\gamma": "γ",
        r"\delta": "δ",
        r"\epsilon": "ε",
        r"\zeta": "ζ",
        r"\eta": "η",
        r"\theta": "θ",
        r"\iota": "ι",
        r"\kappa": "κ",
        r"\lambda": "λ",
        r"\mu": "μ",
        r"\nu": "ν",
        r"\xi": "ξ",
        r"\pi": "π",
        r"\rho": "ρ",
        r"\sigma": "σ",
        r"\tau": "τ",
        r"\upsilon": "υ",
        r"\phi": "φ",
        r"\chi": "χ",
        r"\psi": "ψ",
        r"\omega": "ω",
        # Uppercase
        r"\Gamma": "Γ",
        r"\Delta": "Δ",
        r"\Theta": "Θ",
        r"\Lambda": "Λ",
        r"\Xi": "Ξ",
        r"\Pi": "Π",
        r"\Sigma": "Σ",
        r"\Phi": "Φ",
        r"\Psi": "Ψ",
        r"\Omega": "Ω",
    }

    # Pattern 1: Fix broken inline math like `$\mu$g/L` -> `μg/L`
    # These are single Greek letters that got wrapped in $ but aren't full equations
    for latex, unicode_char in greek_map.items():
        # Match $\mu$ followed by non-space (like units)
        escaped_latex = re.escape(latex)
        pattern = rf"\${escaped_latex}\$(?=\S)"
        text = re.sub(pattern, unicode_char, text)

    # Pattern 2: Convert standalone Greek letters in $...$ to Unicode
    # when they appear in unit contexts (followed by letters like g, L, m, etc.)
    for latex, unicode_char in greek_map.items():
        escaped_latex = re.escape(latex)
        # Match $\mu$ at word boundaries or before units
        pattern = rf"\${escaped_latex}\$"
        text = re.sub(pattern, unicode_char, text)

    # Pattern 3: Fix double-escaped backslashes from some LLMs
    text = text.replace("\\\\mu", r"\mu")
    text = text.replace("\\\\sigma", r"\sigma")

    # Pattern 4: Common unit patterns - convert to proper Unicode
    # e.g., "µg/L" variations
    text = text.replace("\\textmu", "μ")

    return text


def _prepare_interpretation_markdown(
    text: str,
    backend: Optional[str] = None,
    model: Optional[str] = None,
    usage: Optional[Any] = None,
    cached: bool = False,
    cache_created: bool = False,
) -> str:
    """Prepare the styled markdown for interpretation result."""
    # Strip any redundant 'Generated by' coda from the text
    text = _strip_generated_coda(text)

    # Normalize LaTeX/math notation for better Jupyter rendering
    text = _normalize_latex_for_jupyter(text)

    # Build footer with usage info - prefer full model name
    footer_parts = []
    if model:
        footer_parts.append(f"**{model}**")
    elif backend:
        footer_parts.append(f"**{backend}**")
    if usage:
        tokens = f"{usage.input_tokens:,}→{usage.output_tokens:,} tokens"
        cost = f"${usage.cost:.4f}"

        # Show cached tokens count if present
        if hasattr(usage, "cached_tokens") and usage.cached_tokens:
            tokens += f" ({usage.cached_tokens:,} cached)"

        footer_parts.append(tokens)
        footer_parts.append(cost)

    # Show cache status: creation (miss) vs hit
    if cached and cache_created:
        # Cache was created on this call - this is a MISS
        footer_parts.append("cache created")
    elif cached and not cache_created:
        # Cache was reused - this is a HIT
        footer_parts.append("cached")

    footer_line = ""
    if footer_parts:
        footer_line = f"\n\n---\n<small>{' · '.join(footer_parts)}</small>"

    # Get primary color from current palette (ocean blue by default)
    colors = _get_style_colors("ai")

    return _format_styled_box(text, backend, footer_line, colors)


def display_interpretation(
    text: str,
    backend: Optional[str] = None,
    model: Optional[str] = None,
    usage: Optional[Any] = None,
    cached: bool = False,
    cache_created: bool = False,
) -> None:
    """
    Display an AI interpretation result with consistent styling.

    This is the primary display function for AnalyticsInterpreter results.
    Uses the "primary" color from the current palette (ocean blue by default).

    Args:
        text: The interpretation text (markdown)
        backend: Backend name (e.g., "gemini", "claude")
        model: Full model name (e.g., "gemini-2.0-flash", "claude-sonnet-4-20250514")
        usage: UsageInfo object with token counts and cost
        cached: Whether context caching was used
        cache_created: Whether the cache was newly created (miss) vs reused (hit)
    """
    if not _check_ipython():
        # Strip any redundant 'Generated by' coda from the text
        text = _strip_generated_coda(text)
        # Normalize LaTeX/math notation
        text = _normalize_latex_for_jupyter(text)

        print(text)
        if usage:
            model_display = model or backend or "unknown"
            tokens = f"{usage.input_tokens}→{usage.output_tokens}"
            print(f"\n[{model_display}] Tokens: {tokens}, Cost: ${usage.cost:.4f}")
        return

    from IPython.display import Markdown, display

    styled_markdown = _prepare_interpretation_markdown(
        text, backend, model, usage, cached, cache_created
    )
    display(Markdown(styled_markdown))


def display_info(content: str, title: Optional[str] = None) -> None:
    """Display info message with blue background."""
    display_result(content, title, "info")


def display_success(content: str, title: Optional[str] = None) -> None:
    """Display success message with green background."""
    display_result(content, title, "success")


def display_warning(content: str, title: Optional[str] = None) -> None:
    """Display warning message with yellow background."""
    display_result(content, title, "warning")


def display_error(content: str, title: Optional[str] = None) -> None:
    """Display error message with red background."""
    display_result(content, title, "error")


def format_dict_as_list(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format dictionary as markdown bullet list for display in result boxes.

    Args:
        data: Dictionary to format
        indent: Indentation level (unused, kept for API compat)

    Returns:
        Markdown formatted string
    """
    items = []
    for key, value in data.items():
        items.append(f"- **{key}:** {value}")

    return "\n".join(items)


def format_cost_summary(summary: Dict[str, Any]) -> str:
    """
    Format a cost summary dictionary as markdown table.

    Args:
        summary: Cost summary from interpreter.get_cost_summary()

    Returns:
        Markdown formatted string
    """
    tokens = summary.get("total_tokens", {})
    return f"""| Metric | Value |
|:-------|------:|
| **Backend** | {summary.get("backend", "unknown")} |
| **Total Calls** | {summary.get("total_calls", 0)} |
| **Input Tokens** | {tokens.get("input", 0):,} |
| **Output Tokens** | {tokens.get("output", 0):,} |
| **Total Cost** | ${summary.get("total_cost_usd", 0):.4f} |
| **Avg Cost/Call** | ${summary.get("avg_cost_per_call", 0):.4f} |"""


def stream_interpretation(
    iterator: Any,
    backend_name: str = "unknown",
    display_output: bool = True,
) -> Any:
    """Stream interpretation chunks with hybrid display approach.

    Phase 1: Shows raw text chunks as they arrive for immediate feedback
    Phase 2: After completion, displays styled box with full response and metadata

    Args:
        iterator: Chunk iterator from backend
        backend_name: Name of the backend (e.g., "gemini", "claude")
        display_output: Whether to show display outputs (streaming + final styled box)

    Yields:
        InterpretationChunk objects from the iterator
    """
    if not _check_ipython():
        # Fallback for terminal: just print text chunks
        text_buffer = []
        final_usage = None
        final_metadata = None

        for chunk in iterator:
            if chunk.type == "text":
                print(chunk.content, end="", flush=True)
                text_buffer.append(chunk.content)
            elif chunk.type == "usage" and chunk.usage:
                final_usage = chunk.usage
            if chunk.metadata:
                final_metadata = chunk.metadata
            yield chunk

        # Print footer in terminal
        if final_usage:
            model = (
                final_metadata.get("model", backend_name)
                if final_metadata
                else backend_name
            )
            tokens = f"{final_usage.input_tokens}→{final_usage.output_tokens}"
            print(f"\n\n[{model}] {tokens} tokens · ${final_usage.cost:.4f}")
        return

    # Jupyter notebook environment
    from IPython.display import Markdown, display

    # Streaming with styled final display
    text_buffer = []
    final_usage = None
    final_metadata = None
    cached = False
    cache_created = False

    # Initialize display handle
    display_handle = None

    try:
        # Stream chunks
        for chunk in iterator:
            if chunk.type == "text":
                text_buffer.append(chunk.content)

                if display_output:
                    current_text = "".join(text_buffer)
                    # Use lavender streaming frame
                    styled_html = _format_styled_box(
                        text=current_text,
                        backend=backend_name,
                        footer="",  # No footer during streaming
                        colors=_STREAMING_COLORS,
                    )

                    if display_handle is None:
                        display_handle = display(Markdown(styled_html), display_id=True)
                    else:
                        display_handle.update(Markdown(styled_html))

            elif chunk.type == "usage" and chunk.usage:
                final_usage = chunk.usage
                # Check for caching info
                if hasattr(chunk.usage, "cache_created"):
                    cache_created = chunk.usage.cache_created
                if hasattr(chunk.usage, "cached_tokens") and chunk.usage.cached_tokens:
                    cached = True

            if chunk.metadata:
                final_metadata = chunk.metadata

            yield chunk

        # Display final styled box (replaces streaming box)
        if display_output and text_buffer:
            full_text = "".join(text_buffer)
            model = final_metadata.get("model") if final_metadata else None

            final_markdown = _prepare_interpretation_markdown(
                text=full_text,
                backend=backend_name,
                model=model,
                usage=final_usage,
                cached=cached,
                cache_created=cache_created,
            )

            if display_handle:
                display_handle.update(Markdown(final_markdown))
            else:
                display(Markdown(final_markdown))

    except Exception as e:
        if display_output:
            print(f"\nError streaming: {e}")
        raise e


class StreamingResultIterator:
    """
    Wraps a generator to support auto-execution in Jupyter when displayed.

    Allows usage like:
        interpreter.interpret(..., stream=True)

    Instead of requiring:
        for _ in interpreter.interpret(..., stream=True): pass
    """

    def __init__(self, iterator: Any):
        self._iterator = iterator
        self._started = False

    def __iter__(self) -> "StreamingResultIterator":
        return self

    def __next__(self) -> Any:
        self._started = True
        return next(self._iterator)

    def _ipython_display_(self) -> None:
        """Execute the stream when displayed in a notebook."""
        if self._started:
            return  # Already being consumed elsewhere

        # Consume the iterator to trigger side effects (display)
        # We don't need to do anything with the chunks as the
        # wrapped stream_interpretation handles the display
        for _ in self:
            pass


__all__ = [
    # Display functions
    "display_result",
    "display_interpretation",
    "display_info",
    "display_success",
    "display_warning",
    "display_error",
    # Formatting helpers
    "format_dict_as_list",
    "format_cost_summary",
    # Color palette customization
    "set_color_palette",
    "get_color_palette",
    # Classes
    "StreamingResultIterator",
]
