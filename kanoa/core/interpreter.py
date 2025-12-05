from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple, Type, Union

import matplotlib.pyplot as plt

from ..backends.base import BaseBackend
from ..knowledge_base.manager import KnowledgeBaseManager
from .types import InterpretationResult

# Canonical list of supported backends (in recommended order: open-source first)
supported_backends: Tuple[str, ...] = ("vllm", "gemini", "claude", "openai")

# Type alias for backend parameter (must match supported_backends)
BackendType = Literal["vllm", "gemini", "claude", "openai"]


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
        "openai": OpenAIBackend,
        "vllm": OpenAIBackend,
    }

    if name not in backends:
        raise ValueError(f"Unknown backend: {name}. Available: {list(backends.keys())}")

    return backends[name]


class AnalyticsInterpreter:
    """
    AI-powered analytics interpreter with multi-backend support.

    Supports:
    - Multiple AI backends (vLLM, Gemini, Claude, OpenAI)
    - Knowledge base grounding (text, PDFs, or none)
    - Multiple input types (figures, DataFrames, dicts)
    - Cost tracking and optimization

    Install backends with:
        pip install kanoa[local]    # vLLM (Molmo, Gemma 3)
        pip install kanoa[gemini]   # Google Gemini
        pip install kanoa[claude]   # Anthropic Claude
        pip install kanoa[openai]   # OpenAI GPT models
        pip install kanoa[all]      # All backends
    """

    def __init__(
        self,
        backend: BackendType = "gemini",
        kb_path: Optional[Union[str, Path]] = None,
        kb_content: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 3000,
        enable_caching: bool = True,
        track_costs: bool = True,
        **backend_kwargs: Any,
    ):
        """
        Initialize analytics interpreter.

        Args:
            backend: AI backend to use ('vllm', 'gemini', 'claude', 'openai')
            kb_path: Path to knowledge base directory
            kb_content: Pre-loaded knowledge base string
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
        self.kb: Optional[KnowledgeBaseManager] = None
        if kb_path or kb_content:
            self.kb = KnowledgeBaseManager(kb_path=kb_path, kb_content=kb_content)

        # Cost tracking - delegated to backend
        self.track_costs = track_costs

    def with_kb(
        self,
        kb_path: Optional[Union[str, Path]] = None,
        kb_content: Optional[str] = None,
    ) -> "AnalyticsInterpreter":
        """
        Create a new interpreter instance with a specific knowledge base,
        sharing the same backend and cost tracking state.

        Behavior:
            - REPLACES any existing knowledge base.
            - Shares the underlying backend instance (and thus cost stats).
            - Returns a new AnalyticsInterpreter instance.

        Example:
            # Base interpreter (no KB)
            interp = AnalyticsInterpreter()

            # Specialized interpreter (shares costs with base)
            env_interp = interp.with_kb("kbs/environmental")
        """
        import copy

        # Create a shallow copy
        new_interpreter = copy.copy(self)

        # Initialize the new KB (Replaces existing)
        if kb_path or kb_content:
            new_interpreter.kb = KnowledgeBaseManager(
                kb_path=kb_path, kb_content=kb_content
            )
        else:
            new_interpreter.kb = None

        return new_interpreter

    def interpret(
        self,
        fig: Optional[plt.Figure] = None,
        data: Optional[Any] = None,
        context: Optional[str] = None,
        focus: Optional[str] = None,
        include_kb: bool = True,
        display_result: Optional[bool] = None,
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
            display_result: Auto-display as Markdown in Jupyter.
                If None, uses kanoa.options.display_result (default: True)
            custom_prompt: Override default prompt template
            **kwargs: Additional backend-specific arguments

        Returns:
            InterpretationResult with text, metadata, and cost info

        Raises:
            ValueError: If neither fig nor data provided
        """
        # Validate input
        if fig is None and data is None and custom_prompt is None:
            raise ValueError(
                "Must provide either 'fig', 'data', or 'custom_prompt' to interpret"
            )

        # Use global option if display_result not explicitly set
        from ..config import options

        if display_result is None:
            display_result = options.display_result

        # Get knowledge base context
        kb_context = None
        if include_kb and self.kb:
            kb_context = self.backend.encode_kb(self.kb)

        # Call backend (logs will go to active stream or handlers)
        result = self.backend.interpret(
            fig=fig,
            data=data,
            context=context,
            focus=focus,
            kb_context=kb_context,
            custom_prompt=custom_prompt,
            **kwargs,
        )

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
                cache_created = (
                    result.metadata.get("cache_created", False)
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
                    cache_created=cache_created,
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
        return self.backend.get_cost_summary()

    def get_kb(self) -> KnowledgeBaseManager:
        """
        Get the active knowledge base.

        Returns:
            The active KnowledgeBaseManager instance.

        Raises:
            RuntimeError: If no knowledge base has been configured.
        """
        if self.kb is None:
            raise RuntimeError(
                "No knowledge base configured. "
                "Initialize with 'kb_path' or use '.with_kb()'."
            )
        return self.kb

    def reload_knowledge_base(self) -> None:
        """Reload knowledge base from source."""
        if self.kb:
            self.kb.reload()

    def check_kb_cost(self) -> Any:
        """
        Check the cost/token count of the current knowledge base.

        Returns:
            TokenCheckResult or None if not supported/empty.
        """
        # Ensure KB is encoded via backend
        if self.kb:
            self.backend.encode_kb(self.kb)

        return self.backend.check_kb_cost()

    def get_cache_status(self) -> Dict[str, Any]:
        """
        Check the status of the context cache for the current KB.

        Returns:
            Dict with cache status details (exists, source, tokens, etc.)
            or {'exists': False, 'reason': ...} if not supported/found.
        """
        if not hasattr(self.backend, "get_cache_status"):
            return {
                "exists": False,
                "reason": f"Backend '{self.backend_name}' does not support caching",
            }

        kb_context = None
        if self.kb:
            kb_context = self.backend.encode_kb(self.kb)

        if not kb_context:
            return {"exists": False, "reason": "No knowledge base loaded"}

        from typing import cast

        return cast(
            "Dict[str, Any]", cast("Any", self.backend).get_cache_status(kb_context)
        )
