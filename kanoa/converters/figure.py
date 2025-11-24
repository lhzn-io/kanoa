import base64
import io

import matplotlib.pyplot as plt


def fig_to_base64(fig: plt.Figure) -> str:
    """Convert a Matplotlib figure to a base64‑encoded PNG string.

    The function renders the figure to an in‑memory ``BytesIO`` buffer, encodes the
    binary PNG data using ``base64`` and returns the resulting string. This is
    useful for embedding figures in JSON payloads or markdown.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
