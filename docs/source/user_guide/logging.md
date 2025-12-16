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
lavender "kanoa" container:

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(backend="gemini", verbose=True)
result = interpreter.interpret(fig=my_figure, display_result=True, stream=False)
```

## Log Levels

kanoa supports four log levels with visual differentiation via text opacity:

| Level | Text Opacity | Use Case |
| --- | --- | --- |
| DEBUG | 50% | Detailed diagnostics (faded) |
| INFO | 85% | General progress |
| WARNING | 95% | Important notices |
| ERROR | 100% | Failures (full intensity) |

## User Log Functions

Import from `kanoa.utils`:

```python
from kanoa.utils import log_debug, log_info, log_warning, log_error
```

Each function accepts:

- `message` (str): The log message
- `title` (str, optional): A bolded title prefix for the message
- `context` (dict, optional): Structured metadata

```python
log_info("Processing complete", title="Status")
log_warning("Rate limit approaching", context={"remaining": 10})
log_error("API call failed", title="Error")
```

User log calls outside of a `log_stream()` context are collected into an
auto-created container with a gray background (one per cell execution).

## Custom Log Streams

Use `log_stream()` to group related messages into a single container:

```python
from kanoa.utils import log_stream, log_info, log_warning

with log_stream(title="Data Pipeline"):
    log_info("Step 1: Loading data...")
    log_warning("Found 5 missing values", title="Data Quality")
    log_info("Step 2: Transformations complete")
```

This produces a single styled container with all messages, rather than separate
boxes for each log call.

### Custom Colors and Opacity

Override the default gray background with RGB tuples and opacity:

```python
# Ocean blue theme with custom opacity
with log_stream(title="Ocean Theme", bg_color=(2, 62, 138), bg_opacity=0.2):
    log_info("Using ocean blue colors")

# Sunset orange theme
with log_stream(title="Sunset Theme", bg_color=(230, 115, 0), bg_opacity=0.15):
    log_info("Using sunset orange colors")
```

Text color inherits from your notebook/editor theme and is not customizable.

## Logging Rich Objects

Use `log_object()` to render DataFrames and other objects as styled tables:

```python
from kanoa.utils import log_stream, log_info, log_object
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

with log_stream(title="Data Analysis"):
    log_info("Loading dataset...")
    log_object(df, label="Dataset Preview")
    log_info("Analysis complete")
```

## Configuration Options

### Default Stream Title

By default, user logs go to an untitled stream. Change this globally:

```python
kanoa.options.default_log_stream = "My App"  # Custom title
kanoa.options.default_log_stream = False     # Disable auto-streaming
```

### Background Colors

There are two background color settings:

- **`user_log_bg_color`** — For user `log_*()` calls and `log_stream()` (default: gray)
- **`internal_log_bg_color`** — For kanoa internal logs during `interpret()` (default: lavender)

```python
kanoa.options.user_log_bg_color = (100, 149, 237)      # Cornflower blue
kanoa.options.internal_log_bg_color = (138, 43, 226)   # Purple
```

### User Log Opacity

Adjust the background opacity for user logs (default: 0.04, very translucent):

```python
kanoa.options.user_log_opacity = 0.12  # More visible
```

## Console Mode

Outside of Jupyter notebooks, logs print progressively to the console with the
same grouping behavior — no special styling, just clean text output.

## Per-Cell Behavior

In notebooks, each cell execution gets its own log container. Running multiple
cells produces separate containers:

```python
# Cell 1
with log_stream(title="Step 1"):
    log_info("Message A")
    log_info("Message B")
```

```python
# Cell 2
with log_stream(title="Step 2"):
    log_info("Message C")
```

You'll see two separate boxes — one per cell — rather than all messages
merging into a single container across cells.

## Disabling Logging

Set verbose to 0 to disable all verbose output:

```python
kanoa.options.verbose = 0
```

Disable just the auto-streaming for user logs:

```python
kanoa.options.default_log_stream = False
```
