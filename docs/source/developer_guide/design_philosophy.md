# Design Philosophy

This document captures key design decisions and their rationale.

## Display System

### Explicit Display Over Magic Methods

**Decision**: `InterpretationResult` does not implement `_repr_markdown_()`. Instead, display is handled explicitly via `display_interpretation()` when appropriate.

**Rationale**:

1. **Clarity of Intent**: Display is a side-effect, not a property of the object. Making it explicit in the code path makes the behavior predictable.
2. **Streaming Support**: In streaming mode, chunks are displayed incrementally via `stream_interpretation()`. A magic method would display both during iteration AND when the final result is returned, causing duplication.
3. **Programmatic Use**: When `interpret()` is used in scripts (stream=False, display_result=False), returning the raw result is cleaner without triggering unexpected notebook rendering.

**Implementation Pattern**:

```python
# Streaming mode: display happens during iteration
if stream:
    return stream_interpretation(chunk_iterator, display=display_result)

# Blocking mode: explicit display after result is complete
result = InterpretationResult(...)
if display_result:
    display_interpretation(result)
return result
```text
**Alternative Considered**: Implementing `_repr_markdown_()` and conditionally suppressing display. Rejected as too implicit and harder to reason about.

## Logging Defaults

### Verbose Logging by Default

**Decision**: `kanoa.options.verbose = 1` by default (info level).

**Rationale**:

1. **Cost Transparency**: Data science workflows often involve expensive API calls. Showing token usage and cache hits by default builds trust and helps users optimize costs.
2. **Debugging Workflows**: When an AI interpretation fails or gives unexpected results, seeing upload status, model selection, and token counts provides immediate diagnostic value.
3. **Educational**: For new users, seeing the internal flow (cache check → upload → interpret) demystifies the library's behavior.
4. **Easy to Disable**: Users can opt out with a single line: `kanoa.options.verbose = 0`.

**Logging Levels**:

- **0 (Silent)**: No internal logs. Only AI response is shown.
- **1 (Info)**: Token counts, cache status, uploads, model info. Default.
- **2 (Debug)**: Full request/response payloads. For troubleshooting only.

**Visual Design**: Internal logs use lavender background (`rgb(186, 164, 217)`) to distinguish them from AI responses (ocean blue).

**Example Output**:

```text
┌─ kanoa ──────────────────────────────────────┐
│ ℹ️ Uploading figure: 1.2 MB                  │
│ ✓ Cache hit: gemini-2.0-flash-exp           │
│ ⚡ Tokens: 1,234 (~$0.0012)                  │
└──────────────────────────────────────────────┘

┌─ gemini-2.0-flash-exp ───────────────────────┐
│ The plot shows a parabolic trajectory...     │
└──────────────────────────────────────────────┘
```text
**Alternative Considered**: Default to `verbose=0` for cleaner output. Rejected as reducing transparency makes the library feel like a "black box" and hides cost implications.

## Configuration Philosophy

### Layered Configuration

kanoa uses a **hierarchical configuration system**:

1. **Hard-coded Defaults**: Sensible defaults in `kanoa/config.py`
2. **User Config Files**: `~/.config/kanoa/*.yaml` for persistent settings
3. **Runtime Options**: `kanoa.options.<setting> = value`
4. **Constructor Overrides**: Per-instance customization

**Priority Order**: Constructor params → Runtime options → User YAML → Defaults

**Example**: Pricing configuration (see `kanoa/pricing.py`)

```python
# 1. Defaults in kanoa/utils/pricing_data.py
default_pricing = {...}

# 2. User overrides at ~/.config/kanoa/pricing.yaml
custom_pricing:
  gemini-2.0-flash-exp:
    input_per_million: 0.30

# 3. Runtime override
kanoa.pricing.set("gemini-2.0-flash-exp", input=0.35)

# 4. Constructor override
interpreter = AnalyticsInterpreter(pricing_override={...})
```text
**Rationale**: Gives users control at every layer while maintaining sensible defaults for beginners.

## Streaming Architecture

### Stream by Default, Block on Request

**Decision**: `interpret()` returns an `Iterator[InterpretationChunk]` by default (`stream=True`). Users opt into blocking mode with `stream=False`.

**Rationale**:

1. **Responsiveness**: Streaming gives immediate feedback in notebooks, reducing perceived latency for multi-second API calls.
2. **Progressive Enhancement**: Users see partial results as they arrive, useful for long responses.
3. **Modern API Alignment**: OpenAI, Anthropic, and Google all default to streaming in their SDKs.
4. **Backward Compatibility**: `stream=False` preserves the original blocking behavior for scripts and automation.

**Implementation**: `stream_interpretation()` accumulates chunks into a final `InterpretationResult` while displaying them incrementally.

**Example**:

```python
# Streaming (default)
for chunk in interpreter.interpret(data):
    # Display happens automatically if display_result=True
    pass

# Blocking (opt-in)
result = interpreter.interpret(data, stream=False)
print(result.interpretation)  # Wait for full response
```text
## Error Handling Philosophy

### Fail Fast, Surface Costs Early

kanoa uses **pre-flight checks** to prevent expensive mistakes:

- **Token Guard**: Estimates token usage before API calls, prompts for confirmation above thresholds.
- **Model Availability**: Validates backend models on first use, caches results.
- **Early Validation**: Checks data types, sizes, and formats before uploading.

**Rationale**: Data science API costs can escalate quickly. Catching issues before spending money is user-friendly.

**Example**:

```python
# Token guard in action
guard = TokenGuard(counter, warn_threshold=5000)
result = guard.check(large_dataset)
# → "⚠️ This will use ~47,000 tokens (~$0.09). Continue? (y/n)"
```text
## API Design Principles

### Progressive Disclosure

kanoa's API is designed for **layered complexity**:

1. **Zero Config**: `interpret(data)` works out of the box with ADC/GOOGLE_API_KEY.
2. **Simple Customization**: `interpret(data, context="focus on outliers")`.
3. **Advanced Control**: `interpreter.set_pricing(...).with_kb(...).interpret(...)`.

**Goal**: Minimize time-to-first-result while supporting power users.

### Type Safety

- All public APIs have full type hints (enforced by mypy --strict).
- Runtime validation via Pydantic models where appropriate.
- `@overload` signatures for parameter-dependent return types (e.g., `stream=True` vs `stream=False`).

**Rationale**: Type safety catches bugs at development time, improves IDE autocomplete, and serves as inline documentation.

## Testing Philosophy

See [Testing Guide](testing_philosophy.md) for detailed philosophy on mocking, cost-awareness, and integration testing.

## Future Considerations

- **Async Support**: Streaming already uses iterators; async generators could enable concurrent interpretation.
- **Caching Layer**: Persistent result caching to avoid redundant API calls (similar to context caching but for full results).
- **Multi-Backend Ensemble**: Route requests to multiple backends, compare results, or fall back on errors.

---

**Document Status**: Living document. Update when making architectural decisions.
