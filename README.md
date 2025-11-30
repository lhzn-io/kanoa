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

Check out [10 Minutes to kanoa](./examples/quickstart_10min.ipynb) for a comprehensive introduction, including local inference with Gemma 3.

### Basic Usage

```python
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# 1. Create your plot
plt.plot([1, 2, 3], [1, 4, 9])
plt.title("Growth Curve")

# 2. Initialize Interpreter (defaults to Gemini)
# Ensure GOOGLE_API_KEY is set in your environment
interpreter = AnalyticsInterpreter(backend='gemini-3')

# 3. Interpret it
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Bacterial growth experiment",
    focus="Exponential phase"
)

# 4. View results (auto-displays in Jupyter)
print(result.text)
```

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
    context="Compare with Smith et al. 2023 results"
)
```

### Local Inference (vLLM / Gemma 3)

Use `kanoa-mlops` to host local models like Gemma 3 or Molmo:

```python
# Connect to local vLLM server (see kanoa-mlops repo)
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='http://localhost:8000/v1',
    model='google/gemma-3-12b-it'
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
| `openai` | Generic OpenAI support (GPT-5.1, vLLM) | Local inference (Gemma 3), Azure OpenAI |

## API Keys

kanoa requires API keys for cloud backends. **Recommended**: Store in `~/.config/kanoa/.env`:

```bash
mkdir -p ~/.config/kanoa
echo "GOOGLE_API_KEY=your-key" > ~/.config/kanoa/.env
echo "ANTHROPIC_API_KEY=your-key" >> ~/.config/kanoa/.env
```

⚠️ **Security Note**: API keys generate costs. We recommend `keeping secrets outside of your kanoa-dev workspace,
and we include detect-secrets in our pre-commit hooks for defense-in-depth.

**For detailed setup instructions**, see:

- [Authentication Guide](./docs/source/user_guide/authentication.md) - Complete setup, security best practices
- [Get Gemini API Key](https://aistudio.google.com/apikey)
- [Get Claude API Key](https://console.anthropic.com/)

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
