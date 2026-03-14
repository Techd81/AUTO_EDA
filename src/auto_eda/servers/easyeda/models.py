"""Pydantic models for all EasyEDA MCP tools.

Naming convention: <ToolName>Input / <ToolName>Result
All coordinates in mils (1 inch = 1000 mil), matching hyl64/jlcmcp convention.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class ComponentInfo(BaseModel):
    ref: str             # e.g. "U1"
    lcsc: str            # LCSC part number e.g. "C8734"
    value: str
    footprint: str = ""
    x: int = 0           # PCB position in mil
    y: int = 0
    rotation: int = 0


class Violation(BaseModel):
    severity: Literal["error", "warning"]
    rule: str
    description: str
    location: str = ""


# ---------------------------------------------------------------------------
# eda_ping
# ---------------------------------------------------------------------------

class EdaPingInput(BaseModel):
    pass


class EdaPingResult(BaseModel):
    success: bool
    connected: bool
    eda_version: Optional[str] = None
    bridge_version: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# eda_get_status
# ---------------------------------------------------------------------------

class EdaGetStatusInput(BaseModel):
    pass


class EdaGetStatusResult(BaseModel):
    success: bool
    open_documents: list[str] = Field(default_factory=list)
    active_document: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_get_state
# ---------------------------------------------------------------------------

class SchGetStateInput(BaseModel):
    pass


class SchGetStateResult(BaseModel):
    success: bool
    document_name: Optional[str] = None
    symbol_count: int = 0
    wire_count: int = 0
    net_label_count: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_place_symbol
# ---------------------------------------------------------------------------

class SchPlaceSymbolInput(BaseModel):
    lcsc: str = Field(description="LCSC part number, e.g. 'C8734'")
    x: int = Field(description="Schematic X position in mil")
    y: int = Field(description="Schematic Y position in mil")
    rotation: int = Field(default=0, description="Rotation in degrees (0/90/180/270)")


class SchPlaceSymbolResult(BaseModel):
    success: bool
    ref: Optional[str] = None   # assigned reference e.g. "U1"
    lcsc: str = ""
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_add_wire
# ---------------------------------------------------------------------------

class SchAddWireInput(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class SchAddWireResult(BaseModel):
    success: bool
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_add_net_label
# ---------------------------------------------------------------------------

class SchAddNetLabelInput(BaseModel):
    name: str = Field(description="Net name, e.g. 'VCC', 'GND', 'SWDIO'")
    x: int
    y: int
    rotation: int = Field(default=0)


class SchAddNetLabelResult(BaseModel):
    success: bool
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_add_power_symbol
# ---------------------------------------------------------------------------

class SchAddPowerSymbolInput(BaseModel):
    name: Literal["VCC", "GND", "3V3", "5V", "VBUS"] = Field(
        description="Power net name"
    )
    x: int
    y: int


class SchAddPowerSymbolResult(BaseModel):
    success: bool
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_run_erc
# ---------------------------------------------------------------------------

class SchRunERCInput(BaseModel):
    pass


class SchRunERCResult(BaseModel):
    success: bool
    violation_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    violations: list[Violation] = Field(default_factory=list)
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_get_netlist
# ---------------------------------------------------------------------------

class SchGetNetlistInput(BaseModel):
    pass


class SchGetNetlistResult(BaseModel):
    success: bool
    net_count: int = 0
    nets: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# sch_update_pcb  (sync schematic changes to PCB layout)
# ---------------------------------------------------------------------------

class SchUpdatePCBInput(BaseModel):
    pass


class SchUpdatePCBResult(BaseModel):
    success: bool
    added_footprints: int = 0
    removed_footprints: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_get_state
# ---------------------------------------------------------------------------

class PcbGetStateInput(BaseModel):
    pass


class PcbGetStateResult(BaseModel):
    success: bool
    document_name: Optional[str] = None
    board_width_mil: Optional[int] = None
    board_height_mil: Optional[int] = None
    layer_count: int = 0
    component_count: int = 0
    net_count: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_place_component
# ---------------------------------------------------------------------------

class PcbPlaceComponentInput(BaseModel):
    lcsc: str = Field(description="LCSC part number")
    x: int = Field(description="PCB X position in mil")
    y: int = Field(description="PCB Y position in mil")
    rotation: int = Field(default=0)
    layer: Literal["top", "bottom"] = "top"


class PcbPlaceComponentResult(BaseModel):
    success: bool
    ref: Optional[str] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_move_component
# ---------------------------------------------------------------------------

class PcbMoveComponentInput(BaseModel):
    ref: str = Field(description="Component reference, e.g. 'U1'")
    x: int
    y: int
    rotation: Optional[int] = None


class PcbMoveComponentResult(BaseModel):
    success: bool
    ref: str = ""
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_route_track
# ---------------------------------------------------------------------------

class PcbRouteTrackInput(BaseModel):
    net: str = Field(description="Net name, e.g. 'GND'")
    x1: int
    y1: int
    x2: int
    y2: int
    layer: Literal["F_Cu", "B_Cu"] = "F_Cu"
    width_mil: int = Field(default=10, description="Track width in mil")


class PcbRouteTrackResult(BaseModel):
    success: bool
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_create_via
# ---------------------------------------------------------------------------

class PcbCreateViaInput(BaseModel):
    net: str
    x: int
    y: int
    drill_mil: int = Field(default=12, description="Drill diameter in mil")
    outer_mil: int = Field(default=24, description="Pad outer diameter in mil")


class PcbCreateViaResult(BaseModel):
    success: bool
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_flood_fill
# ---------------------------------------------------------------------------

class PcbFloodFillInput(BaseModel):
    net: str = Field(default="GND", description="Net to flood fill")
    layer: Literal["F_Cu", "B_Cu"] = "B_Cu"
    clearance_mil: int = Field(default=8)


class PcbFloodFillResult(BaseModel):
    success: bool
    poured_area_mm2: Optional[float] = None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_run_drc
# ---------------------------------------------------------------------------

class PcbRunDRCInput(BaseModel):
    pass


class PcbRunDRCResult(BaseModel):
    success: bool
    violation_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    violations: list[Violation] = Field(default_factory=list)
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# pcb_screenshot
# ---------------------------------------------------------------------------

class PcbScreenshotInput(BaseModel):
    output_path: Optional[str] = Field(
        default=None,
        description="Local file path to save PNG; None = return base64",
    )


class PcbScreenshotResult(BaseModel):
    success: bool
    output_path: Optional[str] = None
    base64_png: Optional[str] = None   # set when output_path is None
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# export_gerber
# ---------------------------------------------------------------------------

class ExportGerberInput(BaseModel):
    output_dir: str = Field(description="Directory to write Gerber + drill files")


class ExportGerberResult(BaseModel):
    success: bool
    output_dir: str = ""
    files: list[str] = Field(default_factory=list)
    file_count: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# export_bom
# ---------------------------------------------------------------------------

class ExportBOMInput(BaseModel):
    output_path: str = Field(description="Output CSV/JSON file path")
    format: Literal["csv", "json"] = "csv"


class ExportBOMResult(BaseModel):
    success: bool
    output_path: str = ""
    component_count: int = 0
    unique_parts: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# export_pick_place
# ---------------------------------------------------------------------------

class ExportPickPlaceInput(BaseModel):
    output_path: str = Field(description="Output CPL CSV file path")


class ExportPickPlaceResult(BaseModel):
    success: bool
    output_path: str = ""
    component_count: int = 0
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# export_pdf
# ---------------------------------------------------------------------------

class ExportPDFInput(BaseModel):
    output_path: str = Field(description="Output PDF file path")
    target: Literal["schematic", "pcb"] = "schematic"


class ExportPDFResult(BaseModel):
    success: bool
    output_path: str = ""
    error: Optional[str] = None
    suggested_next_steps: list[str] = Field(default_factory=list)
