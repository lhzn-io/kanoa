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

    # Parse
    parsed_args = parser.parse_args(args)

    # Dispatch
    if parsed_args.command == "gemini":
        if parsed_args.subcommand == "cache":
            gemini_cache.handle_command(parsed_args)
        else:
            gemini_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
