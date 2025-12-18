"""
Integration tests for Vertex AI RAG Engine.

These tests verify the end-to-end workflow of creating a corpus, importing files,
retrieving context, and using it with the AnalyticsInterpreter.

Usage:
    pytest tests/integration/test_vertex_rag_integration.py \
      --vertex-project=my-project \
      --vertex-display-name=my-corpus \
      --vertex-gcs-uri=gs://my-bucket/files/
"""

import time
import warnings

import pytest

# Suppress Vertex AI SDK deprecation warnings
warnings.filterwarnings("ignore", module="vertexai.generative_models")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.vertex,
]


def run_basic_corpus_workflow(
    project_id,
    location,
    corpus_display_name,
    gcs_uri,
):
    """Test basic corpus creation, import, and retrieval."""
    print("=" * 60)
    print("Testing Basic Corpus Workflow")
    print("=" * 60)

    from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

    # 1. Create knowledge base
    print("\n1. Creating VertexRAGKnowledgeBase...")
    print(f"   Project: {project_id}")
    print(f"   Corpus: {corpus_display_name}")

    rag_kb = VertexRAGKnowledgeBase(
        project_id=project_id,
        location=location,
        corpus_display_name=corpus_display_name,
        chunk_size=512,
        chunk_overlap=100,
        top_k=5,
        similarity_threshold=0.7,
    )
    print("   ✓ VertexRAGKnowledgeBase initialized")

    # 2. Create or reuse corpus
    print("\n2. Creating or reusing corpus...")
    corpus_name = rag_kb.create_corpus()
    print(f"   ✓ Corpus: {corpus_name}")

    if gcs_uri:
        # 3. Import files from GCS
        print(f"\n3. Importing files from {gcs_uri}...")
        print("   Note: This is an async operation. Import may take 2-5 minutes.")
        rag_kb.import_files(gcs_uri)
        print("   ✓ Import started")

        # 4. Wait for import to complete
        print("\n4. Waiting 30 seconds for import to process...")
        time.sleep(30)
    else:
        print("\n3. Skipping file import (no --vertex-gcs-uri provided)")

    # 5. Test retrieval
    print("\n5. Testing semantic retrieval...")
    # Use a generic query that is likely to match something if files were imported
    test_query = "machine learning"
    print(f"   Query: '{test_query}'")

    results = rag_kb.retrieve(test_query)
    print(f"   ✓ Retrieved {len(results)} chunks")

    if results:
        print("\n   Top results:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n   [{i}] Score: {result['score']:.3f}")
            print(f"       Source: {result['source_uri']}")
            print(f"       Text preview: {result['text'][:100]}...")
    else:
        print("\n   ⚠ No results returned (import may still be processing)")

    print("\n" + "=" * 60)
    print("✓ Basic corpus workflow test complete!")
    print("=" * 60)

    return rag_kb


def run_analytics_interpreter_integration(rag_kb):
    """Test integration with AnalyticsInterpreter."""
    print("\n" + "=" * 60)
    print("Testing AnalyticsInterpreter Integration")
    print("=" * 60)

    import matplotlib.pyplot as plt

    from kanoa import AnalyticsInterpreter

    # Create interpreter with RAG grounding
    print("\n1. Creating AnalyticsInterpreter with RAG grounding...")
    interpreter = AnalyticsInterpreter(
        backend="gemini",
        grounding_mode="rag_engine",
        knowledge_base=rag_kb,
    )
    print("   ✓ Interpreter created")

    # Create test figure
    print("\n2. Creating test figure...")
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [0.72, 0.85, 0.89, 0.91])
    ax.set_title("Model Accuracy Over Time")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Accuracy")
    print("   ✓ Figure created")

    # Interpret with RAG grounding
    print("\n3. Interpreting with RAG grounding...")
    print("   (This will call Gemini API and cost ~$0.01)")

    result = interpreter.interpret(
        stream=False,
        fig=fig,
        context="Machine learning model improvement experiment",
        focus="Explain the accuracy improvement curve using concepts from research literature",
        display_result=False,
    )

    print("\n   ✓ Interpretation complete!")
    print(f"\n   Backend: {result.backend}")
    if result.usage:
        print(
            f"   Tokens: {result.usage.input_tokens} in, {result.usage.output_tokens} out"
        )
        print(f"   Cost: ${result.usage.cost:.4f}")

    print("\n   Interpretation:")
    print("   " + "-" * 56)
    print("   " + result.text[:300] + "...")
    print("   " + "-" * 56)

    if result.grounding_sources:
        print(f"\n   Grounding sources: {len(result.grounding_sources)}")
        for i, source in enumerate(result.grounding_sources[:3], 1):
            print(f"   [{i}] {source.uri} (score: {source.score:.2f})")
    else:
        print("\n   ⚠ No grounding sources (retrieval may have failed)")

    print("\n" + "=" * 60)
    print("✓ AnalyticsInterpreter integration test complete!")
    print("=" * 60)

    plt.close(fig)


def test_vertex_rag_workflow(vertex_config):
    """Run the full Vertex RAG workflow integration test."""

    # 1. Basic Corpus Workflow
    rag_kb = run_basic_corpus_workflow(
        project_id=vertex_config["project_id"],
        location=vertex_config["location"],
        corpus_display_name=vertex_config["corpus_display_name"],
        gcs_uri=vertex_config["gcs_uri"],
    )

    # 2. Analytics Interpreter Integration
    run_analytics_interpreter_integration(rag_kb)
