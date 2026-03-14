"""CLI entry point for AUTO_EDA MCP servers."""
from __future__ import annotations
import argparse
import sys


def main() -> None:
    """Launch AUTO_EDA MCP server."""
    parser = argparse.ArgumentParser(
        prog="auto-eda",
        description="AUTO_EDA — 嘉立创EDA Pro MCP Server",
    )
    parser.add_argument(
        "server",
        choices=["easyeda"],
        help="MCP server to launch",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    args = parser.parse_args()

    if args.server == "easyeda":
        from auto_eda.servers.easyeda.server import mcp
    else:
        print(f"Unknown server: {args.server}", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
