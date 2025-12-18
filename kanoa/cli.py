"""
kanoa CLI Entry Point.
"""

import argparse
import sys
from typing import List, Optional


def handle_interpret(args: argparse.Namespace) -> None:
    """Handle the interpret command."""
    from kanoa.core.interpreter import AnalyticsInterpreter

    # Read input data if provided
    data = None
    if args.data:
        try:
            with open(args.data, "r") as f:
                data = f.read()
        except Exception as e:
            print(f"Error reading data file: {e}", file=sys.stderr)
            sys.exit(1)

    # Read KB context if provided
    kb_context = None
    if args.kb:
        try:
            with open(args.kb, "r") as f:
                kb_context = f.read()
        except Exception:
            # Assume string if file fails? Or explicit flag?
            # For CLI, explicit files are better.
            kb_context = args.kb

    # Initialize interpreter
    kwargs = {
        "backend": args.backend,
        "api_key": args.api_key,
        "verbose": args.verbose,
        "system_prompt": args.system_prompt,
    }
    if args.model:
        kwargs["model"] = args.model

    interpreter = AnalyticsInterpreter(**kwargs)

    print(f"Analyzing with {interpreter.backend.backend_name}...", file=sys.stderr)

    # Invoke interpret (returns iterator)
    iterator = interpreter.interpret(
        context=args.context,
        data=data,
        focus=args.focus,
        kb_context=kb_context,
        # CLI implies display_result is handled here manually
        display_result=False,
        stream=True,
    )

    # Consume stream
    try:
        for chunk in iterator:
            if chunk.type == "text":
                sys.stdout.write(chunk.content)
                sys.stdout.flush()
            elif chunk.type == "status":
                # Print status to stderr to avoid polluting pipeable stdout
                print(f"[{chunk.content}]", file=sys.stderr)
            elif chunk.type == "usage" and chunk.usage:
                model_info = f" [{chunk.usage.model}]" if chunk.usage.model else ""
                tier_info = f" ({chunk.usage.tier})" if chunk.usage.tier else ""

                # Use higher precision for very small non-zero costs
                cost_str = f"${chunk.usage.cost:.4f}"
                if 0 < chunk.usage.cost < 0.0001:
                    cost_str = f"${chunk.usage.cost:.6f}"

                print(
                    f"\nUsage{model_info}{tier_info}: {chunk.usage.input_tokens} in / {chunk.usage.output_tokens} out ({cost_str})",
                    file=sys.stderr,
                )
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stdout)  # Final newline


def main(args: Optional[List[str]] = None) -> None:
    """Main entry point for the kanoa CLI."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="kanoa: AI-powered data science interpretation library."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- Interpret Subcommand ---
    interpret_parser = subparsers.add_parser(
        "interpret", help="Interpret data or context"
    )
    interpret_parser.add_argument(
        "context", nargs="?", help="Context for interpretation"
    )
    interpret_parser.add_argument("--data", help="Path to data file")
    interpret_parser.add_argument("--kb", help="Path to knowledge base file")
    interpret_parser.add_argument("--focus", help="Focus for analysis")
    interpret_parser.add_argument(
        "--system-prompt", help="Override system prompt (use empty string to disable)"
    )
    interpret_parser.add_argument(
        "--backend", default="gemini", help="Backend to use (gemini, openai, claude)"
    )
    interpret_parser.add_argument("--model", help="Model name override")
    interpret_parser.add_argument("--api-key", help="API key override")
    interpret_parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Verbosity level"
    )
    interpret_parser.set_defaults(func=handle_interpret)

    # --- Gemini Subcommand (conditional on backend availability) ---
    try:
        from kanoa.tools import gemini_cache

        gemini_parser = subparsers.add_parser("gemini", help="Gemini backend tools")
        gemini_subparsers = gemini_parser.add_subparsers(
            dest="subcommand", help="Gemini tools"
        )

        # Gemini Cache Tool
        cache_parser = gemini_subparsers.add_parser(
            "cache", help="Manage context caches"
        )
        gemini_cache.register_subcommand(cache_parser)
        gemini_available = True
    except ImportError:
        gemini_available = False

    # --- Vertex AI Subcommand ---
    try:
        from kanoa.tools import vertex_rag

        vertex_parser = subparsers.add_parser("vertex", help="Vertex AI tools")
        vertex_rag.register_subcommand(vertex_parser)
        vertex_available = True
    except ImportError:
        vertex_available = False

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
        if not gemini_available:
            print(
                "Error: Gemini backend not installed. "
                "Install with: pip install kanoa[gemini]",
                file=sys.stderr,
            )
            sys.exit(1)

        from kanoa.tools import gemini_cache

        if parsed_args.subcommand == "cache":
            gemini_cache.handle_command(parsed_args)
        else:
            gemini_parser.print_help()
    elif parsed_args.command == "vertex":
        if not vertex_available:
            print(
                "Error: Vertex AI tools not available. "
                "Install with: pip install kanoa[vertexai]",
                file=sys.stderr,
            )
            sys.exit(1)

        from kanoa.tools import vertex_rag

        vertex_rag.handle_command(parsed_args)
    elif hasattr(parsed_args, "func"):
        parsed_args.func(parsed_args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
