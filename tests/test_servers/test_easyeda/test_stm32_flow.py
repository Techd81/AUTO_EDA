"""Tests for stm32_flow — exercises the 14-step pipeline with a mock bridge."""
from __future__ import annotations

import pytest
from typing import Any

from auto_eda.servers.easyeda.bridge import EDABridge
from auto_eda.servers.easyeda.components import STM32_MIN_SYS, STM32_BY_REF
from auto_eda.servers.easyeda.stm32_flow import draw_minimum_system


# ---------------------------------------------------------------------------
# Mock bridge that returns canned happy-path responses
# ---------------------------------------------------------------------------

class _HappyBridge(EDABridge):
    """Returns success for every command, simulating a fully connected EDA client."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, dict]] = []

    async def ping(self) -> bool:
        self.calls.append(("ping", {}))
        return True

    async def send_command(self, method: str, params: dict,
                           timeout: float = 30.0) -> dict:
        self.calls.append((method, params))
        # eda.invoke wraps everything — return minimal valid structure
        if method == "eda.invoke":
            path = params.get("path", "")
            if "create" in path.lower():
                return {"result": {"primitiveId": "mock-pid"}}
            if "getAll" in path.lower():
                return {"result": []}
            if "check" in path.lower() or "Drc" in path:
                return {"result": []}
            if "save" in path.lower():
                return {"result": True}
            if "getPreviewImage" in path.lower():
                return {"result": "base64data"}
            if "saveFile" in path.lower():
                return {"result": True}
            if "getGerberFile" in path.lower():
                return {"result": "gerber_data"}
            if "getBomFile" in path.lower():
                return {"result": "bom_data"}
            if "getPickAndPlaceFile" in path.lower():
                return {"result": "cpl_data"}
            return {"result": {}}
        return {}

    async def eda_invoke(self, path: str, *args: Any,
                         timeout: float = 30.0) -> Any:
        resp = await self.send_command(
            "eda.invoke", {"path": path, "args": list(args)}, timeout=timeout,
        )
        return resp.get("result")


class _DeadBridge(_HappyBridge):
    """Simulates no EDA connection — ping always fails."""
    async def ping(self) -> bool:
        return False


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
        output_dir="D:/AUTO_EDA/project/test_output",
        bridge=bridge,
    )
    assert result.success is True
    assert result.abort_reason is None
    assert len(result.steps) == 14


@pytest.mark.asyncio
async def test_flow_aborts_on_ping_failure() -> None:
    result = await draw_minimum_system(bridge=_DeadBridge())
    assert result.success is False
    assert result.abort_reason is not None


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
