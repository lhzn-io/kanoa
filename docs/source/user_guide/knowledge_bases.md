# Knowledge Bases

kanoa can ground its interpretations in your project's documentation and literature.

## Quick Start

Simply point kanoa at a directory containing your documentation:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs'
)
```

kanoa will automatically:

1. Scan the directory for all file types
2. Detect PDFs, markdown files, text files, and code
3. Use the optimal encoding strategy for your backend

## Supported File Types

### Text Files

**Formats**: Markdown (`.md`), text (`.txt`), reStructuredText (`.rst`)

**All backends support text files** — they're concatenated and included in the prompt.

### PDF Files

**Format**: PDF files (`.pdf`)

**Backend Support**:

- **Gemini**: Native PDF support via File API (best quality, sees figures/tables)
- **Claude**: Coming soon (native PDF support planned)
- **OpenAI/vLLM**: Coming soon (PDF-to-image conversion planned)

Currently, non-Gemini backends will show a warning and use text files only.

### Code Files

**Formats**: Python (`.py`), JavaScript (`.js`), and other code files

**Use case**: Include implementation details and examples

## Direct Content

For small, dynamic knowledge bases, pass content directly:

```python
kb_content = """
# Project Context
This analysis uses the Smith et al. 2023 methodology.
Key parameters: alpha=0.05, n=100
"""

interpreter = AnalyticsInterpreter(
    kb_content=kb_content
)
```

## Examples

### Mixed Content Directory

```python
# Directory structure:
# ./docs/
#   ├── README.md
#   ├── api_reference.md
#   ├── paper.pdf
#   └── example.py

interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs'
)
# kanoa automatically:
# - Reads text from .md files
# - Uploads paper.pdf via Gemini File API
# - Includes example.py code
```

### Academic Papers (PDF)

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs/literature'  # Contains PDFs
)

# Gemini "sees" the entire PDF:
# - Text content
# - Figures and tables
# - Equations and formatting
```

### Project Documentation (Text)

```python
interpreter = AnalyticsInterpreter(
    backend='claude',  # Works with any backend
    kb_path='./docs/project'  # Contains .md files
)
```

## Best Practices

### For Text Files

- Use clear markdown headers
- Keep files focused and modular
- Include code snippets and examples
- Total size: aim for <100K tokens

### For PDF Files

- Use high-quality PDFs (not scanned images)
- Limit to 10-20 key papers
- Gemini caches PDFs, so reuse is cheap
- Total size: aim for <500K tokens

## Reloading

If your knowledge base files change during a session:

```python
interpreter.reload_knowledge_base()
```

This will re-scan the directory and update the content.

## Migration from v0.1.x

**Breaking Change in v0.2.0**: The `kb_type` parameter has been removed.

Before (v0.1.x):

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    kb_type='auto'  # ❌ No longer needed
)
```

After (v0.2.0+):

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs'  # ✓ Automatic detection
)
```

kanoa now automatically detects and optimally encodes all file types.
