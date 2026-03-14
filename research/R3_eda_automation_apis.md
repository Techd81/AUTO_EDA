# R3: EDA Software Automation APIs and Scripting Interfaces

> Research Date: 2026-03-14
> Source: Web search via Grok Search MCP, official documentation, community resources

---

## Table of Contents

1. [Cadence Automation Interfaces](#1-cadence-automation-interfaces)
2. [Synopsys Automation Interfaces](#2-synopsys-automation-interfaces)
3. [Siemens EDA Automation Interfaces](#3-siemens-eda-automation-interfaces)
4. [KiCad Automation](#4-kicad-automation)
5. [OpenROAD/OpenLane Automation](#5-openroadopenlane-automation)
6. [Common EDA Automation Patterns](#6-common-eda-automation-patterns)
7. [Cross-Platform Comparison Matrix](#7-cross-platform-comparison-matrix)
8. [MCP Integration Opportunities](#8-mcp-integration-opportunities)

---

## 1. Cadence Automation Interfaces

### 1.1 SKILL Language (Virtuoso)

**Overview**: SKILL is a Lisp dialect (influenced by Scheme and Common Lisp, originally based on Franz Lisp) serving as Cadence's native scripting language across its EDA tools. It is the primary automation layer for Virtuoso custom IC design.

**Key Characteristics**:
- Lisp prefix notation: `(function arg1 arg2)`
- File extensions: `.il` (SKILL), `.ils` (SKILL++ with OO extensions)
- Executed in CIW (Command Interpreter Window) via `(load "script.il")`
- SKILL++ adds object-oriented programming capabilities
- Hundreds of built-in tool-specific functions (prefixed: `db*`, `ge*`, `sch*`)

**Automation Capabilities**:
- Parameterized Cell (PCell) creation and modification
- Layout/schematic manipulation via database objects
- Custom UI tools and menu extensions
- Design rule automation and flow integration
- Batch processing in non-GUI mode

**Discovery Tools**:
- SKILL API Finder: CIW -> Tools -> SKILL API Finder
- Smart Search (Virtuoso Studio 2025+): Natural-language function discovery
- CDS.log recording: Mark START/STOP to capture GUI actions as SKILL commands

**Example - Basic SKILL Procedure**:
```skill
procedure(createViaArray(cv x y count pitch)
  let((via)
    foreach(i 0 count-1
      via = dbCreateRect(cv "VIA" list((x+i*pitch y) (x+i*pitch+0.1 y+0.1)))
    )
    printf("Created %d vias\n" count)
  )
)
; Load: (load "via_array.il")
; Call: (createViaArray geGetEditCellView() 0 0 10 0.2)
```

**Key API Prefixes**:
| Prefix | Domain |
|--------|--------|
| `db*` | Database operations (cells, instances, shapes) |
| `ge*` | Geometry creation/manipulation |
| `sch*` | Schematic operations |
| `hi*` | GUI/interactive commands (convert to non-hi for batch) |
| `rod*` | Relative Object Design for PCells |

### 1.2 Ocean Scripts (Simulation Automation)

**Overview**: OCEAN (Open Command Environment for Analysis) is a specialized SKILL subset for automating analog simulations in Virtuoso's ADE (Analog Design Environment), primarily targeting the Spectre simulator.

**Key Features**:
- Built on SKILL - can freely mix core SKILL code
- Generated from ADE GUI: Session -> Save Ocean Script
- Ideal for batch runs, corners (SS/FF/TT), PVT sweeps, Monte Carlo
- File extension: `.ocn`
- Run: `(load "file.ocn")` in CIW or `ocean file.ocn` from shell

**Example - Ocean Batch Simulation**:
```ocn
simulator('spectre)
design("/path/to/lib" "myCell" "schematic")
resultsDir("./results")
modelFile("/path/to/models.scs")
analysis('tran ?stop "1u" ?errpreset "conservative")
desVar("Vdd" 1.8)
temp(27)
run()
openResults("./results")
selectResult('tran)
vout = v("/out")
printf("Average output: %g\n" average(vout))

; Corner sweep example
foreach(corner '("tt" "ss" "ff")
  modelFile(strcat("/models/" corner ".scs"))
  run()
  printf("Corner %s: Vout_avg = %g\n" corner average(v("/out")))
)
```

### 1.3 Innovus TCL Interface

**Overview**: Innovus is Cadence's digital implementation (place-and-route) tool. It uses TCL as its primary scripting interface, with newer Innovus+ (2025+) adding native Python support.

**Shell**: `innovus` or `innovus -batch -files script.tcl`

**Core TCL Commands**:
| Command | Purpose |
|---------|---------|
| `init_design` | Initialize design from LEF/DEF/Verilog |
| `floorPlan` | Define floorplan parameters |
| `place_design` | Run placement |
| `clockDesign` | Clock tree synthesis |
| `route_design` | Detail routing |
| `dbGet` / `dbSet` | Database query/modify |
| `addRing` / `addStripe` | Power planning |
| `write_def` / `streamOut` | Export DEF/GDSII |

**Foundation Flow**: Auto-generated via `gen_flow.tcl` producing step scripts:
- `run_init.tcl` - Design initialization
- `run_place.tcl` - Placement
- `run_cts.tcl` - Clock tree synthesis
- `run_route.tcl` - Routing

**Example - Innovus TCL Flow**:
```tcl
set init_verilog   [list "design.v"]
set init_lef_file  [list "tech.lef" "cells.lef"]
set init_design_name "top"
set init_power_nets "VDD"
set init_ground_nets "VSS"
init_design
floorPlan -r 1.0 0.7 10 10 10 10
addRing -nets {VDD VSS} -type core_rings -width 2 -spacing 1 -layer {top M5 bottom M5 left M6 right M6}
place_design
clockDesign -specFile cts.spec
route_design
streamOut top.gds -mapFile gds2.map
```

### 1.4 Python API (PyCell, Innovus+)

**PCell (SKILL-based)**: Native parameterized cells in Virtuoso using SKILL/SKILL++ or PCell Designer GUI. Industry standard for custom cell creation.

**PyCell (Python-based)**: Python-language PCells via Ciranova/Synopsys PyCell Studio + OpenAccess. Offers portability but is third-party (not officially supported by Cadence).

**Innovus+ Python Support (2025+)**:
- Native Python scripting alongside TCL with shared database
- LLM AI Assistant generates scripts from natural language
- Python can call AI/ML libraries directly on live design data
- Common for meta-automation, report parsing, optimization loops

**Python-TCL Bridge Pattern**:
```python
import os
params = {"util": 0.7, "aspect": 1.0, "design": "top"}
tcl = f"""
set init_design_name "{params['design']}"
floorPlan -r {params['aspect']} {params['util']} 10 10 10 10
place_design
"""
with open("generated.tcl", "w") as f:
    f.write(tcl)
os.system("innovus -batch -files generated.tcl")
```

---

## 2. Synopsys Automation Interfaces

### 2.1 TCL Interfaces

**Overview**: All Synopsys tools embed TCL as the core scripting language, extending standard TCL with EDA-specific commands (collections, design queries, flow control).

**Tool Shells**:
| Tool | Shell | Purpose |
|------|-------|---------|
| Design Compiler | `dc_shell` | Logic synthesis |
| IC Compiler II | `icc2_shell` | Physical implementation (P&R) |
| PrimeTime | `pt_shell` | Static timing analysis |
| Fusion Compiler | `fc_shell` | Unified synthesis + implementation |

**Key Synopsys TCL Extensions**:
- `get_cells`, `get_nets`, `get_pins` - Object queries (return collections)
- `foreach_in_collection` - Iterate design objects
- `get_attribute` / `set_attribute` - Property access
- `filter_collection` - Object filtering
- `define_proc_attributes` / `parse_proc_arguments` - Reusable procedures

### 2.2 Design Compiler (Synthesis)

**Example - DC Synthesis Script**:
```tcl
# DC automation script
set search_path [list . $search_path]
set link_library [list * your_lib.db]
set target_library your_lib.db
read_verilog top.v
current_design top
read_sdc top.sdc
create_clock -name clk -period 10 [get_ports clk]
set_input_delay 2 -clock clk [all_inputs]
set_output_delay 2 -clock clk [all_outputs]
compile_ultra
write -format ddc -hierarchy -output top.ddc
write -format verilog -output top_netlist.v
write_sdc top_post_synth.sdc
report_qor > qor.rpt
report_timing > timing.rpt
report_area > area.rpt
```

### 2.3 IC Compiler II (Place and Route)

**Example - ICC2 Flow Snippet**:
```tcl
source icc2_common_setup.tcl
create_lib -technology tech.tf -ref_libs {std_cell.ndm io.ndm}
read_verilog top_netlist.v
link_design
read_sdc top.sdc
initialize_floorplan -core_utilization 0.7 -core_aspect_ratio 1.0
create_placement
legalize_placement
place_opt
clock_opt
route_opt
report_routing_rules
write_gds top.gds
```

### 2.4 PrimeTime (Static Timing Analysis)

**Example - PT Signoff Script**:
```tcl
read_db top.ddc
read_sdc top.sdc
update_timing
report_timing -delay_type max -max_paths 100 > timing_max.rpt
report_timing -delay_type min -max_paths 100 > timing_min.rpt
report_power > power.rpt
report_constraint -all_violators > violations.rpt
```

**Python Integration**: PrimeTime supports `py_eval` for calling Python code within TCL sessions.

### 2.5 SAIF/VCD Format Support

- **SAIF** (Switching Activity Interchange Format): Activity data for power analysis
- **VCD** (Value Change Dump): Waveform data from simulation
- Used by: PrimeTime (power), Design Compiler (power-aware synthesis)
- Read via: `read_saif`, `read_vcd` TCL commands

### 2.6 Reference Methodology (RM)

Synopsys provides production-quality RM scripts (TCL) for each tool via SolvNet customer portal. These are template-based complete flows that serve as starting points for automation.

---

## 3. Siemens EDA Automation Interfaces

### 3.1 Calibre TCL/SVRF

**SVRF (Standard Verification Rule Format)**:
- Declarative, geometry-focused rule language for DRC/LVS/reliability
- "Golden" reference format adopted by foundries worldwide
- Defines precise layout rules (spacing, width, connectivity)

**TVF (Tcl Verification Format)**:
- TCL-based preprocessor/extension to SVRF
- Adds programming constructs: loops, variables, conditionals, procedures
- Compiles to SVRF at runtime
- Enables dynamic, maintainable rule decks

**Calibre TCL Scripting**:
- Calibre Interactive: TCL customization files for runsets
- Calibre DESIGNrev: Full TCL/Tk API for layout viewer/editor
  - Custom scripts, batch runs, GUI extensions, triggers
- Calibre RealTime: TCL-driven DRC integration with P&R tools
- Calibre Connectivity Interface (CCI): Data exchange API

**Example - Calibre Run Command**:
```bash
calibre -drc -hier svrf_rules.cal layout.gds
calibre -lvs svrf_rules.cal layout.gds schematic.sp
```

### 3.2 Xpedition Automation

- TCL-based scripting for PCB design automation
- COM/automation interface for Windows integration
- Constraint Manager API for design rules
- ECAD-MCAD collaboration interfaces

### 3.3 Questa Verification API

**Core TCL Usage**:
- `vsim` command-line and DO-file scripting
- Questa SIM Command Reference for all TCL commands
- UVM flow automation via TCL/SystemVerilog

**UCDB (Unified Coverage Database) API**:
- Merge coverage results across engines (simulation + formal + emulation)
- Coverage reporting and verification management
- TCL and C API interfaces

**Questa One (AI-Enhanced)**:
- Verification IQ: Data-driven analytics
- Agentic Toolkit: AI-driven automation
- Stimulus-Free Verification
- Intelligent regression planning and coverage closure

**Verification Run Manager (VRM)**:
- TCL-based regression management
- Results aggregation and analytics
- Integration with coverage databases

---

## 4. KiCad Automation

### 4.1 Python Scripting API (pcbnew, eeschema)

**Evolution Timeline**:
| Version | Year | API Status |
|---------|------|------------|
| KiCad 7 | 2023 | SWIG pcbnew stable |
| KiCad 8 | Feb 2024 | SWIG pcbnew stable + kicad-cli enhanced |
| KiCad 9 | Feb 2025 | IPC API introduced, SWIG deprecated |
| KiCad 10 | Feb 2026 | SWIG removal planned, IPC API primary |

**Legacy SWIG pcbnew API (KiCad 8, still works in 9)**:
```python
import pcbnew

# Standalone script (headless)
board = pcbnew.LoadBoard("board.kicad_pcb")
print(f"Board has {board.GetNetCount()} nets")
for footprint in board.GetFootprints():
    print(f"  {footprint.GetReference()}: {footprint.GetPosition()}")
board.Save("modified.kicad_pcb")

# Action Plugin (appears in Tools menu)
class MyPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "My Plugin"
        self.category = "Utility"
        self.description = "Does something useful"
        self.show_toolbar_button = True

    def Run(self):
        board = pcbnew.GetBoard()
        # ... modify board ...
        pcbnew.Refresh()

MyPlugin().register()
```

**New IPC Python API (KiCad 9+, recommended)**:
```bash
pip install kicad-python
```
- Client-server architecture: Protocol Buffers + NNG sockets
- External Python process talks to running KiCad instance
- Stable across minor versions, language-agnostic
- Plugins register via `plugin.json` manifest
- Requires KiCad running with API enabled in settings

### 4.2 KiCad CLI (kicad-cli)

**Available since KiCad 7, enhanced significantly in 8 and 9.**

**Key PCB Commands**:
```bash
# Design Rule Check
kicad-cli pcb drc --output report.json board.kicad_pcb

# Export formats
kicad-cli pcb export gerbers --output gerbers/ --layers F.Cu,B.Cu board.kicad_pcb
kicad-cli pcb export drill --output drill/ board.kicad_pcb
kicad-cli pcb export step --output board.step board.kicad_pcb
kicad-cli pcb export pdf --layers F.Cu,B.Cu board.kicad_pcb
kicad-cli pcb export svg board.kicad_pcb
kicad-cli pcb export pos --output positions.csv board.kicad_pcb

# Schematic exports
kicad-cli sch export pdf schematic.kicad_sch
kicad-cli sch export bom --output bom.csv schematic.kicad_sch

# Advanced formats
kicad-cli pcb export odb++ board.kicad_pcb
kicad-cli pcb export ipc2581 board.kicad_pcb
```

**Jobsets (KiCad 9+)**:
- `.kicad_jobset` JSON files chain multiple CLI commands
- Run: `kicad-cli jobset run my_workflow.kicad_jobset`
- Ideal for CI/CD pipelines

### 4.3 Plugin System and Action Plugins

**Plugin Types**:
1. **Action Plugins** (legacy): Python scripts in `~/.kicad/scripting/plugins/`
2. **IPC Plugins** (KiCad 9+): External Python with `plugin.json` manifest
3. **Content Manager**: Install plugins from KiCad Plugin Repository

**Notable Community Plugins**:
- **KiKit**: Panelization, fabrication automation CLI
- **kigadgets**: Cross-version (v5-v9) stable Python wrapper
- **InteractiveHtmlBom**: BOM visualization

### 4.4 IPC-2581/ODB++ Export

- Native CLI export: `kicad-cli pcb export ipc2581` / `odb++`
- Standards for PCB manufacturing data exchange
- Replace traditional Gerber+drill+BOM bundles
- Enable intelligent factory floor integration

---

## 5. OpenROAD/OpenLane Automation

### 5.1 OpenROAD TCL API

**Overview**: OpenROAD is the core open-source physical design engine with a unified database (OpenDB) and modular stage architecture.

**TCL Commands (Primary Interface)**:
```tcl
# Read design
read_lef tech.lef
read_lef std_cell.lef
read_def floorplan.def
read_verilog netlist.v
link_design top

# Flow stages
initialize_floorplan -die_area "0 0 1000 1000" -core_area "50 50 950 950"
global_placement
detailed_placement
clock_tree_synthesis
global_route
detailed_route

# Output
write_def final.def
write_db final.odb
```

### 5.2 Python Bindings

**OpenROAD Python API** (SWIG bindings to C++):
```python
# Run with: openroad -python script.py
from openroad import Design, Tech

tech = Tech()
tech.readLef("sky130A/tech.lef")
design = Design(tech)
design.readDef("floorplan.def")
# Call placement, CTS, routing APIs directly
design.writeDb("final.db")
```

**Limitations**: Python API covers DB operations; TCL remains more complete for all stages.

### 5.3 Flow Configuration

**OpenLane v1 (Maintenance Mode)**:
```tcl
# config.tcl
set ::env(DESIGN_NAME) "my_design"
set ::env(VERILOG_FILES) "rtl.v"
set ::env(CLOCK_PERIOD) "10"
set ::env(CLOCK_PORT) "clk"
# Run: ./flow.tcl -design my_design
```

**LibreLane / OpenLane 2 (Recommended, 2025+)**:

Configuration supports JSON, YAML, TCL, and Python dict:

```json
{
  "DESIGN_NAME": "my_design",
  "VERILOG_FILES": ["dir::rtl/*.v"],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 10.0,
  "PDK": "sky130A",
  "RUN_CTS": true,
  "RUN_DRT": true
}
```

**Python API (Full Programmatic Control)**:
```python
from openlane.flows import Flow
from openlane.config import Config

config = Config(
    DESIGN_NAME="my_design",
    VERILOG_FILES=["rtl/top.v"],
    CLOCK_PERIOD=10.0,
    PDK="sky130A",
)

Classic = Flow.factory.get("Classic")
results = Classic.run(config)

# Parameter sweep example
for period in [8.0, 10.0, 12.0]:
    config = config.with_updated(CLOCK_PERIOD=period)
    results = Classic.run(config)
    print(f"Period {period}: area = {results.metrics['design__die__area']}")
```

**Architecture**: Immutable States -> Steps (TclStep wraps OpenROAD) -> Flows (e.g., Classic)

**Installation**:
```bash
# Nix (recommended)
nix run github:librelane/librelane
# Python + Docker
pip install --upgrade librelane
librelane --dockerized --pdk-root ~/.volare config.json
```

---

## 6. Common EDA Automation Patterns

### 6.1 File Formats as Interfaces

The standard EDA interchange formats form the backbone of tool-to-tool automation:

| Format | Type | Purpose | Stage |
|--------|------|---------|-------|
| **Verilog** | Text/HDL | RTL description, gate-level netlist | Input/Synthesis output |
| **VHDL** | Text/HDL | RTL description (alternative) | Input/Synthesis output |
| **SDC** | Text/TCL | Timing constraints | All stages |
| **LEF** | ASCII | Library abstracts (tech + cell) | P&R input |
| **DEF** | ASCII | Design placement/routing | P&R I/O |
| **GDSII** | Binary | Final layout for fabrication | Tape-out |
| **OASIS** | Binary | Compressed layout (GDSII successor) | Tape-out |
| **SPICE** | Text | Transistor-level netlist | Simulation |
| **SPEF** | Text | Parasitic extraction data | Timing/Power |
| **SAIF/VCD** | Text/Binary | Switching activity / waveforms | Power analysis |
| **Liberty (.lib)** | Text | Timing/power characterization | All stages |
| **SDF** | Text | Standard Delay Format | Timing |
| **GDS/ODB++/IPC-2581** | Various | Manufacturing data | Fabrication |

**Standard RTL-to-GDSII Flow**:
```
Verilog RTL -> [Synthesis] -> Gate Netlist + SDC
  -> [P&R reads LEF] -> DEF (placed/routed)
    -> [Extraction] -> SPEF/SPICE
      -> [Timing Signoff] -> Reports
        -> [Stream Out] -> GDSII
```

### 6.2 Command-Line Batch Processing

**All major EDA tools support batch/non-GUI mode**:

| Tool | Batch Command |
|------|--------------|
| Cadence Virtuoso | `virtuoso -nograph -replay script.il` |
| Cadence Innovus | `innovus -batch -files script.tcl` |
| Synopsys DC | `dc_shell -f script.tcl` |
| Synopsys ICC2 | `icc2_shell -f script.tcl` |
| Synopsys PT | `pt_shell -f script.tcl` |
| Calibre | `calibre -drc rules.svrf layout.gds` |
| OpenROAD | `openroad -exit script.tcl` |
| KiCad | `kicad-cli pcb export gerbers board.kicad_pcb` |
| Yosys | `yosys -p "read_verilog top.v; synth; write_verilog out.v"` |
| Magic | `magic -dnull -noconsole < script.tcl` |
| KLayout | `klayout -b -r script.py` |

**Python Orchestration Pattern**:
```python
import subprocess
import json

# Chain tools via file I/O
subprocess.run(["yosys", "-p", "synth -top my_design", "rtl.v"])
subprocess.run(["openroad", "-exit", "pnr_flow.tcl"])
subprocess.run(["klayout", "-b", "-r", "drc_check.py"])
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "board.kicad_pcb"])
```

### 6.3 GUI Automation (Last Resort)

**Native scripting should always be preferred.** When APIs are unavailable:

| Tool | Approach | Reliability |
|------|----------|-------------|
| **SikuliX** | Image recognition (OpenCV) | Medium (70-90%) |
| **PyAutoGUI** | Coordinate/image-based | Low (fragile) |
| **xdotool** | X11 window manipulation (Linux) | Medium |
| **AI GUI Agents** | LLM vision models | Experimental (2026) |

**SikuliX Example**:
```python
# Jython/Python syntax
click("place_icon.png")
type("cell_name")
wait(2)
click("simulate.png")
```

**Best Practice**: Use GUI automation only for testing third-party viewers, legacy GUI-only modules, or cross-tool regression suites where no API exists.

### 6.4 Python Libraries for EDA File Manipulation

| Library | Format | Purpose |
|---------|--------|---------|
| `gdstk` / `gdspy` | GDSII | Layout creation/manipulation |
| `gdsfactory` | GDSII | Photonics + electronics layout |
| `pyverilog` | Verilog | RTL parsing and analysis |
| `PySpice` | SPICE | Circuit simulation from Python |
| `KiKit` | KiCad | Panelization and automation |
| `kigadgets` | KiCad | Cross-version pcbnew wrapper |
| `openroad` (module) | OpenDB | Direct database access |
| `librelane` | OpenLane | Flow orchestration |
| `spydrnet` | EDIF/Verilog | Netlist manipulation |
| `amaranth` | HDL | Python-based hardware description |

---

## 7. Cross-Platform Comparison Matrix

### Scripting Language Support

| Vendor/Tool | TCL | Python | SKILL | Other |
|-------------|-----|--------|-------|-------|
| Cadence Virtuoso | - | PyCell (3rd party) | Native | - |
| Cadence Innovus | Native | Native (Innovus+) | - | - |
| Synopsys DC/ICC2/PT | Native | Limited (py_eval) | - | - |
| Siemens Calibre | TVF | - | - | SVRF |
| Siemens Questa | Native | - | - | SystemVerilog |
| KiCad | - | Native (IPC API) | - | CLI |
| OpenROAD | Native | SWIG bindings | - | - |
| OpenLane/LibreLane | Legacy | Native (primary) | - | JSON/YAML config |
| Yosys | Native | - | - | - |
| Magic | Native | - | - | - |
| KLayout | - | Native | - | Ruby |

### Automation Maturity Levels

| Tool | Batch Mode | Scripting API | Python | CI/CD Ready |
|------|-----------|--------------|--------|-------------|
| Cadence Virtuoso | Good | Excellent (SKILL) | Limited | Medium |
| Cadence Innovus | Excellent | Excellent (TCL) | Good (Innovus+) | Good |
| Synopsys DC | Excellent | Excellent (TCL) | Limited | Good |
| Synopsys ICC2 | Excellent | Excellent (TCL) | Limited | Good |
| Synopsys PT | Excellent | Good (TCL+py_eval) | Limited | Good |
| Calibre | Excellent | Good (TCL/SVRF) | Limited | Good |
| KiCad | Excellent | Good (IPC API) | Excellent | Excellent |
| OpenROAD | Excellent | Good (TCL) | Good | Excellent |
| LibreLane | Excellent | Excellent (Python) | Excellent | Excellent |
| Yosys | Excellent | Good (TCL) | Limited | Excellent |

---

## 8. MCP Integration Opportunities

### 8.1 High-Value MCP Server Targets

Based on automation API analysis, the following are prime candidates for MCP server development:

**Tier 1 - Direct API Integration (Open Source)**:
1. **KiCad MCP Server**: Full IPC API integration via `kicad-python`, plus CLI wrapper
2. **OpenROAD/LibreLane MCP Server**: Python API + flow configuration
3. **Yosys MCP Server**: TCL interface for synthesis automation
4. **KLayout MCP Server**: Python API for layout viewing/DRC

**Tier 2 - File Format Manipulation**:
5. **GDSII/OASIS MCP Server**: via gdstk for layout manipulation
6. **Verilog/HDL MCP Server**: via pyverilog for RTL analysis
7. **SPICE MCP Server**: via PySpice for circuit simulation
8. **LEF/DEF MCP Server**: Parser/generator for physical design data

**Tier 3 - Wrapper/Orchestration**:
9. **EDA Flow Orchestrator MCP**: Chain tools via subprocess + file I/O
10. **Calibre/Questa Wrapper MCP**: TCL script generation and execution

### 8.2 Key Integration Patterns

**Pattern 1: Direct Python API**
```
Claude -> MCP Server -> Python API -> EDA Tool
Example: Claude -> KiCad MCP -> kicad-python -> Running KiCad instance
```

**Pattern 2: CLI Wrapper**
```
Claude -> MCP Server -> subprocess -> CLI tool -> File output -> Parse results
Example: Claude -> OpenROAD MCP -> openroad -exit script.tcl -> Parse reports
```

**Pattern 3: File-Based**
```
Claude -> MCP Server -> Generate/Parse files -> EDA tool reads/writes
Example: Claude -> GDSII MCP -> gdstk create layout -> Export .gds
```

**Pattern 4: Script Generation**
```
Claude -> MCP Server -> Generate TCL/SKILL script -> User runs in tool
Example: Claude -> Innovus MCP -> Generate flow.tcl -> User sources in innovus
```

### 8.3 Recommended MCP Server Architecture

```
                    +------------------+
                    |   Claude Code    |
                    +--------+---------+
                             |
                    +--------+---------+
                    |   MCP Protocol   |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v--------+
     | KiCad MCP  |  | OpenROAD    |  | File Format |
     | Server     |  | MCP Server  |  | MCP Server  |
     +--------+---+  +------+------+  +----+--------+
              |              |              |
     +--------v---+  +------v------+  +----v--------+
     | kicad-cli  |  | openroad    |  | gdstk /     |
     | kicad-python| | librelane   |  | pyverilog   |
     +------------+  +-------------+  +-------------+
```

---

## Summary

### Key Findings

1. **TCL dominates commercial EDA**: Cadence Innovus, all Synopsys tools, Calibre, and OpenROAD use TCL as primary scripting language
2. **Python is rising**: KiCad IPC API, LibreLane, Innovus+ all adopt Python as first-class scripting
3. **SKILL is Cadence-specific**: Powerful but proprietary to Virtuoso ecosystem
4. **File formats are universal interfaces**: GDSII, LEF/DEF, Verilog, SPICE enable tool-agnostic automation
5. **Open-source tools are most MCP-friendly**: KiCad, OpenROAD, LibreLane, Yosys all have Python APIs or CLIs suitable for direct integration
6. **Commercial tools require script generation**: Best approached by generating TCL/SKILL scripts rather than direct API calls

### Automation API Access Difficulty

| Difficulty | Tools |
|-----------|-------|
| Easy (Public Python API) | KiCad, LibreLane, KLayout, gdstk |
| Medium (Open TCL + Python) | OpenROAD, Yosys, Magic |
| Hard (Licensed TCL) | Cadence Innovus, Synopsys DC/ICC2/PT |
| Hardest (Proprietary SKILL) | Cadence Virtuoso |
| N/A (Rule languages) | Calibre SVRF/TVF |
