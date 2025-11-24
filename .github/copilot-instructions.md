You are an expert AI coding assistant working on the `kanoa` repository.

# Core Directives

1.  **Style Adherence**: You MUST follow the guidelines in `CONTRIBUTING.md`.
    *   **Branding**: The project name is `kanoa` (lowercase). Never write "Kanoa".
    *   **Emojis**: Use sparingly. ⚠️ for warnings (not "WARNING:"), ❌ for errors. Avoid ✅ checkmarks in prose. For checklists in planning docs, use `[✓]` for completed items and `[ ]` for planned items.
    *   **Markdown**: Ensure valid, lint-free markdown.
        *   **MD029**: Use sequential ordered list numbering (1, 2, 3, not 1, 1, 1).
        *   **MD036**: Use proper headings (`##`) instead of bold text for section titles.
        *   **MD040**: Always specify language for fenced code blocks (` ```python `, not ` ``` `).

2.  **Code Quality**:
    *   **Type Hints**: All function signatures must have type hints.
        *   Always annotate return types: `-> None`, `-> str`, `-> Optional[T]`
        *   Always annotate parameters: `param: str`, `**kwargs: Any`
        *   Import types: `from typing import Any, Optional, Dict, List, cast`
        *   Use `cast(Any, obj)` in tests to access mock attributes
    *   **Docstrings**: Use Google-style docstrings.
    *   **Imports**: Keep imports clean and sorted (standard lib -> third party -> local).
    *   **Line Length**: Max 88 characters (black default). Break long strings with `\` or multi-line f-strings.
    *   **Before Submitting**: Run `make lint` - mypy and flake8 must pass with zero errors.

3.  **Context Awareness**:
    *   This is a library for interpreting data science outputs.
    *   It supports multiple backends: Gemini, Claude, Molmo.
    *   It supports Knowledge Bases (Text/PDF).

4.  **Response Format**:
    *   Be concise.
    *   When generating code, provide the full file content if it's a new file, or clear `diff` blocks if editing.
    *   Do not be chatty.

# Project Specifics

- **Setup**: Activate the development environment with `conda activate kanoa` before running any commands.
