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

# Interpret
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Bacterial growth experiment",
    focus="Identify growth phase"
)

print(result.text)
```

### Using Claude Sonnet 4.5

```python
interpreter = AnalyticsInterpreter(backend='claude')
result = interpreter.interpret(fig=plt.gcf())
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
    context="Compare with Smith et al. 2023"
)
```

### Interpreting Data

```python
import pandas as pd

df = pd.DataFrame({
    'quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
    'revenue': [100, 120, 150, 140]
})

result = interpreter.interpret(
    data=df,
    context="Quarterly revenue report",
    focus="Identify trends"
)
```

## Cost Tracking

```python
# Get cost summary
summary = interpreter.get_cost_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
print(f"Total tokens: {summary['total_tokens']}")
```
