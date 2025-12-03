# Logging

kanoa provides a built-in logging system optimized for Jupyter notebooks. When
`verbose` mode is enabled, log messages appear in styled containers that update
in place — avoiding the clutter of multiple output boxes.

## Quick Start

```python
import kanoa

# Enable verbose logging
kanoa.options.verbose = 1  # INFO level
kanoa.options.verbose = 2  # DEBUG level (more detailed)
```

When you call `interpret()`, log messages automatically stream into a single
"kanoa" container:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(backend="gemini", verbose=True)
result = interpreter.interpret(fig=my_figure, display_result=True)
```

## Log Levels

kanoa supports four log levels with visual differentiation via opacity:

| Level | Opacity | Use Case |
|-------|---------|----------|
| DEBUG | 50% | Detailed diagnostics |
| INFO | 85% | General progress |
| WARNING | 95% | Important notices |
| ERROR | 100% | Failures |

## Custom Log Streams

For your own code, use `log_stream()` to group related messages:

```python
from kanoa.utils import log_stream, log_info, log_warning

with log_stream(title="Data Pipeline"):
    log_info("Step 1: Loading data...")
    log_warning("Found 5 missing values", title="Data Quality")
    log_info("Step 2: Transformations complete")
```

This produces a single styled container with all messages, rather than separate
boxes for each log call.

### Custom Colors

Override the default lavender background with RGB tuples:

```python
# Ocean blue theme
with log_stream(title="Ocean Theme", bg_color=(2, 62, 138)):
    log_info("Using ocean blue colors")

# Sunset orange theme
with log_stream(title="Sunset Theme", bg_color=(230, 115, 0)):
    log_info("Using sunset orange colors")
```

## Log Functions

Import from `kanoa.utils`:

```python
from kanoa.utils import log_debug, log_info, log_warning, log_error
```

Each function accepts:

- `message` (str): The log message
- `title` (str, optional): A title prefix for the message
- `context` (dict, optional): Structured metadata
- `stream` (LogStream, optional): Explicit stream to route to

```python
log_info("Processing complete", title="Status")
log_warning("Rate limit approaching", context={"remaining": 10})
log_error("API call failed", title="Error")
```

## Configuration Options

### Default Stream Title

By default, logs go to a stream titled "kanoa". Change this globally:

```python
kanoa.options.default_log_stream = "My App"  # Custom title
kanoa.options.default_log_stream = ""        # Disable auto-streaming
```

### Background Color

Set the default background color (RGB tuple):

```python
kanoa.options.log_bg_color = (138, 43, 226)  # Purple
```

## Console Mode

Outside of Jupyter notebooks, logs print progressively to the console with the
same grouping behavior — no special styling, just clean text output.

## Per-Cell Behavior

In notebooks, each cell execution gets its own log container. If you run:

```python
# Cell 1
log_info("Message A")
log_info("Message B")
```

```python
# Cell 2
log_info("Message C")
```

You'll see two separate "kanoa" boxes — one per cell — rather than all messages
merging into a single container across cells.

## Disabling Logging

Set verbose to 0 to disable all log output:

```python
kanoa.options.verbose = 0
```

Or disable just the auto-streaming while keeping handler-based logging:

```python
kanoa.options.default_log_stream = ""
```
