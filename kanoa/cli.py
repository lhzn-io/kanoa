"""
kanoa CLI Entry Point.
"""

import argparse
import sys
from typing import List, Optional

from kanoa.tools import gemini_cache


def main(args: Optional[List[str]] = None) -> None:
    """Main entry point for the kanoa CLI."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="kanoa: AI-powered data science interpretation library."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- Gemini Subcommand ---
    gemini_parser = subparsers.add_parser("gemini", help="Gemini backend tools")
    gemini_subparsers = gemini_parser.add_subparsers(
        dest="subcommand", help="Gemini tools"
    )

    # Gemini Cache Tool
    cache_parser = gemini_subparsers.add_parser("cache", help="Manage context caches")
    gemini_cache.register_subcommand(cache_parser)

    # --- Load Plugins ---
    if sys.version_info < (3, 10):
        from importlib_metadata import entry_points
    else:
        from importlib.metadata import entry_points

    # Load commands from plugins (e.g., kanoa-mlops)
    # Plugins should export a function `register(subparsers)`
    # Group: kanoa.cli.commands
    eps = entry_points(group="kanoa.cli.commands")
    for ep in eps:
        try:
            register_func = ep.load()
            register_func(subparsers)
        except Exception as e:
            # We don't want to crash the CLI if a plugin fails to load,
            # but we should probably warn in verbose mode.
            # For now, just print a suppressed warning to stderr if needed, or ignore.
            print(f"Warning: Failed to load plugin {ep.name}: {e}", file=sys.stderr)

    # Parse
    parsed_args = parser.parse_args(args)

    # Dispatch
    if parsed_args.command == "gemini":
        if parsed_args.subcommand == "cache":
            gemini_cache.handle_command(parsed_args)
        else:
            gemini_parser.print_help()
    elif hasattr(parsed_args, "func"):
        parsed_args.func(parsed_args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
