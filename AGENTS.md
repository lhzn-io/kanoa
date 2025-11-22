# kanoa Agent Instructions

## Project Overview

`kanoa` (Hawaiian for "The Free One") is an open source, MIT-licensed Python library for AI-powered interpretation of data science outputs with multi-backend support (Gemini, Claude, Molmo).

## Purpose

Assist contributors by suggesting code changes, tests, and documentation edits for the kanoa repository while maintaining code quality, type safety, and adherence to project standards.

## Persona & Tone

Concise, technical, code-focused. Prioritize correctness, type safety, and comprehensive testing.

## Project Guidelines

Follow all guidelines specified in `CONTRIBUTING.md`, including:

- **Branding**: Always use `kanoa` (lowercase), never "Kanoa" or "KANOA"
- **Emojis**: Use sparingly. ⚠️ for warnings, ❌ for errors. Avoid ✅ checkmarks and header emojis.
- **Type hints**: Required for all function signatures
- **Docstrings**: Google-style format for all public APIs
- **Testing**: Maintain 85%+ code coverage

## Decision Heuristics

- Favor small, focused changes with comprehensive tests
- Prioritize type safety and explicit error handling
- Keep the API surface minimal and intuitive
- Ensure backward compatibility; use deprecation warnings for breaking changes
- Add integration tests for backend interactions

## Code Style (summary)

- **Formatting**: Use `black` and `isort` (enforced by pre-commit hooks)
- **Linting**: Pass `flake8` and `mypy` checks
- **Imports**: Standard library → third-party → local, sorted alphabetically
- **Line length**: 88 characters (black default)

## Markdown Style (summary)

- **MD029**: Use sequential ordered list numbering (1, 2, 3)
- **MD036**: Use proper headings (`##`) instead of bold text for sections
- **MD040**: Always specify language for fenced code blocks (` ```python `)

## Type Hints Guidance (summary)

- Use types from `typing` and `kanoa.core.types`
- Annotate all function signatures with parameter and return types
- Use `Optional[T]` for nullable types
- Use `Any` sparingly; prefer specific types when possible

## Docstring Guidance (summary)

- Follow Google-style docstrings
- Include: brief summary, detailed description, Args, Returns, Raises, Examples
- Ensure examples are runnable and deterministic
- Use triple double-quotes (`"""`)

## Pull Requests (summary)

Pull request titles should be descriptive and include one of the following prefixes:

- **ENH**: Enhancement, new functionality
- **BUG**: Bug fix
- **DOC**: Additions/updates to documentation
- **TST**: Additions/updates to tests
- **BLD**: Updates to the build process/scripts
- **PERF**: Performance improvement
- **TYP**: Type annotations
- **CLN**: Code cleanup
- **REF**: Refactoring

Pull request descriptions should:

- Succinctly describe the change (a few sentences is usually sufficient)
- Link to any related GitHub issues
- Include testing notes if applicable
- Avoid adding summaries to individual commit messages (PR description is sufficient)

## Testing Guidelines

- Write unit tests for all new functionality
- Use mocks for external API calls (Gemini, Claude, Molmo)
- Add integration tests for critical paths (with API keys in CI/CD)
- Ensure tests are deterministic and don't depend on external state
- Run `make test` before submitting PRs

## Development Workflow

1. Activate conda environment: `conda activate kanoa`
2. Install pre-commit hooks: `pre-commit install`
3. Make changes and write tests
4. Run formatters: `make format`
5. Run linters: `make lint`
6. Run tests: `make test`
7. Commit (pre-commit hooks will run automatically)
8. Submit PR with descriptive title and summary
