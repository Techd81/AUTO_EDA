"""Tests for stm32_flow — exercises the 14-step pipeline with a mock bridge."""
from __future__ import annotations

import json
import pytest

from auto_eda.servers.easyeda.bridge import EDABridge
from auto_eda.servers.easyeda.components import STM32_MIN_SYS, STM32_BY_REF
from auto_eda.servers.easyeda.stm32_flow import draw_minimum_system


# ---------------------------------------------------------------------------
# Mock bridge that returns canned happy-path responses
# ---------------------------------------------------------------------------

class _HappyBridge(EDABridge):
    """Returns success for every command, simulating a fully connected EDA client."""

    def __init__(self) -> None:
        super().__init__(url="ws://mock")
        self.calls: list[tuple[str, dict]] = []

    async def ping(self) -> bool:
        self.calls.append(("ping", {}))
        return True

    async def send_command(self, method: str, params: dict, timeout: float = 30.0) -> dict:
        self.calls.append((method, params))
        # Return minimal valid responses per method
        responses: dict[str, dict] = {
            "sys.getInfo":        {"edaVersion": "2.1.0", "bridgeVersion": "0.1.0"},
            "sch.placeSymbol":    {"ref": params.get("lcsc", "X1")},
            "sch.addPowerSymbol": {},
            "sch.addNetLabel":    {},
            "sch.addWire":        {},
            "sch.runERC":         {"violations": []},
            "sch.updatePCB":      {"added": 19, "removed": 0},
            "pcb.getState":       {"componentCount": 19, "widthMil": 50000, "heightMil": 35000},
            "pcb.moveComponent":  {},
            "pcb.routeTrack":     {},
            "pcb.floodFill":      {"areamm2": 1200.0},
            "pcb.runDRC":         {"violations": []},
            "pcb.screenshot":     {"path": "/tmp/pcb_preview.png"},
            "pcb.exportGerber":   {"files": ["F_Cu.gbr", "B_Cu.gbr", "drill.drl"]},
            "pcb.exportBOM":      {"componentCount": 19, "uniqueParts": 12},
            "pcb.exportPickPlace":{"componentCount": 19},
        }
        return responses.get(method, {})


# ---------------------------------------------------------------------------
# Component table tests
# ---------------------------------------------------------------------------

def test_stm32_component_count() -> None:
    assert len(STM32_MIN_SYS) == 19


def test_all_lcsc_numbers_valid() -> None:
    for comp in STM32_MIN_SYS:
        assert comp.lcsc.startswith("C"), f"{comp.ref} LCSC={comp.lcsc} invalid"
        assert comp.lcsc[1:].isdigit(), f"{comp.ref} LCSC={comp.lcsc} non-numeric"


def test_lookup_by_ref() -> None:
    u1 = STM32_BY_REF["U1"]
    assert u1.lcsc == "C8734"
    assert "STM32" in u1.value


def test_no_duplicate_refs() -> None:
    refs = [c.ref for c in STM32_MIN_SYS]
    assert len(refs) == len(set(refs)), "Duplicate refs found"


# ---------------------------------------------------------------------------
# Flow tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_happy_path_flow() -> None:
    bridge = _HappyBridge()
    result = await draw_minimum_system(
        output_dir="/tmp/stm32_test_output",
        bridge=bridge,
    )
    assert result.success is True
    assert result.abort_reason is None
    assert result.erc_violations == 0
    assert result.drc_violations == 0
    assert result.gerber_dir is not None
    assert result.bom_path is not None
    assert result.cpl_path is not None


@pytest.mark.asyncio
async def test_flow_aborts_on_ping_failure() -> None:
    class _DeadBridge(_HappyBridge):
        async def ping(self) -> bool:
            return False

    result = await draw_minimum_system(bridge=_DeadBridge())
    assert result.success is False
    assert result.abort_reason is not None
    assert "bridge" in result.abort_reason.lower() or "running" in result.abort_reason.lower()


@pytest.mark.asyncio
async def test_flow_aborts_on_erc_errors() -> None:
    class _ERCFailBridge(_HappyBridge):
        async def send_command(self, method: str, params: dict, timeout: float = 30.0) -> dict:
            if method == "sch.runERC":
                return {"violations": [{"severity": "error", "rule": "pin_unconnected",
                                        "description": "Pin unconnected"}]}
            return await super().send_command(method, params, timeout)

    result = await draw_minimum_system(bridge=_ERCFailBridge())
    assert result.success is False
    assert result.erc_violations == 1
    assert "ERC" in result.abort_reason


@pytest.mark.asyncio
async def test_step_callback_called_for_all_14_steps() -> None:
    bridge = _HappyBridge()
    step_log: list[int] = []

    def _on_step(step: int, name: str) -> None:
        step_log.append(step)

    await draw_minimum_system(bridge=bridge, on_step=_on_step)
    assert step_log == list(range(1, 15)), f"Expected steps 1-14, got {step_log}"


@pytest.mark.asyncio
async def test_flow_summary_contains_all_steps() -> None:
    bridge = _HappyBridge()
    result = await draw_minimum_system(bridge=bridge)
    summary = result.summary()
    for step_num in range(1, 15):
        assert f"Step {step_num:02d}" in summary, f"Step {step_num} missing from summary"
