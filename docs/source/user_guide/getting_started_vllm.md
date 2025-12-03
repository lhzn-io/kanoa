# Getting Started with vLLM and OpenAI

This guide covers two scenarios:

1. **Local inference** with vLLM (via `kanoa-mlops`)
2. **OpenAI API** (GPT models or Azure OpenAI)

## Option 1: Local Inference with vLLM

Running models locally gives you full control, privacy, and zero API costs. The `kanoa-mlops` repository provides tools to run models like Gemma 3 and Molmo on your local GPU.

### Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)
- NVIDIA GPU with at least 12GB VRAM (for Gemma 3)
- kanoa-mlops repository cloned

### Step 1: Set Up vLLM Server

Clone and set up the `kanoa-mlops` repository:

```bash
git clone https://github.com/lhzn-io/kanoa-mlops.git
cd kanoa-mlops
# Follow setup instructions in the repository README
```

Then start the vLLM server with your chosen model:

```bash
# Example: Running Gemma 3 12B
vllm serve google/gemma-3-12b-it \
    --port 8000 \
    --max-model-len 4096
```

For detailed setup instructions, see the [kanoa-mlops repository](https://github.com/lhzn-io/kanoa-mlops).

### Step 2: Connect kanoa to vLLM

```python
import numpy as np
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# Create some sample data
x = np.linspace(0, 10, 100)
y = np.exp(-x/5) * np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("Damped Oscillation")
plt.xlabel("Time")
plt.ylabel("Amplitude")

# Connect to local vLLM server
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='http://localhost:8000/v1',
    model='google/gemma-3-12b-it'
)

# Interpret the plot
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Physics simulation results",
    focus="Describe the pattern and suggest what physical process this could represent"
)

print(result.text)
```

### Supported Local Models

- **Gemma 3 12B** (Google): Strong general-purpose text model
- **Molmo 7B** (Allen Institute): Multimodal model with vision capabilities
- **Llama 3.2** (Meta): Open source alternative
- **Mistral/Mixtral**: High performance for reasoning tasks

For setup instructions specific to each model, see the [vLLM Backend Reference](../backends/vllm.md).

---

## Option 2: OpenAI API

### Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)
- OpenAI API key

### Step 1: Get Your API Key

Visit [OpenAI Platform](https://platform.openai.com/api-keys) and:

- Sign in or create an account
- Click "Create new secret key"
- Copy the API key (you'll need it in the next step)

### Step 2: Configure Authentication

Store your API key in `~/.config/kanoa/.env`:

```bash
mkdir -p ~/.config/kanoa
echo "OPENAI_API_KEY=your-api-key-here" >> ~/.config/kanoa/.env
```

Or set it as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Step 3: Use OpenAI Models

```python
from kanoa import AnalyticsInterpreter

# Use with OpenAI GPT models
interpreter = AnalyticsInterpreter(backend='openai')

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Sales analysis",
    focus="Identify trends"
)

print(result.text)
print(f"\nCost: ${result.usage.total_cost:.4f}")
```

---

## Azure OpenAI

For Azure OpenAI deployments:

```python
interpreter = AnalyticsInterpreter(
    backend='openai',
    api_base='https://your-resource.openai.azure.com/openai/deployments/your-deployment',
    api_key='your-azure-key'
)
```

## Next Steps

- **Learn about Knowledge Bases**: See [Knowledge Bases Guide](knowledge_bases.md)
- **Explore vLLM Options**: Check the [vLLM Backend Reference](../backends/vllm.md)
- **Explore OpenAI Options**: Check the [OpenAI Backend Reference](../backends/openai.md)
- **Understand Cost Management**: Read the [Cost Management Guide](cost_management.md)

## Troubleshooting

### vLLM server connection failed

- Verify the server is running: `curl http://localhost:8000/health`
- Check that the port matches your configuration
- Ensure no firewall is blocking the connection

### Out of memory errors (vLLM)

Reduce `--max-model-len` or use a smaller model. See the [kanoa-mlops repository](https://github.com/lhzn-io/kanoa-mlops) for GPU memory requirements.
