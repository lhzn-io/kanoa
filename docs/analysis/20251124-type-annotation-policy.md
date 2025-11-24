# Type Annotation Policy and Mypy Configuration Analysis

**Date:** 2025-11-24
**Status:** Implemented

This document consolidates the detailed type annotation policy and the comparative analysis of mypy settings against pandas. The core policy summary has been integrated into `CONTRIBUTING.md`.

---

## Part 1: Type Annotation Policy

### Philosophy

kanoa follows **gradual typing** - we require complete type hints for public APIs while allowing flexibility for internal code and tests. This balances code quality with development velocity.

### Requirements by Code Type

#### Public APIs (Required)

All functions, methods, and classes in the public API **must** have complete type annotations.

**Public API includes:**

- Any function/class directly imported by users
- Any function/class documented in API docs
- Module-level `__all__` exports

**Examples:**

```python
# ✓ Correct - Fully typed public function
def interpret(
    fig: Optional[plt.Figure] = None,
    data: Optional[Any] = None,
    context: Optional[str] = None,
    **kwargs: Any,
) -> InterpretationResult:
    """Interpret analytical output."""
    pass
```

#### Private/Internal Code (Encouraged)

Internal helper functions should have type hints for maintainability, but enforcement is relaxed.

#### Tests (Flexible)

Test functions do not require strict type annotations. Type hints are welcome but not enforced.

### Type Hint Conventions

#### Use Standard Types

Prefer built-in types and `typing` module:

```python
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# ✓ Correct
def load_files(paths: List[Path]) -> Dict[str, str]:
    pass
```

#### Any vs Specific Types

⚠️ **Use `Any` as a last resort only.** It defeats the purpose of type checking.

**Before using `Any`, try:**

1. **Union types** - if multiple types are possible
2. **Protocol** - for duck typing
3. **TypeVar** - for generic functions
4. **Specific container types** - `Dict[str, int]` not `Any`

**Code review will reject PRs with unnecessary `Any` usage.**

---

## Part 2: Mypy Configuration Comparison (vs pandas)

We compared kanoa's target mypy settings against pandas (as of Nov 2025) to ensure alignment with industry best practices while maintaining appropriate strictness for a newer codebase.

### Summary

kanoa has adopted **stricter** settings than pandas regarding `Any` usage, while matching their strictness on other safety checks.

### Detailed Comparison

#### Settings Where kanoa Is **STRICTER** Than pandas

| Setting | kanoa | pandas | Impact |
| :--- | :--- | :--- | :--- |
| `disallow_any_generics` | `true` | `false` | ✓ kanoa requires `Dict[str, int]` not `Dict` |
| `disallow_any_unimported` | `true` | `false` | ✓ kanoa prevents implicit `Any` from untyped imports |
| `warn_return_any` | `true` | `false` | ✓ kanoa warns when functions return `Any` |

#### Settings Where kanoa Is **SAME** As pandas

| Setting | Both Use | Purpose |
| :--- | :--- | :--- |
| `disallow_untyped_defs` | `true` | All functions must have type hints |
| `disallow_incomplete_defs` | `true` | Partial type hints not allowed |
| `check_untyped_defs` | `true` | Check bodies of untyped functions |
| `no_implicit_optional` | `true` | Must use `Optional[T]` explicitly |
| `strict_optional` | `true` | Enforces strict None checking |
| `strict_equality` | `true` | Prevents `==` between incompatible types |
| `warn_redundant_casts` | `true` | Catch unnecessary casts |
| `warn_unused_ignores` | `true` | Catch stale `# type: ignore` |
| `warn_no_return` | `true` | Functions must return if annotated |

#### Settings Where kanoa Is **MORE LENIENT** Than pandas

| Setting | kanoa | pandas | Rationale |
| :--- | :--- | :--- | :--- |
| `disallow_untyped_decorators` | `false` | `true` | Decorator typing is complex; relaxed for now. |
| `disallow_untyped_calls` | `false` | `true` | pandas requires all function calls to be typed. |

### Final Configuration

The implemented `pyproject.toml` configuration:

```toml
[tool.mypy]
python_version = "3.10"

# Disallow dynamic typing (STRICTER than pandas)
disallow_any_unimported = true
disallow_any_generics = true
warn_return_any = true

# Untyped definitions and calls
disallow_untyped_defs = false
disallow_incomplete_defs = true
check_untyped_defs = false
disallow_untyped_decorators = false

# None and Optional handling
no_implicit_optional = true
strict_optional = true

# Configuring warnings
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
warn_unused_configs = true

# Miscellaneous strictness flags (from pandas)
strict_equality = true
enable_error_code = "ignore-without-code"
```
