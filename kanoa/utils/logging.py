"""
Structured logging system for kanoa with pluggable handlers.

Provides notebook-aware logging with styled output, file logging,
and extensibility for remote logging services (Datadog, Prometheus, etc.).

Key Features:
    - Notebook detection with styled markdown output (lavender background)
    - Plain text console fallback
    - Optional JSON file logging with auto-rotation
    - Structured log records with context (backend, model, tokens, cost)
    - Pluggable handler protocol for custom integrations
    - Respects kanoa.options.verbose levels (0=Silent, 1=Info, 2=Debug)

Example:
    >>> from kanoa.utils.logging import log_info, log_warning
    >>> log_info("Processing 3 PDFs", context={"pdf_count": 3})
    >>> log_warning("Cache expired, recreating", title="Cache Miss")

    >>> # Enable file logging
    >>> import kanoa
    >>> kanoa.options.log_to_file = True
    >>> kanoa.options.verbose = 1

    >>> # Add custom handler
    >>> kanoa.options.log_handlers.append(MyDatadogHandler())
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

# Lazy imports for IPython
_ipython_available: Optional[bool] = None


# =============================================================================
# Core Data Structures
# =============================================================================


@dataclass
class LogRecord:
    """
    Structured log record with context.

    Attributes:
        timestamp: UTC timestamp of the log
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
        message: Human-readable message
        context: Structured context (backend, model, tokens, cost, etc.)
        source: Logger name (e.g., "kanoa.backends.gemini")
        title: Optional title for styled display
    """

    timestamp: datetime
    level: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "kanoa"
    title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "context": self.context,
            **({"title": self.title} if self.title else {}),
        }


class LogHandler(Protocol):
    """Protocol for custom log handlers."""

    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record.

        Args:
            record: Structured log record to emit
        """
        ...


# =============================================================================
# Built-in Handlers
# =============================================================================


class ConsoleHandler:
    """Plain text console handler for terminals."""

    def __init__(self, use_colors: bool = True) -> None:
        """
        Initialize console handler.

        Args:
            use_colors: Whether to use ANSI color codes (if supported)
        """
        self.use_colors = use_colors and sys.stdout.isatty()

    def emit(self, record: LogRecord) -> None:
        """Emit log record to console."""
        # Color codes
        colors = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[34m",  # Blue
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
        }
        reset = "\033[0m"

        prefix = f"[{record.level}]"
        if self.use_colors and record.level in colors:
            prefix = f"{colors[record.level]}{prefix}{reset}"

        title_str = f" {record.title}: " if record.title else " "
        print(f"{prefix}{title_str}{record.message}")


class NotebookHandler:
    """Styled markdown handler for Jupyter notebooks."""

    def __init__(self) -> None:
        """Initialize notebook handler."""
        self._check_ipython()

    def _check_ipython(self) -> bool:
        """Check if IPython display is available."""
        global _ipython_available
        if _ipython_available is None:
            try:
                from IPython.display import Markdown, display  # noqa: F401

                _ipython_available = True
            except ImportError:
                _ipython_available = False
        return _ipython_available or False

    def emit(self, record: LogRecord) -> None:
        """Emit styled log record to notebook."""
        if not self._check_ipython():
            # Fallback to console
            ConsoleHandler(use_colors=False).emit(record)
            return

        from IPython.display import Markdown, display

        # Import at runtime to avoid circular dependency
        from ..config import options

        # Get background color from options (default: lavender)
        bg_rgb = options.log_bg_color

        # Check for backend-specific colors
        backend = record.context.get("backend")
        if backend and backend in options.backend_colors:
            bg_rgb = options.backend_colors[backend]

        # Convert RGB to rgba with transparency
        bg_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.12)"
        border_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.35)"
        accent_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.75)"

        # Level-specific icons
        icons = {
            "DEBUG": "🔍",
            "INFO": "i",
            "WARNING": "⚠️",
            "ERROR": "❌",
        }
        icon = icons.get(record.level, "•")

        # Build title line
        title_text = record.title or record.level.title()
        title_line = (
            f'**<span style="font-size: 0.9em;">{icon} {title_text}</span>**\n\n'
        )

        # Wrap message in styled div
        styled_markdown = f"""
<div style="background: {bg_color};
            border: 1px solid {border_color};
            border-left: 3px solid {accent_color};
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 6px;
            font-size: 0.95em;">

{title_line}{record.message}

</div>
"""

        display(Markdown(styled_markdown))


class FileHandler:
    """JSON Lines file handler with auto-rotation."""

    def __init__(
        self,
        filepath: Optional[Path] = None,
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 7,
    ) -> None:
        """
        Initialize file handler.

        Args:
            filepath: Path to log file (defaults to ~/.cache/kanoa/logs/kanoa.log)
            max_bytes: Max file size before rotation (default: 100MB)
            backup_count: Number of backup files to keep (default: 7)
        """
        if filepath is None:
            # Use standard Python logging to file
            import os

            xdg_cache = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
            log_dir = Path(xdg_cache) / "kanoa" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            filepath = log_dir / "kanoa.log"

        self.filepath = Path(filepath)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Use Python's RotatingFileHandler for proper rotation
        from logging.handlers import RotatingFileHandler

        self._handler = RotatingFileHandler(
            str(self.filepath),
            maxBytes=max_bytes,
            backupCount=backup_count,
        )

    def emit(self, record: LogRecord) -> None:
        """Emit log record to file as JSON line."""
        json_line = json.dumps(record.to_dict())
        # Use the underlying handler's stream
        self._handler.stream.write(json_line + "\n")
        self._handler.stream.flush()

        # Check if rotation is needed
        if self._handler.shouldRollover(
            logging.LogRecord(
                name="kanoa",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="",
                args=(),
                exc_info=None,
            )
        ):
            self._handler.doRollover()


class StructuredLogHandler:
    """
    Base class for structured logging handlers (Datadog, Prometheus, etc.).

    Subclass this to implement custom remote logging integrations.

    Example:
        >>> class DatadogHandler(StructuredLogHandler):
        ...     def emit(self, record: LogRecord) -> None:
        ...         datadog.api.Log.create(
        ...             message=record.message,
        ...             level=record.level.lower(),
        ...             attributes=record.context
        ...         )
    """

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record to remote service.

        Args:
            record: Structured log record to emit

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement emit()")


# =============================================================================
# Core Logging Functions
# =============================================================================


def _get_handlers() -> List[LogHandler]:
    """Get active log handlers based on kanoa.options configuration."""
    # Import here to avoid circular dependency
    from ..config import options

    handlers: List[LogHandler] = []

    # Always add appropriate primary handler based on environment
    if options.log_style == "plain" or not _check_notebook_env():
        handlers.append(ConsoleHandler())
    else:
        handlers.append(NotebookHandler())

    # Add file handler if enabled
    if options.log_to_file:
        handlers.append(FileHandler(filepath=options.log_file_path))

    # Add custom handlers
    handlers.extend(options.log_handlers)

    return handlers


def _check_notebook_env() -> bool:
    """Check if we're running in a Jupyter notebook."""
    global _ipython_available
    if _ipython_available is None:
        try:
            from IPython.core.getipython import get_ipython

            ipython = get_ipython()
            _ipython_available = ipython is not None and hasattr(ipython, "kernel")
        except ImportError:
            _ipython_available = False
    return _ipython_available or False


def _emit_log(
    level: str,
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
    verbose_threshold: int = 1,
) -> None:
    """
    Emit a log record to all active handlers.

    Args:
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name
        verbose_threshold: Minimum verbose level required (0=always, 1=info, 2=debug)
    """
    # Import here to avoid circular dependency
    from ..config import options

    # Check verbose level
    verbose_level = int(options.verbose) if options.verbose else 0
    if verbose_level < verbose_threshold:
        return

    # Create log record
    record = LogRecord(
        timestamp=datetime.utcnow(),
        level=level,
        message=message,
        context=context or {},
        source=source,
        title=title,
    )

    # Emit to all handlers
    handlers = _get_handlers()
    for handler in handlers:
        try:
            handler.emit(record)
        except Exception as e:
            # Fallback to stderr if handler fails
            print(
                f"[kanoa] Log handler {type(handler).__name__} failed: {e}",
                file=sys.stderr,
            )


# =============================================================================
# Public API
# =============================================================================


def log_debug(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Log debug message (verbose=2).

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name

    Example:
        >>> log_debug("Full request payload", context={"payload": {...}})
    """
    _emit_log("DEBUG", message, title, context, source, verbose_threshold=2)


def log_info(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Log info message (verbose=1).

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name

    Example:
        >>> log_info("Found 3 PDFs to process", context={"pdf_count": 3})
        >>> log_info("Upload complete", title="File API")
    """
    _emit_log("INFO", message, title, context, source, verbose_threshold=1)


def log_warning(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Log warning message (verbose=1).

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name

    Example:
        >>> log_warning("Cache expired, recreating", title="Cache Miss")
        >>> log_warning("Token count estimation failed", context={"error": str(e)})
    """
    _emit_log("WARNING", message, title, context, source, verbose_threshold=1)


def log_error(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Log error message (always shown, ignores verbose).

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name

    Example:
        >>> log_error(
        ...     "Failed to upload PDF",
        ...     context={"file": "report.pdf", "error": str(e)}
        ... )
    """
    _emit_log("ERROR", message, title, context, source, verbose_threshold=0)


__all__ = [
    # Core types
    "LogRecord",
    "LogHandler",
    # Handlers
    "ConsoleHandler",
    "NotebookHandler",
    "FileHandler",
    "StructuredLogHandler",
    # Logging functions
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
]
