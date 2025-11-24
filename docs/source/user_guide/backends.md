# Backends

kanoa supports multiple AI backends, each with different strengths and use cases.

## Gemini (`gemini-3`)

**Best for**: PDF knowledge bases, large context windows, cost optimization

### Features

- **Native PDF Support**: Upload PDFs directly, Gemini "sees" figures and tables
- **2M Token Context**: Massive context window (Gemini 3 Pro) for large knowledge bases
- **Context Caching**: Reuse cached content to reduce costs
- **Multimodal**: Images, PDFs, text, and more

### Authentication

```bash
# Option 1: API Key
export GOOGLE_API_KEY="your-api-key"

# Option 2: Application Default Credentials (ADC)
gcloud auth application-default login
```

### Usage

```python
from kanoa import AnalyticsInterpreter

# With API key
interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    api_key='your-api-key'
)

# With ADC (Vertex AI)
interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    project='your-project-id',
    location='us-central1'
)
```

### Pricing

- Input: $2.00 per 1M tokens (<200K context)
- Output: $12.00 per 1M tokens
- Cached: $0.20 per 1M tokens

## Claude (`claude`)

**Best for**: Strong reasoning, text-heavy analysis (Claude Sonnet 4.5)

### Features

- **Vision Support**: Interprets images (but not PDFs directly)
- **Strong Reasoning**: Excellent for complex analytical tasks
- **200K Context**: Large context window for text knowledge bases

### Authentication

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Usage

```python
interpreter = AnalyticsInterpreter(
    backend='claude',
    api_key='your-api-key'
)
```

### Pricing

- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

## Molmo (`molmo`)

**Best for**: Privacy-sensitive data, local inference

### Status

⚠️ **Experimental**: Stub implementation, not yet functional.

### Planned Features

- Local inference (no API calls)
- GPU acceleration
- Text knowledge base support
