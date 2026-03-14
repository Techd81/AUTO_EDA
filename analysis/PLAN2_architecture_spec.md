# PLAN2: AUTO_EDA 代码架构与项目结构规范

> 文档版本: 0.1.0
> 日期: 2026-03-14
> 作者: 架构规划团队
> 前置文档: DA1_architecture_deep_design.md · DA3_phase0_implementation_spec.md · A7_tech_stack_decision.md · NEW_R3_mcp_quality_guide.md
> 状态: 规范文档 — 开发基准

---

## 目录

1. [最终项目目录结构](#1-最终项目目录结构)
2. [核心模块接口规范](#2-核心模块接口规范)
3. [Pydantic 模型设计规范](#3-pydantic-模型设计规范)
4. [MCP Tool 命名和组织规范](#4-mcp-tool-命名和组织规范)
5. [测试架构规范](#5-测试架构规范)
6. [配置管理设计](#6-配置管理设计)
7. [版本和兼容性策略](#7-版本和兼容性策略)

---

## 1. 最终项目目录结构

### 1.1 完整目录树

```
auto-eda/                                   # 项目根目录
├── pyproject.toml                          # 项目元数据、依赖声明、工具配置（hatchling 后端）
├── README.md                               # 项目说明、快速上手
├── CHANGELOG.md                            # 版本变更记录（Keep a Changelog 格式）
├── LICENSE                                 # MIT 许可证
├── .mcp.json                               # Claude Code MCP 集成配置（本地开发用）
├── .env.example                            # 环境变量示例（不含敏感值）
├── .pre-commit-config.yaml                 # Git 钩子：ruff + mypy
│
├── .github/
│   └── workflows/
│       ├── ci.yml                          # 基础 CI：lint + typecheck + unit tests
│       └── integration.yml                 # 集成测试（需 Docker EDA 环境）
│
├── docker/
│   ├── Dockerfile                          # 生产镜像（多阶段构建）
│   ├── Dockerfile.dev                      # 开发镜像（含调试工具）
│   └── docker-compose.yml                  # 本地多服务联调
│
├── scripts/
│   ├── install_eda_tools.sh                # Linux/CI EDA 工具安装脚本
│   ├── check_dependencies.py               # 运行前依赖检查（打印缺失项）
│   └── generate_mcp_json.py               # 从 pyproject.toml 生成 .mcp.json
│
├── src/
│   └── auto_eda/
│       ├── __init__.py                     # 包版本 (__version__)、公共导出
│       ├── __main__.py                     # `python -m auto_eda --server yosys` 入口
│       │
│       ├── core/                           # 共享基础层（无 EDA 工具依赖）
│       │   ├── __init__.py
│       │   ├── base_server.py              # BaseEDAServer 抽象基类
│       │   ├── errors.py                   # EDAError 异常层次 + 错误码枚举
│       │   ├── process.py                  # EDAProcessRunner 子进程管理
│       │   ├── progress.py                 # ProgressReporter（MCP Context 封装）
│       │   ├── registry.py                 # ToolRegistry（工具元数据注册）
│       │   └── result.py                   # ToolResult 序列化辅助
│       │
│       ├── models/                         # 跨 Server 共享 Pydantic 模型
│       │   ├── __init__.py
│       │   ├── base.py                     # EDABaseModel、FilePathStr、带验证的基类
│       │   ├── common.py                   # 通用数据结构（TimingConstraint 等）
│       │   ├── yosys.py                    # Yosys 工具 I/O 模型
│       │   ├── kicad.py                    # KiCad 工具 I/O 模型
│       │   ├── verilog.py                  # Verilog 工具 I/O 模型
│       │   ├── openroad.py                 # OpenROAD 工具 I/O 模型（Phase 1）
│       │   └── klayout.py                  # KLayout 工具 I/O 模型（Phase 1）
│       │
│       └── servers/                        # 各 MCP Server 实现
│           ├── __init__.py
│           │
│           ├── yosys/                      # Yosys MCP Server（Phase 0）
│           │   ├── __init__.py             # main() 入口
│           │   ├── server.py               # YosysServer(BaseEDAServer)，注册全部工具
│           │   ├── synthesizer.py          # 综合逻辑：Pyosys API 优先，CLI 回退
│           │   ├── netlist.py              # 网表读写：read_verilog, write_json/blif
│           │   ├── reporter.py             # 综合报告解析：parse_stat, parse_timing
│           │   └── scripts.py              # TCL 脚本模板（综合、优化、映射）
│           │
│           ├── kicad/                      # KiCad MCP Server（Phase 0）
│           │   ├── __init__.py
│           │   ├── server.py               # KiCadServer(BaseEDAServer)
│           │   ├── ipc_client.py           # KiCad IPC API 连接管理（Protobuf）
│           │   ├── cli_fallback.py         # kicad-cli Jobsets 回退实现
│           │   └── version.py              # KiCad 版本检测与兼容层
│           │
│           ├── verilog_utils/              # Verilog Utils MCP Server（Phase 0）
│           │   ├── __init__.py
│           │   ├── server.py               # VerilogUtilsServer(BaseEDAServer)
│           │   ├── parser.py               # pyverilog 封装，AST 提取
│           │   └── linter.py               # Verilog lint 规则实现
│           │
│           ├── openroad/                   # OpenROAD MCP Server（Phase 1）
│           │   ├── __init__.py
│           │   ├── server.py
│           │   ├── floorplan.py
│           │   ├── placement.py
│           │   ├── routing.py
│           │   └── reporter.py
│           │
│           ├── klayout/                    # KLayout MCP Server（Phase 1）
│           │   ├── __init__.py
│           │   ├── server.py
│           │   ├── viewer.py               # 版图截图与预览
│           │   ├── drc.py                  # DRC/LVS 运行
│           │   └── gds_ops.py              # GDSII 操作（读写、层操作）
│           │
│           ├── simulation/                 # 仿真 MCP Server（Phase 1）
│           │   ├── __init__.py
│           │   ├── server.py
│           │   ├── cocotb_runner.py        # cocotb 测试执行
│           │   ├── verilator_runner.py     # Verilator 仿真
│           │   └── waveform.py             # VCD/FST 波形解析与可视化
│           │
│           └── orchestrator/               # 跨工具编排 Server（Phase 2）
│               ├── __init__.py
│               ├── server.py
│               ├── pipeline.py             # DAG 工作流定义与执行
│               └── templates/              # 预置工作流模板
│                   ├── rtl_to_netlist.py
│                   └── rtl_to_gdsii.py
│
├── tests/
│   ├── conftest.py                         # 全局 fixtures（tmp_path 工厂、mock 工厂）
│   ├── fixtures/
│   │   ├── verilog/                        # 测试用 Verilog 源文件
│   │   │   ├── counter.v                   # 简单计数器（基础测试）
│   │   │   ├── adder.v                     # 组合逻辑（快速综合）
│   │   │   ├── fifo.v                      # 时序逻辑（综合回归）
│   │   │   └── syntax_error.v              # 语法错误（错误处理测试）
│   │   ├── kicad/
│   │   │   └── blinky/                     # 最小 KiCad 工程（LED 闪烁电路）
│   │   │       ├── blinky.kicad_pro
│   │   │       ├── blinky.kicad_sch
│   │   │       └── blinky.kicad_pcb
│   │   └── yosys/
│   │       ├── counter_synth.json          # 预生成综合 JSON 网表
│   │       └── counter_stat.txt            # 预生成 stat 报告
│   │
│   ├── unit/                               # 纯逻辑单元测试（无 EDA 工具）
│   │   ├── core/
│   │   │   ├── test_errors.py
│   │   │   ├── test_process.py
│   │   │   └── test_result.py
│   │   ├── models/
│   │   │   ├── test_base_models.py
│   │   │   ├── test_yosys_models.py
│   │   │   ├── test_kicad_models.py
│   │   │   └── test_verilog_models.py
│   │   └── servers/
│   │       ├── test_yosys_parser.py        # 解析逻辑（用 fixtures/ 预生成输出）
│   │       ├── test_yosys_scripts.py
│   │       ├── test_kicad_version.py
│   │       └── test_verilog_parser.py
│   │
│   ├── integration/                        # 需 EDA 工具已安装（CI Docker）
│   │   ├── test_yosys_server.py
│   │   ├── test_kicad_server.py
│   │   └── test_verilog_utils.py
│   │
│   └── mcp/                                # MCP 协议合规性测试
│       ├── test_yosys_mcp_protocol.py
│       ├── test_kicad_mcp_protocol.py
│       └── test_verilog_mcp_protocol.py
│
└── docs/                                   # 开发者文档（非用户文档）
    ├── architecture.md                     # 架构决策记录（ADR）
    ├── adding_new_server.md                # 新增 MCP Server 操作手册
    └── eda_tool_setup.md                   # EDA 工具安装说明
```

### 1.2 模块职责边界（禁止清单）

| 模块 | 职责 | 严禁 |
|------|------|------|
| `core/errors.py` | 错误码枚举、异常类定义 | 不得引用任何 EDA 库 |
| `core/process.py` | 子进程启动、超时、流捕获 | 不得解析 EDA 特定输出 |
| `core/base_server.py` | 基类骨架、内建工具注册 | 不得包含 EDA 业务逻辑 |
| `models/*.py` | Pydantic 输入/输出模型定义 | 不得包含执行逻辑 |
| `servers/*/server.py` | MCP tool/resource/prompt 注册 | 不得直接调用 EDA 工具 |
| `servers/*/synthesizer.py` 等 | EDA 工具调用与结果处理 | 不得直接处理 MCP 协议 |

---

## 2. 核心模块接口规范

### 2.1 `base_server.py` — BaseEDAServer 完整接口

```python
# src/auto_eda/core/base_server.py
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from .errors import EDAErrorCode
from .progress import ProgressReporter
from .registry import ToolRegistry


class ServerConfig(BaseModel):
    """每个 EDA Server 的静态配置，子类以 ClassVar[ServerConfig] 覆盖。"""
    server_name: str                    # MCP 协议中的服务器标识名
    server_version: str                 # 语义版本号，与包版本一致
    domain: str                         # "pcb" | "digital_ic" | "simulation" | "layout"
    description: str                    # 面向 LLM 的服务器功能描述
    required_tools: list[str]           # 启动时检测的系统二进制名（如 "yosys"）
    optional_tools: list[str] = []      # 可选二进制（不影响启动，影响功能可用性）
    min_python: tuple[int, int] = (3, 10)    # 最低 Python 版本要求


class BaseEDAServer(ABC):
    """
    所有 AUTO_EDA MCP Server 的公共抽象基类。

    继承规则：
    1. 子类必须定义 CONFIG: ClassVar[ServerConfig]
    2. 子类必须实现 register_tools() 方法
    3. 子类不得覆盖 __init__、run、_register_builtin_tools

    内建工具（每个 Server 自动拥有）：
    - health_check() -> dict  检查服务器状态与工具可用性
    """

    CONFIG: ClassVar[ServerConfig]

    def __init__(self) -> None:
        self.mcp: FastMCP = FastMCP(
            self.CONFIG.server_name,
            version=self.CONFIG.server_version,
            instructions=self.CONFIG.description,
        )
        self.logger: logging.Logger = logging.getLogger(self.CONFIG.server_name)
        self.progress: ProgressReporter = ProgressReporter()
        self.registry: ToolRegistry = ToolRegistry()
        self._register_builtin_tools()
        self.register_tools()

    def _register_builtin_tools(self) -> None:
        @self.mcp.tool(description="检查 EDA Server 状态和工具可用性")
        def health_check() -> dict[str, Any]:
            return {
                "server": self.CONFIG.server_name,
                "version": self.CONFIG.server_version,
                "domain": self.CONFIG.domain,
                "tools_available": self.registry.check_required(self.CONFIG.required_tools),
                "optional_tools": self.registry.check_required(self.CONFIG.optional_tools),
                "registered_mcp_tools": self.registry.list_names(),
            }

    @abstractmethod
    def register_tools(self) -> None:
        ...

    def run(self, transport: str = "stdio") -> None:
        self.mcp.run(transport=transport)

    @classmethod
    def create_and_run(cls, transport: str = "stdio") -> None:
        cls().run(transport=transport)
```

**子类实现模式（YosysServer）：**

```python
class YosysServer(BaseEDAServer):
    CONFIG = ServerConfig(
        server_name="auto-eda-yosys",
        server_version="0.1.0",
        domain="digital_ic",
        description="Yosys RTL synthesis server. Synthesizes Verilog to gate-level netlist.",
        required_tools=["yosys"],
    )

    def register_tools(self) -> None:
        @self.mcp.tool(description="将 Verilog RTL 综合为门级网表")
        async def synthesize_rtl(params: SynthesizeInput) -> str:
            from .synthesizer import run_synthesis
            result = await run_synthesis(params, self.progress)
            return result.model_dump_json(indent=2)
```

### 2.2 `errors.py` — 错误层次结构与错误码体系

```
EDAErrorCode (IntEnum)
├── 通用错误 1xxx
│   ├── 1000  UNKNOWN
│   ├── 1001  INVALID_INPUT
│   ├── 1002  FILE_NOT_FOUND
│   ├── 1003  FILE_PERMISSION
│   ├── 1004  UNSUPPORTED_FORMAT
│   ├── 1005  TIMEOUT
│   └── 1006  CANCELLED
├── 环境错误 2xxx
│   ├── 2001  TOOL_NOT_FOUND
│   ├── 2002  TOOL_VERSION_MISMATCH
│   ├── 2003  TOOL_LICENSE_ERROR
│   └── 2004  DEPENDENCY_MISSING
├── Yosys 错误 3xxx
│   ├── 3001  YOSYS_SYNTHESIS_FAIL
│   ├── 3002  YOSYS_PARSE_ERROR
│   ├── 3003  YOSYS_SCRIPT_ERROR
│   ├── 3004  YOSYS_NO_TOP_MODULE
│   └── 3005  YOSYS_TECH_LIB_ERROR
├── KiCad 错误 4xxx
│   ├── 4001  KICAD_IPC_CONN_FAIL
│   ├── 4002  KICAD_IPC_TIMEOUT
│   ├── 4003  KICAD_PROJECT_INVALID
│   ├── 4004  KICAD_DRC_ERROR
│   ├── 4005  KICAD_VERSION_LOW
│   └── 4006  KICAD_NOT_RUNNING
├── Verilog 解析错误 5xxx
│   ├── 5001  VERILOG_SYNTAX_ERROR
│   ├── 5002  VERILOG_INCLUDE_ERROR
│   └── 5003  VERILOG_PARSE_CRASH
├── OpenROAD 错误 6xxx（Phase 1 预留）
│   ├── 6001  OPENROAD_FLOORPLAN_FAIL
│   ├── 6002  OPENROAD_PLACE_FAIL
│   └── 6003  OPENROAD_ROUTE_FAIL
└── KLayout 错误 7xxx（Phase 1 预留）
    ├── 7001  KLAYOUT_DRC_FAIL
    └── 7002  KLAYOUT_GDS_CORRUPT
```

#### 异常类层次

```python
class EDAError(Exception):
    """
    所有 AUTO_EDA 异常的根基类。
    属性:
      code        EDAErrorCode
      message     str          — 面向 LLM 的简洁描述
      detail      str | None   — 操作建议或详细说明
      tool_output str | None   — EDA 工具原始 stderr（截断 2000 字符）
    """
    def to_mcp_error_text(self) -> str:
        """
        四要素格式:
          [ERROR {code}] {message}
          Detail: {detail}
          Suggestion: {suggestion}
          Tool output:\n{tool_output[:2000]}
        """

class ToolNotFoundError(EDAError): ...        # code=2001
class ToolVersionError(EDAError): ...         # code=2002
class DependencyMissingError(EDAError): ...   # code=2004
class ToolTimeoutError(EDAError): ...         # code=1005
class FileNotFoundEDAError(EDAError): ...     # code=1002
class UnsupportedFormatError(EDAError): ...   # code=1004
class YosysSynthesisError(EDAError): ...      # code=3001
class YosysParseError(EDAError): ...          # code=3002
class KiCadIPCError(EDAError): ...            # code=4001
class KiCadNotRunningError(EDAError): ...     # code=4006
class VerilogSyntaxError(EDAError): ...       # code=5001
```

#### MCP 错误转换规则

所有 MCP tool handler 必须遵循统一转换模式：

```python
try:
    result = await do_eda_work(params)
except EDAError as e:
    raise ToolError(e.to_mcp_error_text()) from None
except Exception as e:
    await ctx.error(f"Unexpected: {e}")
    raise ToolError("Internal server error. Check server logs.") from None
```

### 2.3 `process.py` — EDA 进程管理器接口

```python
@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    elapsed_s: float

    @property
    def success(self) -> bool:
        return self.returncode == 0


class EDAProcessRunner:
    """
    异步 EDA 子进程管理器。
    职责：启动子进程、超时控制、流式捕获、进度关键字匹配、env 隔离。
    不包含：任何 EDA 工具特定输出解析逻辑。
    """
    DEFAULT_TIMEOUT_SHORT: ClassVar[int] = 30
    DEFAULT_TIMEOUT_LONG: ClassVar[int] = 300
    MAX_OUTPUT_LINES: ClassVar[int] = 10_000

    async def run(
        self,
        cmd: list[str],
        *,
        cwd: Path | None = None,
        env_extra: dict[str, str] | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_SHORT,
        input_text: str | None = None,
    ) -> ProcessResult:
        """同步等待完成。适用于短时任务（<30s）。"""
        ...

    async def run_streaming(
        self,
        cmd: list[str],
        *,
        cwd: Path | None = None,
        env_extra: dict[str, str] | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_LONG,
        progress_keywords: dict[str, str] | None = None,
        progress_reporter: ProgressReporter | None = None,
        task_id: str | None = None,
    ) -> ProcessResult:
        """
        流式执行，实时匹配关键字推进进度。适用于长时任务（>30s）。
        progress_keywords: {关键字: 人类可读描述}
        例: {"Synthesis complete": "综合完成", "Running ABC": "逻辑优化中"}
        """
        ...

    @staticmethod
    def find_binary(name: str) -> Path | None:
        """在 PATH 中查找 EDA 工具二进制，返回绝对路径或 None。"""
        ...
```

**超时策略表：**

| 任务类型 | 环境变量 | 默认值 |
|----------|---------|--------|
| 短时（lint / parse / format） | `AUTOEDA_TIMEOUT_SHORT` | 30s |
| 中时（小型综合 / DRC） | `AUTOEDA_TIMEOUT_MEDIUM` | 120s |
| 长时（综合 / P&R / 仿真） | `AUTOEDA_TIMEOUT_LONG` | 300s |
| 超长时（全流程 / 大设计） | `AUTOEDA_TIMEOUT_EXTRA` | 1800s |

---

## 3. Pydantic 模型设计规范

### 3.1 通用模型基类

```python
# src/auto_eda/models/base.py
from pydantic import BaseModel, ConfigDict

class EDABaseModel(BaseModel):
    """
    所有 AUTO_EDA Pydantic 模型根基类。
    - extra='forbid'            拒绝未声明字段（防 LLM 幻觉字段）
    - validate_assignment=True  赋值时触发验证
    - str_strip_whitespace=True 自动去除字符串首尾空白
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

class EDAInputModel(EDABaseModel):
    """
    MCP tool 输入模型基类。
    命名规范: {Domain}{Action}Input
    例: SynthesizeRtlInput, RunDrcInput, ParseVerilogInput
    """

class EDAOutputModel(EDABaseModel):
    """
    MCP tool 输出模型基类。
    命名规范: {Domain}{Action}Output
    序列化: model.model_dump_json(indent=2) 作为 tool 返回字符串。
    """
```

### 3.2 文件路径验证模式

```python
# 类型别名：验证文件必须存在
ExistingFilePath = Annotated[str, Field(description="文件的绝对路径，文件必须存在")]

# 类型别名：验证目录必须存在
ExistingDirPath = Annotated[str, Field(description="目录的绝对路径，目录必须存在")]

# 类型别名：输出路径（父目录必须存在，文件本身可不存在）
OutputFilePath = Annotated[str, Field(description="输出文件的绝对路径")]
```

路径字段统一使用 `@field_validator` 进行 `Path(v).exists()` 检查，不接受相对路径。

**路径字段验证规则：**
1. 必须是绝对路径（`Path(v).is_absolute()` 为 True）
2. `ExistingFilePath` 必须通过 `Path(v).is_file()` 检查
3. `ExistingDirPath` 必须通过 `Path(v).is_dir()` 检查
4. `OutputFilePath` 仅检查父目录存在
5. 验证失败抛出 `ValueError`，Pydantic 自动转为 422 类错误返回 LLM

### 3.3 EDA 工具结果模型基类

```python
# src/auto_eda/models/common.py
class EDAToolResultBase(EDAOutputModel):
    """
    所有 EDA 工具执行结果的共同字段。
    """
    success: bool                        # 工具是否成功退出
    tool_name: str                       # EDA 工具名称（如 "yosys"）
    tool_version: str | None = None      # 工具版本（如 "0.40"）
    elapsed_s: float                     # 执行耗时（秒）
    warnings: list[str] = []             # 工具产生的警告列表
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

# 示例：Yosys 综合结果继承
class SynthesizeRtlOutput(EDAToolResultBase):
    netlist_path: str
    netlist_format: Literal["json", "blif", "edif", "verilog"]
    top_module: str
    num_cells: int
    num_wires: int
    cell_breakdown: dict[str, int]
    critical_path_ns: float | None = None
    area_um2: float | None = None
```

### 3.4 命名约定总表

| 类型 | 命名模式 | 示例 |
|------|---------|------|
| 输入模型 | `{Domain}{Action}Input` | `SynthesizeRtlInput`, `RunDrcInput` |
| 输出模型 | `{Domain}{Action}Output` | `SynthesizeRtlOutput`, `RunDrcOutput` |
| 枚举 | `{Domain}{Concept}` | `NetlistFormat`, `DrcSeverity` |
| 通用数据结构 | 名词短语 | `TimingConstraint`, `DrcViolation` |
| 跨 Server 传输 | `{Source}To{Dest}Result` | `YosysToOpenRoadResult` |

**字段命名规则：**
- 使用 `snake_case`
- 路径字段以 `_path` 结尾（如 `netlist_path`）
- 布尔字段以动词开头（如 `include_timing`、`enable_optimization`）
- 列表字段使用复数（如 `warnings`、`violations`）
- 时间字段以 `_s` 结尾表示秒，`_ns` 表示纳秒，`_ms` 表示毫秒

---

## 4. MCP Tool 命名和组织规范

### 4.1 命名规则

**格式：** `{动词}_{名词}[_{修饰语}]`

所有名称使用 `snake_case`，长度 1-64 字符，仅字母数字和下划线，同一 Server 内唯一。

**允许的动词前缀：**

| 动词 | 语义 | 典型场景 |
|------|------|----------|
| `synthesize_` | 综合/生成 | RTL 综合、报告生成 |
| `analyze_` | 分析（只读） | 设计分析、时序分析 |
| `run_` | 执行流程 | DRC、仿真、lint |
| `parse_` | 解析文件 | Verilog 解析、网表解析 |
| `get_` | 获取单项 | 获取统计、获取版本 |
| `list_` | 列举多项 | 列举模块、列举违规 |
| `export_` | 导出文件 | 导出 GDSII、导出报告 |
| `import_` | 导入文件 | 导入网表、导入约束 |
| `generate_` | 生成产物 | 生成脚本、生成文档 |
| `check_` | 检查/验证 | 检查语法、检查兼容性 |
| `open_` | 打开资源 | 打开工程、打开设计 |
| `close_` | 关闭资源 | 关闭连接 |

### 4.2 工具命名示例表（20 条）

| 工具名 | Server | 功能描述 |
|--------|--------|----------|
| `synthesize_rtl` | yosys | Verilog RTL 综合为门级网表 |
| `analyze_design_stats` | yosys | 分析综合后设计统计（面积/时序）|
| `parse_verilog_ast` | verilog_utils | 解析 Verilog 文件返回 AST 摘要 |
| `check_verilog_syntax` | verilog_utils | 语法检查，返回错误和警告列表 |
| `list_verilog_modules` | verilog_utils | 列举 Verilog 文件中的所有模块 |
| `get_module_ports` | verilog_utils | 获取指定模块的端口列表 |
| `run_drc` | kicad | 运行 PCB 设计规则检查 |
| `export_gerber` | kicad | 导出 Gerber 制造文件 |
| `get_board_statistics` | kicad | 获取 PCB 板级统计（面积/器件数）|
| `list_schematic_components` | kicad | 列举原理图中的所有元件 |
| `check_erc` | kicad | 运行原理图电气规则检查 |
| `open_kicad_project` | kicad | 通过 IPC API 打开 KiCad 工程 |
| `run_floorplan` | openroad | 执行布图规划 |
| `run_placement` | openroad | 执行标准单元布局 |
| `run_routing` | openroad | 执行全局+详细布线 |
| `get_timing_report` | openroad | 获取时序分析报告（WNS/TNS）|
| `run_klayout_drc` | klayout | 使用 KLayout 运行 DRC |
| `export_layout_screenshot` | klayout | 导出版图截图（PNG）|
| `run_cocotb_test` | simulation | 执行 cocotb 验证测试套件 |
| `parse_vcd_waveform` | simulation | 解析 VCD 波形文件提取信号 |

### 4.3 工具分组策略

每个 MCP Server 的工具数量控制在 **5-15 个**（依据 NEW_R3 最佳实践）。超过 15 个时，按功能子域拆分为独立 Server 或使用 FastMCP `mount()` 组合。

**分组原则：**
1. 同一 Server 内工具共享同一 EDA 工具依赖（如都依赖 `yosys` 二进制）
2. 原子操作（细粒度）与高层工作流（粗粒度）可在同一 Server 共存
3. 跨工具编排逻辑归属 `orchestrator` Server，不放入领域 Server

### 4.4 Resource 命名规范

格式：`{scheme}://{path-template}`

| URI 模式 | 说明 | 示例 |
|---------|------|------|
| `eda://servers` | 已注册服务器列表 | `eda://servers` |
| `eda://{server}/tools` | Server 工具列表 | `eda://yosys/tools` |
| `design://{project_id}` | 设计工程状态 | `design://my_chip` |
| `design://{project_id}/netlist` | 网表文件 | `design://my_chip/netlist` |
| `config://env` | 当前环境配置 | `config://env` |
| `config://tool-paths` | EDA 工具路径 | `config://tool-paths` |

### 4.5 Prompt 模板命名规范

格式：`{domain}_{workflow}_{variant?}`

| Prompt 名 | 说明 |
|-----------|------|
| `rtl_synthesis_guided` | 引导式 RTL 综合工作流 |
| `pcb_drc_fix_loop` | PCB DRC 发现-修复循环 |
| `verilog_debug_syntax` | Verilog 语法错误调试 |
| `ic_full_flow_rtl_to_gds` | RTL 到 GDSII 全流程 |
| `sim_cocotb_setup` | cocotb 测试环境搭建 |

---

## 5. 测试架构规范

### 5.1 测试目录结构

```
tests/
├── conftest.py              # 全局 fixtures（所有层共享）
├── fixtures/                # 静态测试数据（版本控制追踪）
│   ├── verilog/
│   ├── kicad/
│   └── yosys/
├── unit/                    # 标记: @pytest.mark.unit
│   ├── core/
│   ├── models/
│   └── servers/
├── integration/             # 标记: @pytest.mark.integration
│   ├── test_yosys_server.py
│   ├── test_kicad_server.py
│   └── test_verilog_utils.py
└── mcp/                     # 标记: @pytest.mark.mcp
    ├── test_yosys_mcp_protocol.py
    ├── test_kicad_mcp_protocol.py
    └── test_verilog_mcp_protocol.py
```

### 5.2 Fixture 复用策略

```python
# tests/conftest.py
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ── 文件路径 fixtures（所有层复用）──
@pytest.fixture(scope="session")
def counter_v() -> Path:
    return FIXTURES_DIR / "verilog" / "counter.v"

@pytest.fixture(scope="session")
def counter_synth_json() -> Path:
    return FIXTURES_DIR / "yosys" / "counter_synth.json"

@pytest.fixture(scope="session")
def blinky_project_dir() -> Path:
    return FIXTURES_DIR / "kicad" / "blinky"

# ── 进程 mock（unit 层专用）──
@pytest.fixture
def mock_process_runner(mocker):
    runner = AsyncMock()
    runner.run.return_value = MagicMock(
        returncode=0, stdout="", stderr="", elapsed_s=0.1, success=True
    )
    return runner

# ── FastMCP 测试客户端（mcp 层专用）──
@pytest.fixture
async def yosys_mcp_client():
    from fastmcp import Client
    from auto_eda.servers.yosys.server import YosysServer
    server = YosysServer()
    async with Client(server.mcp) as client:
        yield client
```

### 5.3 Mock 边界定义

| 测试层 | Mock 边界 | 不 Mock 的部分 |
|--------|----------|----------------|
| `unit/` | `EDAProcessRunner.run`、`EDAProcessRunner.run_streaming`、文件系统（用 `tmp_path`）| Pydantic 验证、错误类逻辑、解析函数 |
| `integration/` | 无（使用真实 EDA 工具）| 全部真实执行 |
| `mcp/` | `EDAProcessRunner`（返回预设 ProcessResult）| MCP 协议层、参数验证、序列化 |

**Mock 原则：**
- 只 mock 外部边界（系统进程、网络、文件系统），不 mock 被测逻辑本身
- 使用 `fixtures/` 中的预生成输出文件替代真实 EDA 工具调用（unit 层）
- Integration 测试用 `@pytest.mark.integration` 标记，CI 中按条件跳过

### 5.4 测试命名规范

格式：`test_{功能描述}_{场景/条件}`

```python
# 好的命名
def test_synthesize_rtl_returns_valid_json_on_success()
def test_synthesize_rtl_raises_tool_error_when_yosys_missing()
def test_parse_verilog_returns_module_list_for_multi_module_file()
def test_run_drc_raises_kicad_not_running_when_ipc_unavailable()
def test_health_check_reports_tool_unavailable_when_binary_missing()

# 不好的命名
def test_synth()                    # 太模糊
def test_error()                    # 不知道测什么错误
def test_kicad_1()                  # 无意义编号
```

**规则：**
- 测试文件：`test_{模块名}.py`
- 测试函数：`test_{功能}_{场景}`，使用完整英文描述
- 参数化测试使用 `ids=` 提供可读名称

---

## 6. 配置管理设计

### 6.1 环境变量 Schema

所有环境变量以 `AUTOEDA_` 为前缀，通过 `pydantic-settings` 的 `BaseSettings` 加载和验证。

```python
# src/auto_eda/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AutoEDASettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AUTOEDA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # EDA 工具路径（覆盖 PATH 自动发现，留空则自动发现）
    yosys_path: str = Field(default="")
    kicad_path: str = Field(default="")
    openroad_path: str = Field(default="")
    klayout_path: str = Field(default="")
    verilator_path: str = Field(default="")
    ngspice_path: str = Field(default="")

    # 超时配置（秒）
    timeout_short: int = Field(default=30, ge=5, le=300)
    timeout_medium: int = Field(default=120, ge=30, le=600)
    timeout_long: int = Field(default=300, ge=60, le=3600)
    timeout_extra: int = Field(default=1800, ge=300, le=86400)

    # KiCad IPC 配置
    kicad_ipc_host: str = Field(default="localhost")
    kicad_ipc_port: int = Field(default=8765, ge=1024, le=65535)
    kicad_ipc_timeout: int = Field(default=30, ge=5, le=120)

    # 日志配置
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_format: str = Field(default="json", pattern="^(json|text)$")

    # 工作目录（空则使用系统 tmpdir）
    work_dir: str = Field(default="")
```

### 6.2 `.env` 文件规范

```bash
# .env.example — 复制为 .env 并根据本机环境修改
# .env 已加入 .gitignore，不提交到版本控制

# EDA 工具路径（留空则从 PATH 自动发现）
AUTOEDA_YOSYS_PATH=
AUTOEDA_KICAD_PATH=
AUTOEDA_OPENROAD_PATH=
AUTOEDA_KLAYOUT_PATH=
AUTOEDA_VERILATOR_PATH=
AUTOEDA_NGSPICE_PATH=

# 超时配置（秒）
AUTOEDA_TIMEOUT_SHORT=30
AUTOEDA_TIMEOUT_MEDIUM=120
AUTOEDA_TIMEOUT_LONG=300
AUTOEDA_TIMEOUT_EXTRA=1800

# KiCad IPC（仅 KiCad Server 需要）
AUTOEDA_KICAD_IPC_HOST=localhost
AUTOEDA_KICAD_IPC_PORT=8765
AUTOEDA_KICAD_IPC_TIMEOUT=30

# 日志
AUTOEDA_LOG_LEVEL=INFO
AUTOEDA_LOG_FORMAT=json
```

### 6.3 `.mcp.json` 完整模板

```json
{
  "mcpServers": {
    "auto-eda-yosys": {
      "command": "uv",
      "args": ["run", "auto-eda-yosys"],
      "env": {
        "AUTOEDA_LOG_LEVEL": "INFO",
        "AUTOEDA_TIMEOUT_LONG": "300"
      },
      "description": "Yosys RTL synthesis server (Verilog to netlist)"
    },
    "auto-eda-kicad": {
      "command": "uv",
      "args": ["run", "auto-eda-kicad"],
      "env": {
        "AUTOEDA_LOG_LEVEL": "INFO",
        "AUTOEDA_KICAD_IPC_HOST": "localhost",
        "AUTOEDA_KICAD_IPC_PORT": "8765"
      },
      "description": "KiCad PCB design server (schematic, layout, DRC, Gerber)"
    },
    "auto-eda-verilog": {
      "command": "uv",
      "args": ["run", "auto-eda-verilog"],
      "env": {
        "AUTOEDA_LOG_LEVEL": "INFO"
      },
      "description": "Verilog utilities server (parse, lint, module analysis)"
    }
  }
}
```

**使用说明：**
- 开发时放于项目根目录，Claude Code 自动发现
- 生产时放于 `~/.claude/` 实现全局注册
- `uv run` 自动使用项目虚拟环境，无需手动激活
- 不使用 `uv` 时：`command: "python"`, `args: ["-m", "auto_eda.servers.yosys"]`

### 6.4 工具路径发现策略

```
优先级（从高到低）：
1. 环境变量 AUTOEDA_{TOOL}_PATH 明确指定
2. .env 文件中的对应变量
3. shutil.which(tool_name) — PATH 自动发现
4. 常见安装路径探测: /usr/bin, /usr/local/bin, /opt/homebrew/bin, /snap/bin
5. 未找到 -> ToolNotFoundError (code=2001)
```

```python
def discover_tool_path(tool_name: str, settings: AutoEDASettings) -> Path:
    explicit = getattr(settings, f"{tool_name}_path", "")
    if explicit and Path(explicit).is_file():
        return Path(explicit)
    found = shutil.which(tool_name)
    if found:
        return Path(found)
    for candidate in [Path("/usr/bin"), Path("/usr/local/bin"),
                      Path("/opt/homebrew/bin"), Path("/snap/bin")]:
        p = candidate / tool_name
        if p.is_file():
            return p
    raise ToolNotFoundError(tool_name)
```

---

## 7. 版本和兼容性策略

### 7.1 Semver 规范

遵循 [Semantic Versioning 2.0.0](https://semver.org/)：`MAJOR.MINOR.PATCH`

| 版本段 | 触发条件 |
|--------|----------|
| `MAJOR` | 破坏性变更（tool 接口不兼容、移除工具、参数重命名、错误码变更） |
| `MINOR` | 向后兼容的功能新增（新增工具、新增可选参数、新增 Server） |
| `PATCH` | 向后兼容的 bug 修复、内部重构、文档更新 |

**Phase 0 特殊规则：** `0.x.x` 阶段 MINOR 版本可含破坏性变更（pre-stable），但必须在 CHANGELOG 中加 `**BREAKING:**` 标注。

包版本统一在 `pyproject.toml` 的 `[project] version` 字段维护，各 Server 的 `CONFIG.server_version` 与之保持一致。

### 7.2 CHANGELOG 维护格式

遵循 [Keep a Changelog](https://keepachangelog.com/) 格式：

```markdown
# Changelog

## [Unreleased]
### Added
### Changed
### Fixed
### Deprecated
### Removed
### Security

## [0.1.0] - 2026-03-15
### Added
- Yosys MCP Server: synthesize_rtl, analyze_design_stats, get_cell_library_info
- KiCad MCP Server: run_drc, export_gerber, get_board_statistics
- Verilog Utils MCP Server: parse_verilog_ast, check_verilog_syntax, list_verilog_modules
- BaseEDAServer 基类框架
- EDAError 错误体系（错误码 1xxx-5xxx）
```

**维护规则：**
1. 每个 PR 必须更新 `[Unreleased]` 段对应 section
2. 发版时将 `[Unreleased]` 改为 `[x.y.z] - YYYY-MM-DD`，并新建空 `[Unreleased]`
3. Breaking changes 在 section 条目前加 `**BREAKING:**` 前缀

### 7.3 破坏性变更处理流程

```
识别破坏性变更需求
        |
        v
1. CHANGELOG [Unreleased] 标注 **BREAKING:**
        |
        v
2. 废弃旧接口：docstring 加 "Deprecated since 0.x, use Y instead"
   旧工具继续运行，返回值的 warnings 字段中加入废弃提示
        |
        v
3. 保留至少一个 MINOR 版本的废弃期（0.x pre-stable 阶段可豁免）
        |
        v
4. 下一 MAJOR（或 0.x MINOR）中移除旧接口
        |
        v
5. 在 docs/architecture.md 中记录 ADR（架构决策记录）
```

### 7.4 MCP Tool 接口兼容性规则

| 变更类型 | 兼容性 | 版本影响 |
|---------|--------|----------|
| 新增 MCP tool | 向后兼容 | MINOR |
| 新增 tool 可选参数（有默认值） | 向后兼容 | MINOR |
| 修改 tool 描述/docstring | 向后兼容 | PATCH |
| 重命名 tool | 破坏性 | MAJOR |
| 移除 tool 必填参数 | 破坏性 | MAJOR |
| 移除返回值 JSON 字段 | 破坏性 | MAJOR |
| 新增返回值 JSON 字段 | 向后兼容 | MINOR |
| 修改错误码数值 | 破坏性 | MAJOR |
| bug 修复（不改接口） | 向后兼容 | PATCH |

### 7.5 依赖版本锁定策略

- `pyproject.toml` 使用 `>=` 下界约束（不精确锁定，避免与用户环境冲突）
- CI 通过 `uv lock` 生成锁文件用于可复现构建（不提交至仓库）
- 最低 Python：3.10（`requires-python = ">=3.10"`）
- 每季度检查并更新依赖下界，重点关注 `mcp`（FastMCP）和 `pydantic` 版本变更
- EDA 库（`gdstk`、`pyverilog`）的 mypy stub 缺失通过 `[[tool.mypy.overrides]] ignore_missing_imports = true` 处理

---

*文档结束 — PLAN2_architecture_spec.md v0.1.0*
