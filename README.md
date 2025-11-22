# kanoa

> **In-notebook AI interpretation of data science outputs, grounded in your project's knowledge base.**

[![Tests](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml/badge.svg)](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**kanoa** brings the power of a dedicated AI research assistant directly into your **Python workflows—whether in Jupyter notebooks, Streamlit apps, or automated scripts**. It programmatically interprets visualizations, tables, and results using multimodal LLMs (Gemini, Claude, OpenAI, Molmo), grounded in your project's documentation and literature. It is designed to be dropped into any data science project to provide instant, context-aware analysis.

## How it Works

1. **Run Code**: Generate a plot, table, or result in your notebook.
2. **Ask**: Pass the result to `kanoa` with a specific question.
3. **Ground**: The LLM consults your project's codebase, docs, and PDF knowledge base.
4. **Interpret**: Receive a rich Markdown interpretation with tables and diagrams, rendered directly in the notebook.

## Features

- **Multi-Backend Support**: Seamlessly switch between Gemini 3.0 (native PDF/vision), Claude Sonnet 4.5, OpenAI GPT-4o, and local Molmo models.
- **Provider-Native Grounding**: Offloads knowledge retrieval to best-in-breed provider solutions (Gemini Context Caching, OpenAI Vector Stores) for maximum efficiency and accuracy.
- **Native Vision**: Uses Gemini's native multimodal capabilities to "see" complex plots and diagrams without OCR.
- **Cost Optimized**: Intelligent context caching and token usage tracking to keep costs low (<$0.05/run).
- **Privacy First**: Support for local inference using Molmo for sensitive data.

## Roadmap

- **Streamlit Integration**: Reference implementation for building interactive research assistants.
- **Reference Manager Sync**: Connect to Zotero/Paperguide to auto-sync PDFs from your library.
- **BibTeX Automation**: Utilities to convert `.bib` files into a populated PDF knowledge base.

## Quick Start

```bash
pip install kanoa
```

```python
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# 1. Create your plot
plt.plot([1, 2, 3], [1, 4, 9])
plt.title("Growth Curve")

# 2. Interpret it
interpreter = AnalyticsInterpreter(backend='gemini-3')
result = interpreter.interpret(plt.gcf(), context="Bacterial growth experiment")

# 3. Get insights
print(result.text)
```

## Documentation

(forthcoming)

## Installation

```bash
git clone https://github.com/lhzn-io/kanoa.git
cd kanoa
pip install -e .
```

## License

MIT © 2025 Long Horizon Observatory
