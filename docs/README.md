# kanoa Documentation

This directory contains the Sphinx documentation for kanoa.

## Structure

```text
docs/
├── source/              # Sphinx source files
│   ├── index.md        # Main landing page
│   ├── quickstart.md   # Quick start guide
│   ├── user_guide/     # User guide section
│   │   ├── index.md
│   │   ├── backends.md
│   │   ├── knowledge_bases.md
│   │   ├── authentication.md
│   │   └── vertex_ai_integration.md
│   ├── api.md          # Auto-generated API reference
│   └── conf.py         # Sphinx configuration
├── build/              # Generated HTML (gitignored)
├── planning/           # Internal planning docs (not built)
├── analysis/           # Internal analysis docs (not built)
├── Makefile           # Build commands
└── requirements-docs.txt  # Documentation dependencies
```

## Building the Documentation

Install dependencies:

```bash
pip install -r requirements-docs.txt
```

Build HTML:

```bash
make html
```

View the documentation:

```bash
open build/html/index.html
```

## Adding New Pages

1. Create a new `.md` file in `source/` or `source/user_guide/`
2. Add it to the appropriate `toctree` directive in `index.md` or `user_guide/index.md`
3. Rebuild with `make html`

## Auto-Generated API Reference

The API reference in `source/api.md` is automatically generated from docstrings in the source code using Sphinx's `autodoc` extension. Update the docstrings in the code to update the API docs.
