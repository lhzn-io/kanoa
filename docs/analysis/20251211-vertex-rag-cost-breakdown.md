# Vertex AI RAG Engine: Complete Cost Breakdown

**Date:** December 11, 2025<br>
**Purpose:** Detailed cost analysis for GCS-based RAG with Vertex AI RAG Engine<br>

---

## TL;DR Cost Structure

**Good News:** Vertex AI RAG Engine itself is **FREE**. You only pay for underlying infrastructure:

1. ** **GCS Storage**: $0.020/GB/month (one-time upload, ongoing storage)
2. ** **Embedding Generation**: $0.025/1M tokens (one-time indexing cost)
3. ** **Vector DB Storage**: ~$0.30-0.50/GB/month (Spanner-backed)
4. ** **NO per-query fees** (retrieval is included in vector DB cost)
5. ** **NO mileage-based costs** for queries (unlimited retrievals)

#### Total for 50 PDFs (~200MB, ~500K tokens)

- **Setup (one-time)**: ~$0.50
- **Monthly ongoing**: ~$0.40-0.60
- **Per interpretation**: ~$0.005-0.01 (Gemini call only)

---

## Detailed Cost Dimensions

### 1. GCS Storage (Source PDFs)

#### What You're Charged For

- Storing original PDF files in your GCS bucket
- Billed per GB per month

#### Pricing (US Regions - Standard Storage)

- **$0.020/GB/month** (us-central1, us-east1, etc.)
- **$0.026/GB/month** (multi-region)

#### Example

- 50 PDFs, 4 MB each = 200 MB = 0.2 GB
- Cost: `0.2 GB × $0.020 = $0.004/month`

#### Key Points

- ** **One-time upload** (free ingress to GCS)
- ** **No download fees** when RAG Engine reads files (internal GCP traffic)
- ** **Ongoing cost** as long as files remain in bucket
- WARNING: **Tip**: Delete test PDFs after validation to avoid lingering costs

#### No Mileage Costs

- Reading PDFs from GCS for indexing = **FREE** (internal GCP traffic)
- RAG Engine accessing GCS files = **FREE** (no egress charges)

---

### 2. Embedding Generation (One-Time Indexing)

#### What You're Charged For

- Converting document text into vector embeddings
- Billed per character (Google uses characters, not tokens)

#### Pricing (text-embedding-005)

- **$0.025/1M characters** (official Vertex AI pricing)
- Approximately **$0.025/250K tokens** (using 4 chars/token estimate)

#### Example

- 50 PDFs, ~10K tokens each = 500K tokens total
- Characters: `500K tokens × 4 = 2M characters`
- Cost: `2M chars × ($0.025/1M) = $0.05`

#### Key Points

- ** **One-time cost** when importing files to corpus
- ** **No re-indexing charges** for queries (embeddings are stored)
- WARNING: **Incremental cost** when adding new PDFs to existing corpus
- 💡 **Chunking impact**: 512-token chunks with 100 overlap = ~20% more embeddings than raw tokens

#### Per-PDF Indexing Cost

- Small paper (5K tokens): ~$0.0005 (half a cent)
- Medium paper (15K tokens): ~$0.0015
- Large paper (50K tokens): ~$0.005

#### No Mileage Costs

- Query embeddings are included in retrieval (see below)

---

### 3. Vector Database Storage (Ongoing)

#### What You're Charged For

- Storing vector embeddings in Vertex AI RAG Engine's managed database
- Backed by Cloud Spanner (Google's distributed database)

#### Pricing

#### RagManagedDb (Default - Recommended)

- **Basic Tier**: 100 processing units + backup
  - ~$0.30-0.50/GB/month (estimated based on Spanner pricing)
  - Suitable for <10GB vector data
- **Scaled Tier**: 1,000+ processing units + autoscaling
  - Starts at 1 node, scales to 10 nodes
  - Higher throughput for production workloads

#### Spanner Pricing Reference

- Regional: $0.90/node/hour (~$648/month per node)
- Multi-regional: $3.00/node/hour (~$2,160/month per node)
- Storage: $0.30/GB/month

#### Example (50 PDFs with text-embedding-005)

- 500K tokens → 2M characters
- Vector dimensions: 768 (for text-embedding-005)
- Estimated vector storage: ~50-100 MB
- Cost: **~$0.30-0.40/month** (Basic Tier sufficient)

#### Key Points

- ** **Managed service** (no provisioning, scaling automatic)
- ** **Includes backups** (no separate backup charges)
- ** **NO per-query charges** (unlimited retrievals included in DB cost)
- 💡 **Scales with corpus size**, not query volume

#### No Mileage Costs

- Query processing is included in DB tier pricing
- Unlimited semantic searches per month

---

### 4. Retrieval/Query Costs

#### What You're Charged For

- **NOTHING** (included in vector DB storage cost)

#### Pricing

- **$0.00/query** for semantic retrieval
- Query embedding generation: Included in vector DB tier

#### Key Points

- ** **Unlimited queries** per month (no mileage fees!)
- ** **retrieveContexts API** is free (no LLM invocation)
- WARNING: **Only pay for Gemini calls** when using retrieved chunks for generation

#### Example

- 1,000 queries/month: **$0.00**
- 10,000 queries/month: **$0.00**
- 100,000 queries/month: **$0.00**

#### This is a HUGE advantage over alternatives

- OpenAI Assistants: $0.20/GB/day retrieval
- Pinecone: $0.095/1M queries
- Vertex AI RAG Engine: **FREE**

---

### 5. Gemini Generation (Per Interpretation)

#### What You're Charged For

- LLM calls using retrieved chunks for grounded generation
- Billed per token (input + output)

#### Pricing (Gemini Models)

| Model | Input (≤128K ctx) | Input (>128K ctx) | Output | Cached Input |
|-------|-------------------|-------------------|--------|--------------|
| gemini-2.0-flash-exp | $0.075/1M | $0.15/1M | $0.30/1M | $0.01875/1M |
| gemini-2.5-flash | $0.075/1M | $0.15/1M | $0.30/1M | $0.01875/1M |
| gemini-2.5-pro | $1.25/1M | $2.50/1M | $5.00/1M | $0.3125/1M |

#### Example (Single Interpretation)

- Retrieved chunks: 5 × 500 tokens = 2,500 tokens
- System prompt + context: 500 tokens
- Output: 400 tokens
- **Total**: 3,000 input + 400 output = 3,400 tokens
- **Cost (gemini-2.0-flash-exp)**: `(3K × $0.075/1M) + (400 × $0.30/1M) = $0.000345`

#### With Context Caching (for repeated queries)

- First query: $0.000345
- Subsequent queries (cached prompt): `(500 new × $0.075/1M) + (2.5K cached × $0.01875/1M) + (400 out × $0.30/1M) = $0.000205`

#### Key Points

- ** **Only cost that scales with query volume**
- ** **Much cheaper than context stuffing** (2.5K vs 500K tokens)
- 💡 **Use flash models** for cost efficiency (10x cheaper than Pro)

---

## Complete Cost Scenario: 50 Academic Papers

### Setup

#### One-Time Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Upload PDFs to GCS | Free (ingress) | $0.00 |
| Generate embeddings | 2M chars × $0.025/1M | $0.05 |
| Create RAG corpus | Free (Vertex AI RAG Engine) | $0.00 |
| **Total Setup** | | **$0.05** |

### Monthly Recurring Costs

| Item | Calculation | Cost |
|------|-------------|------|
| GCS storage (200 MB) | 0.2 GB × $0.020/GB | $0.004 |
| Vector DB (Basic Tier) | ~50-100 MB vectors | $0.35 |
| **Total Monthly** | | **$0.354** |

### Per-Interpretation Costs

#### Scenario: 100 interpretations/month

| Item | Per Query | 100 Queries |
|------|-----------|-------------|
| RAG retrieval | $0.00 | $0.00 |
| Gemini call (flash) | $0.000345 | $0.0345 |
| **Total** | **$0.000345** | **$0.0345** |

### Grand Total (First Month)

| Component | Cost |
|-----------|------|
| Setup (one-time) | $0.05 |
| Monthly storage | $0.35 |
| 100 interpretations | $0.03 |
| **First Month Total** | **$0.43** |

**Subsequent Months:** $0.38 (storage + queries only)

---

## Cost Comparison: RAG vs Context Stuffing

**Scenario:** 50 papers (500K tokens), 100 queries/month

### Context Stuffing (Current kanoa Default)

| Item | Cost |
|------|------|
| First query (cache write) | $2.00 |
| 99 queries (cache read @ 90% discount) | $19.80 |
| **Monthly Total** | **$21.80** |

### RAG Engine (Proposed)

| Item | Cost |
|------|------|
| Setup (one-time) | $0.05 |
| Monthly storage (GCS + vector DB) | $0.35 |
| 100 queries (retrieval + Gemini) | $0.03 |
| **Monthly Total (ongoing)** | **$0.38** |

**Savings:** 98.3% cost reduction! ($21.80 → $0.38)

#### Break-even Analysis

- Setup cost amortized over first month
- Month 1: $0.43 vs $21.80 (98% savings)
- Month 2+: $0.38 vs $21.80 (98.3% savings)

---

## Scaling Analysis

### 10 PDFs (100K tokens)

| Component | Cost |
|-----------|------|
| Setup | $0.01 |
| Monthly storage | $0.15 |
| 100 queries/month | $0.03 |
| **Total (monthly)** | **$0.18** |

**vs Context Stuffing:** $4.50 → **96% savings**

### 100 PDFs (1M tokens)

| Component | Cost |
|-----------|------|
| Setup | $0.10 |
| Monthly storage | $0.80 |
| 100 queries/month | $0.03 |
| **Total (monthly)** | **$0.83** |

**vs Context Stuffing:** $43.00 → **98% savings**

### 500 PDFs (5M tokens)

| Component | Cost |
|-----------|------|
| Setup | $0.50 |
| Monthly storage (scaled tier) | $3.00 |
| 100 queries/month | $0.03 |
| **Total (monthly)** | **$3.03** |

**vs Context Stuffing:** $215.00 → **98.6% savings**

**Key Insight:** RAG Engine scales **linearly** with corpus size, while context stuffing scales **per query**.

---

## Query Volume Scaling

**Fixed monthly storage:** $0.35 (50 PDFs)

| Queries/Month | Gemini Cost | Total Monthly | Cost/Query |
|---------------|-------------|---------------|------------|
| 10 | $0.003 | $0.353 | $0.0353 |
| 100 | $0.035 | $0.385 | $0.00385 |
| 1,000 | $0.35 | $0.70 | $0.0007 |
| 10,000 | $3.50 | $3.85 | $0.000385 |

**vs Context Stuffing (100 queries):** $21.80

**Break-even:** RAG is cheaper until ~5,600 queries/month (at which point you're still saving 98%+ on context stuffing costs!)

---

## Cost Optimization Tips

### 1. Use Cheapest Gemini Model

- **gemini-2.0-flash-exp**: $0.075/1M input (10x cheaper than Pro)
- Sufficient for most interpretation tasks
- Upgrade to Pro only for complex reasoning

### 2. Reduce Retrieved Chunks

```python
rag_kb = VertexRAGKnowledgeBase(
    top_k=3,  # Instead of 5 (40% fewer tokens)
    similarity_threshold=0.8,  # Stricter (filters low-relevance chunks)
)
```

**Impact:** 2,500 tokens → 1,500 tokens per query = 40% cost reduction

### 3. Batch Similar Queries

- Cache system prompts across similar interpretations
- Use same focus/context structure to maximize cache hits

### 4. Delete Unused Corpora

```python
# Cleanup old test corpora
old_kb.delete_corpus()  # Saves $0.35/month per corpus
```

### 5. Use GCS Lifecycle Policies

```bash
# Auto-delete old test PDFs after 30 days
gsutil lifecycle set lifecycle.json gs://your-test-bucket
```

#### lifecycle.json

```json
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 30}
  }]
}
```

---

## Hidden Costs to Watch

### 1. GCS Egress (Usually Free for RAG)

- ** **Free**: GCS → Vertex AI (same region, internal traffic)
- WARNING: **Charged**: Downloading PDFs to local machine
- 💡 **Tip**: Keep PDFs in GCS, don't download unless needed

### 2. Multi-Region Deployments

- GCS multi-region: $0.026/GB (vs $0.020 single region)
- Higher Spanner costs for multi-regional vector DB
- 💡 **Tip**: Use single region (us-central1) for testing

### 3. Embedding Model Upgrades

- text-embedding-005: $0.025/1M chars
- Future models may have different pricing
- 💡 **Tip**: Lock pricing in docs, review quarterly

### 4. Large PDF Pre-processing

- Document AI Layout Parser: $1.50/1K pages (optional)
- LLM Parser: Gemini costs per page
- 💡 **Tip**: Use default parser unless PDFs have complex layouts

---

## No Mileage-Based Fees! **

**Great News:** Vertex AI RAG Engine does **NOT** charge for:

- ** Number of queries/retrievals per month
- ** Number of semantic searches
- ** Number of corpus accesses
- ** Data transfer within GCP (GCS → Vertex AI)
- ** Retrieval API calls (`retrieveContexts`)

#### You ONLY pay for

1. ** **Storage** (GCS + vector DB) - fixed monthly cost
2. ** **Embeddings** (one-time indexing) - only when adding files
3. ** **Gemini calls** (generation) - only when interpreting with LLM

#### This is fundamentally different from

- **OpenAI Assistants**: $0.20/GB/day retrieval (mileage-based!)
- **Pinecone**: $0.095/1M queries (mileage-based!)
- **Weaviate Cloud**: Query-based pricing tiers

---

## Billing Transparency with Multiple Projects

### Single Project (Multiple Corpora)

```python
# All under one GCP project
ml_kb = VertexRAGKnowledgeBase(project_id="my-research", corpus_display_name="ml")
health_kb = VertexRAGKnowledgeBase(project_id="my-research", corpus_display_name="health")
cv_kb = VertexRAGKnowledgeBase(project_id="my-research", corpus_display_name="cv")
```

#### Billing

- All costs on one invoice
- Hard to separate costs per corpus (requires log analysis)
- Use for personal research with single budget

### Multiple Projects (Billing Isolation)

```python
# Separate GCP projects
client_a = VertexRAGKnowledgeBase(project_id="client-a-project", corpus_display_name="kb")
client_b = VertexRAGKnowledgeBase(project_id="client-b-project", corpus_display_name="kb")
personal = VertexRAGKnowledgeBase(project_id="my-research", corpus_display_name="kb")
```

#### Billing

- Separate invoices per project
- Perfect for client billing/chargebacks
- Use for consulting or multi-team organizations

---

## Cost Monitoring

### Via GCP Console

1. **Cloud Billing** → Reports
2. Filter by:
   - Service: "Vertex AI"
   - SKU: "RAG Engine", "Embeddings", "Spanner"
3. Group by: Project, Service

### Via Command Line

```bash
# Get current month's Vertex AI costs
gcloud billing accounts list
gcloud billing accounts list --filter="my-billing-account"

# Detailed cost breakdown
gcloud beta billing budgets list --billing-account=<ACCOUNT_ID>
```

### Programmatic (Cloud Billing API)

```python
from google.cloud import billing

client = billing.CloudBillingClient()
# Query costs by project, service, time range
```

---

## Summary: Cost Dimensions

| Cost Dimension | Billed By | Frequency | Scales With | Mileage Fees? |
|----------------|-----------|-----------|-------------|---------------|
| **GCS Storage** | GB/month | Monthly | Corpus size | ** No |
| **Embeddings** | Characters | One-time | # of documents | ** No |
| **Vector DB** | Tier/GB | Monthly | Corpus size | ** No |
| **Retrieval** | N/A | Free | N/A | ** No |
| **Gemini Calls** | Tokens | Per query | Query volume | ** Yes* |

*Only component with per-query cost, but unrelated to RAG (standard Gemini pricing)

---

## References

- [Vertex AI RAG Engine Billing](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-engine-billing)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [GCS Pricing](https://cloud.google.com/storage/pricing)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Spanner Pricing](https://cloud.google.com/spanner/pricing)

---

**Last Updated:** December 11, 2025<br>
**Pricing Subject to Change:** Always verify current rates at official GCP pricing pages
