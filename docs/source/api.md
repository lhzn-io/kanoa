# API Reference

This section contains the auto-generated API documentation from the kanoa source code.

```{eval-rst}
.. automodule:: kanoa
   :members:
   :undoc-members:
   :show-inheritance:
```

## Core

```{eval-rst}
.. automodule:: kanoa.core.interpreter
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: kanoa.core.types
   :members:
   :undoc-members:
   :show-inheritance:
```

## Backends

```{eval-rst}
.. automodule:: kanoa.backends.gemini
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: kanoa.backends.claude
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: kanoa.backends.molmo
   :members:
   :undoc-members:
   :show-inheritance:
```

## Data Types

### `InterpretationChunk`

```python
@dataclass
class InterpretationChunk:
    content: str               # Text delta or status message
    type: str                  # "text", "status", "usage", or "meta"
    is_final: bool = False     # True if this is the last chunk
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
```

### `InterpretationResult`

```python
@dataclass
class InterpretationResult:
    text: str
    backend: str
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
```

### `UsageInfo`

## Knowledge Base

```{eval-rst}
.. automodule:: kanoa.knowledge_base.text_kb
   :members:
   :undoc-members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: kanoa.knowledge_base.pdf_kb
   :members:
   :undoc-members:
   :show-inheritance:
```
