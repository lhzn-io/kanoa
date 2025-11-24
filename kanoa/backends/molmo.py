from typing import Any, Optional

import matplotlib.pyplot as plt

from .base import BaseBackend, InterpretationResult


class MolmoBackend(BaseBackend):
    """
    Molmo backend implementation (Stub).

    Intended for local inference using Molmo models.
    """

    def interpret(
        self,
        fig: Optional[plt.Figure],
        data: Optional[Any],
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
        **kwargs: Any,
    ) -> InterpretationResult:
        """
        Interpret using Molmo (Not implemented).
        """
        return InterpretationResult(
            text=(
                "Molmo backend not implemented yet. "
                "This is a placeholder for local inference."
            ),
            backend="molmo",
        )

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        return ""
