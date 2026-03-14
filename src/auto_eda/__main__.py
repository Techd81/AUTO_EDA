"""CLI entry point for AUTO_EDA MCP servers."""
from __future__ import annotations
import argparse
import sys


def main() -> None:
    """Launch AUTO_EDA MCP server."""
    parser = argparse.ArgumentParser(
        prog="auto-eda",
        description="AUTO_EDA MCP Server — AI-driven EDA automation",
    )
    parser.add_argument(
        "server",
        choices=["yosys", "kicad", "verilog", "all"],
        help="MCP server to launch",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    args = parser.parse_args()

    if args.server == "yosys":
        from auto_eda.servers.yosys.server import mcp
    elif args.server == "kicad":
        from auto_eda.servers.kicad.server import mcp
    elif args.server == "verilog":
        from auto_eda.servers.verilog_utils.server import mcp
    elif args.server == "all":
        # Full multi-server mounting is implemented in Phase 1.
        print(
            "The 'all' option is not yet implemented. "
            "Run each server separately:\n"
            "  python -m auto_eda yosys\n"
            "  python -m auto_eda kicad\n"
            "  python -m auto_eda verilog",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(f"Unknown server: {args.server}", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
