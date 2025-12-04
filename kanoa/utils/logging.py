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
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

# Lazy imports for IPython
_ipython_available: Optional[bool] = None

# Active log stream (thread-local for safety)
_log_stream_stack: threading.local = threading.local()

# Default stream singleton (auto-created per notebook session)
_default_stream: Optional["LogStream"] = None


def _get_active_stream() -> Optional["LogStream"]:
    """Get currently active log stream, if any."""
    if not hasattr(_log_stream_stack, "stack"):
        _log_stream_stack.stack = []
    return _log_stream_stack.stack[-1] if _log_stream_stack.stack else None


_post_exec_hook_registered = False


def _on_cell_complete() -> None:
    """
    IPython post-execute callback to mark the default stream as finalized.

    This is called after each cell completes execution, allowing us to
    distinguish "rendered in this cell" from "rendered in a previous cell".
    """
    global _default_stream  # noqa: PLW0602

    if _default_stream is not None:
        _default_stream._cell_finalized = True  # type: ignore[attr-defined]


def _register_post_exec_hook() -> None:
    """Register the post-execute hook with IPython (once only)."""
    global _post_exec_hook_registered
    if _post_exec_hook_registered:
        return

    try:
        from IPython.core.getipython import get_ipython

        ipython = get_ipython()
        if ipython is not None:
            ipython.events.register("post_execute", _on_cell_complete)
            _post_exec_hook_registered = True
    except Exception:
        pass  # Not in IPython or hook registration failed


def _get_or_create_default_stream() -> Optional["LogStream"]:
    """
    Get or create the default log stream for user-facing logs.

    Auto-creates a fresh stream per cell execution in notebooks by using
    IPython's post-execute hook to mark streams as finalized after cell
    completion.

    User logs use a clear/translucent background (configurable via
    options.user_log_bg_color and options.user_log_opacity).

    Returns None if:
    - Not in notebook environment
    - default_log_stream option is False
    - User has explicitly created their own stream
    """
    global _default_stream

    from ..config import options

    # Check if default streaming is disabled (False disables, True or string enables)
    if options.default_log_stream is False:
        return None

    # Check if we're in a notebook
    if not _check_notebook_env():
        return None

    # Check if user has an explicit stream active
    if _get_active_stream() is not None:
        return None

    # Register post-execute hook (idempotent)
    _register_post_exec_hook()

    # Detect new cell execution
    # If the previous stream was finalized (cell completed), create a fresh one
    if _default_stream is not None and getattr(
        _default_stream, "_cell_finalized", False
    ):
        _default_stream = None

    # Create stream if needed - use user log color (clear/translucent)
    if _default_stream is None:
        # Title: None if True (untitled), otherwise use the string value
        title = (
            None if options.default_log_stream is True else options.default_log_stream
        )
        _default_stream = LogStream(
            title=title,
            bg_color=options.user_log_bg_color,
            auto_display=True,
        )
        # Mark this as a user stream for special opacity handling
        _default_stream._is_user_stream = True  # type: ignore[attr-defined]
        # Note: We intentionally do NOT call start() here because the default
        # stream should not be pushed onto the stack. Only explicit log_stream()
        # contexts use the stack. This allows _get_or_create_default_stream()
        # to be called on every log and check _cell_finalized properly.

    return _default_stream


def _push_stream(stream: "LogStream") -> None:
    """Push a new log stream onto the stack."""
    if not hasattr(_log_stream_stack, "stack"):
        _log_stream_stack.stack = []
    _log_stream_stack.stack.append(stream)


def _pop_stream() -> None:
    """Pop the current log stream from the stack."""
    if hasattr(_log_stream_stack, "stack") and _log_stream_stack.stack:
        _log_stream_stack.stack.pop()


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

        # Standard console prefixes
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
        bg_rgb = options.internal_log_bg_color

        # Check for backend-specific colors
        backend = record.context.get("backend")
        if backend and backend in options.backend_colors:
            bg_rgb = options.backend_colors[backend]

        # Convert RGB to rgba with transparency
        bg_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.12)"
        border_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.35)"
        accent_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, 0.75)"

        # Level-specific opacity (simple and clean)
        opacities = {
            "DEBUG": "0.5",
            "INFO": "0.85",
            "WARNING": "0.95",
            "ERROR": "1.0",
        }
        opacity = opacities.get(record.level, "0.85")

        # Build title line
        title_text = record.title or "kanoa"
        title_line = f'<div style="font-weight: 600; margin-bottom: 8px; opacity: 0.9;">{title_text}</div>\n\n'

        # Wrap message in styled div
        styled_markdown = f"""
<div style="background: {bg_color};
            border: 1px solid {border_color};
            border-left: 3px solid {accent_color};
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 6px;
            font-size: 0.9em;
            line-height: 1.5;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono', 'Source Code Pro', monospace;
            box-sizing: border-box;
            max-width: 100%;
            overflow-x: auto;
            word-wrap: break-word;">

{title_line}<div style="opacity: {opacity};">{record.message}</div>

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
# Log Stream Context Manager
# =============================================================================


class LogStream:
    """
    Context manager for streaming logs into a single styled container.

    Accumulates log messages and renders them in one cohesive output,
    updating in-place for notebooks (via display_id) or printing
    progressively for consoles.

    Example:
        >>> with log_stream(title="Processing Data"):
        ...     log_info("Step 1: Loading...")
        ...     log_info("Step 2: Transforming...")
        ...     log_info("Step 3: Complete!")
        # All 3 messages appear in a single lavender box

        >>> # Can also be used explicitly
        >>> stream = LogStream(title="Custom Operation")
        >>> stream.start()
        >>> log_info("Working...")
        >>> stream.stop()

        >>> # Log rich objects like DataFrames
        >>> import pandas as pd
        >>> df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        >>> with log_stream(title="Data Analysis"):
        ...     log_info("Loading data...")
        ...     log_object(df, label="Dataset")  # Renders as styled table
    """

    def __init__(
        self,
        title: Optional[str] = None,
        bg_color: Optional[tuple[int, int, int]] = None,
        bg_opacity: Optional[float] = None,
        auto_display: bool = True,
    ) -> None:
        """
        Initialize log stream.

        Args:
            title: Optional title for the log container
            bg_color: Override background color (RGB tuple)
            bg_opacity: Override background opacity (0.0-1.0)
            auto_display: If False, caller must manually call render()
        """
        self.title = title
        self.bg_color = bg_color
        self.bg_opacity = bg_opacity
        self.auto_display = auto_display
        self.messages: List[str] = []
        self.display_id = f"kanoa-log-{id(self)}"
        self._is_notebook = self._check_ipython()
        self._started = False
        self._last_message_count = 0

    def _check_ipython(self) -> bool:
        """Check if running in notebook."""
        global _ipython_available
        if _ipython_available is None:
            try:
                from IPython.core.getipython import get_ipython

                _ipython_available = get_ipython() is not None
            except ImportError:
                _ipython_available = False
        return _ipython_available or False

    def add_message(self, record: LogRecord) -> None:
        """
        Add a log message to the stream.

        Args:
            record: LogRecord to add
        """
        # Level-specific opacity (simple and clean)
        opacities = {
            "DEBUG": "0.5",  # Very translucent
            "INFO": "0.85",  # Normal
            "WARNING": "0.95",  # Slightly emphasized
            "ERROR": "1.0",  # Full opacity
        }
        opacity = opacities.get(record.level, "0.85")

        # Format message with optional title
        if record.title:
            msg = f'<div style="opacity: {opacity};">{record.title}: {record.message}</div>'
        else:
            msg = f'<div style="opacity: {opacity};">{record.message}</div>'

        self.messages.append(msg)

        if self.auto_display:
            self.render()

    def add_html(self, html: str, label: Optional[str] = None) -> None:
        """
        Add raw HTML content to the stream (e.g., DataFrame tables).

        Args:
            html: Raw HTML content to embed
            label: Optional label to display above the content
        """
        if label:
            msg = f'<div style="margin: 8px 0;"><div style="opacity: 0.7; margin-bottom: 4px; font-weight: 500;">{label}</div>{html}</div>'
        else:
            msg = f'<div style="margin: 8px 0;">{html}</div>'

        self.messages.append(msg)

        if self.auto_display:
            self.render()

    def add_text(self, text: str, label: Optional[str] = None) -> None:
        """
        Add plain text content to the stream (fallback for console).

        Args:
            text: Plain text content
            label: Optional label to display above the content
        """
        if label:
            msg = f'<div style="margin: 8px 0;"><div style="opacity: 0.7; margin-bottom: 4px; font-weight: 500;">{label}</div><pre style="margin: 0; white-space: pre-wrap;">{text}</pre></div>'
        else:
            msg = f'<div style="margin: 8px 0;"><pre style="margin: 0; white-space: pre-wrap;">{text}</pre></div>'

        self.messages.append(msg)

        if self.auto_display:
            self.render()

    def render(self) -> None:
        """Render accumulated messages to output."""
        if not self.messages:
            return

        if self._is_notebook:
            self._render_notebook()
        else:
            self._render_console()

    def _render_notebook(self) -> None:
        """Render to Jupyter notebook with live updates."""
        from IPython.display import Markdown, display, update_display

        # Import at runtime to avoid circular dependency
        from ..config import options

        # Get background color
        bg_rgb = self.bg_color or options.internal_log_bg_color

        # Determine opacity: explicit > user_stream default > internal default
        if self.bg_opacity is not None:
            opacity = self.bg_opacity
        elif getattr(self, "_is_user_stream", False):
            opacity = options.user_log_opacity
        else:
            opacity = 0.12

        is_user_stream = getattr(self, "_is_user_stream", False)
        bg_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, {opacity})"
        border_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, {0.35 if not is_user_stream else 0.15})"
        accent_color = f"rgba({bg_rgb[0]}, {bg_rgb[1]}, {bg_rgb[2]}, {0.75 if not is_user_stream else 0.25})"

        # Build title line
        title_line = ""
        if self.title:
            title_line = f'<div style="font-weight: 600; margin-bottom: 10px; font-size: 1.1em; opacity: 0.9;">{self.title}</div>\n'

        # Combine messages (already wrapped in divs from add_message)
        content = "\n".join(self.messages)

        styled_markdown = f"""
<div style="background: {bg_color};
            border: 1px solid {border_color};
            border-left: 3px solid {accent_color};
            padding: 14px 18px;
            margin: 10px 0;
            border-radius: 6px;
            font-size: 0.9em;
            line-height: 1.5;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono', 'Source Code Pro', monospace;
            box-sizing: border-box;
            max-width: 100%;
            overflow-x: auto;
            word-wrap: break-word;">

{title_line}{content}

</div>
"""

        if self._started:
            # Update existing display
            update_display(Markdown(styled_markdown), display_id=self.display_id)
        else:
            # Create new display
            display(Markdown(styled_markdown), display_id=self.display_id)
            self._started = True

    def _render_console(self) -> None:
        """Render to console (print new messages only)."""
        import re

        # Only print messages that haven't been printed yet
        # For console, we print progressively, not all at once
        if not self._started:
            if self.title:
                print(f"\n{'=' * 60}")
                print(self.title)
                print(f"{'=' * 60}")
            self._started = True

        # Print only new messages since last render
        new_messages = self.messages[self._last_message_count :]
        for msg in new_messages:
            # Strip HTML tags for console output
            clean_msg = re.sub(r"<[^>]+>", "", msg)
            # Also strip markdown bold
            clean_msg = clean_msg.replace("**", "")
            # Collapse multiple newlines
            clean_msg = re.sub(r"\n{3,}", "\n\n", clean_msg)
            print(clean_msg.strip())

        self._last_message_count = len(self.messages)

    def start(self) -> None:
        """Start the log stream (push to stack)."""
        _push_stream(self)

    def stop(self) -> None:
        """Stop the log stream (pop from stack)."""
        _pop_stream()
        # Final render
        if self.messages and self.auto_display:
            self.render()

    def __enter__(self) -> "LogStream":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


def log_stream(
    title: Optional[str] = None,
    bg_color: Optional[tuple[int, int, int]] = None,
    bg_opacity: Optional[float] = None,
) -> LogStream:
    """
    Create a log stream context for collecting logs into one container.

    Args:
        title: Optional title for the log container
        bg_color: Optional background color override (RGB tuple).
            Defaults to user_log_bg_color (gray).
        bg_opacity: Optional background opacity (0.0-1.0).
            Defaults to user_log_opacity.

    Returns:
        LogStream context manager

    Example:
        >>> with log_stream(title="Data Processing"):
        ...     log_info("Loading data...")
        ...     log_info("Transforming...")
        ...     log_info("Complete!")
        # All logs appear in a single styled box

        >>> # Custom color and opacity
        >>> with log_stream(title="Ocean", bg_color=(2, 62, 138), bg_opacity=0.2):
        ...     log_info("Deep blue theme")
    """
    # Import here to avoid circular dependency
    from ..config import options

    # Default to user color (gray) for user-created streams
    effective_bg_color = bg_color if bg_color is not None else options.user_log_bg_color
    stream = LogStream(title=title, bg_color=effective_bg_color, bg_opacity=bg_opacity)
    # Mark as user stream for consistent opacity handling
    stream._is_user_stream = True  # type: ignore[attr-defined]
    return stream


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
    stream: Optional["LogStream"] = None,
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
        stream: Optional specific stream to route to (otherwise uses active stream)
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

    # Route to specified stream, active stream, or default stream
    target_stream = stream or _get_active_stream() or _get_or_create_default_stream()
    if target_stream:
        # Add to stream instead of emitting directly
        target_stream.add_message(record)
        return

    # No stream - emit to handlers normally
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


def _is_rich_object(obj: Any) -> bool:
    """Check if object has rich HTML representation (DataFrame, Series, etc.)."""
    return hasattr(obj, "_repr_html_") and callable(obj._repr_html_)


def log_debug(
    message: Any,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
    stream: Optional["LogStream"] = None,
) -> None:
    """
    Log debug message (verbose=2).

    Args:
        message: Message string or rich object (DataFrame, Series, etc.)
        title: Optional title/label for styled display
        context: Structured context dictionary
        source: Logger name
        stream: Optional specific stream to route to

    Example:
        >>> log_debug("Full request payload", context={"payload": {...}})
        >>> log_debug(df, title="Debug DataFrame")  # Rich objects supported
    """
    # Detect rich objects (DataFrame, etc.) and delegate to log_object
    if _is_rich_object(message):
        from ..config import options

        verbose_level = int(options.verbose) if options.verbose else 0
        if verbose_level >= 2:  # DEBUG threshold
            log_object(message, label=title, stream=stream)
        return

    _emit_log(
        "DEBUG",
        str(message),
        title,
        context,
        source,
        verbose_threshold=2,
        stream=stream,
    )


def log_info(
    message: Any,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
    stream: Optional["LogStream"] = None,
) -> None:
    """
    Log info message (verbose=1).

    Args:
        message: Message string or rich object (DataFrame, Series, etc.)
        title: Optional title/label for styled display
        context: Structured context dictionary
        source: Logger name
        stream: Optional specific stream to route to

    Example:
        >>> log_info("Found 3 PDFs to process", context={"pdf_count": 3})
        >>> log_info(df, title="Loaded Data")  # Rich objects supported
        >>> log_info(df)  # DataFrames render as styled tables
    """
    # Detect rich objects (DataFrame, etc.) and delegate to log_object
    if _is_rich_object(message):
        from ..config import options

        verbose_level = int(options.verbose) if options.verbose else 0
        if verbose_level >= 1:  # INFO threshold
            log_object(message, label=title, stream=stream)
        return

    _emit_log(
        "INFO", str(message), title, context, source, verbose_threshold=1, stream=stream
    )


def log_warning(
    message: Any,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
    stream: Optional["LogStream"] = None,
) -> None:
    """
    Log warning message (verbose=1).

    Args:
        message: Message string or rich object (DataFrame, Series, etc.)
        title: Optional title/label for styled display
        context: Structured context dictionary
        source: Logger name
        stream: Optional specific stream to route to

    Example:
        >>> log_warning("Cache expired, recreating", title="Cache Miss")
        >>> log_warning(df, title="Problematic Data")  # Rich objects supported
    """
    # Detect rich objects (DataFrame, etc.) and delegate to log_object
    if _is_rich_object(message):
        from ..config import options

        verbose_level = int(options.verbose) if options.verbose else 0
        if verbose_level >= 1:  # WARNING threshold
            log_object(message, label=title, stream=stream)
        return

    _emit_log(
        "WARNING",
        str(message),
        title,
        context,
        source,
        verbose_threshold=1,
        stream=stream,
    )


def log_error(
    message: Any,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
    stream: Optional["LogStream"] = None,
) -> None:
    """
    Log error message (always shown, ignores verbose).

    Args:
        message: Message string or rich object (DataFrame, Series, etc.)
        title: Optional title/label for styled display
        context: Structured context dictionary
        source: Logger name
        stream: Optional specific stream to route to

    Example:
        >>> log_error("Failed to upload PDF", context={"file": "report.pdf"})
        >>> log_error(df, title="Error Data")  # Rich objects supported
    """
    # Detect rich objects (DataFrame, etc.) and delegate to log_object
    if _is_rich_object(message):
        # Error always shows (threshold=0)
        log_object(message, label=title, stream=stream, verbose_threshold=0)
        return

    _emit_log(
        "ERROR",
        str(message),
        title,
        context,
        source,
        verbose_threshold=0,
        stream=stream,
    )


def log_object(
    obj: Any,
    label: Optional[str] = None,
    stream: Optional["LogStream"] = None,
    verbose_threshold: int = 1,
) -> None:
    """
    Log a rich object (DataFrame, Series, etc.) with native rendering.

    In notebooks, objects with `_repr_html_()` (like pandas DataFrames)
    will be rendered as styled HTML tables within the log stream container.
    Falls back to str() representation for other objects or console output.

    Args:
        obj: Object to display (DataFrame, Series, or any object)
        label: Optional label to display above the object
        stream: Optional specific stream to route to
        verbose_threshold: Minimum verbose level (0=always, 1=info, 2=debug)

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
        >>> log_object(df, label="Sample Data")

        >>> # Within a log stream
        >>> with log_stream(title="Data Analysis"):
        ...     log_info("Loading dataset...")
        ...     log_object(df, label="Loaded DataFrame")
        ...     log_info("Processing complete!")
    """
    from ..config import options

    # Check verbose level
    verbose_level = int(options.verbose) if options.verbose else 0
    if verbose_level < verbose_threshold:
        return

    # Get target stream
    target_stream = stream or _get_active_stream() or _get_or_create_default_stream()

    if target_stream:
        # Check if object has _repr_html_ (pandas DataFrame, Series, etc.)
        if hasattr(obj, "_repr_html_") and target_stream._is_notebook:
            html = obj._repr_html_()
            target_stream.add_html(html, label=label)
        else:
            # Fallback to string representation
            target_stream.add_text(str(obj), label=label)
        return

    # No stream - display directly
    if _check_notebook_env():
        from IPython.display import HTML, display

        if hasattr(obj, "_repr_html_"):
            html = obj._repr_html_()
            if label:
                html = f'<div style="opacity: 0.7; margin-bottom: 4px; font-weight: 500;">{label}</div>{html}'
            display(HTML(html))
        else:
            if label:
                print(f"{label}:")
            print(obj)
    else:
        # Console fallback
        if label:
            print(f"{label}:")
        print(obj)


# =============================================================================
# Internal Logging API (for kanoa internals - lavender background)
# =============================================================================

# Thread-local storage for internal stream
_internal_stream: Optional["LogStream"] = None


def _get_or_create_internal_stream() -> Optional["LogStream"]:
    """
    Get or create the internal log stream for kanoa internals.

    This stream uses the lavender background color and is titled "kanoa".
    It's separate from user-facing logs which use a clear/translucent background.
    """
    global _internal_stream

    from ..config import options

    # Check if we're in a notebook
    if not _check_notebook_env():
        return None

    # Check if user has an explicit stream active
    if _get_active_stream() is not None:
        return None

    # Register post-execute hook (idempotent)
    _register_post_exec_hook()

    # Detect new cell execution
    if _internal_stream is not None and getattr(
        _internal_stream, "_cell_finalized", False
    ):
        _internal_stream = None

    # Create stream if needed - use lavender background
    if _internal_stream is None:
        _internal_stream = LogStream(
            title="kanoa",
            bg_color=options.internal_log_bg_color,  # Lavender by default
            auto_display=True,
        )

    return _internal_stream


def _emit_internal_log(
    level: str,
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
    verbose_threshold: int = 1,
) -> None:
    """
    Emit a log record for kanoa internal operations.

    Always routes to the internal "kanoa" stream with lavender background.
    """
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

    # Route to internal stream (lavender background)
    target_stream = _get_active_stream() or _get_or_create_internal_stream()
    if target_stream:
        target_stream.add_message(record)
        return

    # No stream - emit to handlers normally
    handlers = _get_handlers()
    for handler in handlers:
        try:
            handler.emit(record)
        except Exception as e:
            print(
                f"[kanoa] Log handler {type(handler).__name__} failed: {e}",
                file=sys.stderr,
            )


def ilog_debug(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Internal debug log (verbose=2) - for kanoa internals.

    Uses lavender background in notebooks. Prefer this over log_debug()
    for all kanoa library internal logging.

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name
    """
    _emit_internal_log("DEBUG", message, title, context, source, verbose_threshold=2)


def ilog_info(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Internal info log (verbose=1) - for kanoa internals.

    Uses lavender background in notebooks. Prefer this over log_info()
    for all kanoa library internal logging.

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name
    """
    _emit_internal_log("INFO", message, title, context, source, verbose_threshold=1)


def ilog_warning(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Internal warning log (verbose=1) - for kanoa internals.

    Uses lavender background in notebooks. Prefer this over log_warning()
    for all kanoa library internal logging.

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name
    """
    _emit_internal_log("WARNING", message, title, context, source, verbose_threshold=1)


def ilog_error(
    message: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    source: str = "kanoa",
) -> None:
    """
    Internal error log (always shown) - for kanoa internals.

    Uses lavender background in notebooks. Prefer this over log_error()
    for all kanoa library internal logging.

    Args:
        message: Human-readable message
        title: Optional title for styled display
        context: Structured context dictionary
        source: Logger name
    """
    _emit_internal_log("ERROR", message, title, context, source, verbose_threshold=0)


__all__ = [
    # Core types
    "LogRecord",
    "LogHandler",
    # Handlers
    "ConsoleHandler",
    "NotebookHandler",
    "FileHandler",
    "StructuredLogHandler",
    # Streaming context
    "LogStream",
    "log_stream",
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
]
