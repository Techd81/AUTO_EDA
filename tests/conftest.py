from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_verilog(tmp_path: Path) -> Path:
    content = '''module counter #(parameter WIDTH=8) (
    input clk, input rst_n,
    output reg [WIDTH-1:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= 0;
        else count <= count + 1;
    end
endmodule'''
    f = tmp_path / "counter.v"
    f.write_text(content)
    return f


@pytest.fixture
def mock_process_result():
    """成功的 ProcessResult stub，不依赖真实子进程。"""
    try:
        from auto_eda.core.process import ProcessResult
        return ProcessResult(returncode=0, stdout="", stderr="", timed_out=False)
    except ImportError:
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        result.timed_out = False
        return result


@pytest.fixture
def mock_run_tool(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    mock.return_value = MagicMock(returncode=0, stdout="", stderr="", timed_out=False)
    monkeypatch.setattr("auto_eda.core.process.run_tool", mock)
    return mock
