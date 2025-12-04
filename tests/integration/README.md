# Integration Tests

Integration tests validate end-to-end functionality with live APIs. Cost: **~$0.07 per full run**.

## Quick Reference

```bash
pytest -m integration                           # All tests (~$0.07)
pytest -m "integration and gemini"              # Free tier only
pytest -m integration --force-integration       # Bypass rate limits
```

## Cost Profile

| Test | Model | Cost |
| :--- | :--- | :--- |
| `test_gemini_integration.py` | gemini-2.5-flash | FREE |
| `test_molmo_egpu_integration.py` | Molmo-7B (local) | FREE |
| `test_dynamic_kb.py` | Mocked | FREE |
| `test_claude_integration.py` | claude-haiku-4-5 | $0.008 |
| `test_gemini_caching_integration.py` | gemini-3-pro-preview | $0.038 |
| `test_gemini_cache_persistence.py` | gemini-3-pro-preview | $0.024 |

## Rate Limiting

- **5 min** between runs, **20/day** max
- Override: `--force-integration` or `rm ~/.config/kanoa/.integration_test_lock`

## Setup

```bash
# Gemini
export GOOGLE_API_KEY="..." or gcloud auth application-default login

# Claude
export ANTHROPIC_API_KEY="..."
```

See [Authentication Guide](../../docs/source/user_guide/authentication.md).
