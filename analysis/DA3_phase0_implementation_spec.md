# DA3: AUTO_EDA Phase 0 MVP 精确实现规格

> 文档类型: 直接可执行的开发规格
> 生成日期: 2026-03-14
> 数据来源: A7_tech_stack_decision.md + A8_integration_roadmap.md
> 覆盖范围: Phase 0 MVP (Month 1-2) 全部交付物

---

## 目录

1. [项目结构设计](#1-项目结构设计)
2. [pyproject.toml 完整设计](#2-pyprojecttoml-完整设计)
3. [核心基础设施规格](#3-核心基础设施规格)
4. [Yosys MCP Server 精确规格](#4-yosys-mcp-server-精确规格)
5. [KiCad MCP Server 精确规格](#5-kicad-mcp-server-精确规格)
6. [Verilog Utils MCP Server 精确规格](#6-verilog-utils-mcp-server-精确规格)
7. [测试框架设计](#7-测试框架设计)
8. [`.mcp.json` 配置模板](#8-mcpjson-配置模板)
9. [错误码与错误消息规范](#9-错误码与错误消息规范)
10. [开发里程碑检查清单](#10-开发里程碑检查清单)

---

## 1. 项目结构设计

### 1.1 完整目录树

```
auto-eda/
├── pyproject.toml                    # 项目元数据、依赖、工具配置
├── README.md                         # 项目说明
├── .mcp.json                         # Claude Code MCP 集成配置
├── .pre-commit-config.yaml           # Git 钩子配置
├── .github/
│   └── workflows/
│       ├── ci.yml                    # 基础 CI (lint + typecheck + test)
│       └── integration.yml           # 集成测试 (需 EDA 工具环境)
├── src/
│   └── auto_eda/
│       ├── __init__.py               # 包版本、公共导出
│       ├── __main__.py               # `python -m auto_eda` 入口
│       ├── core/
│       │   ├── __init__.py
│       │   ├── base_server.py        # MCP Server 基类与通用装饰器
│       │   ├── errors.py             # 统一错误码与异常类
│       │   ├── process.py            # 子进程管理 (CLI 调用封装)
│       │   └── result.py             # Result[T, E] 类型与工具输出规范
│       ├── models/
│       │   ├── __init__.py
│       │   ├── yosys.py              # Yosys 工具输入/输出 Pydantic 模型
│       │   ├── kicad.py              # KiCad 工具输入/输出 Pydantic 模型
│       │   └── verilog.py            # Verilog 工具输入/输出 Pydantic 模型
│       └── servers/
│           ├── __init__.py
│           ├── yosys/
│           │   ├── __init__.py
│           │   ├── server.py         # Yosys MCP Server 主文件
│           │   ├── synthesizer.py    # 综合逻辑 (Pyosys/CLI 决策)
│           │   ├── scripts.py        # 综合脚本模板
│           │   └── parser.py         # Yosys 输出解析 (JSON/文本)
│           ├── kicad/
│           │   ├── __init__.py
│           │   ├── server.py         # KiCad MCP Server 主文件
│           │   ├── ipc_client.py     # IPC API 连接管理
│           │   ├── cli_fallback.py   # CLI Jobsets fallback
│           │   └── version.py        # KiCad 版本检测与兼容处理
│           └── verilog_utils/
│               ├── __init__.py
│               ├── server.py         # Verilog Utils MCP Server 主文件
│               ├── parser.py         # pyverilog 封装
│               └── linter.py         # Verilog lint 逻辑
├── tests/
│   ├── conftest.py                   # 全局 fixtures
│   ├── fixtures/
│   │   ├── verilog/                  # 测试用 Verilog 文件
│   │   │   ├── counter.v
│   │   │   ├── adder.v
│   │   │   ├── fifo.v
│   │   │   └── syntax_error.v
│   │   ├── kicad/                    # 测试用 KiCad 工程
│   │   │   └── blinky/
│   │   │       ├── blinky.kicad_pro
│   │   │       ├── blinky.kicad_sch
│   │   │       └── blinky.kicad_pcb
│   │   └── yosys/                   # 测试用综合输出
│   │       ├── counter_synth.json
│   │       └── counter_stat.txt
│   ├── unit/
│   │   ├── test_errors.py
│   │   ├── test_process.py
│   │   ├── test_result.py
│   │   ├── test_yosys_models.py
│   │   ├── test_kicad_models.py
│   │   ├── test_verilog_models.py
│   │   ├── test_yosys_parser.py
│   │   ├── test_yosys_scripts.py
│   │   ├── test_kicad_version.py
│   │   └── test_verilog_parser.py
│   ├── integration/
│   │   ├── test_yosys_server.py      # 需要 Yosys 已安装
│   │   ├── test_kicad_server.py      # 需要 KiCad 已安装
│   │   └── test_verilog_utils.py
│   └── mcp/
│       ├── test_yosys_mcp_protocol.py   # MCP 协议合规性测试
│       ├── test_kicad_mcp_protocol.py
│       └── test_verilog_mcp_protocol.py
└── scripts/
    ├── install_eda_tools.sh           # EDA 工具安装脚本 (Linux/CI)
    └── check_dependencies.py          # 依赖检查脚本
```

### 1.2 模块职责边界

| 模块 | 职责 | 禁止 |
|------|------|------|
| `core/errors.py` | 定义错误码枚举和异常类 | 不引用任何 EDA 库 |
| `core/process.py` | 子进程启动、超时、流式捕获 | 不解析 EDA 特定输出 |
| `core/result.py` | Result 类型和序列化 | 不包含业务逻辑 |
| `models/*.py` | Pydantic 输入/输出模型 | 不包含执行逻辑 |
| `servers/*/server.py` | MCP tool 注册和路由 | 不直接调用 EDA 工具 |
| `servers/*/synthesizer.py` | EDA 工具调用逻辑 | 不直接处理 MCP 协议 |

---

## 2. pyproject.toml 完整设计

```toml
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
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
]

# Layer 1: MCP 协议层 + 最小运行时 (必须)
dependencies = [
    "mcp[cli]>=1.3.0",           # FastMCP SDK, 含 CLI 工具和 stdio 传输
    "pydantic>=2.6.0",           # 运行时类型验证与模型定义
    "anyio>=4.3.0",              # 异步运行时抽象
    "psutil>=5.9.0",             # 进程监控与资源管理
    "rich>=13.7.0",              # 结构化 CLI 输出 (调试/日志)
]

[project.optional-dependencies]
# PCB 设计功能 (依赖 KiCad 已安装)
pcb = [
    "kikit>=1.3.0",              # KiCad 自动化 (拼板/制造文件)
    "sexpdata>=1.0.0",           # KiCad S-expression 解析
]

# IC/ASIC 数字前端功能
ic = [
    "pyverilog>=1.3.0",          # Verilog AST 解析
    "gdstk>=0.9.0",              # GDSII/OASIS 高性能读写 (C++后端)
]

# 扩展 HDL 解析 (SystemVerilog/VHDL)
hdl = [
    "auto-eda[ic]",
    # hdlConvertor 需从源码安装 (未上 PyPI 主流源)
    # 用户手动: pip install hdlConvertor
]

# 完整安装 (所有功能)
full = [
    "auto-eda[pcb]",
    "auto-eda[ic]",
]

# 开发依赖
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
    # mypy stubs
    "types-psutil",
]

[project.scripts]
# 单独启动各 MCP Server 的 CLI 入口
auto-eda-yosys    = "auto_eda.servers.yosys:main"
auto-eda-kicad    = "auto_eda.servers.kicad:main"
auto-eda-verilog  = "auto_eda.servers.verilog_utils:main"
# 统一入口 (通过 --server 参数选择)
auto-eda          = "auto_eda.__main__:main"

[project.urls]
Homepage       = "https://github.com/auto-eda/auto-eda"
Documentation  = "https://auto-eda.readthedocs.io"
Repository     = "https://github.com/auto-eda/auto-eda"
"Bug Tracker"  = "https://github.com/auto-eda/auto-eda/issues"

# ---------- Hatchling 构建配置 ----------
[tool.hatch.build.targets.wheel]
packages = ["src/auto_eda"]

[tool.hatch.build.targets.sdist]
exclude = [
    "/.github",
    "/tests",
    "/scripts",
    "*.pyc",
    "__pycache__",
]

# ---------- ruff: Linting + Formatting ----------
[tool.ruff]
target-version = "py310"         # 最低支持版本
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ANN",  # flake8-annotations (强制类型注解)
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
]
ignore = [
    "ANN101",  # self 无需注解
    "ANN102",  # cls 无需注解
    "E501",    # 行长由 ruff format 处理
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN"]        # 测试文件不强制注解

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# ---------- mypy: 静态类型检查 ----------
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_reexport = true
namespaces_packages = false

[[tool.mypy.overrides]]
module = [
    "pyverilog.*",
    "gdstk.*",
    "kikit.*",
    "sexpdata.*",
]
ignore_missing_imports = true   # EDA 库暂无 stub

# ---------- pytest ----------
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"            # pytest-asyncio 自动检测
timeout = 120                    # 默认超时 120s (EDA 工具可能较慢)
markers = [
    "unit: 纯逻辑单元测试，无需 EDA 工具",
    "integration: 需要 EDA 工具已安装",
    "slow: 运行时间超过 30s 的测试",
    "mcp: MCP 协议合规性测试",
]
addopts = [
    "--strict-markers",
    "-ra",                        # 显示所有非通过的测试摘要
    "--tb=short",
]

# ---------- coverage ----------
[tool.coverage.run]
source = ["src/auto_eda"]
omit = ["*/tests/*", "*/__main__.py"]
branch = true

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]

---

## 3. 核心基础设施规格

### 3.1 `core/errors.py` — 错误码与异常体系

```python
# src/auto_eda/core/errors.py
from enum import IntEnum

class EDAErrorCode(IntEnum):
    # 通用错误 (1xxx)
    UNKNOWN              = 1000
    INVALID_INPUT        = 1001
    FILE_NOT_FOUND       = 1002
    FILE_PERMISSION      = 1003
    UNSUPPORTED_FORMAT   = 1004
    TIMEOUT              = 1005
    CANCELLED            = 1006

    # 工具未找到/环境错误 (2xxx)
    TOOL_NOT_FOUND       = 2001  # EDA 工具未安装
    TOOL_VERSION_MISMATCH= 2002  # 版本不兼容
    TOOL_LICENSE_ERROR   = 2003  # 许可证问题
    DEPENDENCY_MISSING   = 2004  # Python 依赖缺失

    # Yosys 错误 (3xxx)
    YOSYS_SYNTHESIS_FAIL = 3001  # 综合失败 (设计错误)
    YOSYS_PARSE_ERROR    = 3002  # Verilog 解析错误
    YOSYS_SCRIPT_ERROR   = 3003  # TCL 脚本错误
    YOSYS_NO_TOP_MODULE  = 3004  # 未指定或未找到顶层模块
    YOSYS_TECH_LIB_ERROR = 3005  # 工艺库加载失败

    # KiCad 错误 (4xxx)
    KICAD_IPC_CONN_FAIL  = 4001  # IPC API 连接失败
    KICAD_IPC_TIMEOUT    = 4002  # IPC 操作超时
    KICAD_PROJECT_INVALID= 4003  # 工程文件损坏/无效
    KICAD_DRC_ERROR      = 4004  # DRC 执行错误 (非 DRC 违规)
    KICAD_VERSION_LOW    = 4005  # KiCad 版本低于最低要求
    KICAD_NOT_RUNNING    = 4006  # KiCad GUI 未运行 (IPC 模式需要)

    # Verilog 解析错误 (5xxx)
    VERILOG_SYNTAX_ERROR = 5001
    VERILOG_INCLUDE_ERROR= 5002  # include 文件未找到
    VERILOG_PARSE_CRASH  = 5003  # pyverilog 内部崩溃


class EDAError(Exception):
    """所有 AUTO_EDA 异常的基类。"""
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
        self.tool_output = tool_output  # EDA 工具原始输出（调试用）
        super().__init__(message)

    def to_mcp_error_text(self) -> str:
        """格式化为 MCP tool 错误返回文本。"""
        lines = [f"[ERROR {self.code.value}] {self.message}"]
        if self.detail:
            lines.append(f"Detail: {self.detail}")
        if self.tool_output:
            lines.append(f"Tool output:\n{self.tool_output[:2000]}")
        return "\n".join(lines)


# 常用子类（可直接 raise，无需指定 code）
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

### 3.2 `core/process.py` — 子进程管理

```python
# src/auto_eda/core/process.py
import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path

from .errors import EDAErrorCode, EDAError, ToolNotFoundError, ToolTimeoutError


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def find_tool(tool_name: str) -> Path:
    """在 PATH 中查找 EDA 工具，找不到抛出 ToolNotFoundError。"""
    found = shutil.which(tool_name)
    if found is None:
        raise ToolNotFoundError(tool_name)
    return Path(found)


async def run_tool(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout_s: int = 300,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
) -> ProcessResult:
    """
    异步执行 EDA CLI 工具。

    - 超时自动 kill 子进程并抛出 ToolTimeoutError
    - stdout/stderr 完整捕获（不截断，最大 10MB 缓冲）
    - 不在此处检查 returncode，由调用方决定成功/失败语义
    """
    tool_name = Path(args[0]).name
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if stdin_data else None,
            cwd=cwd,
            env=env,
        )
        stdin_bytes = stdin_data.encode() if stdin_data else None
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout_s,
            )
            return ProcessResult(
                returncode=proc.returncode or 0,
                stdout=stdout_b.decode(errors="replace"),
                stderr=stderr_b.decode(errors="replace"),
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise ToolTimeoutError(tool_name, timeout_s)
    except FileNotFoundError:
        raise ToolNotFoundError(tool_name)


def check_tool_available(tool_name: str) -> bool:
    """非抛出式工具可用性检查，用于 fallback 决策。"""
    return shutil.which(tool_name) is not None
```

### 3.3 `core/result.py` — 统一工具输出格式

```python
# src/auto_eda/core/result.py
from typing import Any
from pydantic import BaseModel


class ToolSuccess(BaseModel):
    """MCP tool 成功返回的标准包装。"""
    success: bool = True
    data: dict[str, Any]          # 实际结果数据
    warnings: list[str] = []      # 非致命警告
    tool_used: str = ""           # 实际使用的后端 ("pyosys"/"yosys-cli"/"kicad-ipc"/...)
    elapsed_s: float = 0.0        # 执行耗时（秒）


class ToolFailure(BaseModel):
    """MCP tool 失败返回的标准包装（不抛异常，用于预期失败）。"""
    success: bool = False
    error_code: int
    error_message: str
    detail: str | None = None
    tool_output: str | None = None  # 截断的工具原始输出


def format_mcp_error(error: Exception) -> str:
    """将任意异常格式化为 MCP tool 错误文本（用于 raise McpError 前）。"""
    from .errors import EDAError
    if isinstance(error, EDAError):
        return error.to_mcp_error_text()
    return f"[ERROR] Unexpected error: {type(error).__name__}: {error}"
```

### 3.4 `core/base_server.py` — Server 基类

```python
# src/auto_eda/core/base_server.py
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from mcp.server.fastmcp import FastMCP

from .errors import EDAError
from .result import format_mcp_error

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def create_server(name: str, version: str = "0.1.0") -> FastMCP:
    """创建带统一配置的 FastMCP 实例。"""
    mcp = FastMCP(name, version=version)
    return mcp


def eda_tool(func: F) -> F:
    """
    MCP tool 装饰器：统一处理异常、记录耗时、格式化错误。
    用法：在 @mcp.tool() 之后叠加此装饰器。
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.monotonic() - start
            logger.debug("%s completed in %.2fs", func.__name__, elapsed)
            return result
        except EDAError as e:
            logger.warning("%s failed: [%s] %s", func.__name__, e.code, e.message)
            # FastMCP 将字符串返回值直接作为 tool content 返回
            return format_mcp_error(e)
        except Exception as e:
            logger.exception("Unexpected error in %s", func.__name__)
            return format_mcp_error(e)
    return wrapper  # type: ignore[return-value]
```


---

## 4. Yosys MCP Server 精确规格

### 4.1 Pyosys vs CLI Fallback 决策逻辑

```
启动时检测顺序：
1. 尝试 import pyosys（Pyosys Python 绑定，需要从源码编译安装）
   → 成功：BACKEND = "pyosys"（最优，进程内调用，无启动开销）
2. 尝试 shutil.which("yosys")
   → 成功：BACKEND = "yosys-cli"（CLI 子进程，主流安装方式）
3. 两者均失败：BACKEND = None
   → 所有 synthesis tool 调用返回 EDAErrorCode.TOOL_NOT_FOUND
   → 仅文件解析类 tool（parse_verilog 等）仍可用

每次工具调用时均使用初始化时确定的 BACKEND，不在调用时重新检测。
```

**决策依据**：
- Pyosys 通过 pybind11 直接操作 Yosys 内部对象，避免进程启动开销（~200ms/次），且可访问完整的设计数据库（RTLIL）
- 系统包安装的 Yosys（apt/brew/conda）通常不含 Pyosys；CLI 是更广泛可用的 fallback
- 两种后端对外暴露完全相同的 MCP tool 接口，`tool_used` 字段区分实际后端

### 4.2 综合脚本模板设计

```python
# src/auto_eda/servers/yosys/scripts.py

SYNTH_SCRIPT_FPGA = """\
read_verilog {options} {verilog_files}
{read_liberty_cmds}
hierarchy -check -top {top_module}
proc
opt
fsm
opt
memory
opt
synth {target_opts}
write_json {output_json}
stat{liberty_stat_opts}
"""
# {target_opts}: "-top {top}" for generic, "-run begin:fine" for partial
# {liberty_stat_opts}: " -liberty {lib}" if liberty provided

SYNTH_SCRIPT_ASIC = """\
read_verilog {options} {verilog_files}
read_liberty -lib {liberty_file}
hierarchy -check -top {top_module}
proc
opt
fsm
opt
memory
opt -full
synth -top {top_module}
dfflibmap -liberty {liberty_file}
abc -liberty {liberty_file}
cleanup
write_netlist {output_netlist}
write_json {output_json}
stat -liberty {liberty_file}
"""

SYNTH_SCRIPT_GENERIC = """\
read_verilog {options} {verilog_files}
hierarchy -check{top_opt}
proc
opt
write_json {output_json}
stat
"""
# {top_opt}: " -top {top_module}" or "" if auto-detect

SHOW_SCRIPT = """\
read_verilog {options} {verilog_files}
hierarchy -check{top_opt}
proc
opt
show -format {fmt} -prefix {output_prefix} {top_opt_show}
"""
# {fmt}: "dot", "svg", "ps"

STAT_ONLY_SCRIPT = """\
read_verilog {options} {verilog_files}
{read_liberty_cmds}
hierarchy -check{top_opt}
proc
stat{liberty_stat_opts}
"""
```

### 4.3 Pydantic 输入/输出模型

```python
# src/auto_eda/models/yosys.py
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, field_validator


# ---- synthesize tool ----

class SynthesizeInput(BaseModel):
    verilog_files: list[str] = Field(
        description="Verilog/SystemVerilog 源文件路径列表（绝对路径或相对于 cwd）"
    )
    top_module: str | None = Field(
        default=None,
        description="顶层模块名。None 时 Yosys 自动推断（仅单顶层设计有效）"
    )
    liberty_file: str | None = Field(
        default=None,
        description="Liberty (.lib) 工艺库文件路径。提供时执行 ASIC 映射综合"
    )
    target: Literal["generic", "asic", "xilinx", "ice40", "ecp5", "gowin"] = Field(
        default="generic",
        description="综合目标。'asic' 需要 liberty_file；FPGA 目标使用对应 synth_* 命令"
    )
    output_dir: str = Field(
        description="输出文件目录（绝对路径）"
    )
    systemverilog: bool = Field(
        default=False,
        description="True 时使用 -sv 参数支持 SystemVerilog"
    )
    include_dirs: list[str] = Field(
        default_factory=list,
        description="Verilog include 搜索路径"
    )
    defines: dict[str, str] = Field(
        default_factory=dict,
        description="预处理宏定义，如 {\"WIDTH\": \"8\"}"
    )
    timeout_s: int = Field(default=300, ge=10, le=3600)

    @field_validator("verilog_files")
    @classmethod
    def check_files_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("verilog_files must not be empty")
        return v


class ResourceStats(BaseModel):
    """Yosys stat 命令输出的资源统计。"""
    num_wires: int = 0
    num_wire_bits: int = 0
    num_cells: int = 0
    num_memories: int = 0
    num_processes: int = 0
    cell_types: dict[str, int] = Field(default_factory=dict)  # {"$dff": 4, "$add": 2}
    # ASIC 映射后的工艺单元统计
    mapped_cells: dict[str, int] = Field(default_factory=dict)  # {"sky130_fd_sc_hd__dfxtp_2": 4}
    estimated_area: float | None = None  # 仅 ASIC 模式，单位 um²


class SynthesizeOutput(BaseModel):
    success: bool
    top_module: str
    backend_used: Literal["pyosys", "yosys-cli"]
    output_netlist: str | None = None   # Verilog 网表路径
    output_json: str | None = None      # JSON 网表路径
    stats: ResourceStats | None = None
    warnings: list[str] = []
    elapsed_s: float = 0.0
    yosys_log: str = ""                 # 完整 Yosys 日志（截断至 50KB）


# ---- stat tool ----

class StatInput(BaseModel):
    verilog_files: list[str]
    top_module: str | None = None
    liberty_file: str | None = None
    systemverilog: bool = False
    timeout_s: int = Field(default=60, ge=5, le=300)


class StatOutput(BaseModel):
    success: bool
    stats: ResourceStats
    raw_output: str


# ---- check tool ----

class CheckInput(BaseModel):
    verilog_files: list[str]
    top_module: str | None = None
    systemverilog: bool = False
    include_dirs: list[str] = []
    defines: dict[str, str] = {}
    timeout_s: int = Field(default=30, ge=5, le=120)


class CheckIssue(BaseModel):
    severity: Literal["error", "warning"]
    message: str
    location: str | None = None  # "file.v:42" 格式


class CheckOutput(BaseModel):
    success: bool
    issues: list[CheckIssue] = []
    raw_output: str


# ---- write_netlist tool ----

class WriteNetlistInput(BaseModel):
    json_netlist: str = Field(description="synthesize 产生的 JSON 网表路径")
    output_path: str = Field(description="输出 Verilog 网表路径")
    format: Literal["verilog", "blif", "edif", "json"] = "verilog"
    noattr: bool = Field(default=False, description="True 时移除综合属性注释")


class WriteNetlistOutput(BaseModel):
    success: bool
    output_path: str
    file_size_bytes: int


# ---- show_rtl tool ----

class ShowRTLInput(BaseModel):
    verilog_files: list[str]
    top_module: str | None = None
    output_dir: str
    format: Literal["dot", "svg"] = "svg"
    systemverilog: bool = False
    timeout_s: int = Field(default=60, ge=5, le=300)


class ShowRTLOutput(BaseModel):
    success: bool
    output_file: str   # .svg 或 .dot 文件路径
    format: str
```

### 4.4 MCP Server 工具注册（核心部分）

```python
# src/auto_eda/servers/yosys/server.py (结构示例)
from mcp.server.fastmcp import FastMCP
from auto_eda.core.base_server import create_server, eda_tool
from auto_eda.models.yosys import (
    SynthesizeInput, SynthesizeOutput,
    StatInput, StatOutput,
    CheckInput, CheckOutput,
    WriteNetlistInput, WriteNetlistOutput,
    ShowRTLInput, ShowRTLOutput,
)
from .synthesizer import YosysSynthesizer

mcp: FastMCP = create_server("auto-eda-yosys", version="0.1.0")
_synth = YosysSynthesizer()   # 单例，持有 BACKEND 检测结果


@mcp.tool()
@eda_tool
async def synthesize(params: SynthesizeInput) -> SynthesizeOutput:
    """
    执行 RTL 综合。支持 generic/ASIC/FPGA 目标。
    输入 Verilog/SV 文件，输出 JSON 网表和资源统计。
    """
    return await _synth.synthesize(params)


@mcp.tool()
@eda_tool
async def stat(params: StatInput) -> StatOutput:
    """快速统计 RTL 设计的资源使用（不执行完整综合映射）。"""
    return await _synth.stat(params)


@mcp.tool()
@eda_tool
async def check(params: CheckInput) -> CheckOutput:
    """检查 Verilog 设计语法和设计规则（不综合，快速反馈）。"""
    return await _synth.check(params)


@mcp.tool()
@eda_tool
async def write_netlist(params: WriteNetlistInput) -> WriteNetlistOutput:
    """将 JSON 网表转换为 Verilog/BLIF/EDIF 格式。"""
    return await _synth.write_netlist(params)


@mcp.tool()
@eda_tool
async def show_rtl(params: ShowRTLInput) -> ShowRTLOutput:
    """生成 RTL 电路图（SVG 或 DOT 格式），用于设计可视化。"""
    return await _synth.show_rtl(params)


@mcp.resource("yosys://help/synthesis-targets")
def synthesis_targets_help() -> str:
    """列出支持的综合目标及说明。"""
    return (
        "Supported synthesis targets:\n"
        "  generic  - Technology-independent (no cell mapping)\n"
        "  asic     - ASIC mapping using Liberty file (requires liberty_file)\n"
        "  xilinx   - Xilinx 7-series/UltraScale\n"
        "  ice40    - Lattice iCE40\n"
        "  ecp5     - Lattice ECP5\n"
        "  gowin    - Gowin GW1N series\n"

    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### 4.5 Yosys 输出解析规格

解析器位于 `src/auto_eda/servers/yosys/parser.py`，关键正则：

| 提取目标 | 正则模式 |
|----------|----------|
| 总 wire 数 | `Number of wires:\s+(\d+)` |
| wire bits | `Number of wire bits:\s+(\d+)` |
| 总 cell 数 | `Number of cells:\s+(\d+)` |
| 各类型 cell | `^\s{5}(\$[\w]+\|[\w]+)\s+(\d+)$`（多行） |
| 芯片面积 | `Chip area for.*?:\s+([\d.]+)` |
| WARNING 行 | `^Warning: (.+)$`（多行） |
| ERROR 行 | `^ERROR: (.+)$`（多行） |

**综合成功判断条件**：`returncode == 0` AND `stderr` 中无 `ERROR:` 行。

---

## 5. KiCad MCP Server 精确规格

### 5.1 版本检测与兼容性处理

```python
# src/auto_eda/servers/kicad/version.py
import re
import shutil
from dataclasses import dataclass
from enum import Flag, auto


class KiCadCapability(Flag):
    NONE         = 0
    CLI_BASIC    = auto()   # v6+: kicad-cli 基础命令
    CLI_JOBSETS  = auto()   # v8+: jobsets / scripted 模式
    IPC_API      = auto()   # v10+: IPC API (Protobuf socket)


@dataclass
class KiCadVersion:
    major: int
    minor: int
    patch: int
    capabilities: KiCadCapability

    @property
    def version_str(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> "KiCadVersion":
        m = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str)
        if not m:
            raise ValueError(f"Cannot parse KiCad version: {version_str}")
        major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        caps = KiCadCapability.NONE
        if major >= 6:
            caps |= KiCadCapability.CLI_BASIC
        if major >= 8:
            caps |= KiCadCapability.CLI_JOBSETS
        if major >= 10:
            caps |= KiCadCapability.IPC_API
        return cls(major, minor, patch, caps)


def detect_kicad_version() -> KiCadVersion | None:
    """
    检测已安装的 KiCad 版本。
    依次尝试：kicad-cli --version，kicad --version。
    返回 None 表示未安装。
    """
    import subprocess
    for cmd in ["kicad-cli", "kicad"]:
        if shutil.which(cmd) is None:
            continue
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True, text=True, timeout=10
            )
            # kicad-cli 输出示例: "8.0.3"
            # kicad 输出示例: "KiCad 8.0.3, release build"
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                if re.search(r"\d+\.\d+\.\d+", line):
                    ver_str = re.search(r"(\d+\.\d+\.\d+)", line).group(1)
                    return KiCadVersion.from_string(ver_str)
        except (subprocess.TimeoutExpired, OSError):
            continue
    return None


MIN_KICAD_VERSION = KiCadVersion.from_string("7.0.0")
```

### 5.2 IPC API 连接管理（Phase 0 预留，v10+ 激活）

Phase 0 KiCad server 全部基于 `kicad-cli` 实现（v7/v8 兼容）。
IPC API 连接管理器作为接口预留，v10 检测到时自动启用：

```
IPCConnectionManager 设计（Phase 0 预留）：
- 连接目标：KiCad IPC API Unix Socket (Linux/macOS) 或 Named Pipe (Windows)
- Socket 路径：$KICAD_RUN_DIR/kicad.sock 或用户配置
- 连接池大小：1（KiCad 单实例，不支持并发写操作）
- 重连策略：指数退避，最大 3 次，初始间隔 1s
- 超时：连接超时 5s，操作超时可配置（默认 60s）
- 健康检查：每次操作前 ping，失败则重连
- Phase 0 实现：IPCConnectionManager 存根，所有方法抛出
  NotImplementedError（防止误用），实际路由至 cli_fallback.py
```

### 5.3 Pydantic 输入/输出模型

```python
# src/auto_eda/models/kicad.py
from pydantic import BaseModel, Field
from typing import Literal


# ---- open_project tool ----

class OpenProjectInput(BaseModel):
    project_path: str = Field(description=".kicad_pro 文件绝对路径")

class ProjectInfo(BaseModel):
    project_name: str
    project_dir: str
    schematic_file: str | None
    pcb_file: str | None
    kicad_version: str

class OpenProjectOutput(BaseModel):
    success: bool
    project: ProjectInfo | None = None


# ---- list_components tool ----

class ListComponentsInput(BaseModel):
    schematic_file: str = Field(description=".kicad_sch 文件绝对路径")
    include_power: bool = Field(default=False, description="是否包含电源符号")

class Component(BaseModel):
    reference: str       # "R1", "U3" 等
    value: str           # "10k", "STM32F103" 等
    footprint: str
    datasheet: str = ""
    description: str = ""
    quantity: int = 1

class ListComponentsOutput(BaseModel):
    success: bool
    components: list[Component] = []
    total_count: int = 0


# ---- run_drc tool ----

class RunDRCInput(BaseModel):
    pcb_file: str = Field(description=".kicad_pcb 文件绝对路径")
    output_dir: str
    rules_file: str | None = None  # 自定义 DRC 规则文件
    timeout_s: int = Field(default=120, ge=10, le=600)

class DRCViolation(BaseModel):
    rule: str
    severity: Literal["error", "warning"]
    description: str
    location: str | None = None  # "(x, y) mm" 格式

class RunDRCOutput(BaseModel):
    success: bool               # DRC 执行成功（非零 violation 不影响此字段）
    violation_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    violations: list[DRCViolation] = []
    report_path: str | None = None


# ---- run_erc tool ----

class RunERCInput(BaseModel):
    schematic_file: str
    output_dir: str
    timeout_s: int = Field(default=60, ge=10, le=300)

class ERCViolation(BaseModel):
    rule: str
    severity: Literal["error", "warning"]
    description: str
    sheet: str = ""

class RunERCOutput(BaseModel):
    success: bool
    violation_count: int = 0
    violations: list[ERCViolation] = []
    report_path: str | None = None


# ---- export_gerber tool ----

class ExportGerberInput(BaseModel):
    pcb_file: str
    output_dir: str
    layers: list[str] = Field(
        default_factory=list,
        description="导出图层列表；空列表导出所有铜层+掩膜层"
    )
    include_drill: bool = True
    timeout_s: int = Field(default=60, ge=10, le=300)

class ExportGerberOutput(BaseModel):
    success: bool
    output_dir: str
    files: list[str] = []   # 生成的 Gerber/Drill 文件路径列表
    file_count: int = 0


# ---- export_bom tool ----

class ExportBOMInput(BaseModel):
    schematic_file: str
    output_path: str
    format: Literal["csv", "json", "xml"] = "csv"
    group_by: list[str] = Field(
        default_factory=lambda: ["Value", "Footprint"],
        description="BOM 分组字段"
    )
    timeout_s: int = Field(default=30, ge=10, le=120)

class ExportBOMOutput(BaseModel):
    success: bool
    output_path: str
    component_count: int = 0
    unique_values: int = 0


# ---- get_netlist tool ----

class GetNetlistInput(BaseModel):
    schematic_file: str
    output_path: str
    format: Literal["kicad", "spice", "cadstar"] = "kicad"
    timeout_s: int = Field(default=60, ge=10, le=300)

class GetNetlistOutput(BaseModel):
    success: bool
    output_path: str
    net_count: int = 0
```

### 5.4 CLI Jobsets Fallback 命令映射

| Tool | kicad-cli 命令 |
|------|---------------|
| `run_drc` | `kicad-cli pcb drc --output <dir> --format json <pcb_file>` |
| `run_erc` | `kicad-cli sch erc --output <dir> --format json <sch_file>` |
| `export_gerber` | `kicad-cli pcb export gerbers --output <dir> <pcb_file>` |
| `export_drill` | `kicad-cli pcb export drill --output <dir> <pcb_file>` |
| `export_bom` | `kicad-cli sch export bom --output <path> --format csv <sch_file>` |
| `get_netlist` | `kicad-cli sch export netlist --output <path> --format kicad <sch_file>` |
| `export_svg` | `kicad-cli sch export svg --output <dir> <sch_file>` |

kicad-cli 不可用时降级为纯 S-expression 文件解析（`sexpdata`），仅 `list_components`、`open_project`、`get_netlist` 可用。

---

## 6. Verilog Utils MCP Server 精确规格

### 6.1 Pydantic 输入/输出模型

```python
# src/auto_eda/models/verilog.py  (核心模型)
from pydantic import BaseModel, Field
from typing import Literal

class PortDef(BaseModel):
    name: str
    direction: Literal["input", "output", "inout"]
    width: str = "1"        # "1", "[7:0]", "[WIDTH-1:0]"
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
    children: list["HierarchyNode"] = []

class LintIssue(BaseModel):
    rule: str
    severity: Literal["error", "warning", "info"]
    message: str
    file: str
    line: int
    column: int = 0
```

### 6.2 pyverilog 封装要点

- 使用 `pyverilog.vparser.parser.VerilogCodeParser` 解析
- `ParseError` → `EDAErrorCode.VERILOG_SYNTAX_ERROR`
- pyverilog 内部崩溃 → `EDAErrorCode.VERILOG_PARSE_CRASH`
- `include_dirs` / `defines` 通过 `preprocess=True` 传入
- SystemVerilog：检查 `hdlConvertor` can import when available, fall back to pyverilog with warning

### 6.3 Phase 0 Lint Rules (AST traversal)

| Rule ID | Description | Implementation |
|---------|-------------|----------------|
| `W001` | Unused output port | AST reference analysis |
| `W002` | Implicit net declaration | Port connection analysis |
| `W003` | Blocking assignment in sequential always | always block type check |
| `E001` | Instantiated undefined module | Cross-file module name lookup |
| `E002` | Port width mismatch | Connection point width comparison |

---

## 7. 测试框架设计

### 7.1 全局 Fixture 设计

```python
# tests/conftest.py
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from auto_eda.core.process import ProcessResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def counter_v() -> Path:
    return FIXTURES_DIR / "verilog" / "counter.v"

@pytest.fixture
def adder_v() -> Path:
    return FIXTURES_DIR / "verilog" / "adder.v"

@pytest.fixture
def blinky_project() -> Path:
    return FIXTURES_DIR / "kicad" / "blinky" / "blinky.kicad_pro"

@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    out.mkdir()
    return out

@pytest.fixture
def yosys_success_result() -> ProcessResult:
    return ProcessResult(
        returncode=0,
        stdout=(
            "=== counter ===\n"
            "   Number of wires:                  8\n"
            "   Number of wire bits:             12\n"
            "   Number of cells:                  4\n"
            "     $dff                            4\n"
            "     $add                            2\n"
        ),
        stderr="",
    )

@pytest.fixture
def yosys_failure_result() -> ProcessResult:
    return ProcessResult(
        returncode=1,
        stdout="",
        stderr="ERROR: Module `undefined_module' referenced but not found!\n",
    )

@pytest.fixture
def mock_run_tool(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    mock.return_value = ProcessResult(returncode=0, stdout="", stderr="")
    monkeypatch.setattr("auto_eda.core.process.run_tool", mock)
    return mock

@pytest.fixture
def mock_find_tool(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(return_value=Path("/usr/bin/yosys"))
    monkeypatch.setattr("auto_eda.core.process.find_tool", mock)
    return mock

@pytest.fixture
def mock_kicad_available(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil
    orig = shutil.which
    monkeypatch.setattr(shutil, "which",
        lambda n: f"/usr/bin/{n}" if n in ("kicad-cli", "kicad") else orig(n))
```

### 7.2 测试用 Verilog Fixture 文件规格

```verilog
// tests/fixtures/verilog/counter.v
module counter #(parameter WIDTH = 8) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    output reg  [WIDTH-1:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= {WIDTH{1'b0}};
        else if (en) count <= count + 1'b1;
    end
endmodule
```

```verilog
// tests/fixtures/verilog/adder.v
module adder #(parameter WIDTH = 8) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire             cin,
    output wire [WIDTH-1:0] sum,
    output wire             cout
);
    assign {cout, sum} = a + b + cin;
endmodule
```

### 7.3 单元测试规格表

#### Yosys 单元测试

| 测试函数 | 验证点 |
|----------|--------|
| `test_synthesize_input_empty_files` | `verilog_files=[]` 触发 `ValidationError` |
| `test_synthesize_input_timeout_low` | `timeout_s=5` 低于 `ge=10` 触发 `ValidationError` |
| `test_parse_stat_generic` | 正确解析 wire/cell 数量 |
| `test_parse_stat_asic_area` | 解析含 `Chip area` 行 |
| `test_parse_stat_cell_types` | `$dff: 4, $add: 2` 写入 `cell_types` |
| `test_extract_warnings_multiple` | 3 条 Warning 行顺序正确 |
| `test_is_success_nonzero_returncode` | `returncode=1` 返回 False |
| `test_is_success_error_in_stderr` | stderr 含 `ERROR:` 返回 False |
| `test_script_template_asic` | ASIC 脚本含 `dfflibmap` 和 `abc` |
| `test_script_template_ice40` | ice40 脚本含 `synth_ice40` |
| `test_backend_detection_pyosys` | pyosys 可 import 时 BACKEND=pyosys |
| `test_backend_detection_cli` | pyosys 不可用时 BACKEND=yosys-cli |

#### KiCad 单元测试

| 测试函数 | 验证点 |
|----------|--------|
| `test_version_v10_has_ipc` | v10.0.0 具备 `IPC_API` 能力 |
| `test_version_v8_no_ipc` | v8.0.0 无 `IPC_API`，有 `CLI_JOBSETS` |
| `test_version_v7_basic_only` | v7.0.0 仅 `CLI_BASIC` |
| `test_version_invalid_raises` | 非法版本字符串抛出 `ValueError` |
| `test_detect_not_installed` | `which` 返回 None 则 detect 返回 None |
| `test_drc_violation_parsing` | JSON DRC 报告解析为 `DRCViolation` 列表 |
| `test_export_gerber_output_files` | `ExportGerberOutput.files` 包含所有路径 |
| `test_bom_csv_grouping` | `group_by=["Value"]` 正确聚合元件 |

#### Verilog Utils 单元测试

| 测试函数 | 验证点 |
|----------|--------|
| `test_parse_counter_modules` | 解析出 1 个 `counter` 模块 |
| `test_parse_counter_ports` | 含 clk/rst_n/en/count，方向正确 |
| `test_parse_counter_params` | 参数 `WIDTH` 默认值为 `8` |
| `test_parse_syntax_error_file` | syntax_error.v 返回非空 `syntax_errors` |
| `test_hierarchy_no_children` | counter.v 无子模块，children 为空 |
| `test_hierarchy_undefined_module` | 未定义模块出现在 `undefined_modules` |
| `test_lint_w003_blocking_in_seq` | W003 检出时序块中的阻塞赋值 |

### 7.4 集成测试规格

集成测试标记 `@pytest.mark.integration`，CI 中仅在含 EDA 工具的 Docker 环境运行。

| 测试函数 | 前置条件 | 验证点 |
|----------|----------|--------|
| `test_yosys_synthesize_counter` | Yosys 已安装 | counter.v 综合成功，stats.num_cells > 0 |
| `test_yosys_synthesize_adder` | Yosys 已安装 | adder.v 综合成功，output_json 文件存在 |
| `test_yosys_check_syntax_error` | Yosys 已安装 | syntax_error.v check 返回 issues 非空 |
| `test_yosys_stat_counter` | Yosys 已安装 | stat 返回 num_wires > 0 |
| `test_kicad_open_blinky` | kicad-cli v7+ | open_project 返回 schematic_file 路径 |
| `test_kicad_drc_blinky` | kicad-cli v7+ | run_drc 执行成功，report_path 存在 |
| `test_kicad_export_bom` | kicad-cli v7+ | export_bom 生成 CSV，component_count > 0 |
| `test_verilog_parse_skywater_cell` | pyverilog 已安装 | 成功解析 sky130_fd_sc_hd__dfxtp_2.v |

### 7.5 MCP 协议合规性测试

```python
# tests/mcp/test_yosys_mcp_protocol.py
# 使用 mcp Python SDK 直接构造 MCP 请求，验证协议合规性
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.mcp
async def test_yosys_tools_list():
    """tools/list 返回所有注册工具，含完整 inputSchema。"""
    params = StdioServerParameters(
        command="auto-eda-yosys", args=[]
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            assert "synthesize" in tool_names
            assert "stat" in tool_names
            assert "check" in tool_names
            assert "write_netlist" in tool_names
            assert "show_rtl" in tool_names

@pytest.mark.mcp
async def test_yosys_tool_schema_synthesize():
    """synthesize 工具的 inputSchema 包含必要字段。"""
    params = StdioServerParameters(command="auto-eda-yosys", args=[])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            synth = next(t for t in tools.tools if t.name == "synthesize")
            schema = synth.inputSchema
            assert "verilog_files" in schema["properties"]
            assert "verilog_files" in schema["required"]

@pytest.mark.mcp
async def test_yosys_invalid_input_returns_error_text():
    """无效输入返回包含 [ERROR] 的文本，而非 MCP 协议级错误。"""
    params = StdioServerParameters(command="auto-eda-yosys", args=[])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool(
                "synthesize",
                {"verilog_files": [], "output_dir": "/tmp"}
            )
            assert result.content[0].text.startswith("[ERROR")
```

### 7.6 CI 配置

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv pip install -e ".[dev]" --system
      - run: ruff check src tests
      - run: ruff format --check src tests

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv pip install -e ".[dev]" --system
      - run: mypy --strict src/auto_eda

  test-unit:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv pip install -e ".[dev]" --system
      - run: >
          pytest tests/unit tests/mcp
          -m "not integration"
          --cov=src/auto_eda
          --cov-report=xml
          --timeout=60
      - uses: codecov/codecov-action@v4
        with:
          files: coverage.xml

  test-integration:
    runs-on: ubuntu-latest
    # 仅在 main 分支或带 [integration] 标签的 PR 上运行
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'integration')
    container:
      image: ghcr.io/auto-eda/ci-eda-tools:latest  # 预装 Yosys/KiCad/pyverilog
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration -m integration --timeout=300 -v
```

---

## 8. `.mcp.json` 配置模板

### 8.1 Claude Code 标准配置

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "auto-eda-yosys",
      "args": [],
      "env": {
        "AUTO_EDA_LOG_LEVEL": "INFO",
        "AUTO_EDA_YOSYS_TIMEOUT": "300"
      },
      "description": "Yosys RTL synthesis MCP server (synthesize, stat, check, write_netlist, show_rtl)"
    },
    "auto-eda-kicad": {
      "command": "auto-eda-kicad",
      "args": [],
      "env": {
        "AUTO_EDA_LOG_LEVEL": "INFO",
        "AUTO_EDA_KICAD_TIMEOUT": "120"
      },
      "description": "KiCad PCB design MCP server (open_project, list_components, run_drc, run_erc, export_gerber, export_bom, get_netlist)"
    },
    "auto-eda-verilog": {
      "command": "auto-eda-verilog",
      "args": [],
      "env": {
        "AUTO_EDA_LOG_LEVEL": "INFO"
      },
      "description": "Verilog/SV analysis tools (parse_verilog, extract_modules, analyze_hierarchy, lint_check, extract_ports, format_code)"
    }
  }
}
```

### 8.2 uvx 零安装运行配置

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "uvx",
      "args": ["--from", "auto-eda[ic]", "auto-eda-yosys"]
    },
    "auto-eda-kicad": {
      "command": "uvx",
      "args": ["--from", "auto-eda[pcb]", "auto-eda-kicad"]
    },
    "auto-eda-verilog": {
      "command": "uvx",
      "args": ["--from", "auto-eda[ic]", "auto-eda-verilog"]
    }
  }
}
```

### 8.3 Docker 容器运行配置

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "-e", "AUTO_EDA_LOG_LEVEL=INFO",
        "ghcr.io/auto-eda/auto-eda:latest",
        "auto-eda-yosys"
      ]
    },
    "auto-eda-kicad": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "ghcr.io/auto-eda/auto-eda:latest",
        "auto-eda-kicad"
      ]
    }
  }
}
```

### 8.4 项目根目录 `.mcp.json` (开发环境)

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "uv",
      "args": ["run", "auto-eda-yosys"],
      "env": {
        "AUTO_EDA_LOG_LEVEL": "DEBUG",
        "AUTO_EDA_YOSYS_TIMEOUT": "600"
      }
    },
    "auto-eda-kicad": {
      "command": "uv",
      "args": ["run", "auto-eda-kicad"],
      "env": {
        "AUTO_EDA_LOG_LEVEL": "DEBUG"
      }
    },
    "auto-eda-verilog": {
      "command": "uv",
      "args": ["run", "auto-eda-verilog"],
      "env": {
        "AUTO_EDA_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## 9. 错误码与错误消息规范

### 9.1 完整错误码表

| 错误码 | 枚举名 | 触发场景 | 用户可读消息模板 |
|--------|--------|----------|------------------|
| 1001 | `INVALID_INPUT` | Pydantic 验证失败 | `Invalid input: {field} — {reason}` |
| 1002 | `FILE_NOT_FOUND` | 输入文件不存在 | `File not found: {path}` |
| 1003 | `FILE_PERMISSION` | 文件无读取权限 | `Permission denied: {path}` |
| 1004 | `UNSUPPORTED_FORMAT` | 不支持的文件格式 | `Unsupported format: {ext}. Supported: {list}` |
| 1005 | `TIMEOUT` | EDA 工具超时 | `'{tool}' timed out after {n}s. Consider increasing timeout_s.` |
| 2001 | `TOOL_NOT_FOUND` | EDA 工具未安装 | `EDA tool '{tool}' not found. Install it and ensure it is in PATH.` |
| 2002 | `TOOL_VERSION_MISMATCH` | 版本低于最低要求 | `'{tool}' v{found} < minimum required v{min}. Please upgrade.` |
| 3001 | `YOSYS_SYNTHESIS_FAIL` | 综合失败（设计错误） | `Synthesis failed. Check tool_output for Yosys error details.` |
| 3002 | `YOSYS_PARSE_ERROR` | Verilog 解析错误 | `Verilog parse error in {file}. Check syntax.` |
| 3004 | `YOSYS_NO_TOP_MODULE` | 未找到顶层模块 | `Top module '{module}' not found. Available: {list}` |
| 3005 | `YOSYS_TECH_LIB_ERROR` | Liberty 库加载失败 | `Cannot load Liberty library: {path}` |
| 4001 | `KICAD_IPC_CONN_FAIL` | IPC socket 连接失败 | `Cannot connect to KiCad IPC API. Is KiCad running?` |
| 4003 | `KICAD_PROJECT_INVALID` | 工程文件损坏 | `Invalid KiCad project file: {path}` |
| 4005 | `KICAD_VERSION_LOW` | KiCad 版本过低 | `KiCad v{found} is below minimum v{min}. Please upgrade.` |
| 5001 | `VERILOG_SYNTAX_ERROR` | Verilog 语法错误 | `Verilog syntax error: {detail}` |
| 5003 | `VERILOG_PARSE_CRASH` | pyverilog 内部崩溃 | `Verilog parser crashed on {file}. File may use unsupported syntax.` |

### 9.2 错误返回格式

MCP tool 发生错误时返回纯文本（FastMCP 将其包装为 `TextContent`）：

```
[ERROR {code}] {message}
Detail: {detail}
Tool output:
{tool_output 前 2000 字符}
```

示例：
```
[ERROR 3001] Synthesis failed. Check tool_output for Yosys error details.
Detail: Yosys returned exit code 1
Tool output:
3. Executing HIERARCHY pass.
ERROR: Module `undefined_module' referenced in module `counter' in cell `u_undef' is not part of the design.
```

---

## 10. 开发里程碑检查清单

### M0.1: 框架就绪 (Week 2)

- [ ] `pyproject.toml` 配置完整，`uv pip install -e ".[dev]"` 成功
- [ ] `src/auto_eda/core/` 全部模块可 import，mypy --strict 通过
- [ ] `tests/unit/test_errors.py` 全部通过
- [ ] `tests/unit/test_process.py` 全部通过（mock 模式）
- [ ] `tests/unit/test_result.py` 全部通过
- [ ] CI lint + typecheck job 绿色
- [ ] `tests/fixtures/verilog/counter.v` 和 `adder.v` 就绪
- [ ] `tests/fixtures/kicad/blinky/` KiCad 工程就绪

### M0.2: Yosys MCP 可用 (Week 4)

- [ ] `auto-eda-yosys` 命令可启动，MCP stdio 握手成功
- [ ] `tools/list` 返回 synthesize/stat/check/write_netlist/show_rtl
- [ ] 所有工具 inputSchema 正确（通过 `test_yosys_mcp_protocol.py`）
- [ ] `tests/unit/test_yosys_models.py` 全部通过
- [ ] `tests/unit/test_yosys_parser.py` 全部通过
- [ ] `tests/unit/test_yosys_scripts.py` 全部通过
- [ ] Claude Code 可通过 `.mcp.json` 连接 Yosys server
- [ ] 集成测试：`synthesize(counter.v)` 成功（需 Yosys 安装）

### M0.3: KiCad MCP 可用 (Week 6)

- [ ] `auto-eda-kicad` 命令可启动
- [ ] `tools/list` 返回 open_project/list_components/run_drc/run_erc/export_gerber/export_bom/get_netlist
- [ ] `tests/unit/test_kicad_models.py` 全部通过
- [ ] `tests/unit/test_kicad_version.py` 全部通过
- [ ] 集成测试：`run_drc(blinky.kicad_pcb)` 成功（需 kicad-cli 安装）
- [ ] 集成测试：`export_gerber` 生成至少 4 个 Gerber 文件

### M0.4: Verilog Utils 可用 (Week 7)

- [ ] `auto-eda-verilog` 命令可启动
- [ ] `tools/list` 返回 parse_verilog/extract_modules/analyze_hierarchy/lint_check/extract_ports/format_code
- [ ] `tests/unit/test_verilog_models.py` 全部通过
- [ ] `tests/unit/test_verilog_parser.py` 全部通过
- [ ] `parse_verilog(counter.v)` 返回正确模块/端口/参数
- [ ] `lint_check` 检出 W003（测试用含阻塞赋值的 fixture 文件）

### M0.5: MVP 发布 (Week 8)

- [ ] 单元测试覆盖率 >= 80%（`pytest --cov` 验证）
- [ ] 所有 MCP 协议测试通过（`tests/mcp/`）
- [ ] 三个 server 均通过 Claude Code 端到端测试：
  - [ ] 对话："帮我综合这个 counter Verilog" → Yosys synthesize 成功调用
  - [ ] 对话："检查这个 PCB 的 DRC" → KiCad run_drc 成功调用
  - [ ] 对话："分析这个 Verilog 文件的模块层次" → verilog analyze_hierarchy 成功调用
- [ ] `.mcp.json` 模板（3 种形式）就绪
- [ ] README.md 含快速入门指南
- [ ] PyPI 首次发布（0.1.0）

### 验收标准汇总

| 标准 | 目标值 | 测量方法 |
|------|--------|----------|
| 单元测试覆盖率 | >= 80% | `pytest --cov` |
| mypy 严格模式 | 0 错误 | `mypy --strict src/` |
| ruff lint | 0 警告 | `ruff check src/ tests/` |
| MCP 协议合规 | 3/3 server 通过 | MCP Inspector + pytest mcp |
| Yosys 综合基准 | counter/adder/fifo 全通过 | 集成测试 |
| KiCad DRC+Gerber | blinky 工程全通过 | 集成测试 |
| Verilog 解析 | SkyWater PDK 标准单元可解析 | 集成测试 |
| Claude Code 端到端 | 3 种场景全通过 | 手动验证 |

---

## 附录 A: 依赖安装快速参考

```bash
# 开发环境完整安装
git clone https://github.com/auto-eda/auto-eda
cd auto-eda
uv pip install -e ".[dev]"

# EDA 工具安装 (Ubuntu/Debian)
sudo apt-get install -y yosys kicad verilator
pip install pyverilog gdstk

# 验证安装
yosys --version           # >= 0.36
kicad-cli --version       # >= 7.0.0
python -c "import pyverilog; print('pyverilog OK')"
python -c "import gdstk; print('gdstk OK')"

# 运行测试
pytest tests/unit -v                              # 无需 EDA 工具
pytest tests/integration -m integration -v        # 需要 EDA 工具
```

## 附录 B: 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AUTO_EDA_LOG_LEVEL` | `WARNING` | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `AUTO_EDA_YOSYS_BIN` | `yosys` | Yosys 可执行文件路径（覆盖 PATH 搜索）|
| `AUTO_EDA_YOSYS_TIMEOUT` | `300` | Yosys 默认超时秒数 |
| `AUTO_EDA_KICAD_CLI_BIN` | `kicad-cli` | kicad-cli 路径 |
| `AUTO_EDA_KICAD_TIMEOUT` | `120` | KiCad 操作默认超时秒数 |
| `AUTO_EDA_KICAD_IPC_SOCKET` | 自动检测 | KiCad IPC socket 路径（v10+）|
| `AUTO_EDA_DISABLE_PYOSYS` | `0` | 设为 `1` 强制使用 CLI 后端 |
