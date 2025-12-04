# Getting Started with Local Inference

Run models locally with full control, privacy, and zero API costs. The `kanoa-mlops` repository provides infrastructure to run models like Molmo and Gemma 3 on your local GPU.

## Prerequisites

- Python 3.11 or higher
- kanoa installed (`pip install kanoa`)
- NVIDIA GPU (see [hardware requirements](#hardware-requirements))
- kanoa-mlops repository cloned

## Quick Start

### Step 1: Set Up Infrastructure

Clone and set up the `kanoa-mlops` repository:

```bash
git clone https://github.com/lhzn-io/kanoa-mlops.git
cd kanoa-mlops

# Create environment
conda env create -f environment.yml
conda activate kanoa-mlops
```

### Step 2: Download and Start Model

```bash
# Download Molmo 7B (verified working)
./scripts/download-models.sh molmo-7b-d

# Start vLLM server
docker compose -f docker/vllm/docker-compose.molmo.yml up -d
```

The server will be available at `http://localhost:8000`.

### Step 3: Connect kanoa to Local Server

```python
import numpy as np
import matplotlib.pyplot as plt
from kanoa import AnalyticsInterpreter

# Create sample data
x = np.linspace(0, 10, 100)
y = np.exp(-x/5) * np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("Damped Oscillation")
plt.xlabel("Time")
plt.ylabel("Amplitude")

# Connect to local vLLM server
interpreter = AnalyticsInterpreter(
    backend='vllm',
    api_base='http://localhost:8000/v1',
    model='allenai/Molmo-7B-D-0924'
)

# Interpret the plot
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Physics simulation results",
    focus="Describe the pattern and suggest what physical process this could represent"
)

print(result.text)
```

## Hardware Requirements

### Minimum Requirements

- **GPU**: NVIDIA GPU with CUDA support
- **VRAM**: 12GB minimum (for 7B models with quantization)
- **Storage**: 20GB for model weights
- **RAM**: 16GB system RAM

### Tested Configurations

See [vLLM Backend Reference](../backends/vllm.md#tested-models) for the complete list of tested hardware configurations.

## Supported Models

For a comprehensive list of supported models (both tested and theoretical), see the [vLLM Backend Reference](../backends/vllm.md).

## Next Steps

- **Model Selection**: Check [vLLM Backend Reference](../backends/vllm.md) for model options
- **Infrastructure Details**: See [kanoa-mlops repository](https://github.com/lhzn-io/kanoa-mlops) for advanced setup
- **Knowledge Bases**: Learn about [Knowledge Bases Guide](knowledge_bases.md)
- **Cost Tracking**: Understand [Cost Management](cost_management.md) for local models

## Troubleshooting

### Server connection failed

Verify the server is running:

```bash
curl http://localhost:8000/health
```

Check Docker logs:

```bash
docker compose -f docker/vllm/docker-compose.molmo.yml logs -f
```

### Out of memory errors

- Use 4-bit quantization (default in provided Docker configs)
- Reduce `--max-model-len` parameter
- Try a smaller model (7B instead of 12B)
- See [kanoa-mlops hardware guide](https://github.com/lhzn-io/kanoa-mlops#hardware-testing-roadmap)

### GPU not detected

```bash
# Verify GPU detection
nvidia-smi

# For WSL2 users
# See kanoa-mlops/docs/source/wsl2-gpu-setup.md
```
