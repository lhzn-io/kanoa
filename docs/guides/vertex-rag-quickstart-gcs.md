# Vertex AI RAG Engine Quick Start (GCS Test)

**Goal:** Get a working RAG corpus with 5-10 PDFs in under 10 minutes<br>
**Use Case:** Testing/validation before full implementation<br>
**Minimal Setup:** GCS bucket + PDFs only (no Drive complexity)<br>

---

## Prerequisites

- GCP organization account
- `gcloud` CLI installed
- 5-10 test PDFs (research papers, documentation, etc.)

---

## Step 1: Create Dedicated GCP Project (2 min)

```bash
# Set your org ID (find at console.cloud.google.com/iam-admin/settings)
ORG_ID="123456789012"  # Replace with your org ID

# Create dedicated test project
PROJECT_ID="kanoa-rag-test-$(date +%s)"
gcloud projects create $PROJECT_ID \
  --organization=$ORG_ID \
  --name="kanoa RAG Engine Test"

# Set as active project
gcloud config set project $PROJECT_ID

# Link billing account (required for Vertex AI)
# Find your billing account: gcloud billing accounts list
BILLING_ACCOUNT="01ABCD-234567-89ABCD"  # Replace with your billing account
gcloud billing projects link $PROJECT_ID \
  --billing-account=$BILLING_ACCOUNT

echo "OK: Created project: $PROJECT_ID"
```

**Alternative:** Use existing project if you have one:

```bash
PROJECT_ID="your-existing-project"
gcloud config set project $PROJECT_ID
```

---

## Step 2: Enable Required APIs (1 min)

```bash
# Enable Vertex AI and Cloud Storage
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com

# Verify
gcloud services list --enabled | grep -E "aiplatform|storage"

echo "OK: APIs enabled"
```

---

## Step 3: Create GCS Bucket & Upload PDFs (3 min)

```bash
# Create bucket in same region as Vertex AI (recommended: us-east1)
BUCKET_NAME="${PROJECT_ID}-rag-papers"
gsutil mb -p $PROJECT_ID -l us-east1 gs://$BUCKET_NAME

# Upload your test PDFs
# Option A: Upload from local directory
gsutil -m cp ~/Downloads/test-papers/*.pdf gs://$BUCKET_NAME/papers/

# Option B: Upload individual files
gsutil cp paper1.pdf gs://$BUCKET_NAME/papers/
gsutil cp paper2.pdf gs://$BUCKET_NAME/papers/

# Verify upload
gsutil ls gs://$BUCKET_NAME/papers/

echo "OK: Uploaded PDFs to gs://$BUCKET_NAME/papers/"
```

#### Recommended Test Papers

- 5-10 PDFs, each 1-5 MB
- Text-searchable (not scanned images)
- Related topic (e.g., all ML papers, all healthcare papers)

---

## Step 4: Set Up Authentication (1 min)

```bash
# Set up Application Default Credentials (ADC)
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token > /dev/null && echo "OK: ADC configured"
```

**Important:** This allows local Python scripts to authenticate as you with your GCP permissions.

---

## Step 5: Install kanoa with Vertex AI Support (1 min)

```bash
# Once implemented, this will be
pip install kanoa[vertexai]

# For now (pre-implementation), install dependencies manually
pip install google-cloud-aiplatform
```

---

## Step 6: Test RAG Corpus Creation (CLI)

Instead of writing Python scripts, you can use the `kanoa` CLI to manage your RAG corpus.

#### 1. Create the Corpus

```bash
kanoa vertex rag create \
    --project $PROJECT_ID \
    --display-name "test-papers-kb" \
    --region $LOCATION
```

#### 2. Import Files from GCS

```bash
kanoa vertex rag import \
    --project $PROJECT_ID \
    --display-name "test-papers-kb" \
    --gcs-uri "gs://${BUCKET_NAME}/papers/" \
    --region $LOCATION
```

#### 3. Verify Retrieval (Interactive Chat)

Once the import is complete (it may take a few minutes), you can test retrieval interactively:

```bash
kanoa vertex rag chat \
    --project $PROJECT_ID \
    --display-name "test-papers-kb" \
    --region $LOCATION
```

This will open a chat session where you can ask questions about your documents.

---

## Step 7: Clean Up

When you are done, you can delete the corpus to avoid storage charges:

```bash
kanoa vertex rag delete \
    --project $PROJECT_ID \
    --display-name "test-papers-corpus" \
    --region $LOCATION
```

<!-- Old Python script removed -->
<!--
```python
"""
Minimal RAG Engine test script.
Tests corpus creation and file import from GCS.
"""

from vertexai import rag
import vertexai
import time

# Configuration
PROJECT_ID = "kanoa-rag-test-1234567890"  # Replace with your project
LOCATION = "us-east1"
GCS_URI = "gs://kanoa-rag-test-1234567890-rag-papers/papers/"  # Replace

# Initialize Vertex AI
print(f"Initializing Vertex AI (project: {PROJECT_ID}, region: {LOCATION})...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Create RAG corpus
print("\nCreating RAG corpus...")
embedding_model_config = rag.RagEmbeddingModelConfig(
    vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
        publisher_model="publishers/google/models/text-embedding-005"
    )
)

corpus = rag.create_corpus(
    display_name="test-papers-corpus",
    backend_config=rag.RagVectorDbConfig(
        rag_embedding_model_config=embedding_model_config
    ),
)

print(f"OK: Corpus created: {corpus.name}")

# Import files from GCS
print(f"\nImporting files from {GCS_URI}...")
rag.import_files(
    corpus.name,
    [GCS_URI],  # List of URIs
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(
            chunk_size=512,
            chunk_overlap=100,
        ),
    ),
    max_embedding_requests_per_min=1000,
)

print("OK: Import started (async operation)")
print("  Note: Import runs in background. May take 2-5 minutes for 10 PDFs.")

# Wait for import to complete
print("\nWaiting 30 seconds for import to process...")
time.sleep(30)

# List imported files
print("\nListing imported files...")
try:
    # Note: list_files() may not be immediately available in all SDK versions
    # Fallback: use retrieval_query to test if corpus is working
    response = rag.retrieval_query(
        rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
        text="test query",
        rag_retrieval_config=rag.RagRetrievalConfig(top_k=1),
    )
    print(f"OK: Corpus is operational (retrieved {len(response.contexts.contexts)} chunks)")
except Exception as e:
    print(f"⚠ Could not verify import yet: {e}")
    print("  Try again in 2-3 minutes if import is still processing")

# Test retrieval
print("\n" + "="*60)
print("Testing semantic retrieval...")
print("="*60)

test_query = "machine learning interpretability"  # Adjust to your papers' topic

response = rag.retrieval_query(
    rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
    text=test_query,
    rag_retrieval_config=rag.RagRetrievalConfig(
        top_k=3,
        filter=rag.Filter(vector_distance_threshold=0.5),
    ),
)

print(f"\nQuery: '{test_query}'")
print(f"Retrieved {len(response.contexts.contexts)} chunks:\n")

for i, context in enumerate(response.contexts.contexts, 1):
    print(f"{i}. Score: {context.score:.3f}")
    print(f"   Source: {context.source_uri if hasattr(context, 'source_uri') else 'N/A'}")
    print(f"   Text preview: {context.text[:150]}...")
    print()

print("="*60)
print("OK: RAG Engine test complete!")
print("="*60)

# Cleanup instructions
print(f"\nTo delete this test corpus:")
print(f"  rag.delete_corpus(name='{corpus.name}')")
print(f"\nTo delete GCS bucket:")
print(f"  gsutil rm -r gs://{GCS_URI.split['/'](2)}")
print(f"\nTo delete test project:")
print(f"  gcloud projects delete {PROJECT_ID}")
```

Run the test:

```bash
python test_rag.py
```

#### Expected Output

```
Initializing Vertex AI (project: kanoa-rag-test-1234567890, region: us-east1)...

Creating RAG corpus...
OK: Corpus created: projects/123456/locations/us-east1/ragCorpora/789012

Importing files from gs://kanoa-rag-test-1234567890-rag-papers/papers/...
OK: Import started (async operation)
  Note: Import runs in background. May take 2-5 minutes for 10 PDFs.

Waiting 30 seconds for import to process...

Listing imported files...
OK: Corpus is operational (retrieved 1 chunks)

============================================================
Testing semantic retrieval...
============================================================

Query: 'machine learning interpretability'
Retrieved 3 chunks:

1. Score: 0.847
   Source: gs://kanoa-rag-test-1234567890-rag-papers/papers/SHAP_2017.pdf
   Text preview: SHAP (SHapley Additive exPlanations) is a unified approach to explain the output of any machine learning model. SHAP connects game theory with local...

2. Score: 0.821
   Source: gs://kanoa-rag-test-1234567890-rag-papers/papers/LIME_2016.pdf
   Text preview: We propose LIME, a novel explanation technique that explains the predictions of any classifier in an interpretable and faithful manner by learning an...

3. Score: 0.795
   Source: gs://kanoa-rag-test-1234567890-rag-papers/papers/attention_2017.pdf
   Text preview: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration...

============================================================
OK: RAG Engine test complete!
============================================================
```

---

## Step 7: Test with kanoa (Once Implemented)

After implementing `VertexRAGKnowledgeBase`, test the kanoa integration:

```python
from kanoa import AnalyticsInterpreter
from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase
import matplotlib.pyplot as plt

# Create RAG knowledge base
rag_kb = VertexRAGKnowledgeBase(
    project_id="kanoa-rag-test-1234567890",  # Your test project
    location="us-east1",
    corpus_display_name="test-papers-corpus",
)

# Create corpus and import files
rag_kb.create_corpus()
rag_kb.import_files("gs://kanoa-rag-test-1234567890-rag-papers/papers/")

# Wait for import
import time
time.sleep(60)

# Create interpreter with RAG grounding
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='rag_engine',
    rag_corpus=rag_kb,
)

# Test interpretation
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [0.72, 0.85, 0.89, 0.91])
ax.set_title("Model Accuracy Over Time")
ax.set_xlabel("Iteration")
ax.set_ylabel("Accuracy")

result = interpreter.interpret(
    fig=fig,
    context="Machine learning model improvement experiment",
    focus="Explain the accuracy improvement curve using concepts from the research literature"
)

print(result.text)
print("\nGrounding Sources:")
for source in result.grounding_sources:
    print(f"  - {source.uri} (score: {source.score:.2f})")
```

---

## Cleanup (After Testing)

```bash
# Delete RAG corpus (via Python)
python -c "
from vertexai import rag
import vertexai

PROJECT_ID = 'kanoa-rag-test-1234567890'
CORPUS_NAME = 'projects/.../ragCorpora/...'  # From test output

vertexai.init(project=PROJECT_ID, location='us-east1')
rag.delete_corpus(name=CORPUS_NAME)
print('OK: Corpus deleted')
"

# Delete GCS bucket
gsutil rm -r gs://kanoa-rag-test-1234567890-rag-papers

# Delete entire test project (removes all resources and billing)
gcloud projects delete kanoa-rag-test-1234567890

echo "OK: Cleanup complete"
```

---

## Troubleshooting

### Error: "API not enabled"

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### Error: "Permission denied" on GCS bucket

```bash
# Verify project ownership
gcloud projects get-iam-policy $PROJECT_ID

# Add yourself as owner if needed
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:your-email@gmail.com" \
  --role="roles/owner"
```

### Error: "Billing not enabled"

Link billing account to project:

```bash
gcloud billing accounts list
gcloud billing projects link $PROJECT_ID --billing-account=<ACCOUNT_ID>
```

### Import takes too long (>10 minutes)

- Check file sizes: Large PDFs (>50 MB) take longer
- Check file count: 100+ files may take 20-30 minutes
- Monitor progress: Use Cloud Console → Vertex AI → RAG Engine

### Low retrieval scores (<0.5)

- Check query relevance: Does query match paper topics?
- Check PDF quality: Are PDFs text-searchable (not scanned images)?
- Adjust threshold: Lower `vector_distance_threshold` to 0.3

---

## Cost Estimate (Test Project)

For a 2-hour testing session with 10 PDFs:

| Item | Cost |
|------|------|
| GCS storage (10 PDFs, 50 MB) | $0.001 |
| Embedding generation (one-time) | $0.05 |
| RAG corpus storage (1 day) | $0.01 |
| Test queries (10 retrievals) | $0.01 |
| Gemini calls (10 interpretations) | $0.05 |
| **Total** | **~$0.13** |

**Recommendation:** Delete project after testing to avoid ongoing storage costs.

---

## Next Steps

Once this basic test works:

1. **Validate kanoa integration** with the `VertexRAGKnowledgeBase` class
2. **Understand chunking strategy** - Read [Optimizing Chunking Strategy](vertex-rag-academic-papers.md#optimizing-chunking-strategy) in the full user guide to learn how chunk size affects retrieval quality
3. **Test multi-KB workflow** with 2-3 different corpora
4. **Benchmark costs** vs context stuffing with your real workloads
5. **Test Drive integration** if you need Drive support
6. **Move to production project** once validated

#### Recommended Reading

- **[Using Vertex AI RAG Engine with Academic Papers](vertex-rag-academic-papers.md)** - Complete user guide with 50-paper workflow, multi-KB management, and best practices
- **[Chunking Strategy Section](vertex-rag-academic-papers.md#optimizing-chunking-strategy)** - Learn when and how to tune chunk size/overlap for your domain

---

## Validation Checklist

- [ ] GCP project created with billing enabled
- [ ] Vertex AI and Storage APIs enabled
- [ ] GCS bucket created and PDFs uploaded
- [ ] ADC authentication configured
- [ ] RAG corpus created successfully
- [ ] Files imported (check after 2-3 min)
- [ ] Semantic retrieval returns relevant chunks (score >0.7)
- [ ] Grounding sources match query intent
- [ ] Cleanup completed (project/bucket deleted)

---

**Document Status:** Ready for testing<br>
**Prerequisites:** Requires google-cloud-aiplatform SDK<br>
**Test Duration:** 10-15 minutes (excluding import wait time)<br>

**Feedback:** This is the minimal path for validating RAG Engine before full kanoa integration. Report issues to [github.com/lhzn-io/kanoa/issues](https://github.com/lhzn-io/kanoa/issues)
