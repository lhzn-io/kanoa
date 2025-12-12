"""
Vertex AI RAG Engine Management Tool.

Usage:
    kanoa vertex rag list --project <project_id> [--region <region>]
    kanoa vertex rag create --project <project_id> --display-name <name> [--region <region>]
    kanoa vertex rag import --project <project_id> --display-name <name> --gcs-uri <uri> [--region <region>]
    kanoa vertex rag chat --project <project_id> --display-name <name> [--region <region>]
    kanoa vertex rag delete --project <project_id> --display-name <name> [--region <region>] [--force]

Note: --location and --region are aliases (both map to GCP location parameter)
"""

import argparse
import contextlib
import os
import sys
import warnings

try:
    import vertexai
    from vertexai import rag
    from vertexai.generative_models import GenerativeModel, Tool

    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False


def _get_project_id(args: argparse.Namespace) -> str:
    """Get project ID from args or environment."""
    project_id = (
        args.project
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
    )
    if not project_id:
        print("❌ Error: Project ID is required.")
        print("   Use --project or set GOOGLE_CLOUD_PROJECT/GCP_PROJECT env var.")
        sys.exit(1)
    return project_id


def _init_vertex(project_id: str, location: str) -> None:
    """Initialize Vertex AI SDK."""
    if not VERTEX_AI_AVAILABLE:
        print("❌ Error: google-cloud-aiplatform is not installed.")
        print("   Install with: pip install kanoa[vertexai]")
        sys.exit(1)

    try:
        vertexai.init(project=project_id, location=location)
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI: {e}")
        sys.exit(1)


def list_corpora(args: argparse.Namespace) -> None:
    """List all RAG corpora in the project."""
    project_id = _get_project_id(args)
    _init_vertex(project_id, args.location)

    print(f"\n=== Vertex AI RAG Corpora ({project_id}/{args.location}) ===")
    print(f"{'Display Name':<30} | {'Create Time':<25} | {'Name (ID)'}")
    print("-" * 100)

    count = 0
    try:
        corpora = rag.list_corpora()
        for corpus in corpora:
            count += 1
            display_name = corpus.display_name or "n/a"
            create_time = (
                str(corpus.create_time).split(".")[0] if corpus.create_time else "n/a"
            )
            name = corpus.name

            print(f"{display_name[:28]:<30} | {create_time:<25} | {name}")

    except Exception as e:
        print(f"\n❌ Error listing corpora: {e}")
        return

    if count == 0:
        print("No corpora found.")
    else:
        print("-" * 100)
        print(f"Total: {count} corpora")


def create_corpus(args: argparse.Namespace) -> None:
    """Create a new RAG corpus."""
    project_id = _get_project_id(args)

    from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

    print(f"\nCreating corpus '{args.display_name}' in {project_id}...")

    try:
        rag_kb = VertexRAGKnowledgeBase(
            project_id=project_id,
            location=args.location,
            corpus_display_name=args.display_name,
        )
        corpus_name = rag_kb.create_corpus()
        print(f"✅ Corpus created/reused successfully: {corpus_name}")

    except Exception as e:
        print(f"❌ Failed to create corpus: {e}")
        sys.exit(1)


def import_files(args: argparse.Namespace) -> None:
    """Import files into a RAG corpus."""
    project_id = _get_project_id(args)

    from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

    print(f"\nImporting files from {args.gcs_uri} into '{args.display_name}'...")
    print("Note: This is an async operation and may take several minutes.")

    try:
        rag_kb = VertexRAGKnowledgeBase(
            project_id=project_id,
            location=args.location,
            corpus_display_name=args.display_name,
        )
        # Ensure corpus exists/is linked
        rag_kb.create_corpus()

        rag_kb.import_files(args.gcs_uri)
        print("✅ Import started successfully.")
        print("   Check Vertex AI console for progress.")

    except Exception as e:
        print(f"❌ Failed to import files: {e}")
        sys.exit(1)


def delete_corpus(args: argparse.Namespace) -> None:
    """Delete a RAG corpus."""
    project_id = _get_project_id(args)

    if not args.force:
        confirm = input(
            f"⚠️  This will PERMANENTLY DELETE corpus '{args.display_name}' and all its data. Are you sure? [y/N] "
        )
        if confirm.lower() != "y":
            print("Aborted.")
            return

    from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

    print(f"\nDeleting corpus '{args.display_name}'...")

    try:
        rag_kb = VertexRAGKnowledgeBase(
            project_id=project_id,
            location=args.location,
            corpus_display_name=args.display_name,
        )
        # Ensure corpus exists/is linked so we can delete it
        rag_kb.create_corpus()

        rag_kb.delete_corpus()
        print("✅ Corpus deleted successfully.")

    except Exception as e:
        print(f"❌ Failed to delete corpus: {e}")
        sys.exit(1)


def chat(args: argparse.Namespace) -> None:
    """Interactive chat with RAG corpus."""
    project_id = _get_project_id(args)
    _init_vertex(project_id, args.location)

    from kanoa.knowledge_base.vertex_rag import VertexRAGKnowledgeBase

    # Suppress Vertex AI SDK deprecation warnings
    warnings.filterwarnings("ignore", module="vertexai.generative_models")

    print(f"\nInitializing chat with corpus '{args.display_name}'...")

    try:
        # Initialize Knowledge Base wrapper to get corpus name/config
        rag_kb = VertexRAGKnowledgeBase(
            project_id=project_id,
            location=args.location,
            corpus_display_name=args.display_name,
            top_k=args.top_k,
        )
        # Ensure we have the corpus name (will raise if not created, which is fine)
        # But actually, VertexRAGKnowledgeBase.get_corpus() or create_corpus() needs to be called
        # to populate self._corpus_name if we want to use rag_kb.corpus_name property.
        # Let's try to get it.
        try:
            rag_kb.get_corpus()
        except Exception:
            print(f"❌ Corpus '{args.display_name}' not found. Please create it first.")
            sys.exit(1)

        print(f"Using model: {args.model}")
        print("Type 'exit', 'quit', or Ctrl+D to stop.\n")
        print("=" * 60)

        # Create grounding tool with RAG corpus
        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k=rag_kb.top_k,
        )

        rag_grounding_tool = Tool.from_retrieval(
            rag.Retrieval(
                source=rag.VertexRagStore(
                    rag_resources=[
                        rag.RagResource(
                            rag_corpus=rag_kb.corpus_name,
                        )
                    ],
                    rag_retrieval_config=rag_retrieval_config,
                )
            )
        )

        # Create model with RAG grounding
        model = GenerativeModel(
            model_name=args.model,
            tools=[rag_grounding_tool],
        )
        chat_session = model.start_chat()

    except Exception as e:
        print(f"❌ Failed to initialize chat: {e}")
        sys.exit(1)

    while True:
        try:
            try:
                question = input("Question: ").strip()
            except EOFError:
                print("\nExiting...")
                break

            if not question:
                continue

            if question.lower() in ("exit", "quit", "q"):
                print("\nExiting...")
                break

            print("\nGenerating answer...")
            response_stream = chat_session.send_message(question, stream=True)

            # Display answer
            print("\n" + "=" * 60)
            print("Answer:")
            print("=" * 60)

            grounding_metadata = None
            for chunk in response_stream:
                with contextlib.suppress(ValueError):
                    print(chunk.text, end="", flush=True)

                # Capture grounding metadata if present in any chunk
                if hasattr(chunk, "candidates") and chunk.candidates:
                    cand = chunk.candidates[0]
                    if hasattr(cand, "grounding_metadata") and cand.grounding_metadata:
                        grounding_metadata = cand.grounding_metadata

            print("\n" + "=" * 60)

            # Extract and display grounding sources
            if grounding_metadata and hasattr(grounding_metadata, "grounding_chunks"):
                print("\nGrounding sources:")
                for i, chunk in enumerate(grounding_metadata.grounding_chunks, 1):
                    if hasattr(chunk, "web") and chunk.web:
                        print(f"  [{i}] Web: {chunk.web.uri}")
                        if hasattr(chunk.web, "title"):
                            print(f"      Title: {chunk.web.title}")
                    elif hasattr(chunk, "retrieved_context"):
                        rc = chunk.retrieved_context
                        print(f"  [{i}] Retrieved context:")
                        if hasattr(rc, "uri"):
                            print(f"      URI: {rc.uri}")
                        if hasattr(rc, "title") and rc.title:
                            print(f"      Title: {rc.title}")
                        if hasattr(rc, "text") and rc.text:
                            # Clean up text for display
                            text_preview = rc.text.replace("\n", " ").strip()
                            if len(text_preview) > 150:
                                text_preview = text_preview[:147] + "..."
                            print(f"      Snippet: {text_preview}")
            print()

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def register_subcommand(parser: argparse.ArgumentParser) -> None:
    """Register subcommands for the vertex tool."""
    # vertex -> rag -> [list, create, import, delete]
    vertex_subparsers = parser.add_subparsers(
        dest="vertex_service", help="Vertex AI Service"
    )

    rag_parser = vertex_subparsers.add_parser("rag", help="RAG Engine management")
    rag_subparsers = rag_parser.add_subparsers(dest="rag_command", help="RAG action")

    # Common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--project", help="GCP Project ID")
    parent_parser.add_argument(
        "--location",
        "--region",
        dest="location",
        default="us-east1",
        help="GCP region/location (default: us-east1)",
    )

    # List
    rag_subparsers.add_parser("list", parents=[parent_parser], help="List RAG corpora")

    # Create
    create_parser = rag_subparsers.add_parser(
        "create", parents=[parent_parser], help="Create RAG corpus"
    )
    create_parser.add_argument(
        "--display-name", required=True, help="Corpus display name"
    )

    # Import
    import_parser = rag_subparsers.add_parser(
        "import", parents=[parent_parser], help="Import files from GCS"
    )
    import_parser.add_argument(
        "--display-name", required=True, help="Corpus display name"
    )
    import_parser.add_argument(
        "--gcs-uri", required=True, help="GCS URI (gs://bucket/path/)"
    )

    # Delete
    delete_parser = rag_subparsers.add_parser(
        "delete", parents=[parent_parser], help="Delete RAG corpus"
    )
    delete_parser.add_argument(
        "--display-name", required=True, help="Corpus display name"
    )
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # Chat
    chat_parser = rag_subparsers.add_parser(
        "chat", parents=[parent_parser], help="Interactive chat with RAG corpus"
    )
    chat_parser.add_argument(
        "--display-name", required=True, help="Corpus display name"
    )
    chat_parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Model name (default: gemini-2.5-flash)",
    )
    chat_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of chunks to retrieve (default: 5)"
    )


def handle_command(args: argparse.Namespace) -> None:
    """Handle the vertex command."""
    if args.vertex_service == "rag":
        if args.rag_command == "list":
            list_corpora(args)
        elif args.rag_command == "create":
            create_corpus(args)
        elif args.rag_command == "import":
            import_files(args)
        elif args.rag_command == "delete":
            delete_corpus(args)
        elif args.rag_command == "chat":
            chat(args)
        else:
            print("Please specify a RAG command: list, create, import, delete, chat")
    else:
        print("Please specify a Vertex service: rag")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Vertex AI Resources")
    register_subcommand(parser)
    args = parser.parse_args()
    handle_command(args)


if __name__ == "__main__":
    main()
