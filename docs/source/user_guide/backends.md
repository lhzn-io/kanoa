# Backends

kanoa supports multiple AI backends, each with different strengths and use cases.

## Gemini (`gemini`)

> For detailed documentation, see [Gemini Backend Reference](../backends/gemini.md).

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
    backend='gemini',
    api_key='your-api-key'
)

# With ADC (Vertex AI)
interpreter = AnalyticsInterpreter(
    backend='gemini',
    project='your-project-id',
    location='us-central1'
)
```

### Pricing

| Token Type | Price (per 1M tokens) | Notes |
| --- | --- | --- |
| Standard Input | $2.00 | For context <200K tokens |
| Cached Input | $0.50 | 75% savings |
| Cache Storage | $0.20/hour | Per million cached tokens |
| Output | $12.00 | All output tokens |

#### Real-World Cost Study

Using an **8.5 MB PDF** (WMO State of the Climate 2025 Report, ~9,500 tokens):

| Operation | Cost | Notes |
| --- | --- | --- |
| First query (cache creation) | $0.02 | Full token cost |
| Subsequent queries (cached) | < $0.01 | 67% savings |
| 10-query session | ~$0.11 | vs. $0.21 without caching |

**Bottom line**: For a typical research session analyzing a scientific paper:

- **Free tier**: Works for simple text analysis, but no caching or PDF support
- **Paid tier**: ~$0.02 to cache a paper, then pennies per question

See the [Context Caching Demo](../../../examples/gemini_context_caching_demo.ipynb) for a complete walkthrough.

### Context Caching

Gemini supports **explicit context caching** for knowledge bases, providing significant
cost savings when making multiple queries against the same content.

#### How It Works

1. **First Query**: kanoa uploads your KB and creates a cache (billed at standard rate)
2. **Subsequent Queries**: Cached content is reused (billed at $0.50/1M vs $2.00/1M)
3. **Content Hashing**: kanoa detects KB changes and refreshes the cache automatically

#### Enabling Context Caching

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    cache_ttl=3600,  # Cache valid for 1 hour (default)
)
```

#### Usage Tracking

The `UsageInfo` object includes caching metrics:

```python
result = interpreter.interpret(
    prompt="Analyze this data",
    stream=False
)

print(f"Cached tokens: {result.usage.cached_tokens}")
print(f"Cache savings: ${result.usage.cache_savings:.4f}")
```

#### Minimum Token Requirements

Context caching requires a minimum number of tokens to be beneficial:

| Model | Minimum Tokens |
| --- | --- |
| gemini-2.5-flash | 1,024 |
| gemini-3-pro-preview | 2,048 |
| gemini-2.5-pro | 4,096 |

#### Cache Management

You can manage caches programmatically or via the CLI:

```python
# Clear cache manually (e.g., after updating KB files)
interpreter.clear_cache()

# Cache is also cleared automatically when KB content hash changes
```

For CLI usage:

```bash
python -m kanoa.tools.gemini_cache list
```

#### Best Practices

- ✅ Use for interactive sessions with multiple queries
- ✅ Set `cache_ttl` based on your session length
- ✅ Monitor `cache_savings` to track ROI
- ❌ Avoid for single-shot queries (cache creation overhead)
- ❌ Avoid for KBs < 2,048 tokens (no caching benefit)

## Claude (`claude`)

> For detailed documentation, see [Claude Backend Reference](../backends/claude.md).

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

## vLLM (`vllm`)

> For detailed documentation, see [vLLM Backend Reference](../backends/vllm.md).

**Best for**: Local inference with open-source models (Molmo, Gemma 3)

### Features

- **Fully Open Source**: Run inference locally with no API costs
- **Privacy**: Your data never leaves your machine
- **Vision Support**: Supports multimodal models like Molmo
- **GPU Acceleration**: Optimized for NVIDIA GPUs via vLLM

### Usage

```python
from kanoa import AnalyticsInterpreter

# Local vLLM (Molmo 7B)
interpreter = AnalyticsInterpreter(
    backend='vllm',
    api_base='http://localhost:8000/v1',
    model='allenai/Molmo-7B-D-0924'
)

# Local vLLM (Gemma 3 12B)
interpreter = AnalyticsInterpreter(
    backend='vllm',
    api_base='http://localhost:8000/v1',
    model='google/gemma-3-12b-it'
)
```

See the [Local Inference Guide](getting_started_local.md) for setup instructions.

## OpenAI (`openai`)

> For detailed documentation, see [OpenAI Backend Reference](../backends/openai.md).

**Best for**: GPT models, Azure OpenAI

### Features

- **GPT Models**: Access to GPT-4, GPT-5.1, and future models
- **Azure OpenAI**: Enterprise deployment via Azure
- **Vision Support**: Supports image inputs with compatible models

### Usage

#### OpenAI (GPT-5.1)

```python
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_key='sk-...'
)
```

#### Azure OpenAI

```python
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='https://your-resource.openai.azure.com/...',
    api_key='your-azure-key'
)
```

---

## Enterprise Considerations

### Current: Google AI Studio (`google-genai`)

kanoa currently uses the `google-genai` SDK, which connects to Google AI Studio.
This is the recommended approach for most users:

- ✅ Simple API key authentication
- ✅ Application Default Credentials (ADC) support
- ✅ Low friction setup
- ✅ Full Gemini feature support (context caching, multimodal)

### Future: Vertex AI Backend

For enterprise users requiring advanced compliance and security features,
a dedicated Vertex AI backend is on the roadmap.

| Feature | Google AI (`google-genai`) | Vertex AI (roadmap) |
| --------- | --------------------------- | --------------------- |
| Auth | API key / ADC | Service account / ADC |
| VPC Service Controls | ❌ | ✅ |
| Audit Logs | ❌ | ✅ (Cloud Logging) |
| CMEK (Customer-Managed Keys) | ❌ | ✅ |
| Private Endpoints | ❌ | ✅ |
| Model Registry | Limited | Full access |
| SLA | Consumer | Enterprise |

**Interested in enterprise features?**
Open an issue on [GitHub](https://github.com/lhzn-io/kanoa/issues)
to discuss your requirements and help prioritize the Vertex AI backend.
