# kanoa 

> **AI-powered interpretation of data science outputs with multi-backend support.**

[![Tests](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml/badge.svg)](https://github.com/lhzn-io/kanoa/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**kanoa** is a standalone Python package that programmatically interprets matplotlib figures, DataFrames, and statistical summaries using state-of-the-art AI models. It is designed to be dropped into any data science project to provide instant, context-aware analysis.

## Features 🚀

- **Multi-Backend Support**: Seamlessly switch between Gemini 3.0 Pro (native PDF/vision), Claude Sonnet 4.5, and remote & local Molmo models.
- **Knowledge Base Grounding**: Automatically load project documentation (Markdown) or academic papers (PDFs) to ground interpretations in domain-specific facts.
- **Native Vision**: Uses Gemini's native multimodal capabilities to "see" complex plots and diagrams without OCR.
- **Cost Optimized**: Intelligent context caching and token usage tracking to keep costs low (<$0.05/run).
- **Privacy First**: Support for local inference using Molmo for sensitive data.

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
