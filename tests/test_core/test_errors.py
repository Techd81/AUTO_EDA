"""Unit tests for auto_eda.core.errors — error class hierarchy and behaviour."""
from __future__ import annotations

import pytest
from auto_eda.core.errors import (
    EDAError,
    EDAErrorCode,
    ToolNotFoundError,
    ToolExecutionError,
    TimeoutError,
)


def test_tool_not_found_error_code() -> None:
    err = ToolNotFoundError("yosys")
    assert err.code == EDAErrorCode.TOOL_NOT_FOUND


def test_tool_not_found_error_message_contains_tool_name() -> None:
    err = ToolNotFoundError("yosys")
    assert "yosys" in str(err)


def test_tool_not_found_error_has_suggested_fix() -> None:
    err = ToolNotFoundError("yosys")
    assert err.suggested_fix


def test_tool_execution_error_code() -> None:
    err = ToolExecutionError("yosys", 1, "Error: syntax error")
    assert err.code == EDAErrorCode.TOOL_EXECUTION_FAILED


def test_tool_execution_error_returncode() -> None:
    err = ToolExecutionError("yosys", 1, "Error: syntax error")
    assert err.returncode == 1  # type: ignore[attr-defined]


def test_timeout_error_code() -> None:
    err = TimeoutError("openroad", 300.0)
    assert err.code == EDAErrorCode.TIMEOUT


def test_timeout_error_message_contains_duration() -> None:
    err = TimeoutError("openroad", 300.0)
    assert "300" in str(err)


def test_error_to_dict_error_code_field() -> None:
    err = ToolNotFoundError("klayout")
    d = err.to_dict()
    assert d["error_code"] == "TOOL_NOT_FOUND"


def test_error_to_dict_tool_field() -> None:
    err = ToolNotFoundError("klayout")
    d = err.to_dict()
    assert d["tool"] == "klayout"


def test_error_to_dict_suggested_fix_present() -> None:
    err = ToolNotFoundError("klayout")
    d = err.to_dict()
    assert "suggested_fix" in d


def test_eda_error_is_exception() -> None:
    err = ToolNotFoundError("verilator")
    assert isinstance(err, Exception)
    assert isinstance(err, EDAError)
