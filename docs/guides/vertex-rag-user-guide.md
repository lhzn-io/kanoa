# Vertex AI RAG Engine User Guide

Complete guide to using kanoa with Google Cloud's Vertex AI RAG Engine for cost-efficient, scalable knowledge base grounding.

## Table of Contents

- [Overview](#overview)
- [When to Use RAG Engine vs Local KB](#when-to-use-rag-engine-vs-local-kb)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [CLI Management](#cli-management)
- [Python API](#python-api)
- [Configuration Guide](#configuration-guide)
- [Cost Analysis](#cost-analysis)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)

---

## Overview

Vertex AI RAG Engine is Google's managed retrieval-augmented generation service that enables semantic search over large document collections without loading entire files into context.

#### Key Benefits

- **98% cost savings** vs context stuffing for large KBs (50+ papers)
- **No per-query retrieval fees** (unlimited semantic search)
- **Server-side GCS transfer** (no local bandwidth bottleneck)
- **Automatic corpus reuse** by display name
- **Scalable** to thousands of documents

#### Architecture

```text
GCS Bucket → Vertex AI RAG Engine (chunks + embeds + indexes)
             ↓
         Retrieval (top-k chunks with scores)
             ↓
Local Kernel ← Gemini API (grounds response on retrieved chunks)
```text
---

## When to Use RAG Engine vs Local KB

### Use RAG Engine When

- **Large knowledge bases** (20+ PDFs, 100+ MB total)
- **Cost is a priority** (frequent queries, many users)
- **GCS storage is preferred** (compliance, backup, sharing)
- **Text-heavy documents** (research papers, reports, documentation)
- **Scalability matters** (KB will grow over time)

### Use Local KB When

- **Small knowledge bases** (1-5 PDFs, <10 MB total)
- **Visual content critical** (charts, diagrams need full vision)
- **Offline access required** (no internet, no GCP)
- **Rapid iteration** (testing different KB configurations)
- **One-time analysis** (infrequent queries, low volume)

#### Trade-off Summary

| Feature | RAG Engine | Local KB |
|---------|------------|----------|
| Cost (50 papers) | $0.38/month | $21.80/month |
| Setup time | 2-5 min import | Instant |
| Visual content | Text only | Full vision |
| Max KB size | Unlimited | ~100 MB (context limit) |
| Retrieval latency | ~200-500ms | 0ms (in context) |
| GCP dependency | Required | Optional |

---

## Prerequisites

### 1. Google Cloud Setup

```bash
# Install gcloud SDK
# https://cloud.google.com/sdk/docs/install

# Authenticate with Application Default Credentials (ADC)
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```text
### 2. Enable APIs

Enable Vertex AI API in your GCP project:

```bash
gcloud services enable aiplatform.googleapis.com
```text
Or via [Google Cloud Console](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com).

### 3. Install kanoa with Vertex AI Support

```bash
pip install kanoa[vertexai]
```text
### 4. Prepare Your Documents

Upload PDFs to Google Cloud Storage:

```bash
# Create bucket (if needed)
gsutil mb -p YOUR_PROJECT_ID gs://your-kb-bucket/

# Upload PDFs
gsutil -m cp local/papers/*.pdf gs://your-kb-bucket/papers/

# Verify
gsutil ls gs://your-kb-bucket/papers/
```text
---

## Quick Start

### Option 1: CLI Workflow (Recommended)

```bash
# 1. Create corpus
kanoa vertex rag create \
  --project YOUR_PROJECT_ID \
  --display-name "research-papers"

# 2. Import PDFs from GCS (async, 2-5 min for 10 files)
kanoa vertex rag import \
  --project YOUR_PROJECT_ID \
  --display-name "research-papers" \
  --gcs-uri "gs://your-kb-bucket/papers/"

# 3. List corpora to verify
kanoa vertex rag list --project YOUR_PROJECT_ID

# 4. Use in Python
python
```text
```python
from kanoa import AnalyticsInterpreter
from kanoa.knowledge_base import VertexRAGKnowledgeBase

# Connect to existing corpus
rag_kb = VertexRAGKnowledgeBase(
    project_id="YOUR_PROJECT_ID",
    corpus_display_name="research-papers",
)
rag_kb.create_corpus()  # Reuses existing corpus

# Use in interpreter
interp = AnalyticsInterpreter(
    backend="gemini",
    grounding_mode="rag_engine",
    knowledge_base=rag_kb,
)

result = interp.interpret(
    fig=my_plot,
    context="Model performance analysis",
    focus="Compare to SOTA from literature",
)
```text
### Option 2: Pure Python Workflow

```python
from kanoa import AnalyticsInterpreter
from kanoa.knowledge_base import VertexRAGKnowledgeBase

# Create and configure corpus
rag_kb = VertexRAGKnowledgeBase(
    project_id="YOUR_PROJECT_ID",
    corpus_display_name="research-papers",
    chunk_size=512,        # Tokens per chunk
    chunk_overlap=100,     # Overlap to prevent concept splitting
    top_k=5,               # Retrieve top 5 chunks
    similarity_threshold=0.7,  # Minimum relevance score
)

# Create corpus (idempotent - reuses if exists)
corpus_name = rag_kb.create_corpus()
print(f"Corpus: {corpus_name}")

# Import files (async operation)
rag_kb.import_files("gs://your-kb-bucket/papers/")
print("Import started (check console for progress)")

# Use with interpreter
interp = AnalyticsInterpreter(
    backend="gemini",
    grounding_mode="rag_engine",
    knowledge_base=rag_kb,
)

result = interp.interpret(
    fig=my_plot,
    context="Experiment results",
    focus="Explain using concepts from uploaded papers",
)

# Check grounding sources
if result.grounding_sources:
    for src in result.grounding_sources:
        print(f"[{src.score:.2f}] {src.uri}")
```text
---

## CLI Management

### List Corpora

```bash
kanoa vertex rag list --project YOUR_PROJECT_ID

# Output
# === Vertex AI RAG Corpora (YOUR_PROJECT_ID/us-east1) ===
# Display Name                   | Create Time               | Name (ID)
# research-papers                | 2025-12-12 14:30:22       | projects/123/locations/us-east1/ragCorpora/456
# client-docs                    | 2025-12-10 09:15:33       | projects/123/locations/us-east1/ragCorpora/789
```text
### Create Corpus

```bash
kanoa vertex rag create \
  --project YOUR_PROJECT_ID \
  --display-name "my-corpus" \
  --location us-east1  # Optional, default: us-east1
```text
**Note:** Creates new corpus or reuses existing with same display name.

### Import Files

```bash
kanoa vertex rag import \
  --project YOUR_PROJECT_ID \
  --display-name "my-corpus" \
  --gcs-uri "gs://bucket/path/"

# Import single file
kanoa vertex rag import \
  --display-name "my-corpus" \
  --gcs-uri "gs://bucket/paper.pdf"
```text
#### Import timing

- 10 PDFs: ~2-5 minutes
- 50 PDFs: ~10-20 minutes
- 100+ PDFs: ~30-60 minutes

Check progress in [Vertex AI Console](https://console.cloud.google.com/vertex-ai/rag).

### Delete Corpus

```bash
# With confirmation prompt
kanoa vertex rag delete \
  --project YOUR_PROJECT_ID \
  --display-name "my-corpus"

# Skip confirmation (for scripts)
kanoa vertex rag delete \
  --display-name "my-corpus" \
  --force
```text
**Warning:** Deletion is permanent. All imported documents and embeddings are lost.

### Environment Variables

Set `GOOGLE_CLOUD_PROJECT` or `GCP_PROJECT` to avoid `--project` flag:

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
kanoa vertex rag list  # Uses env var
```text
---

## Python API

### VertexRAGKnowledgeBase

Full API reference for `VertexRAGKnowledgeBase` class.

#### Constructor

```python
from kanoa.knowledge_base import VertexRAGKnowledgeBase

rag_kb = VertexRAGKnowledgeBase(
    project_id: str,              # Required: GCP project ID
    corpus_display_name: str,     # Required: Corpus identifier
    location: str = "us-east1", # Optional: GCP region
    chunk_size: int = 512,         # Optional: Tokens per chunk
    chunk_overlap: int = 100,      # Optional: Chunk overlap
    top_k: int = 5,                # Optional: Chunks to retrieve
    similarity_threshold: float = 0.7,  # Optional: Min score (0-1)
)
```text
#### Parameters

- `project_id`: GCP project ID. **Required** for billing transparency. No defaults.
- `corpus_display_name`: Logical corpus identifier. Used for automatic reuse. Use descriptive names like `"ml-papers"` or `"client-acme-docs"`.
- `location`: GCP region. Default: `us-east1`. See [available regions](https://cloud.google.com/vertex-ai/docs/general/locations).
- `chunk_size`: Document chunk size in tokens. Default: 512. See [chunking guide](#chunking-configuration).
- `chunk_overlap`: Overlap between chunks in tokens. Default: 100. Prevents concept splitting at boundaries.
- `top_k`: Number of chunks to retrieve per query. Default: 5. Higher = more context but noisier.
- `similarity_threshold`: Minimum relevance score (0-1). Default: 0.7. Lower = more chunks, higher = more selective.

#### Methods

#### create_corpus()

Create new corpus or reuse existing by display_name.

```python
corpus_name = rag_kb.create_corpus()
# Returns: "projects/123/locations/us-east1/ragCorpora/456"
```text
- Idempotent: Safe to call multiple times
- Automatic reuse: Finds existing corpus with same `display_name`
- Returns: Full corpus resource name

#### import_files(gcs_uri, max_embedding_requests_per_min=1000)

Import documents from GCS into corpus.

```python
# Import directory
rag_kb.import_files("gs://bucket/papers/")

# Import single file
rag_kb.import_files("gs://bucket/paper.pdf")

# With rate limiting
rag_kb.import_files("gs://bucket/papers/", max_embedding_requests_per_min=500)
```text
- Async operation: Returns immediately, processing in background
- Server-side: GCS → Vertex AI transfer (no local bandwidth)
- Progress: Check Vertex AI Console
- Costs: One-time embedding fee ($0.025 per 1M characters)

#### retrieve(query)

Perform semantic retrieval over corpus.

```python
results = rag_kb.retrieve("machine learning interpretability")

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Source: {result['source_uri']}")
    print(f"Text: {result['text'][:100]}...")
```text
- Returns: List of dicts with `text`, `score`, `source_uri`, `chunk_id`
- Free: No per-query retrieval fees
- Latency: ~200-500ms typical

#### delete_corpus()

Permanently delete corpus and all data.

```python
rag_kb.delete_corpus()
```text
- **Irreversible**: All documents and embeddings deleted
- Use with caution: Prefer CLI with confirmation prompt

---

## Configuration Guide

### Chunking Configuration

Chunk size affects retrieval quality and cost. Choose based on your domain:

#### Recommended Settings

| Domain | chunk_size | chunk_overlap | Rationale |
|--------|------------|---------------|-----------|
| Academic papers | 512 | 100 | Balanced: preserves context, precise retrieval |
| Legal documents | 1024 | 200 | Larger: maintains legal context and clauses |
| FAQ / short-form | 256 | 50 | Smaller: precise answers, less noise |
| Technical docs | 512 | 100 | Balanced: code snippets + explanations |
| News articles | 384 | 75 | Medium: paragraph-level retrieval |

#### Tuning Guide

#### Symptoms of chunk_size too small

- Incomplete explanations in retrieved chunks
- Missing context around key concepts
- High retrieval count needed (top_k > 10)

#### Symptoms of chunk_size too large

- Too much irrelevant content per chunk
- Lower precision (multiple topics per chunk)
- Higher embedding costs

#### Experimentation workflow

```python
# Test different chunk sizes
for chunk_size in [256, 512, 1024]:
    rag_kb = VertexRAGKnowledgeBase(
        project_id="YOUR_PROJECT",
        corpus_display_name=f"test-chunks-{chunk_size}",
        chunk_size=chunk_size,
    )
    rag_kb.create_corpus()
    rag_kb.import_files("gs://bucket/sample.pdf")

    # Wait for import, then test retrieval quality
    results = rag_kb.retrieve("your test query")
    # Evaluate: completeness, relevance, noise
```text
### Retrieval Configuration

**top_k** (number of chunks):

- Default: 5
- Too low (<3): May miss relevant context
- Too high (>10): Noise dilutes signal, higher API costs
- Recommendation: Start with 5, increase if answers incomplete

**similarity_threshold** (relevance filter):

- Default: 0.7
- Range: 0.0 (no filter) to 1.0 (perfect match)
- Lower (0.5): More chunks, higher recall, more noise
- Higher (0.8): Fewer chunks, higher precision, may miss edge cases
- Recommendation: Start with 0.7, lower if too few results

### Multi-Corpus Workflows

#### Separate corpora for different domains

```python
# Research area 1
rag_kb_ml = VertexRAGKnowledgeBase(
    project_id="my-project",
    corpus_display_name="ml-interpretability",
)

# Research area 2
rag_kb_cv = VertexRAGKnowledgeBase(
    project_id="my-project",
    corpus_display_name="computer-vision",
)

# Use different corpus per analysis
interp_ml = AnalyticsInterpreter(grounding_mode="rag_engine", knowledge_base=rag_kb_ml)
interp_cv = AnalyticsInterpreter(grounding_mode="rag_engine", knowledge_base=rag_kb_cv)
```text
#### Client/project separation

```python
# Use different projects for billing isolation
rag_kb_client_a = VertexRAGKnowledgeBase(
    project_id="client-a-project",
    corpus_display_name="analysis-docs",
)

rag_kb_client_b = VertexRAGKnowledgeBase(
    project_id="client-b-project",
    corpus_display_name="analysis-docs",
)
```text
---

## Cost Analysis

### Detailed Cost Breakdown

#### Example: 50 academic papers (average 20 pages, 5,000 words each)

#### One-time setup costs

- GCS storage: 50 PDFs × 2 MB = 100 MB → $0.002/month
- Embedding generation: 50 × 5,000 words × 5 chars = 1.25M chars → $0.03 one-time
- Vector DB storage: ~350 MB → $0.35/month

#### Per-query costs

- Retrieval: **$0.00** (no mileage fees!)
- Gemini API: Standard pricing (~$0.01 per query with 5 chunks)

#### Monthly total: ~$0.38/month + $0.01 per interpretation

#### Comparison to context stuffing (local KB)

- Load 50 PDFs into context: ~500K tokens
- Gemini input: 500K tokens × $1.25 per 1M → $0.625 per query
- 35 queries/month: $21.88/month

#### Savings: 98% ($21.50/month)

#### Cost grows with

- **More documents (linear embedding + storage)
- **NOT** with query volume (retrieval is free!)

#### Break-even analysis

- RAG Engine: $0.38/month + $0.01/query
- Context stuffing: $0.625/query
- Break-even: ~1 query/month (RAG wins almost always for KB > 20 docs)

See [full cost analysis](../analysis/20251211-vertex-rag-cost-breakdown.md) for detailed calculations.

---

## Limitations

### Current Limitations

#### PDF Processing (as of December 2025)

Vertex AI RAG Engine uses an integrated **layout parser** (Document AI technology) that intelligently processes PDFs:

#### What the layout parser handles

- Text extraction preserving document structure (headings, paragraphs, lists)
- **Table detection and content extraction** (tables are parsed and indexed)
- Multi-column layouts with correct reading order
- OCR for embedded images with text
- Automatic chunking based on semantic boundaries

#### What is NOT currently supported

- **Visual semantics** of charts/diagrams (e.g., trend analysis from line plots)
- **Image understanding** (e.g., interpreting architectural diagrams, flow charts)
- Cross-referencing "Figure 3" to its visual content

#### Example of what works

```text
PDF contains table:
| Model    | Accuracy | F1 Score |
|----------|----------|----------|
| BERT     | 0.92     | 0.89     |
| GPT-3    | 0.95     | 0.91     |
```text
→ RAG Engine will index: "Model BERT has accuracy 0.92 and F1 Score 0.89..."

#### Example of limitation

```text
PDF contains chart showing accuracy improving from 0.72 → 0.91 over 4 iterations
```text
→ RAG Engine will NOT understand the visual trend, only text like "Figure 1: Model accuracy over training iterations"

#### Recommendation

- For text-heavy papers with tables: RAG Engine works great
- For visual analysis (comparing chart patterns): Use local KB mode with Gemini File API vision

#### Workaround for mixed workflows

```python
# Use RAG for text retrieval, local KB for vision
rag_kb = VertexRAGKnowledgeBase(...)  # Text-based retrieval
kb_manager = KnowledgeBaseManager(kb_path="papers/")  # Full PDFs for vision

# Query text corpus first
interp_rag = AnalyticsInterpreter(grounding_mode="rag_engine", knowledge_base=rag_kb)
result = interp_rag.interpret(fig=plot, context="...")

# If charts needed, fall back to local KB
if needs_visual_content:
    interp_local = AnalyticsInterpreter(kb_path="papers/")
    result = interp_local.interpret(fig=plot, context="... reference Figure 3 in paper X")
```text
#### File Type Support

- **Supported:** PDF (50 MB), DOCX, PPTX, HTML, Markdown, TXT
- **Not supported:** Images (PNG, JPG), videos, audio
- See [Google Cloud docs](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/supported-documents) for full list

#### Geographic Restrictions

- RAG Engine available in: `us-east1`, `us-east1`, `europe-west1`, others
- Check [available regions](https://cloud.google.com/vertex-ai/docs/general/locations)

#### Import Latency

- Synchronous workflow not possible (2-5 min minimum)
- Not suitable for rapid KB iteration during development
- Recommendation: Test chunking with small samples, then scale up

---

## Troubleshooting

### Authentication Errors

**Error:** `PermissionDenied: 403 Permission denied`

#### Fix

```bash
gcloud auth application-default login
gcloud auth list  # Verify active account
```text
**Error:** `DefaultCredentialsError: Could not automatically determine credentials`

#### Fix

```bash
gcloud auth application-default login
# Or set env var
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```text
### Import Failures

**Error:** Import starts but no chunks appear after 30 min

#### Fix

- Check GCS bucket permissions: `gsutil ls gs://your-bucket/`
- Verify file format: Only PDF, DOCX, PPTX, etc. supported
- Check file size: Max 50 MB per PDF
- View logs in [Vertex AI Console](https://console.cloud.google.com/vertex-ai/rag)

**Error:** `InvalidArgument: GCS URI must end with /`

#### Fix

```python
# Wrong
rag_kb.import_files("gs://bucket/papers")

# Correct
rag_kb.import_files("gs://bucket/papers/")
```text
### Retrieval Issues

**Problem:** `retrieve()` returns empty list

#### Possible causes

1. Import not complete: Wait 5-10 min after import
2. `similarity_threshold` too high: Lower to 0.5 or 0.6
3. Query mismatch: Try broader query terms
4. Corpus empty: Check file import logs

#### Fix

```python
# Lower threshold temporarily
rag_kb.similarity_threshold = 0.5
results = rag_kb.retrieve("your query")

# Or increase top_k
rag_kb.top_k = 10
results = rag_kb.retrieve("your query")
```text
**Problem:** Retrieved chunks not relevant

#### Possible causes

1. `chunk_size` too large: Chunks contain multiple topics
2. `top_k` too high: Noise drowns signal
3. Query too vague: Make more specific

#### Fix

```python
# Recreate corpus with smaller chunks
rag_kb_new = VertexRAGKnowledgeBase(
    project_id="...",
    corpus_display_name="papers-small-chunks",
    chunk_size=256,  # Smaller for precision
)
```text
### Cost Concerns

**Problem:** Unexpected charges

#### Check

- GCS storage costs: `gsutil du -sh gs://your-bucket/`
- Vector DB storage: View in [Vertex AI Console](https://console.cloud.google.com/vertex-ai/rag)
- Embedding costs: One-time, $0.025 per 1M chars
- Gemini API calls: Standard pricing per interpretation

#### Prevent

- Delete unused corpora: `kanoa vertex rag delete --display-name "old-corpus" --force`
- Set billing alerts in GCP Console
- Monitor via [GCP Billing Reports](https://console.cloud.google.com/billing)

### API Quota Limits

**Error:** `ResourceExhausted: Quota exceeded`

#### Fix

- Embedding quota: 1000 requests/min default, increase in quotas page
- Wait and retry with lower `max_embedding_requests_per_min`:

```python
rag_kb.import_files("gs://bucket/", max_embedding_requests_per_min=500)
```text
---

## Next Steps

- **Test with your data:** Follow [Quick Start](#quick-start) with your GCS bucket
- **Optimize chunking:** Experiment with [chunk_size configurations](#chunking-configuration)
- **Compare costs:** Run [cost analysis](../analysis/20251211-vertex-rag-cost-breakdown.md) for your use case
- **Scale up:** Create multi-corpus workflows for different domains

#### Related Guides

- [Quick Start (GCS only)](vertex-rag-quickstart-gcs.md)
- [Academic Papers Workflow](vertex-rag-academic-papers.md)
- [Cost Breakdown Analysis](../analysis/20251211-vertex-rag-cost-breakdown.md)
- [Implementation Plan](../planning/vertex-rag-gcs-drive-implementation.md)

#### Need Help?

- [GitHub Issues](https://github.com/longhorizonai/kanoa/issues)
- [Google Cloud Vertex AI Docs](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
