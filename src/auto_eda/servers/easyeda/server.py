"""EasyEDA Pro MCP Server — 22 tools bridging Claude to 嘉立创EDA via WebSocket.

Architecture:
  Claude (MCP stdio) → this server → EDABridge (WS) → jlc-bridge.eext → EDA client

All tools follow the same pattern as the KiCad server:
  @mcp.tool() + @eda_tool decorator, Pydantic I/O, suggested_next_steps.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from auto_eda.core.base_server import create_server, eda_tool
from auto_eda.core.errors import EDAError, EDAErrorCode

from .bridge import get_bridge
from .models import (
    EdaGetStatusInput, EdaGetStatusResult,
    EdaPingInput, EdaPingResult,
    ExportBOMInput, ExportBOMResult,
    ExportGerberInput, ExportGerberResult,
    ExportPDFInput, ExportPDFResult,
    ExportPickPlaceInput, ExportPickPlaceResult,
    PcbCreateViaInput, PcbCreateViaResult,
    PcbFloodFillInput, PcbFloodFillResult,
    PcbGetStateInput, PcbGetStateResult,
    PcbMoveComponentInput, PcbMoveComponentResult,
    PcbPlaceComponentInput, PcbPlaceComponentResult,
    PcbRouteTrackInput, PcbRouteTrackResult,
    PcbRunDRCInput, PcbRunDRCResult,
    PcbScreenshotInput, PcbScreenshotResult,
    SchAddNetLabelInput, SchAddNetLabelResult,
    SchAddPowerSymbolInput, SchAddPowerSymbolResult,
    SchAddWireInput, SchAddWireResult,
    SchGetNetlistInput, SchGetNetlistResult,
    SchGetStateInput, SchGetStateResult,
    SchPlaceSymbolInput, SchPlaceSymbolResult,
    SchRunERCInput, SchRunERCResult,
    SchUpdatePCBInput, SchUpdatePCBResult,
    Violation,
)

mcp: FastMCP = create_server("auto-eda-easyeda", version="0.1.0")

# Start WS server on import so EDA extension can connect immediately
import asyncio as _asyncio
import threading as _threading

_ws_loop: _asyncio.AbstractEventLoop | None = None


def _start_ws_server_thread() -> None:
    """Run the WS server in a dedicated background thread/event loop."""
    global _ws_loop
    loop = _asyncio.new_event_loop()
    _ws_loop = loop
    bridge = get_bridge()

    async def _run() -> None:
        await bridge.start_server()
        logger.info("EDA bridge server ready — waiting for EasyEDA Pro extension to connect...")
        # Keep loop alive
        await _asyncio.Future()

    loop.run_until_complete(_run())


_t = _threading.Thread(target=_start_ws_server_thread, daemon=True, name="eda-bridge-ws")
_t.start()
import logging as _logging
logger = _logging.getLogger(__name__)


# ===========================================================================
# Connection tools
# ===========================================================================

@mcp.tool()
@eda_tool
async def eda_ping(params: EdaPingInput) -> EdaPingResult:
    """Check if EasyEDA Pro is running and the jlc-bridge extension is connected."""
    bridge = get_bridge()
    connected = await bridge.ping()
    if not connected:
        return EdaPingResult(
            success=False,
            connected=False,
            error=(
                "Cannot reach EasyEDA Pro bridge.\n"
                "1. Open 嘉立创EDA Pro desktop client\n"
                "2. Install jlc-bridge.eext via Settings > Extensions\n"
                "3. Confirm bridge is listening on ws://127.0.0.1:18800"
            ),
        )
    info = await bridge.send_command("sys.getInfo", {})
    return EdaPingResult(
        success=True,
        connected=True,
        eda_version=info.get("edaVersion"),
        bridge_version=info.get("bridgeVersion"),
        suggested_next_steps=[
            "Use eda_get_status to see open documents",
            "Use sch_get_state to inspect the active schematic",
        ],
    )


@mcp.tool()
@eda_tool
async def eda_get_status(params: EdaGetStatusInput) -> EdaGetStatusResult:
    """List all open EDA documents and the currently active one."""
    bridge = get_bridge()
    data = await bridge.send_command("sys.getOpenDocuments", {})
    docs = data.get("documents", [])
    active = data.get("activeDocument")
    return EdaGetStatusResult(
        success=True,
        open_documents=docs,
        active_document=active,
        suggested_next_steps=[
            "Use sch_get_state to inspect the schematic",
            "Use pcb_get_state to inspect the PCB layout",
        ],
    )


# ===========================================================================
# Schematic tools
# ===========================================================================

@mcp.tool()
@eda_tool
async def sch_get_state(params: SchGetStateInput) -> SchGetStateResult:
    """Get current schematic document metadata: symbol count, wire count, net labels."""
    bridge = get_bridge()
    data = await bridge.send_command("sch.getState", {})
    return SchGetStateResult(
        success=True,
        document_name=data.get("name"),
        symbol_count=data.get("symbolCount", 0),
        wire_count=data.get("wireCount", 0),
        net_label_count=data.get("netLabelCount", 0),
        suggested_next_steps=[
            "Use sch_place_symbol to add components",
            "Use sch_run_erc to check electrical rules",
        ],
    )


@mcp.tool()
@eda_tool
async def sch_place_symbol(params: SchPlaceSymbolInput) -> SchPlaceSymbolResult:
    """Place a component symbol on the schematic by LCSC part number."""
    bridge = get_bridge()
    data = await bridge.send_command("sch.placeSymbol", {
        "lcsc": params.lcsc,
        "x": params.x,
        "y": params.y,
        "rotation": params.rotation,
    })
    ref = data.get("ref")
    return SchPlaceSymbolResult(
        success=True,
        ref=ref,
        lcsc=params.lcsc,
        suggested_next_steps=[
            "Use sch_add_wire to connect pins",
            "Use sch_add_net_label to name key nets",
        ],
    )


@mcp.tool()
@eda_tool
async def sch_add_wire(params: SchAddWireInput) -> SchAddWireResult:
    """Draw a wire segment between two schematic coordinates (in mil)."""
    bridge = get_bridge()
    await bridge.send_command("sch.addWire", {
        "x1": params.x1, "y1": params.y1,
        "x2": params.x2, "y2": params.y2,
    })
    return SchAddWireResult(
        success=True,
        suggested_next_steps=["Continue wiring or use sch_add_net_label for named nets"],
    )


@mcp.tool()
@eda_tool
async def sch_add_net_label(params: SchAddNetLabelInput) -> SchAddNetLabelResult:
    """Add a net label (e.g. VCC, GND, SWDIO) to the schematic."""
    bridge = get_bridge()
    await bridge.send_command("sch.addNetLabel", {
        "name": params.name,
        "x": params.x,
        "y": params.y,
        "rotation": params.rotation,
    })
    return SchAddNetLabelResult(
        success=True,
        suggested_next_steps=[
            "Use sch_add_power_symbol for VCC/GND power ports",
            "Use sch_run_erc when all connections are complete",
        ],
    )


@mcp.tool()
@eda_tool
async def sch_add_power_symbol(params: SchAddPowerSymbolInput) -> SchAddPowerSymbolResult:
    """Place a power symbol (VCC, GND, 3V3, 5V, VBUS) on the schematic."""
    bridge = get_bridge()
    await bridge.send_command("sch.addPowerSymbol", {
        "name": params.name,
        "x": params.x,
        "y": params.y,
    })
    return SchAddPowerSymbolResult(
        success=True,
        suggested_next_steps=["Use sch_run_erc to verify power connections"],
    )


@mcp.tool()
@eda_tool
async def sch_run_erc(params: SchRunERCInput) -> SchRunERCResult:
    """Run Electrical Rules Check on the active schematic. Returns violation list."""
    bridge = get_bridge()
    data = await bridge.send_command("sch.runERC", {})
    raw = data.get("violations", [])
    violations = [
        Violation(
            severity=v.get("severity", "error"),
            rule=v.get("rule", "unknown"),
            description=v.get("description", ""),
            location=v.get("location", ""),
        )
        for v in raw
    ]
    error_count = sum(1 for v in violations if v.severity == "error")
    warning_count = len(violations) - error_count
    next_steps = []
    if error_count:
        next_steps.append(f"Fix {error_count} ERC error(s) before updating PCB")
    else:
        next_steps.append("ERC passed — use sch_update_pcb to sync to PCB layout")
    return SchRunERCResult(
        success=True,
        violation_count=len(violations),
        error_count=error_count,
        warning_count=warning_count,
        violations=violations,
        suggested_next_steps=next_steps,
    )


@mcp.tool()
@eda_tool
async def sch_get_netlist(params: SchGetNetlistInput) -> SchGetNetlistResult:
    """Extract the net list from the active schematic."""
    bridge = get_bridge()
    data = await bridge.send_command("sch.getNetlist", {})
    nets = data.get("nets", [])
    return SchGetNetlistResult(
        success=True,
        net_count=len(nets),
        nets=nets,
        suggested_next_steps=["Use sch_update_pcb to push net changes to PCB"],
    )


@mcp.tool()
@eda_tool
async def sch_update_pcb(params: SchUpdatePCBInput) -> SchUpdatePCBResult:
    """Synchronise schematic changes to the PCB layout (import netlist)."""
    bridge = get_bridge()
    data = await bridge.send_command("sch.updatePCB", {})
    return SchUpdatePCBResult(
        success=True,
        added_footprints=data.get("added", 0),
        removed_footprints=data.get("removed", 0),
        suggested_next_steps=[
            "Use pcb_get_state to confirm footprints",
            "Use pcb_place_component to arrange components",
        ],
    )


# ===========================================================================
# PCB tools
# ===========================================================================

@mcp.tool()
@eda_tool
async def pcb_get_state(params: PcbGetStateInput) -> PcbGetStateResult:
    """Get PCB document metadata: board size, layer count, component count."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.getState", {})
    return PcbGetStateResult(
        success=True,
        document_name=data.get("name"),
        board_width_mil=data.get("widthMil"),
        board_height_mil=data.get("heightMil"),
        layer_count=data.get("layerCount", 0),
        component_count=data.get("componentCount", 0),
        net_count=data.get("netCount", 0),
        suggested_next_steps=[
            "Use pcb_place_component to position footprints",
            "Use pcb_run_drc to check design rules",
        ],
    )


@mcp.tool()
@eda_tool
async def pcb_place_component(params: PcbPlaceComponentInput) -> PcbPlaceComponentResult:
    """Place a footprint on the PCB by LCSC part number at given coordinates."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.placeComponent", {
        "lcsc": params.lcsc,
        "x": params.x,
        "y": params.y,
        "rotation": params.rotation,
        "layer": params.layer,
    })
    return PcbPlaceComponentResult(
        success=True,
        ref=data.get("ref"),
        suggested_next_steps=[
            "Use pcb_move_component to fine-tune position",
            "Use pcb_run_drc after placing all components",
        ],
    )


@mcp.tool()
@eda_tool
async def pcb_move_component(params: PcbMoveComponentInput) -> PcbMoveComponentResult:
    """Move a component to new coordinates. Optionally update rotation."""
    bridge = get_bridge()
    cmd_params: dict = {"ref": params.ref, "x": params.x, "y": params.y}
    if params.rotation is not None:
        cmd_params["rotation"] = params.rotation
    await bridge.send_command("pcb.moveComponent", cmd_params)
    return PcbMoveComponentResult(
        success=True,
        ref=params.ref,
        suggested_next_steps=["Use pcb_run_drc to verify spacing after move"],
    )


@mcp.tool()
@eda_tool
async def pcb_route_track(params: PcbRouteTrackInput) -> PcbRouteTrackResult:
    """Route a track segment between two PCB coordinates on a specified copper layer."""
    bridge = get_bridge()
    await bridge.send_command("pcb.routeTrack", {
        "net": params.net,
        "x1": params.x1, "y1": params.y1,
        "x2": params.x2, "y2": params.y2,
        "layer": params.layer,
        "widthMil": params.width_mil,
    })
    return PcbRouteTrackResult(
        success=True,
        suggested_next_steps=[
            "Continue routing or use pcb_flood_fill for ground plane",
            "Use pcb_run_drc to verify clearance",
        ],
    )


@mcp.tool()
@eda_tool
async def pcb_create_via(params: PcbCreateViaInput) -> PcbCreateViaResult:
    """Place a through-hole via connecting top and bottom copper layers."""
    bridge = get_bridge()
    await bridge.send_command("pcb.createVia", {
        "net": params.net,
        "x": params.x, "y": params.y,
        "drillMil": params.drill_mil,
        "outerMil": params.outer_mil,
    })
    return PcbCreateViaResult(
        success=True,
        suggested_next_steps=["Use pcb_run_drc to check via clearance"],
    )


@mcp.tool()
@eda_tool
async def pcb_flood_fill(params: PcbFloodFillInput) -> PcbFloodFillResult:
    """Pour a copper flood fill for the specified net on a layer (default GND/B_Cu)."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.floodFill", {
        "net": params.net,
        "layer": params.layer,
        "clearanceMil": params.clearance_mil,
    })
    return PcbFloodFillResult(
        success=True,
        poured_area_mm2=data.get("areamm2"),
        suggested_next_steps=[
            "Use pcb_run_drc to verify fill clearances",
            "Use pcb_screenshot to visually confirm fill",
        ],
    )


@mcp.tool()
@eda_tool
async def pcb_run_drc(params: PcbRunDRCInput) -> PcbRunDRCResult:
    """Run Design Rule Check on the active PCB. Returns all violations."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.runDRC", {})
    raw = data.get("violations", [])
    violations = [
        Violation(
            severity=v.get("severity", "error"),
            rule=v.get("rule", "unknown"),
            description=v.get("description", ""),
            location=v.get("location", ""),
        )
        for v in raw
    ]
    error_count = sum(1 for v in violations if v.severity == "error")
    warning_count = len(violations) - error_count
    next_steps = []
    if error_count:
        next_steps.append(f"Fix {error_count} DRC error(s) before exporting Gerbers")
    else:
        next_steps.append("DRC passed — use export_gerber to generate manufacturing files")
    next_steps.append("Use pcb_screenshot to capture current layout")
    return PcbRunDRCResult(
        success=True,
        violation_count=len(violations),
        error_count=error_count,
        warning_count=warning_count,
        violations=violations,
        suggested_next_steps=next_steps,
    )


@mcp.tool()
@eda_tool
async def pcb_screenshot(params: PcbScreenshotInput) -> PcbScreenshotResult:
    """Capture a screenshot of the current PCB view. Returns path or base64 PNG."""
    bridge = get_bridge()
    cmd_params: dict = {}
    if params.output_path:
        cmd_params["outputPath"] = params.output_path
    data = await bridge.send_command("pcb.screenshot", cmd_params)
    return PcbScreenshotResult(
        success=True,
        output_path=data.get("path"),
        base64_png=data.get("base64"),
        suggested_next_steps=[
            "Review layout visually before exporting",
            "Use export_gerber to generate manufacturing files",
        ],
    )


# ===========================================================================
# Export tools
# ===========================================================================

@mcp.tool()
@eda_tool
async def export_gerber(params: ExportGerberInput) -> ExportGerberResult:
    """Export Gerber + drill files for PCB fabrication (e.g. JLCPCB)."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.exportGerber", {
        "outputDir": params.output_dir,
    })
    files = data.get("files", [])
    return ExportGerberResult(
        success=True,
        output_dir=params.output_dir,
        files=files,
        file_count=len(files),
        suggested_next_steps=[
            "Upload Gerber ZIP to https://jlcpcb.com for instant quote",
            "Use export_bom for JLCPCB SMT assembly service",
        ],
    )


@mcp.tool()
@eda_tool
async def export_bom(params: ExportBOMInput) -> ExportBOMResult:
    """Export Bill of Materials with LCSC part numbers for JLCPCB one-click ordering."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.exportBOM", {
        "outputPath": params.output_path,
        "format": params.format,
    })
    return ExportBOMResult(
        success=True,
        output_path=params.output_path,
        component_count=data.get("componentCount", 0),
        unique_parts=data.get("uniqueParts", 0),
        suggested_next_steps=[
            "Use export_pick_place for SMT assembly CPL file",
            "Upload BOM + CPL to JLCPCB for SMT assembly quote",
        ],
    )


@mcp.tool()
@eda_tool
async def export_pick_place(params: ExportPickPlaceInput) -> ExportPickPlaceResult:
    """Export pick-and-place (CPL) file for SMT assembly."""
    bridge = get_bridge()
    data = await bridge.send_command("pcb.exportPickPlace", {
        "outputPath": params.output_path,
    })
    return ExportPickPlaceResult(
        success=True,
        output_path=params.output_path,
        component_count=data.get("componentCount", 0),
        suggested_next_steps=[
            "Upload Gerber + BOM + CPL to JLCPCB for full turnkey order",
        ],
    )


@mcp.tool()
@eda_tool
async def export_pdf(params: ExportPDFInput) -> ExportPDFResult:
    """Export schematic or PCB layout as PDF."""
    bridge = get_bridge()
    await bridge.send_command("doc.exportPDF", {
        "outputPath": params.output_path,
        "target": params.target,
    })
    return ExportPDFResult(
        success=True,
        output_path=params.output_path,
        suggested_next_steps=["Share PDF for design review or documentation"],
    )


# ===========================================================================
# High-level orchestration tool
# ===========================================================================

from pydantic import BaseModel as _BaseModel


class DrawSTM32Input(_BaseModel):
    output_dir: str = "D:/AUTO_EDA/project/stm32_output"


class DrawSTM32Result(_BaseModel):
    success: bool
    summary: str
    screenshot_path: str | None = None
    gerber_dir: str | None = None
    bom_path: str | None = None
    cpl_path: str | None = None
    erc_violations: int = 0
    drc_violations: int = 0
    error: str | None = None
    suggested_next_steps: list[str] = []


@mcp.tool()
@eda_tool
async def draw_stm32_minimum_system(params: DrawSTM32Input) -> DrawSTM32Result:
    """Draw a complete STM32F103C8T6 minimum system board automatically.

    Executes the full 14-step pipeline:
      schematic symbols -> power/nets -> ERC -> PCB sync -> layout ->
      copper pour -> DRC -> screenshot -> Gerber + BOM + CPL export.

    This is the single entry-point for: 'STM32F103C8T6 minimum system board'
    """
    from .stm32_flow import draw_minimum_system

    result = await draw_minimum_system(output_dir=params.output_dir)

    next_steps: list[str] = []
    if result.success:
        next_steps = [
            f"Upload {result.gerber_dir} to https://jlcpcb.com for PCB quote",
            f"Upload {result.bom_path} + {result.cpl_path} for SMT assembly",
            "Use pcb_screenshot to review layout",
            "Use pcb_run_drc to re-check after any manual edits",
        ]
    elif result.abort_reason:
        next_steps = [
            "Fix the reported issue in EasyEDA Pro",
            "Re-run draw_stm32_minimum_system after fixing",
        ]

    return DrawSTM32Result(
        success=result.success,
        summary=result.summary(),
        screenshot_path=result.screenshot_path,
        gerber_dir=result.gerber_dir,
        bom_path=result.bom_path,
        cpl_path=result.cpl_path,
        erc_violations=result.erc_violations,
        drc_violations=result.drc_violations,
        error=result.abort_reason,
        suggested_next_steps=next_steps,
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
