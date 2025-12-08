"""
Prompt templates for the interpreter.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

DEFAULT_SYSTEM_PROMPT = (
    """You are an expert data analyst with access to """
    """domain-specific knowledge.

# Knowledge Base

{kb_context}

Use this information to provide informed, technically accurate """
    """interpretations.
"""
)

DEFAULT_USER_PROMPT = (
    """Analyze this analytical output and provide a """
    """technical interpretation.

{context_block}
{focus_block}

Provide:
1. **Summary**: What the output shows
2. **Key Observations**: Notable patterns and trends
3. **Technical Interpretation**: Insights based on domain knowledge
4. **Potential Issues**: Data quality concerns or anomalies
5. **Recommendations**: Suggestions for further analysis

Use markdown formatting. Be concise but technically precise.
"""
)


@dataclass
class PromptTemplates:
    """
    Default prompt templates for analytical interpretation.

    This class centralizes all prompt templates used by kanoa backends.
    Templates can be customized at multiple levels:
    - Global: Via ~/.config/kanoa/prompts.yaml
    - Per-interpreter: Via AnalyticsInterpreter(..., system_prompt=...)
    - Per-call: Via interpret(..., custom_prompt=...)

    Template Variables:
        system_prompt:
            - {kb_context}: Knowledge base content (when available)

        user_prompt:
            - {context_block}: User-provided context description
            - {focus_block}: Specific focus areas for analysis

    Example:
        >>> templates = PromptTemplates()
        >>> templates.system_prompt
        'You are an expert data analyst...'

        >>> # Customize for specific domain
        >>> environmental_templates = PromptTemplates(
        ...     system_prompt="You are an environmental data scientist..."
        ... )
    """

    system_prompt: str = (
        """You are an expert data analyst with access to """
        """domain-specific knowledge.

# Knowledge Base

{kb_context}

Use this information to provide informed, technically accurate """
        """interpretations.
"""
    )

    user_prompt: str = (
        """Analyze this analytical output and provide a """
        """technical interpretation.

{context_block}
{focus_block}

Provide:
1. **Summary**: What the output shows
2. **Key Observations**: Notable patterns and trends
3. **Technical Interpretation**: Insights based on domain knowledge
4. **Potential Issues**: Data quality concerns or anomalies
5. **Recommendations**: Suggestions for further analysis

Use markdown formatting. Be concise but technically precise.
"""
    )

    # Per-backend customizations (optional)
    backend_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def get_system_prompt(self, backend: Optional[str] = None) -> str:
        """
        Get system prompt for a specific backend.

        Args:
            backend: Backend name (gemini, claude, openai, vllm).
                If None, returns the default system prompt.

        Returns:
            System prompt template string
        """
        if backend and backend in self.backend_overrides:
            return self.backend_overrides[backend].get(
                "system_prompt", self.system_prompt
            )
        return self.system_prompt

    def get_user_prompt(self, backend: Optional[str] = None) -> str:
        """
        Get user prompt for a specific backend.

        Args:
            backend: Backend name (gemini, claude, openai, vllm).
                If None, returns the default user prompt.

        Returns:
            User prompt template string
        """
        if backend and backend in self.backend_overrides:
            return self.backend_overrides[backend].get("user_prompt", self.user_prompt)
        return self.user_prompt


# Default instance for backward compatibility
DEFAULT_PROMPTS = PromptTemplates()
