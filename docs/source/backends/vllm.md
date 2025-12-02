# vLLM / Local Backend

The `vllm` backend allows `kanoa` to connect to locally hosted models or any OpenAI-compatible API endpoint. This is ideal for students, researchers, and organizations running their own inference infrastructure.

## Configuration

To use vLLM or a local model, you need to point `kanoa` to your API endpoint.

### Initialization

Initialize the interpreter with `backend="vllm"` (or `"openai"`) and provide the `api_base`:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend="vllm",
    api_base="http://localhost:8000/v1",  # URL of your vLLM server
    model="google/gemma-3-12b-it",        # Model name served by vLLM
    api_key="EMPTY"                       # vLLM usually doesn't require a key  pragma: allowlist secret
)
```

## Supported Models

This backend supports any model served by an OpenAI-compatible server, including:

* **Gemma 3** (Google)
* **Llama 3** (Meta)
* **Molmo** (Multimodal)
* **Mistral / Mixtral**

## Features

### Vision Capabilities

Vision support depends on the underlying model and server capabilities.

* If you are serving a multimodal model (like Molmo or Llama 3.2 Vision), `kanoa` can send images (figures) to it.
* If the model is text-only, passing a figure will result in an error or the image being ignored.

### Knowledge Base

The vLLM backend supports **Text Knowledge Bases**.

```python
# Load a text-based knowledge base
interpreter = interpreter.with_kb(kb_path="data/docs", kb_type="text")
```

## Cost Tracking

Since local models do not have a standard API price, `kanoa` estimates "computational cost" to help you track usage scale.

* **Default Estimate**: ~$0.10 per 1 million tokens (input + output).

This is a rough heuristic for tracking relative usage intensity rather than actual dollar spend.
