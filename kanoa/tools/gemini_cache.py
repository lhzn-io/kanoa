"""
Gemini Context Cache Management Tool.

Usage:
    python -m kanoa.tools.gemini_cache list
    python -m kanoa.tools.gemini_cache delete <name_or_id>
    python -m kanoa.tools.gemini_cache prune [--force]
"""

import argparse
import os
import sys

from google import genai


def get_client() -> genai.Client:
    """Initialize Gemini client."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    # Fallback to Vertex AI (ADC)
    try:
        return genai.Client(vertexai=True)
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print("   Please set GOOGLE_API_KEY or ensure gcloud auth is configured.")
        sys.exit(1)


def list_caches(args: argparse.Namespace) -> None:
    """List all active caches."""
    client = get_client()
    print("\n=== Active Gemini Context Caches ===")
    print(
        f"{'Display Name':<30} | {'Token Count':<12} | {'Expires (UTC)':<20} | {'Name (ID)'}"
    )
    print("-" * 100)

    count = 0
    try:
        for cache in client.caches.list():
            count += 1
            name = cache.name
            display_name = getattr(cache, "display_name", "n/a") or "n/a"

            tokens = 0
            if hasattr(cache, "usage_metadata"):
                tokens = getattr(cache.usage_metadata, "total_token_count", 0)

            expire_time = getattr(cache, "expire_time", "n/a")
            if isinstance(expire_time, str):
                expire_str = expire_time.split(".")[0].replace("T", " ")
            else:
                expire_str = str(expire_time)

            print(
                f"{display_name[:28]:<30} | {tokens:<12,} | {expire_str:<20} | {name}"
            )

    except Exception as e:
        print(f"\n❌ Error listing caches: {e}")
        return

    if count == 0:
        print("No active caches found.")
    else:
        print("-" * 100)
        print(f"Total: {count} active caches")


def delete_cache(args: argparse.Namespace) -> None:
    """Delete a specific cache."""
    client = get_client()
    name = args.name

    print(f"🗑️  Deleting cache: {name}...")
    try:
        client.caches.delete(name=name)
        print("✅ Cache deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to delete cache: {e}")


def prune_caches(args: argparse.Namespace) -> None:
    """Delete ALL active caches."""
    client = get_client()

    if not args.force:
        confirm = input(
            "⚠️  This will delete ALL active context caches. Are you sure? [y/N] "
        )
        if confirm.lower() != "y":
            print("Aborted.")
            return

    print("🗑️  Pruning all caches...")
    count = 0
    try:
        for cache in client.caches.list():
            if not cache.name:
                continue
            try:
                client.caches.delete(name=cache.name)
                print(f"  ✓ Deleted {cache.name}")
                count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {cache.name}: {e}")
    except Exception as e:
        print(f"❌ Error listing caches for prune: {e}")

    print(f"\n✅ Pruned {count} caches.")


def register_subcommand(parser: argparse.ArgumentParser) -> None:
    """Register subcommands for the cache tool."""
    subparsers = parser.add_subparsers(dest="cache_command", help="Cache action")

    # List command
    subparsers.add_parser("list", help="List active caches")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a specific cache")
    delete_parser.add_argument("name", help="Cache name or ID")

    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Delete ALL caches")
    prune_parser.add_argument("--force", action="store_true", help="Skip confirmation")


def handle_command(args: argparse.Namespace) -> None:
    """Handle the cache command."""
    if args.cache_command == "list":
        list_caches(args)
    elif args.cache_command == "delete":
        delete_cache(args)
    elif args.cache_command == "prune":
        prune_caches(args)
    else:
        print("Please specify a cache command: list, delete, prune")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Gemini Context Caches")
    register_subcommand(parser)
    args = parser.parse_args()
    handle_command(args)


if __name__ == "__main__":
    main()
