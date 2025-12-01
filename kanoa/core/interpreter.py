from pathlib import Path
from typing import Any, Dict, Literal, Optional, Type, Union

import matplotlib.pyplot as plt

from ..backends.base import BaseBackend
from ..knowledge_base.base import BaseKnowledgeBase
from ..knowledge_base.pdf_kb import PDFKnowledgeBase
from ..knowledge_base.text_kb import TextKnowledgeBase
from .types import InterpretationResult


def _get_backend_class(name: str) -> Type[BaseBackend]:
    """
    Lazily import backend classes to handle missing dependencies.

    Raises:
        ImportError: If backend dependencies are not installed
        ValueError: If backend name is unknown
    """
    # Import from package __init__ which handles lazy loading
    from ..backends import ClaudeBackend, GeminiBackend, OpenAIBackend

    backends: Dict[str, Type[BaseBackend]] = {
        "claude": ClaudeBackend,
        "claude-sonnet-4.5": ClaudeBackend,
        "gemini": GeminiBackend,
        "gemini-3": GeminiBackend,
        "openai": OpenAIBackend,
        "vllm": OpenAIBackend,
    }

    if name not in backends:
        raise ValueError(
            f"Unknown backend: {name}. " f"Available: {list(backends.keys())}"
        )

    return backends[name]


class AnalyticsInterpreter:
    """
    AI-powered analytics interpreter with multi-backend support.

    Supports:
    - Multiple AI backends (Claude, Gemini, OpenAI)
    - Knowledge base grounding (text, PDFs, or none)
    - Multiple input types (figures, DataFrames, dicts)
    - Cost tracking and optimization

    Install backends with:
        pip install kanoa[gemini]   # Google Gemini
        pip install kanoa[claude]   # Anthropic Claude
        pip install kanoa[openai]   # OpenAI / vLLM
        pip install kanoa[all]      # All backends
    """

    def __init__(
        self,
        backend: Literal["claude", "gemini-3", "openai", "vllm"] = "gemini-3",
        kb_path: Optional[Union[str, Path]] = None,
        kb_content: Optional[str] = None,
        kb_type: Literal["text", "pdf", "auto"] = "auto",
        api_key: Optional[str] = None,
        max_tokens: int = 3000,
        enable_caching: bool = True,
        track_costs: bool = True,
        **backend_kwargs: Any,
    ):
        """
        Initialize analytics interpreter.

        Args:
            backend: AI backend to use ('claude', 'gemini-3', 'openai')
            kb_path: Path to knowledge base directory
            kb_content: Pre-loaded knowledge base string
            kb_type: Knowledge base type ('text', 'pdf', 'auto')
            api_key: API key for cloud backends (or use env vars)
            max_tokens: Maximum tokens for response
            enable_caching: Enable context caching for cost savings
            track_costs: Track token usage and costs
            **backend_kwargs: Additional backend-specific arguments

        Raises:
            ImportError: If the requested backend's dependencies aren't installed
            ValueError: If the backend name is unknown
        """
        # Initialize backend (lazy import handles missing deps)
        backend_class = _get_backend_class(backend)

        self.backend_name = backend
        self.backend: BaseBackend = backend_class(
            api_key=api_key,
            max_tokens=max_tokens,
            enable_caching=enable_caching,
            **backend_kwargs,
        )

        # Initialize knowledge base
        self.kb: Optional[BaseKnowledgeBase] = None
        if kb_path or kb_content:
            self.kb = self._initialize_knowledge_base(
                kb_path=kb_path, kb_content=kb_content, kb_type=kb_type, backend=backend
            )

        # Cost tracking
        self.track_costs = track_costs
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0}

    def _initialize_knowledge_base(
        self,
        kb_path: Optional[Union[str, Path]],
        kb_content: Optional[str],
        kb_type: str,
        backend: str,
    ) -> BaseKnowledgeBase:
        """Initialize appropriate knowledge base type."""
        # Auto-detect KB type
        if kb_type == "auto":
            if kb_path:
                kb_path = Path(kb_path)
                has_pdfs = any(kb_path.glob("**/*.pdf"))
                kb_type = "pdf" if has_pdfs else "text"
            else:
                kb_type = "text"

        # Create KB instance
        if kb_type == "pdf":
            # PDF KB requires Gemini backend
            if "gemini" not in backend.lower():
                raise ValueError(
                    "PDF knowledge base requires Gemini backend "
                    "(for native vision). "
                    f"Current backend: {backend}. "
                    "Use kb_type='text' or switch to 'gemini-3'."
                )
            return PDFKnowledgeBase(kb_path=kb_path, backend=self.backend)
        else:
            return TextKnowledgeBase(kb_path=kb_path, kb_content=kb_content)

    def interpret(
        self,
        fig: Optional[plt.Figure] = None,
        data: Optional[Any] = None,
        context: Optional[str] = None,
        focus: Optional[str] = None,
        include_kb: bool = True,
        display_result: bool = True,
        custom_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> InterpretationResult:
        """
        Interpret analytical output using configured backend.

        Args:
            fig: Matplotlib figure to interpret
            data: DataFrame/dict/other data to interpret
            context: Brief description of the output
            focus: Specific aspects to analyze
            include_kb: Whether to include knowledge base context
            display_result: Auto-display as Markdown in Jupyter
            custom_prompt: Override default prompt template
            **kwargs: Additional backend-specific arguments

        Returns:
            InterpretationResult with text, metadata, and cost info

        Raises:
            ValueError: If neither fig nor data provided
        """
        # Validate input
        if fig is None and data is None:
            raise ValueError("Must provide either 'fig' or 'data' to interpret")

        # Get knowledge base context
        kb_context = None
        if include_kb and self.kb:
            kb_context = self.kb.get_context()

        # Call backend
        result = self.backend.interpret(
            fig=fig,
            data=data,
            context=context,
            focus=focus,
            kb_context=kb_context,
            custom_prompt=custom_prompt,
            **kwargs,
        )

        # Track costs
        if self.track_costs and result.usage:
            self.total_tokens["input"] += result.usage.input_tokens
            self.total_tokens["output"] += result.usage.output_tokens
            self.total_cost += result.usage.cost

        # Auto-display
        if display_result:
            try:
                from ..utils.notebook import display_interpretation

                # Extract cache and model info from metadata
                cached = (
                    result.metadata.get("cache_used", False)
                    if result.metadata
                    else False
                )
                model_name = (
                    result.metadata.get("model", self.backend_name)
                    if result.metadata
                    else self.backend_name
                )
                display_interpretation(
                    text=result.text,
                    backend=self.backend_name,
                    model=model_name,
                    usage=result.usage,
                    cached=cached,
                )
            except ImportError:
                # Fallback to plain markdown display
                try:
                    from IPython.display import Markdown, display

                    display(Markdown(result.text))
                except ImportError:
                    pass  # Not in Jupyter

        return result

    def interpret_figure(
        self, fig: Optional[plt.Figure] = None, **kwargs: Any
    ) -> InterpretationResult:
        """Convenience method for matplotlib figures."""
        if fig is None:
            fig = plt.gcf()
        return self.interpret(fig=fig, **kwargs)

    def interpret_dataframe(self, df: Any, **kwargs: Any) -> InterpretationResult:
        """Convenience method for DataFrames."""
        return self.interpret(data=df, **kwargs)

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get summary of token usage and costs."""
        return {
            "backend": self.backend_name,
            "total_calls": self.backend.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "avg_cost_per_call": self.total_cost / max(self.backend.call_count, 1),
        }

    def reload_knowledge_base(self) -> None:
        """Reload knowledge base from source."""
        if self.kb:
            self.kb.reload()
