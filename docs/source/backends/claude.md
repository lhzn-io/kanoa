# Anthropic Claude Backend

The `claude` backend integrates with Anthropic's Claude models, known for their strong reasoning capabilities and large context windows.

## Configuration

To use the Claude backend, you need an Anthropic API key.

### Environment Variables

Set the `ANTHROPIC_API_KEY` environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # pragma: allowlist secret
```

### Initialization

Initialize the interpreter with `backend="claude"`:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend="claude",
    model="claude-sonnet-4-5-20250929"  # Optional: Specify model version
)
```

## Supported Models

`kanoa` supports the latest Claude 4.5 models:

* **Claude 4.5 Sonnet** (`claude-sonnet-4-5-20250929`): The default model. Balanced performance and cost.
* **Claude 4.5 Opus** (`claude-opus-4-5-20251101`): High-intelligence model for complex reasoning tasks.

## Features

### Vision Capabilities

Claude supports multimodal input, allowing `kanoa` to interpret matplotlib figures directly.

```python
import matplotlib.pyplot as plt

# Create a plot
plt.plot([1, 2, 3], [1, 4, 9])

# Interpret the figure
result = interpreter.interpret(fig=plt.gcf(), stream=False)
```

### Knowledge Base

The Claude backend supports **Text Knowledge Bases**. You can load text files or raw strings as context.

> **Note**: Unlike the Gemini backend, Claude does not currently support native PDF ingestion via `kanoa`. PDFs must be converted to text first or used with a text-based KB.

```python
# Load a text-based knowledge base
interpreter = interpreter.with_kb(kb_path="data/docs")  # Auto-detects file types
```

## Cost Tracking

`kanoa` tracks token usage and estimates costs based on current Anthropic pricing.

* **Input**: ~$3.00 / 1M tokens (Sonnet 4.5)
* **Output**: ~$15.00 / 1M tokens (Sonnet 4.5)

You can view the cost summary at any time:

```python
print(interpreter.get_cost_summary())
```
