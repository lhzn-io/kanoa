# Gemini Context Caching Design

**Date**: 2024-12-01
**Status**: Implemented
**Author**: kanoa Development Team

## Summary

This document describes the design and implementation of explicit context caching
for the Gemini backend in kanoa. Context caching allows users to upload a knowledge
base once and reuse it across multiple queries, reducing costs by up to 75%.

## Problem Statement

When using kanoa with a knowledge base, every `interpret()` call sends the full KB
content as part of the prompt. For large knowledge bases (10K-100K+ tokens), this
creates significant costs:

- **Cost**: $2.00 per 1M input tokens × multiple queries
- **Latency**: Re-uploading KB content on every request
- **Redundancy**: Identical content processed repeatedly

### Example Scenario

A climate scientist with a 50K token KB making 20 queries/day:

```text
Daily cost = 20 queries × 50K tokens × $2.00/1M
           = 20 × 0.05 × $2.00
           = $2.00/day
```

With caching:

```text
Daily cost = 1 × 50K × $2.00/1M + 19 × 50K × $0.50/1M
           = $0.10 + $0.475
           = $0.575/day (71% savings)
```

## Solution: Explicit Context Caching

Gemini's API supports **explicit context caching** via the `caches.create()` endpoint.
Once created, a cache can be referenced in subsequent requests using the
`cached_content` parameter.

### API Overview

```python
# Create cache
cache = client.caches.create(
    model="gemini-2.0-flash-001",  # Cache model (not preview)
    contents=[...],                 # KB content
    config={"ttl": "3600s"}         # Time-to-live
)

# Use cache in request
response = client.models.generate_content(
    model="gemini-3-pro-preview",   # Request model
    contents=[user_prompt],
    config=GenerateContentConfig(
        cached_content=cache.name   # Reference cache
    )
)
```

## Implementation Details

### Key Design Decisions

#### 1. Content Hashing for Cache Invalidation

We hash the KB content to detect changes:

```python
import hashlib

content_hash = hashlib.sha256(kb_content.encode()).hexdigest()[:16]
```

When the hash changes, the old cache is invalidated and a new one is created.

**Rationale**: Avoids stale cache issues when users update their KB files.

#### 2. Model Name Mapping for Cache Creation

Cache creation requires non-preview model names, but requests use preview names:

| Request Model | Cache Model |
| --- | --- |
| `gemini-3-pro-preview` | `gemini-2.0-flash-001` |
| `gemini-2.5-flash-preview` | `gemini-2.0-flash-001` |
| `gemini-2.5-pro-preview` | `gemini-2.5-pro-001` |

**Rationale**: The caching API doesn't accept preview model names. We use compatible
stable models for cache creation.

#### 3. Minimum Token Thresholds

Caching has minimum token requirements that vary by model:

| Model | Minimum Tokens |
| --- | --- |
| gemini-2.5-flash | 1,024 |
| gemini-3-pro-preview | 2,048 |
| gemini-2.5-pro | 4,096 |

We warn users but don't block caching attempts for smaller KBs.

**Rationale**: The API handles this gracefully; let users experiment.

#### 4. Lazy Cache Creation

Caches are created on the **first `interpret()` call**, not during initialization:

```python
def interpret(self, ...):
    if self.cache_ttl and self._kb_content and not self._cache:
        self._cache = self._create_kb_cache(self._kb_content)
    ...
```

**Rationale**: Avoids unnecessary API calls if the interpreter is never used.

### Data Flow

```text
┌─────────────────────────────────────────────────────────────┐
│                    First interpret() Call                    │
├─────────────────────────────────────────────────────────────┤
│  1. Hash KB content                                          │
│  2. Create cache via caches.create()                         │
│  3. Store cache reference + content hash                     │
│  4. Send request with cached_content parameter               │
│  5. Return result with usage (no cached_tokens yet)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Subsequent interpret() Calls                 │
├─────────────────────────────────────────────────────────────┤
│  1. Check if KB content hash changed                         │
│  2. If changed: create new cache (invalidate old)            │
│  3. If same: reuse existing cache                            │
│  4. Send request with cached_content parameter               │
│  5. Return result with usage (cached_tokens populated)       │
└─────────────────────────────────────────────────────────────┘
```

### Usage Tracking

The `UsageInfo` dataclass was extended to track caching:

```python
@dataclass
class UsageInfo:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_tokens: Optional[int] = None  # NEW

    @property
    def cache_savings(self) -> float:  # NEW
        """Calculate cost savings from caching."""
        if not self.cached_tokens:
            return 0.0
        # $2.00/1M standard - $0.50/1M cached = $1.50/1M savings
        return (self.cached_tokens / 1_000_000) * 1.50
```

### Error Handling

| Scenario | Behavior |
| --- | --- |
| Cache creation fails | Log warning, fall back to non-cached request |
| Cache expired | Create new cache automatically |
| KB content changed | Invalidate old cache, create new one |
| Model doesn't support caching | Fall back to non-cached request |

## Testing Strategy

### Unit Tests (`tests/unit/test_gemini_caching.py`)

1. **test_create_kb_cache_creates_cache**: Verify cache creation API call
2. **test_create_kb_cache_with_custom_ttl**: Verify TTL parameter
3. **test_interpret_uses_cache_when_available**: Verify cached_content in request
4. **test_clear_cache_removes_cache**: Verify cache deletion
5. **test_cache_invalidated_on_content_change**: Verify hash-based invalidation
6. **test_usage_info_includes_cached_tokens**: Verify usage tracking
7. **test_cache_savings_calculation**: Verify savings formula
8. **test_cache_model_name_mapping**: Verify model name translation

### Integration Tests (Future)

- End-to-end caching with real Gemini API
- Cache persistence across interpreter instances
- Cost verification with billing API

## Alternatives Considered

### 1. Implicit Caching (Prompt Caching)

Gemini also supports implicit/automatic caching where the API caches repeated
prompt prefixes automatically.

**Rejected because**:

- Less control over cache lifetime
- No explicit cache management
- Harder to track savings

### 2. Client-Side Caching

Store KB content locally and only send a reference.

**Rejected because**:

- Requires persistent storage
- Complex cache invalidation
- Doesn't reduce API costs (content still sent)

### 3. Embedding-Based Retrieval

Use embeddings to retrieve only relevant KB chunks.

**Future consideration**: This is RAG (Retrieval-Augmented Generation) and is
planned for Vertex AI RAG Engine integration. It's complementary to context
caching, not a replacement.

## Future Enhancements

1. **Cache Sharing**: Share caches across interpreter instances (requires cache persistence)
2. **Automatic TTL Adjustment**: Extend TTL based on usage patterns
3. **Cache Warming**: Pre-create caches during initialization
4. **Multi-Region Caching**: Support for geo-distributed caches

## References

- [Gemini Context Caching Guide](https://ai.google.dev/gemini-api/docs/caching)
- [Gemini API Pricing](https://ai.google.dev/pricing)
- [kanoa Knowledge Base Documentation](../source/user_guide/knowledge_bases.md)
