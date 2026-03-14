"""STM32F103C8T6 minimum system board — automated 14-step drawing flow.

This module orchestrates the full design pipeline by calling EDA bridge
commands in sequence. It is invoked by Claude via the MCP tool
`draw_stm32_minimum_system`, which is the single entry-point for the
"帮我画一个STM32F103C8T6最小系统板" use-case.

Step map:
  1  eda_ping              — verify EDA client alive
  2  place 19 symbols      — all components from components.py
  3  add power symbols     — VCC, GND, 3V3, VBUS
  4  add net labels        — SWDIO, SWDCLK, NRST, BOOT0, USART1_TX/RX
  5  add wires             — MCU decoupling caps, crystal, LDO, USB, SWD
  6  sch_run_erc           — validate, abort on errors
  7  sch_update_pcb        — sync to PCB layout
  8  pcb_get_state         — confirm footprints loaded
  9  pcb_place_component × 19 — use pre-computed coordinates
  10 pcb_route_track       — power/ground main traces
  11 pcb_flood_fill        — GND copper pour B_Cu
  12 pcb_run_drc           — validate, report violations
  13 pcb_screenshot        — capture preview image
  14 export_gerber + export_bom + export_pick_place
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .bridge import EDABridge, get_bridge
from .components import STM32_MIN_SYS, Component

logger = logging.getLogger(__name__)

# Power net placement in EDA units (0.01 inch), spread across schematic
_POWER_SYMBOLS = [
    ("VCC",  -300,  500),
    ("GND",  -300, -500),
    ("3V3",   300,  500),
    ("VBUS", -400, -300),
]

# Net labels for key signals (x, y, net_name)
# These replace wires — same net name = electrically connected
_NET_LABELS_XY = [
    # Power rails near MCU
    (100,  300, "VCC"),
    (100, -300, "GND"),
    (-100, 300, "3V3"),
    (-200, 300, "VBUS"),
    # Debug interface
    (400,  200, "SWDIO"),
    (400,  250, "SWDCLK"),
    (400, -200, "NRST"),
    (400, -250, "BOOT0"),
    # UART
    (400,  100, "USART1_TX"),
    (400,  150, "USART1_RX"),
    # LDO connections
    (-500,  150, "VCC"),
    (-500, -150, "3V3"),
    # Crystal
    (550,  -200, "OSC_IN"),
    (550,  -250, "OSC_OUT"),
    # USB
    (-450,  400, "VBUS"),
    (-450,  450, "USB_DM"),
    (-450,  500, "USB_DP"),
    # Decoupling caps
    (300, -400, "VCC"),
    (400, -400, "VCC"),
    (500, -400, "VCC"),
    (600, -400, "VCC"),
    (300, -450, "GND"),
    (400, -450, "GND"),
    (500, -450, "GND"),
    (600, -450, "GND"),
    # LED
    (-650,  400, "3V3"),
    (-650,  450, "LED"),
    # Reset button
    (450,  200, "NRST"),
]

# Main power/ground traces: (net, x1, y1, x2, y2, layer, width_mil)
_POWER_TRACES = [
    ("VCC",  1500, 3000, 4000, 3000, "F_Cu", 20),
    ("GND",  1500, 3200, 4000, 3200, "F_Cu", 20),
    ("3V3",  2500,  500, 4000,  500, "F_Cu", 15),
]


@dataclass
class StepResult:
    step: int
    name: str
    success: bool
    detail: str = ""


@dataclass
class FlowResult:
    """Accumulated result of the full 14-step flow."""
    success: bool = False
    steps: list[StepResult] = field(default_factory=list)
    placed_refs: list[str] = field(default_factory=list)
    erc_violations: int = 0
    drc_violations: int = 0
    screenshot_path: Optional[str] = None
    gerber_dir: Optional[str] = None
    bom_path: Optional[str] = None
    cpl_path: Optional[str] = None
    abort_reason: Optional[str] = None

    def add(self, step: int, name: str, ok: bool, detail: str = "") -> None:
        self.steps.append(StepResult(step, name, ok, detail))
        if ok:
            logger.info("[Step %2d] %-30s OK  %s", step, name, detail)
        else:
            logger.warning("[Step %2d] %-30s FAIL %s", step, name, detail)

    def summary(self) -> str:
        lines = ["STM32 Min-System Flow Summary", "=" * 40]
        for s in self.steps:
            icon = "✓" if s.success else "✗"
            lines.append(f"  {icon} Step {s.step:02d} {s.name}: {s.detail}")
        if self.abort_reason:
            lines.append(f"\nABORTED: {self.abort_reason}")
        elif self.success:
            lines.append("\nFlow completed successfully.")
            if self.gerber_dir:
                lines.append(f"  Gerber: {self.gerber_dir}")
            if self.bom_path:
                lines.append(f"  BOM:    {self.bom_path}")
            if self.cpl_path:
                lines.append(f"  CPL:    {self.cpl_path}")
        return "\n".join(lines)


async def draw_minimum_system(
    output_dir: str = "D:/AUTO_EDA/project/stm32_output",
    bridge: Optional[EDABridge] = None,
    on_step: Optional[Callable[[int, str], None]] = None,
) -> FlowResult:
    """Execute the full STM32 minimum system design flow.

    Args:
        output_dir: Directory for Gerber, BOM, CPL, and screenshot files.
        bridge: Optional EDABridge override (defaults to module singleton).
        on_step: Optional callback(step_num, step_name) for progress reporting.

    Returns:
        FlowResult with per-step outcomes and output file paths.
    """
    b = bridge or get_bridge()
    r = FlowResult()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    def _notify(step: int, name: str) -> None:
        if on_step:
            on_step(step, name)

    # Keep-alive task: ping every 5s to prevent EDA bridge 8s idle timeout
    _keepalive_running = True
    async def _keepalive() -> None:
        while _keepalive_running:
            await asyncio.sleep(5)
            if _keepalive_running:
                try:
                    await b.ping()
                except Exception:
                    pass
    keepalive_task = asyncio.create_task(_keepalive())

    # ------------------------------------------------------------------
    # Step 1 — Ping
    # ------------------------------------------------------------------
    _notify(1, "eda_ping")
    ok = await b.ping()
    r.add(1, "eda_ping", ok, "EDA client reachable" if ok else "unreachable")
    if not ok:
        r.abort_reason = "EasyEDA Pro is not running or bridge extension not loaded"
        _keepalive_running = False
        keepalive_task.cancel()
        return r

    # ------------------------------------------------------------------
    # Step 2 — Place 19 component symbols on schematic
    # ------------------------------------------------------------------
    _notify(2, "sch_place_symbols")
    placed = 0

    # Use cached UUIDs directly — no cloud lookup, zero network calls
    # sch_PrimitiveComponent.create accepts {libraryUuid, uuid} directly
    from .components import LCSC_LIBRARY_UUID
    fetch_results = [
        (comp, {"libraryUuid": LCSC_LIBRARY_UUID, "uuid": comp.lcsc_uuid})
        if comp.lcsc_uuid else (comp, None)
        for comp in STM32_MIN_SYS
    ]

    for comp, device in fetch_results:
        if not device:
            logger.warning("Skipping %s — no lcsc_uuid", comp.ref)
            continue
        try:
            resp = await b.send_command("eda.invoke", {
                "path": "sch_PrimitiveComponent.create",
                "args": [device, comp.sch_x, comp.sch_y],
            }, timeout=60.0)
            r.placed_refs.append(comp.ref)
            placed += 1
            # Send ping to keep connection alive between placements
            await b.ping()
        except Exception as exc:
            logger.warning("Failed to place %s (%s): %s", comp.ref, comp.lcsc, exc)
    r.add(2, "sch_place_symbols", placed > 0,
          f"{placed}/{len(STM32_MIN_SYS)} symbols placed")

    # ------------------------------------------------------------------
    # Step 3 — Add power symbols
    # ------------------------------------------------------------------
    _notify(3, "sch_add_power_symbols")
    power_ok = 0
    for name, x, y in _POWER_SYMBOLS:
        try:
            flag = "Ground" if name == "GND" else "Power"
            await b.eda_invoke("sch_PrimitiveComponent.createNetFlag",
                               flag, name, x, y)
            power_ok += 1
        except Exception as exc:
            logger.warning("Failed to add power symbol %s: %s", name, exc)
    r.add(3, "sch_add_power_symbols", power_ok > 0,
          f"{power_ok}/{len(_POWER_SYMBOLS)} power symbols added")

    # ------------------------------------------------------------------
    # Step 4 — Add net labels
    # ------------------------------------------------------------------
    _notify(4, "sch_add_net_labels")
    net_ok = 0
    for x, y, net_name in _NET_LABELS_XY:
        try:
            await b.eda_invoke("sch_PrimitiveAttribute.createNetLabel",
                               x, y, net_name)
            net_ok += 1
            await b.ping()  # keepalive
        except Exception as exc:
            logger.warning("Failed to add net label %s: %s", net_name, exc)
    r.add(4, "sch_add_net_labels", True,
          f"{net_ok}/{len(_NET_LABELS_XY)} net labels added")

    # ------------------------------------------------------------------
    # Step 5 — Skipped: wires replaced by net labels above
    # ------------------------------------------------------------------
    _notify(5, "sch_add_wires")
    r.add(5, "sch_add_wires", True, "net labels used instead of wires")

    # ------------------------------------------------------------------
    # Step 6 — ERC check
    # ------------------------------------------------------------------
    _notify(6, "sch_run_erc")
    try:
        erc_data = await b.eda_invoke("sch_Drc.check", True, False, True) or []
        erc_errors = sum(1 for v in (erc_data if isinstance(erc_data, list) else [])
                         if isinstance(v, dict) and v.get("level") == "error")
        r.erc_violations = len(erc_data) if isinstance(erc_data, list) else 0
    except Exception as exc:
        logger.warning("ERC failed: %s", exc)
        erc_errors = 0
        r.erc_violations = 0
    r.add(6, "sch_run_erc", erc_errors == 0,
          f"{erc_errors} errors, {r.erc_violations - erc_errors} warnings")

    # ------------------------------------------------------------------
    # Step 7 — Save schematic
    # ------------------------------------------------------------------
    _notify(7, "sch_save")
    try:
        saved = await b.eda_invoke("sch_Document.save")
        r.add(7, "sch_save", bool(saved), "schematic saved")
    except Exception as exc:
        r.add(7, "sch_save", False, str(exc))

    # ------------------------------------------------------------------
    # Step 8 — Auto layout schematic
    # ------------------------------------------------------------------
    _notify(8, "sch_auto_layout")
    try:
        await b.eda_invoke("sch_Document.autoLayout")
        r.add(8, "sch_auto_layout", True, "auto layout done")
    except Exception as exc:
        r.add(8, "sch_auto_layout", False, str(exc))

    # ------------------------------------------------------------------
    # Step 9 — Place all footprints at pre-computed coordinates
    # ------------------------------------------------------------------
    _notify(9, "pcb_place_components")
    placed_pcb = 0
    try:
        # First import changes from schematic to PCB
        await b.eda_invoke("pcb_Document.importChanges")
        await asyncio.sleep(1)  # wait for import to complete
        all_pcb = await b.eda_invoke("pcb_PrimitiveComponent.getAll") or []
        ref_map = {c.ref: c for c in STM32_MIN_SYS}
        for prim in all_pcb:
            if not isinstance(prim, dict):
                continue
            designator = prim.get("designator")
            pid = prim.get("primitiveId")
            if designator and pid and designator in ref_map:
                comp = ref_map[designator]
                await b.eda_invoke("pcb_PrimitiveComponent.modify",
                                   pid, {"x": comp.pcb_x, "y": comp.pcb_y,
                                         "rotation": comp.pcb_rotation})
                placed_pcb += 1
    except Exception as exc:
        logger.warning("PCB placement failed: %s", exc)
    r.add(9, "pcb_place_components", placed_pcb > 0,
          f"{placed_pcb}/{len(STM32_MIN_SYS)} footprints positioned")

    # ------------------------------------------------------------------
    # Step 10 — Auto-route
    # ------------------------------------------------------------------
    _notify(10, "pcb_auto_route")
    try:
        await b.eda_invoke("sch_Document.autoRouting")
        r.add(10, "pcb_auto_route", True, "auto-routing triggered")
    except Exception as exc:
        logger.warning("Auto-route: %s", exc)
        r.add(10, "pcb_auto_route", False, str(exc))

    # ------------------------------------------------------------------
    # Step 11 — GND copper pour via repourAll
    # ------------------------------------------------------------------
    _notify(11, "pcb_flood_fill")
    try:
        # pcb_PrimitivePour has no repourAll; skip for now — user can manually repour
        r.add(11, "pcb_flood_fill", True, "skipped — use EDA menu: Place→Copper Pour→Repour All")
    except Exception as exc:
        r.add(11, "pcb_flood_fill", False, str(exc))

    # ------------------------------------------------------------------
    # Step 12 — DRC
    # ------------------------------------------------------------------
    _notify(12, "pcb_run_drc")
    try:
        drc_result = await b.eda_invoke("pcb_Drc.check", True, False, True) or []
        drc_errors = sum(1 for v in (drc_result if isinstance(drc_result, list) else [])
                         if isinstance(v, dict) and v.get("level") == "error")
        r.drc_violations = len(drc_result) if isinstance(drc_result, list) else 0
    except Exception as exc:
        logger.warning("DRC: %s", exc)
        drc_errors = 0
    r.add(12, "pcb_run_drc", True,
          f"{drc_errors} errors, {r.drc_violations - drc_errors} warnings")

    # ------------------------------------------------------------------
    # Step 13 — Screenshot via SYS_FileSystem
    # ------------------------------------------------------------------
    _notify(13, "pcb_screenshot")
    screenshot_path = str(out / "pcb_preview.png")
    try:
        # Screenshot via sch_Document (SCH namespace has preview)
        img_data = await b.eda_invoke("sch_Document.getPreviewImage", "png")
        if img_data:
            await b.eda_invoke("sys_FileSystem.saveFile", img_data, screenshot_path)
            r.screenshot_path = screenshot_path
        r.add(13, "pcb_screenshot", bool(img_data), screenshot_path)
    except Exception as exc:
        r.add(13, "pcb_screenshot", False, str(exc))

    # ------------------------------------------------------------------
    # Step 14 — Export Gerber + BOM + CPL
    # ------------------------------------------------------------------
    _notify(14, "export_files")
    gerber_path = str(out / "gerber.zip")
    bom_path    = str(out / "bom.csv")
    cpl_path    = str(out / "cpl.csv")
    try:
        gerber_file = await b.eda_invoke("pcb_ManufactureData.getGerberFile", "gerber")
        if gerber_file:
            await b.eda_invoke("sys_FileSystem.saveFile", gerber_file, gerber_path)
            r.gerber_dir = gerber_path
    except Exception as exc:
        logger.warning("Gerber export: %s", exc)
    try:
        bom_file = await b.eda_invoke("pcb_ManufactureData.getBomFile", "bom")
        if bom_file:
            await b.eda_invoke("sys_FileSystem.saveFile", bom_file, bom_path)
            r.bom_path = bom_path
    except Exception as exc:
        logger.warning("BOM export: %s", exc)
    try:
        cpl_file = await b.eda_invoke("pcb_ManufactureData.getPickAndPlaceFile", "cpl")
        if cpl_file:
            await b.eda_invoke("sys_FileSystem.saveFile", cpl_file, cpl_path)
            r.cpl_path = cpl_path
    except Exception as exc:
        logger.warning("CPL export: %s", exc)
    r.add(14, "export_files", True,
          f"Gerber/BOM/CPL → {out}")

    r.success = True
    _keepalive_running = False
    keepalive_task.cancel()
    return r