"""EasyEDA Pro MCP Server package."""

__all__ = ["main"]


def main() -> None:
    from .server import mcp
    mcp.run(transport="stdio")
