from __future__ import annotations

import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from auto_eda.core.base_server import create_server, eda_tool
from auto_eda.core.errors import EDAError, EDAErrorCode

from .cli import (
    export_bom_cli,
    export_gerbers_cli,
    get_board_info_cli,
    run_drc_cli,
    run_erc_cli,
)
from .models import (
    ExportBOMInput,
    ExportBOMResult,
    ExportGerberInput,
    ExportGerberResult,
    GetBoardInfoInput,
    GetBoardInfoResult,
    GetSchematicInfoInput,
    GetSchematicInfoResult,
    ListComponentsInput,
    ListComponentsResult,
    RunDRCInput,
    RunDRCResult,
    RunERCInput,
    RunERCResult,
)
from .version import MIN_KICAD_VERSION, detect_kicad_version

mcp: FastMCP = create_server("auto-eda-kicad", version="0.1.0")

# Detect KiCad capabilities once at import time
_kicad_version = detect_kicad_version()


def _kicad_unavailable_result(tool_name: str) -> str:
    return (
        f"[ERROR 2001] KiCad not found. Tool '{tool_name}' requires kicad-cli in PATH.\n"
        "Install: https://www.kicad.org/download/\n"
        "  Linux:   sudo apt install kicad\n"
        "  macOS:   brew install --cask kicad\n"
        "  Windows: winget install KiCad.KiCad"
    )


@mcp.tool()
@eda_tool
async def get_board_info(params: GetBoardInfoInput) -> GetBoardInfoResult:
    """Read PCB file metadata: dimensions, layer count, footprint count, net count."""
    if not os.path.isfile(params.pcb_file):
        raise EDAError(EDAErrorCode.FILE_NOT_FOUND, f"PCB file not found: {params.pcb_file}")

    data = await get_board_info_cli(params.pcb_file)

    return GetBoardInfoResult(
        success=True,
        pcb_file=params.pcb_file,
        footprint_count=data.get("footprint_count"),
        net_count=data.get("net_count"),
        layer_count=data.get("layer_count"),
        kicad_version=data.get("kicad_version"),
        suggested_next_steps=[
            "Use run_drc to check design rule violations",
            "Use list_components on the paired schematic file",
            "Use export_gerber to generate manufacturing files",
        ],
    )


@mcp.tool()
@eda_tool
async def list_components(params: ListComponentsInput) -> ListComponentsResult:
    """List all components in a KiCad schematic (.kicad_sch)."""
    if _kicad_version is None:
        return ListComponentsResult(
            success=False,
            schematic_file=params.schematic_file,
            error=_kicad_unavailable_result("list_components"),
        )
    if not os.path.isfile(params.schematic_file):
        raise EDAError(
            EDAErrorCode.FILE_NOT_FOUND,
            f"Schematic file not found: {params.schematic_file}",
        )

    # Parse schematic S-expression for component list
    from .cli import _parse_sch_components  # type: ignore[attr-defined]
    components = await _parse_sch_components(
        params.schematic_file, include_power=params.include_power
    )
    return ListComponentsResult(
        success=True,
        schematic_file=params.schematic_file,
        components=components,
        total_count=len(components),
        suggested_next_steps=[
            "Use export_bom to generate a Bill of Materials file",
            "Use run_erc to check electrical rule violations",
        ],
    )


@mcp.tool()
@eda_tool
async def run_drc(params: RunDRCInput) -> RunDRCResult:
    """Run Design Rule Check (DRC) on a KiCad PCB file. Returns violations list."""
    if _kicad_version is None:
        return RunDRCResult(
            success=False,
            pcb_file=params.pcb_file,
            error=_kicad_unavailable_result("run_drc"),
        )
    if not os.path.isfile(params.pcb_file):
        raise EDAError(EDAErrorCode.FILE_NOT_FOUND, f"PCB file not found: {params.pcb_file}")

    data = await run_drc_cli(params.pcb_file, params.output_dir, timeout_s=params.timeout_s)

    # Parse violations from kicad-cli JSON report format
    violations = []
    raw_violations = data.get("violations", [])
    for v in raw_violations:
        from .models import DRCViolation
        violations.append(DRCViolation(
            rule=v.get("type", "unknown"),
            severity=v.get("severity", "error"),
            description=v.get("description", ""),
            location=v.get("pos"),
        ))

    error_count = sum(1 for v in violations if v.severity == "error")
    warning_count = sum(1 for v in violations if v.severity == "warning")
    next_steps = []
    if error_count > 0:
        next_steps.append(f"Fix {error_count} DRC error(s) before generating Gerbers")
    if error_count == 0:
        next_steps.append("DRC passed — use export_gerber to generate manufacturing files")
    next_steps.append("Use get_board_info to review board metadata")

    return RunDRCResult(
        success=True,
        pcb_file=params.pcb_file,
        violation_count=len(violations),
        error_count=error_count,
        warning_count=warning_count,
        violations=violations,
        report_path=data.get("report_path"),
        suggested_next_steps=next_steps,
    )


@mcp.tool()
@eda_tool
async def export_gerber(params: ExportGerberInput) -> ExportGerberResult:
    """Export Gerber and drill files from a KiCad PCB for PCB fabrication."""
    if _kicad_version is None:
        return ExportGerberResult(
            success=False,
            pcb_file=params.pcb_file,
            output_dir=params.output_dir,
            error=_kicad_unavailable_result("export_gerber"),
        )
    if not os.path.isfile(params.pcb_file):
        raise EDAError(EDAErrorCode.FILE_NOT_FOUND, f"PCB file not found: {params.pcb_file}")

    files = await export_gerbers_cli(
        params.pcb_file,
        params.output_dir,
        include_drill=params.include_drill,
        timeout_s=params.timeout_s,
    )
    return ExportGerberResult(
        success=True,
        pcb_file=params.pcb_file,
        output_dir=params.output_dir,
        files=files,
        file_count=len(files),
        suggested_next_steps=[
            "Verify Gerber files with a Gerber viewer (e.g. gerbview)",
            "Submit Gerber package to PCB fabrication service",
        ],
    )


@mcp.tool()
@eda_tool
async def export_bom(params: ExportBOMInput) -> ExportBOMResult:
    """Export Bill of Materials (BOM) from a KiCad schematic."""
    if _kicad_version is None:
        return ExportBOMResult(
            success=False,
            schematic_file=params.schematic_file,
            output_path=params.output_path,
            error=_kicad_unavailable_result("export_bom"),
        )
    if not os.path.isfile(params.schematic_file):
        raise EDAError(
            EDAErrorCode.FILE_NOT_FOUND,
            f"Schematic file not found: {params.schematic_file}",
        )

    result = await export_bom_cli(
        params.schematic_file,
        params.output_path,
        fmt=params.format,
        timeout_s=params.timeout_s,
    )
    return ExportBOMResult(
        success=True,
        schematic_file=params.schematic_file,
        output_path=result["output_path"],
        component_count=result["row_count"],
        suggested_next_steps=[
            "Review BOM for missing footprints or values",
            "Use list_components to cross-check component references",
        ],
    )


@mcp.tool()
@eda_tool
async def run_erc(params: RunERCInput) -> RunERCResult:
    """Run Electrical Rules Check (ERC) on a KiCad schematic."""
    if _kicad_version is None:
        return RunERCResult(
            success=False,
            schematic_file=params.schematic_file,
            error=_kicad_unavailable_result("run_erc"),
        )
    if not os.path.isfile(params.schematic_file):
        raise EDAError(
            EDAErrorCode.FILE_NOT_FOUND,
            f"Schematic file not found: {params.schematic_file}",
        )

    data = await run_erc_cli(params.schematic_file, params.output_dir, timeout_s=params.timeout_s)

    violations = []
    for v in data.get("violations", []):
        from .models import ERCViolation
        violations.append(ERCViolation(
            rule=v.get("type", "unknown"),
            severity=v.get("severity", "error"),
            description=v.get("description", ""),
            sheet=v.get("sheet", ""),
        ))

    next_steps = []
    if violations:
        next_steps.append(f"Fix {len(violations)} ERC violation(s) before proceeding")
    else:
        next_steps.append("ERC passed — use export_bom or get_schematic_info next")

    return RunERCResult(
        success=True,
        schematic_file=params.schematic_file,
        violation_count=len(violations),
        violations=violations,
        report_path=data.get("report_path"),
        suggested_next_steps=next_steps,
    )


@mcp.tool()
@eda_tool
async def get_schematic_info(params: GetSchematicInfoInput) -> GetSchematicInfoResult:
    """Read schematic file metadata: sheet count, symbol count, net count."""
    if not os.path.isfile(params.schematic_file):
        raise EDAError(
            EDAErrorCode.FILE_NOT_FOUND,
            f"Schematic file not found: {params.schematic_file}",
        )

    import re
    info: dict = {}
    try:
        with open(params.schematic_file, encoding="utf-8") as f:
            content = f.read(256 * 1024)
        m = re.search(r'\(kicad_sch\s+\(version\s+(\d+)\)', content)
        if m:
            info["kicad_version"] = m.group(1)
        info["symbol_count"] = content.count("(symbol ")
        info["net_count"] = len(re.findall(r'\(net_name\s+"', content))
        info["sheet_count"] = max(1, content.count("(sheet "))
    except OSError as e:
        return GetSchematicInfoResult(
            success=False,
            schematic_file=params.schematic_file,
            error=str(e),
        )

    return GetSchematicInfoResult(
        success=True,
        schematic_file=params.schematic_file,
        sheet_count=info.get("sheet_count", 1),
        symbol_count=info.get("symbol_count", 0),
        net_count=info.get("net_count", 0),
        kicad_version=info.get("kicad_version"),
        suggested_next_steps=[
            "Use list_components to enumerate all components",
            "Use run_erc to check electrical rule violations",
            "Use export_bom to generate Bill of Materials",
        ],
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
