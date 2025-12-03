# Getting Started with Gemini

This guide will help you get started with kanoa using Google's Gemini models.

## Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)

## Step 1: Get Your API Key

Visit [Google AI Studio](https://aistudio.google.com/apikey) and:

- Sign in with your Google account
- Click "Create API Key" to generate a new key
- Copy the API key (you'll need it in the next step)

## Step 2: Configure Authentication

The recommended approach is to store your API key in `~/.config/kanoa/.env`:

```bash
mkdir -p ~/.config/kanoa
echo "GOOGLE_API_KEY=your-api-key-here" > ~/.config/kanoa/.env
```

Alternatively, you can set it as an environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

⚠️ **Security Note**: Never commit API keys to version control. kanoa includes `detect-secrets` in pre-commit hooks for defense-in-depth.

## Step 3: Your First Interpretation

```python
import numpy as np
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# Create some sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("Sample Data")
plt.xlabel("Time")
plt.ylabel("Amplitude")

# Initialize the interpreter
interpreter = AnalyticsInterpreter(backend='gemini-3')

# Interpret the plot
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing a time series signal",
    focus="What pattern does this data show?"
)

print(result.text)
print(f"\nCost: ${result.usage.total_cost:.4f}")
```

## Next Steps

- **Learn about Knowledge Bases**: See [Knowledge Bases Guide](knowledge_bases.md) to ground your analysis in project documentation
- **Explore Advanced Features**: Check the [Gemini Backend Reference](../backends/gemini.md) for context caching, Vertex AI integration, and more
- **Understand Cost Management**: Read the [Cost Management Guide](cost_management.md) to optimize your spending
- **Authentication Options**: See the [Authentication Guide](authentication.md) for advanced options like Application Default Credentials (ADC)

## Troubleshooting

### "API key not found" error

Make sure your API key is properly configured in `~/.config/kanoa/.env` or as an environment variable.

### "Quota exceeded" error

Check your [Google AI Studio quota](https://aistudio.google.com/quota) and consider using Vertex AI for production workloads.
