"""
Global configuration and options for kanoa.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .utils.prompts import PromptTemplates


class PromptConfig:
    """
    Global prompt configuration.

    This class provides access to globally configured prompt templates,
    loaded from ~/.config/kanoa/prompts.yaml.

    Attributes:
        templates: PromptTemplates instance loaded from config file, or None

    Example:
        >>> from kanoa.config import options
        >>> # Check if custom prompts are configured
        >>> if options.prompts.templates:
        ...     print("Using custom prompts")
        >>> else:
        ...     print("Using default prompts")
    """

    def __init__(self) -> None:
        self._templates: Optional["PromptTemplates"] = None
        self._loaded: bool = False

    @property
    def templates(self) -> Optional["PromptTemplates"]:
        """
        Get global prompt templates (lazy loaded).

        Returns:
            PromptTemplates instance if config file exists, None otherwise
        """
        if not self._loaded:
            from .prompt_config import get_global_prompts

            self._templates = get_global_prompts()
            self._loaded = True
        return self._templates

    def reload(self) -> None:
        """Reload prompt configuration from disk."""
        self._loaded = False
        self._templates = None


class GeminiConfig:
    """Gemini-specific configuration."""

    def __init__(self) -> None:
        self.free_tier: bool = False


class Options:
    """
    Global options for kanoa.

    Attributes:
        verbose (bool | int): Control verbosity level.
            0 or False: Silent
            1 or True: Info (Uploads, cache status, token usage)
            2: Debug (Full request/response payloads)
        kb_home (Path | str | None): Default directory for persisting knowledge bases.
            If None, defaults to ~/.cache/kanoa/kb

        display_result (bool): Global default for display_result parameter.
            If True, auto-display AI interpretations in notebooks.
            If False, return results without displaying.

        log_style (str): Display style for verbose logging.
            "styled": Notebook-aware styled markdown boxes (default)
            "plain": Plain text output for all environments

        internal_log_bg_color (Tuple[int, int, int]): RGB color for internal log background.
            Default: (186, 164, 217) - Lavender
            Used by kanoa internals (ilog_* functions).

        user_log_bg_color (Tuple[int, int, int]): RGB color for user log background.
            Default: (128, 128, 128) - Gray
            Used by user-facing logs (log_* functions).

        user_log_opacity (float): Opacity for user log backgrounds.
            Default: 0.04 - Very translucent/clear
            Set higher (e.g., 0.12) for more visible user logs.

        default_log_stream (bool | str): Enable auto-collecting user logs in a stream.
            Default: True - User logs collected with no title, clear background.
            False: Disable auto-streaming.
            String: Use as stream title (e.g., "My App").

        backend_colors (Dict[str, Tuple[int, int, int]]): Optional per-backend colors.
            Example: {"gemini": (186, 164, 217), "claude": (170, 200, 180)}

        log_to_file (bool): Enable JSON file logging.
            Default: False (opt-in for privacy)

        log_file_path (Path | None): Custom log file path.
            If None, defaults to ~/.cache/kanoa/logs/kanoa.log

        log_handlers (List): Custom log handlers for remote logging (Datadog, etc.).
            Example: [DatadogHandler(), PrometheusHandler()]

        prompts (PromptConfig): Global prompt configuration.
            Access to globally configured prompt templates loaded from
            ~/.config/kanoa/prompts.yaml
    """

    def __init__(self) -> None:
        # Verbosity
        # Default: 1 (info level) - show token usage, cache status, uploads
        # Rationale: Data science workflows benefit from cost/performance transparency.
        # Users can opt-out with `kanoa.options.verbose = 0` if needed.
        # See docs/source/developer_guide/design_philosophy.md for details.
        self.verbose: bool | int = 1

        # Knowledge Base
        self._kb_home: Optional[Path | str] = None

        # Gemini Configuration
        self.gemini = GeminiConfig()

        # Display Options
        self.display_result: bool = True
        self.log_style: str = "styled"  # "styled" or "plain"
        self.internal_log_bg_color: Tuple[int, int, int] = (186, 164, 217)  # Lavender
        self.user_log_bg_color: Tuple[int, int, int] = (128, 128, 128)  # Gray (user)
        self.user_log_opacity: float = 0.04  # Very translucent for user logs
        self.backend_colors: Dict[str, Tuple[int, int, int]] = {}

        # Stream-specific colors (by stream title)
        # Example: {"kanoa": (186, 164, 217), "notebook": (255, 255, 255)}
        self.stream_colors: Dict[str, Tuple[int, int, int]] = {}

        # Default log stream (auto-created, collects all logs)
        # Set to True for untitled stream, string for titled, False to disable
        self.default_log_stream: bool | str = True  # Enabled with no title

        # File Logging
        self.log_to_file: bool = False
        self.log_file_path: Optional[Path] = None

        # Custom Handlers
        self.log_handlers: List[Any] = []

        # Token Guard Thresholds
        # Warn: ~2048 tokens (Gemini context caching minimum)
        self.token_warn_threshold = 2048
        # Approval: 50k tokens (~$0.10 - $0.20)
        self.token_approval_threshold = 50_000
        # Reject: 200k tokens (Safety limit)
        self.token_reject_threshold = 200_000
        # Auto-approve large requests (useful for scripts)
        self.auto_approve = False

        # Prompt Configuration
        self.prompts = PromptConfig()

    @property
    def kb_home(self) -> Path:
        if self._kb_home:
            return Path(self._kb_home)
        # Default to XDG cache home or ~/.cache
        xdg_cache = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        return Path(xdg_cache) / "kanoa" / "kb"

    @kb_home.setter
    def kb_home(self, value: str | Path | None) -> None:
        self._kb_home = value


options = Options()
