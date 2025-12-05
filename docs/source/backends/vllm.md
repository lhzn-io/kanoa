# vLLM / Local Backend

The `vllm` backend allows `kanoa` to connect to locally hosted models or any OpenAI-compatible API endpoint. This is ideal for students, researchers, and organizations running their own inference infrastructure.

## Configuration

To use vLLM or a local model, point `kanoa` to your API endpoint.

### Basic Setup

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend="vllm",
    api_base="http://localhost:8000/v1",  # URL of your vLLM server
    model="allenai/Molmo-7B-D-0924",      # Model name served by vLLM
    api_key="EMPTY"                        # vLLM usually doesn't require a key  pragma: allowlist secret
)
```

## Supported Models

### Tested Models

These models have been verified working with specific hardware configurations:

| Model | Parameters | VRAM Required | Hardware Tested | Vision Support | Status |
|-------|------------|---------------|-----------------|----------------|--------|
| **Molmo 7B-D** (Allen AI) | 7B | 12GB (4-bit) | NVIDIA RTX 5080 (eGPU, 16GB) | ✓ | [✓] Verified |
| **Gemma 3 4B** (Google) | 4B | 8GB (4-bit) | NVIDIA RTX 5080 (eGPU, 16GB) | ✓ | [✓] Verified (2.5 tok/s) |
| **Gemma 3 12B** (Google) | 12B | 14GB (4-bit + FP8 KV) | NVIDIA RTX 5080 (eGPU, 16GB) | ✓ | [✓] Verified (10.3 tok/s avg) |
| **Gemma 3 12B** (Google) | 12B | 24GB (fp16) | GCP L4 GPU (24GB) | ✓ | [ ] Planned |

#### Performance Benchmarks (RTX 5080 16GB)

**Gemma 3 12B Statistics** (3-run benchmark on RTX 5080 eGPU):

| Test | Mean (tok/s) | StdDev | Min | Max | Notes |
|------|--------------|--------|-----|-----|-------|
| **Vision - Boardwalk** | 2.2 | 0.3 | 2.0 | 2.5 | Stable ✓ |
| **Vision - Chart** | 13.6 | 1.0 | 12.5 | 14.4 | Stable ✓ |
| **Basic Chat** | 12.6 | 1.4 | 10.9 | 13.7 | Stable ✓ |
| **Code Generation** | 16.0 | 2.9 | 14.3 | 19.4 | Medium variance |
| **Reasoning** | 2.3 | 2.3 | 0.8 | 4.9 | High variance ⚠️ |
| **Structured Output** | 25.1 | 18.0 | 13.5 | 45.8 | High variance ⚠️ |
| **Multi-turn** | 0.2 | 0.2 | 0.1 | 0.3 | High variance ⚠️ |
| **Overall Average** | 10.3 | 3.5 | 8.1 | 14.4 | 43% CV |

**Gemma 3 12B vs 4B Comparison**:

| Metric | Gemma 3 4B | Gemma 3 12B | Speedup |
|--------|------------|-------------|----------|
| **Avg Throughput** | 2.5 tok/s | 10.3 tok/s | **4.1x** |
| **Vision Tasks** | 0.8-1.5 tok/s | 2.0-14.4 tok/s | **3-10x** |
| **Text Tasks** | 3.3-7.1 tok/s | 12.6-25.1 tok/s | **2-4x** |
| **Stability** | Consistent | Variable | See notes |

**Key Findings**:

- **Vision tasks** (charts, photos): Most stable performance, 2-14 tok/s
- **Text generation** (chat, code): Fast and relatively stable, 12-16 tok/s
- **Complex reasoning**: High variance (0.8-4.9 tok/s) suggests KV cache eviction
- **Overall**: 12B is 4x faster than 4B on average, but with notable variance

**Performance Notes**:

- High variance in reasoning/multi-turn tasks indicates KV cache pressure
- Vision tasks show excellent stability despite large image inputs
- Prefix caching helps with repeated queries but may evict under memory pressure
- Both models fit in 16GB VRAM with 4-bit quantization + FP8 KV cache

**Recommendation**: Use Gemma 3 12B over 4B if you have 16GB VRAM — it's significantly faster for most tasks. Monitor vLLM metrics (`/metrics` endpoint) to track cache performance if you experience latency spikes.

### Theoretically Supported

These models should work with vLLM but have not been tested with kanoa:

| Model | Parameters | Est. VRAM (4-bit) | Vision Support | Notes |
|-------|------------|-------------------|----------------|-------|
| **Llama 3.2 Vision** (Meta) | 11B, 90B | 12GB, 48GB | ✓ | Strong multimodal capabilities |
| **Llama 4 Scout/Maverick** (Meta) | 17B (16E/128E) | 16GB, 32GB | ✓ | Latest from Meta (Dec 2024), any-to-any model |
| **Qwen2.5-VL** (Alibaba) | 3B, 7B, 72B | 6GB, 12GB, 40GB | ✓ | Latest Qwen vision model (Nov 2024) |
| **Qwen3-VL** (Alibaba) | 2B, 4B, 32B, 235B | 4GB, 6GB, 20GB, 120GB | ✓ | Newest Qwen series (Dec 2024) |
| **InternVL 3 / 3.5** (OpenGVLab) | 1B, 4B, 8B, 26B, 78B | 4GB, 6GB, 12GB, 20GB, 40GB | ✓ | Latest InternVL series (2024) |
| **Llama 3.1** (Meta) | 8B, 70B, 405B | 8GB, 40GB, 200GB+ | ✗ | Text-only, excellent reasoning |
| **Mistral** | 7B | 8GB | ✗ | Fast, efficient text model |
| **Mixtral 8x7B** | 47B total | 28GB | ✗ | Mixture-of-experts architecture |

### Hardware Requirements

**Minimum Configuration:**

- NVIDIA GPU with CUDA support
- 12GB VRAM (for 7B models with 4-bit quantization)
- 16GB system RAM

**Recommended Configuration:**

- 16GB+ VRAM for 12B models
- 24GB+ VRAM for full-precision inference
- PCIe 3.0 x4 or better (important for eGPU setups)

For detailed infrastructure setup and more hardware configurations, see the [kanoa-mlops repository](https://github.com/lhzn-io/kanoa-mlops).

## Features

### Vision Capabilities

Vision support depends on the underlying model:

- **Multimodal models** (Molmo, Llama 3.2 Vision, Gemma 3, Qwen-VL, InternVL): `kanoa` can send figures as images
- **Text-only models**: Passing a figure will result in an error or the image being ignored

### Knowledge Base

The vLLM backend supports **Text Knowledge Bases**:

```python
# Load a text-based knowledge base
interpreter = interpreter.with_kb(kb_path="data/docs")  # Auto-detects file types
```

## Cost Tracking

Since local models don't have standard API pricing, `kanoa` estimates computational cost to help track usage:

- **Default Estimate**: ~$0.10 per 1 million tokens (input + output)

This is a rough heuristic for tracking relative usage intensity rather than actual dollar spend.

## Advanced Configuration

### Custom Model Parameters

```python
# Example with additional vLLM parameters
interpreter = AnalyticsInterpreter(
    backend="vllm",
    api_base="http://localhost:8000/v1",
    model="allenai/Molmo-7B-D-0924",
    temperature=0.7,
    max_tokens=2048
)
```

### Multiple Model Endpoints

Switch between different local models by restarting the vLLM server:

```python
# Molmo for vision tasks
molmo = AnalyticsInterpreter(
    backend="vllm",
    api_base="http://localhost:8000/v1",
    model="allenai/Molmo-7B-D-0924"
)

# Gemma 3 4B for text reasoning (restart server with different model)
gemma = AnalyticsInterpreter(
    backend="vllm",
    api_base="http://localhost:8000/v1",
    model="google/gemma-3-4b-it"
)
```

## See Also

- [Getting Started with Local Inference](../user_guide/getting_started_local.md)
- [kanoa-mlops Repository](https://github.com/lhzn-io/kanoa-mlops)
- [vLLM Documentation](https://docs.vllm.ai/)
