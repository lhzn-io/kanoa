You are an expert AI coding assistant working on the `kanoa` repository.
For detailed persona, commands, and boundaries, consult [agents.md](../agents.md).

# Core Directives

1.  **Style Adherence**: You MUST follow all guidelines in [CONTRIBUTING.md](../CONTRIBUTING.md).
    *   All naming conventions, emoji policy, markdown standards, and code quality rules are documented there.
    *   **Quick Reference**:
        *   Project name: `kanoa` (lowercase, never "Kanoa")
        *   Type hints required for all function signatures
        *   Google-style docstrings
        *   Line length: 88 characters (ruff default)
        *   Run `make lint` before submitting

2.  **Context Awareness**:
    *   This is a library for interpreting data science outputs.
    *   It supports multiple backends: Gemini, Claude, Molmo.
    *   It supports Knowledge Bases (Text/PDF).
    *   **Architecture**: Follow patterns in `kanoa/pricing.py` for config features. See CONTRIBUTING.md § "Architecture Patterns".

3.  **Response Format**:
    *   Be concise.
    *   When generating code, provide the full file content if it's a new file, or clear `diff` blocks if editing.
    *   Do not be chatty.

# Project Specifics

- **Setup**: Activate the development environment with `conda activate kanoa-dev` before running any commands.

## Release Process

⚠️ **CRITICAL**: When preparing a release, you MUST:

1. **Update `kanoa/__init__.py`**:
   ```python
   __version__ = "X.Y.Z"  # ← Increment this!
   ```

2. **Run pre-release check**:
   ```bash
   make pre-release VERSION=X.Y.Z
   ```

3. **Commit version bump BEFORE creating GitHub release**:
   ```bash
   git add kanoa/__init__.py
   git commit -m "chore: bump version to X.Y.Z"
   git push origin main
   ```

4. **Then create release**:
   ```bash
   gh release create vX.Y.Z --generate-notes
   ```

See [RELEASING.md](../RELEASING.md) for full details.

**Never create a GitHub release without updating `__version__` first!**

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
