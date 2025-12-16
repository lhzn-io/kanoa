# Getting Started with OpenAI

Use kanoa with OpenAI's GPT models or Azure OpenAI deployments.

## OpenAI API

### Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)
- OpenAI API key

### Step 1: Get Your API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key

### Step 2: Configure Authentication

#### Option A: Configuration File (Recommended)

Store your API key in `~/.config/kanoa/.env`:

```bash
mkdir -p ~/.config/kanoa
echo "OPENAI_API_KEY=your-api-key-here" >> ~/.config/kanoa/.env
```

#### Option B: Environment Variable

```bash
export OPENAI_API_KEY="your-api-key-here"  # pragma: allowlist secret
```

### Step 3: Use OpenAI Models

```python
import matplotlib.pyplot as plt
import numpy as np
from kanoa import AnalyticsInterpreter

# Create sample data
x = np.linspace(0, 10, 100)
y = np.sin(x) * np.exp(-x/10)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("Damped Sine Wave")
plt.xlabel("Time")
plt.ylabel("Amplitude")

# Use OpenAI GPT models
interpreter = AnalyticsInterpreter(
    backend='openai',
    model='gpt-4o'  # or 'gpt-4-turbo', 'gpt-3.5-turbo'
)

# Interpret output (streaming by default, disable for single result)
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing environmental data",
    focus="Identify key trends",
    stream=False
)

print(result.text)
print(f"\nCost: ${result.usage.total_cost:.4f}")
```

## Azure OpenAI

For Azure OpenAI deployments, provide your Azure endpoint and credentials:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='https://your-resource.openai.azure.com/openai/deployments/your-deployment',
    api_key='your-azure-key',  # pragma: allowlist secret
    api_version='2024-02-01'  # Azure API version
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Business metrics",
    focus="Summarize trends",
    stream=False
)
```

### Azure Configuration

You can also store Azure credentials in your config file:

```bash
# ~/.config/kanoa/.env
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

Then use:

```python
interpreter = AnalyticsInterpreter(backend='openai')
```

## Model Selection

### Recommended Models

- **`gpt-4o`**: Latest and most capable multimodal model
- **`gpt-4-turbo`**: Fast, high-quality responses
- **`gpt-3.5-turbo`**: Cost-effective for simpler tasks

See [OpenAI Backend Reference](../backends/openai.md) for detailed model information.

## Next Steps

- **Cost Management**: Learn about [Cost Management](cost_management.md)
- **Knowledge Bases**: Explore [Knowledge Bases Guide](knowledge_bases.md)
- **Backend Details**: Check [OpenAI Backend Reference](../backends/openai.md)

## Troubleshooting

### Authentication failed

Verify your API key is set correctly:

```python
import os
print(os.getenv('OPENAI_API_KEY'))  # Should show your key
```

### Rate limit errors

- Reduce request frequency
- Upgrade your OpenAI account tier
- See [OpenAI rate limits documentation](https://platform.openai.com/docs/guides/rate-limits)

### Model not found

Ensure the model name matches OpenAI's current offerings. Check [OpenAI models documentation](https://platform.openai.com/docs/models).
