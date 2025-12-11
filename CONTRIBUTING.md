# Contributing to kanoa

We welcome contributions! Please follow these guidelines to ensure a smooth process.

## Getting Started

1. **Fork the repository** and clone it locally.
2. **Set up your development environment**:

    **Option A: Conda (recommended for contributors)**

    ```bash
    # Full dev environment with Jupyter support
    conda env create -f environment-dev.yml
    conda activate kanoa-dev
    ```

    **Option B: pip only**

    ```bash
    pip install -e ".[dev]"
    ```

    ⚠️ The pip-only option does not include Jupyter/notebook support for running examples.

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
├── kanoa-mlops/
└── kanoa-vscode-bridge/  # (optional)
```

#### VS Code Multi-Root Workspace

1. Copy the workspace template:

    ```bash
    cd kanoa/.vscode
    cp kanoa.code-workspace.template kanoa.code-workspace
    ```

2. Open VS Code: **File** > **Open Workspace from File...** > select `kanoa.code-workspace`

The workspace file is gitignored, so you can customize it (add/remove repos) without affecting others.

#### Local Development Dependencies

When developing `kanoa-mlops` alongside `kanoa`, use editable installs instead of git URLs:

```bash
# In kanoa-mlops directory, install kanoa as editable
cd ~/Projects/lhzn-io/kanoa-mlops
pip install -e ../kanoa[gemini,notebook]
```

Or create a `requirements-local.txt` for local dev:

```txt
# requirements-local.txt (gitignored)
-e ../kanoa[gemini,notebook]
-r requirements-dev.txt
```

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

We use emojis sparingly to highlight important information without creating visual clutter. We prefer a "classy", structured aesthetic over a "cartoony" one.

#### Allowed Contexts

- **Warnings/Alerts**: ⚠️ for warnings, cautions, or important notes (replaces "WARNING:", "CRITICAL:", etc.)
- **Errors**: ❌ for error messages or failed states
- **Checklists**: Use `[✓]` for completed items and `[ ]` for planned/incomplete items in planning documents
- **Marketing docs (README only)**: To distinguish key features in bullet points (e.g., "- 🔒 **Privacy First**")
- **Agent Layer / CLI Output**:
  - **Allowed**: Structural symbols and minimal emojis that enhance readability (e.g., `•`, `→`, `📦` for blobs, `📄` for files).
  - **Style**: Prefer bracketed tags (e.g., `[Blob]`, `[Text]`) over heavy emoji usage.
  - **Goal**: "Classy" and "Technical", not "Playful".

#### Prohibited Contexts

- **Headers**: Do not use emojis in section headers (H1-H6). Let the words speak for themselves.
- **Success indicators**: Avoid ✅ checkmarks in prose, lists, or status messages (use `[✓]` in checklists only)
- **Code comments**: Keep comments strictly technical
- **Commit messages**: Use conventional commits (e.g., `feat:`, `fix:`) without emojis
- **Mid-sentence**: Do not put emojis in the middle of a sentence
- **Excessive decoration**: Do not use emojis as visual flair or decoration
- **"Cartoony" Emojis**: Avoid emojis that look too informal or "cute" (e.g., 🧠, 🚀, 🤖) in technical logs.

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

#### Punctuation

- **Em-dashes**: Use spaces around em-dashes for readability.
  - ✓ `kanoa is modular — install only the backends you need`
  - ❌ `kanoa is modular—install only the backends you need`
- **Colons**: Use a colon (`:`) when introducing a list or explanation.
- **Semicolons**: Prefer shorter sentences over semicolons.

### 4. AI Contribution Policy

`kanoa` itself was built with the assistance of GitHub Coding Agent, and we embrace the use of AI tools in development. We particularly recommend Claude Code in VSCode for DevOps and infrastructure tasks.

However, to maintain the quality and reliability of the library, we enforce a strict **Human-in-the-Loop** policy:

1. **You Own the Code**: If you submit a PR generated by AI, you are responsible for understanding, explaining, and maintaining it. "The AI wrote it" is not a valid defense for bugs or security issues.
2. **Testing is Mandatory**: AI-generated code must be accompanied by comprehensive unit tests. Do not rely on the AI to verify its own work.
3. **No "Vibe Coding"**: Do not submit raw, unreviewed AI output. You must review the code for style, efficiency, and correctness before submitting.
4. **Transparency**: We appreciate transparency. If a significant portion of your PR was AI-generated, feel free to mention the tools used in the PR description.

### 5. AI Agent Instructions

If you are an AI assistant (GitHub Copilot, Antigravity, etc.):

1. **Read this file first.**
2. **Respect the `kanoa` lowercase branding.**
3. **Do not hallucinate APIs.** Check `kanoa/core/interpreter.py` for the source of truth.
4. **Keep responses concise.**

### 6. Tooling

- We use **Ruff** for linting and formatting, and **mypy** for type checking.
- Run all checks with:

    ```bash
    make lint
    ```

- Auto-format code with:

    ```bash
    make format
    ```

- **Markdown lint**: Although not part of the pre‑commit hooks, run
  `npx -y markdownlint-cli@latest . --config .markdownlint.json` and fix any
  reported issues before committing.

- Type hints are required for all function signatures.

#### Configuration Files

- **Ruff**: See `[tool.ruff]` in `pyproject.toml`
  - Line length: 88 characters (black-compatible)
  - Target: Python 3.11
  - Replaces black, isort, and flake8
- **Mypy**: See `[tool.mypy]` in `pyproject.toml`
  - Strict mode with pandas-level rigor
  - Disallows untyped definitions in library code

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

### 7. Architecture Patterns

When extending `kanoa`, follow established patterns for consistency.

#### Configuration Features

Follow the **pricing override pattern** (`kanoa/pricing.py`) when adding user-configurable features:

1. **Centralize defaults** in `kanoa/utils/<feature>.py`
2. **Runtime config class** in `kanoa/config.py`
3. **YAML support** at `~/.config/kanoa/<feature>.yaml`
4. **Constructor overrides** for per-instance customization

**Priority order**: Defaults → YAML → Runtime → Constructor params

**Example reference**: See `kanoa/pricing.py` and `kanoa/config.py` for the pricing configuration implementation.

#### Backward Compatibility

⚠️ **CRITICAL**: All new parameters MUST be optional. Existing behavior must remain unchanged unless users explicitly opt in.

#### Chainable Methods

Configuration methods should return `self` to enable method chaining.

**Example pattern**:

```python
def set_option(self, value: str) -> "ClassName":
    self._option = value
    return self
```

#### Inspection Methods

Provide `get_<feature>()` and `preview_<feature>()` methods for transparency.

**Rationale**: Users need visibility for debugging and cost management.

#### Error Handling

- Use custom exceptions from `kanoa/core/` (e.g., `TokenLimitExceeded`)
- Validate early, fail fast with actionable messages
- Include available options in error messages (e.g., "Supported models: gemini-2.0-flash, claude-3-5-sonnet")

**For detailed examples, see existing implementations in the codebase.**

## Managing API Costs During Development

When running integration tests or developing features that hit live APIs, costs can accumulate. kanoa provides the `TokenGuard` system to help manage this.

### Token Guard for Pre-flight Checks

Use `TokenGuard` to check token counts before making API calls:

```python
from kanoa.backends.gemini import GeminiTokenCounter
from kanoa.core.token_guard import TokenGuard

counter = GeminiTokenCounter(client, model="gemini-3-pro-preview")
guard = TokenGuard(counter, warn_threshold=5000)  # Conservative for dev

result = guard.check(your_content)
print(f"Tokens: {result.token_count:,}, Cost: ${result.estimated_cost:.4f}")
```

### Environment Variables for CI/CD

In automated environments, configure thresholds via environment variables:

```bash
export KANOA_TOKEN_WARN_THRESHOLD=10000
export KANOA_TOKEN_APPROVAL_THRESHOLD=50000
export KANOA_TOKEN_REJECT_THRESHOLD=200000
export KANOA_AUTO_APPROVE=1  # Skip interactive prompts in CI
```

### Integration Test Cost Tracking

The integration test suite includes a `CostTracker` that summarizes API costs at the end of each session. Check `tests/integration/conftest.py` for the implementation pattern.

For detailed documentation, see [Cost Management](docs/source/user_guide/cost_management.md).

## Testing

We use `pytest` for testing. The test suite is divided into **Unit Tests** (fast, mocked) and **Integration Tests** (slower, hit live APIs).

See [Testing Guide](docs/source/developer_guide/testing_philosophy.md) for philosophy, cost-awareness, and detailed practices.

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

⚠️ **Cost Awareness**: Integration tests cost approximately **$0.07 per full run**. They include automatic rate limiting (5 min between runs, 20 runs/day max) to prevent accidental cost overruns.

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

## Documentation

Good documentation is as important as code. We use **Sphinx** to generate our documentation.

### Building Docs Locally

To preview documentation changes locally:

1. **Install documentation dependencies**:

    ```bash
    pip install -r docs/requirements-docs.txt
    ```

2. **Build the HTML**:

    ```bash
    cd docs
    make html
    ```

3. **View**: Open `docs/build/html/index.html` in your browser.

## Release Process

For maintainers, the release process is documented in [RELEASING.md](RELEASING.md).

⚠️ **CRITICAL REMINDER**: Always update `kanoa/__version__` BEFORE creating a release!

```bash
# Quick pre-flight check
make check-version                    # Check current version
make pre-release VERSION=0.1.4        # Automated verification
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
