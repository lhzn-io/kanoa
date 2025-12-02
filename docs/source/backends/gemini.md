# Google Gemini Backend

The `GeminiBackend` provides access to Google's Gemini models via the `google-genai` SDK. It supports both Google AI Studio (API Key) and Vertex AI (ADC) authentication methods.

## Authentication

`kanoa` automatically detects your environment:

1. **Google AI Studio**: If `GOOGLE_API_KEY` is set, it uses the AI Studio API.
2. **Vertex AI**: If no API key is found, it falls back to Application Default Credentials (ADC) for Vertex AI.

## File Handling & Context Caching

The backend handles file uploads differently depending on the environment:

### AI Studio vs. Vertex AI

* **AI Studio**: Uses the **File API** to upload files to a temporary staging area. The model references these files via URI.
* **Vertex AI**: The File API is not available. `kanoa` automatically switches to an **inline transfer strategy**, reading file bytes and passing them directly to the model as inline data.

### Production Best Practice

For production datasets on Vertex AI, we recommend using **Google Cloud Storage (`gs://`) URIs**. `kanoa` supports adding resources from GCS, which allows for more efficient handling of large files.

```python
# Example: Adding a resource from GCS
interpreter.kb.add_resource("gs://my-bucket/my-doc.pdf")
```

## Context Caching

Gemini supports **Context Caching**, which allows you to cache large prompts (like knowledge bases) to reduce costs and latency for subsequent requests.

* **Minimum Size**: Caching is typically effective for contexts larger than ~2,048 tokens.
* **TTL**: You can configure the Time-To-Live (TTL) for the cache.
* **Cost Savings**: Cached input tokens are significantly cheaper than standard input tokens.

See the [Gemini Context Caching Demo](../../examples/gemini_context_caching_demo.ipynb) for a working example.
