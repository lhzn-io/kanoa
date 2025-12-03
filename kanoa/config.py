"""
Global configuration and options for kanoa.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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

        log_bg_color (Tuple[int, int, int]): RGB color for log background.
            Default: (186, 164, 217) - Lavender

        backend_colors (Dict[str, Tuple[int, int, int]]): Optional per-backend colors.
            Example: {"gemini-3": (186, 164, 217), "claude": (170, 200, 180)}

        log_to_file (bool): Enable JSON file logging.
            Default: False (opt-in for privacy)

        log_file_path (Path | None): Custom log file path.
            If None, defaults to ~/.cache/kanoa/logs/kanoa.log

        log_handlers (List): Custom log handlers for remote logging (Datadog, etc.).
            Example: [DatadogHandler(), PrometheusHandler()]
    """

    def __init__(self) -> None:
        # Verbosity
        self.verbose: bool | int = False

        # Knowledge Base
        self._kb_home: Optional[Path | str] = None

        # Display Options
        self.display_result: bool = True
        self.log_style: str = "styled"  # "styled" or "plain"
        self.log_bg_color: Tuple[int, int, int] = (186, 164, 217)  # Lavender
        self.backend_colors: Dict[str, Tuple[int, int, int]] = {}

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
