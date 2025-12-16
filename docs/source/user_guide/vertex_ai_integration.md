# kanoa Integration Guide

This guide helps you integrate `kanoa` into your data science project with domain-specific customizations.

## Quick Start

### 1. Install kanoa

```bash
pip install kanoa
# or add to requirements.txt
echo "kanoa>=0.1.0" >> requirements.txt
```

### 2. Basic Usage

```python
from kanoa import AnalyticsInterpreter
import matplotlib.pyplot as plt

# Create interpreter
interpreter = AnalyticsInterpreter(backend='gemini')

# Interpret a plot
plt.plot(data)
result = interpreter.interpret(plt.gcf(), context="Your analysis context", stream=False)
print(result.text)
```

## Recommended: Create a Domain-Specific Wrapper

For better integration, create a thin wrapper that provides domain-specific defaults.

### Step 1: Create Wrapper Module

**File**: `your_project/analysis/interpretation.py`

```python
"""
Domain-specific analytics interpretation wrapper for [Your Project].
"""

from pathlib import Path
from typing import Optional
from kanoa import AnalyticsInterpreter


class YourProjectInterpreter:
    """Wrapper with project-specific defaults."""

    def __init__(self, backend='gemini', **kwargs):
        # Auto-detect project knowledge base
        project_root = Path(__file__).parent.parent.parent
        kb_path = project_root / "docs"  # or wherever your docs are

        self.interpreter = AnalyticsInterpreter(
            backend=backend,
            kb_path=kb_path,
            **kwargs
        )

    def interpret_your_viz_type(self, fig, metadata=None, **kwargs):
        """Domain-specific convenience method."""
        context = "Your domain-specific context"
        if metadata:
            context += f" - {metadata}"

        return self.interpreter.interpret(
            fig=fig,
            context=context,
            focus="Domain-specific analysis focus",
            **kwargs
        )

    def interpret(self, *args, **kwargs):
        """Pass-through to underlying interpreter."""
        return self.interpreter.interpret(*args, **kwargs)


# Convenience function for notebooks
def interpret(fig=None, **kwargs):
    """Quick helper for project notebooks."""
    return YourProjectInterpreter().interpret(fig=fig, **kwargs)
```

### Step 2: Export from Module

**File**: `your_project/analysis/__init__.py`

```python
from .interpretation import YourProjectInterpreter, interpret

__all__ = [
    # ... existing exports ...
    'YourProjectInterpreter',
    'interpret',
]
```

### Step 3: Use in Notebooks

```python
from your_project.analysis import interpret

# Simple one-liner interpretation
plt.plot(your_data)
interpret(context="Experiment 1")
```

## Knowledge Base Setup

### Option 1: Markdown Documentation

Place `.md` files in your `docs/` directory:

```text
your_project/
├── docs/
│   ├── methods.md
│   ├── background.md
│   └── glossary.md
```

kanoa will automatically load and use these for context.

### Option 2: Academic PDFs (Recommended for Research)

Place PDF papers in a `docs/refs/` directory:

```text
your_project/
├── docs/
│   ├── refs/
│   │   ├── paper1.pdf
│   │   ├── paper2.pdf
│   │   └── review.pdf
```

⚠️ **Note**: PDF knowledge bases require the Gemini backend for native vision support.

### Option 3: Mixed Content

```text
your_project/
├── docs/
│   ├── methods.md
│   ├── glossary.md
│   └── refs/
│       ├── paper1.pdf
│       └── paper2.pdf
```

kanoa will auto-detect and use both.

## Knowledge Base Strategies

kanoa supports multiple strategies for integrating domain knowledge, each optimized for different use cases:

### Strategy 1: Context Stuffing (Default)

**Best for**: Small to medium knowledge bases (<200K tokens), simple setup

The default approach loads your entire knowledge base into the model's context window. With Gemini 3 Pro's 2M token context and context caching, this is cost-effective for most use cases.

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    enable_caching=True  # Reuse KB across calls
)
```

**Pros**:

- Simple setup, no additional configuration
- Works with all content types (PDFs, markdown, code)
- Leverages Gemini's native vision for PDFs
- Context caching makes it cost-effective

**Cons**:

- Limited by context window size
- All content loaded every time (even with caching)
- May include irrelevant information

**Cost**: ~$0.02-0.05 per interpretation (with caching)

### Strategy 2: Vertex AI RAG Engine (Recommended for Production)

**Best for**: Large knowledge bases (>500K tokens), production deployments, multimodal content

**The standard, best-practice approach** for connecting Gemini 3 Pro to a private knowledge base. This is Google's managed RAG service, natively integrated with Gemini and designed specifically for grounding LLM responses in your own data.

```python
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    grounding_mode='rag_engine',  # Use Vertex AI RAG Engine
    rag_config={
        'project_id': 'your-gcp-project',
        'location': 'us-central1',
        'corpus_display_name': 'marine-bio-kb',

        # Data sources (versatile ingestion)
        'sources': ['cloud_storage', 'google_drive', 'local_files'],

        # Chunking and retrieval
        'chunk_size': 512,
        'chunk_overlap': 50,
        'top_k': 5,  # Retrieve top 5 most relevant chunks
        'similarity_threshold': 0.7,

        # Multimodal support
        'extract_images': True,  # Extract and caption plots/images from PDFs
        'extract_tables': True,  # Convert tables to searchable text
        'process_video': True    # Extract transcripts and scene descriptions
    }
)

# First call creates the RAG corpus (one-time setup)
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Dive profile analysis",
    stream=False
)
```

**How it works**:

1. **Ingestion**: Documents are processed to extract text, images, tables, and video content
2. **Multimodal Extraction**:
   - Images/plots → descriptive captions generated
   - Tables → converted to structured text (Markdown)
   - Videos → speech-to-text transcripts + scene descriptions
3. **Embedding**: All content is embedded using multimodal embedding models
4. **Indexing**: RAG corpus created with managed vector database (uses Vertex AI Search backend)
5. **Retrieval**: Semantic search retrieves relevant chunks (text + image descriptions)
6. **Grounding**: Retrieved context grounds Gemini's response

**Pros**:

- **Natively integrated with Gemini 3 Pro** - official, best-practice approach
- **Multimodal knowledge base** - handles PDFs with plots/tables, images, video
- Scales to massive knowledge bases (GBs of content)
- Only retrieves relevant information (semantic search)
- 60-80% cost reduction for large KBs vs context stuffing
- Supports incremental updates (add/remove documents)
- Managed infrastructure - uses Vertex AI Search backend
- Versatile data sources (Cloud Storage, Google Drive, local files)
- Minimizes hallucinations through grounded retrieval

**Cons**:

- Requires GCP project and Vertex AI access
- Initial corpus creation takes time (one-time)
- Additional complexity vs simple context stuffing
- Corpus storage costs (~$0.40/GB/month)

**Cost**: ~$0.01-0.02 per interpretation + corpus storage (~$0.40/GB/month)

#### Managing RAG Corpora with CLI

`kanoa` provides a powerful CLI for managing your Vertex AI RAG corpora, making it easy to create, inspect, and test your knowledge bases without writing code.

**List Corpora**:

```bash
kanoa vertex rag list --project <PROJECT_ID>
```

**Create Corpus**:

```bash
kanoa vertex rag create --project <PROJECT_ID> --display-name "my-knowledge-base"
```

**Import Files**:

```bash
kanoa vertex rag import \
    --project <PROJECT_ID> \
    --display-name "my-knowledge-base" \
    --gcs-uri "gs://my-bucket/docs/"
```

**Interactive Chat (Test Retrieval)**:
Test your RAG corpus with an interactive chat session. This is great for verifying that the correct documents are being retrieved before integrating with your code.

```bash
kanoa vertex rag chat --project <PROJECT_ID> --display-name "my-knowledge-base"
```

**Delete Corpus**:

```bash
kanoa vertex rag delete --project <PROJECT_ID> --display-name "my-knowledge-base"
```

#### RAG Engine Workflow in Python

##### Initial Setup

```python
from kanoa import AnalyticsInterpreter
from pathlib import Path

# Initialize with RAG Engine
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    grounding_mode='rag_engine',
    rag_config={
        'project_id': 'my-research-project',
        'location': 'us-central1',
        'corpus_display_name': 'research-kb-2025',

        # Chunking strategy
        'chunk_size': 512,  # Tokens per chunk
        'chunk_overlap': 50,  # Overlap for context continuity

        # Retrieval parameters
        'top_k': 5,  # Number of chunks to retrieve
        'similarity_threshold': 0.7,  # Minimum relevance score

        # Optional: Use existing corpus
        # 'corpus_name': 'projects/.../corpora/...'
    }
)

# First call triggers corpus creation if it doesn't exist
print("Creating RAG corpus... (one-time setup)")
result = interpreter.interpret(
    fig=my_plot,
    context="Initial analysis",
    stream=False
)

# Corpus ID is cached for future use
print(f"Corpus created: {interpreter.kb.corpus_name}")
```

##### Adding Documents to Existing Corpus

```python
# Add new papers to existing corpus
interpreter.kb.add_documents([
    './docs/new_paper_2025.pdf',
    './docs/updated_methods.md'
])

# Corpus automatically updates
result = interpreter.interpret(fig, context="Updated analysis")
```

##### Inspecting Retrieved Context

```python
result = interpreter.interpret(
    fig=plt.gcf(),
    context="Dive behavior analysis"
)

# View what was retrieved
print("Retrieved chunks:")
for chunk in result.metadata['retrieved_chunks']:
    print(f"- {chunk['source']}: {chunk['text'][:100]}...")
    print(f"  Relevance: {chunk['score']:.2f}")
```

### Strategy 3: Grounding with Google Search

**Best for**: Real-time information, current events, general knowledge augmentation

Enables Gemini to search Google for relevant information when needed.

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='google_search',
    google_search_config={
        'dynamic_retrieval': True,  # Model decides when to search
        'max_search_results': 5
    }
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Compare this trend with recent oceanographic findings"
)

# Result includes grounding sources
print("Grounded with sources:")
for source in result.metadata['grounding_sources']:
    print(f"- {source['title']}: {source['url']}")
```

**Pros**:

- Access to real-time, up-to-date information
- No knowledge base maintenance
- Verifiable citations
- Dynamic retrieval optimizes cost

**Cons**:

- Requires internet connectivity
- May retrieve irrelevant results
- No control over source quality
- Additional cost per search

**Cost**: ~$0.05-0.10 per interpretation (when grounding is used)

### Strategy 4: Hybrid (RAG Engine + Google Search)

**Best for**: Production systems requiring both domain expertise and current information

Combines your private knowledge base with real-time web search.

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    grounding_mode='hybrid',
    rag_config={
        'project_id': 'my-project',
        'location': 'us-central1',
        'corpus_display_name': 'domain-kb',
        'top_k': 3
    },
    google_search_config={
        'dynamic_retrieval': True,
        'max_search_results': 3
    }
)

result = interpreter.interpret(
    fig=plt.gcf(),
    context="Analyze with both internal methods and recent publications"
)

# Result includes both RAG and search sources
print(f"Retrieved {len(result.metadata['rag_chunks'])} KB chunks")
print(f"Grounded with {len(result.metadata['search_sources'])} web sources")
```

**Pros**:

- Best of both worlds
- Domain expertise + current information
- Comprehensive source attribution

**Cons**:

- Highest complexity
- Higher cost
- Requires careful configuration

**Cost**: ~$0.03-0.08 per interpretation

### Strategy Comparison

| Strategy | Setup | Cost/Call | KB Size Limit | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| Context Stuffing | Simple | $0.02-0.05 | ~800K tokens | Small KBs, PDFs with figures |
| RAG Engine | Moderate | $0.01-0.02 | Unlimited | Large KBs, production |
| Google Search | Simple | $0.05-0.10 | N/A | Current events, general knowledge |
| Hybrid (RAG+Search) | Complex | $0.03-0.08 | Unlimited | Production, comprehensive |

### Choosing a Strategy

**Use Context Stuffing if**:

- Your KB is <200K tokens (~150 pages)
- You have PDFs with important figures/tables
- You want the simplest setup
- You're prototyping

**Use RAG Engine if**:

- Your KB is >500K tokens
- You have many documents (>50 PDFs)
- You need cost optimization
- You're deploying to production
- You need to update KB frequently

**Use Google Search if**:

- You need current information
- You're analyzing trends or recent events
- You want verifiable web citations
- Your domain has good web coverage

**Use Hybrid if**:

- You need both domain expertise and current info
- Cost is less important than comprehensiveness
- You're building a production research assistant
- You need maximum accuracy

**Use BigQuery if**:

- Your data is already in BigQuery
- You need to query structured/tabular data
- You're analyzing time-series or sensor data
- You want to combine historical data with current analysis
- You have embeddings stored in BigQuery for semantic search
- You're in an enterprise environment with data warehouses

## Advanced RAG Engine Configuration

### Custom Chunking Strategy

Different content types benefit from different chunking strategies:

```python
# For academic papers (preserve section context)
rag_config = {
    'chunk_size': 1024,  # Larger chunks for papers
    'chunk_overlap': 100,  # More overlap for continuity
    'chunking_strategy': 'semantic',  # Respect paragraph boundaries
}

# For code documentation (smaller, focused chunks)
rag_config = {
    'chunk_size': 256,
    'chunk_overlap': 25,
    'chunking_strategy': 'fixed',  # Fixed-size chunks
}

# For mixed content (adaptive)
rag_config = {
    'chunk_size': 512,
    'chunk_overlap': 50,
    'chunking_strategy': 'auto',  # Auto-detect best strategy
}
```

### Multi-Corpus Setup

Organize knowledge by topic or project:

```python
from kanoa import AnalyticsInterpreter

# Methods corpus
methods_interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs/methods',
    grounding_mode='rag_engine',
    rag_config={
        'corpus_display_name': 'methods-kb',
        'top_k': 3
    }
)

# Literature corpus
literature_interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs/literature',
    grounding_mode='rag_engine',
    rag_config={
        'corpus_display_name': 'literature-kb',
        'top_k': 5
    }
)

# Use appropriate interpreter for each analysis
methods_interpreter.interpret(fig1, context="Methodology validation")
literature_interpreter.interpret(fig2, context="Compare with prior work")
```

### Corpus Management

```python
from kanoa.knowledge_base import VertexRAGKnowledgeBase

# Initialize corpus manager
kb = VertexRAGKnowledgeBase(
    project_id='my-project',
    location='us-central1',
    corpus_display_name='my-kb'
)

# List all documents in corpus
docs = kb.list_documents()
for doc in docs:
    print(f"{doc.display_name}: {doc.chunk_count} chunks")

# Update specific document
kb.update_document(
    document_name='paper_2024.pdf',
    new_path='./docs/paper_2024_revised.pdf'
)

# Delete outdated documents
kb.delete_document('old_paper_2020.pdf')

# Get corpus statistics
stats = kb.get_stats()
print(f"Total chunks: {stats['total_chunks']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Storage cost: ${stats['monthly_cost_usd']:.2f}/month")
```

## Complete RAG Engine Example

Here's a complete workflow for setting up kanoa with Vertex AI RAG Engine for a marine biology research project:

```python
# marine_project/analysis/interpretation.py
from pathlib import Path
from kanoa import AnalyticsInterpreter
import os

class MarineBioInterpreter:
    """Marine biology interpreter with RAG Engine."""

    def __init__(self, use_rag_engine=True):
        project_root = Path(__file__).parent.parent.parent
        kb_path = project_root / "docs"

        if use_rag_engine:
            # Production: Use RAG Engine for large KB
            self.interpreter = AnalyticsInterpreter(
                backend='gemini',
                kb_path=kb_path,
                grounding_mode='rag_engine',
                rag_config={
                    'project_id': os.environ.get('GCP_PROJECT_ID'),
                    'location': 'us-central1',
                    'corpus_display_name': 'marine-bio-kb-2025',
                    'chunk_size': 512,
                    'chunk_overlap': 50,
                    'top_k': 5,
                    'similarity_threshold': 0.7
                },
                enable_caching=True,
                track_costs=True
            )
        else:
            # Development: Use context stuffing for simplicity
            self.interpreter = AnalyticsInterpreter(
                backend='gemini',
                kb_path=kb_path,
                enable_caching=True,
                track_costs=True
            )

    def interpret_dive_profile(self, fig, species=None, deployment_id=None):
        """Interpret dive profile with marine biology context."""
        context = f"Dive profile analysis"
        if species:
            context += f" for {species}"
        if deployment_id:
            context += f" (deployment: {deployment_id})"

        result = self.interpreter.interpret(
            fig=fig,
            context=context,
            focus="Dive frequency, depth range, behavioral patterns, anomalies"
        )

        # Show retrieved sources
        if 'retrieved_chunks' in result.metadata:
            print("\nGrounded with sources:")
            for chunk in result.metadata['retrieved_chunks']:
                print(f"  - {chunk['source']} (relevance: {chunk['score']:.2f})")

        return result

    def get_cost_summary(self):
        """Get interpretation cost summary."""
        summary = self.interpreter.get_cost_summary()

        # Add RAG-specific metrics
        if hasattr(self.interpreter.kb, 'get_stats'):
            rag_stats = self.interpreter.kb.get_stats()
            summary['rag_corpus_size'] = rag_stats['total_chunks']
            summary['rag_storage_cost_monthly'] = rag_stats['monthly_cost_usd']

        return summary

# Convenience function
def interpret(fig=None, **kwargs):
    return MarineBioInterpreter().interpret(fig=fig, **kwargs)
```

### Usage in Notebooks

```python
from marine_project.analysis import MarineBioInterpreter
import matplotlib.pyplot as plt

# Initialize (one-time per session)
interpreter = MarineBioInterpreter(use_rag_engine=True)

# Interpret dive profiles
plt.figure(figsize=(12, 6))
plt.plot(time, depth)
plt.title("Whale Shark Dive Profile - Deployment RED001")

result = interpreter.interpret_dive_profile(
    fig=plt.gcf(),
    species="Whale Shark",
    deployment_id="RED001"
)

# View cost summary
summary = interpreter.get_cost_summary()
print(f"\nSession costs:")
print(f"  Total calls: {summary['total_calls']}")
print(f"  Total cost: ${summary['total_cost_usd']:.4f}")
print(f"  Avg per call: ${summary['avg_cost_per_call']:.4f}")
if 'rag_corpus_size' in summary:
    print(f"  RAG corpus: {summary['rag_corpus_size']} chunks")
    print(f"  Storage: ${summary['rag_storage_cost_monthly']:.2f}/month")
```

### Migrating from Context Stuffing to RAG Engine

If you're currently using context stuffing and want to migrate:

```python
# Step 1: Test RAG Engine with existing code
interpreter_rag = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',  # Same KB path
    grounding_mode='rag_engine',
    rag_config={
        'project_id': 'my-project',
        'location': 'us-central1',
        'corpus_display_name': 'test-migration',
        'top_k': 5
    }
)

# Step 2: Compare results
result_context = interpreter_context_stuffing.interpret(fig, context="Test")
result_rag = interpreter_rag.interpret(fig, context="Test")

print("Context stuffing cost:", result_context.usage.cost)
print("RAG Engine cost:", result_rag.usage.cost)

# Step 3: Validate accuracy (manual review)
# Compare interpretations for quality

# Step 4: Switch to RAG Engine in production
# Update your wrapper to use grounding_mode='rag_engine'
```

### Gemini 3 Pro (Recommended)

- Best for: PDF knowledge bases, cost optimization
- Requires: `GOOGLE_API_KEY` environment variable
- Cost: ~$0.02-0.05 per interpretation (with caching)

```python
interpreter = AnalyticsInterpreter(backend='gemini')
```

### Claude Sonnet 4.5

- Best for: Proven reliability, text-only knowledge bases
- Requires: `ANTHROPIC_API_KEY` environment variable
- Cost: ~$0.30 per interpretation

```python
interpreter = AnalyticsInterpreter(backend='claude')
```

### OpenAI GPT 5.1

- Best for: Vector store integration
- Requires: `OPENAI_API_KEY` environment variable

```python
interpreter = AnalyticsInterpreter(backend='openai')
```

### Molmo (Local)

- Best for: Privacy-sensitive data, no API costs
- Requires: GPU, local model download

```python
interpreter = AnalyticsInterpreter(backend='molmo')
```

## Advanced Configuration

### Custom System Prompts

```python
result = interpreter.interpret(
    fig=fig,
    context="Your context",
    custom_prompt="Analyze this plot focusing on X, Y, Z..."
)
```

### Cost Tracking

```python
interpreter = AnalyticsInterpreter(track_costs=True)

# ... multiple interpretations ...

summary = interpreter.get_cost_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
```

### Backend-Specific Options

```python
# Gemini with high thinking level
interpreter = AnalyticsInterpreter(
    backend='gemini',
    thinking_level='high'
)

# Claude with specific model
interpreter = AnalyticsInterpreter(
    backend='claude',
    model='claude-sonnet-4-5-20250514'
)
```

## Testing Your Integration

### 1. Unit Tests

```python
import pytest
from your_project.analysis import YourProjectInterpreter

def test_interpreter_initialization():
    """Test wrapper initializes correctly."""
    interp = YourProjectInterpreter()
    assert interp.interpreter is not None

def test_domain_specific_method():
    """Test domain-specific convenience method."""
    interp = YourProjectInterpreter()
    # Mock or use test fixtures
    result = interp.interpret_your_viz_type(test_fig)
    assert result.text is not None
```

### 2. Integration Tests

```python
@pytest.mark.integration
def test_real_interpretation(test_data):
    """Test with real API (requires API key)."""
    from your_project.analysis import interpret

    fig = create_test_plot(test_data)
    result = interpret(fig, context="Test")

    assert len(result.text) > 100
    assert result.usage.cost > 0
```

## Best Practices

1. **Set API Keys in Environment**

   ```bash
   export GOOGLE_API_KEY='your-key'
   export ANTHROPIC_API_KEY='your-key'
   export OPENAI_API_KEY='your-key'
   ```

2. **Use Context Caching for Repeated Calls**

   ```python
   # Initialize once, reuse for multiple interpretations
   interpreter = AnalyticsInterpreter(enable_caching=True)

   for fig in figures:
       result = interpreter.interpret(fig)
   ```

3. **Provide Specific Context**

   ```python
   # Good: Specific context
   result = interpreter.interpret(
       fig,
       context="Water temperature time series from Station A, July 2024",
       focus="Identify anomalies and trends"
   )

   # Less effective: Vague context
   result = interpreter.interpret(fig, context="Data")
   ```

4. **Organize Knowledge Base**

   - Keep documentation up to date
   - Remove outdated PDFs
   - Use clear, descriptive filenames

## Troubleshooting

### "No module named 'kanoa'"

```bash
pip install kanoa
```

### "API key not found"

Set environment variables:

```bash
export GOOGLE_API_KEY='your-key'
```

### "PDF knowledge base requires Gemini backend"

Either:

- Switch to Gemini: `backend='gemini'`

### High costs

- Enable caching: `enable_caching=True`
- Use Gemini instead of Claude (10x cheaper with caching)
- Reduce knowledge base size

## Example: Complete Integration

Here's a complete example for a marine biology project:

```python
# marine_project/analysis/interpretation.py
from pathlib import Path
from kanoa import AnalyticsInterpreter


class MarineBioInterpreter:
    """Marine biology analysis interpreter."""

    def __init__(self, backend='gemini', **kwargs):
        project_root = Path(__file__).parent.parent.parent
        kb_path = project_root / "docs"

        self.interpreter = AnalyticsInterpreter(
            backend=backend,
            kb_path=kb_path,
            enable_caching=True,
            track_costs=True,
            **kwargs
        )

    def interpret_dive_profile(self, fig, species=None, deployment_id=None):
        """Interpret dive profile with marine biology context."""
        context = f"Dive profile analysis"
        if species:
            context += f" for {species}"
        if deployment_id:
            context += f" (deployment: {deployment_id})"

        return self.interpreter.interpret(
            fig=fig,
            context=context,
            focus="Dive frequency, depth range, behavioral patterns, anomalies"
        )

    def get_cost_summary(self):
        """Get interpretation cost summary."""
        return self.interpreter.get_cost_summary()


# Convenience function
def interpret(fig=None, **kwargs):
    return MarineBioInterpreter().interpret(fig=fig, **kwargs)
```

## Resources & References

### Official Vertex AI RAG Engine Documentation

#### 1. Vertex AI RAG Engine Quickstart (Start Here)

The fastest way to get your proprietary data indexed and connected to Gemini for Q&A.

- **[Intro to Vertex AI RAG Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/overview)**
- **What it covers:**
  - Create a RAG Corpus
  - Import files (PDFs, documents)
  - Configure RAG retrieval as a Tool for Gemini
  - Generate responses grounded in your data

#### 2. Multimodal RAG Codelab (For PDFs with Plots/Tables)

Essential for handling documents with both text and images (plots, tables, charts).

- **[Multimodal RAG using Gemini API](https://www.cloudskillsboost.google/focuses/85643)**
- **What it covers:**
  - Extract and index text + images from PDFs
  - Generate multimodal embeddings
  - Retrieve relevant text chunks AND images
  - Pass both text and image context to Gemini
  - Advanced grounded reasoning over complex documents

#### 3. Document AI Layout Parser (For Complex PDFs)

For PDFs with complex layouts (tables, multi-column text, charts).

- **[Document AI Layout Parser Integration](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/layout-parser-integration)**
- **What it covers:**
  - Enable Document AI layout parser for RAG Corpus
  - Accurate parsing of visual elements and structure
  - Superior retrieval accuracy for complex documents

### Additional Resources

- **Vertex AI Search (RAG Backend)**: [Documentation](https://cloud.google.com/vertex-ai/docs/search)
- **Grounding with Google Search**: [Documentation](https://cloud.google.com/vertex-ai/docs/grounding)
- **Gemini 3 Pro API**: [Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- **Context Caching**: [Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/context-cache)

### kanoa Support

- Documentation: [GitHub README](https://github.com/lhzn-io/kanoa)
- Issues: [GitHub Issues](https://github.com/lhzn-io/kanoa/issues)
- Discussions: [GitHub Discussions](https://github.com/lhzn-io/kanoa/discussions)
