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
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
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
            system_prompt: Custom system prompt template (overrides default).
                Use {kb_context} placeholder for knowledge base content.
            user_prompt: Custom user prompt template (overrides default).
                Use {context_block} and {focus_block} placeholders.
            **backend_kwargs: Additional backend-specific arguments

        Example:
            >>> # Use custom prompts for environmental analysis
            >>> interp = AnalyticsInterpreter(
            ...     system_prompt="You are an environmental data scientist...",
            ...     user_prompt="Analyze for ecological trends and impacts..."
            ... )

        Raises:
            ImportError: If the requested backend's dependencies aren't installed
            ValueError: If the backend name is unknown
        """
        # Create custom prompt templates if provided
        from ..utils.prompts import PromptTemplates

        prompt_templates = None

        # Priority: explicit params > global config > defaults
        if system_prompt or user_prompt:
            # Explicit parameters provided
            from ..utils.prompts import DEFAULT_PROMPTS

            prompt_templates = PromptTemplates(
                system_prompt=system_prompt or DEFAULT_PROMPTS.system_prompt,
                user_prompt=user_prompt or DEFAULT_PROMPTS.user_prompt,
            )
        else:
            # Check for global configuration
            from ..config import options

            if options.prompts.templates:
                prompt_templates = options.prompts.templates

        # Initialize backend (lazy import handles missing deps)
        backend_class = _get_backend_class(backend)

        self.backend_name = backend
        self.backend: BaseBackend = backend_class(
            api_key=api_key,
            max_tokens=max_tokens,
            enable_caching=enable_caching,
            prompt_templates=prompt_templates,
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

    def get_prompts(self) -> Dict[str, str]:
        """
        Get the current prompt templates used by this interpreter.

        Returns a dictionary with the active prompt templates:
        - system_prompt: Template for system instruction (with {kb_context} placeholder)
        - user_prompt: Template for user prompt (with {context_block}, {focus_block} placeholders)

        Example:
            >>> interp = AnalyticsInterpreter()
            >>> prompts = interp.get_prompts()
            >>> print(prompts["system_prompt"])
            You are an expert data analyst...

        Returns:
            Dict[str, str]: Dictionary with 'system_prompt' and 'user_prompt' keys
        """
        return {
            "system_prompt": self.backend.prompt_templates.get_system_prompt(
                self.backend_name
            ),
            "user_prompt": self.backend.prompt_templates.get_user_prompt(
                self.backend_name
            ),
        }

    def preview_prompt(
        self,
        context: Optional[str] = None,
        focus: Optional[str] = None,
        include_kb: bool = True,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        Preview the exact prompt that would be sent to the LLM.

        This method builds the complete prompt using the current templates
        and configuration, allowing you to see exactly what the AI will receive.

        Args:
            context: Brief description of the analytical output
            focus: Specific aspects to analyze
            include_kb: Whether to include knowledge base context
            custom_prompt: Custom prompt to preview (overrides templates)

        Example:
            >>> interp = AnalyticsInterpreter(kb_path="./my_kb")
            >>> prompt = interp.preview_prompt(
            ...     context="Inertial sensor calibration data",
            ...     focus="Drift compensation and alignment"
            ... )
            >>> print(prompt)

        Returns:
            str: The complete rendered prompt string
        """
        # Get KB context if requested
        kb_context = None
        if include_kb and self.kb:
            kb_context = self.backend.encode_kb(self.kb)

        # Build prompt using backend's method
        return self.backend._build_prompt(
            context=context,
            focus=focus,
            kb_context=kb_context,
            custom_prompt=custom_prompt,
        )

    def set_prompts(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
    ) -> "AnalyticsInterpreter":
        """
        Update prompt templates at runtime (chainable).

        This method allows you to modify the system and/or user prompt
        templates after the interpreter has been initialized.

        Args:
            system_prompt: New system prompt template (or None to keep current).
                Use {kb_context} placeholder for knowledge base content.
            user_prompt: New user prompt template (or None to keep current).
                Use {context_block} and {focus_block} placeholders.

        Example:
            >>> interp = AnalyticsInterpreter()
            >>> interp.set_prompts(
            ...     user_prompt="Provide exactly 3 bullet points..."
            ... ).interpret(data=df)

            >>> # Chain multiple configuration calls
            >>> interp.set_prompts(
            ...     system_prompt="You are an environmental data scientist..."
            ... ).with_kb("./conservation_kb")

        Returns:
            Self for method chaining
        """
        from ..utils.prompts import PromptTemplates

        # Get current templates
        current = self.backend.prompt_templates

        # Update with new values
        self.backend.prompt_templates = PromptTemplates(
            system_prompt=system_prompt or current.system_prompt,
            user_prompt=user_prompt or current.user_prompt,
            backend_overrides=current.backend_overrides,
        )

        return self
