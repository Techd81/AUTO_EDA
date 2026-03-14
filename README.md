# AUTO_EDA

> AI-driven EDA automation platform — natural language to real EDA tool operations via Claude + MCP

AUTO_EDA is an open-source AI capability layer for the open-source EDA ecosystem. It bridges Claude (or any MCP-compatible AI) with real EDA tools through the [Model Context Protocol](https://modelcontextprotocol.io), enabling engineers to automate PCB design, digital IC synthesis, HDL analysis, and more through natural language.

## What It Does

Instead of memorizing EDA tool commands, you describe what you want:

```
"Synthesize this Verilog file targeting Xilinx and show me the gate count"
"Run DRC on my KiCad board and list all violations"
"Check this HDL file for lint issues and undefined modules"
```

AUTO_EDA translates those instructions into real tool invocations via MCP tools.

## MCP Servers (Phase 0)

### Yosys Server — RTL Synthesis
For open-source RTL synthesis with [Yosys](https://yosyshq.net/yosys/).

| Tool | Description |
|------|-------------|
| `synthesize` | Synthesize Verilog/SystemVerilog to gate-level netlist |
| `rtl_stats` | Report wire/cell/memory counts at RTL level |
| `check_design` | Check for undefined modules, multi-driven signals, combinational loops |
| `show_schematic` | Generate DOT-format RTL schematic (renders with Graphviz) |
| `optimize_design` | Run opt passes and report cell reduction percentage |

### KiCad Server — PCB Design
For PCB automation with [KiCad](https://www.kicad.org/) v9/v10.

| Tool | Description |
|------|-------------|
| `get_board_info` | Read PCB metadata: dimensions, layer count, footprint count |
| `list_components` | List all schematic components with values and footprints |
| `get_schematic_info` | Read schematic summary: component count, net count |
| `run_drc` | Run Design Rule Check, return violations list |
| `run_erc` | Run Electrical Rule Check on schematic |
| `export_bom` | Export Bill of Materials (CSV/JSON) |
| `export_gerber` | Export Gerber manufacturing files |

### Verilog Utils Server — HDL Analysis
Language-level tools for Verilog/SystemVerilog files (no EDA tool required).

| Tool | Description |
|------|-------------|
| `parse_verilog` | Parse HDL file, extract module definitions and port lists |
| `extract_modules` | List all module names declared in a file |
| `analyze_hierarchy` | Analyze module instantiation hierarchy |
| `lint_check` | Static checks: unused ports, implicit nets, blocking assignments in sequential always |
| `extract_ports` | Extract port directions, widths, and parameters for a specific module |

## Installation

```bash
# Clone the repository
git clone https://github.com/Techd81/AUTO_EDA.git
cd AUTO_EDA

# Install with uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### EDA Tool Prerequisites

```bash
# Ubuntu/Debian
sudo apt install yosys kicad

# macOS
brew install yosys
brew install --cask kicad
```

## Usage

### Run a MCP Server

```bash
# Yosys MCP Server (stdio transport for Claude Desktop / Claude Code)
python -m auto_eda yosys

# KiCad MCP Server
python -m auto_eda kicad

# Verilog Utils MCP Server
python -m auto_eda verilog
```

### Connect to Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "python",
      "args": ["-m", "auto_eda", "yosys"]
    },
    "auto-eda-kicad": {
      "command": "python",
      "args": ["-m", "auto_eda", "kicad"]
    },
    "auto-eda-verilog": {
      "command": "python",
      "args": ["-m", "auto_eda", "verilog"]
    }
  }
}
```

### Run Tests

```bash
pytest tests/ -v
```

## Architecture

```
src/auto_eda/
├── core/              # Shared foundation
│   ├── errors.py      # EDAErrorCode hierarchy
│   ├── process.py     # Async subprocess management with timeout
│   ├── base_server.py # FastMCP factory + @eda_tool decorator
│   └── result.py      # Unified success/failure response types
├── models/            # Shared Pydantic models
└── servers/
    ├── yosys/         # Yosys MCP Server (5 tools)
    ├── kicad/         # KiCad MCP Server (7 tools)
    └── verilog_utils/ # Verilog Utils MCP Server (5 tools)
```

**Tech stack:** Python 3.10+ · FastMCP · Pydantic · mypy strict · ruff · pytest

## Roadmap

| Phase | Timeline | Scope |
|-------|----------|-------|
| **Phase 0 (now)** | Month 1-2 | Yosys + KiCad + Verilog Utils (~17 tools) |
| Phase 1 | Month 3-4 | Verilator + cocotb + KLayout (~30 new tools) |
| Phase 2 | Month 5-8 | OpenROAD + ngspice + full RTL→GDSII flow |
| Phase 3 | Month 9-12 | Visual feedback loop: screenshot → AI analysis → auto-fix |

## Comparison

| Feature | AUTO_EDA | MCP4EDA |
|---------|-----------|---------|
| PCB (KiCad) | ✅ | ❌ |
| Digital IC (Yosys) | ✅ | ✅ |
| SPICE simulation | Planned Phase 2 | ❌ |
| Visual feedback loop | Planned Phase 3 | ❌ |
| Multi-tool orchestration | ✅ | ❌ |
| Language | Python | TypeScript |

## Contributing

Contributions welcome. See [`analysis/PLAN4_community_ops.md`](analysis/PLAN4_community_ops.md) for community plans.

```bash
# Development setup
uv sync --extra dev
ruff check src/        # lint
mypy src/              # type check
pytest tests/ -v       # test
```

## License

MIT
