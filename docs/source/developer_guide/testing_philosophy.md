# Testing Guide

## Philosophy

### Real-World Integration Over Mocks

Integration tests with real APIs catch issues that mocks miss: authentication, rate limiting, image encoding, model parameter changes, and API version incompatibilities.

- **Unit tests**: Logic, edge cases, error handling (fast, mocked)
- **Integration tests**: End-to-end validation with live APIs (slower, real)

### Cost-Awareness

Testing shouldn't break the bank. ~70% of integration tests use free-tier models, the rest use low-cost options. Full suite: **~$0.07/run**.

- Free-first: `gemini-2.5-flash`, local Molmo, local Gemma-3-4B, mocked tests
- Low-cost fallback: `claude-haiku-4-5-20251022` ($0.80/$4.00 per million tokens)
- Rate limiting: 5 min between runs, 20/day max
- Cost tracking: `CostTracker` reports costs at session end

### Golden Set Strategy

Small, fixed test cases validating pipeline functionality, not model intelligence:

- Focus on connectivity and plumbing
- Minimal data (programmatic plots, not large files)
- Each test <10 seconds
- Loose assertions (e.g., `assert "sine" in result.text.lower()`)

## Running Tests

```bash
pytest -m "not integration"                    # Unit tests only (fast, free)
pytest -m integration                          # All integration (~$0.07)
pytest -m "integration and gemini"             # Free tier only
pytest -m integration --force-integration      # Bypass rate limits
```

## Integration Test Cost Breakdown

| Test | Model | Cost |
| :--- | :--- | :--- |
| `test_gemini_integration.py` | gemini-2.5-flash | FREE |
| `test_molmo_local_integration.py` | Molmo-7B (local) | FREE |
| `test_gemma3_local_integration.py` | Gemma-3-4B (local) | FREE |
| `test_dynamic_kb.py` | Mocked | FREE |
| `test_claude_integration.py` | claude-haiku-4-5 | $0.008 |
| `test_gemini_caching_integration.py` | gemini-3-pro-preview | $0.038 |
| `test_gemini_cache_persistence.py` | gemini-3-pro-preview | $0.024 |
| `test_vertex_rag_integration.py` | gemini-3-pro-preview | ~$0.02 + storage |

Caching tests use paid tier to validate core feature (75% cost savings in production).

### Vertex AI RAG Tests

Vertex AI tests require specific CLI flags to point to your GCP resources:

```bash
pytest tests/integration/test_vertex_rag_integration.py \
  --vertex-project=your-project-id \
  --vertex-display-name="your-kb-name" \
  --vertex-gcs-uri="gs://your-bucket/files/"
```

## Adding Integration Tests

1. **Choose cheapest model**: gemini-2.5-flash (free), claude-haiku-4-5 (low-cost), local Molmo, or local Gemma-3-4B
2. **Add cost tracking**: `get_cost_tracker().record("test_name", result.usage.cost)`
3. **Keep data minimal**: Programmatic test data, not large files
4. **Update cost table** if adding new suite

## Best Practices

**DO:**

- Use free/low-cost models for connectivity tests
- Keep test data minimal
- Use pytest markers: `@pytest.mark.integration`, `@pytest.mark.gemini`
- Provide helpful skip messages with auth documentation links

**DON'T:**

- Use expensive models unless testing specific features
- Create large test datasets
- Run integration tests in tight loops

## Coverage Target: 85%+

Prioritize meaningful coverage over raw numbers:

- **High priority**: Public APIs, backend implementations, error handling
- **Lower priority**: CLI scripts, deprecated paths, third-party integrations
- **Acceptable gaps**: Code tested via integration tests, hard-to-mock async code, logging utilities

## Troubleshooting

**"Integration test rate limit"**: Wait 5 min or use `--force-integration`
**"No credentials found"**: See [Authentication Guide](../user_guide/authentication.md)
**"API call failed"**: Check API status, verify credentials, check quotas
**High costs**: Verify low-cost models in test fixtures

## CI/CD

```yaml
# PR: Unit tests only
pytest -m "not integration"

# Main: Full suite with cost protection
env:
  KANOA_SKIP_RATE_LIMIT: "1"
run: pytest -m integration
```

Consider running expensive tests only on `main` or scheduled nightly runs.
