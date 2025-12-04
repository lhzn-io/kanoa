# Releasing kanoa

This guide outlines the process for releasing a new version of `kanoa` to PyPI and deploying the documentation.

## Prerequisites

- **Maintainer Access**: You must be a maintainer on the [PyPI project](https://pypi.org/project/kanoa/) (or part of the `lhzn-io` organization).
- **GitHub CLI**: Recommended for creating releases (`gh` command).
- **Permissions**: You need write access to the GitHub repository to push tags/releases.

## Versioning Policy

We follow [Semantic Versioning](https://semver.org/):

- **Major (X.y.z)**: Breaking changes.
- **Minor (x.Y.z)**: New features, backward compatible.
- **Patch (x.y.Z)**: Bug fixes, backward compatible.

## Pre-Flight Checklist

Before creating a release, **YOU MUST** complete this checklist:

### 1. Update Version Number

⚠️ **CRITICAL**: Increment `__version__` in `kanoa/__init__.py`

```bash
# Check current version
make check-version

# Manually edit kanoa/__init__.py
vim kanoa/__init__.py  # Update __version__ = "X.Y.Z"
```

Version must follow [Semantic Versioning](https://semver.org/):

- **Major (X.y.z)**: Breaking changes
- **Minor (x.Y.z)**: New features, backward compatible
- **Patch (x.y.Z)**: Bug fixes, backward compatible

### 2. Run Pre-Release Checks

```bash
# Automated pre-flight check
make pre-release VERSION=0.1.4
```

This verifies:

- [✓] Version in `__init__.py` matches intended release
- [✓] All tests pass
- [✓] Linting passes
- [✓] No uncommitted changes

### 3. Update Changelog

Add release notes to `CHANGELOG.md` (if it exists) or prepare notes for GitHub release.

### 4. Commit Version Bump

```bash
git add kanoa/__init__.py
git commit -m "chore: bump version to 0.1.4"
git push origin main
```

## Release Process

After completing the pre-flight checklist, create the release.

### Option 1: Using GitHub CLI (Recommended)

1. **Create and Publish Release**:
    Run this command from the repository root. Replace `v0.1.0` with your target version.

    ```bash
    gh release create v0.1.0 --generate-notes
    ```

    - `--generate-notes`: Automatically compiles a changelog from merged PRs.
    - You can add a title or edit the notes interactively if you omit the flags or use `--notes-file`.

2. **Verify**:

    ```bash
    gh release view v0.1.0 --web
    ```

### Option 2: Using GitHub Web UI

1. Navigate to the [Releases page](https://github.com/lhzn-io/kanoa/releases).
2. Click **Draft a new release**.
3. **Choose a tag**: Enter your version (e.g., `v0.1.0`) and select "Create new tag".
4. **Release title**: Enter the version number or a descriptive title.
5. **Description**: Click **Generate release notes** to auto-fill.
6. Click **Publish release**.

## What Happens Next?

Once the release is published, the following GitHub Actions are triggered:

1. **Publish to PyPI** (`publish.yml`):
    - Builds the source distribution (sdist) and binary wheel.
    - Publishes the package to PyPI using Trusted Publishing.

2. **Deploy Docs** (`docs.yml`):
    - Builds the Sphinx documentation.
    - Deploys the updated docs to GitHub Pages.

## Verification

After the workflows complete (check the [Actions tab](https://github.com/lhzn-io/kanoa/actions)):

1. **PyPI**: Check [pypi.org/project/kanoa](https://pypi.org/project/kanoa/) for the new version.
2. **Docs**: Check [lhzn-io.github.io/kanoa](https://lhzn-io.github.io/kanoa/) for the updated documentation.
