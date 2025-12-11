# kanoa Product Roadmap

**Version:** 2.1
**Date:** December 7, 2025
**Status:** Living Document

---

## Table of Contents

1. [Current State](#current-state)
2. [Strategic Direction](#strategic-direction)
3. [Phase 1: Advanced Grounding (Q1 2025)](#phase-1-advanced-grounding-q1-2025)
4. [Phase 2: Enterprise & Production (Q2 2025)](#phase-2-enterprise--production-q2-2025)
5. [Phase 3: Community & Ecosystem (Q3 2025)](#phase-3-community--ecosystem-q3-2025)
6. [Deferred Features](#deferred-features)

---

## Current State

### ✅ Implemented (v0.1.x)

#### Core Infrastructure

- [x] Multi-backend architecture (`GeminiBackend`, `ClaudeBackend`, `OpenAIBackend`)
- [x] Unified `AnalyticsInterpreter` API
- [x] Knowledge base abstraction (`TextKnowledgeBase`, `PDFKnowledgeBase`)
- [x] Cost tracking and token usage monitoring
- [x] Context caching for cost optimization
- [x] Type-safe codebase (mypy strict)
- [x] 85%+ test coverage

#### Backends

- [x] **Gemini 3 Pro**: Native PDF vision, 2M context, context caching
- [x] **Claude Sonnet 4.5**: Proven reliability, prompt caching
- [x] **OpenAI/vLLM**: GPT-5.1 and local inference (Molmo, Gemma 3)
- [ ] **Advanced Local Models**: Llama 4, Olmo 3, Ministral 3 (Jetson Thor optimized) — *Verification Underway*

#### Knowledge Base

- [x] **Text KB**: Markdown files with caching
- [x] **PDF KB**: Full PDF processing with Gemini native vision
- [x] **Context Stuffing**: Default strategy using Gemini's 2M context window

#### Developer Experience

- [x] Comprehensive documentation (Sphinx)
- [x] Example notebooks for all backends
- [x] PyPI packaging and releases
- [x] CI/CD with GitHub Actions
- [x] Pre-commit hooks (ruff, mypy)

---

## Strategic Direction

**Core Thesis**: kanoa should be the **definitive library for grounded interpretation of data science outputs**, leveraging best-in-class provider-native solutions rather than building custom infrastructure.

**Key Principles**:

1. **Provider-Native First**: Use Google's Vertex AI RAG Engine, not custom vector stores
2. **Multimodal Grounding**: Text, images, video, code — all grounded in domain knowledge
3. **Flexible Retrieval**: Support private data, public web, and specialized sources (GitHub, arXiv)
4. **Cost-Optimized**: Intelligent chunking, dynamic retrieval, and context caching

---

## Phase 1: Advanced Grounding (Q1 2025)

**Goal**: Implement Google's full suite of grounding capabilities, establishing kanoa as the premier solution for grounded LLM interpretation.

### 1.1 Vertex AI RAG Engine (High Priority)

**Status**: Not yet implemented
**Timeline**: 4-6 weeks
**Deliverables**:

- [ ] `VertexRAGKnowledgeBase` class
  - [ ] RAG corpus creation and management via Vertex AI SDK
  - [ ] Support for GCS, Google Drive, and local file ingestion
  - [ ] Automatic chunking with configurable parameters
  - [ ] Multimodal extraction (images from PDFs, video transcripts)
  - [ ] Incremental corpus updates

- [ ] Integration with `GeminiBackend`
  - [ ] `grounding_mode='rag_engine'` parameter
  - [ ] Semantic retrieval with similarity thresholds
  - [ ] Retrieved context injection into prompts
  - [ ] Source attribution in results

- [ ] Cost optimization
  - [ ] Benchmark: 60-80% cost reduction vs context stuffing for large KBs
  - [ ] Dynamic chunk retrieval (top-k, similarity threshold)

- [ ] Documentation
  - [ ] Migration guide: context stuffing → RAG Engine
  - [ ] Complete workflow examples
  - [ ] Cost comparison analysis

**Technical Approach**:

```python
# New API
interpreter = AnalyticsInterpreter(
    backend='gemini',
    kb_path='./docs',
    grounding_mode='rag_engine',
    rag_config={
        'project_id': 'my-gcp-project',
        'location': 'us-central1',
        'corpus_display_name': 'research-kb',
        'chunk_size': 512,
        'chunk_overlap': 50,
        'top_k': 5,
        'similarity_threshold': 0.7
    }
)

```

**Success Metrics**:

- RAG Engine handles >1GB knowledge bases efficiently
- 85%+ retrieval precision on domain-specific queries
- Cost reduction validated in real-world use cases

---

### 1.2 Grounding with Google Search

**Status**: Not yet implemented
**Timeline**: 2-3 weeks
**Deliverables**:

- [ ] `grounding_mode='google_search'` support
- [ ] Dynamic retrieval: model decides when to search
- [ ] Web source attribution with URLs
- [ ] Configurable search parameters
- [ ] Cost tracking for search grounding

**API**:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='google_search',
    google_search_config={
        'dynamic_retrieval': True,
        'max_search_results': 5
    }
)

```

**Use Cases**:

- Current events and trends analysis
- Real-time data interpretation
- Verifiable web citations

---

### 1.3 Hybrid Grounding (RAG + Search)

**Status**: Not yet implemented
**Timeline**: 1-2 weeks (after 1.1 and 1.2)
**Deliverables**:

- [ ] `grounding_mode='hybrid'` orchestration
- [ ] Combine private knowledge base with web search
- [ ] Source priority and attribution
- [ ] Cost-optimized retrieval strategies

**Use Case**: Production research assistants requiring both domain expertise and current information.

---

### 1.4 Grounding on Custom Search (Advanced)

**Status**: Exploratory
**Timeline**: 3-4 weeks
**Deliverables**:

- [ ] **GitHub Code Search Integration**
  - [ ] Ground interpretations in project codebases
  - [ ] Semantic code retrieval for debugging insights
  - [ ] Commit history and PR context

- [ ] **arXiv Search Integration**
  - [ ] Ground in latest research papers
  - [ ] Citation extraction and formatting

- [ ] **Generic Search Adapter**
  - [ ] Abstract interface for custom search engines
  - [ ] Support for internal documentation portals
  - [ ] Elasticsearch, Algolia, etc.

**Strategic Vision**: Enable grounding on **any** specialized knowledge source, not just generic web search.

**API Sketch**:

```python
interpreter = AnalyticsInterpreter(
    backend='gemini',
    grounding_mode='custom_search',
    search_config={
        'engine': 'github',
        'repos': ['lhzn-io/kanoa', 'lhzn-io/kanoa-mlops'],
        'max_results': 5
    }
)

```

---

### 1.5 Document AI Layout Parser Integration

**Status**: Not yet implemented
**Timeline**: 2 weeks
**Deliverables**:

- [ ] Enable Document AI layout parser for RAG corpus
- [ ] Accurate parsing of complex PDFs (tables, multi-column, charts)
- [ ] Superior retrieval accuracy for academic papers
- [ ] Integration tests with real research papers

---

### 1.6 Ollama Integration

**Status**: In Progress
**Timeline**: Immediate
**Deliverables**:

- [ ] Docker Compose service for Ollama (kanoa-mlops)
- [ ] Makefile integration (`make serve-ollama`)
- [ ] Documentation and HF Cache integration
- [ ] Verification with Gemini 3 / Llama 3 models

**Rationale**: Strategic integration for VSCode AI Chat compatibility.

---

## Phase 2: Enterprise & Production (Q2 2025)

**Goal**: Production-grade reliability, security, and enterprise features.

### 2.1 Vertex AI Enterprise Backend

**Status**: Not yet implemented
**Timeline**: 3-4 weeks
**Deliverables**:

- [ ] `VertexAIBackend` class using `google-cloud-aiplatform` SDK
- [ ] Service account authentication
- [ ] VPC Service Controls support
- [ ] Cloud Audit Logs integration
- [ ] CMEK (Customer-Managed Encryption Keys)
- [ ] Private endpoint configuration
- [ ] `kanoa[vertexai]` package extra

**Use Case**: Enterprise deployments requiring compliance, audit trails, and private networks.

---

### 2.2 Batch Processing & Async API

**Status**: Not yet implemented
**Timeline**: 2-3 weeks
**Deliverables**:

- [ ] Batch interpretation API
- [ ] Async/await support for concurrent processing
- [ ] Progress tracking and resumption
- [ ] Cost optimization for batch workflows

**API Sketch**:

```python
results = await interpreter.interpret_batch(
    figures=[fig1, fig2, fig3],
    contexts=["Analysis 1", "Analysis 2", "Analysis 3"]
)

```

---

### 2.3 Structured Output & Data Extraction

**Status**: Not yet implemented
**Timeline**: 2 weeks
**Deliverables**:

- [ ] Pydantic schema support for structured outputs
- [ ] JSON schema validation
- [ ] Automatic table/metric extraction
- [ ] Integration with Gemini structured output API

**Use Case**: Extract structured insights for downstream processing, databases, dashboards.

---

## Phase 3: Community & Ecosystem (Q3 2025)

### 3.2 Agent Development Kit (ADK) Evaluation

**Status**: Future consideration
**Timeline**: TBD (contingent on demand)
**Scope**:

- [ ] Evaluate ADK for agentic interpretation workflows
- [ ] Multi-step reasoning with tool use
- [ ] Integration with Vertex AI Agent Builder

**Decision Point**: Wait for ADK maturity and community feedback.

---

### 3.3 Reference Manager Integration

**Status**: Future
**Deliverables**:

- [ ] Zotero API connector
- [ ] Paperguide integration
- [ ] Auto-populate `docs/refs/` from `.bib` files

---

### 3.4 Interactive Codelabs

**Status**: Planned
**Deliverables**:

- [ ] "Zero to Hero" Codelab (General Quickstart)
- [ ] "Local AI Analyst" Codelab (Ollama/vLLM)
- [ ] "Enterprise RAG" Codelab (Vertex AI)
- [ ] Integration with `claat` tool for generation

## Deferred Features

### Low Priority (Backlog)

- [ ] Audio/Video knowledge base (beyond RAG Engine multimodal)
- [ ] Multi-turn conversation history (`ChatSession` class)
- [ ] Structured logging with `structlog`
- [ ] Redis/disk-based persistent cache
- [ ] Cost prediction and budget alerts

### Explicitly Rejected

#### Log Stream Reuse by ID/Handle

**Status**: Won't implement (out of scope)
**Date**: December 3, 2024

**Rationale**: The `log_stream()` context manager is sufficient for its primary use case (grouping verbose logs during `interpret()` calls). Advanced log streaming features would constitute scope creep and add unnecessary complexity. Users needing sophisticated logging should use dedicated libraries (loguru, structlog, rich).

---

## Success Metrics

### Technical

- [ ] RAG Engine reduces costs by 60%+ for KBs >500K tokens
- [ ] Retrieval precision >85% on domain-specific benchmarks
- [ ] Grounding sources include verifiable citations
- [ ] Support for KBs >1GB with efficient retrieval

### Adoption

- [ ] 100+ GitHub stars
- [ ] 10+ community contributions
- [ ] 3+ case studies from different domains
- [ ] Featured in Google Vertex AI documentation (aspirational)

---

## Changelog

### v2.1 (December 7, 2025)

- **Ollama Integration**: Accelerated to Phase 1 (Immediate) for VSCode compatibility.

### v2.0 (December 4, 2025)

- **Complete roadmap overhaul**: Removed vestigial implementation plans
- **Strategic refocus**: Prioritize Google grounding capabilities (RAG Engine, Search, Custom Search)
- **Phase sequencing**: Grounding (Phase 1) → Enterprise (Phase 2) → Community (Phase 3)
- **Deferred Ollama**: Moved to Phase 3 to focus on core differentiation

### v1.3 (December 1, 2025)

- Added Vertex AI Enterprise Backend
- Added ADK integration consideration

### v1.2 (November 30, 2025)

- Replaced Molmo backend with vLLM strategy

### v1.0 (November 20, 2025)

- Initial specification

---

## Contact

- **Repository**: [github.com/lhzn-io/kanoa](https://github.com/lhzn-io/kanoa)
- **Issues**: [github.com/lhzn-io/kanoa/issues](https://github.com/lhzn-io/kanoa/issues)
- **Discussions**: [github.com/lhzn-io/kanoa/discussions](https://github.com/lhzn-io/kanoa/discussions)
