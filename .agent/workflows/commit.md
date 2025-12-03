---
description: Stage, lint, and commit changes with pre-commit hooks
---

# Commit Workflow

## Quick Checklist

1. Run `pre-commit run --all-files` before staging
2. If hooks modify files, re-stage them
3. If detect-secrets fails, stage `.secrets.baseline` first
4. After failed commit, always re-stage and retry

## Standard Flow

```bash
# 1. Pre-flight check
conda activate kanoa-dev
pre-commit run --all-files

# 2. Stage and commit
git add -A
git commit -m "type: description"

# 3. If commit fails (hooks modified files), retry
git add -A && git commit -m "type: description"
```

## Commit Message Format

Use conventional commits: `type: description`

| Type | Use Case |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes nor adds |
| `test` | Adding/updating tests |
| `chore` | Maintenance (deps, config, workflows) |

## Handling detect-secrets

### Baseline Not Staged

```bash
git add .secrets.baseline
```

### New False Positives in Docs

When documentation contains placeholder API keys (`your-api-key-here`):

```bash
# Update baseline
detect-secrets scan --baseline .secrets.baseline

# Mark docs as false positives
python -c "
import json
with open('.secrets.baseline', 'r') as f:
    baseline = json.load(f)
for filename, secrets in baseline.get('results', {}).items():
    if filename.startswith('docs/'):
        for secret in secrets:
            secret['is_secret'] = False
with open('.secrets.baseline', 'w') as f:
    json.dump(baseline, f, indent=2)
"

git add .secrets.baseline
```

## Handling Ruff Errors

### Intentional Unicode (Greek Letters, etc.)

Add to `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"path/to/file.py" = ["RUF001"]  # Intentional Unicode
```

### Auto-fixable Issues

```bash
ruff check --fix .
ruff format .
```

## Pre-commit Hook Order

1. `trim trailing whitespace` - modifies files
2. `fix end of files` - modifies files
3. `check yaml` - validation
4. `check for added large files` - validation
5. `ruff` - modifies files (auto-fix)
6. `ruff-format` - modifies files
7. `detect-secrets` - requires staged baseline
8. `mypy` - validation

## Key Reminders

- **Always run pre-commit before staging** to catch issues early
- **Stage `.secrets.baseline` immediately after updating** - hook checks if staged
- **If commit fails, re-stage and retry** - hooks may have modified files
- **Doc placeholder keys are false positives** - mark them in baseline
