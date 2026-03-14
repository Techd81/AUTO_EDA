from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ToolSuccess(BaseModel):
    """Standard wrapper for successful MCP tool returns."""

    success: bool = True
    data: dict[str, Any]
    warnings: list[str] = []
    tool_used: str = ""
    elapsed_s: float = 0.0


class ToolFailure(BaseModel):
    """Standard wrapper for expected tool failures (no exception raised)."""

    success: bool = False
    error_code: int
    error_message: str
    detail: str | None = None
    tool_output: str | None = None


def format_mcp_error(error: Exception) -> str:
    """Format any exception as MCP tool error text."""
    from .errors import EDAError

    if isinstance(error, EDAError):
        return error.to_mcp_error_text()
    return f"[ERROR] Unexpected error: {type(error).__name__}: {error}"
