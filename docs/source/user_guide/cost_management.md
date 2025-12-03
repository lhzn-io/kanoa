# Cost Management

When working with LLM APIs, costs can accumulate quickly — especially during development
and experimentation. kanoa provides the `TokenGuard` system to help you monitor and
control API costs before requests are sent.

## Overview

`TokenGuard` provides pre-flight token counting with configurable guardrails:

- **Warnings**: Log when requests exceed a threshold (default: 10K tokens)
- **Approval prompts**: Interactive confirmation for large requests (default: 50K tokens)
- **Hard limits**: Block requests that exceed safety limits (default: 200K tokens)

## Quick Start

```python
from google import genai
from kanoa.backends.gemini import GeminiTokenCounter
from kanoa.core.token_guard import TokenGuard

# Initialize your client
client = genai.Client()

# Create a token counter for your backend
counter = GeminiTokenCounter(client, model="gemini-3-pro-preview")

# Wrap it with a guard
guard = TokenGuard(counter)

# Check before making an API call
content = "Your prompt here..."
result = guard.check(content)

print(f"Tokens: {result.token_count:,}")
print(f"Estimated cost: ${result.estimated_cost:.4f}")
print(f"Level: {result.level}")  # ok, warn, approval, reject

if result.approved:
    # Proceed with API call
    response = client.models.generate_content(...)
```

## Backend-Specific Counters

Each backend has its own token counter that uses the provider's native API:

### Gemini

```python
from kanoa.backends.gemini import GeminiTokenCounter

counter = GeminiTokenCounter(client, model="gemini-3-pro-preview")
```

### Claude

```python
from kanoa.backends.claude import ClaudeTokenCounter

counter = ClaudeTokenCounter(
    client,
    model="claude-sonnet-4-5",
    system="Optional system prompt"  # Counted separately by Claude
)
```

### Fallback (Estimation Only)

For backends without native token counting, use the estimation-based fallback:

```python
from kanoa.core.token_guard import FallbackTokenCounter

counter = FallbackTokenCounter(backend_name="custom", model="my-model")
```

## Threshold Configuration

### Via Constructor

```python
guard = TokenGuard(
    counter,
    warn_threshold=5_000,       # Warn above 5K tokens
    approval_threshold=25_000,  # Require approval above 25K
    reject_threshold=100_000,   # Hard block above 100K
    auto_approve=False,         # Require interactive confirmation
)
```

### Via Environment Variables

For automation and CI/CD:

```bash
export KANOA_TOKEN_WARN_THRESHOLD=5000
export KANOA_TOKEN_APPROVAL_THRESHOLD=25000
export KANOA_TOKEN_REJECT_THRESHOLD=100000
export KANOA_AUTO_APPROVE=1  # Skip interactive prompts
```

## Usage Patterns

### Basic Check

```python
result = guard.check(content)

if result.level == "reject":
    print(f"Request too large: {result.message}")
elif result.requires_approval and not result.approved:
    print("User declined large request")
else:
    # Safe to proceed
    pass
```

### Guard with Exception

The `guard()` method combines checking with automatic exception raising:

```python
from kanoa.core.token_guard import TokenLimitExceeded

try:
    result = guard.guard(content)
    # Request approved, proceed
    response = client.models.generate_content(...)
except TokenLimitExceeded as e:
    print(f"Blocked: {e.token_count:,} tokens exceeds {e.limit:,}")
    print(f"Would have cost: ${e.estimated_cost:.4f}")
```

### Custom Pricing

Override default pricing for accurate cost estimates:

```python
# Gemini 3.0 Pro pricing
pricing = {
    "input_short": 2.00,   # Per 1M tokens, <=200K context
    "input_long": 4.00,    # Per 1M tokens, >200K context
}

result = guard.check(content, pricing=pricing)
```

## Interactive Approval

When a request exceeds the approval threshold (and `auto_approve=False`),
TokenGuard displays an interactive prompt:

```text
============================================================
⚠️  LARGE TOKEN REQUEST - APPROVAL REQUIRED
============================================================
   Token count:    75,000
   Estimated cost: $0.1500
   Approval limit: 50,000 tokens
============================================================
Proceed with this request? [y/N]:
```

This works in both terminals and Jupyter notebooks.

## Integration with Backends

TokenGuard is designed to integrate with kanoa backends. Here's an example
of adding token checking to a custom workflow:

```python
from kanoa import AnalyticsInterpreter
from kanoa.backends.gemini import GeminiBackend, GeminiTokenCounter
from kanoa.core.token_guard import TokenGuard

# Set up guard with the backend's client
backend = GeminiBackend(model="gemini-3-pro-preview")
counter = GeminiTokenCounter(backend.client, model=backend.model)
guard = TokenGuard(counter, warn_threshold=5000)

# Check before expensive operations
kb_content = load_large_knowledge_base()
result = guard.check(kb_content)

if result.level in ("reject", "approval"):
    print(f"⚠️ Large KB detected: {result.token_count:,} tokens")
    print("Consider summarizing or chunking the knowledge base.")
```

## Best Practices

1. **Set conservative defaults during development**: Use lower thresholds
   to catch runaway costs early.

2. **Use `auto_approve=True` in CI/CD**: Set via `KANOA_AUTO_APPROVE=1`
   environment variable.

3. **Monitor cumulative costs**: TokenGuard checks individual requests.
   For session-wide tracking, see the integration test cost tracker pattern.

4. **Estimate before loading large KBs**: Check token counts before
   passing large knowledge bases to caching APIs.

## API Reference

```{eval-rst}
.. autoclass:: kanoa.core.token_guard.TokenGuard
   :members:
   :undoc-members:

.. autoclass:: kanoa.core.token_guard.TokenCheckResult
   :members:

.. autoclass:: kanoa.core.token_guard.TokenLimitExceeded
   :members:

.. autoclass:: kanoa.core.token_guard.TokenCounter
   :members:

.. autoclass:: kanoa.core.token_guard.BaseTokenCounter
   :members:
```
