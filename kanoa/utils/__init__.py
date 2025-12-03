"""Utility functions for kanoa."""

from .logging import (
    LogStream,
    ilog_debug,
    ilog_error,
    ilog_info,
    ilog_warning,
    log_debug,
    log_error,
    log_info,
    log_object,
    log_stream,
    log_warning,
)
from .notebook import (
    display_error,
    display_info,
    display_interpretation,
    display_result,
    display_success,
    display_warning,
    format_cost_summary,
    format_dict_as_list,
    get_color_palette,
    set_color_palette,
)

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
    # Logging functions (user-facing, clear background)
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_object",
    # Internal logging functions (kanoa internals, lavender background)
    "ilog_debug",
    "ilog_info",
    "ilog_warning",
    "ilog_error",
    # Streaming context
    "LogStream",
    "log_stream",
]
