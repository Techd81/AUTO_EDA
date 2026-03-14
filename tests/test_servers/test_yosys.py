"""Unit tests for Yosys MCP server tools — all EDA calls are mocked."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


# ---------------------------------------------------------------------------
# test_synthesize_tool_not_found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_synthesize_tool_not_found(tmp_path: Path) -> None:
    """yosys 未安装时应返回 error dict，error_code == TOOL_NOT_FOUND。"""
    vf = tmp_path / "top.v"
    vf.write_text("module top(); endmodule")

    from auto_eda.core.errors import ToolNotFoundError

    with patch("auto_eda.core.process.find_tool", side_effect=ToolNotFoundError("yosys")):
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl
        result = await synthesize_rtl(
            verilog_files=[str(vf)],
            top_module="top",
            target="generic",
        )

    assert result["success"] is False
    assert result["error_code"] == "TOOL_NOT_FOUND"
    assert "yosys" in result["error_message"].lower()


# ---------------------------------------------------------------------------
# test_synthesize_file_not_found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_synthesize_file_not_found() -> None:
    """输入 Verilog 文件不存在时应抛出 ValidationError 或返回 FILE_NOT_FOUND。"""
    from pydantic import ValidationError

    try:
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl
        result = await synthesize_rtl(
            verilog_files=["/nonexistent/design.v"],
            top_module="top",
            target="generic",
        )
        assert result["success"] is False
        assert "not_found" in result["error_code"].lower() or "file" in result["error_code"].lower()
    except ValidationError:
        pass  # Pydantic rejects missing file — also acceptable


# ---------------------------------------------------------------------------
# test_synthesize_success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_synthesize_success(tmp_path: Path) -> None:
    """mock 成功执行时，返回结构应包含 success=True、data、elapsed_s。"""
    vf = tmp_path / "counter.v"
    vf.write_text("module counter(input clk, output reg q); endmodule")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"modules": {"counter": {"cells": {}, "ports": {}}}}'
    mock_result.stderr = "Yosys 0.45"
    mock_result.timed_out = False

    with patch("auto_eda.core.process.run_tool", new_callable=AsyncMock, return_value=mock_result):
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl
        result = await synthesize_rtl(
            verilog_files=[str(vf)],
            top_module="counter",
            target="generic",
        )

    assert result["success"] is True
    assert "data" in result
    assert "elapsed_s" in result
    assert result["elapsed_s"] >= 0


# ---------------------------------------------------------------------------
# test_stat_success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stat_success(tmp_path: Path) -> None:
    """mock stat 命令成功，返回设计统计信息。"""
    vf = tmp_path / "top.v"
    vf.write_text("module top(); endmodule")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Number of cells: 4\
Number of wires: 8"
    mock_result.stderr = ""
    mock_result.timed_out = False

    with patch("auto_eda.core.process.run_tool", new_callable=AsyncMock, return_value=mock_result):
        from auto_eda.servers.yosys.synthesizer import stat_design
        result = await stat_design(verilog_files=[str(vf)], top_module="top")

    assert result["success"] is True


# ---------------------------------------------------------------------------
# test_check_success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_success(tmp_path: Path) -> None:
    """mock check 命令成功，无语法错误。"""
    vf = tmp_path / "top.v"
    vf.write_text("module top(); endmodule")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Check passed."
    mock_result.stderr = ""
    mock_result.timed_out = False

    with patch("auto_eda.core.process.run_tool", new_callable=AsyncMock, return_value=mock_result):
        from auto_eda.servers.yosys.synthesizer import check_syntax
        result = await check_syntax(verilog_files=[str(vf)], top_module="top")

    assert result["success"] is True
