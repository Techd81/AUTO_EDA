from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from auto_eda.core.errors import EDAError, EDAErrorCode, ToolNotFoundError
from auto_eda.core.process import run_tool

from .version import get_kicad_cli_name


def _require_cli() -> str:
    """Return kicad-cli name or raise ToolNotFoundError."""
    cmd = get_kicad_cli_name()
    if cmd is None:
        raise ToolNotFoundError("kicad-cli")
    return cmd


async def run_drc_cli(
    pcb_file: str,
    output_dir: str,
    timeout_s: int = 120,
) -> dict[str, Any]:
    """
    Run DRC via kicad-cli and return parsed JSON report.
    Raises EDAError on execution failure.
    """
    cmd = _require_cli()
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "drc_report.json")

    args = [
        cmd, "pcb", "drc",
        "--output", report_path,
        "--format", "json",
        "--exit-code-violations",  # non-zero exit if violations found (informational)
        pcb_file,
    ]
    result = await run_tool(args, cwd=Path(output_dir), timeout_s=timeout_s)

    if not os.path.exists(report_path):
        raise EDAError(
            EDAErrorCode.KICAD_DRC_ERROR,
            "DRC report not generated",
            detail=result.stderr[:2000],
        )

    with open(report_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    data["report_path"] = report_path
    return data


async def export_gerbers_cli(
    pcb_file: str,
    output_dir: str,
    include_drill: bool = True,
    timeout_s: int = 60,
) -> list[str]:
    """
    Export Gerber files via kicad-cli.
    Returns list of generated file paths.
    """
    cmd = _require_cli()
    os.makedirs(output_dir, exist_ok=True)

    gerber_args = [
        cmd, "pcb", "export", "gerbers",
        "--output", output_dir,
        pcb_file,
    ]
    result = await run_tool(gerber_args, cwd=Path(output_dir), timeout_s=timeout_s)
    if result.returncode != 0:
        raise EDAError(
            EDAErrorCode.KICAD_DRC_ERROR,
            "Gerber export failed",
            detail=result.stderr[:2000],
        )

    if include_drill:
        drill_args = [
            cmd, "pcb", "export", "drill",
            "--output", output_dir,
            pcb_file,
        ]
        await run_tool(drill_args, cwd=Path(output_dir), timeout_s=timeout_s)

    # Collect all generated files
    generated = [
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.endswith((".gbr", ".drl", ".gtl", ".gbl", ".gts", ".gbs",
                       ".gto", ".gbo", ".gko", ".exc", ".xln"))
    ]
    return sorted(generated)


async def export_bom_cli(
    sch_file: str,
    output_file: str,
    fmt: str = "csv",
    timeout_s: int = 30,
) -> dict[str, Any]:
    """
    Export BOM via kicad-cli.
    Returns dict with output_path and row count.
    """
    cmd = _require_cli()
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    args = [
        cmd, "sch", "export", "bom",
        "--output", output_file,
        "--format", fmt,
        sch_file,
    ]
    result = await run_tool(args, timeout_s=timeout_s)
    if result.returncode != 0:
        raise EDAError(
            EDAErrorCode.KICAD_PROJECT_INVALID,
            "BOM export failed",
            detail=result.stderr[:2000],
        )

    row_count = 0
    if os.path.exists(output_file):
        with open(output_file, encoding="utf-8") as f:
            row_count = max(0, sum(1 for _ in f) - 1)  # subtract header

    return {"output_path": output_file, "row_count": row_count}


async def export_schematic_svg_cli(
    sch_file: str,
    output_dir: str,
    timeout_s: int = 30,
) -> Optional[str]:
    """
    Export schematic as SVG via kicad-cli.
    Returns path to generated SVG or None on failure.
    """
    cmd = _require_cli()
    os.makedirs(output_dir, exist_ok=True)

    args = [
        cmd, "sch", "export", "svg",
        "--output", output_dir,
        sch_file,
    ]
    result = await run_tool(args, cwd=Path(output_dir), timeout_s=timeout_s)
    if result.returncode != 0:
        return None

    svgs = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".svg")]
    return svgs[0] if svgs else None


async def run_erc_cli(
    sch_file: str,
    output_dir: str,
    timeout_s: int = 60,
) -> dict[str, Any]:
    """
    Run ERC via kicad-cli and return parsed JSON report.
    Raises EDAError on execution failure.
    """
    cmd = _require_cli()
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "erc_report.json")

    args = [
        cmd, "sch", "erc",
        "--output", report_path,
        "--format", "json",
        sch_file,
    ]
    result = await run_tool(args, cwd=Path(output_dir), timeout_s=timeout_s)

    if not os.path.exists(report_path):
        raise EDAError(
            EDAErrorCode.KICAD_DRC_ERROR,
            "ERC report not generated",
            detail=result.stderr[:2000],
        )

    with open(report_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    data["report_path"] = report_path
    return data


async def get_board_info_cli(
    pcb_file: str,
    timeout_s: int = 30,
) -> dict[str, Any]:
    """
    Extract board info by running a minimal kicad-cli inspect command.
    Falls back to S-expression parsing if CLI inspect is unavailable.
    """
    # kicad-cli does not have a direct 'board info' command; use DRC in dry-run
    # or fall back to sexpdata parsing for board metadata.
    return await _parse_board_sexp(pcb_file)


async def _parse_board_sexp(pcb_file: str) -> dict[str, Any]:
    """Parse .kicad_pcb S-expression for basic board metadata without running KiCad."""
    import re

    info: dict[str, Any] = {"pcb_file": pcb_file}
    try:
        with open(pcb_file, encoding="utf-8") as f:
            content = f.read(128 * 1024)  # read first 128 KB only

        # Extract kicad version
        m = re.search(r'\(kicad_pcb\s+\(version\s+(\d+)\)', content)
        if m:
            info["kicad_version"] = m.group(1)

        # Count footprints
        info["footprint_count"] = content.count("(footprint ")

        # Count nets
        net_matches = re.findall(r'\(net\s+\d+\s+"', content)
        info["net_count"] = len(net_matches)

        # Extract layer count
        layer_matches = re.findall(r'\(layer\s+\d+\s+"', content)
        info["layer_count"] = len(layer_matches)

    except OSError as e:
        info["parse_error"] = str(e)

    return info

async def _parse_sch_components(
    sch_file: str,
    include_power: bool = False,
) -> list[Any]:
    """
    Parse .kicad_sch S-expression to extract component list.
    Returns a list of ComponentInfo-compatible dicts.
    """
    import re
    from auto_eda.servers.kicad.models import ComponentInfo

    components: list[ComponentInfo] = []
    try:
        with open(sch_file, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return components

    # Match symbol blocks: (symbol (lib_id "...") ... (property "Reference" "R1") ...)
    # We use a simple regex scan for property blocks near symbol definitions.
    # This is a best-effort parse; full S-expr parsing would require sexpdata.
    symbol_blocks = re.split(r'(?=\(symbol\s)', content)
    for block in symbol_blocks[1:]:
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
        fp_m = re.search(r'\(property\s+"Footprint"\s+"([^"]+)"', block)
        ds_m = re.search(r'\(property\s+"Datasheet"\s+"([^"]+)"', block)
        desc_m = re.search(r'\(property\s+"Description"\s+"([^"]+)"', block)

        if not ref_m or not val_m:
            continue

        reference = ref_m.group(1)
        # Skip power symbols (PWR, #PWR, GND, etc.) unless requested
        if not include_power and (reference.startswith("#") or reference.startswith("PWR")):
            continue

        components.append(ComponentInfo(
            reference=reference,
            value=val_m.group(1),
            footprint=fp_m.group(1) if fp_m else "",
            datasheet=ds_m.group(1) if ds_m else "",
            description=desc_m.group(1) if desc_m else "",
        ))

    return components
