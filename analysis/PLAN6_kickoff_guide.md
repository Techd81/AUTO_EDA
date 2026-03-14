# PLAN6: AUTO_EDA 项目启动手册 (Day 1 可执行版)

> 文档版本: 0.1.0
> 生成日期: 2026-03-14
> 数据来源: DA3_phase0_implementation_spec · DA1_architecture_deep_design · A7_tech_stack_decision · DA4_risk_mitigation_deep
> 定位: 开发者入手即用的操作手册，无需阅读其他分析文档

---

## 目录

1. [开发环境搭建步骤](#1-开发环境搭建步骤)
2. [项目脚手架创建命令序列](#2-项目脚手架创建命令序列)
3. [第一个可运行的 MCP Server](#3-第一个可运行的-mcp-server)
4. [Week 1 详细任务清单](#4-week-1-详细任务清单)
5. [开发规范速查卡](#5-开发规范速查卡)
6. [常见问题预案](#6-常见问题预案)

---

## 1. 开发环境搭建步骤

### 1.1 前置条件确认

开始前确认以下环境（Windows 开发者使用 WSL2，Linux/macOS 直接操作）：

```bash
# 确认 WSL2 已启用（Windows 用户）
wsl --version
# 建议: Ubuntu 22.04 LTS
wsl --install -d Ubuntu-22.04

# 进入 WSL2 环境（后续所有命令均在 WSL2 内执行）
wsl
```

### 1.2 Python 环境（uv）

uv 是 Rust 实现的 Python 包管理器，速度比 pip 快 10-100x，是本项目的包管理器。

```bash
# Step 1: 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # 或 source ~/.zshrc

# 验证
uv --version
# 期望输出: uv 0.x.x

# Step 2: 安装 Python 3.11（推荐版本，EDA 库兼容性最佳）
uv python install 3.11
uv python pin 3.11

# 验证
python --version
# 期望输出: Python 3.11.x
```

### 1.3 EDA 工具安装（WSL2/Linux）

#### Yosys（综合工具，Phase 0 第一优先级）

```bash
# 方法 A: apt 安装（快速，推荐先用这个验证环境）
sudo apt update
sudo apt install -y yosys

# 验证
yosys --version
# 期望输出: Yosys 0.x.x (git sha1 ...)

# 方法 B: OSS CAD Suite（包含完整工具链，推荐 CI/生产环境）
# 下载地址: https://github.com/YosysHQ/oss-cad-suite-build/releases
# 选择最新 linux-x64 版本
wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-03-01/oss-cad-suite-linux-x64-20260301.tgz
tar xzf oss-cad-suite-linux-x64-*.tgz
echo 'source ~/oss-cad-suite/environment' >> ~/.bashrc
source ~/.bashrc
```

#### KiCad（PCB 工具，Phase 0 第二优先级）

```bash
# KiCad v10（推荐，IPC API 最完整）
sudo add-apt-repository ppa:kicad/kicad-10.0-releases
sudo apt update
sudo apt install -y kicad

# 验证 CLI
kicad-cli --version
# 期望输出: 10.x.x

# 注意: KiCad GUI 在 WSL2 中需要 X11/Wayland 转发
# 对于 IPC API 模式，KiCad GUI 必须在 Windows 本机运行
# CLI 模式（DRC/导出）不需要 GUI，WSL2 中直接可用
```

#### Verilator（仿真工具，可选）

```bash
sudo apt install -y verilator
verilator --version
```

### 1.4 代码质量工具配置

所有代码质量工具通过项目 `pyproject.toml` 驱动，无需全局安装。但 pre-commit 需要系统级安装：

```bash
# pre-commit（Git 钩子管理）
pip install pre-commit   # 或 uv tool install pre-commit
pre-commit --version
```

### 1.5 IDE 配置（VS Code / Cursor）

#### 推荐扩展（.vscode/extensions.json 内容）

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.mypy-type-checker",
    "charliermarsh.ruff",
    "ms-vscode-remote.remote-wsl",
    "tamasfe.even-better-toml"
  ]
}
```

#### 工作区设置（.vscode/settings.json 内容）

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "mypy-type-checker.args": ["--config-file=pyproject.toml"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".venv": true
  }
}
```

### 1.6 .mcp.json 初始配置

此文件告知 Claude Code 如何启动本项目的 MCP Server（放在项目根目录）：

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "uv",
      "args": ["run", "auto-eda-yosys"],
      "cwd": ".",
      "description": "Yosys MCP Server for RTL synthesis and analysis"
    },
    "auto-eda-kicad": {
      "command": "uv",
      "args": ["run", "auto-eda-kicad"],
      "cwd": ".",
      "description": "KiCad MCP Server for PCB design automation"
    },
    "auto-eda-verilog": {
      "command": "uv",
      "args": ["run", "auto-eda-verilog"],
      "cwd": ".",
      "description": "Verilog utilities MCP Server (lint, parse, format)"
    }
  }
}
```

---

## 2. 项目脚手架创建命令序列

以下命令序列可以复制粘贴整块执行，从零创建完整项目结构。

### 2.1 目录结构创建

```bash
# 在 WSL2 中执行（Windows 路径映射为 /mnt/d/AUTO_EDA/）
cd /mnt/d/AUTO_EDA   # 或任意工作目录

# 创建项目根目录
mkdir -p auto-eda && cd auto-eda

# 创建完整目录树
mkdir -p src/auto_eda/core
mkdir -p src/auto_eda/models
mkdir -p src/auto_eda/servers/yosys
mkdir -p src/auto_eda/servers/kicad
mkdir -p src/auto_eda/servers/verilog_utils
mkdir -p tests/fixtures/verilog
mkdir -p tests/fixtures/kicad/blinky
mkdir -p tests/fixtures/yosys
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/mcp
mkdir -p .github/workflows
mkdir -p scripts
mkdir -p .vscode

# 创建所有 __init__.py 文件
touch src/auto_eda/__init__.py
touch src/auto_eda/__main__.py
touch src/auto_eda/core/__init__.py
touch src/auto_eda/models/__init__.py
touch src/auto_eda/servers/__init__.py
touch src/auto_eda/servers/yosys/__init__.py
touch src/auto_eda/servers/kicad/__init__.py
touch src/auto_eda/servers/verilog_utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/mcp/__init__.py
touch tests/conftest.py

# 验证结构
find . -type f -name '*.py' | sort
```

### 2.2 pyproject.toml 完整内容

```bash
cat > pyproject.toml << 'TOML_EOF'
[build-system]
requires = ["hatchling>=1.21"]
build-backend = "hatchling.build"

[project]
name = "auto-eda"
version = "0.1.0"
description = "MCP servers for open-source EDA tools (Yosys, KiCad, Verilator, OpenROAD and more)"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
keywords = ["mcp", "eda", "yosys", "kicad", "verilog", "hdl", "fpga", "asic"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
]

# Layer 1: MCP 协议层 + 最小运行时（必须）
dependencies = [
    "mcp[cli]>=1.3.0",
    "pydantic>=2.6.0",
    "anyio>=4.3.0",
    "psutil>=5.9.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
pcb = [
    "kikit>=1.3.0",
    "sexpdata>=1.0.0",
]
ic = [
    "pyverilog>=1.3.0",
    "gdstk>=0.9.0",
]
full = [
    "auto-eda[pcb]",
    "auto-eda[ic]",
]
dev = [
    "auto-eda[full]",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-timeout>=2.3.0",
    "mypy>=1.9.0",
    "ruff>=0.3.0",
    "pre-commit>=3.7.0",
    "types-psutil",
]

[project.scripts]
auto-eda-yosys   = "auto_eda.servers.yosys:main"
auto-eda-kicad   = "auto_eda.servers.kicad:main"
auto-eda-verilog = "auto_eda.servers.verilog_utils:main"
auto-eda         = "auto_eda.__main__:main"

[project.urls]
Homepage   = "https://github.com/auto-eda/auto-eda"
Repository = "https://github.com/auto-eda/auto-eda"

[tool.hatch.build.targets.wheel]
packages = ["src/auto_eda"]

[tool.hatch.build.targets.sdist]
exclude = ["/.github", "/tests", "/scripts", "*.pyc", "__pycache__"]

[tool.ruff]
target-version = "py310"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ANN", "SIM", "TCH"]
ignore = ["ANN101", "ANN102", "E501"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_reexport = true

[[tool.mypy.overrides]]
module = ["pyverilog.*", "gdstk.*", "kikit.*", "sexpdata.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
timeout = 120
markers = [
    "unit: 纯逻辑单元测试，无需 EDA 工具",
    "integration: 需要 EDA 工具已安装",
    "slow: 运行时间超过 30s 的测试",
    "mcp: MCP 协议合规性测试",
]
addopts = ["--strict-markers", "-ra", "--tb=short"]

[tool.coverage.run]
source = ["src/auto_eda"]
omit = ["*/tests/*", "*/__main__.py"]
branch = true

[tool.coverage.report]
fail_under = 80
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "raise NotImplementedError"]
TOML_EOF
```

### 2.3 虚拟环境创建与依赖安装

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装开发依赖（首次，含所有可选依赖）
uv pip install -e ".[dev]"

# 验证安装
python -c "import mcp; import pydantic; print('MCP layer OK')"
python -c "import pyverilog; print('pyverilog OK')"

# 若 gdstk 安装失败（需要 C++ 编译环境）
sudo apt install -y build-essential cmake libglib2.0-dev
uv pip install gdstk
```

### 2.4 Git 初始化与 .gitignore

```bash
git init
git checkout -b main
```

将以下内容保存为 `.gitignore`：

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
*.vcd
*.fst
*.vvp
synthesis_output/
simulation_output/
work/
.vscode/settings.json
.idea/
*.swp
.DS_Store
Thumbs.db
/oss-cad-suite/
*.log
```

```bash
git add pyproject.toml .gitignore
git commit -m "chore: project scaffold"
```

### 2.5 pre-commit 初始配置

将以下内容保存为 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.6.0
          - types-psutil
        args: [--config-file=pyproject.toml]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
```

```bash
pre-commit install
# 首次全量检查（CI 绿灯前不强制）
pre-commit run --all-files
```

---

## 3. 第一个可运行的 MCP Server

这是一个**最简 Yosys MCP Server**，可直接复制运行，用于验证整个工具链端到端打通。

### 3.1 最小可运行代码

**第一步**：将以下内容保存为 `src/auto_eda/core/errors.py`：

```python
from __future__ import annotations
from enum import IntEnum


class EDAErrorCode(IntEnum):
    UNKNOWN              = 1000
    INVALID_INPUT        = 1001
    FILE_NOT_FOUND       = 1002
    TIMEOUT              = 1005
    TOOL_NOT_FOUND       = 2001
    TOOL_VERSION_MISMATCH = 2002
    YOSYS_SYNTHESIS_FAIL = 3001
    YOSYS_PARSE_ERROR    = 3002
    YOSYS_NO_TOP_MODULE  = 3004
    KICAD_IPC_CONN_FAIL  = 4001
    KICAD_NOT_RUNNING    = 4006
    VERILOG_SYNTAX_ERROR = 5001


class EDAError(Exception):
    def __init__(
        self,
        code: EDAErrorCode,
        message: str,
        detail: str | None = None,
        tool_output: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        self.tool_output = tool_output
        super().__init__(message)

    def to_mcp_error_text(self) -> str:
        lines = [f"[ERROR {self.code.value}] {self.message}"]
        if self.detail:
            lines.append(f"Detail: {self.detail}")
        if self.tool_output:
            lines.append(f"Tool output:\n{self.tool_output[:2000]}")
        return "\n".join(lines)


class ToolNotFoundError(EDAError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(
            EDAErrorCode.TOOL_NOT_FOUND,
            f"EDA tool '{tool_name}' not found in PATH",
            detail=f"Install {tool_name} and ensure it is accessible from PATH",
        )


class ToolTimeoutError(EDAError):
    def __init__(self, tool_name: str, timeout_s: int) -> None:
        super().__init__(
            EDAErrorCode.TIMEOUT,
            f"'{tool_name}' timed out after {timeout_s}s",
        )
```

**第二步**：将以下内容保存为 `src/auto_eda/servers/yosys/server.py`：

```python
"""
Yosys MCP Server - Hello World 最简版本
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from auto_eda.core.errors import ToolNotFoundError, ToolTimeoutError

mcp = FastMCP("auto-eda-yosys", version="0.1.0")

try:
    import pyosys  # type: ignore[import-not-found]
    _BACKEND = "pyosys"
except ImportError:
    _BACKEND = "yosys-cli" if shutil.which("yosys") else "unavailable"


@mcp.tool(description="检查 Yosys Server 状态和工具可用性")
def yosys_health_check() -> dict[str, object]:
    yosys_version: str | None = None
    if _BACKEND == "yosys-cli":
        try:
            r = subprocess.run(
                ["yosys", "--version"], capture_output=True, text=True, timeout=5
            )
            yosys_version = r.stdout.strip() or r.stderr.strip()
        except Exception:
            pass
    return {
        "server": "auto-eda-yosys",
        "version": "0.1.0",
        "backend": _BACKEND,
        "yosys_version": yosys_version,
        "status": "ok" if _BACKEND != "unavailable" else "degraded",
        "message": (
            "Yosys ready"
            if _BACKEND != "unavailable"
            else "Yosys not found — install yosys to enable synthesis"
        ),
    }


@mcp.tool(description="综合 Verilog RTL 代码，生成网表和统计信息")
async def synthesize_rtl(
    verilog_files: list[str],
    top_module: str,
    target: str = "generic",
    timeout_s: int = 300,
) -> str:
    """
    参数:
        verilog_files: Verilog 源文件路径列表
        top_module: 顶层模块名称
        target: 综合目标，"generic" 或 "ice40"
        timeout_s: 超时秒数
    """
    if _BACKEND == "unavailable":
        raise ToolNotFoundError("yosys")
    for f in verilog_files:
        if not Path(f).exists():
            return f"[ERROR 1002] File not found: {f}"
    read_cmds = "\n".join(f"read_verilog {f}" for f in verilog_files)
    synth_cmd = (
        f"synth_ice40 -top {top_module} -json /tmp/synth_out.json"
        if target == "ice40"
        else f"synth -top {top_module}"
    )
    script = f"{read_cmds}\n{synth_cmd}\nstat\n"
    try:
        proc = await asyncio.create_subprocess_exec(
            "yosys", "-p", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_s
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise ToolTimeoutError("yosys", timeout_s)
        combined = stdout_b.decode(errors="replace") + stderr_b.decode(errors="replace")
        if proc.returncode != 0:
            return f"[ERROR 3001] Synthesis failed\nTool output:\n{combined[:3000]}"
        stat_start = combined.find("=== design hierarchy ===")
        stats = combined[stat_start:stat_start + 2000] if stat_start >= 0 else ""
        return (
            f"Synthesis SUCCESS (backend={_BACKEND}, target={target})\n"
            f"Top module: {top_module}\n\n{stats}"
        )
    except ToolTimeoutError:
        raise
    except FileNotFoundError:
        raise ToolNotFoundError("yosys")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### 3.2 测试验证步骤

```bash
# Step 1: 安装包
uv pip install -e .

# Step 2: 快速验证（不走 MCP 协议）
python -c "
from auto_eda.servers.yosys.server import yosys_health_check
print(yosys_health_check())
"
# 期望: dict 含 backend: yosys-cli 或 unavailable

# Step 3: 用 MCP Inspector 验证协议层
mcp dev src/auto_eda/servers/yosys/server.py
# 浏览器打开 http://localhost:5173
# 找到 yosys_health_check -> Execute -> 验证返回 JSON
# 若 mcp 命令不存在: uv run mcp dev src/auto_eda/servers/yosys/server.py

# Step 4: 端到端综合测试（需要 Yosys 已安装）
# 将以下内容保存为 /tmp/counter.v:
# module counter(input clk, rst, output reg [3:0] count);
#   always @(posedge clk or posedge rst)
#     if (rst) count <= 0; else count <= count + 1;
# endmodule

python -c "
import asyncio
from auto_eda.servers.yosys.server import synthesize_rtl
print(asyncio.run(synthesize_rtl(['/tmp/counter.v'], 'counter')))
"
# 期望: Synthesis SUCCESS 并附带 stat 输出
```

### 3.3 Claude Code 集成验证

1. 确认 `.mcp.json` 在项目根目录（见 1.6 节）
2. 在 Claude Code 中打开项目根目录
3. Claude Code 自动检测并启动 MCP Server（约 3-5 秒）
4. 在对话中输入：`请调用 yosys_health_check 工具` — 应看到 JSON 状态返回
5. 若 Server 未出现：`Ctrl+Shift+P` → `MCP: Restart Servers`

---

## 4. Week 1 详细任务清单

### Day 1: 环境搭建 + 脚手架（目标 ~6h）

| 时间 | 任务 | 验收标准 | 风险预案 |
|------|------|----------|----------|
| 上午 2h | 安装 uv、Python 3.11、Yosys（见第 1 节） | `yosys --version` 正常输出 | WSL2 网络慢 → 换国内镜像源 |
| 上午 1h | 创建脚手架目录 + pyproject.toml（见第 2 节） | `uv pip install -e .[dev]` 无报错 | gdstk 编译失败 → 见 6.1 节 |
| 下午 2h | Hello World Server + MCP Inspector 验证（见第 3 节） | 两个工具在 Inspector 中可调用 | mcp 命令不存在 → `uv run mcp dev` |
| 下午 1h | 配置 pre-commit + 首次 git commit | `pre-commit run --all-files` 通过 | mypy 报错 → 先加 `# type: ignore`，Day 2 修复 |

**Day 1 完成标志**：`git log --oneline` 可见提交，MCP Inspector 可调用 `yosys_health_check`。

### Day 2: core 基础设施（目标 ~6h）

| 任务 | 目标文件 | 预计时间 | 测试方式 |
|------|----------|----------|----------|
| 完善 `core/errors.py`（全部错误码 + 子类） | `src/auto_eda/core/errors.py` | 1h | `pytest tests/unit/test_errors.py -v` |
| 实现 `core/process.py`（`run_tool`, `find_tool`） | `src/auto_eda/core/process.py` | 2h | mock subprocess 单元测试 |
| 实现 `core/result.py`（`ToolSuccess`, `ToolFailure`） | `src/auto_eda/core/result.py` | 1h | 单元测试 |
| 实现 `core/base_server.py`（`eda_tool` 装饰器） | `src/auto_eda/core/base_server.py` | 1h | 单元测试 |
| 补写单元测试 | `tests/unit/test_errors.py` 等 | 1h | `pytest tests/unit/ -m unit` |

**Day 2 完成标志**：`pytest tests/unit/ -m unit` 全绿，`mypy src/` 零报错。

### Day 3: Yosys 基础工具 — synthesize_rtl（目标 ~6h）

| 任务 | 目标文件 | 预计时间 | 关键点 |
|------|----------|----------|--------|
| 创建 `models/yosys.py` Pydantic 模型 | `src/auto_eda/models/yosys.py` | 1h | `top_module` 非空验证；`target` 枚举约束 |
| 实现 `servers/yosys/scripts.py` 脚本模板 | `src/auto_eda/servers/yosys/scripts.py` | 1h | generic / ice40 / asic 三种模板 |
| 实现 `servers/yosys/parser.py` 输出解析 | `src/auto_eda/servers/yosys/parser.py` | 1.5h | 解析 `stat` 输出中的 cell 数量和面积 |
| 重构 `server.py` 用 core 基础设施 | `src/auto_eda/servers/yosys/server.py` | 1.5h | 使用 `run_tool`、`eda_tool` 装饰器 |
| 集成测试 | `tests/integration/test_yosys_server.py` | 1h | `pytest -m integration`（需要 Yosys） |

**Day 3 完成标志**：`synthesize_rtl` 对 `counter.v` 返回含 cell 统计的结构化数据。

### Day 4: Yosys 工具补全 + 单元测试（目标 ~6h）

需完成的工具（按 DA3 规格）：

| 工具名 | 功能 | 依赖 |
|--------|------|------|
| `get_synthesis_stats` | 返回综合统计 JSON | `synthesize_rtl` 输出 |
| `check_rtl_syntax` | Verilog 语法检查（不综合） | `yosys -p "read_verilog ..."` |
| `optimize_rtl` | 逻辑优化（opt 命令序列） | `synthesize_rtl` 基础 |
| `generate_netlist` | 导出 JSON/BLIF 网表文件 | `write_json`/`write_blif` |

```bash
# Day 4 完成验证
pytest tests/unit/ tests/integration/ -m "unit or integration" --tb=short
# 期望: 全绿，coverage > 60%
```

**Day 4 完成标志**：Yosys Server 4 个核心工具全部可用，单元测试覆盖率 > 60%。

### Day 5: KiCad 基础工具开始（目标 ~6h）

| 任务 | 目标文件 | 预计时间 | 关键点 |
|------|----------|----------|--------|
| 实现版本检测（来自 DA4 风险缓解方案） | `src/auto_eda/servers/kicad/version.py` | 1.5h | 返回 `KiCadCapabilities`，永不抛异常 |
| 实现 `models/kicad.py` Pydantic 模型 | `src/auto_eda/models/kicad.py` | 1h | `RunDRCInput`, `RunDRCOutput` |
| 实现 `servers/kicad/cli_fallback.py` | `src/auto_eda/servers/kicad/cli_fallback.py` | 2h | `kicad-cli pcb drc` 命令封装 |
| 创建 `servers/kicad/server.py` 骨架 | `src/auto_eda/servers/kicad/server.py` | 1h | `kicad_health_check` 工具注册 |
| 单元测试版本检测逻辑 | `tests/unit/test_kicad_version.py` | 0.5h | mock `subprocess.run` |

**Day 5 完成标志**：`kicad_health_check` 可通过 MCP Inspector 调用，CLI DRC 骨架完成。

---

## 5. 开发规范速查卡

### 5.1 Tool 命名规则

所有 MCP tool 函数名遵循 `{动词}_{对象}_{修饰}` 格式，全小写下划线：

| 示例名 | 动词 | 对象 | 修饰 | 所属 Server |
|--------|------|------|------|-------------|
| `synthesize_rtl` | synthesize | rtl | - | yosys |
| `check_rtl_syntax` | check | rtl | syntax | yosys |
| `get_synthesis_stats` | get | synthesis | stats | yosys |
| `run_drc` | run | drc | - | kicad |
| `export_gerber` | export | gerber | - | kicad |
| `parse_verilog_ast` | parse | verilog | ast | verilog_utils |
| `lint_verilog` | lint | verilog | - | verilog_utils |
| `yosys_health_check` | - | - | - | yosys（通用工具固定格式） |

**禁止**：驼峰命名（`synthesizeRTL`）、过于通用（`run`、`process`）、含 Server 名前缀（`yosys_synthesize_rtl` 多余）。

### 5.2 Pydantic 模型模板

每个工具的输入/输出模型放在对应的 `models/*.py` 文件中：

```python
# src/auto_eda/models/yosys.py
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class SynthTarget(str, Enum):
    GENERIC = "generic"
    ICE40   = "ice40"
    ECP5    = "ecp5"
    XILINX  = "xilinx"


class SynthesizeRTLInput(BaseModel):
    verilog_files: list[str] = Field(
        ..., description="Verilog 源文件路径列表", min_length=1
    )
    top_module: str = Field(
        ..., description="顶层模块名称", min_length=1, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    )
    target: SynthTarget = Field(default=SynthTarget.GENERIC, description="综合目标")
    timeout_s: int = Field(default=300, ge=10, le=3600, description="超时秒数")

    @field_validator("verilog_files")
    @classmethod
    def files_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("至少需要一个 Verilog 文件")
        return v


class SynthesizeRTLOutput(BaseModel):
    success: bool
    top_module: str
    target: SynthTarget
    backend: str                     # "pyosys" | "yosys-cli"
    cell_count: int | None = None
    wire_count: int | None = None
    elapsed_s: float = 0.0
    warnings: list[str] = []
    raw_stats: str = ""              # Yosys stat 原始输出
```

### 5.3 错误处理模板

```python
# MCP tool 函数的标准错误处理结构
@mcp.tool(description="工具描述")
async def my_eda_tool(param: str) -> str:
    # 1. 输入验证（快速失败）
    if not param.strip():
        return "[ERROR 1001] param cannot be empty"

    # 2. 工具可用性检查
    if _BACKEND == "unavailable":
        raise ToolNotFoundError("yosys")  # FastMCP 将此转为错误响应

    # 3. 执行（捕获预期错误，透传意外错误）
    try:
        result = await run_tool(["yosys", "-p", script], timeout_s=300)
    except ToolTimeoutError:
        raise  # 透传，让调用方看到超时信息
    except ToolNotFoundError:
        raise

    # 4. 返回值检查
    if not result.success:
        return f"[ERROR 3001] Synthesis failed\n{result.stderr[:2000]}"

    # 5. 成功路径（结构化返回）
    return f"SUCCESS\n{parse_output(result.stdout)}"
```

### 5.4 测试用例模板

```python
# tests/unit/test_yosys_parser.py
import pytest
from auto_eda.servers.yosys.parser import parse_stat_output


SAMPLE_STAT = """
=== design hierarchy ===
   counter                           1
     Number of wires:               12
     Number of cells:                8
       $_DFF_P_                       4
       $_MUX_                         4
"""


@pytest.mark.unit
def test_parse_stat_cell_count() -> None:
    result = parse_stat_output(SAMPLE_STAT)
    assert result["cell_count"] == 8


@pytest.mark.unit
def test_parse_stat_wire_count() -> None:
    result = parse_stat_output(SAMPLE_STAT)
    assert result["wire_count"] == 12


@pytest.mark.unit
def test_parse_stat_empty_returns_none() -> None:
    result = parse_stat_output("")
    assert result["cell_count"] is None
```

```python
# tests/integration/test_yosys_server.py
import asyncio
import pytest
from auto_eda.servers.yosys.server import synthesize_rtl


COUNTER_V = """
module counter(input clk, rst, output reg [3:0] count);
  always @(posedge clk or posedge rst)
    if (rst) count <= 0; else count <= count + 1;
endmodule
"""


@pytest.mark.integration
def test_synthesize_counter(tmp_path):
    vf = tmp_path / "counter.v"
    vf.write_text(COUNTER_V)
    result = asyncio.run(synthesize_rtl([str(vf)], "counter"))
    assert "SUCCESS" in result
    assert "counter" in result
```

### 5.5 提交信息规范

格式：`<type>(<scope>): <subject>`

| Type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(yosys): add synthesize_rtl tool` |
| `fix` | Bug 修复 | `fix(kicad): handle IPC connection timeout` |
| `test` | 测试 | `test(yosys): add parser unit tests` |
| `refactor` | 重构（无功能变更） | `refactor(core): simplify run_tool error handling` |
| `chore` | 构建/工具/配置 | `chore: add pre-commit hooks` |
| `docs` | 文档 | `docs: update .mcp.json example` |

**Scope** 使用 Server 名：`yosys`、`kicad`、`verilog`、`core`、`ci`。

**Subject** 规则：小写英文，动词原形开头，不加句号，不超过 72 字符。

---

## 6. 常见问题预案

### 6.1 EDA 工具未安装时的处理

**现象**：`synthesize_rtl` 返回 `[ERROR 2001] EDA tool 'yosys' not found in PATH`

**原因**：Yosys 未安装，或安装路径不在 `PATH` 中。

**处理步骤**：

```bash
# Step 1: 确认问题
which yosys || echo "NOT FOUND"
yosys --version

# Step 2a: Ubuntu/Debian 安装
sudo apt update && sudo apt install -y yosys

# Step 2b: OSS CAD Suite（推荐，版本更新）
# 从 https://github.com/YosysHQ/oss-cad-suite-build/releases 下载
# 解压后执行: source ~/oss-cad-suite/environment

# Step 2c: conda 环境（科学计算用户）
conda install -c conda-forge yosys

# Step 3: 验证
yosys --version
python -c "from auto_eda.servers.yosys.server import yosys_health_check; print(yosys_health_check())"
# 期望: status: ok, backend: yosys-cli
```

**降级模式**：Yosys 未安装时，Server 仍可启动，`yosys_health_check` 返回 `status: degraded`，仅 Yosys 相关工具不可用，其他 Server（kicad、verilog_utils）不受影响。

### 6.2 KiCad IPC 连接失败处理

**现象**：`run_drc` 返回 `[ERROR 4001] KiCad IPC connection failed` 或 `[ERROR 4006] KiCad not running`

**根本原因**（来自 DA4 风险分析）：KiCad IPC API 需要 KiCad GUI 正在运行，且 IPC socket 已建立。

**处理步骤**：

```bash
# Step 1: 确认 KiCad 版本（需 v9+）
kicad-cli --version
# v10.x = 最优；v9.x = IPC 实验版；v8 以下 = 仅 CLI

# Step 2: 确认 KiCad GUI 正在运行（IPC 模式必须）
# Windows: 任务管理器确认 kicad.exe 进程存在
# Linux: ps aux | grep kicad

# Step 3: 检查 IPC socket
ls /tmp/kicad/api.sock 2>/dev/null || echo "Socket not found"

# Step 4: 自动 fallback 到 CLI 模式
# 代码层面：KiCad Server 已实现自动 fallback
# 手动触发 CLI 模式（不需要 GUI）：
python -c "
from auto_eda.servers.kicad.version import detect_kicad_capabilities
print(detect_kicad_capabilities())
"
# 若 api_mode = CLI_ONLY，DRC 工具将使用 kicad-cli pcb drc 命令
```

**WSL2 特别说明**：KiCad GUI 必须在 Windows 本机运行（不在 WSL2 内），IPC socket 路径需通过 Windows-WSL2 桥接。在 WSL2 开发环境中，建议**仅使用 CLI 模式**（`kicad-cli` 在 WSL2 中可独立运行）。

### 6.3 Yosys 版本不兼容处理

**现象**：综合脚本运行但产生意外错误，或 `synth_ice40` 命令不存在。

**版本要求**：Yosys >= 0.20（2022 年后发布，支持 `write_json` 网表格式）

```bash
# 检查版本
yosys --version
# 期望: Yosys 0.4x.x 或更高（0.20+ 均可）

# 若版本过低（如系统包 0.9.x）
# 方法 1: 升级系统包
sudo apt install -y yosys  # Ubuntu 22.04 提供 0.20+

# 方法 2: 使用 OSS CAD Suite（始终最新版）
source ~/oss-cad-suite/environment
yosys --version  # 期望 0.4x+

# 方法 3: 代码层版本检查（server.py 启动时）
# 已在 yosys_health_check 中返回版本号
# 若版本不满足要求，工具返回 EDAErrorCode.TOOL_VERSION_MISMATCH (2002)
```

### 6.4 pyverilog 安装失败

**现象**：`uv pip install -e .[ic]` 报 `pyverilog` 相关错误。

```bash
# pyverilog 依赖 PLY（Python Lex-Yacc）
pip install ply
pip install pyverilog

# 验证
python -c "import pyverilog; print(pyverilog.__version__)"
```

### 6.5 mypy strict 模式报错太多

**现象**：`pre-commit` 或 CI 中 mypy 报告大量类型错误，阻塞提交。

**处理原则**：不用 `# type: ignore` 掩盖，逐步修复。

```bash
# 查看错误列表（按文件分组）
mypy src/ --no-error-summary 2>&1 | sort

# 常见修复:
# 1. 函数缺少返回类型 → 添加 -> None 或 -> str
# 2. 变量类型推断失败 → 显式注解: x: list[str] = []
# 3. 第三方库无 stub → 已在 pyproject.toml 配置 ignore_missing_imports
# 4. Optional 未处理 → 添加 if x is not None 检查

# 临时允许文件级跳过（仅限 Day 1-2 过渡期）
# 在文件顶部添加: # mypy: ignore-errors
# 但必须在 Week 1 结束前移除所有此类注释
```

---

## 附录：快速参考

### 常用命令速查

```bash
# 运行所有单元测试
pytest tests/unit/ -m unit -v

# 运行集成测试（需要 EDA 工具）
pytest tests/integration/ -m integration -v

# 类型检查
mypy src/

# 代码格式化
ruff format src/ tests/

# Lint 检查
ruff check src/ tests/

# 启动 MCP Inspector（开发调试）
mcp dev src/auto_eda/servers/yosys/server.py

# 覆盖率报告
pytest tests/unit/ --cov=src/auto_eda --cov-report=html
# 打开 htmlcov/index.html 查看详情
```

### 错误码速查表

| 错误码 | 含义 | 常见原因 |
|--------|------|----------|
| 1001 | 无效输入 | 参数为空或格式错误 |
| 1002 | 文件未找到 | 路径错误或文件不存在 |
| 1005 | 超时 | EDA 工具运行时间超过 timeout_s |
| 2001 | 工具未找到 | EDA 工具未安装或不在 PATH |
| 2002 | 版本不兼容 | EDA 工具版本低于最低要求 |
| 3001 | 综合失败 | RTL 设计错误（非工具错误） |
| 3002 | Verilog 解析错误 | 语法错误 |
| 3004 | 顶层模块未找到 | top_module 参数错误 |
| 4001 | KiCad IPC 连接失败 | KiCad GUI 未运行或 socket 不存在 |
| 4006 | KiCad 未运行 | IPC 模式下 KiCad GUI 必须开启 |
| 5001 | Verilog 语法错误 | pyverilog 解析失败 |

### Phase 0 MVP 验收清单

- [ ] Yosys Server: `synthesize_rtl` 对标准计数器设计成功率 > 90%
- [ ] Yosys Server: `check_rtl_syntax` 正确识别语法错误
- [ ] KiCad Server: `kicad_health_check` 正确报告版本和 API 模式
- [ ] KiCad Server: `run_drc` CLI 模式可用（不依赖 GUI）
- [ ] Verilog Server: `parse_verilog_ast` 返回模块列表
- [ ] 所有 Server: `health_check` 工具 < 1s 响应
- [ ] 单元测试覆盖率 > 80%
- [ ] mypy strict 零报错
- [ ] Claude Code `.mcp.json` 集成验证通过
