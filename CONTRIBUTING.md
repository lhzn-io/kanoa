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
- **Marketing docs (README only)**: To distinguish key features in bullet points (e.g., "- 🔒 **Privacy First**")

#### Prohibited Contexts

- **Headers**: Do not use emojis in section headers (H1-H6). Let the words speak for themselves.
- **Success indicators**: Avoid ✅ checkmarks in lists, checklists, or status messages
- **Code comments**: Keep comments strictly technical
- **Commit messages**: Use conventional commits (e.g., `feat:`, `fix:`) without emojis
- **Mid-sentence**: Do not put emojis in the middle of a sentence
- **Excessive decoration**: Do not use emojis as visual flair or decoration

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

## Testing

- Run the full test suite:

    ```bash
    pytest tests/
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
