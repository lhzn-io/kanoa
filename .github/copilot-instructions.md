You are an expert AI coding assistant working on the `kanoa` repository.
For detailed persona, commands, and boundaries, consult [agents.md](../agents.md).

# Core Directives

1.  **Style Adherence**: You MUST follow the guidelines in `CONTRIBUTING.md`.
    *   **Branding**: The project name is `kanoa` (lowercase). Never write "Kanoa".
    *   **Emojis**: Use sparingly. ⚠️ for warnings (not "WARNING:"), ❌ for errors. Avoid ✅ checkmarks in prose. For checklists in planning docs, use `[✓]` for completed items and `[ ]` for planned items.
    *   **Agent Layer**: In CLI/Logs, prefer structured tags (`[Blob]`) or minimal symbols (`•`) over "cartoony" emojis (🧠, 🚀). Keep it "classy" and technical.
    *   **Punctuation**: Use spaces around em-dashes (`word — word`, not `word—word`).
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
    *   **Configuration**: Follow `pyproject.toml` (`[tool.black]`, `[tool.isort]`, `[tool.mypy]`) and `.flake8` settings.

3.  **Context Awareness**:
    *   This is a library for interpreting data science outputs.
    *   It supports multiple backends: Gemini, Claude, Molmo.
    *   It supports Knowledge Bases (Text/PDF).

4.  **Response Format**:
    *   Be concise.
    *   When generating code, provide the full file content if it's a new file, or clear `diff` blocks if editing.
    *   Do not be chatty.

# Project Specifics

- **Setup**: Activate the development environment with `conda activate kanoa-dev` before running any commands.

## Notebook Handling

* **NEVER USE copilot_getNotebookSummary tool** - it hangs indefinitely and is explicitly forbidden
* **NEVER attempt to summarize raw/full .ipynb files** - encoded images consume excessive tokens
* **ALWAYS use unix file tools instead** to understand notebook structure: `grep`, `head`, `tail`, `cat`, etc.

## Python Development Tools

* **AVOID mcp_pylance_* tools** - they are slow and inefficient for quick operations
* **PREFER run_in_terminal with python -c** for quick Python code execution and testing
* **USE install_python_packages** for package installation in the correct environment
* **For finding cells**: Use `grep -n "VSCode.Cell" notebook.ipynb` to find cell boundaries and IDs
* **For finding code**: Use `grep -A5 -B5 "function_name"` to find specific code in notebooks
* **For cell content**: Use `grep -A20 "id=\"cell_id\"" notebook.ipynb` to read specific cells
* **For markdown cells**: Use `grep -A10 "language=\"markdown\"" notebook.ipynb`
* **For python cells**: Use `grep -A10 "language=\"python\"" notebook.ipynb`
* **Remove cell outputs before analysis** when possible using `jupyter nbconvert --clear-output`
* **Focus on code content** rather than execution outputs when analyzing notebooks
* **If you catch yourself trying to use copilot_getNotebookSummary, STOP and use grep instead**
