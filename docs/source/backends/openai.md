# OpenAI Backend

The `openai` backend integrates with OpenAI's GPT models.

## Configuration

Set the `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY="sk-..."  # pragma: allowlist secret
```

Initialize with:

```python
interpreter = AnalyticsInterpreter(backend="openai", model="gpt-4-turbo")
```

*Documentation in progress.*
