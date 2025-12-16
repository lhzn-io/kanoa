# Getting Started with Local Inference

Run models locally with full control, privacy, and zero API costs. We recommend **Molmo 7B** for vision tasks (31 tok/s, 3x faster than Gemma) or **Gemma 3 12B** for text reasoning (10.3 tok/s, strong for code/JSON). The `kanoa-mlops` repository provides infrastructure for local hosting.

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

#### Option A: Gemma 3 12B (Recommended for 16GB VRAM)

```bash
# Start vLLM server (downloads model automatically)
vllm serve google/gemma-3-12b-it --port 8000
```

#### Option B: Molmo 7B (Best for vision tasks)

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

# Connect to local vLLM server (Gemma 3 12B)
interpreter = AnalyticsInterpreter(
    backend='openai',  # vLLM uses OpenAI-compatible API
    api_base='http://localhost:8000/v1',
    model='google/gemma-3-12b-it'  # Use whatever model you started
)

# Analyze
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyzing environmental sensor data",
    focus="Identify any anomalies in the time series",
    stream=False
)

print(result.text)
print(f"Tokens: {result.usage.total_tokens}, Cost: ${result.usage.cost:.4f}")
```

## Hardware Requirements

### Verified Working Configurations

| Model | VRAM Required | Hardware Tested | Avg Throughput |
|-------|---------------|-----------------|----------------|
| **Molmo 7B** | 12GB (4-bit) | NVIDIA RTX 5080 (16GB) | **31.1 tok/s** (±5.9) |
| **Gemma 3 12B** | 14GB (4-bit + FP8 KV) | NVIDIA RTX 5080 (16GB) | **10.3 tok/s** (±3.5) |
| **Gemma 3 4B** | 8GB (4-bit) | NVIDIA RTX 5080 (16GB) | 2.5 tok/s |

**Recommendations**:

- **Vision-focused**: Use **Molmo 7B** — it's **3x faster** than Gemma 3 12B (31 tok/s average)
- **Text reasoning/code**: Use **Gemma 3 12B** — better for structured outputs, multi-turn chat
- **Limited VRAM**: Use **Gemma 3 4B** — fits in 8GB but significantly slower

### Minimum Requirements

- **GPU**: NVIDIA GPU with CUDA support
- **VRAM**: 12GB minimum (for 7B models with 4-bit quantization)
- **Storage**: 20-30GB for model weights
- **RAM**: 16GB system RAM
- **PCIe**: 3.0 x4 or better (important for eGPU setups)

### Tested Configurations

See [vLLM Backend Reference](../backends/vllm.md#tested-models) for the complete list of tested hardware configurations.

## Supported Models

### Recommended Models (Verified)

**For 16GB VRAM:**

- ✅ **Molmo 7B** (`allenai/Molmo-7B-D-0924`) — Best for vision, 31 tok/s average, 3x faster than Gemma
- ✅ **Gemma 3 12B** (`google/gemma-3-12b-it`) — Best for text reasoning, 10.3 tok/s average

**For <16GB VRAM:**

- ✅ **Gemma 3 4B** (`google/gemma-3-4b-it`) — Fits in 8GB, slower but capable

### Performance Comparison

Based on 3-run benchmark (RTX 5080 16GB):

| Task Type | Gemma 3 4B | Gemma 3 12B | Molmo 7B | Best Model |
|-----------|------------|-------------|----------|------------|
| **Vision (photos)** | 1.0 tok/s | 2.2 ± 0.3 tok/s | **29.3 ± 5.8 tok/s** | **Molmo 7B (13x)** |
| **Vision (charts)** | 1.5 tok/s | 13.6 ± 1.0 tok/s | **32.7 ± 6.3 tok/s** | **Molmo 7B (2.4x)** |
| **Vision (data viz)** | ~1 tok/s | ~10 tok/s | **28.8 ± 8.8 tok/s** | **Molmo 7B (2.9x)** |
| **Basic chat** | 3.3 tok/s | **12.6 ± 1.4 tok/s** | Not tested | **Gemma 3 12B** |
| **Code generation** | 5.0 tok/s | **16.0 ± 2.9 tok/s** | Not tested | **Gemma 3 12B** |
| **Overall Average** | 2.5 tok/s | 10.3 ± 3.5 tok/s | **31.1 ± 5.9 tok/s** | **Molmo 7B (3x)** |

**Performance Notes**:

- **Molmo 7B dominates vision tasks** (29-33 tok/s) — 3x faster than Gemma 3 12B overall
- **Gemma 3 12B excels at text** reasoning, code, and structured outputs (12-25 tok/s)
- **Molmo has better stability** (19% CV) vs Gemma 3 12B (34% CV)
- Complex reasoning on Gemma may show higher latency due to KV cache pressure
- Monitor vLLM `/metrics` endpoint to track cache hits and GPU utilization

For a comprehensive list of models (including theoretical support), see the [vLLM Backend Reference](../backends/vllm.md).

## Next Steps

- **Model Selection**: Check [vLLM Backend Reference](../backends/vllm.md) for model options
- **Performance Monitoring**: See [kanoa-mlops GPU Monitoring](https://github.com/lhzn-io/kanoa-mlops/blob/main/docs/source/gpu-monitoring.md) for Prometheus and Grafana setup
- **Infrastructure Details**: See [kanoa-mlops repository](https://github.com/lhzn-io/kanoa-mlops) for advanced setup
- **Knowledge Bases**: Learn about [Knowledge Bases Guide](knowledge_bases.md)
- **Cost Tracking**: Understand [Cost Management](cost_management.md) for local models

## Troubleshooting

### Server connection failed

Verify the server is running:

```bash
# Check server health
curl http://localhost:8000/health

# List available models
curl http://localhost:8000/v1/models
```

Check logs:

```bash
# For direct vLLM process (Gemma 3)
ps aux | grep vllm

# For Docker (Molmo)
docker compose -f docker/vllm/docker-compose.molmo.yml logs -f
```

### Out of memory errors

If you hit VRAM limits:

```bash
# For Gemma 3 12B (reduce GPU memory allocation)
vllm serve google/gemma-3-12b-it --gpu-memory-utilization 0.85

# Or switch to 4B variant
vllm serve google/gemma-3-4b-it

# For Docker setups: use 4-bit quantization (default in configs)
# Reduce --max-model-len parameter in docker-compose.yml
```

See [kanoa-mlops hardware guide](https://github.com/lhzn-io/kanoa-mlops#hardware-testing-roadmap) for detailed memory optimization.

### GPU not detected

```bash
# Verify GPU detection
nvidia-smi

# For WSL2 users
# See kanoa-mlops/docs/source/wsl2-gpu-setup.md
```
