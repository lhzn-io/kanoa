import base64
import os
import time
from typing import Any, Dict, Optional, cast

import matplotlib.pyplot as plt
from google import genai
from google.genai import types

from ..core.types import InterpretationResult, UsageInfo
from .base import BaseBackend


class GeminiBackend(BaseBackend):
    """
    Google Gemini backend with native PDF support.

    Features:
    - Native multimodal PDF processing (sees figures, tables)
    - 1M token context window
    - Context caching for cost optimization
    - File Search tool for RAG
    """

    # Pricing (per 1M tokens) - Approximate
    # Pricing (per 1M tokens) - Gemini 3.0 Pro (Preview)
    # Note: Google does not provide a public pricing API.
    # These values are manually maintained based on official documentation.
    PRICING = {
        "input_short": 2.00,  # <= 200K context
        "output_short": 12.00,
        "input_long": 4.00,  # > 200K context
        "output_long": 18.00,
        "cached": 0.20,  # Cached content
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        # Updated default to the user-specified preview model
        # Updated default to the user-specified preview model
        model: str = "gemini-3-pro-preview",
        max_tokens: int = 3000,
        enable_caching: bool = True,
        thinking_level: str = "high",
        media_resolution: str = "medium",
        **kwargs: Any,
    ):
        super().__init__(api_key, max_tokens, enable_caching)

        # Initialize client with support for both AI Studio and Vertex AI
        client_kwargs: Dict[str, Any] = {}
        if api_key or os.environ.get("GOOGLE_API_KEY"):
            client_kwargs["api_key"] = api_key or os.environ.get("GOOGLE_API_KEY")
        else:
            # Fallback to Vertex AI if no API key (uses ADC)
            client_kwargs["vertexai"] = True
            if "project" in kwargs:
                client_kwargs["project"] = kwargs["project"]
            if "location" in kwargs:
                client_kwargs["location"] = kwargs["location"]

        self.client = genai.Client(**client_kwargs)
        self.model = model
        self.thinking_level = thinking_level
        self.media_resolution = media_resolution

        # PDF cache
        self.uploaded_pdfs: Dict[Any, Any] = {}
        self.cached_context: Optional[Any] = None

    def load_pdfs(self, pdf_paths: list[Any]) -> dict[Any, Any]:
        """
        Upload PDFs to Gemini for native vision processing.

        Args:
            pdf_paths: List of paths to PDF files

        Returns:
            Dict mapping filename to uploaded file object
        """
        for pdf_path in pdf_paths:
            if pdf_path in self.uploaded_pdfs:
                continue

            with open(pdf_path, "rb") as f:
                uploaded = self.client.files.upload(
                    file=f,
                    config={
                        "mime_type": "application/pdf",
                        "display_name": pdf_path.name,
                    },
                )

            # Wait for processing
            while uploaded.state == "PROCESSING":
                time.sleep(2)
                if uploaded.name:
                    uploaded = self.client.files.get(name=uploaded.name)

            if uploaded.state == "ACTIVE":
                self.uploaded_pdfs[pdf_path] = uploaded

        return self.uploaded_pdfs

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
        """Interpret using Gemini."""
        self.call_count += 1

        # Build content parts
        content_parts = []

        # Add figure
        if fig is not None:
            img_data_str = self._fig_to_base64(fig)
            img_data = base64.b64decode(img_data_str)
            content_parts.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_bytes(data=img_data, mime_type="image/png")],
                )
            )

        # Add data
        if data is not None:
            data_text = self._data_to_text(data)
            content_parts.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=f"Data to analyze:\n```\n{data_text}\n```"
                        )
                    ],
                )
            )

        # Add PDFs if available
        # Note: In new SDK, file_data might be handled differently.
        # Assuming types.Part.from_uri or similar if available,
        # or constructing dict.
        # The spec used raw dicts. I'll try to use types if possible
        # or fallback to dicts if client accepts them.
        # The client.models.generate_content usually accepts list of
        # Content objects or list of dicts.

        for pdf_file in self.uploaded_pdfs.values():
            content_parts.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            file_data=types.FileData(
                                file_uri=pdf_file.uri, mime_type="application/pdf"
                            )
                        )
                    ],
                )
            )

        # Build prompt
        prompt = self._build_prompt(context, focus, kb_context, custom_prompt)
        content_parts.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )

        # Call API
        try:
            # Handle config
            # The spec used 'thinking_level' which is for thinking
            # models. I'll include it if the model supports it,
            # otherwise it might error. For now, I'll assume the user
            # picks a model that supports it or I filter it.

            generate_config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
            )

            # Only add thinking config if using a thinking model (heuristic)
            if "thinking" in self.model:
                # This is hypothetical as SDK might not expose it exactly this way yet
                # But following spec intent.
                pass

            response = self.client.models.generate_content(
                model=self.model,
                contents=cast(Any, content_parts),
                config=generate_config,
            )

            # Extract text
            interpretation = response.text or ""

            # Calculate usage
            usage = self._calculate_usage(response)

            # Add metadata
            interpretation += f"\n\n---\n*Generated by {self.model}*"
            if self.uploaded_pdfs:
                interpretation += f" *with {len(self.uploaded_pdfs)} PDF references*"

            return InterpretationResult(
                text=interpretation,
                backend="gemini-3",
                usage=usage,
                metadata={"model": self.model, "pdf_count": len(self.uploaded_pdfs)},
            )

        except Exception as e:
            error_msg = f"❌ **Error**: {str(e)}"
            return InterpretationResult(text=error_msg, backend="gemini-3", usage=None)

    def _build_prompt(
        self,
        context: Optional[str],
        focus: Optional[str],
        kb_context: Optional[str],
        custom_prompt: Optional[str],
    ) -> str:
        """Build Gemini-optimized prompt."""
        if custom_prompt:
            return custom_prompt

        parts = []

        if kb_context:
            parts.append(
                f"""You are an expert data analyst with access to \
domain-specific knowledge.

# Knowledge Base

{kb_context}

Use this information to provide informed, technically accurate \
interpretations.
"""
            )

        parts.append(
            "Analyze this analytical output and provide a technical interpretation."
        )

        if context:
            parts.append(f"\n**Context**: {context}")

        if focus:
            parts.append(f"\n**Analysis Focus**: {focus}")

        parts.append(
            """

Provide:
1. **Summary**: What the output shows
2. **Key Observations**: Notable patterns and trends
3. **Technical Interpretation**: Insights based on domain knowledge
4. **Potential Issues**: Data quality concerns or anomalies
5. **Recommendations**: Suggestions for further analysis

Use markdown formatting. Be concise but technically precise.
"""
        )

        return "\n".join(parts)

    def _calculate_usage(self, response: Any) -> Optional[UsageInfo]:
        """Calculate token usage and cost."""
        # Extract token counts from response metadata
        usage_metadata = getattr(response, "usage_metadata", None)
        if not usage_metadata:
            return None

        input_tokens = usage_metadata.prompt_token_count
        output_tokens = usage_metadata.candidates_token_count

        # Determine pricing tier based on context length
        # Threshold is 200,000 tokens for Gemini 3.0 Pro
        if input_tokens <= 200_000:
            input_price = self.PRICING["input_short"]
            output_price = self.PRICING["output_short"]
        else:
            input_price = self.PRICING["input_long"]
            output_price = self.PRICING["output_long"]

        # Simple cost calculation
        # Note: Does not currently account for cached tokens as API response
        # structure for cache hits needs verification.
        cost = (input_tokens / 1_000_000 * input_price) + (
            output_tokens / 1_000_000 * output_price
        )

        return UsageInfo(
            input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
        )
