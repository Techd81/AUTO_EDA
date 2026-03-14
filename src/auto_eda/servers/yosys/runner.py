# src/auto_eda/servers/yosys/runner.py
"""Low-level Yosys subprocess helpers."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from auto_eda.core.process import ProcessResult, run_tool

# ---------------------------------------------------------------------------
# Script builders
# ---------------------------------------------------------------------------

_OPT_FLAGS: dict[str, str] = {
    "none": "",
    "speed": "; opt -fast",
    "area": "; opt",
}


def _build_synth_script(
    top: str,
    source_files: list[str],
    tech_lib: str | None,
    output_netlist: str | None,
    flatten: bool,
    optimize: str,
) -> str:
    """Return a Yosys TCL/script string for synthesis."""
    lines: list[str] = []
    for src in source_files:
        lines.append(f"read_verilog -sv {src}")
    lines.append(f"hierarchy -check -top {top}")
    if flatten:
        lines.append("flatten")
    opt_flag = _OPT_FLAGS.get(optimize, "")
    if tech_lib:
        lines.append(f"synth_{tech_lib} -top {top}{opt_flag}")
    else:
        lines.append(f"synth -top {top}{opt_flag}")
    if output_netlist:
        lines.append(f"write_verilog -noattr {output_netlist}")
    lines.append("stat")
    return "; ".join(lines)


def _build_stats_script(top: str, source_files: list[str]) -> str:
    lines = [f"read_verilog -sv {src}" for src in source_files]
    lines += [f"hierarchy -check -top {top}", "proc", "stat"]
    return "; ".join(lines)


def _build_check_script(top: str, source_files: list[str]) -> str:
    lines = [f"read_verilog -sv {src}" for src in source_files]
    lines += [f"hierarchy -check -top {top}", "proc", "check"]
    return "; ".join(lines)


def _build_show_script(
    top: str, source_files: list[str], dot_path: str
) -> str:
    lines = [f"read_verilog -sv {src}" for src in source_files]
    lines += [
        f"hierarchy -check -top {top}",
        "proc",
        f"show -format dot -prefix {dot_path} -notitle {top}",
    ]
    return "; ".join(lines)


def _build_opt_script(
    top: str, source_files: list[str], passes: list[str]
) -> str:
    lines = [f"read_verilog -sv {src}" for src in source_files]
    lines += [f"hierarchy -check -top {top}", "proc"]
    lines += passes
    lines.append("stat")
    return "; ".join(lines)


# ---------------------------------------------------------------------------
# Stat parser
# ---------------------------------------------------------------------------


def parse_stat_output(
    log: str,
) -> tuple[int, int, list[tuple[str, int]]]:
    """Extract (gate_count, wire_count, [(cell_type, count)]) from yosys stat output."""
    gate_count = 0
    wire_count = 0
    cells: list[tuple[str, int]] = []

    # Wire count: "   Number of wires:               42"
    m = re.search(r"Number of wires:\s+(\d+)", log)
    if m:
        wire_count = int(m.group(1))

    # Cell count: "   Number of cells:               18"
    m = re.search(r"Number of cells:\s+(\d+)", log)
    if m:
        gate_count = int(m.group(1))

    # Per-cell breakdown: "     $_AND_                           5"
    for cell_m in re.finditer(r"^\s+(\$\w+|\w+)\s+(\d+)\s*$", log, re.MULTILINE):
        cells.append((cell_m.group(1), int(cell_m.group(2))))

    return gate_count, wire_count, cells


def parse_check_output(log: str) -> tuple[list[str], list[str]]:
    """Return (issues, warnings) from yosys check output."""
    issues: list[str] = []
    warnings: list[str] = []
    for line in log.splitlines():
        ll = line.strip()
        if ll.startswith("ERROR") or ll.startswith("Assertion failed"):
            issues.append(ll)
        elif ll.startswith("Warning"):
            warnings.append(ll)
    return issues, warnings


# ---------------------------------------------------------------------------
# Public runners
# ---------------------------------------------------------------------------


async def run_synthesis(
    top: str,
    source_files: list[str],
    tech_lib: str | None,
    output_netlist: str | None,
    flatten: bool,
    optimize: str,
    timeout: float = 300.0,
) -> ProcessResult:
    script = _build_synth_script(
        top, source_files, tech_lib, output_netlist, flatten, optimize
    )
    return await run_tool(["yosys", "-p", script], timeout=timeout)


async def run_stats(
    top: str,
    source_files: list[str],
    timeout: float = 120.0,
) -> ProcessResult:
    script = _build_stats_script(top, source_files)
    return await run_tool(["yosys", "-p", script], timeout=timeout)


async def run_check(
    top: str,
    source_files: list[str],
    timeout: float = 120.0,
) -> ProcessResult:
    script = _build_check_script(top, source_files)
    return await run_tool(["yosys", "-p", script], timeout=timeout)


async def run_show(
    top: str,
    source_files: list[str],
    output_dot: str | None,
    timeout: float = 120.0,
) -> tuple[ProcessResult, str]:
    """Returns (result, dot_path_used)."""
    if output_dot:
        dot_path = output_dot.removesuffix(".dot")
        result = await run_tool(
            ["yosys", "-p", _build_show_script(top, source_files, dot_path)],
            timeout=timeout,
        )
        return result, output_dot
    # Use a temp file
    with tempfile.NamedTemporaryFile(suffix=".dot", delete=False) as tf:
        tmp = tf.name
    dot_prefix = tmp.removesuffix(".dot")
    result = await run_tool(
        ["yosys", "-p", _build_show_script(top, source_files, dot_prefix)],
        timeout=timeout,
    )
    return result, tmp


async def run_optimize(
    top: str,
    source_files: list[str],
    passes: list[str],
    timeout: float = 180.0,
) -> ProcessResult:
    script = _build_opt_script(top, source_files, passes)
    return await run_tool(["yosys", "-p", script], timeout=timeout)
