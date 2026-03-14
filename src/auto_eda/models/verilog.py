# src/auto_eda/models/verilog.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core domain models (shared between parser and server)
# ---------------------------------------------------------------------------


class PortDef(BaseModel):
    name: str
    direction: Literal["input", "output", "inout"]
    width: str = "1"  # e.g. "1", "[7:0]", "[WIDTH-1:0]"
    signed: bool = False


class ParamDef(BaseModel):
    name: str
    default_value: str | None = None
    param_type: Literal["parameter", "localparam"] = "parameter"


class ModuleDef(BaseModel):
    name: str
    ports: list[PortDef]
    parameters: list[ParamDef]
    line_start: int
    line_end: int


class HierarchyNode(BaseModel):
    module: str
    instance_name: str
    children: list[HierarchyNode] = []


class LintIssue(BaseModel):
    rule: str
    severity: Literal["error", "warning", "info"]
    message: str
    file: str
    line: int
    column: int = 0


# ---------------------------------------------------------------------------
# Tool input models
# ---------------------------------------------------------------------------


class ParseVerilogInput(BaseModel):
    file_path: str = Field(description="Path to the Verilog/SystemVerilog file")
    include_dirs: list[str] = Field(
        default_factory=list,
        description="Include search directories",
    )
    defines: dict[str, str] = Field(
        default_factory=dict,
        description="Preprocessor macro definitions (name -> value)",
    )


class ExtractModulesInput(BaseModel):
    file_path: str = Field(description="Path to the Verilog/SystemVerilog file")
    include_dirs: list[str] = Field(default_factory=list)


class AnalyzeHierarchyInput(BaseModel):
    top_file: str = Field(description="Path to the top-level Verilog file")
    source_files: list[str] = Field(
        default_factory=list,
        description="Additional source files that may contain instantiated modules",
    )
    top_module: str | None = Field(
        default=None,
        description="Top module name; auto-detected when None",
    )


class LintCheckInput(BaseModel):
    file_path: str = Field(description="Path to the Verilog file to lint")
    rules: list[str] = Field(
        default_factory=list,
        description="Rule IDs to enable; empty list enables all supported rules",
    )
    include_dirs: list[str] = Field(default_factory=list)


class ExtractPortsInput(BaseModel):
    file_path: str = Field(description="Path to the Verilog file")
    module_name: str | None = Field(
        default=None,
        description="Module to extract ports from; first module used when None",
    )


# ---------------------------------------------------------------------------
# Tool result models
# ---------------------------------------------------------------------------


class ParseVerilogResult(BaseModel):
    success: bool
    file_path: str
    modules: list[ModuleDef] = []
    syntax_errors: list[str] = []
    warnings: list[str] = []


class ExtractModulesResult(BaseModel):
    success: bool
    file_path: str
    module_names: list[str] = []
    error: str | None = None


class AnalyzeHierarchyResult(BaseModel):
    success: bool
    top_module: str | None
    hierarchy: HierarchyNode | None = None
    undefined_modules: list[str] = []
    warnings: list[str] = []


class LintCheckResult(BaseModel):
    success: bool
    file_path: str
    issues: list[LintIssue] = []
    rules_checked: list[str] = []


class ExtractPortsResult(BaseModel):
    success: bool
    file_path: str
    module_name: str | None
    ports: list[PortDef] = []
    parameters: list[ParamDef] = []
    error: str | None = None


# Allow HierarchyNode self-reference
HierarchyNode.model_rebuild()
