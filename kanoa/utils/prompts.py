"""
Prompt templates for the interpreter.
"""

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
