# Streaming API

`kanoa` uses a streaming-first architecture to provide real-time feedback during long-running interpretation tasks. This guide explains how to work with the streaming interface effectively.

## Core Concepts

The `AnalyticsInterpreter.interpret` method returns an iterator of `InterpretationChunk` objects by default (`stream=True`).

### `InterpretationChunk`

Each chunk yielded by the stream has the following structure:

```python
@dataclass
class InterpretationChunk:
    content: str               # The actual data (text delta or status message)
    type: str                  # "text", "status", "usage", or "meta"
    is_final: bool = False     # True if this is the last chunk
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict] = None
```

- **`type="text"`**: A partial text update from the LLM. Concatenate these to build the full response.
- **`type="status"`**: A status update (e.g., "Connecting...", "Generating..."). Useful for UI spinners or logs.
- **`type="usage"`**: Emitted at the end of the stream, containing token usage and cost information.

## Basic Usage

### Streaming (Default)

The most efficient way to use `kanoa` is to consume the stream directly:

```python
iterator = interpreter.interpret(fig=plt.gcf())

print("Status:", end=" ")
for chunk in iterator:
    if chunk.type == "status":
        print(f"[{chunk.content}]", end=" ", flush=True)
    elif chunk.type == "text":
        print(chunk.content, end="", flush=True)
    elif chunk.type == "usage":
        print(f"\nTotal Cost: ${chunk.usage.cost:.4f}")
```

### Blocking (Legacy Behavior)

If you prefer a single result object after generation is complete, pass `stream=False`:

```python
result = interpreter.interpret(fig=plt.gcf(), stream=False)
print(result.text)
print(f"Cost: ${result.usage.cost:.4f}")
```

> **Note:** `stream=False` simply consumes the iterator internally and aggregates the result. It does not disable streaming at the API level.

## Jupyter Notebooks

In Jupyter notebooks, `kanoa` automatically handles streaming display if `display_result=True` (default).

**To see the output automatically without writing a loop, use `stream=False`:**

```python
# In a notebook cell
interpreter.interpret(fig=plt.gcf(), stream=False)
# Output updates in real-time below the cell, and returns final result object
```

If you use `stream=True` (default), you must iterate over the result to trigger the streaming output:

```python
# In a notebook cell
for _ in interpreter.interpret(fig=plt.gcf()):
    pass
```

## Backend Support

All supported backends implement the streaming interface:

- **Gemini**: Supports full text streaming.
- **Claude**: Supports full text streaming.
- **OpenAI**: Supports full text streaming.
- **vLLM**: Supports full text streaming.
