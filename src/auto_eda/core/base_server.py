from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from mcp.server.fastmcp import FastMCP

from .errors import EDAError
from .result import format_mcp_error

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def create_server(name: str, version: str = "0.1.0") -> FastMCP:
    """Create a FastMCP instance with unified configuration."""
    # FastMCP signature varies by mcp SDK version; pass only name to stay compatible.
    return FastMCP(name)


def eda_tool(func: F) -> F:
    """
    MCP tool decorator: unified exception handling, timing, error formatting.
    Stack after @mcp.tool().
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.monotonic() - start
            logger.debug("%s completed in %.2fs", func.__name__, elapsed)
            return result
        except EDAError as e:
            logger.warning("%s failed: [%s] %s", func.__name__, e.code, e.message)
            return format_mcp_error(e)
        except Exception as e:
            logger.exception("Unexpected error in %s", func.__name__)
            return format_mcp_error(e)
    return wrapper  # type: ignore[return-value]
