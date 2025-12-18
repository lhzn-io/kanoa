# Getting Started with Claude

This guide will help you get started with kanoa using Anthropic's Claude models.

## Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)

## Step 1: Get Your API Key

Visit the [Anthropic Console](https://console.anthropic.com/) and:

- Sign in or create an account
- Navigate to "API Keys" in the dashboard
- Click "Create Key" to generate a new API key
- Copy the API key (you'll need it in the next step)

## Step 2: Configure Authentication

The recommended approach is to store your API key in `~/.config/kanoa/.env`:

```bash
mkdir -p ~/.config/kanoa
echo "ANTHROPIC_API_KEY=your-api-key-here" >> ~/.config/kanoa/.env
```

Alternatively, you can set it as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

⚠️ **Security Note**: Never commit API keys to version control. kanoa includes `detect-secrets` in pre-commit hooks for defense-in-depth.

## Step 3: Your First Interpretation

```python
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# Sample Data
sites = ['Site A', 'Site B', 'Site C', 'Site D']
dissolved_oxygen = [6.5, 6.8, 7.2, 7.0]

# Create Bar Chart
plt.figure(figsize=(10, 6))
plt.bar(sites, dissolved_oxygen)
plt.title("Dissolved Oxygen Levels")
plt.xlabel("Monitoring Sites")
plt.ylabel("DO (mg/L)")

# Initialize the interpreter with Claude
interpreter = AnalyticsInterpreter(backend='claude')

# Use kanoa to interpret output (using stream=False for single result)
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing environmental sensor data",
    focus="Identify any anomalies",
    stream=False
)

print(result.text)
print(f"\nCost: ${result.usage.total_cost:.4f}")
```

## Next Steps

- **Learn about Knowledge Bases**: See [Knowledge Bases Guide](knowledge_bases.md) to ground your analysis in project documentation
- **Explore Advanced Features**: Check the [Claude Backend Reference](../backends/claude.md) for detailed configuration options
- **Understand Cost Management**: Read the [Cost Management Guide](cost_management.md) to optimize your spending
- **Authentication Options**: See the [Authentication Guide](authentication.md) for more details

## Troubleshooting

### "API key not found" error

Make sure your API key is properly configured in `~/.config/kanoa/.env` or as an environment variable.

### "Rate limit exceeded" error

Claude has rate limits on API usage. Check your [Anthropic Console](https://console.anthropic.com/) for current limits and consider implementing rate limiting in your application.

## Why Choose Claude?

Claude excels at:

- **Strong reasoning**: Excellent for complex analytical tasks
- **Text-heavy analysis**: Great for interpreting detailed reports and documentation
- **Vision support**: Can interpret charts and visualizations (but not PDFs directly like Gemini)
