# src/auto_eda/servers/yosys/server.py
"""Yosys MCP Server — 5 tools for RTL synthesis and analysis."""
from __future__ import annotations

import logging
from pathlib import Path

from auto_eda.core.base_server import create_server, eda_tool
from auto_eda.core.errors import EDAError, EDAErrorCode

from .models import (
    CheckDesignInput,
    CheckDesignResult,
    GateStats,
    OptimizeInput,
    OptimizeResult,
    RTLStatsInput,
    RTLStatsResult,
    ShowSchematicInput,
    ShowSchematicResult,
    SynthesizeInput,
    SynthesizeResult,
)
from .runner import (
    parse_check_output,
    parse_stat_output,
    run_check,
    run_optimize,
    run_show,
    run_stats,
    run_synthesis,
)

logger = logging.getLogger(__name__)

mcp = create_server("auto-eda-yosys", version="0.1.0")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_sources(source_files: list[str]) -> list[str]:
    """Return error strings for missing source files."""
    return [
        f"Source file not found: {f}"
        for f in source_files
        if not Path(f).is_file()
    ]


# ---------------------------------------------------------------------------
# Tool 1: synthesize
# ---------------------------------------------------------------------------


@mcp.tool()
@eda_tool
async def synthesize(params: SynthesizeInput) -> SynthesizeResult:
    """
    Synthesize RTL Verilog/SystemVerilog to a gate-level netlist using Yosys.

    Runs ``synth`` (generic) or ``synth_<tech_lib>`` (technology-specific)
    and returns gate counts, wire counts, and per-cell statistics.
    Optionally writes the netlist to *output_netlist*.

    Supported tech_lib values: xilinx, intel, lattice, gowin, cmos, ecp5, ice40.
    Leave as None for a technology-agnostic generic synthesis.
    """
    missing = _validate_sources(params.source_files)
    if missing:
        raise EDAError(
            EDAErrorCode.FILE_NOT_FOUND,
            "One or more source files not found",
            detail="\n".join(missing),
        )

    result = await run_synthesis(
        top=params.top_module,
        source_files=params.source_files,
        tech_lib=params.tech_lib,
        output_netlist=params.output_netlist,
        flatten=params.flatten,
        optimize=params.optimize,
    )

    log = result.stdout + result.stderr
    gate_count, wire_count, cells = parse_stat_output(log)

    netlist_inline: str | None = None
    if params.output_netlist and Path(params.output_netlist).exists():
        netlist_path = params.output_netlist
    elif params.output_netlist is None:
        # Return a snippet of the log as inline summary (netlist not written)
        netlist_inline = _extract_netlist_section(log)
        netlist_path = None
    else:
        netlist_path = None

    warnings = [ln.strip() for ln in log.splitlines() if "Warning" in ln]

    return SynthesizeResult(
        success=True,
        top_module=params.top_module,
        gate_count=gate_count,
        wire_count=wire_count,
        gate_stats=[GateStats(cell_type=c, count=n) for c, n in cells],
        netlist_path=netlist_path,
        netlist_inline=netlist_inline,
        warnings=warnings,
        yosys_log=log[:4000],
        suggested_next_steps=[
            "Use rtl_stats to compare pre/post-synthesis statistics",
            "Pass output_netlist path and feed to OpenROAD for placement & routing",
            "Use check_design to verify the synthesized netlist",
        ],
    )


def _extract_netlist_section(log: str) -> str | None:
    """Return the stat summary block from Yosys log, if present."""
    marker = "=== design hierarchy ==="
    idx = log.find(marker)
    if idx == -1:
        return None
    return log[idx : idx + 2000]


# ---------------------------------------------------------------------------
# Tool 2: rtl_stats
# ---------------------------------------------------------------------------


@mcp.tool()
@eda_tool
async def rtl_stats(params: RTLStatsInput) -> RTLStatsResult:
    """
    Report RTL-level statistics for a Verilog design without full synthesis.

    Runs ``proc`` + ``stat`` to count wires, cells, memories, and processes
    as they appear in the RTL, before any technology mapping.
    Useful for design complexity estimation and comparison.
    """
    missing = _validate_sources(params.source_files)
    if missing:
        return RTLStatsResult(
            success=False,
            top_module=params.top_module,
            error="\n".join(missing),
        )

    result = await run_stats(top=params.top_module, source_files=params.source_files)
    log = result.stdout + result.stderr
    gate_count, wire_count, cells = parse_stat_output(log)

    # Parse memory and process counts from stat output
    import re
    num_memories = 0
    num_processes = 0
    m = re.search(r"Number of memories:\s+(\d+)", log)
    if m:
        num_memories = int(m.group(1))
    m = re.search(r"Number of processes:\s+(\d+)", log)
    if m:
        num_processes = int(m.group(1))
    m = re.search(r"Number of wire bits:\s+(\d+)", log)
    num_wire_bits = int(m.group(1)) if m else 0

    warnings = [ln.strip() for ln in log.splitlines() if "Warning" in ln]

    return RTLStatsResult(
        success=True,
        top_module=params.top_module,
        num_wires=wire_count,
        num_wire_bits=num_wire_bits,
        num_cells=gate_count,
        num_memories=num_memories,
        num_processes=num_processes,
        cell_breakdown=[GateStats(cell_type=c, count=n) for c, n in cells],
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Tool 3: check_design
# ---------------------------------------------------------------------------


@mcp.tool()
@eda_tool
async def check_design(params: CheckDesignInput) -> CheckDesignResult:
    """
    Run Yosys design-rule checks on RTL source files.

    Executes ``hierarchy -check`` and ``check`` passes to detect:
    - Undefined module instantiations
    - Multi-driven signals
    - Undriven signals
    - Combinational loops

    Returns a list of issues (errors) and warnings.
    """
    missing = _validate_sources(params.source_files)
    if missing:
        return CheckDesignResult(
            success=False,
            top_module=params.top_module,
            issues=missing,
        )

    result = await run_check(top=params.top_module, source_files=params.source_files)
    log = result.stdout + result.stderr
    issues, warnings = parse_check_output(log)

    return CheckDesignResult(
        success=True,
        top_module=params.top_module,
        issues=issues,
        warnings=warnings,
        passed=len(issues) == 0,
    )


# ---------------------------------------------------------------------------
# Tool 4: show_schematic
# ---------------------------------------------------------------------------


@mcp.tool()
@eda_tool
async def show_schematic(params: ShowSchematicInput) -> ShowSchematicResult:
    """
    Generate a DOT-format schematic graph of the RTL design using Yosys.

    Runs ``show -format dot`` and either writes the result to *output_dot*
    or returns the DOT source inline (when output_dot is None).
    The DOT file can be rendered with Graphviz: ``dot -Tsvg design.dot -o design.svg``.
    """
    missing = _validate_sources(params.source_files)
    if missing:
        return ShowSchematicResult(
            success=False,
            top_module=params.top_module,
            error="\n".join(missing),
        )

    result, dot_path = await run_show(
        top=params.top_module,
        source_files=params.source_files,
        output_dot=params.output_dot,
    )

    dot_source: str | None = None
    if Path(dot_path).exists():
        dot_source = Path(dot_path).read_text(encoding="utf-8")[:8000]
        if params.output_dot is None:
            # Temp file — clean up
            Path(dot_path).unlink(missing_ok=True)
            dot_path_out = None
        else:
            dot_path_out = dot_path
    else:
        dot_path_out = None

    return ShowSchematicResult(
        success=dot_source is not None or dot_path_out is not None,
        top_module=params.top_module,
        dot_path=dot_path_out,
        dot_source=dot_source,
    )


# ---------------------------------------------------------------------------
# Tool 5: optimize_design
# ---------------------------------------------------------------------------


@mcp.tool()
@eda_tool
async def optimize_design(params: OptimizeInput) -> OptimizeResult:
    """
    Run Yosys optimisation passes on an RTL design and report cell reduction.

    Default passes: ``opt``, ``opt_expr``, ``opt_clean``.
    Custom passes may include any valid Yosys command (e.g. ``share``, ``alumacc``).
    Returns cell counts before and after optimisation and the percentage reduction.
    """
    missing = _validate_sources(params.source_files)
    if missing:
        return OptimizeResult(
            success=False,
            top_module=params.top_module,
            error="\n".join(missing),
        )

    # Capture pre-optimisation stats
    before_result = await run_stats(
        top=params.top_module, source_files=params.source_files
    )
    cells_before, _, _ = parse_stat_output(
        before_result.stdout + before_result.stderr
    )

    # Run optimisation
    result = await run_optimize(
        top=params.top_module,
        source_files=params.source_files,
        passes=params.passes,
    )
    log = result.stdout + result.stderr
    cells_after, _, _ = parse_stat_output(log)

    reduction = 0.0
    if cells_before > 0:
        reduction = round((cells_before - cells_after) / cells_before * 100, 1)

    warnings = [ln.strip() for ln in log.splitlines() if "Warning" in ln]

    return OptimizeResult(
        success=True,
        top_module=params.top_module,
        passes_run=params.passes,
        cells_before=cells_before,
        cells_after=cells_after,
        reduction_pct=reduction,
        warnings=warnings,
    )
