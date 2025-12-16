# kanoa Documentation

Welcome to the **kanoa** documentation!

**kanoa** is an AI-powered analytics interpreter that brings multimodal LLM capabilities directly into your Python workflows.

```{toctree}
:maxdepth: 2
:caption: Contents:

quickstart
user_guide/index
backends/index
developer_guide/index
api
```

## Installation

```bash
pip install kanoa
```

## Quick Start

```python
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# Create a plot
plt.plot([1, 2, 3], [1, 4, 9])
plt.title("Growth Curve")

# Initialize interpreter
interpreter = AnalyticsInterpreter(backend='gemini')

# Interpret
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Water quality analysis",
    stream=False
)

print(result.text)
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
