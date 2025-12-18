# OpenAI Backend

The `openai` backend integrates with OpenAI's GPT models and Azure OpenAI deployments.

## Configuration

### OpenAI API

Set the `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY="sk-..."  # pragma: allowlist secret
```

Or store it in `~/.config/kanoa/.env`:

```bash
mkdir -p ~/.config/kanoa
echo "OPENAI_API_KEY=your-api-key-here" >> ~/.config/kanoa/.env
```

Initialize with:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend="openai",
    model="gpt-4o"  # or 'gpt-4-turbo', 'gpt-3.5-turbo'
)
```

### Azure OpenAI

For Azure OpenAI deployments:

```python
interpreter = AnalyticsInterpreter(
    backend="openai",
    api_base="https://your-resource.openai.azure.com/openai/deployments/your-deployment",
    api_key="your-azure-key",  # pragma: allowlist secret
    api_version="2024-02-01"
)
```

Or configure via environment variables:

```bash
# ~/.config/kanoa/.env
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

## Supported Models

### Recommended Models

- **`gpt-4o`**: Latest and most capable multimodal model
- **`gpt-4-turbo`**: Fast, high-quality responses with vision support
- **`gpt-4`**: Most capable for complex reasoning tasks
- **`gpt-3.5-turbo`**: Cost-effective for simpler tasks

All models support vision capabilities (can process matplotlib figures).

## Features

### Vision Capabilities

All GPT-4 models support multimodal inputs. kanoa automatically converts matplotlib figures to images and sends them to the model.

### Knowledge Base

The OpenAI backend supports both **Text** and **PDF** knowledge bases:

```python
# Text knowledge base
interpreter = interpreter.with_kb(kb_path="data/docs")  # Auto-detects file types

# PDF knowledge base
```

## Cost Tracking

kanoa automatically tracks token usage and costs for OpenAI models:

```python
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analysis",
    stream=False
)
print(f"Cost: ${result.usage.total_cost:.4f}")
print(f"Input tokens: {result.usage.prompt_tokens}")
print(f"Output tokens: {result.usage.completion_tokens}")
```

Pricing is based on current OpenAI API rates and updated regularly.

## Advanced Configuration

### Custom Parameters

```python
interpreter = AnalyticsInterpreter(
    backend="openai",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
    top_p=0.9
)
```

### Streaming Responses

```python
# Streaming is not yet supported in the current version
# Coming in a future release
```

## See Also

- [Getting Started with OpenAI](../user_guide/getting_started_openai.md)
- [Cost Management Guide](../user_guide/cost_management.md)
- [OpenAI API Documentation](https://platform.openai.com/docs)
