# kanoa

> **In-notebook AI interpretation of data science outputs, grounded in your project's knowledge base.**

[![Tests](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml/badge.svg)](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml)
[![Docs](https://img.shields.io/badge/docs-kanoa.docs.lhzn.io-blue)](https://kanoa.docs.lhzn.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Companion: kanoa-mlops](https://img.shields.io/badge/companion-kanoa--mlops-purple)](https://github.com/lhzn-io/kanoa-mlops)

`kanoa` brings the power of a dedicated AI research assistant directly into your Python workflows — whether in Jupyter notebooks, Streamlit apps, or automated scripts. It programmatically interprets visualizations, tables, and results using multimodal LLMs (Molmo, Gemini, Claude, OpenAI), grounded in your project's documentation and literature.

## Supported Backends

| Backend | Best For | Getting Started |
| :--- | :--- | :--- |
| `vllm` | Local inference with [Molmo](https://molmo.allenai.org/), Gemma 3, Olmo 3 | [Guide](./docs/source/user_guide/getting_started_local.md) |
| `gemini` | Free tier, native PDF support, Vertex AI RAG Engine | [Guide](./docs/source/user_guide/getting_started_gemini.md) |
| `claude` | Strong reasoning, vision support | [Guide](./docs/source/user_guide/getting_started_claude.md) |
| `openai` | GPT models, Azure OpenAI | [Guide](./docs/source/user_guide/backends.md#openai) |

For detailed backend comparison, see [Backends Overview](./docs/source/user_guide/backends.md).

## Features

- **Multi-Backend Support**: Seamlessly switch between vLLM (local), Gemini, Claude, and OpenAI.
- **Real-time Streaming**: Get immediate feedback with streaming responses.
- **Enterprise Grounding**: Native integration with **Vertex AI RAG Engine** for scalable, secure knowledge retrieval from thousands of documents.
- **Native Vision**: Uses multimodal capabilities to "see" complex plots and diagrams.
- **Cost Optimized**: Intelligent context caching and token usage tracking.
- **Knowledge Base**: Support for text (Markdown), PDF, and managed RAG knowledge bases.
- **Notebook-Native Logging**: see the [Logging Guide](./docs/source/user_guide/logging.md).

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

# 2. Ask kanoa to debug
interpreter = AnalyticsInterpreter(backend="gemini")
# Returns a stream by default
iterator = interpreter.interpret(
    fig=plt.gcf(),
    context="Simulating a projectile launch. Something looks wrong.",
    focus="Identify the physics error in the trajectory.",
)

# Consume the stream
for chunk in iterator:
    if chunk.type == "text":
        print(chunk.content, end="")
```

`kanoa`'s response:
> "The plot shows a linear relationship between height and time..."

### Using Claude

```python
# Ensure ANTHROPIC_API_KEY is set
interpreter = AnalyticsInterpreter(backend='claude')

# Use stream=False for blocking behavior (returns legacy result object)
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing environmental data for climate trends",
    focus="Explain any regime changes in the data.",
    stream=False
)
print(result.text)
```

### Using a Knowledge Base

```python
# Point to a directory of Markdown or PDF files
interpreter = AnalyticsInterpreter(
    backend='gemini',
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
[Molmo](https://molmo.allenai.org/) from AI2 and Google's Gemma 3 12B — fully-open multimodal models.
See `kanoa-mlops` for our local hosting setup.

```python
# Molmo 7B (recommended for vision - 31 tok/s avg, 3x faster than Gemma)
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='http://localhost:8000/v1',
    model='allenai/Molmo-7B-D-0924'
)

# Gemma 3 12B (recommended for text reasoning - 10.3 tok/s avg)
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='http://localhost:8000/v1',
    model='google/gemma-3-12b-it'
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing aquaculture sensor data",
    focus="Identify drivers of dissolved oxygen levels"
)
```

## Local & Edge Deployment

Run state-of-the-art open weights models locally using our companion library, [`kanoa-mlops`](https://github.com/lhzn-io/kanoa-mlops).

- **Privacy First**: Your data never leaves your machine.
- **Models**: Support for **Gemma 3**, **Molmo**, and **Olmo 3**.
- **Performance**: Optimized for consumer hardware (RTX 4090/5080) and edge devices (NVIDIA Jetson Thor).

### Benchmarks (NVIDIA RTX 5080)

| Model | Task | Speed |
| :--- | :--- | :--- |
| **Molmo-7B** | Complex Plot Interpretation | **92.8 tokens/sec** |
| **Molmo-7B** | Data Interpretation | **59.5 tokens/sec** |

### Benchmarks (NVIDIA Jetson Thor)

| Model | Task | Speed |
| :--- | :--- | :--- |
| **Molmo-7B** | Complex Plot Interpretation | **9.6 tokens/sec** |
| **Molmo-7B** | Data Interpretation | **9.5 tokens/sec** |
| **Gemma 3 12B** | Vision (Chart Analysis) | **4.3 tokens/sec** |
| **Gemma 3 12B** | Code Generation | **4.4 tokens/sec** |

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

## Pricing Configuration

`kanoa` includes up-to-date pricing for all supported models. You can override these values locally without waiting for a package update:

1. Create `~/.config/kanoa/pricing.json`
2. Add your custom pricing (merges with defaults):

```json
{
  "gemini": {
    "gemini-3-pro-preview": {
      "input_price": 2.00,
      "output_price": 12.00
    }
  },
  "claude": {
    "claude-opus-4-5-20251101": {
      "input_price": 5.00,
      "output_price": 25.00
    }
  }
}
```

Pricing sources:

- **Gemini**: [ai.google.dev/pricing](https://ai.google.dev/pricing)
- **Claude**: [anthropic.com/pricing](https://www.anthropic.com/pricing)
- **OpenAI**: [openai.com/api/pricing](https://openai.com/api/pricing)

## Documentation

📖 **[Full documentation](https://kanoa.docs.lhzn.io)** — User guides, API reference, and examples.

<details>
<summary>Building docs locally</summary>

```bash
cd docs
pip install -r requirements-docs.txt
make html
```

Then open `docs/build/html/index.html` in your browser.

</details>

## License

Copyright 2025 Long Horizon Observatory

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.
