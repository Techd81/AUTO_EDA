"""Unit tests for KiCad MCP server tools — all EDA calls are mocked."""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


# ---------------------------------------------------------------------------
# test_detect_kicad_unavailable
# ---------------------------------------------------------------------------

def test_detect_kicad_unavailable() -> None:
    """kicad-cli 不在 PATH 时，能力探测应返回 UNAVAILABLE 状态。"""
    with patch("shutil.which", return_value=None):
        from auto_eda.adapters.kicad.version_detect import detect_kicad_capabilities, KiCadApiMode
        caps = detect_kicad_capabilities()
    assert caps.api_mode == KiCadApiMode.UNAVAILABLE


# ---------------------------------------------------------------------------
# test_run_drc_success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_drc_success(tmp_path: Path) -> None:
    """mock kicad-cli drc 命令成功执行，返回零违规结果。"""
    pcb_file = tmp_path / "board.kicad_pcb"
    pcb_file.write_text("(kicad_pcb)")

    drc_output = {
        "violations": [],
        "unconnected_items": [],
        "schematic_errors": [],
    }
    report_file = tmp_path / "drc_report.json"
    report_file.write_text(json.dumps(drc_output))

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_result.timed_out = False

    def _write_report(*args: object, **kwargs: object) -> MagicMock:
        # side-effect: write the report that the tool reads back
        return mock_result

    with patch("auto_eda.core.process.run_tool", new_callable=AsyncMock, side_effect=_write_report):
        with patch("auto_eda.servers.kicad.drc.read_drc_report", return_value=drc_output):
            from auto_eda.servers.kicad.drc import run_drc
            result = await run_drc(pcb_file=str(pcb_file))

    assert result["success"] is True
    assert result["data"]["violation_count"] == 0


# ---------------------------------------------------------------------------
# test_export_gerber_success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_gerber_success(tmp_path: Path) -> None:
    """mock kicad-cli export gerbers 成功，返回输出文件列表。"""
    pcb_file = tmp_path / "board.kicad_pcb"
    pcb_file.write_text("(kicad_pcb)")
    out_dir = tmp_path / "gerbers"
    out_dir.mkdir()

    # Simulate gerber files created by the tool
    (out_dir / "board-F_Cu.gtl").write_text("G04 Front copper*")
    (out_dir / "board-B_Cu.gbl").write_text("G04 Back copper*")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_result.timed_out = False

    with patch("auto_eda.core.process.run_tool", new_callable=AsyncMock, return_value=mock_result):
        from auto_eda.servers.kicad.export import export_gerbers
        result = await export_gerbers(
            pcb_file=str(pcb_file),
            output_dir=str(out_dir),
        )

    assert result["success"] is True
    assert len(result["data"]["files"]) >= 2
