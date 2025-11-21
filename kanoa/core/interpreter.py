"""
Main AnalyticsInterpreter class.

See PRODUCT_SPEC.md for complete implementation details.
"""

from pathlib import Path
from typing import Any, Literal, Optional, Union

import matplotlib.pyplot as plt


class AnalyticsInterpreter:
    """
    AI-powered analytics interpreter.

    TODO: Implement according to PRODUCT_SPEC.md
    """

    def __init__(
        self,
        backend: Literal["claude", "gemini-3", "molmo"] = "gemini-3",
        kb_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> None:
        raise NotImplementedError("See PRODUCT_SPEC.md for implementation")

    def interpret(
        self,
        fig: Optional[plt.Figure] = None,
        data: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError("See PRODUCT_SPEC.md for implementation")
