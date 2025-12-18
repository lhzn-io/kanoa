# Getting Started with Gemini

This guide will help you get started with kanoa using Google's Gemini models.

## Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)

## Free Tier Overview

Gemini offers a **free tier** that's perfect for learning and experimentation:

| Feature | Free Tier | Paid Tier |
| --------- | ----------- | ----------- |
| Input/Output tokens | **Free** | Pay-per-use |
| Rate limits | 500 requests/day | Higher limits |
| Context caching | ❌ | ✅ |
| Batch API | ❌ | ✅ |
| Data usage | Used to improve Google products | Not used for training |

⚠️ **Privacy Note**: On the free tier, your prompts and responses may be used to improve Google's products. For sensitive data, consider upgrading to the paid tier or using Vertex AI.

**Recommended models for the free tier**:

- `gemini-2.5-flash` — Fast, efficient, great for most use cases
- `gemini-2.0-flash` — Previous generation, still capable
- `gemini-2.5-pro` — Most capable, for complex analysis (also free!)

### Knowledge Base Limitations on Free Tier

The free tier has a **reduced context window** which limits knowledge base capabilities:

| Knowledge Base Type | Free Tier | Paid Tier (Gemini 3 Pro) |
| --------------------- | ----------- | -------------------------- |
| Text (Markdown) | ✅ Works well | ✅ Full support |
| PDF (multimodal) | ⚠️ Limited | ✅ Full support (1M+ tokens) |
| Context caching | ❌ Not available | ✅ ~67% cost savings |

For **serious knowledge-grounded analysis** (e.g., scientific papers, technical docs), the paid tier with context caching is surprisingly affordable:

**Real-world example** (8.5 MB PDF — WMO Climate Report):

| Operation | Cost |
| ----------- | ------ |
| Cache creation (first query) | $0.02 |
| Subsequent queries (cached) | < $0.01 each |
| Cache savings per query | ~$0.014 (67% reduction) |

See the [Context Caching Demo](../../../examples/gemini_context_caching_demo.ipynb) for a complete walkthrough.

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
interpreter = AnalyticsInterpreter(backend='gemini')

# Interpret (blocking mode for simple results)
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing weather data from sensor array",
    focus="Identify any temperature anomalies",
    stream=False
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
