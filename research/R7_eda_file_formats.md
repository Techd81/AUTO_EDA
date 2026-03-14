# R7: EDA File Formats, Standards, and Interoperability

> Research Date: 2026-03-14
> Status: Complete

## Table of Contents

1. [IC Design File Formats](#1-ic-design-file-formats)
2. [HDL and Netlist Formats](#2-hdl-and-netlist-formats)
3. [PCB Design File Formats](#3-pcb-design-file-formats)
4. [Exchange and Interoperability Standards](#4-exchange-and-interoperability-standards)
5. [Python Library Support](#5-python-library-support)
6. [Format Conversion Tools](#6-format-conversion-tools)
7. [Format Comparison Matrix](#7-format-comparison-matrix)
8. [Implications for AUTO_EDA Project](#8-implications-for-auto_eda-project)

---

## 1. IC Design File Formats

### 1.1 GDSII (Graphic Design System II)

**Overview**: GDSII is the de facto industry-standard binary database file format for exchanging IC layout artwork in EDA tools. It represents 2D geometric shapes, text labels, and hierarchical structures for photomask creation in semiconductor manufacturing.

**History & Governance**:
- Created by Calma in 1978; ownership later passed to Cadence
- Official specification: Calma GDSII Stream Format Manual 6.0 (Feb 1987)
- Despite being proprietary, universally supported by all EDA tools and foundries

**Technical Specification**:
- **Format**: Binary stream of variable-length records
- **Record Header**: 4 bytes (2B length, 1B record type, 1B data type)
- **Data Types**: 0=no data, 1=bit array, 2=2B int, 3=4B int, 4=4B real, 5=8B real, 6=ASCII
- **Coordinates**: 32-bit signed integers in database units (DBU)
- **Units**: Defined via UNITS record (e.g., 1 DBU = 1nm)

**File Structure (BNF)**:
```
HEADER -> BGNLIB -> LIBNAME -> UNITS -> {STRUCTURE}* -> ENDLIB
```
Each STRUCTURE: `BGNSTR -> STRNAME -> {element}* -> ENDSTR`

**Key Record Types**:

| Hex | Record | Purpose |
|-----|--------|---------|
| 00 | HEADER | File version (0x0004-0x0006) |
| 01 | BGNLIB | Library timestamps |
| 02 | LIBNAME | Library name |
| 03 | UNITS | DBU-to-user-unit and DBU-to-meter scaling |
| 05 | BGNSTR | Start of cell + timestamps |
| 06 | STRNAME | Cell name (<=32 chars) |
| 08 | BOUNDARY | Polygon element |
| 09 | PATH | Centerline with width |
| 0A | SREF | Single cell reference (instance) |
| 0B | AREF | Array of cell references |
| 0C | TEXT | Text label |
| 0D | LAYER | Layer number (0-255) |
| 0E | DATATYPE | Datatype (0-255) |
| 10 | XY | Coordinate list (4B int pairs) |
| 11 | ENDEL | End of geometry element |
| 04 | ENDLIB | End of library |

**Limitations**:
- 32-bit coordinate overflow at 300mm wafers (~+/-2.1 billion DBU)
- Massive file sizes (often >20GB for advanced nodes)
- No native compression or repetition
- Max 512-char strings, 4096-point polygons

**Usage**: Post-place-and-route verification generates GDSII for foundry mask preparation ("tape-out").

---

### 1.2 OASIS (Open Artwork System Interchange Standard)

**Overview**: OASIS (SEMI P39) is the recommended successor to GDSII for hierarchical IC mask layout data exchange. It addresses data-volume explosions in modern chip designs.

**History & Governance**:
- Developed by SEMI starting 2001; first specification released 2004
- Standard: SEMI P39-0416
- Variant: OASIS.MASK (SEMI P44) for photomask tools

**Key Advantages over GDSII**:
- **File size**: 5-20x smaller (80-97% reduction with CBLOCK + strict mode)
- **Performance**: 65-90% faster load times in EDA tools
- **Precision**: 64-bit+ arithmetic support
- **Compression**: Variable-length byte encoding, CBLOCK per-cell gzip

**Technical Features**:
- 11 repetition types for patterns (e.g., memory arrays)
- 25 trapezoid geometry variants + native circles and paths
- Strict mode: cell-name lookup table with file offsets for random access
- CBLOCK: internal per-cell DEFLATE compression

**File Structure**:
```
START -> CELLNAME -> LAYERNAME -> CELL definitions -> END
```
Records: START, CELLNAME, LAYERNAME, PLACEMENT, RECTANGLE, POLYGON, PATH, TRAPEZOID, CIRCLE, PROPERTY, CBLOCK, END

**Best Practices**:
- Enable CBLOCK + strict mode for maximum benefit
- Avoid re-zipping OASIS files (defeats internal compression)
- Recommended for designs at 16nm and below

---

### 1.3 LEF/DEF (Library Exchange Format / Design Exchange Format)

**Overview**: LEF and DEF are standard ASCII file formats used in physical design (place-and-route) for VLSI IC design.

**Specification**: LEF/DEF Language Reference v5.7 (Nov 2009, 414 pages); distributed by Si2 under Apache-2.0 license.

#### LEF (Library/Technology Definition)

**Purpose**: Defines reusable library and technology information (abstract views of cells, layers, vias, sites, design rules).

**Statement Order**: `VERSION -> UNITS -> LAYER -> VIA/VIARULE -> SITE -> MACRO -> END LIBRARY`

**Key Sections**:
```
UNITS
  DATABASE MICRONS 1000 ;
END UNITS

LAYER metal1
  TYPE ROUTING ;
  DIRECTION HORIZONTAL ;
  PITCH 0.56 ;
  WIDTH 0.20 ;
  SPACING 0.18 ;
END metal1

MACRO invX1
  CLASS CORE ;
  SIZE 2.0 BY 1.2 ;
  SITE coreSite ;
  PIN A
    DIRECTION INPUT ;
    PORT
      LAYER metal1 ;
      RECT 0.1 0.1 0.3 0.3 ;
    END
  END
  OBS
    LAYER metal1 ;
    RECT 0.5 0.5 1.5 0.7 ;
  END
END invX1
```

#### DEF (Design Instance Data)

**Purpose**: Captures design-specific physical data (die area, placements, routing, nets) at any stage.

**Structure**: `DESIGN -> DIEAREA -> ROWS/TRACKS -> COMPONENTS -> PINS -> NETS/SPECIALNETS -> END DESIGN`

**Key Sections**:
```
DIEAREA (0 0) (1000 1000) ;

COMPONENTS 2 ;
  - u1 invX1 + PLACED (100 200) N ;
  - u2 bufX2 + FIXED (500 300) FN ;
END COMPONENTS

NETS 1 ;
  - net1 (u1 A) (u2 Z)
    + ROUTED metal1 (100 200) (200 200) ;
END NETS
```

**Usage**: Read LEF + netlist + timing constraints -> generate DEF at each milestone (floorplan -> placed -> routed) -> export final DEF/GDSII for signoff.

---

### 1.4 Liberty (.lib) Format

**Overview**: The industry-standard ASCII specification for timing libraries in EDA, providing pre-characterized models of standard-cell timing, power, area, and logical functions.

**Governance**: Developed by Synopsys; maintained as open standard under Liberty Technical Advisory Board (IEEE-ISTO).

**Key Versions**: Liberty User Guides and Reference Manual Suite 2017.06, 2013.03

**Hierarchical Structure**:
```liberty
library (tech_lib_name) {
    technology (cmos);
    delay_model : table_lookup;    /* NLDM or ccs_timing */
    time_unit : "1ns";
    voltage_unit : "1V";
    capacitive_load_unit (1, pf);
    operating_conditions (TT_0p8V_25C) { ... }

    lu_table_template (delay_template_5x5) {
        variable_1 : input_net_transition;
        variable_2 : total_output_net_capacitance;
        index_1 ("0.01, 0.05, 0.10, 0.20, 0.40");
        index_2 ("0.01, 0.05, 0.10, 0.20, 0.40");
    }

    cell (INV_X1) {
        area : 2.532;
        pin (A) {
            direction : input;
            capacitance : 0.0015;
        }
        pin (Y) {
            direction : output;
            function : "!A";
            timing () {
                related_pin : "A";
                timing_sense : negative_unate;
                cell_rise (delay_template_5x5) {
                    values ( "0.05, 0.06, ..." );
                }
            }
        }
    }
}
```

**Timing Models**:
- **NLDM** (Non-Linear Delay Model): Table lookup for delay/slew vs. input transition and output capacitance
- **CCS** (Composite Current Source): Piecewise-linear current waveforms for sub-22nm accuracy
- **LVF** (Liberty Variation Format): Statistical variation data for advanced OCV analysis

**PVT Corners**: Multiple .lib files per library (worst-case, best-case, typical), each targeting one Process-Voltage-Temperature corner.

---

### 1.5 SPEF / SDF (Parasitic and Delay Formats)

#### SPEF (Standard Parasitic Exchange Format)

**Standard**: IEEE Std 1481-1999 / 1481-2019

**Purpose**: ASCII exchange format for parasitic R/C data from extraction tools to STA tools.

**File Structure**:
```
*SPEF "IEEE 1481-2009"
*DESIGN "my_chip"
*C_UNIT 1FF
*R_UNIT 1K

*D_NET netX total_cap
*CONN
  *P port1 I *C 0.0 100.0
  *I inst1:A I *C 50.0 100.0 *L 5.0
*CAP
  1 *1 7.56                    /* ground cap */
  2 *1 *2 0.62                 /* coupling cap */
*RES
  1 *1 *2 20.15               /* resistance */
*END
```

#### SDF (Standard Delay Format)

**Standard**: IEEE Std 1497-2001

**Purpose**: ASCII format for annotating computed min/typ/max delays into simulators or STA engines.

**File Structure**:
```
(DELAYFILE
  (SDFVERSION "4.0")
  (DESIGN "my_chip")
  (CELL
    (CELLTYPE "AND2")
    (INSTANCE U1)
    (DELAY
      (ABSOLUTE
        (IOPATH A Z (0.15:0.20:0.25))
        (INTERCONNECT U1/Z U2/A (0.08:0.10:0.12))
      )
    )
    (TIMINGCHECK
      (SETUP D CLK (0.10:0.12:0.15))
    )
  )
)
```

**EDA Flow**: Parasitic Extraction -> SPEF -> STA tool + .lib + SDC -> SDF for back-annotation

---

## 2. HDL and Netlist Formats

### 2.1 Verilog / SystemVerilog

**Standard**: IEEE 1364 (Verilog) / IEEE 1800 (SystemVerilog)

**Type**: Hardware Description Language; structural descriptions serve as gate-level netlists post-synthesis.

**Structural Netlist Example**:
```verilog
module and_not (input a, b, output y);
  wire inter;
  and u_and (inter, a, b);
  not u_not (y, inter);
endmodule
```

**Characteristics**: Concise, C-like syntax; widely used in ASIC/FPGA flows for synthesis output and gate-level simulation.

### 2.2 VHDL

**Standard**: IEEE 1076

**Type**: Strongly-typed HDL; structural architecture descriptions provide netlist representations.

**Structural Netlist Example**:
```vhdl
architecture structural of top is
  signal x : std_logic;
  component andgate port (i1, i2 : in std_logic; o : out std_logic); end component;
begin
  u1: andgate port map (i1 => a, i2 => b, o => x);
end architecture;
```

**Characteristics**: Verbose, Ada-like; excels in large-scale reusable designs with explicit typing.

### 2.3 SPICE Netlist

**Usage**: Analog and mixed-signal circuit simulation (HSPICE, LTspice, Ngspice).

**Netlist Example**:
```spice
V1 1 0 DC 5
R1 1 2 1k
R2 2 0 1k
.op
.end
```

**Characteristics**: Instance-based format (component + nodes + parameters); continuous-time electrical behavior.

### 2.4 EDIF (Electronic Design Interchange Format)

**Standard**: ANSI/EIA-548

**Type**: Vendor-neutral, S-expression (Lisp-like) format for exchanging netlists and schematics between EDA tools.

**Example**:
```lisp
(edif example
  (edifVersion 2 0 0)
  (library lib (edifLevel 0)
    (cell cell1 (cellType generic)
      (view view1 (viewType netlist)
        (contents
          (instance ... )
          (net net1 (joined ... )))))))
```

**Characteristics**: Machine-focused, less human-readable; created in 1983 for tool-to-tool data transfer.

### 2.5 Format Comparison (HDL/Netlist)

| Format | Domain | Syntax | Primary Use |
|--------|--------|--------|-------------|
| Verilog/SV | Digital | C-like, concise | Synthesis output, simulation |
| VHDL | Digital | Ada-like, verbose | Synthesis output, formal verification |
| SPICE | Analog | Instance-based | Circuit simulation |
| EDIF | Interchange | S-expression | Tool-to-tool transfer |

---

## 3. PCB Design File Formats

### 3.1 KiCad S-Expression Format (.kicad_pcb)

**Overview**: KiCad uses S-expression (symbolic expression) format - nested parentheses representing hierarchical structures in plain text.

**Specification**: Official at dev-docs.kicad.org/en/file-formats/sexpr-pcb/

**Header**:
```lisp
(kicad_pcb
  (version 20240130)
  (generator "pcbnew")
  ;; sections...
)
```

**Key Sections**:
- **Layers**: Up to 60 layers (32 copper max) with canonical names (F.Cu, B.Cu, etc.)
- **General**: Board thickness in mm
- **Setup**: Stackup, clearances, plot parameters
- **Nets**: Electrical net definitions
- **Footprints**: Component placements with pads, silk, courtyard
- **Tracks**: Segments, vias, arcs
- **Zones**: Copper pours with thermal reliefs

**Characteristics**: Coordinates in mm (1nm resolution), UTF-8 text, Git-friendly, directly accepted by many manufacturers (JLCPCB, PCBWay).

### 3.2 Gerber Format (RS-274X / X2 / X3)

**Overview**: De facto industry standard for describing individual PCB layer images in ASCII vector format.

**Governance**: Maintained by Ucamco (latest spec revision 2024.05)

**Evolution**:
- RS-274-D: Obsolete (retired 2014)
- RS-274X (Extended Gerber): Current base standard
- X2 (2014): Added semantic attributes (pads, nets, stackup)
- X3: Further attribute enhancements

**Characteristics**:
- Multiple files per layer + companion .gbrjob (job file)
- Simple, compact ASCII vector format
- Universal compatibility (90%+ adoption)
- Limitation: Error-prone multi-file approach for complex designs

### 3.3 Excellon (PCB NC Drill)

**Purpose**: Numerical-control text format for drilling and routing instructions.

**Example**:
```
M48          ; Header start
T01C0.6      ; Tool 1: 0.6mm drill
%            ; Header end
T01          ; Select tool
X100Y200     ; Drill at (100, 200)
M30          ; End of file
```

**Characteristics**: Always paired with Gerber; drives CNC machines directly; lacks semantic CAD-to-CAM richness.

### 3.4 ODB++ (Open Database ++)

**Overview**: Intelligent, hierarchical CAD-to-CAM exchange format consolidating all fabrication, assembly, and test data into a single compressed package.

**Governance**: Originally Valor Computerized Systems (1995); now Siemens/Mentor Graphics

**Key Features**:
- Single .tgz/.zip package with design + process + manufacturing data
- Semantic modeling: explicit pad/trace distinction, full netlist, BOM
- Component placement with X/Y rotation, stackup (rigid/flex)
- Enables automated DFM checks and global edits
- Version 8.1 as of 2026

### 3.5 IPC-2581 (IPC-DPMX)

**Overview**: Open, vendor-neutral XML-based industry standard providing a complete "digital twin" of the PCB product model.

**Governance**: IPC consortium since 2004; current Rev C

**Key Features**:
- Single XML file: copper images, stackup, netlist, BOM, materials, tolerances
- Bidirectional and human/machine-readable
- Supports fab, assembly, and test data
- Growing adoption especially in North America/Europe

### 3.6 PCB Format Comparison

| Format | Structure | Intelligence | Adoption (2026) | Best For |
|--------|-----------|-------------|-----------------|----------|
| Gerber + Excellon | Multiple ASCII files | Low (image-based) | Dominant (90%+) | Legacy/simple fabs |
| Gerber X2/X3 | Multiple files (backward-compatible) | Medium | Increasing | Conservative upgrade |
| ODB++ | Single zipped directory | High (semantic DB) | Very high | Complex boards, automated CAM |
| IPC-2581 | Single XML file | High (full product model) | Growing rapidly | Future-proof, open ecosystems |
| KiCad S-expr | Single text file | Medium-High | Growing | Open-source, Git-friendly |

---

## 4. Exchange and Interoperability Standards

### 4.1 OpenAccess

**Overview**: C++ API (2000+ classes) plus managed multi-user reference database for EDA tool interoperability in IC design flows.

**Governance**: Silicon Integration Initiative (Si2) OpenAccess Coalition
- Originated from Cadence contribution (~2000)
- Members: Intel, TSMC, Samsung, Synopsys, Cadence, Google, NVIDIA (2026 board)
- Not an IEEE standard; industry consortium effort

**Key Features**:
- Common persistent design database for multi-vendor tool interop
- Extensible API with translators (Verilog, LEF/DEF, GDSII, JSON)
- Scripting: oaScript in Python/Ruby/Tcl
- Multi-process parallel execution support
- 17x throughput gains via parallel processing in benchmarks

**Purpose**: Runtime shared data model allowing EDA tools from different vendors to read/write/modify shared IC design data without error-prone file translations.

### 4.2 IP-XACT (IEEE 1685)

**Overview**: XML-schema-based format standardizing metadata for reusable electronic design blocks (IP) in EDA tool flows.

**Standards History**:
- SPIRIT Consortium (founded 2003) -> Accellera -> IEEE
- IEEE 1685-2009, 1685-2014, **1685-2022** (current)

**Key Features**:
- Standardized descriptions of: components, bus interfaces, registers, memory maps, power domains, file sets
- TGI (Tight Generator Interface) API for automated IP integration
- 2022 additions: structs/unions, mode-dependent registers, power domain bindings, REST-based TGI
- Free download via IEEE GET program (earlier versions)

**Purpose**: Tool-independent IP exchange enabling automated SoC assembly, register generation, and verification collateral creation.

### 4.3 Complementary Roles

| Standard | Scope | Level | Organization |
|----------|-------|-------|-------------|
| OpenAccess | Runtime design DB sharing | Implementation (physical/logical) | Si2 Coalition |
| IP-XACT | IP metadata exchange | Architecture (SoC integration) | IEEE/Accellera |
| LEF/DEF | Physical design data | File-based exchange | Si2 (Apache 2.0) |
| GDSII/OASIS | Mask layout data | Tape-out delivery | Calma/SEMI |

**Integration Flow**: IP vendors deliver blocks in IP-XACT XML -> integrators use generators to instantiate -> assembled design resides in OpenAccess DB -> synthesis, P&R, verification tools interoperate.

### 4.4 Other IEEE EDA Standards

| Standard | Description |
|----------|-------------|
| IEEE 1364 | Verilog HDL |
| IEEE 1800 | SystemVerilog |
| IEEE 1076 | VHDL |
| IEEE 1481 | SPEF (parasitic exchange) |
| IEEE 1497 | SDF (delay format) |
| IEEE 1735 | Encryption of IP |
| IEEE 1801 | UPF (Unified Power Format) |

---

## 5. Python Library Support

### 5.1 Layout File Libraries

| Library | Purpose | Formats | Status (2026) | Performance |
|---------|---------|---------|---------------|-------------|
| **gdstk** | Fast layout generation/manipulation | GDSII + OASIS | v1.0.0 (Feb 2026), active | 10-16x faster than gdspy |
| gdspy | Legacy GDSII creation | GDSII only | Deprecated, archived (Aug 2024) | Baseline (Python-only) |
| **gdsfactory** | High-level parametric design | GDS/OASIS/Gerber/STL | v9.39.0 (Mar 2026), very active | Uses gdstk + KLayout |
| **KLayout (pya)** | Full layout editor + scripting | GDS/OASIS/CIF/DXF/LEF/DEF/Gerber | Active PyPI module (v0.30.x) | C++ core |

**Recommendation**: Use **gdstk** for raw GDSII/OASIS operations, **gdsfactory** for productive design flows, **KLayout** for interactive editing/DRC.

### 5.2 Simulation Libraries

| Library | Purpose | Interface | Status (2026) |
|---------|---------|-----------|---------------|
| **PySpice** | Analog circuit simulation | Ngspice/Xyce | Stable (v1.5, minor 2024 fixes) |
| **cocotb** | Digital RTL verification | VHDL/SystemVerilog co-simulation | v2.0 (Sep 2025), very active |
| **amaranth** | Digital design framework | Generates Verilog | Active |
| **migen/litex** | SoC builder framework | Generates Verilog | Active |

### 5.3 Parsing Libraries

| Library | Purpose | Status |
|---------|---------|--------|
| **hdlConvertor** | Fast Verilog/VHDL/SV parser to AST/JSON | Active (GitHub: Nic30) |
| **liberty-parser** | Parse Liberty .lib files | Available |
| **pyverilog** | Verilog parser and analysis | Maintained |
| **spydrnet** | Netlist analysis and transformation | Active |

### 5.4 Complete Python EDA Stack (2026)

```
Design Entry:     amaranth/migen -> Verilog
Simulation:       cocotb (digital) + PySpice (analog)
Synthesis:        Yosys (Python bindings)
Layout:           gdstk + gdsfactory + KLayout
Verification:     cocotb + formal tools
Physical:         OpenROAD Python API
Tape-out:         gdstk/KLayout -> GDSII/OASIS
```

---

## 6. Format Conversion Tools

### 6.1 Layout Format Conversion

| Tool | Conversions Supported | Type | Notes |
|------|----------------------|------|-------|
| **KLayout** | GDS <-> OASIS <-> DXF <-> CIF <-> LEF/DEF <-> Gerber | Open source (GPLv2+) | Best all-around; batch CLI + Python scripting |
| **gdstk** | GDS <-> OASIS (programmatic) | Open source (Python/C++) | Best for scripted operations |
| **laykit** | GDS <-> OASIS (bidirectional) | Open source (Rust) | High-performance; released Nov 2025 |
| **gdsfactory** | GDS -> OASIS/Gerber/STL/SVG | Open source (Python) | Integrated in design workflow |
| **Magic** | GDS <-> CIF <-> DEF | Open source | Classic VLSI layout tool |

### 6.2 HDL/RTL Format Conversion

| Tool | Conversions Supported | Type | Notes |
|------|----------------------|------|-------|
| **EDAUtils** | Verilog <-> VHDL <-> IP-XACT <-> Liberty <-> SystemC | Free (SourceForge) | Preserves structure; updated June 2025 |
| **hdlConvertor** | Verilog/VHDL/SV -> AST/JSON | Open source | Fast parser-based |
| **vhd2vl** | VHDL -> Verilog | Open source | Simple structural conversion |
| **Yosys** | Various netlist formats | Open source | Via synthesis passes |

### 6.3 PCB Format Conversion

| Tool | Conversions Supported | Type | Notes |
|------|----------------------|------|-------|
| **KiCad** | Eagle/OrCAD -> KiCad; export Gerber/DXF/IPC-2581 | Open source | Best for PCB migration |
| **pcb-rnd** | Many PCB formats | Open source | High interoperability |
| **gerbv** | Gerber viewer/converter | Open source (GPL) | View and convert Gerber |

### 6.4 Conversion Feasibility Matrix

| From \ To | GDSII | OASIS | LEF/DEF | Verilog | VHDL | SPICE | Gerber |
|-----------|-------|-------|---------|---------|------|-------|--------|
| **GDSII** | - | Yes | Partial | No | No | No | Yes (via KLayout) |
| **OASIS** | Yes | - | Partial | No | No | No | Yes |
| **LEF/DEF** | Partial | Partial | - | No | No | No | No |
| **Verilog** | No | No | No | - | Yes | Partial | No |
| **VHDL** | No | No | No | Yes | - | Partial | No |
| **SPICE** | No | No | No | Partial | Partial | - | No |
| **Gerber** | No | No | No | No | No | No | - |

**Key insight**: Layout formats (GDSII/OASIS) and HDL formats (Verilog/VHDL) operate in fundamentally different domains. Cross-domain conversion requires synthesis (HDL -> layout) or extraction (layout -> netlist), not simple format translation.

---

## 7. Format Comparison Matrix

### 7.1 IC Design Formats

| Format | Type | Encoding | Hierarchy | Size | Standard | Primary Tool |
|--------|------|----------|-----------|------|----------|-------------|
| GDSII | Layout | Binary | Yes (cells) | Very large | Calma proprietary | All EDA |
| OASIS | Layout | Binary | Yes (cells) | 5-20x smaller | SEMI P39 | All EDA |
| LEF | Library abstract | ASCII | No | Small | Si2 Apache-2.0 | P&R tools |
| DEF | Design data | ASCII | Flat | Medium | Si2 Apache-2.0 | P&R tools |
| Liberty | Timing library | ASCII | Groups | Medium | IEEE-ISTO | Synth/STA |
| SPEF | Parasitics | ASCII | Net-based | Medium-Large | IEEE 1481 | STA tools |
| SDF | Delays | ASCII | Cell-based | Medium | IEEE 1497 | Simulation/STA |

### 7.2 HDL/Netlist Formats

| Format | Domain | Encoding | Hierarchy | Simulation | Synthesis |
|--------|--------|----------|-----------|------------|-----------|
| Verilog/SV | Digital | ASCII | Module | Yes | Yes |
| VHDL | Digital | ASCII | Entity/Arch | Yes | Yes |
| SPICE | Analog | ASCII | Subcircuit | Yes | No |
| EDIF | Interchange | ASCII (S-expr) | Library/Cell | No | Partial |

### 7.3 PCB Formats

| Format | Encoding | Single File | Intelligence | Open Standard |
|--------|----------|-------------|-------------|---------------|
| Gerber | ASCII | No (per-layer) | Low | Ucamco spec |
| Excellon | ASCII | No (drill only) | Low | IPC-NC-349 |
| ODB++ | Binary (zipped) | Yes | High | Siemens (public spec) |
| IPC-2581 | XML | Yes | High | IPC open standard |
| KiCad | ASCII (S-expr) | Yes | Medium | Open source |

---

## 8. Implications for AUTO_EDA Project

### 8.1 Key Formats to Support

**Priority 1 (Must Support)**:
- GDSII / OASIS - Layout viewing, manipulation, tape-out
- Verilog / SystemVerilog - RTL and netlist handling
- LEF/DEF - Physical design data exchange
- Liberty (.lib) - Timing library queries
- Gerber - PCB manufacturing output

**Priority 2 (Should Support)**:
- SPEF/SDF - Parasitic and timing data
- VHDL - Alternative HDL support
- KiCad S-expression - Growing open-source PCB ecosystem
- IP-XACT - IP block metadata

**Priority 3 (Nice to Have)**:
- ODB++ / IPC-2581 - Advanced PCB manufacturing
- SPICE - Analog simulation
- EDIF - Legacy interchange

### 8.2 Python Libraries for MCP Integration

For building MCP tools that interact with EDA files:

| Use Case | Recommended Library | MCP Tool Potential |
|----------|--------------------|--------------------|
| Read/write GDSII/OASIS | gdstk | `eda.layout.read`, `eda.layout.write` |
| Layout viewing/DRC | KLayout Python API | `eda.layout.view`, `eda.drc.run` |
| Parse Verilog | pyverilog/hdlConvertor | `eda.hdl.parse`, `eda.hdl.analyze` |
| Parse Liberty timing | liberty-parser | `eda.timing.query` |
| SPICE simulation | PySpice | `eda.simulate.spice` |
| RTL verification | cocotb | `eda.verify.run` |
| Format conversion | KLayout + gdstk | `eda.convert.format` |

### 8.3 Interoperability Considerations

1. **All major IC formats are well-supported** by open-source Python libraries
2. **KLayout is the Swiss Army knife** for layout format handling (read/write/convert/view)
3. **gdstk + gdsfactory** provide the best programmatic layout manipulation
4. **No unified "read everything" library exists** - need specialized parsers per format
5. **Cross-domain conversion** (layout <-> HDL) requires synthesis/extraction tools, not simple converters
6. **ASCII formats** (LEF/DEF, Liberty, SPEF, SDF) are easiest to parse/generate with custom tools
7. **Binary formats** (GDSII, OASIS) require specialized libraries (gdstk, KLayout)

### 8.4 MCP Server Architecture Implications

- **Format-specific tools**: Each major format needs its own MCP tool with specialized parsing
- **Layered approach**: Raw file I/O layer -> format parsing layer -> semantic query layer
- **Caching**: Layout files can be very large; need efficient caching strategies
- **Streaming**: GDSII/OASIS files may need streaming access rather than full load
- **Validation**: Each format has strict syntax rules; MCP tools should validate before write

---

## References

### Official Specifications
1. Calma GDSII Stream Format Manual 6.0 (Feb 1987)
2. SEMI P39 (OASIS Standard)
3. Si2 LEF/DEF Language Reference v5.7 (Nov 2009)
4. Liberty User Guides and Reference Manual Suite v2017.06
5. IEEE Std 1481 (SPEF)
6. IEEE Std 1497 (SDF)
7. IEEE Std 1685-2022 (IP-XACT)
8. KiCad Developer Documentation - Board File Format

### Key Libraries & Tools
9. gdstk: https://github.com/heitzmann/gdstk
10. gdsfactory: https://gdsfactory.github.io/gdsfactory/
11. KLayout: https://www.klayout.de/
12. PySpice: https://github.com/PySpice-org/PySpice
13. cocotb: https://www.cocotb.org/
14. EDAUtils: https://sourceforge.net/projects/edautils-converters/
15. hdlConvertor: https://github.com/Nic30/hdlConvertor

### Standards Organizations
16. Si2 (Silicon Integration Initiative): https://si2.org/
17. SEMI: https://www.semi.org/
18. Accellera: https://www.accellera.org/
19. IPC: https://www.ipc.org/
20. Ucamco (Gerber): https://www.ucamco.com/
