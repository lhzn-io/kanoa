# kanoa

> **In-notebook AI interpretation of data science outputs, grounded in your project's knowledge base.**

[![Tests](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml/badge.svg)](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

`kanoa` brings the power of a dedicated AI research assistant directly into your Python workflows — whether in Jupyter notebooks, Streamlit apps, or automated scripts. It programmatically interprets visualizations, tables, and results using multimodal LLMs (Gemini, Claude, OpenAI, Molmo), grounded in your project's documentation and literature.

## Supported Backends

| Backend | Best For | Getting Started |
| :--- | :--- | :--- |
| `local` | Local inference with [Molmo](https://molmo.allenai.org/), Gemma 3 via vLLM | [Guide](./docs/source/user_guide/getting_started_vllm.md) |
| `gemini` | Free tier, native PDF support, 1M context, caching | [Guide](./docs/source/user_guide/getting_started_gemini.md) |
| `claude` | Strong reasoning, vision support | [Guide](./docs/source/user_guide/getting_started_claude.md) |
| `openai` | GPT models, Azure OpenAI | [Guide](./docs/source/user_guide/backends.md#openai) |

For detailed backend comparison, see [Backends Overview](./docs/source/user_guide/backends.md).

## Features

- **Multi-Backend Support**: Seamlessly switch between Gemini, Claude, and OpenAI (including local vLLM).
- **Provider-Native Grounding**: Offloads knowledge retrieval to best-in-breed provider solutions.
- **Native Vision**: Uses multimodal capabilities to "see" complex plots and diagrams.
- **Cost Optimized**: Intelligent context caching and token usage tracking.
- **Knowledge Base**: Support for text (Markdown) and PDF knowledge bases.
- **Notebook-Native Logging**: see the [Logging Guide](./docs/source/user_guide/logging.md).

## Installation

`kanoa` is modular — install only the backends you need:

```bash
# Local inference (vLLM — Molmo, Gemma 3)
pip install kanoa[local]

# Google Gemini (free tier available)
pip install kanoa[gemini]

# Anthropic Claude
pip install kanoa[claude]

# OpenAI API (GPT models, Azure OpenAI)
pip install kanoa[openai]

# Everything
pip install kanoa[all]
```

<details>
<summary>Development installation</summary>

```bash
git clone https://github.com/lhzn-io/kanoa.git
cd kanoa
pip install -e ".[dev]"
```

</details>

## Quick Start

Check out [2 Minutes to kanoa](./examples/2_minutes_to_kanoa.ipynb) for a hands-on introduction.

For a comprehensive feature overview, see the [detailed quickstart](./examples/quickstart_10min.ipynb).

### Basic Usage: AI-assisted Debugging with Visual Interpretation

In this example, we use `kanoa` to identify a bug in a physics simulation.

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

`kanoa`'s response:
> "The plot shows a linear relationship between height and time, which indicates constant velocity. A projectile under gravity should follow a parabolic path ($y = v_0t - \frac{1}{2}gt^2$). The code is likely missing the $t^2$ term in the gravity component."

### Using Claude

```python
# Ensure ANTHROPIC_API_KEY is set
interpreter = AnalyticsInterpreter(backend='claude')

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing environmental data for climate trends",
    focus="Explain any regime changes in the data."
)
print(result.text)
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
    context="Analyzing marine biologger data from a whale shark deployment",
    focus="Compare diving behavior with Braun et al. 2025 findings."
)
print(result.text)
```

### Local Inference with vLLM

Connect to any model hosted via vLLM's OpenAI-compatible API. We've tested with
[Molmo](https://molmo.allenai.org/) from AI2 — a fully-open multimodal model.
Gemma 3 support coming soon. See `kanoa-mlops` for our local hosting setup.

```python
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='http://localhost:8000/v1',
    model='allenai/Molmo-7B-D-0924'
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing aquaculture sensor data",
    focus="Identify drivers of dissolved oxygen levels"
)
```

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

Copyright 2025 Long Horizon Observatory

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.
