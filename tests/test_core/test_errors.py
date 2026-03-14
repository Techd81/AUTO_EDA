"""Unit tests for auto_eda.core.errors — error class hierarchy and behaviour."""
from __future__ import annotations

import pytest
from auto_eda.core.errors import (
    EDAError,
    EDAErrorCode,
    ToolNotFoundError,
    ToolExecutionError,
    ToolTimeoutError,
    FileNotFoundEDAError,
    DependencyMissingError,
)


def test_tool_not_found_error_code() -> None:
    err = ToolNotFoundError("yosys")
    assert err.code == EDAErrorCode.TOOL_NOT_FOUND


def test_tool_not_found_error_message_contains_tool_name() -> None:
    err = ToolNotFoundError("yosys")
    assert "yosys" in str(err)


def test_tool_not_found_error_has_detail() -> None:
    err = ToolNotFoundError("yosys")
    assert err.detail is not None
    assert "PATH" in err.detail


def test_tool_execution_error_code() -> None:
    err = ToolExecutionError("yosys", 1, "Error: syntax error")
    assert err.code == EDAErrorCode.UNKNOWN


def test_tool_execution_error_returncode() -> None:
    err = ToolExecutionError("yosys", 1, "Error: syntax error")
    assert err.returncode == 1


def test_timeout_error_code() -> None:
    err = ToolTimeoutError("openroad", 300)
    assert err.code == EDAErrorCode.TIMEOUT


def test_timeout_error_message_contains_duration() -> None:
    err = ToolTimeoutError("openroad", 300)
    assert "300" in str(err)


def test_error_to_mcp_error_text_contains_code() -> None:
    err = ToolNotFoundError("klayout")
    text = err.to_mcp_error_text()
    assert "2001" in text  # TOOL_NOT_FOUND = 2001


def test_error_to_mcp_error_text_contains_message() -> None:
    err = ToolNotFoundError("klayout")
    text = err.to_mcp_error_text()
    assert "klayout" in text


def test_eda_error_is_exception() -> None:
    err = ToolNotFoundError("verilator")
    assert isinstance(err, Exception)
    assert isinstance(err, EDAError)
