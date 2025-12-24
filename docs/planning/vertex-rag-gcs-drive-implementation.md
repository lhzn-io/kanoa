# Vertex AI RAG Engine + GCS/Drive Integration Plan

**Date:** December 11, 2025<br>
**Status:** Draft Implementation Plan<br>
**Priority:** Phase 1.1 (High Priority)<br>
**Target Timeline:** 4-6 weeks<br>

---

## Executive Summary

This document provides a detailed implementation plan for integrating Google Vertex AI RAG Engine with Cloud Storage (GCS) and Google Drive data sources into kanoa. This addresses Phase 1.1 of the roadmap and enables production-grade grounding for large knowledge bases.

#### Key Benefits

- 60-80% cost reduction vs context stuffing for large KBs
- Infinite scalability (not limited by context window)
- Multimodal support (PDFs with plots/tables, images, video)
- Native GCS and Google Drive integration with automatic indexing
- Source attribution and grounding metadata

---

## Current State Analysis

### Existing Architecture

kanoa currently implements **context stuffing** as the default knowledge base strategy:

1. **Knowledge Base Manager** ([kanoa/knowledge_base/manager.py](../../kanoa/knowledge_base/manager.py))
   - Categorizes files: PDFs, images, text, code
   - Provides backend-native encoding
   - Works with local file paths only

2. **Gemini Backend** ([kanoa/backends/gemini.py](../../kanoa/backends/gemini.py))
   - Loads entire KB into 2M token context
   - Uses File API for PDFs (AI Studio) or inline data (Vertex AI)
   - Implements context caching for cost optimization
   - Works well for KBs <200K tokens

3. **API Surface** ([kanoa/core/interpreter.py](../../kanoa/core/interpreter.py))
   - `kb_path`: Local directory path
   - `kb_content`: Pre-loaded string content
   - No support for cloud storage URIs

### Gaps for RAG Engine

- No abstraction for remote data sources (GCS, Drive)
- No RAG corpus management APIs
- No semantic retrieval configuration
- No grounding metadata in results
- Missing `google-cloud-aiplatform` dependency

---

## Technical Design

### 1. New Components

#### 1.1 `VertexRAGKnowledgeBase` Class

**Location:** `kanoa/knowledge_base/vertex_rag.py`

#### Responsibilities

- Create and manage RAG corpora via Vertex AI SDK
- Support GCS buckets, Google Drive folders, and local files
- Configure chunking, embeddings, and retrieval parameters
- Handle corpus lifecycle (create, update, delete, list)
- Provide grounding context for Gemini backend
- Enable logical KB separation via `corpus_display_name` for multi-initiative workflows

#### Design Principles

1. **Explicit Project Specification**: No default `project_id` - users must explicitly specify
   for billing transparency and multi-project workflows
2. **Corpus Display Name as Identifier**: `corpus_display_name` is REQUIRED and serves as the
   logical namespace for KB separation (e.g., "ml-research", "healthcare-qa", "legal-contracts")
3. **Automatic Corpus Reuse**: `create_corpus()` checks for existing corpus by display name,
   enabling seamless reconnection across sessions without recreation costs

#### API Sketch

```python
from pathlib import Path
from typing import List, Optional, Union
from vertexai import rag

class VertexRAGKnowledgeBase:
    """
    Vertex AI RAG Engine knowledge base with cloud storage support.

    Supports:
    - Google Cloud Storage (gs://bucket/path)
    - Google Drive (https://drive.google.com/...)
    - Local files (auto-uploaded to temp GCS bucket)
    """

    def __init__(
        self,
        project_id: str,  # REQUIRED - explicit billing separation
        location: str = "us-central1",
        corpus_display_name: str = None,  # REQUIRED for multi-KB workflows
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        embedding_model: str = "text-embedding-005",
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ):
        """
        Initialize Vertex RAG knowledge base.

        Args:
            project_id: GCP project ID (REQUIRED - no defaults for billing transparency)
            location: GCP region (us-central1, us-east4, etc.)
            corpus_display_name: Display name for RAG corpus (REQUIRED - used as unique
                identifier for corpus reuse across sessions and to separate KBs by domain)
            chunk_size: Chunk size in tokens (default: 512)
            chunk_overlap: Overlap between chunks (default: 100)
            embedding_model: Embedding model name
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity score (0-1)

        Raises:
            ValueError: If project_id or corpus_display_name not provided

        Note:
            Multiple VertexRAGKnowledgeBase instances with different corpus_display_name
            values allow logical separation of KBs for different initiatives/domains.
        """

    def create_corpus(self, force_recreate: bool = False) -> str:
        """
        Create RAG corpus with configured embedding model.

        Checks if corpus with matching display_name already exists in the project.
        If found, reuses existing corpus. If not found, creates new corpus.

        Args:
            force_recreate: Delete existing corpus with same display_name if found,
                then create fresh corpus. Use when you need to reset a KB.

        Returns:
            Corpus resource name (e.g., projects/.../locations/.../ragCorpora/...)

        Note:
            corpus_display_name serves as the logical identifier for corpus reuse.
            Two VertexRAGKnowledgeBase instances with the same project_id and
            corpus_display_name will reference the same underlying corpus.
        """

    def import_files(
        self,
        sources: Union[str, Path, List[Union[str, Path]]],
        max_embedding_requests_per_min: int = 1000,
    ) -> None:
        """
        Import files from GCS, Google Drive, or local paths.

        Args:
            sources: Single path or list of paths:
                - GCS: "gs://my-bucket/docs/"
                - Drive: "https://drive.google.com/drive/folders/..."
                - Local: Path("/path/to/local/docs")
            max_embedding_requests_per_min: Rate limit for embedding API

        Note:
            For Google Drive sources, you must share the folder with:
            service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
        """

    def retrieve(self, query: str) -> rag.RagRetrievalResponse:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User query text

        Returns:
            RagRetrievalResponse with retrieved chunks and metadata
        """

    def delete_corpus(self) -> None:
        """Delete the RAG corpus and all indexed data."""

    def list_files(self) -> List[str]:
        """List all imported files in the corpus."""

    @property
    def corpus_name(self) -> Optional[str]:
        """Return corpus resource name if created."""
```

#### 1.2 Extended `GeminiBackend` Integration

**Location:** `kanoa/backends/gemini.py`

#### Changes

- Add `grounding_mode` parameter: `'context_stuffing'` (default), `'rag_engine'`, `'google_search'`, `'hybrid'`
- Add `rag_corpus` parameter to accept `VertexRAGKnowledgeBase` instance
- Modify `interpret()` to use semantic retrieval when RAG mode enabled
- Inject retrieved chunks into prompt with source attribution
- Add grounding metadata to `InterpretationResult`

#### API Example

```python
from kanoa import AnalyticsInterpreter
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# Create RAG knowledge base
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-gcp-project",
    location="us-central1",
    corpus_display_name="research-papers-kb",
    chunk_size=512,
    top_k=5,
)

# Import from GCS
rag_kb.create_corpus()
rag_kb.import_files("gs://my-bucket/research-papers/")

# Use with interpreter
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)

result = interpreter.interpret(
    fig=my_plot,
    context="Analyze this revenue trend",
    focus="Compare to industry benchmarks"
)

# Access grounding sources
print(result.metadata['grounding_sources'])
# [
#   {'uri': 'gs://my-bucket/research-papers/industry-report-2024.pdf', 'score': 0.89},
#   {'uri': 'gs://my-bucket/research-papers/q4-analysis.pdf', 'score': 0.82},
# ]
```

#### 1.3 Extended `InterpretationResult`

**Location:** `kanoa/core/types.py`

#### Changes

```python
@dataclass
class GroundingSource:
    """Source attribution for grounding."""
    uri: str
    score: float
    chunk_text: Optional[str] = None

@dataclass
class InterpretationResult:
    """Result from interpretation."""
    text: str
    backend: str
    usage: Optional[UsageInfo] = None
    metadata: Optional[Dict[str, Any]] = None
    grounding_sources: Optional[List[GroundingSource]] = None  # NEW
```

### 2. Data Source Support

#### 2.1 Google Cloud Storage (GCS)

**Format:** `gs://bucket-name/path/to/files`

#### Authentication

- Application Default Credentials (ADC)
- Service account key file
- Workload Identity (for GKE)

#### Supported Operations

- Import entire bucket: `gs://my-bucket/`
- Import specific folder: `gs://my-bucket/docs/research/`
- Import specific file: `gs://my-bucket/report.pdf`
- Wildcard patterns: `gs://my-bucket/docs/*.pdf`

#### Implementation Notes

- Vertex AI RAG Engine handles GCS natively
- No need to download files locally
- Supports all file types (PDF, DOCX, TXT, etc.)

#### 2.2 Google Drive

**Format:** `https://drive.google.com/drive/folders/{FOLDER_ID}`

#### Authentication

- Must share Drive folder with RAG Engine service account
- Service account format: `service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com`
- Requires "Viewer" or "Editor" role

#### Supported Operations

- Import entire folder (recursive)
- Import specific file by URL

#### Implementation Notes

- Use Google Drive API to validate folder access before import
- Provide clear error messages if permissions missing
- Support for shared drives (Team Drives)

#### 2.3 Local Files (Auto-Upload)

#### Approach

1. Detect local paths in `sources` parameter
2. Create temporary GCS bucket (or use user-provided staging bucket)
3. Upload files to staging bucket
4. Import from staging bucket URI
5. Optionally clean up staging files after import

#### Configuration

```python
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-project",
    staging_bucket="gs://my-staging-bucket/kanoa-uploads/",
    auto_cleanup=True,  # Delete staging files after import
)

rag_kb.import_files([
    Path("/local/docs/paper1.pdf"),
    Path("/local/docs/paper2.pdf"),
])
```

### 3. Chunking Strategy

#### Default Configuration

- `chunk_size`: 512 tokens
- `chunk_overlap`: 100 tokens

#### Configurable Parameters

```python
transformation_config = rag.TransformationConfig(
    chunking_config=rag.ChunkingConfig(
        chunk_size=512,
        chunk_overlap=100,
    ),
)
```

#### Advanced Options (Future)

- Document AI Layout Parser for complex PDFs
- Custom chunking functions
- Multimodal chunking (extract images from PDFs)

### 4. Retrieval Configuration

#### Parameters

- `top_k`: Number of chunks to retrieve (default: 5)
- `similarity_threshold`: Minimum similarity score 0-1 (default: 0.7)

#### Example

```python
rag_retrieval_config = rag.RagRetrievalConfig(
    top_k=3,
    filter=rag.Filter(vector_distance_threshold=0.5),
)

response = rag.retrieval_query(
    rag_resources=[rag.RagResource(rag_corpus=rag_corpus.name)],
    text=user_query,
    rag_retrieval_config=rag_retrieval_config,
)
```

### 5. Prompt Integration

#### Strategy

1. User provides query via `context` and `focus` parameters
2. Retrieve relevant chunks using semantic search
3. Inject retrieved chunks into prompt with source attribution
4. Send to Gemini with grounding context

#### Prompt Template

```python
# Retrieved context
retrieved_chunks = [
    {"text": "...", "uri": "gs://...", "score": 0.89},
    {"text": "...", "uri": "gs://...", "score": 0.82},
]

# Build grounded prompt
prompt = f"""
Based on the following reference material:

{format_retrieved_chunks(retrieved_chunks)}

{context}

{focus}
"""
```

---

## Implementation Plan

### Week 1: Foundation

#### Tasks

- [ ] Add `google-cloud-aiplatform` dependency to `pyproject.toml`
- [ ] Create `kanoa/knowledge_base/vertex_rag.py`
- [ ] Implement `VertexRAGKnowledgeBase.__init__()`
- [ ] Implement `create_corpus()` with basic config
- [ ] Add unit tests with mocked Vertex AI SDK

#### Deliverables

- Basic RAG KB class with corpus creation
- Test coverage for initialization

### Week 2: Data Source Integration

#### Tasks

- [ ] Implement `import_files()` for GCS URIs
- [ ] Implement `import_files()` for Google Drive URLs
- [ ] Implement local file upload to staging bucket
- [ ] Add validation for source URIs
- [ ] Add error handling for permission issues

#### Deliverables

- Support for GCS, Drive, and local files
- Clear error messages for auth issues
- Integration tests (requires GCP project)

### Week 3: Retrieval & Prompt Integration

#### Tasks

- [ ] Implement `retrieve()` method
- [ ] Add `grounding_mode` parameter to `GeminiBackend`
- [ ] Modify `interpret()` to use RAG retrieval when enabled
- [ ] Implement chunk formatting for prompts
- [ ] Add source attribution to results

#### Deliverables

- Working end-to-end RAG pipeline
- Grounding sources in `InterpretationResult`

### Week 4: Advanced Features

#### Tasks

- [ ] Add `GroundingSource` dataclass to `types.py`
- [ ] Implement corpus management (list, update, delete)
- [ ] Add configurable chunking parameters
- [ ] Add configurable retrieval parameters
- [ ] Implement corpus reuse (check existing by display name)

#### Deliverables

- Full corpus lifecycle management
- Configurable chunking and retrieval

### Week 5: Documentation & Examples

#### Tasks

- [ ] Write user guide for RAG Engine integration
- [ ] Create example notebook: GCS knowledge base
- [ ] Create example notebook: Google Drive knowledge base
- [ ] Document migration from context stuffing
- [ ] Document Google Drive permissions setup

#### Deliverables

- Complete documentation
- Working examples
- Migration guide

### Week 6: Testing & Benchmarking

#### Tasks

- [ ] Integration tests with real GCS bucket
- [ ] Integration tests with real Drive folder
- [ ] Cost benchmarking vs context stuffing
- [ ] Retrieval precision benchmarking
- [ ] Performance testing (large KBs)

#### Deliverables

- Comprehensive test suite
- Cost/performance benchmarks
- Bug fixes and optimizations

---

## Dependencies

### Required Packages

```toml
# pyproject.toml
[project.optional-dependencies]
vertexai = [
    "google-cloud-aiplatform>=1.40.0",
]
```

### Installation

```bash
pip install kanoa[vertexai]
```

### Authentication

Users must set up Application Default Credentials:

```bash
gcloud auth application-default login
```

Or use service account key:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

---

## Migration Guide

### From Context Stuffing to RAG Engine

#### Before (Context Stuffing)

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',  # Local directory
)
```

#### After (RAG Engine)

```python
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# One-time setup: Create corpus
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-gcp-project",
    corpus_display_name="my-docs-kb",
)
rag_kb.create_corpus()
rag_kb.import_files("gs://my-bucket/docs/")

# Use with interpreter
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)
```

#### Benefits

- 60-80% cost reduction for large KBs
- Scalable to GBs of documents
- Cloud-native storage (GCS/Drive)
- Automatic chunking and indexing

---

## Cost Analysis

### Context Stuffing (Current)

**Scenario:** 500K token KB, 100 queries

| Operation | Tokens | Cost |
|-----------|--------|------|
| First query (cache write) | 500K | $2.00 |
| 99 queries (cache read) | 49.5M | $19.80 |
| **Total** | | **$21.80** |

### RAG Engine (Proposed)

**Scenario:** Same 500K token KB, 100 queries

| Operation | Cost |
|-----------|------|
| Corpus creation (one-time) | $0.50 |
| Storage (1 month) | $0.40 |
| 100 retrievals (5 chunks each) | $0.50 |
| 100 Gemini calls (500 tokens/call) | $1.00 |
| **Total (first month)** | **$2.40** |
| **Total (subsequent months)** | **$1.90** |

**Savings:** ~89% cost reduction for large KBs with repeated queries.

---

## Success Metrics

### Technical Metrics

- [ ] RAG Engine handles >1GB knowledge bases efficiently
- [ ] Retrieval latency <500ms for p95
- [ ] 85%+ retrieval precision on domain-specific queries
- [ ] 60%+ cost reduction vs context stuffing (validated)

### Quality Metrics

- [ ] Grounding sources match user expectations
- [ ] Source attribution accurate and complete
- [ ] Minimal hallucinations in grounded responses

### Developer Experience

- [ ] Setup time <10 minutes for first corpus
- [ ] Clear error messages for auth/permissions
- [ ] Documentation covers 90% of use cases

---

## Risks & Mitigations

### Risk 1: GCP Project Requirement

**Impact:** Users need GCP project for RAG Engine (not required for AI Studio)

#### Mitigation

- Maintain context stuffing as default
- Document GCP setup clearly
- Provide cost calculator

### Risk 2: Google Drive Permissions Complexity

**Impact:** Users may struggle with service account sharing

#### Mitigation

- Provide step-by-step Drive permissions guide
- Implement permission validator with actionable errors
- Consider Drive API integration to automate sharing

### Risk 3: Corpus Management Overhead

**Impact:** Users need to manage corpus lifecycle

#### Mitigation

- Implement automatic corpus reuse by display name
- Add corpus expiration/cleanup utilities
- Provide CLI tool for corpus management

### Risk 4: Retrieval Quality Variability

**Impact:** RAG may retrieve irrelevant chunks for some queries

#### Mitigation

- Provide tunable similarity thresholds
- Support hybrid mode (RAG + context stuffing)
- Document best practices for chunking

---

## Multi-KB Workflows

### Use Case: Logical KB Separation

Users often need multiple knowledge bases for different initiatives, domains, or projects:

- **Researcher**: Separate KBs for "ml-interpretability", "causal-inference", "computer-vision"
- **Multi-team org**: Separate KBs per team (e.g., "data-science-kb", "product-analytics-kb")
- **Multi-client consultant**: Separate KBs per client for billing/privacy isolation

### Design: Corpus Display Name as Namespace

Each `VertexRAGKnowledgeBase` instance uses `corpus_display_name` as its logical identifier:

```python
# ML research KB
ml_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",
    corpus_display_name="ml-interpretability",  # Unique identifier
)
ml_kb.create_corpus()
ml_kb.import_files("gs://research-papers/ml-interpretability/")

# Healthcare KB (separate corpus, same project)
health_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",
    corpus_display_name="healthcare-ai",  # Different identifier
)
health_kb.create_corpus()
health_kb.import_files("gs://research-papers/healthcare/")

# Legal KB (different project for billing separation)
legal_kb = VertexRAGKnowledgeBase(
    project_id="client-legal-project",  # Different GCP project
    corpus_display_name="contract-analysis",
)
legal_kb.create_corpus()
legal_kb.import_files("gs://client-contracts/")
```

### Switching Between KBs

```python
from kanoa import AnalyticsInterpreter

# Analyze ML experiment with ML KB
ml_interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=ml_kb,
)

result = ml_interpreter.interpret(
    fig=ml_experiment_plot,
    context="Model accuracy vs interpretability trade-off",
)

# Analyze healthcare data with Healthcare KB
health_interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=health_kb,
)

result = health_interpreter.interpret(
    fig=patient_outcomes_plot,
    context="Patient readmission risk by demographics",
)
```

### Multi-Corpus Retrieval (Future)

Phase 2 may support retrieving from multiple corpora simultaneously:

```python
# Future API (not in Phase 1)
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpora=[ml_kb, health_kb],  # List of KBs
)
```

### Corpus Lifecycle Management

#### Persistent Corpora

- Corpora persist in Vertex AI until explicitly deleted
- Reconnect to existing corpus by specifying same `project_id` + `corpus_display_name`
- No need to recreate or re-import files

#### Example: Reconnect Across Sessions

```python
# Session 1: Create and populate corpus
ml_kb = VertexRAGKnowledgeBase(
    project_id="my-project",
    corpus_display_name="ml-research",
)
ml_kb.create_corpus()  # Creates new corpus
ml_kb.import_files("gs://papers/ml/")

# Session 2 (days later): Reconnect to same corpus
ml_kb = VertexRAGKnowledgeBase(
    project_id="my-project",
    corpus_display_name="ml-research",  # Same name
)
# create_corpus() will find existing corpus and reuse it
ml_kb.create_corpus()  # No-op if corpus exists, or recreates if deleted

# Corpus is ready to use immediately (files already imported)
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=ml_kb,
)
```

#### Cleanup

```python
# Delete specific corpus when no longer needed
ml_kb.delete_corpus()

# List all corpora in project (to audit usage)
from vertexai import rag
import vertexai

vertexai.init(project="my-project", location="us-central1")
all_corpora = rag.list_corpora()
for corpus in all_corpora:
    print(f"{corpus.display_name}: {corpus.name}")
```

### Billing Transparency

#### Single Project, Multiple KBs

- All corpora in same GCP project share billing account
- Costs roll up to single invoice
- Use `corpus_display_name` to track which KB generated costs (via Vertex AI logs)

#### Multiple Projects

- Each GCP project has separate billing account
- Use different `project_id` for client/team isolation
- Example: Personal research (`my-project`) vs client work (`client-xyz-project`)

#### Cost Tracking

```python
# Check per-corpus costs via Vertex AI API (future enhancement)
corpus_usage = ml_kb.get_usage_summary()
print(f"Storage: {corpus_usage.storage_gb} GB")
print(f"Queries this month: {corpus_usage.query_count}")
print(f"Estimated cost: ${corpus_usage.estimated_cost:.2f}")
```

---

## Future Enhancements

### Phase 2: Advanced Grounding

- [ ] Document AI Layout Parser integration
- [ ] Multimodal chunking (extract images from PDFs)
- [ ] Video/audio transcript indexing
- [ ] Custom embedding models

### Phase 3: Hybrid Strategies

- [ ] Combine RAG Engine + Google Search
- [ ] Fallback to context stuffing for small queries
- [ ] Multi-corpus retrieval (combine multiple KBs)

### Phase 4: Enterprise Features

- [ ] VPC Service Controls support
- [ ] CMEK (customer-managed encryption)
- [ ] Audit logging integration
- [ ] Corpus versioning and rollback

---

## References

### Official Documentation

- [Vertex AI RAG Engine Overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
- [RAG Quickstart](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-quickstart)
- [RAG Engine API Reference](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api-v1)
- [Manage Your RAG Corpus](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/manage-your-rag-corpus)

### Community Resources

- [Building Vertex AI RAG Engine with Gemini 2 Flash](https://medium.com/google-cloud/building-vertex-ai-rag-engine-with-gemini-2-flash-llm-79c27445dd48)
- [Setup RAG with Google Drive](https://medium.com/google-cloud/setup-a-rag-with-google-drive-data-using-google-clouds-rag-engine-84f932f315e8)
- [RAG Agent with ADK](https://medium.com/google-cloud/build-a-rag-agent-using-google-adk-and-vertex-ai-rag-engine-bb1e6b1ee09d)

### kanoa Documentation

- [Knowledge Base Strategy](../analysis/20251122-knowledge-base-strategy.md)
- [Roadmap - Phase 1.1](roadmap.md#11-vertex-ai-rag-engine-high-priority)

---

## Appendix: Example Code

### Example 1: GCS Knowledge Base

```python
from kanoa import AnalyticsInterpreter
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase
import matplotlib.pyplot as plt

# Create RAG knowledge base pointing to GCS
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-gcp-project",
    location="us-central1",
    corpus_display_name="financial-reports-kb",
    chunk_size=512,
    top_k=5,
)

# Create corpus and import from GCS bucket
rag_kb.create_corpus()
rag_kb.import_files("gs://my-company-docs/financial-reports/")

# Create interpreter with RAG grounding
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)

# Create visualization
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [10, 25, 30, 45])
ax.set_title("Q4 Revenue Growth")

# Interpret with grounding
result = interpreter.interpret(
    fig=fig,
    context="Analyze Q4 revenue growth",
    focus="Compare to historical trends in our financial reports"
)

print(result.text)
print("\nGrounding Sources:")
for source in result.grounding_sources:
    print(f"  - {source.uri} (score: {source.score:.2f})")
```

### Example 2: Google Drive Knowledge Base

```python
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# Get your project number
PROJECT_NUMBER = "123456789012"

print(f"""
Before importing from Google Drive, share your folder with:
service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com

Grant 'Viewer' access.
""")

# Create RAG KB
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-gcp-project",
    corpus_display_name="team-docs-kb",
)

rag_kb.create_corpus()

# Import from Google Drive folder
drive_folder_url = "https://drive.google.com/drive/folders/1ABc..."
rag_kb.import_files(drive_folder_url)

print("Import complete! Files indexed:")
for file in rag_kb.list_files():
    print(f"  - {file}")
```

### Example 3: Hybrid Sources (GCS + Local)

```python
from pathlib import Path
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# Create RAG KB with staging bucket for local uploads
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-gcp-project",
    corpus_display_name="mixed-sources-kb",
    staging_bucket="gs://my-staging-bucket/kanoa/",
    auto_cleanup=True,
)

rag_kb.create_corpus()

# Import from multiple sources
rag_kb.import_files([
    "gs://public-datasets/research-papers/",  # GCS
    Path("/local/docs/internal-report.pdf"),  # Local (auto-uploaded)
    Path("/local/docs/notes.md"),             # Local
])
```

---

**Document Status:** Ready for review
**Next Steps:** Review with team → Approve → Begin Week 1 implementation
