from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---- get_board_info tool ----

class GetBoardInfoInput(BaseModel):
    pcb_file: str = Field(description="Absolute path to .kicad_pcb file")


class GetBoardInfoResult(BaseModel):
    success: bool
    pcb_file: str
    board_width_mm: Optional[float] = None
    board_height_mm: Optional[float] = None
    layer_count: Optional[int] = None
    footprint_count: Optional[int] = None
    net_count: Optional[int] = None
    kicad_version: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---- list_components tool ----

class ListComponentsInput(BaseModel):
    schematic_file: str = Field(description="Absolute path to .kicad_sch file")
    include_power: bool = Field(default=False, description="Include power symbols (PWR, GND)")


class ComponentInfo(BaseModel):
    reference: str        # e.g. "R1", "U3"
    value: str            # e.g. "10k", "STM32F103"
    footprint: str
    datasheet: str = ""
    description: str = ""
    quantity: int = 1


class ListComponentsResult(BaseModel):
    success: bool
    schematic_file: str
    components: list[ComponentInfo] = Field(default_factory=list)
    total_count: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---- run_drc tool ----

class RunDRCInput(BaseModel):
    pcb_file: str = Field(description="Absolute path to .kicad_pcb file")
    output_dir: str = Field(description="Directory for DRC report output")
    rules_file: Optional[str] = Field(default=None, description="Optional custom DRC rules file")
    timeout_s: int = Field(default=120, ge=10, le=600)


class DRCViolation(BaseModel):
    rule: str
    severity: Literal["error", "warning"]
    description: str
    location: Optional[str] = None  # "(x, y) mm" format


class RunDRCResult(BaseModel):
    success: bool           # True = DRC executed OK (violations != failure)
    pcb_file: str
    violation_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    violations: list[DRCViolation] = Field(default_factory=list)
    report_path: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---- run_erc tool ----

class RunERCInput(BaseModel):
    schematic_file: str = Field(description="Absolute path to .kicad_sch file")
    output_dir: str = Field(description="Directory for ERC report output")
    timeout_s: int = Field(default=60, ge=10, le=300)


class ERCViolation(BaseModel):
    rule: str
    severity: Literal["error", "warning"]
    description: str
    sheet: str = ""


class RunERCResult(BaseModel):
    success: bool
    schematic_file: str
    violation_count: int = 0
    violations: list[ERCViolation] = Field(default_factory=list)
    report_path: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---- export_gerber tool ----

class ExportGerberInput(BaseModel):
    pcb_file: str = Field(description="Absolute path to .kicad_pcb file")
    output_dir: str = Field(description="Output directory for Gerber files")
    layers: list[str] = Field(
        default_factory=list,
        description="Layer list to export; empty = all copper + mask layers",
    )
    include_drill: bool = True
    timeout_s: int = Field(default=60, ge=10, le=300)


class ExportGerberResult(BaseModel):
    success: bool
    pcb_file: str
    output_dir: str
    files: list[str] = Field(default_factory=list)
    file_count: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---- export_bom tool ----

class ExportBOMInput(BaseModel):
    schematic_file: str = Field(description="Absolute path to .kicad_sch file")
    output_path: str = Field(description="Output file path")
    format: Literal["csv", "json", "xml"] = "csv"
    group_by: list[str] = Field(
        default_factory=lambda: ["Value", "Footprint"],
        description="BOM grouping fields",
    )
    timeout_s: int = Field(default=30, ge=10, le=120)


class ExportBOMResult(BaseModel):
    success: bool
    schematic_file: str
    output_path: str
    component_count: int = 0
    unique_values: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---- get_schematic_info tool ----

class GetSchematicInfoInput(BaseModel):
    schematic_file: str = Field(description="Absolute path to .kicad_sch file")


class GetSchematicInfoResult(BaseModel):
    success: bool
    schematic_file: str
    sheet_count: int = 0
    symbol_count: int = 0
    net_count: int = 0
    kicad_version: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)
