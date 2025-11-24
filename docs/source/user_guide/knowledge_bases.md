# Knowledge Bases

kanoa can ground its interpretations in your project's documentation and literature.

## Types of Knowledge Bases

### Text Knowledge Base

**Format**: Markdown (`.md`) and text (`.txt`) files

**Use case**: Project documentation, code comments, technical notes

**Example**:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    kb_path='./docs',
    kb_type='text'
)
```

The interpreter will:

1. Recursively find all `.md` and `.txt` files in `./docs`
2. Concatenate them with headers
3. Include the content in the LLM context

### PDF Knowledge Base

**Format**: PDF files (`.pdf`)

**Use case**: Academic papers, technical reports with figures/tables

**Requirements**: Gemini backend only (uses native vision)

**Example**:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini-3',
    kb_path='./docs/literature',
    kb_type='pdf'
)
```

The interpreter will:

1. Upload PDFs to Gemini
2. Gemini "sees" the entire PDF (text, figures, tables, equations)
3. References are available during interpretation

⚠️ **Note**: PDF knowledge bases require the Gemini backend. Claude and Molmo only support text KBs.

## Auto-Detection

Use `kb_type='auto'` (default) to automatically detect the KB type:

```python
interpreter = AnalyticsInterpreter(
    kb_path='./docs',
    kb_type='auto'  # Detects PDFs if present
)
```

## Direct Content

For small, dynamic knowledge bases, pass content directly:

```python
kb_content = \"\"\"
# Project Context
This analysis uses the Smith et al. 2023 methodology.
Key parameters: alpha=0.05, n=100
\"\"\"

interpreter = AnalyticsInterpreter(
    kb_content=kb_content
)
```

## Best Practices

### For Text KBs

- Use clear markdown headers
- Keep files focused and modular
- Include code snippets and examples
- Total size: aim for <100K tokens

### For PDF KBs

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
