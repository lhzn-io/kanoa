"""
Global configuration and options for kanoa.
"""

import os
from pathlib import Path


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
    """

    def __init__(self):
        self.verbose = False
        self._kb_home = None

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
