# EDA工具部署和生产化方案调研报告

**调研日期**: 2026-03-14  
**调研范围**: 开源EDA工具Docker化、跨平台支持、MCP服务器分发、CI/CD集成、PDK管理、许可证  
**状态**: 完成

---

## 1. EDA工具Docker镜像现状表

### 1.1 主要镜像仓库一览

| 镜像来源 | Registry | 维护状态 | 主要包含工具 | 适用场景 |
|---------|---------|---------|-----------|--------|
| efabless/OpenLane2 | `ghcr.io/efabless/openlane2` | 活跃 | OpenROAD, Yosys, Magic, Netgen, KLayout, OpenSTA | ASIC完整流程 |
| OpenROAD官方 | `openroad/flow-ubuntu22.04-*` | 活跃 | OpenROAD, Yosys, ABC, OpenSTA | 物理设计 |
| YosysHQ OSS-CAD-Suite | `yosyshq/oss-cad-suite` | 活跃 | Yosys, nextpnr, icestorm, iverilog, cocotb | FPGA+RTL仿真 |
| hdl/containers | `ghcr.io/hdl/*` | 活跃 | 模块化单工具镜像 | CI/CD |
| IIC-OSIC-TOOLS | `hpretl/iic-osic-tools` | 活跃 | 完整模拟/数字套件+PDK | 教学/研究 |
| LibreLane | `ghcr.io/librelane/librelane` | 最新 | OpenROAD, Yosys, KLayout等 | ASIC (OpenLane2继任) |

### 1.2 关键镜像详情

#### efabless/OpenLane2
```bash
docker pull ghcr.io/efabless/openlane2:latest
docker pull ghcr.io/efabless/openlane2:2.2.8

# 使用方式 (--dockerized 紧跟 openlane)
openlane --dockerized /work/config.json

# 镜像大小: ~8-12 GB
# 包含: OpenROAD, Yosys, KLayout, Magic, Netgen, Verilator, OpenSTA
# 许可: Apache 2.0 (镜像层), 各工具各自许可
# 注: 开发已迁移至 github.com/librelane/librelane
```

#### OpenROAD-flow-scripts官方镜像
```bash
docker pull openroad/flow-ubuntu22.04-builder:latest
docker pull openroad/flow-ubuntu22.04-dev:latest

# GitHub Actions中使用
# jobs:
#   build:
#     container: openroad/flow-ubuntu22.04-builder:latest
# 仓库: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
```

#### YosysHQ OSS-CAD-Suite
```bash
docker pull yosyshq/oss-cad-suite:latest

# 也提供预编译二进制 (非Docker)
# https://github.com/YosysHQ/oss-cad-suite-build/releases
# 支持: Linux x86_64, macOS x86_64/arm64, Windows x64
# 包含: yosys, nextpnr-*, icestorm, trellis, iverilog,
#       ghdl, cocotb, verilator, openFPGALoader
```

#### hdl/containers (模块化)
```bash
# 三个Registry镜像
# gcr.io/hdl-containers/  (主)
# ghcr.io/hdl/            (GitHub)
# hub.docker.com/u/hdlc   (DockerHub)

# 基础OS: debian-bookworm, debian-bullseye, rockylinux-8
docker pull ghcr.io/hdl/debian-bookworm/yosys
docker pull ghcr.io/hdl/debian-bookworm/ghdl
docker pull ghcr.io/hdl/debian-bookworm/verilator
docker pull ghcr.io/hdl/debian-bookworm/cocotb

# 工具完整列表: https://hdl.github.io/containers/ToolsAndImages.html
# 精细化使用: https://hdl.github.io/containers/ug/FineGrained.html
```

#### IIC-OSIC-TOOLS (模拟+数字全套)
```bash
docker pull hpretl/iic-osic-tools:latest
# 包含: Magic, Netgen, Xschem, ngspice, OpenROAD, KLayout,
#       sky130A PDK, gf180mcuC PDK
# 镜像大小: ~15-20 GB
# 适合: 模拟IC教学, 全流程验证
```

---

## 2. 跨平台支持矩阵

### 2.1 平台支持概览

| 工具/套件 | Linux x86_64 | Linux aarch64 | macOS x86_64 | macOS arm64 | Windows 原生 | Windows WSL2 | Windows Docker |
|---------|:-----------:|:-------------:|:-----------:|:-----------:|:-----------:|:-----------:|:--------------:|
| OpenROAD | 完整支持 | 部分支持 | 需编译 | 需编译 | 不支持 | 完整支持 | 完整支持 |
| Yosys | 完整支持 | 完整支持 | 完整支持 | 完整支持 | 部分支持 | 完整支持 | 完整支持 |
| KLayout | 完整支持 | 完整支持 | 完整支持 | 完整支持 | 完整支持 | 完整支持 | 完整支持 |
| OpenLane2 | 完整支持 | 完整支持 | Docker/Nix | Docker/Nix | Docker | WSL2 | 完整支持 |
| Magic | 完整支持 | 完整支持 | 需Xquartz | 需Xquartz | 不支持 | 完整支持 | 完整支持 |
| Verilator | 完整支持 | 完整支持 | 完整支持 | 完整支持 | MSYS2 | 完整支持 | 完整支持 |
| iverilog | 完整支持 | 完整支持 | 完整支持 | 完整支持 | MSYS2 | 完整支持 | 完整支持 |
| ngspice | 完整支持 | 完整支持 | 完整支持 | 部分支持 | 需编译 | 完整支持 | 完整支持 |

### 2.2 Windows 部署方案 (WSL2)

Windows用户最推荐的方案是WSL2+Docker Desktop：

```powershell
# 步骤1: 启用WSL2
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2

# 步骤2: 安装Docker Desktop (启用WSL2 Backend)
# https://docs.docker.com/desktop/install/windows-install/
# 设置: Settings > Resources > WSL Integration > 启用Ubuntu-22.04

# 步骤3: 在WSL2内使用OpenLane2
wsl -d Ubuntu-22.04
pip install openlane
openlane --dockerized config.json
```

**WSL2方案优势**:
- Docker Desktop for Windows 自动提供WSL2集成
- 文件系统性能接近原生Linux (`/home`目录)
- GUI工具通过WSLg支持 (Windows 11)
- 网络与Windows完全共享

**已知限制**:
- `/mnt/c/` 路径下I/O性能较差，PDK应存放在 `~/` 下
- Magic/Xschem等X11工具需WSLg (Windows 11) 或VcXsrv
- 大镜像拉取需较大磁盘空间 (~20-40 GB)

### 2.3 macOS 部署方案

```bash
# 方案A: Nix (推荐, OpenLane2官方推荐)
brew install nix
nix-env -i openlane

# 方案B: Docker Desktop for Mac
brew install --cask docker
pip install openlane
openlane --dockerized config.json

# 方案C: OSS-CAD-Suite 预编译二进制
# 下载 oss-cad-suite-darwin-arm64-*.tgz
# https://github.com/YosysHQ/oss-cad-suite-build/releases
source ./oss-cad-suite/environment
```

**Apple Silicon (arm64) 注意事项**:
- Docker Desktop支持arm64原生镜像
- OpenLane2的Docker镜像支持aarch64
- 部分旧镜像仅x86_64，需通过Rosetta模拟
- OSS-CAD-Suite提供原生arm64二进制

---

## 3. MCP服务器分发方案对比

### 3.1 分发方案全景

| 方案 | 安装方式 | 零安装 | 版本管理 | 隔离性 | 适用场景 |
|-----|---------|:-----:|:-------:|:-----:|--------|
| uvx (推荐) | `uvx eda-mcp-server` | 是 | pip版本号 | 独立venv | 终端用户 |
| npx | `npx eda-mcp` | 是 | npm版本 | node_modules | JS生态 |
| pipx | `pipx run eda-mcp-server` | 是 | pip版本号 | 独立venv | Python用户 |
| pip install | `pip install eda-mcp-server` | 否 | pip版本 | 无 | 开发者 |
| Docker | `docker run eda-mcp-server` | 否 | image tag | 完整容器 | 服务端部署 |
| conda | `conda install eda-mcp-server` | 否 | conda版本 | conda env | 科学计算用户 |

### 3.2 uvx零安装方案 (推荐)

`uvx` 是uv项目提供的零安装运行工具，等效Python版的`npx`：

```bash
# 无需预先安装，直接运行
uvx eda-mcp-server

# 指定版本
uvx eda-mcp-server@1.2.0

# 始终使用最新版
uvx eda-mcp-server@latest

# 带额外依赖
uvx --with klayout eda-mcp-server
```

**Claude Desktop / Cursor配置 (mcp.json)**:
```json
{
  "mcpServers": {
    "eda-tools": {
      "command": "uvx",
      "args": ["eda-mcp-server"],
      "env": {
        "PDK_ROOT": "/home/user/.volare",
        "PDK": "sky130A"
      }
    }
  }
}
```

**uvx工作原理**:
1. 首次调用时从PyPI下载包到临时隔离venv
2. 后续调用使用缓存（除非`@latest`）
3. 不污染系统Python环境
4. `uv tool install` 可将其持久化到PATH

### 3.3 PyPI发布最佳实践

```toml
# pyproject.toml 关键配置
[project]
name = "eda-mcp-server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0",
]

[project.scripts]
eda-mcp-server = "eda_mcp_server:main"

[project.optional-dependencies]
klayout = ["klayout>=0.28"]
full = ["klayout>=0.28", "pyspice"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```bash
# 发布流程
pip install build twine
python -m build
twine upload dist/*

# 或使用uv
uv build
uv publish
```

**发布注意事项**:
- 在`[project.scripts]`中定义console_scripts入口点，供uvx/pipx发现
- EDA工具二进制不打包入wheel，通过`env`变量指向外部安装
- 版本遵循语义化版本(semver)
- 在PyPI description中注明EDA工具前置依赖

### 3.4 MCP传输协议选择

根据MCP官方规范（2025-06-18版）：

| 传输方式 | 适用场景 | 启动方式 |
|---------|---------|--------|
| stdio (推荐) | 本地工具集成，uvx/pipx运行 | Claude/Cursor直接启动子进程 |
| Streamable HTTP | 远程服务，多客户端连接 | 独立服务进程，支持SSE流 |
| 自定义传输 | 特殊需求 | 实现JSON-RPC双向通道 |

**AUTO_EDA推荐**: stdio传输 + PyPI分发 + uvx零安装

---

## 4. CI/CD集成方案

### 4.1 GitHub Actions中使用EDA工具

#### 方案A: Docker容器直接运行
```yaml
# .github/workflows/eda-ci.yml
name: EDA CI Pipeline
on: [push, pull_request]

jobs:
  rtl-lint:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/hdl/debian-bookworm/verilator:latest
    steps:
      - uses: actions/checkout@v4
      - name: Verilator Lint
        run: verilator --lint-only -Wall src/*.v

  synthesis:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/hdl/debian-bookworm/yosys:latest
    steps:
      - uses: actions/checkout@v4
      - name: Yosys Synthesis
        run: yosys -p "synth_xilinx -top top" src/top.v

  openlane-flow:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install OpenLane2
        run: pip install openlane
      - name: Run OpenLane Flow (Dockerized)
        run: openlane --dockerized config.json
        env:
          PDK_ROOT: ${{ github.workspace }}/.volare
          PDK: sky130A
```

#### 方案B: efabless/openlane-action
```yaml
# Efabless官方提供的GitHub Action
jobs:
  openlane:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: efabless/openlane-action@v1
        with:
          config_file: config.json
          pdk: sky130A
          pdk_root: /home/runner/pdk
```

#### 方案C: Caravel用户项目标准流水线
```yaml
# efabless/caravel_user_project 标准CI
jobs:
  caravel-ci:
    runs-on: ubuntu-22.04
    container:
      image: efabless/openlane:latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      - name: Run OpenLane
        run: make user_project_wrapper
      - name: DRC Check
        run: make drc
      - name: LVS Check
        run: make lvs
      - name: Upload GDS
        uses: actions/upload-artifact@v4
        with:
          name: gds
          path: gds/*.gds
```

### 4.2 EDA CI/CD最佳实践

| 阶段 | 工具 | 触发条件 | 耗时估算 |
|-----|-----|---------|--------|
| RTL Lint | Verilator | 每次push | <1分钟 |
| 功能仿真 | cocotb/iverilog | 每次push | 1-10分钟 |
| RTL综合 | Yosys | PR | 5-30分钟 |
| 完整P&R | OpenROAD | 合并main | 1-8小时 |
| DRC/LVS | Magic/Netgen | Release | 30分钟-2小时 |
| GDS导出 | KLayout | Release | 10-30分钟 |

**GitHub Actions限制注意**:
- 免费tier: 2000分钟/月，完整ASIC流程耗时较长
- 大型PDK文件(>1GB)需使用缓存或外部存储
- 推荐使用`actions/cache`缓存PDK和工具层

```yaml
# PDK缓存示例
- name: Cache PDK
  uses: actions/cache@v4
  with:
    path: ~/.volare
    key: pdk-sky130-${{ hashFiles('**/config.json') }}
```

---

## 5. PDK自动安装

### 5.1 volare — PDK版本管理工具 (推荐)

`volare` 是efabless开发的PDK版本管理器，类似PDK的`nvm`：

```bash
# 安装volare
pip install volare

# SkyWater SKY130 PDK
export PDK_ROOT=~/.volare
volare fetch --pdk sky130          # 下载最新版
volare enable --pdk sky130 <hash>  # 启用特定版本

# GlobalFoundries GF180MCU PDK
volare fetch --pdk gf180mcu
volare enable --pdk gf180mcu <hash>

# 查看可用版本
volare ls-remote --pdk sky130
volare ls-remote --pdk gf180mcu

# 环境变量设置
export PDK=sky130A        # 或 sky130B, gf180mcuC, gf180mcuD
export PDK_ROOT=~/.volare
```

### 5.2 conda-forge EDA包

| conda包 | 工具 | 状态 | 安装命令 |
|--------|-----|-----|--------|
| `yosys` | RTL综合 | 稳定 | `conda install -c conda-forge yosys` |
| `klayout` | 版图工具 | 稳定 | `conda install -c conda-forge klayout` |
| `verilator` | HDL仿真 | 稳定 | `conda install -c conda-forge verilator` |
| `iverilog` | Verilog仿真 | 稳定 | `conda install -c conda-forge iverilog` |
| `open_pdks.sky130a` | SKY130 PDK | 稳定 | `conda install -c conda-forge open_pdks.sky130a` |
| `ngspice` | SPICE仿真 | 稳定 | `conda install -c conda-forge ngspice` |
| `magic` | DRC/PEX | 可用 | `conda install -c litex-hub magic` |
| `openroad` | 物理设计 | 不在CF | 使用Docker/volare |

**OpenROAD不在conda-forge**，推荐通过OpenLane2 Docker或从源码编译。

```bash
# SKY130 完整conda环境
conda create -n sky130-env -c conda-forge \
  yosys klayout verilator iverilog ngspice \
  open_pdks.sky130a
conda activate sky130-env

# 验证安装
yosys --version
klayout -v
verilator --version
```

### 5.3 PDK支持矩阵

| PDK | 工艺节点 | 安装方式 | 开放性 | 适用流程 |
|-----|---------|---------|-------|--------|
| SKY130A | 130nm | volare / conda / git | 完全开源 | 数字/模拟/混合 |
| SKY130B | 130nm | volare / conda | 完全开源 | 含SRAM编译器 |
| GF180MCU-C | 180nm | volare / git | 完全开源 | 数字CMOS |
| GF180MCU-D | 180nm | volare | 完全开源 | 含高压 |
| IHPSG13G2 | 130nm BiCMOS | git / Docker | 完全开源 | 模拟RF |
| ASAP7 | 7nm预测 | git | 学术开源 | 研究/教学 |

---

## 6. 工具许可证管理

### 6.1 开源EDA工具许可证汇总

| 工具 | 许可证 | 商业使用 | 专利保护 | 注意事项 |
|-----|--------|---------|---------|--------|
| Yosys | ISC (MIT-like) | 允许 | 无 | 完全自由使用 |
| OpenROAD | BSD 3-Clause | 允许 | 无 | 需保留版权声明 |
| KLayout | GPL v2 + KLayout Exception | 允许 | 无 | Exception允许商业工具链使用不传染GPL |
| Magic | MIT | 允许 | 无 | 完全自由使用 |
| Netgen | GPL v3 | 有限制 | 无 | 独立工具运行，不影响工具链 |
| Verilator | LGPL v3 | 允许 | 无 | 生成代码无GPL感染 |
| iverilog | GPL v2 | 有限制 | 无 | 作为外部进程调用安全 |
| cocotb | BSD 3-Clause | 允许 | 无 | 完全自由 |
| ngspice | BSD-like | 允许 | 无 | 含部分BSIM BSD代码 |
| OpenSTA | GPL v3 | 有限制 | 无 | 作为外部进程调用安全 |
| OpenLane2 | Apache 2.0 | 允许 | 专利授权 | 最友好，含专利保护 |

### 6.2 AUTO_EDA许可证策略建议

**MCP服务器本身**: 建议Apache 2.0
- 兼容所有上游工具许可
- 提供专利保护
- 商业友好，利于采用
- 与OpenLane2保持一致

**GPL工具的安全使用方式**:
```
# 安全模式：通过subprocess/CLI调用，不链接库
subprocess.run(["iverilog", "-o", "out", "src.v"])

# 不安全模式：直接Python绑定到GPL库
import iverilog  # 假设存在，会触发GPL传染
```

**KLayout Exception解读**:
KLayout特有例外允许在商业EDA工具链中使用KLayout，即使工具链本身非GPL，只要不修改KLayout源码并以独立进程运行。AUTO_EDA通过`pya` Python API调用时，应作为独立进程运行。

---

## 7. AUTO_EDA部署架构建议

### 7.1 推荐部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户层 (Claude / Cursor)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP stdio 传输
┌────────────────────────▼────────────────────────────────────┐
│              AUTO_EDA MCP Server (Python)                     │
│         安装方式: uvx auto-eda-mcp  /  pip install           │
│         传输: stdio (本地) | Streamable HTTP (远程)           │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  PCB模块     │  │ 数字IC模块   │  │  模拟仿真模块     │   │
│  │  KiCad IPC  │  │ Yosys/OR    │  │  ngspice/PySpice │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ subprocess / Python API
┌────────────────────────▼────────────────────────────────────┐
│                  EDA工具层                                     │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ OSS-CAD-Suite│  │ OpenLane2  │  │  KiCad (Native/WSL) │  │
│  │ (二进制)    │  │ (Docker)   │  │                     │  │  
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   PDK层                                       │
│   volare管理: ~/.volare/sky130A, ~/.volare/gf180mcuC          │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 三阶段部署路线

#### Phase 0: 开发者本地环境 (当前阶段)

```bash
# 目标用户: 贡献者、高级用户
# 前置要求: Python 3.10+, Docker Desktop

# 1. 安装MCP服务器 (开发模式)
git clone https://github.com/auto-eda/auto-eda-mcp
cd auto-eda-mcp
pip install -e ".[dev]"

# 2. 安装EDA工具 (选择一种)
## 选项A: OSS-CAD-Suite (FPGA/RTL)
curl -L https://github.com/YosysHQ/oss-cad-suite-build/releases/latest/download/oss-cad-suite-linux-x64.tgz | tar xz
source ./oss-cad-suite/environment

## 选项B: OpenLane2 (ASIC完整流程)
pip install openlane

# 3. 安装PDK
pip install volare
volare enable --pdk sky130

# 4. 配置Claude Desktop
# ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "auto-eda": {
      "command": "python",
      "args": ["-m", "auto_eda_mcp"],
      "env": {
        "PDK_ROOT": "~/.volare",
        "PDK": "sky130A"
      }
    }
  }
}
```

#### Phase 1: PyPI发布 (uvx零安装)

```bash
# 目标用户: 普通用户
# 前置要求: Python 3.10+, uv, Docker Desktop

# 用户只需一条命令配置
# mcp.json:
{
  "mcpServers": {
    "auto-eda": {
      "command": "uvx",
      "args": ["auto-eda-mcp"],
      "env": {
        "PDK_ROOT": "${env:HOME}/.volare",
        "EDA_BACKEND": "docker"  # 自动使用Docker后端
      }
    }
  }
}

# MCP服务器首次运行时自动:
# 1. 检测可用EDA工具 (PATH中或Docker)
# 2. 提示安装缺失依赖
# 3. 通过volare拉取PDK
```

#### Phase 2: 云端部署 (远程MCP)

```yaml
# docker-compose.yml (云端部署)
version: '3.8'
services:
  auto-eda-mcp:
    image: ghcr.io/auto-eda/auto-eda-mcp:latest
    ports:
      - "8080:8080"   # Streamable HTTP
    environment:
      - PDK_ROOT=/pdk
      - PDK=sky130A
      - AUTH_TOKEN=${AUTH_TOKEN}
    volumes:
      - pdk-data:/pdk
      - work-data:/work

  pdk-init:
    image: ghcr.io/auto-eda/auto-eda-mcp:latest
    command: volare enable --pdk sky130
    volumes:
      - pdk-data:/pdk
    environment:
      - PDK_ROOT=/pdk

volumes:
  pdk-data:
  work-data:
```

### 7.3 Windows用户快速上手方案

```powershell
# Windows用户最优路径:

# 步骤1: 安装WSL2 + Docker Desktop
wsl --install
# 安装Docker Desktop并启用WSL2 backend

# 步骤2: 安装uv (Windows原生)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 步骤3: 配置mcp.json (uvx在Windows原生运行,
# uvx会自动处理跨WSL2边界的EDA工具调用)
```

**Windows架构说明**:
- MCP服务器: Windows原生 Python (via uvx)
- EDA工具: Docker容器 (通过Docker Desktop WSL2 backend)
- PDK存储: WSL2文件系统 `\wsl$\Ubuntu\home\user\.volare`
- 文件交换: 通过挂载卷共享工作目录

### 7.4 AUTO_EDA Dockerfile参考

```dockerfile
# AUTO_EDA MCP服务器Docker镜像
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl git \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 安装MCP服务器
RUN pip install auto-eda-mcp[full]

# 安装volare和PDK (可选, 也可挂载外部PDK)
RUN pip install volare

# MCP stdio传输
ENTRYPOINT ["python", "-m", "auto_eda_mcp"]

# 或Streamable HTTP模式
# ENTRYPOINT ["python", "-m", "auto_eda_mcp", "--transport", "http", "--port", "8080"]
EXPOSE 8080
```

---

## 8. 关键决策建议

### 8.1 EDA工具集成优先级

| 优先级 | 工具 | 集成方式 | 理由 |
|-------|-----|---------|-----|
| P0 | KiCad | IPC API (进程内) | PCB市场最大, API最成熟 |
| P0 | Yosys | pyosys (进程内) | RTL综合核心, Python绑定完善 |
| P1 | KLayout | pya API (进程内) | 版图查看/DRC, Python API强 |
| P1 | Verilator | subprocess | 仿真最快, 使用广泛 |
| P1 | OpenROAD | Python bindings | P&R核心, 但环境复杂 |
| P2 | cocotb | 原生Python | 验证框架, 直接集成 |
| P2 | ngspice | subprocess | 模拟仿真, PySpice封装 |
| P3 | Magic | subprocess | DRC/PEX, GUI依赖重 |

### 8.2 核心架构决策

1. **传输协议**: stdio优先 (本地uvx), HTTP作为云端扩展
2. **工具隔离**: 核心工具进程内调用(性能好), 复杂工具subprocess(隔离好)
3. **PDK管理**: volare为标准, conda-forge为备选
4. **分发方式**: PyPI + uvx为主渠道, Docker为企业/云端选项
5. **Windows支持**: 通过Docker Desktop + WSL2实现, 不做Windows原生EDA集成
6. **许可证**: Apache 2.0, 所有EDA工具以subprocess方式调用避免GPL感染

### 8.3 与现有研究的关联

| 本报告主题 | 对应已有研究 | 新增信息 |
|-----------|------------|--------|
| Docker镜像 | R2 (开源工具) | hdl/containers模块化方案, LibreLane新动态 |
| 跨平台支持 | R2, R4 | WSL2具体步骤, macOS arm64细节 |
| MCP分发 | R5 (MCP架构) | uvx零安装具体配置, PyPI发布规范 |
| CI/CD | R9 (工作流) | GitHub Actions具体YAML, efabless Action |
| PDK管理 | R2 | volare工具详情, conda-forge包名确认 |
| 许可证 | R4 (现有MCP) | KLayout Exception详解, GPL调用安全边界 |

---

## 参考资源

- efabless OpenLane2: https://github.com/efabless/openlane2
- LibreLane (OpenLane2继任): https://github.com/librelane/librelane
- OpenROAD-flow-scripts: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
- hdl/containers: https://github.com/hdl/containers | https://hdl.github.io/containers/
- YosysHQ OSS-CAD-Suite: https://github.com/YosysHQ/oss-cad-suite-build
- IIC-OSIC-TOOLS: https://github.com/iic-jku/iic-osic-tools
- volare PDK管理: https://github.com/efabless/volare
- SKY130 PDK: https://github.com/google/skywater-pdk
- GF180MCU PDK: https://github.com/google/gf180mcu-pdk
- conda-forge yosys: https://anaconda.org/conda-forge/yosys
- conda-forge klayout: https://anaconda.org/conda-forge/klayout
- MCP传输规范: https://modelcontextprotocol.io/docs/concepts/transports
- uv/uvx文档: https://docs.astral.sh/uv/guides/tools/
