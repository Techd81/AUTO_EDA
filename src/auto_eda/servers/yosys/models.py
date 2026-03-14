# src/auto_eda/servers/yosys/models.py
"""Pydantic models for the Yosys MCP server."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class SynthesizeInput(BaseModel):
    top_module: str = Field(description="Top-level module name to synthesize")
    source_files: list[str] = Field(description="Verilog/SystemVerilog source files")
    tech_lib: str | None = Field(
        default=None,
        description="Technology library name (e.g. 'cmos', 'xilinx'); None = generic",
    )
    output_netlist: str | None = Field(
        default=None,
        description="Path to write Verilog netlist; None = return inline",
    )
    flatten: bool = Field(default=True, description="Flatten design hierarchy")
    optimize: Literal["none", "speed", "area"] = Field(
        default="area",
        description="Optimisation objective",
    )


class RTLStatsInput(BaseModel):
    top_module: str = Field(description="Top-level module name")
    source_files: list[str] = Field(description="Verilog/SystemVerilog source files")


class CheckDesignInput(BaseModel):
    top_module: str = Field(description="Top-level module name")
    source_files: list[str] = Field(description="Verilog/SystemVerilog source files")


class ShowSchematicInput(BaseModel):
    top_module: str = Field(description="Top-level module name")
    source_files: list[str] = Field(description="Verilog/SystemVerilog source files")
    output_dot: str | None = Field(
        default=None,
        description="Path to write .dot file; None = return DOT source inline",
    )


class OptimizeInput(BaseModel):
    top_module: str = Field(description="Top-level module name")
    source_files: list[str] = Field(description="Verilog/SystemVerilog source files")
    passes: list[str] = Field(
        default_factory=lambda: ["opt", "opt_expr", "opt_clean"],
        description="Yosys optimisation passes to run in order",
    )


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class GateStats(BaseModel):
    cell_type: str
    count: int


class SynthesizeResult(BaseModel):
    success: bool
    top_module: str
    gate_count: int = 0
    wire_count: int = 0
    gate_stats: list[GateStats] = []
    netlist_path: str | None = None
    netlist_inline: str | None = None
    warnings: list[str] = []
    yosys_log: str = ""
    suggested_next_steps: list[str] = []


class RTLStatsResult(BaseModel):
    success: bool
    top_module: str
    num_wires: int = 0
    num_wire_bits: int = 0
    num_cells: int = 0
    num_memories: int = 0
    num_processes: int = 0
    cell_breakdown: list[GateStats] = []
    warnings: list[str] = []
    error: str | None = None


class CheckDesignResult(BaseModel):
    success: bool
    top_module: str
    issues: list[str] = []
    warnings: list[str] = []
    passed: bool = False


class ShowSchematicResult(BaseModel):
    success: bool
    top_module: str
    dot_path: str | None = None
    dot_source: str | None = None
    error: str | None = None


class OptimizeResult(BaseModel):
    success: bool
    top_module: str
    passes_run: list[str] = []
    cells_before: int = 0
    cells_after: int = 0
    reduction_pct: float = 0.0
    warnings: list[str] = []
    error: str | None = None
