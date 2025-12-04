# kanoa Documentation

This directory contains the Sphinx documentation for kanoa.

## Documentation Strategy

We distinguish between three types of documentation:

1. **Public Documentation (`source/`)**: The official user manual and API reference. Built with Sphinx.
2. **Planning Documents (`planning/`)**: Living documents that track project status, checklists, and roadmaps. These are updated continuously.
3. **Analysis Documents (`analysis/`)**: Static, dated snapshots of technical research, design decisions, or strategy proposals.
   - **Naming**: `YYYYMMDD-topic-name.md`
   - **Content**: Should NOT contain living checklists. Once an analysis is complete, any action items should be moved to a planning document.
   - **Purpose**: Historical record of "why we did this".

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
