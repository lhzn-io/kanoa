# Using Vertex AI RAG Engine with Academic Papers

**Audience:** Researchers, data scientists analyzing academic literature<br>
**Use Case:** Grounding data interpretations in a corpus of 50+ research papers<br>
**Estimated Setup Time:** 15-20 minutes (one-time)<br>
**Cost:** ~$2-5/month for typical usage<br>

---

## Overview

This guide walks through using kanoa's Vertex AI RAG Engine integration to analyze data visualizations with grounding in academic literature. Instead of loading entire PDFs into the context window (expensive and limited), RAG Engine indexes your papers once and retrieves only relevant sections for each query.

#### What You'll Learn

- Setting up a RAG corpus with 50 academic papers
- Storing papers in Google Cloud Storage (GCS)
- Using the corpus to ground data interpretations
- Accessing source citations and grounding metadata

---

## Prerequisites

### 1. Google Cloud Project

You'll need a GCP project with billing enabled. RAG Engine is a Vertex AI feature (not available in AI Studio).

#### Setup

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Create project (or use existing)
gcloud projects create my-research-project --name="Research RAG"
gcloud config set project my-research-project

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com

# Set up authentication
gcloud auth application-default login
```text
#### Cost Estimate

- RAG corpus storage: ~$0.40/month for 50 papers (~200MB)
- Embedding generation (one-time): ~$0.50
- Query costs: ~$0.01 per interpretation with grounding

### 2. Install kanoa with Vertex AI Support

```bash
pip install kanoa[vertexai]
```text
This installs:

- `kanoa` core library
- `google-cloud-aiplatform` SDK for RAG Engine
- `google` GenAI SDK for Gemini

### 3. Organize Your Papers

#### Option A: Upload to Google Cloud Storage (Recommended)

```bash
# Create a GCS bucket
gsutil mb -p my-research-project -l us-east1 gs://my-research-papers

# Upload your papers
gsutil -m cp papers/*.pdf gs://my-research-papers/ml-interpretability/

# Verify upload
gsutil ls gs://my-research-papers/ml-interpretability/
```text
#### Option B: Use Google Drive

Upload papers to a Google Drive folder and note the folder URL:

```text
https://drive.google.com/drive/folders/1aBcD3FgH...
```text
You'll need to share this folder with the RAG Engine service account (shown later).

#### Option C: Local Files (Auto-uploaded)

kanoa can automatically upload local files to a staging bucket:

```python
rag_kb.import_files(Path("/local/research/papers"))
```text
---

## Limitations and Workarounds

### Multimodal Content (Charts, Tables, Diagrams)

#### PDF Processing (as of December 2025)

Vertex AI RAG Engine uses an integrated **layout parser** (Document AI technology) that intelligently processes academic PDFs:

#### What works well for academic papers

- Text extraction preserving document structure (abstracts, sections, references)
- **Table detection and extraction** (experimental results tables are indexed)
- Multi-column paper layouts with correct reading order
- Mathematical notation and equations (as text)
- OCR for scanned papers

#### Current limitations

- **Visual semantics** of charts/plots (trend analysis, pattern recognition)
- **Image understanding** of diagrams (architectural figures, flow charts)
- Cross-referencing figure captions to visual content

**Recommendation:** Best for papers where key results are in tables or text descriptions. For visual analysis of plots/diagrams, use local KB mode with Gemini File API vision.

#### Impact on Academic Papers

For papers with heavy visual content (experimental results, architectural diagrams), consider:

1. **Hybrid approach** (recommended for most use cases):

   ```python
   # Use RAG for literature review and methods grounding
   rag_kb = VertexRAGKnowledgeBase(
       project_id="my-project",
       corpus_display_name="ml-papers-text",
   )
   interp_rag = AnalyticsInterpreter(
       grounding_mode="rag_engine",
       knowledge_base=rag_kb,
   )

   # For visual content, fall back to local KB with Gemini vision
   if needs_chart_comparison:
       interp_local = AnalyticsInterpreter(kb_path="papers/")
       result = interp_local.interpret(
           fig=plot,
           context="Compare to Figure 3 in Smith et al. 2024",
       )
   ```

2. **Full vision mode** (if visual content is critical):

   ```python
   # Use local KB exclusively for full Gemini vision capabilities
   interp = AnalyticsInterpreter(
       backend="gemini",
       kb_path="papers/",  # Local PDFs get Gemini vision
   )
   ```

#### Cost trade-off

- RAG Engine (text-only): $0.38/month for 50 papers
- Local KB (full vision): $21.80/month for 50 papers (frequent queries)

**Future:** Multimodal RAG preprocessing (Phase 2) may enable visual element indexing via Document AI.

---

## Step-by-Step Workflow

### Step 1: Create Your RAG Corpus

This is a **one-time setup** per research project. The corpus persists in GCP until you delete it.

#### Option 1: Using CLI (Recommended)

The easiest way to create and manage your corpus is via the `kanoa` CLI:

```bash
# Create the corpus
kanoa vertex rag create \
    --project "my-research-project" \
    --display-name "ml-interpretability-papers" \
    --region "us-east1"
```text
#### Option 2: Using Python SDK

```python
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# Create RAG knowledge base
# IMPORTANT: project_id and corpus_display_name are REQUIRED
rag_kb = VertexRAGKnowledgeBase(
    # Billing & project settings (REQUIRED)
    project_id="my-research-project",  # Your GCP project ID
    location="us-east1",             # GCP region

    # Corpus identifier (REQUIRED)
    # This name is used to:
    # 1. Reconnect to corpus across sessions
    # 2. Separate KBs for different domains/initiatives
    corpus_display_name="ml-interpretability-papers",

    # Chunking configuration
    chunk_size=512,        # Tokens per chunk (good for academic text)
    chunk_overlap=100,     # Overlap prevents split concepts

    # Retrieval configuration
    top_k=5,               # Retrieve top 5 most relevant chunks
    similarity_threshold=0.7,  # Minimum relevance score (0-1)

    # Embedding model
    embedding_model="text-embedding-005",  # Google's latest
)

# Create the corpus (stores metadata in Vertex AI)
# If corpus with this display_name exists, it will be reused
corpus_name = rag_kb.create_corpus()
print(f"Created corpus: {corpus_name}")
```text
#### Output

```text
Created corpus: projects/my-research-project/locations/us-east1/ragCorpora/1234567890
```text
#### Why These Parameters Are Required

- **`project_id`**: Ensures explicit billing transparency. RAG Engine costs are tied to specific GCP projects. No defaults - you choose where charges go.
- **`corpus_display_name`**: Acts as a logical identifier for your knowledge base. Use descriptive names like "ml-interpretability-papers", "causal-inference-kb", "healthcare-ai-research".

### Step 2: Import Your Papers

Import papers from GCS, Google Drive, or local files:

#### Option A: From Google Cloud Storage (CLI Recommended)

#### Using CLI

```bash
kanoa vertex rag import \
    --project "my-research-project" \
    --display-name "ml-interpretability-papers" \
    --gcs-uri "gs://my-research-papers/ml-interpretability/" \
    --region "us-east1"
```text
#### Using Python

```python
# Import entire folder
rag_kb.import_files("gs://my-research-papers/ml-interpretability/")

# Or import specific files
rag_kb.import_files([
    "gs://my-research-papers/ml-interpretability/LIME_2016.pdf",
    "gs://my-research-papers/ml-interpretability/SHAP_2017.pdf",
    "gs://my-research-papers/ml-interpretability/attention_2017.pdf",
])
```text
#### Option B: From Google Drive

First, share your Drive folder with the RAG Engine service account:

```python
# Get your project number
import subprocess
project_number = subprocess.check_output(
    ["gcloud", "projects", "describe", "my-research-project",
     "--format=value(projectNumber)"]
).decode().strip()

service_account = f"service-{project_number}@gcp-sa-vertex-rag.iam.gserviceaccount.com"

print(f"""
Share your Google Drive folder with this service account:
{service_account}

Grant 'Viewer' access.
""")
```text
Then import:

```python
drive_folder_url = "https://drive.google.com/drive/folders/1aBcD3FgH..."
rag_kb.import_files(drive_folder_url)
```text
#### Option C: From Local Files

```python
from pathlib import Path

# Automatically uploads to staging bucket
rag_kb.import_files([
    Path("/home/user/papers/LIME_2016.pdf"),
    Path("/home/user/papers/SHAP_2017.pdf"),
    # ... add all 50 papers
])
```text
#### Progress Tracking

The import process runs asynchronously. For 50 papers (~200MB), expect 5-10 minutes:

```python
import time

print("Importing papers...")
rag_kb.import_files("gs://my-research-papers/ml-interpretability/")

# Wait for import to complete
time.sleep(30)  # Initial delay

print("Checking import status...")
files = rag_kb.list_files()
print(f"Imported {len(files)} files:")
for file in files[:5]:  # Show first 5
    print(f"  - {file}")
if len(files) > 5:
    print(f"  ... and {len(files) - 5} more")
```text
### Step 3: Analyze Data with Grounded Interpretations

Now use your RAG corpus to ground interpretations in the academic literature:

```python
from kanoa import AnalyticsInterpreter
import pandas as pd
import matplotlib.pyplot as plt

# Create interpreter with RAG grounding
interpreter = AnalyticsInterpreter(
    backend='gemini',
    model='gemini-2.0-flash-exp',  # Fast and cost-effective
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)

# Load your experiment data
df = pd.DataFrame({
    'model': ['Linear', 'Random Forest', 'Neural Net', 'XGBoost'],
    'accuracy': [0.72, 0.85, 0.89, 0.91],
    'interpretability_score': [0.95, 0.65, 0.30, 0.55],
})

# Create visualization
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(
    df['interpretability_score'],
    df['accuracy'],
    s=200,
    alpha=0.6,
    c=['blue', 'green', 'red', 'orange']
)

for i, model in enumerate(df['model']):
    ax.annotate(
        model,
        (df['interpretability_score'][i], df['accuracy'][i]),
        xytext=(5, 5),
        textcoords='offset points'
    )

ax.set_xlabel('Interpretability Score')
ax.set_ylabel('Accuracy')
ax.set_title('Model Performance vs Interpretability Trade-off')
ax.grid(True, alpha=0.3)

plt.tight_layout()

# Interpret with grounding in research papers
result = interpreter.interpret(
    fig=fig,
    data=df,
    context="Machine learning model comparison for credit risk prediction",
    focus="""
    Analyze the accuracy-interpretability trade-off shown in this scatter plot.
    Reference established frameworks (LIME, SHAP, attention mechanisms) from
    the research literature to explain why this trade-off exists and suggest
    approaches to improve interpretability of high-accuracy models.
    """
)

print(result.text)
```text
#### Example Output

```text
The visualization reveals a classic accuracy-interpretability trade-off in machine
learning models for credit risk prediction. This phenomenon is well-documented in
the interpretability literature.

Linear models achieve the highest interpretability score (0.95) but lowest accuracy
(0.72). This aligns with findings from Ribeiro et al. (2016) showing that linear
models provide inherent interpretability through direct feature coefficient inspection.

Neural networks demonstrate the inverse relationship: 0.89 accuracy with only 0.30
interpretability. However, recent work by Lundberg & Lee (2017) on SHAP values and
Vaswani et al. (2017) on attention mechanisms provide post-hoc explanation methods
that can bridge this gap.

For your credit risk use case, I recommend:

1. Deploy XGBoost (0.91 accuracy, 0.55 interpretability) as it offers the best
   balance in your comparison
2. Augment with SHAP explanations (Lundberg & Lee, 2017) to provide local
   feature importance for individual predictions
3. Consider model distillation techniques to create a more interpretable
   approximation of the neural network

The regulatory requirements for credit decisions may favor the Random Forest
(0.85 accuracy, 0.65 interpretability) as a more defensible choice if explainability
is mandated.
```text
### Step 4: Access Grounding Sources

Every interpretation includes citations to the papers used for grounding:

```python
# Check which papers were cited
if result.grounding_sources:
    print("\n" + "="*60)
    print("GROUNDING SOURCES")
    print("="*60)

    for i, source in enumerate(result.grounding_sources, 1):
        print(f"\n{i}. {source.uri}")
        print(f"   Relevance Score: {source.score:.2f}")

        if source.chunk_text:
            # Show snippet of retrieved text
            preview = source.chunk_text[:150].replace("\n", " ")
            print(f"   Preview: {preview}...")
```text
#### Example Output

```text
============================================================
GROUNDING SOURCES
============================================================

1. gs://my-research-papers/ml-interpretability/SHAP_2017.pdf
   Relevance Score: 0.89
   Preview: SHAP (SHapley Additive exPlanations) is a unified approach to
   explain the output of any machine learning model. SHAP connects game theory...

2. gs://my-research-papers/ml-interpretability/LIME_2016.pdf
   Relevance Score: 0.85
   Preview: We propose LIME, a novel explanation technique that explains the
   predictions of any classifier in an interpretable and faithful manner...

3. gs://my-research-papers/ml-interpretability/attention_2017.pdf
   Relevance Score: 0.81
   Preview: The dominant sequence transduction models are based on complex
   recurrent or convolutional neural networks. We propose a new simple network...

4. gs://my-research-papers/ml-interpretability/model_distillation_2015.pdf
   Relevance Score: 0.76
   Preview: A very simple way to improve the performance of almost any machine
   learning algorithm is to train many different models and average their predictions...

5. gs://my-research-papers/ml-interpretability/interpretable_ml_survey_2018.pdf
   Relevance Score: 0.73
   Preview: The aim of interpretable machine learning is to describe the
   internals of a model in a way that is understandable to humans...
```text
### Step 5: Cost Tracking

Monitor usage and costs:

```python
# Check usage for this interpretation
if result.usage:
    print("\n" + "="*60)
    print("USAGE & COST")
    print("="*60)
    print(f"Input tokens:  {result.usage.input_tokens:,}")
    print(f"Output tokens: {result.usage.output_tokens:,}")
    print(f"Cost:          ${result.usage.cost:.4f}")

    if result.usage.cached_tokens:
        print(f"Cached tokens: {result.usage.cached_tokens:,}")
        print(f"Savings:       ${result.usage.savings:.4f}")

# Check cumulative interpreter costs
print(f"\nTotal interpreter cost: ${interpreter.total_cost:.4f}")
```text
#### Example Output

```text
============================================================
USAGE & COST
============================================================
Input tokens:  2,847
Output tokens: 412
Cost:          $0.0089

Total interpreter cost: $0.0089
```text
#### Cost Breakdown

- **Retrieval**: Retrieved 5 chunks (~500 tokens each) = 2,500 tokens
- **Prompt**: Context + focus + figure description = ~300 tokens
- **Output**: Generated interpretation = 412 tokens
- **Total cost**: $0.0089 (less than 1 cent!)

Compare to context stuffing (loading all 50 papers): ~$0.50 per query.

---

## Advanced Usage

### Managing Multiple Knowledge Bases

Researchers often work across multiple domains or initiatives. kanoa supports logical separation of KBs via `corpus_display_name`.

#### Use Case 1: Multiple Research Areas

```python
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# Same GCP project, multiple research domains
PROJECT_ID = "my-research-project"

# ML Interpretability KB
ml_kb = VertexRAGKnowledgeBase(
    project_id=PROJECT_ID,
    corpus_display_name="ml-interpretability",
)
ml_kb.create_corpus()
ml_kb.import_files("gs://my-papers/ml-interpretability/")

# Causal Inference KB
causal_kb = VertexRAGKnowledgeBase(
    project_id=PROJECT_ID,
    corpus_display_name="causal-inference",
)
causal_kb.create_corpus()
causal_kb.import_files("gs://my-papers/causal-inference/")

# Computer Vision KB
cv_kb = VertexRAGKnowledgeBase(
    project_id=PROJECT_ID,
    corpus_display_name="computer-vision",
)
cv_kb.create_corpus()
cv_kb.import_files("gs://my-papers/computer-vision/")
```text
**Billing:** All three KBs share the same GCP project billing account. Total monthly cost ~$5-10 for typical usage.

#### Use Case 2: Client/Project Separation

For consultants or multi-team organizations, use different GCP projects for billing/privacy isolation:

```python
# Client A (separate GCP project & billing)
client_a_kb = VertexRAGKnowledgeBase(
    project_id="client-a-project",  # Different project
    corpus_display_name="market-research",
)
client_a_kb.create_corpus()
client_a_kb.import_files("gs://client-a-data/research/")

# Client B (separate GCP project & billing)
client_b_kb = VertexRAGKnowledgeBase(
    project_id="client-b-project",  # Different project
    corpus_display_name="financial-analysis",
)
client_b_kb.create_corpus()
client_b_kb.import_files("gs://client-b-data/financials/")

# Internal research (your own project)
internal_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",  # Your project
    corpus_display_name="internal-methods",
)
internal_kb.create_corpus()
internal_kb.import_files("gs://my-papers/internal/")
```text
**Billing:** Each client's usage is billed to their respective GCP project. Perfect for chargebacks or client invoicing.

#### Switching Between KBs

Create separate interpreters for each KB:

```python
from kanoa import AnalyticsInterpreter

# Interpreter for ML Interpretability research
ml_interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=ml_kb,
)

# Interpreter for Causal Inference research
causal_interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=causal_kb,
)

# Use the right interpreter for your analysis
result = ml_interpreter.interpret(
    fig=accuracy_plot,
    context="Model accuracy vs interpretability",
    focus="Reference LIME/SHAP frameworks",
)

result = causal_interpreter.interpret(
    fig=treatment_effect_plot,
    context="Treatment effect estimation",
    focus="Reference propensity score matching and IPW methods",
)
```text
Each interpreter retrieves only from its associated corpus, ensuring clean domain separation.

#### Listing All Your Corpora

Audit which KBs exist in a project:

```python
from vertexai import rag
import vertexai

# List all corpora in a project
vertexai.init(project="my-research-project", location="us-east1")

all_corpora = rag.list_corpora()
print("Existing corpora:")
for corpus in all_corpora:
    print(f"  - {corpus.display_name}: {corpus.name}")
```text
#### Output

```text
Existing corpora:
  - ml-interpretability: projects/.../ragCorpora/1234567890
  - causal-inference: projects/.../ragCorpora/9876543210
  - computer-vision: projects/.../ragCorpora/5555555555
```text
#### Cleanup: Deleting Unused Corpora

```python
# Delete specific corpus when no longer needed
old_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",
    corpus_display_name="old-experiment",
)
old_kb.delete_corpus()
print("Corpus 'old-experiment' deleted")

# Saves ~$0.40/month in storage costs per corpus
```text
### Reusing Corpora Across Sessions

Your corpus persists in Vertex AI. Reconnect in a new session:

```python
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

# Reconnect to existing corpus
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",
    location="us-east1",
    corpus_display_name="ml-interpretability-papers",  # Same name
)

# No need to create_corpus() - it already exists
# Just use it directly
from kanoa import AnalyticsInterpreter

interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)
```text
### Tuning Retrieval Quality

Adjust retrieval parameters based on your needs:

```python
# More exhaustive retrieval (higher cost, better coverage)
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",
    corpus_display_name="ml-papers",
    top_k=10,              # Retrieve more chunks
    similarity_threshold=0.5,  # Lower threshold = more permissive
)

# Precision-focused retrieval (lower cost, higher relevance)
rag_kb = VertexRAGKnowledgeBase(
    project_id="my-research-project",
    corpus_display_name="ml-papers",
    top_k=3,               # Fewer chunks
    similarity_threshold=0.85,  # Higher threshold = stricter
)
```text
### Optimizing Chunking Strategy

**Chunking** determines how your PDFs are split into retrievable segments. Understanding chunking is critical for retrieval quality.

#### The Chunking Trade-off

Every chunking decision balances three competing goals:

1. **Semantic Coherence** - Keep complete thoughts together
2. **Retrieval Precision** - Match query granularity for better relevance scores
3. **Computational Efficiency** - Minimize embedding/storage costs

#### Default Settings (Works for Most Academic Papers)

```python
rag_kb = VertexRAGKnowledgeBase(
    chunk_size=512,        # ~2,000 chars = 1-2 paragraphs
    chunk_overlap=100,     # 20% overlap prevents concept splits
)
```text
#### Why these defaults?

- **512 tokens** fits most complete thoughts in academic writing (1-2 paragraphs = single concept)
- **100 token overlap** ensures key sentences appear in multiple chunks, preventing boundary splits

#### When to Adjust Chunking

#### Symptom: Methodology questions return incomplete explanations

Your queries ask for full methods ("Explain the complete SHAP algorithm") but retrieved chunks cut off mid-explanation.

#### Solution: Increase chunk size

```python
chunk_size=640-768,      # Larger chunks capture full method sections
chunk_overlap=128-150,   # Maintain 20% overlap ratio
```text
#### Symptom: Simple definition queries return too much irrelevant context

Your queries are focused ("What is SHAP?") but retrieved chunks include 3-4 unrelated topics, diluting relevance.

#### Solution: Decrease chunk size

```python
chunk_size=384-448,      # Smaller, more focused chunks
chunk_overlap=75-100,    # Maintain 20% overlap ratio
```text
#### Chunking Guidelines by Query Type

| Query Complexity | Example | Optimal Chunk Size |
|------------------|---------|-------------------|
| **Simple definitions** | "What is SHAP?" | 256-384 tokens |
| **Moderate explanations** | "How does LIME work?" | 512 tokens (DEFAULT) |
| **Full methodologies** | "Describe complete attention mechanism" | 768-1024 tokens |

#### Overlap Guidelines

- **0% overlap**: Only for independent content (FAQs) - NOT for academic papers
- **10-15%**: Loose connections (news articles)
- **20-25%**: Structured documents like papers (**RECOMMENDED**)
- **30-40%**: Dense cross-references (legal docs, specs)

**Why overlap matters:** Without overlap, important sentences at chunk boundaries get split:

- Chunk 1: "The study found that SHAP"
- Chunk 2: "outperforms LIME in all scenarios"
- Neither chunk makes sense alone!

#### Cost Impact of Chunking

Chunking affects embedding costs (one-time) and storage costs (ongoing):

| Config | Chunks (50 papers) | Embedding Cost | Monthly Storage |
|--------|-------------------|----------------|-----------------|
| Small (384/75) | ~140 chunks | $0.07 | $0.42 |
| **Default (512/100)** | **~100 chunks** | **$0.05** | **$0.30** |
| Large (768/150) | ~130 chunks | $0.065 | $0.39 |

**Key insight:** Extreme sizes cost more due to fragmentation (small) or redundancy (large). Defaults are optimal for most cases.

#### Experimentation Workflow

1. **Start with defaults** (512/100) for 2-3 weeks
2. **Collect failure cases**: Track queries with poor/incomplete results
3. **Analyze pattern**:
   - Mostly simple definitions failing? → Try 384/75
   - Mostly methodology questions failing? → Try 640/128
   - Mixed failures? → Adjust `top_k` instead of chunk size
4. **Measure impact**: Compare relevance scores before/after change

#### When to Keep Defaults

For 50 academic papers on ML interpretability, **512/100 is optimal** if your queries include:

- Mix of simple and complex questions
- Typical paragraph-level concepts (most papers)
- Standard academic writing structure

**Only adjust if** you observe consistent failures in a specific query category after testing with real usage patterns.

#### Advanced: Domain-Specific Chunking

#### Papers with complex figures/tables

```python
# Use Document AI Layout Parser (future feature)
# Extracts figures separately for better grounding
chunk_size=512,
use_layout_parser=True,
```text
#### Multi-language corpora

```python
# Adjust for language (Chinese ~2 chars/token vs English ~4)
chunk_size=256,  # Same character count as English 512
chunk_overlap=50,
```text
### Adding New Papers to Existing Corpus

```python
# Import additional papers without recreating corpus
rag_kb.import_files([
    "gs://my-research-papers/new-batch/transformers_2023.pdf",
    "gs://my-research-papers/new-batch/llm_interpretability_2024.pdf",
])

# Verify
all_files = rag_kb.list_files()
print(f"Corpus now contains {len(all_files)} papers")
```text
### Corpus Management

```python
# List all files in corpus
files = rag_kb.list_files()
for file in files:
    print(file)

# Delete specific files (if needed)
# Note: Vertex AI RAG API v1 doesn't support individual file deletion
# To remove files, you must recreate the corpus

# Delete entire corpus
rag_kb.delete_corpus()
print("Corpus deleted")

# Recreate fresh corpus
rag_kb.create_corpus(force_recreate=True)
rag_kb.import_files("gs://my-research-papers/ml-interpretability/")
```text
### Hybrid Mode: RAG + Context Stuffing

For critical analyses, combine RAG retrieval with direct PDF loading:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='hybrid',  # Use both strategies
    rag_corpus=rag_kb,
    kb_path='./key-papers',   # Also load these 2-3 papers directly
)
```text
**Use Case:** RAG retrieves from 50-paper corpus, plus 2-3 critical papers loaded entirely for maximum detail.

---

## Complete Example Notebook

Here's a full Jupyter notebook workflow:

```python
# %% Cell 1: Setup
from kanoa import AnalyticsInterpreter
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ID = "my-research-project"
LOCATION = "us-east1"

# %% Cell 2: Create RAG Corpus (ONE-TIME SETUP)
rag_kb = VertexRAGKnowledgeBase(
    project_id=PROJECT_ID,
    location=LOCATION,
    corpus_display_name="ml-interpretability-papers",
    chunk_size=512,
    chunk_overlap=100,
    top_k=5,
    similarity_threshold=0.7,
)

corpus_name = rag_kb.create_corpus()
print(f"Created corpus: {corpus_name}")

# %% Cell 3: Import Papers (ONE-TIME SETUP)
rag_kb.import_files("gs://my-research-papers/ml-interpretability/")

import time
time.sleep(30)  # Wait for import

files = rag_kb.list_files()
print(f"Imported {len(files)} papers")

# %% Cell 4: Create Interpreter
interpreter = AnalyticsInterpreter(
    backend='gemini',
    model='gemini-2.0-flash-exp',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)

# %% Cell 5: Load Experiment Data
df = pd.DataFrame({
    'model': ['Linear', 'Random Forest', 'Neural Net', 'XGBoost'],
    'accuracy': [0.72, 0.85, 0.89, 0.91],
    'interpretability_score': [0.95, 0.65, 0.30, 0.55],
})

df

# %% Cell 6: Create Visualization
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(
    df['interpretability_score'],
    df['accuracy'],
    s=200,
    alpha=0.6,
    c=['blue', 'green', 'red', 'orange']
)

for i, model in enumerate(df['model']):
    ax.annotate(
        model,
        (df['interpretability_score'][i], df['accuracy'][i]),
        xytext=(5, 5),
        textcoords='offset points'
    )

ax.set_xlabel('Interpretability Score')
ax.set_ylabel('Accuracy')
ax.set_title('Model Performance vs Interpretability Trade-off')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# %% Cell 7: Interpret with Grounding
result = interpreter.interpret(
    fig=fig,
    data=df,
    context="Machine learning model comparison for credit risk prediction",
    focus="""
    Analyze the accuracy-interpretability trade-off. Reference frameworks
    like LIME, SHAP, and attention mechanisms from the literature.
    Suggest approaches to improve interpretability of high-accuracy models.
    """
)

print(result.text)

# %% Cell 8: Review Grounding Sources
if result.grounding_sources:
    print("\nGROUNDING SOURCES")
    print("="*60)
    for i, source in enumerate(result.grounding_sources, 1):
        print(f"\n{i}. {source.uri}")
        print(f"   Relevance: {source.score:.2f}")

# %% Cell 9: Check Costs
if result.usage:
    print("\nUSAGE & COST")
    print("="*60)
    print(f"Input tokens:  {result.usage.input_tokens:,}")
    print(f"Output tokens: {result.usage.output_tokens:,}")
    print(f"Cost:          ${result.usage.cost:.4f}")
    print(f"\nTotal session cost: ${interpreter.total_cost:.4f}")
```text
---

## Troubleshooting

### Error: "Permission denied" when importing from Google Drive

**Cause:** Drive folder not shared with RAG Engine service account.

#### Solution

1. Get your project number:

   ```bash
   gcloud projects describe my-research-project --format="value(projectNumber)"
   ```

2. Service account format:

   ```text
   service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
   ```

3. Share Drive folder with this email address, grant "Viewer" role

4. Wait 1-2 minutes for permissions to propagate

5. Retry import

### Error: "Corpus not found" when reconnecting

**Cause:** Corpus was deleted or display name doesn't match.

#### Solution

List all corpora in your project:

```python
from vertexai import rag
import vertexai

vertexai.init(project="my-research-project", location="us-east1")

# List existing corpora
corpora = rag.list_corpora()
for corpus in corpora:
    print(f"Display name: {corpus.display_name}")
    print(f"Resource name: {corpus.name}")
    print()
```text
Use exact `display_name` when reconnecting.

### Slow Import Performance

**Cause:** Large PDFs or network latency.

#### Solution

- Use GCS in same region as Vertex AI (e.g., both in `us-east1`)
- Import in batches of 10-20 papers
- Monitor progress with `list_files()`

### Low Retrieval Relevance

**Symptom:** Grounding sources have low scores (<0.5) or seem off-topic.

#### Solutions

1. **Lower similarity threshold:**

   ```python
   similarity_threshold=0.5  # Instead of 0.7
   ```

2. **Increase top_k:**

   ```python
   top_k=10  # Retrieve more chunks
   ```

3. **Adjust chunk size:**

   ```python
   chunk_size=256  # Smaller chunks = more granular matching
   ```

4. **Refine focus prompt:**
   - Be more specific about desired citations
   - Use paper titles/authors if known
   - Include domain-specific terminology

### Unexpected Costs

#### Check usage metadata

```python
# Enable detailed cost tracking
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
    verbose=1,  # Show token counts
)

result = interpreter.interpret(...)

# Review breakdown
print(f"Input tokens: {result.usage.input_tokens:,}")
print(f"Output tokens: {result.usage.output_tokens:,}")
```text
#### Cost reduction tips

- Use `gemini-2.0-flash-exp` instead of `gemini-2.0-pro`
- Reduce `top_k` to retrieve fewer chunks
- Increase `similarity_threshold` to skip low-relevance chunks
- Use shorter `focus` prompts

---

## Best Practices

### 1. Corpus Organization

#### Do

- One corpus per research domain (e.g., "ml-interpretability", "healthcare-ai")
- 20-100 papers per corpus (sweet spot for performance)
- Use descriptive, kebab-case `corpus_display_name` (you'll reuse it)
  - Good: `"ml-interpretability"`, `"causal-inference-2024"`, `"client-acme-legal"`
  - Bad: `"corpus1"`, `"test"`, `"My Papers!!!"`, `"kb_final_FINAL_v2"`
- Include version/year if corpus content changes over time
  - `"ml-survey-2024"` vs `"ml-survey-2025"`
  - Allows comparing interpretations against different literature snapshots

#### Don't

- Mix unrelated research areas in one corpus (degrades retrieval precision)
- Create separate corpora for slight variations (wasteful - just add files incrementally)
- Use special characters or spaces in corpus names (stick to alphanumeric + hyphens)
- Reuse corpus names across different projects (causes confusion when reconnecting)

#### Multi-Project/Multi-Initiative Naming Convention

```python
# Pattern: {project|client}-{domain}-{optional-version}

# Personal research
"ml-interpretability"
"causal-inference"
"healthcare-nlp"

# Client work (different GCP projects)
project_id="client-acme-project"
corpus_display_name="acme-market-research"

project_id="client-beta-project"
corpus_display_name="beta-financial-analysis"

# Team-based (same GCP project, logical separation)
project_id="company-research-project"
corpus_display_name="data-science-papers"
corpus_display_name="product-analytics-kb"
corpus_display_name="ml-platform-docs"
```text
### 2. Paper Preparation

#### Do

- Use clean, text-searchable PDFs (not scanned images)
- Include full papers with references
- Organize in GCS folders by topic

#### Don't

- Include presentation slides (low information density)
- Use PDFs with DRM restrictions
- Include duplicate papers

### 3. Query Design

#### Do

- Reference specific concepts you expect in papers
- Use domain terminology (e.g., "SHAP values", "attention mechanisms")
- Ask for citations explicitly in `focus` parameter

#### Don't

- Ask generic questions unrelated to corpus content
- Assume model knows your papers without retrieval
- Expect verbatim quotes (chunks are paraphrased)

### 4. Cost Management

#### Do

- Reuse corpora across sessions (one-time import cost)
- Start with `gemini-2.0-flash-exp` (10x cheaper than Pro)
- Monitor `total_cost` attribute on interpreter

#### Don't

- Recreate corpus for every experiment
- Use `top_k=20` unless necessary
- Ignore retrieval quality (low scores = wasted tokens)

---

## Cost Comparison: RAG vs Context Stuffing

**Scenario:** 50 academic papers (~10MB, ~500K tokens total), 100 interpretations per month

### Context Stuffing (Current kanoa Default)

| Item | Cost |
|------|------|
| Cache creation (first query) | $2.00 |
| Cache reads (99 queries) | $19.80 |
| **Monthly total** | **$21.80** |

#### Limitations

- Limited to ~200K tokens (40 papers max with Gemini 2M context)
- Loads entire corpus even if only 1-2 papers relevant
- Cache expires after 1 hour (frequent reloads)

### RAG Engine (Proposed)

| Item | Cost |
|------|------|
| Corpus creation (one-time) | $0.50 |
| Storage (per month) | $0.40 |
| Embeddings (one-time) | $0.50 |
| Retrieval (100 queries × 5 chunks) | $0.50 |
| Gemini calls (100 × ~500 tokens) | $1.00 |
| **First month total** | **$2.90** |
| **Subsequent months** | **$1.90** |

#### Benefits

- Scales to 1000s of papers (no context limit)
- Retrieves only relevant sections (efficient)
- Persistent corpus (no expiration)
- Source attribution included

**Savings: 87-91%** for typical research workflows.

---

## Next Steps

1. **Set up GCP project** and enable Vertex AI APIs
2. **Upload papers to GCS** (or organize in Google Drive)
3. **Create your first corpus** following Step 1
4. **Import papers** following Step 2
5. **Run your first grounded interpretation** following Step 3

#### Need Help?

- Documentation: [docs.lhzn.io/kanoa](https://kanoa.docs.lhzn.io)
- Issues: [github.com/lhzn-io/kanoa/issues](https://github.com/lhzn-io/kanoa/issues)
- Discussions: [github.com/lhzn-io/kanoa/discussions](https://github.com/lhzn-io/kanoa/discussions)

---

**Last Updated:** December 11, 2025<br>
**Feature Status:** Planned for Phase 1.1 (4-6 week timeline)<br>
**Feedback Welcome:** This is a draft guide for a not-yet-implemented feature. Your feedback on the workflow and API design is valuable!
