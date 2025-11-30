# Contributing to kanoa

We welcome contributions! Please follow these guidelines to ensure a smooth process.

## Getting Started

1. **Fork the repository** and clone it locally.
2. **Install dependencies**:

    ```bash
    pip install -e ".[dev]"
    ```

3. **Install pre-commit hooks**:
    This sets up git hooks to automatically lint and format your code before each commit.

    ```bash
    pre-commit install
    ```

4. **Create a branch** for your feature or fix:

    ```bash
    git checkout -b feature/my-awesome-feature
    ```

5. **Renaming files**: Use `git mv` to preserve file history:

    ```bash
    # ✅ Correct - preserves git history
    git mv old_name.py new_name.py

    # ❌ Incorrect - breaks git history
    rm old_name.py
    touch new_name.py
    ```

## Multi-Repo Workspace

`kanoa` is part of a larger ecosystem that includes `kanoa-mlops` (infrastructure). While each repository is independent, they are designed to work together.

### Workspace Setup

For the best development experience, we recommend cloning `kanoa-mlops` as a sibling directory to `kanoa`:

```bash
~/Projects/lhzn-io/
├── kanoa/
└── kanoa-mlops/
```

You can then open the provided workspace file in VS Code:

1. Open VS Code.
2. **File** > **Open Workspace from File...**
3. Select `kanoa/.vscode/kanoa.code-workspace`.

This will open both repositories in a single window, allowing you to work across the library and infrastructure simultaneously.

## Style Guide

This section outlines the coding, documentation, and aesthetic standards for the `kanoa` repository. All contributors (human and AI) are expected to adhere to these guidelines.

### 1. Naming Conventions

#### Project Name

- **Always** refer to the project as `kanoa` (lowercase), even at the start of sentences if possible (e.g., "`kanoa` is...").
- **Do not** use "Kanoa" (Title Case) or "KANOA" (All Caps) unless specifically required by a rigid external format.

#### Code

- **Classes**: `PascalCase` (e.g., `AnalyticsInterpreter`)
- **Functions/Variables**: `snake_case` (e.g., `interpret_figure`)
- **Constants**: `UPPER_CASE` (e.g., `DEFAULT_MODEL`)
- **Files**: `snake_case` (e.g., `text_kb.py`)

### 2. Emoji Policy

We use emojis sparingly to highlight important information without creating visual clutter.

#### Allowed Contexts

- **Warnings/Alerts**: ⚠️ for warnings, cautions, or important notes (replaces "WARNING:", "CRITICAL:", etc.)
- **Errors**: ❌ for error messages or failed states
- **Checklists**: Use `[✓]` for completed items and `[ ]` for planned/incomplete items in planning documents
- **Marketing docs (README only)**: To distinguish key features in bullet points (e.g., "- 🔒 **Privacy First**")

#### Prohibited Contexts

- **Headers**: Do not use emojis in section headers (H1-H6). Let the words speak for themselves.
- **Success indicators**: Avoid ✅ checkmarks in prose, lists, or status messages (use `[✓]` in checklists only)
- **Code comments**: Keep comments strictly technical
- **Commit messages**: Use conventional commits (e.g., `feat:`, `fix:`) without emojis
- **Mid-sentence**: Do not put emojis in the middle of a sentence
- **Excessive decoration**: Do not use emojis as visual flair or decoration

#### Checklist Convention

For planning documents and task lists:

```markdown
[✓] Completed task
[ ] Planned/incomplete task
```

**Do not use**:

- `[x]` - too harsh, prefer the elegant checkmark
- `✅` - standalone emoji, use bracketed version in checklists
- Mixed styles - be consistent within a document

#### Guidelines

- **Replace ALL CAPS with symbols**: Use ⚠️ instead of "WARNING:", "CRITICAL:", "IMPORTANT:", etc.
- **One emoji per context**: If you use ⚠️ for a warning, don't add additional emojis
- **When in doubt, omit**: Professional technical writing should default to no emojis

### 3. Markdown & Documentation

#### Linting Standards

- **Headers**: Use ATX style (`# Header`).
- **Lists**: Use hyphens (`-`) for unordered lists.
- **Code Blocks**: Always specify the language (e.g., \`\`\`python).
- **Line Length**: Soft wrap at 80-100 characters where possible, but do not break URLs.

#### Tone

- **Professional yet approachable**.
- **Concise**: Avoid fluff. Get to the point.
- **Active Voice**: "The interpreter analyzes the plot" (not "The plot is analyzed by...").

### 4. AI Agent Instructions

If you are an AI assistant (GitHub Copilot, Antigravity, etc.):

1. **Read this file first.**
2. **Respect the `kanoa` lowercase branding.**
3. **Do not hallucinate APIs.** Check `kanoa/core/interpreter.py` for the source of truth.
4. **Keep responses concise.**

### 5. Tooling

- We use **black**, **isort**, **flake8**, and **mypy** as pre‑commit hooks.
- Run all linting checks with:

    ```bash
    make lint
    ```

- **Markdown lint**: Although not part of the pre‑commit hooks, run
  `npx -y markdownlint-cli@latest . --config .markdownlint.json` and fix any
  reported issues before committing.

- Type hints are required for all function signatures.

### Type Annotations

`kanoa` enforces a strict type annotation policy to ensure code quality and maintainability.

**Quick Summary:**

| Code Type | Type Hints | Enforcement |
| :--- | :--- | :--- |
| **Public APIs** | Required | Strict (mypy) |
| **Internal Code** | Encouraged | Relaxed |
| **Tests** | Optional | Not enforced |

**Key Rules:**

1. **Public APIs Must Be Typed**: All functions/classes exported to users must have complete type hints.
2. **Avoid `Any`**: Use `Any` only as a last resort.
    - ❌ `def process(data: Any)`
    - ✓ `def process(data: Union[str, int])`
3. **Typed Containers**: Always specify types for containers.
    - ❌ `data: Dict = {}`
    - ✓ `data: Dict[str, int] = {}`
4. **No Implicit `Any`**: Do not import from untyped libraries without handling types (use stubs or `type: ignore` if necessary).

**Checking Types:**

```bash
# Run strict type check
make lint

# Check Any usage stats
make check-any-usage
```

For detailed guidelines, examples, and migration strategies, see the full [Type Annotation Policy](docs/TYPE_ANNOTATION_POLICY.md).

## Testing

We use `pytest` for testing. The test suite is divided into **Unit Tests** (fast, mocked) and **Integration Tests** (slower, hit live APIs).

### 1. Unit Tests (Required)

Run these before every commit. They mock all external API calls and should complete in seconds.

```bash
# Run only unit tests
pytest -m "not integration"
```

### 2. Integration Tests (Golden Set)

Run these to verify end-to-end functionality with live APIs (Gemini, Claude). These require valid credentials/ADC.

```bash
# Run only integration tests
pytest -m integration
```

**Note**: Integration tests use the "Golden Set" strategy—running a small, fixed set of prompts to verify the pipeline without incurring high costs.

### 3. Full Suite

```bash
# Run everything
pytest
```

- Ensure coverage remains above 85%:

    ```bash
    pytest --cov=kanoa
    ```

- Add new tests for any new features or bug fixes.

## Pull Requests

1. Ensure all tests pass.
2. Update documentation if necessary.
3. Describe your changes clearly in the PR description.
4. Link to any relevant issues.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
