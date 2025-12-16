# Quick Start Guide

## Installation

Install kanoa via pip:

```bash
pip install kanoa
```

For development:

```bash
git clone https://github.com/lhzn-io/kanoa.git
cd kanoa
pip install -e ".[dev]"
```

## Authentication

### Local Development

Use Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

Or set API keys as environment variables:

```bash
export GOOGLE_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"
```

### Production/CI

Use Service Accounts with Workload Identity Federation (recommended) or Service Account keys.

## Basic Usage

### Interpreting a Figure

```python
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# Create a plot
plt.plot([1, 2, 3], [1, 4, 9])
plt.title("Growth Curve")

# Initialize interpreter (defaults to Gemini 3 Pro)
interpreter = AnalyticsInterpreter()

# Interpret (blocking mode for simple results)
result = interpreter.interpret(
    image=plt,
    context="Water quality analysis",
    focus="Identify any concerning trends",
    stream=False
)

print(result.text)
```

### Using Claude Sonnet 4.5

```python
interpreter = AnalyticsInterpreter(backend='claude')
result = interpreter.interpret(fig=plt.gcf(), stream=False)
```

### With a Knowledge Base

```python
# Point to a directory of Markdown or PDF files
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs/literature'  # Auto-detects all file types
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Compare with Smith et al. 2023",
    stream=False
)
```

### Interpreting Data

```python
import pandas as pd

df = pd.DataFrame({
    'dissolved_oxygen': [6.5, 6.8, 7.2, 7.0],
    'site': ['Site A', 'Site B', 'Site C', 'Site D']
})

result = interpreter.interpret(
    data=df,
    context="Water quality monitoring report",
    focus="Summarize the findings",
    stream=False
)

print(result.text)
```

### Streaming (Default)

By default, `kanoa` streams responses token-by-token. This is useful for real-time feedback.

```python
# Returns an iterator of chunks
iterator = interpreter.interpret(
    fig=plt.gcf(),
    context="Detailed analysis"
)

print("Analysis:", end=" ")
for chunk in iterator:
    if chunk.type == "text":
        print(chunk.content, end="", flush=True)
```

## Cost Tracking

```python
# Get cost summary
summary = interpreter.get_cost_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
print(f"Total tokens: {summary['total_tokens']}")
```

## Next Steps

- **[Streaming Guide](user_guide/streaming.md)**: Learn more about real-time responses and chunk types.
- **[Knowledge Bases](user_guide/knowledge_bases.md)**: Ground your analysis in your project's documentation.
- **[Backends](user_guide/backends.md)**: Switch between Gemini, Claude, OpenAI, and local models.
