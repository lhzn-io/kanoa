# kanoa

> **In-notebook AI interpretation of data science outputs, grounded in your project's knowledge base.**

[![Tests](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml/badge.svg)](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**kanoa** brings the power of a dedicated AI research assistant directly into your **Python workflows—whether in Jupyter notebooks, Streamlit apps, or automated scripts**. It programmatically interprets visualizations, tables, and results using multimodal LLMs (Gemini, Claude, OpenAI, Molmo), grounded in your project's documentation and literature. It is designed to be dropped into any data science project to provide instant, context-aware analysis.

## Features

- **Multi-Backend Support**: Seamlessly switch between Gemini, Claude, and OpenAI (including local vLLM).
- **Provider-Native Grounding**: Offloads knowledge retrieval to best-in-breed provider solutions.
- **Native Vision**: Uses multimodal capabilities to "see" complex plots and diagrams.
- **Cost Optimized**: Intelligent context caching and token usage tracking.
- **Knowledge Base**: Support for text (Markdown) and PDF knowledge bases.

## Installation

```bash
pip install kanoa
```

Or for development:

```bash
git clone https://github.com/lhzn-io/kanoa.git
cd kanoa
pip install -e .
```

## Quick Start

Check out [10 Minutes to kanoa](./examples/quickstart_10min.ipynb) for a comprehensive introduction, including local inference with Molmo and Gemma 3.

### Basic Usage: Debugging with Vision

In this example, we use **kanoa** to identify a bug in a physics simulation.

```python
import numpy as np
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# 1. Simulate a projectile (with a bug!)
t = np.linspace(0, 10, 100)
v0 = 50
g = 9.8
# BUG: Missing t**2 in the gravity term (should be 0.5 * g * t**2)
y = v0 * t - 0.5 * g * t

plt.figure(figsize=(10, 6))
plt.plot(t, y)
plt.title("Projectile Trajectory")

# 2. Ask Kanoa to debug
interpreter = AnalyticsInterpreter(backend="gemini-3")
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Simulating a projectile launch. Something looks wrong.",
    focus="Identify the physics error in the trajectory."
)
print(result.text)
```

**kanoa's response:**
> "The plot shows a linear relationship between height and time, which indicates constant velocity. A projectile under gravity should follow a parabolic path ($y = v_0t - \frac{1}{2}gt^2$). The code is likely missing the $t^2$ term in the gravity component."

### Using Claude

```python
# Ensure ANTHROPIC_API_KEY is set
interpreter = AnalyticsInterpreter(backend='claude')

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Sales analysis"
)
```

### Using a Knowledge Base

```python
# Point to a directory of Markdown or PDF files
interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    kb_path='./docs/literature',
    kb_type='auto'  # Detects if PDFs are present
)

# The interpreter will now use the knowledge base to ground its analysis
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Compare with Braun et al. 2025 results"
)
```

### Local Inference (vLLM / Gemma 3)

Use `kanoa-mlops` to host local models like Gemma 3 or Molmo:

```python
# Connect to local vLLM server
# For setup instructions, see: docs/source/user_guide/getting_started_vllm.md
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='http://localhost:8000/v1',
    model='allenai/Molmo-7B-D-0924'
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Local analysis"
)
```

## Supported Backends

| Backend | Key Features | Best For |
| :--- | :--- | :--- |
| `gemini-3` | Native PDF support, 1M context, caching | Complex analysis with PDF references |
| `claude` | Strong reasoning, vision support | General analysis, text-heavy KBs |
| `openai` | Generic OpenAI API support (GPT-5.1, vLLM) | Local inference (Molmo,Gemma 3), Azure OpenAI |

## Getting Started

kanoa requires API keys for cloud backends. Choose your backend and follow the getting started guide:

- **[Getting Started with Gemini](./docs/source/user_guide/getting_started_gemini.md)** - Google's Gemini models (recommended for PDF knowledge bases)
- **[Getting Started with Claude](./docs/source/user_guide/getting_started_claude.md)** - Anthropic's Claude models (excellent reasoning)
- **[Getting Started with vLLM](./docs/source/user_guide/getting_started_vllm.md)** - Local inference or OpenAI API

Each guide includes:

- API key setup instructions
- Basic usage examples
- Links to detailed backend references

**For advanced configuration**, see:

- [Authentication Guide](./docs/source/user_guide/authentication.md) - Security best practices, ADC, and more
- [Backends Overview](./docs/source/user_guide/backends.md) - Detailed comparison of all backends

## Documentation

Full API documentation is available and built using Sphinx:

```bash
cd docs
pip install -r requirements-docs.txt
make html
```

Then open `docs/build/html/index.html` in your browser.

The API reference is auto-generated from docstrings in the source code.

## License

MIT © 2025 Long Horizon Observatory
