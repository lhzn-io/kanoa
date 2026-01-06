# CLI Reference

`kanoa` includes a command-line interface (CLI) for quick interpretation tasks and environment management.

## `kanoa interpret`

The primary command for running interpretations from the terminal.

```bash
kanoa interpret [CONTEXT] [options]
```

### Arguments

- `CONTEXT`: The text context or question to interpret.
- `--data <file>`: Path to a data file (text, code, etc.) to include in the analysis.
- `--kb <file>`: Path to a knowledge base file (e.g., a markdown document) to ground the response.
- `--focus <text>`: Specific aspect to focus on.
- `--backend <name>`: Backend to use (default: `gemini`). Options: `gemini`, `claude`, `openai`, `vllm`.
- `--model <name>`: Override the default model for the backend.
- `--system-prompt <text>`: Override the default system prompt.

### Examples

```bash
# Quick question
kanoa interpret "Explain the difference between PCA and t-SNE"

# Analyze a file
kanoa interpret --data results.csv --focus "Identify outliers"

# Use a specific backend
kanoa interpret "Analyze this code" --data script.py --backend claude
```

## `kanoa gemini`

A suite of tools for managing the Gemini backend environment, specifically useful for switching between Google AI Studio (API Key) and Vertex AI (ADC) modes.

### `kanoa gemini mode`

Switch between `studio` and `vertex` authentication modes. This sets up your environment variables for the current session (if sourced) or updates your configuration.

```bash
# Switch to Vertex AI (Enterprise/GCP)
kanoa gemini mode vertex

# Switch to AI Studio (Personal/Free Tier)
kanoa gemini mode studio
```

### `kanoa gemini status`

Check your current authentication status for both modes.

```bash
kanoa gemini status
```

Output example:

```text
[✓] AI Studio: API Key found
[✓] Vertex AI: ADC configured (Project: my-project)
Current Mode: vertex
```

### `kanoa gemini cache`

Manage Gemini Context Caching to save costs on long contexts.

```bash
# List active caches
kanoa gemini cache list

# Delete a specific cache
kanoa gemini cache delete <cache_name>
```

### `kanoa gemini env`

Print the environment variables required for the current configuration. Useful for shell integration.

```bash
# Add this to your .bashrc or .zshrc
eval $(kanoa gemini env)
```

## Plugins

The CLI supports plugins. If you have `kanoa-mlops` installed, additional commands (like infrastructure management) may be available.
