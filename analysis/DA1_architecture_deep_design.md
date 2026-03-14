# DA1: AUTO_EDA 整体架构深化设计

> 文档版本: 0.1.0
> 日期: 2026-03-14
> 作者: 架构深化分析团队
> 前置文档: A7_tech_stack_decision.md · A8_integration_roadmap.md · A5_differentiation_strategy.md
> 状态: 规划阶段 — 待开发实现

---

## 目录

1. [MCP 服务器内部架构设计](#1-mcp-服务器内部架构设计)
2. [跨服务器数据流架构](#2-跨服务器数据流架构)
3. [状态管理架构](#3-状态管理架构)
4. [错误处理架构](#4-错误处理架构)
5. [可扩展性设计](#5-可扩展性设计)

---

## 1. MCP 服务器内部架构设计

### 1.1 总体分层结构

每个 MCP Server 遵循三层内部架构，从上到下依次为：**协议层 → 领域层 → 工具适配层**。

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Protocol Layer                           │
│  FastMCP @tool / @resource / @prompt 装饰器 · JSON-RPC 2.0 封装  │
│  Pydantic InputModel / OutputModel · 参数验证 · Schema 生成      │
├─────────────────────────────────────────────────────────────────┤
│                      Domain Layer                                │
│  业务逻辑 · 工作流编排 · 结果格式化 · 进度报告                    │
│  BaseServer 共享基础类 · ErrorClassifier · ProgressReporter      │
├─────────────────────────────────────────────────────────────────┤
│                    Tool Adapter Layer                            │
│  EDA 工具调用 (Python API / asyncio.subprocess / TCL CLI)        │
│  进程生命周期管理 · 输出流解析 · 超时控制                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 共享基础层设计

所有 MCP Server 共享 `auto_eda.base` 包，避免跨 Server 重复实现。

#### 1.2.1 目录结构

```
auto_eda/
├── base/
│   ├── __init__.py
│   ├── server.py          # BaseEDAServer
│   ├── errors.py          # EDA 错误分类体系
│   ├── progress.py        # 进度报告 ProgressReporter
│   ├── process.py         # 子进程管理 ProcessRunner
│   ├── models.py          # 共享 Pydantic 模型
│   └── registry.py        # 工具注册与动态发现
├── servers/
│   ├── yosys/
│   ├── kicad/
│   ├── openroad/
│   ├── klayout/
│   ├── cocotb/
│   ├── simulation/
│   └── orchestrator/
└── utils/
    ├── formats/           # 文件格式解析
    └── visual/            # 可视化工具
```

#### 1.2.2 BaseEDAServer

```python
# auto_eda/base/server.py
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from .errors import EDAErrorClassifier
from .progress import ProgressReporter
from .registry import ToolRegistry


class ServerConfig(BaseModel):
    """每个 EDA Server 的静态配置，子类以 ClassVar 覆盖。"""
    server_name: str
    server_version: str
    domain: str                   # "pcb" | "digital_ic" | "simulation" | "layout"
    required_tools: list[str]     # 依赖的系统级工具名（用于启动时检测）
    optional_tools: list[str] = []


class BaseEDAServer(ABC):
    """
    所有 AUTO_EDA MCP Server 的公共基类。

    职责：
    - 统一工具可用性检测（启动时）
    - 提供共享 ProgressReporter / ErrorClassifier
    - 注册 health_check、list_tools 等通用工具
    - 强制子类实现 register_tools()
    """

    CONFIG: ClassVar[ServerConfig]  # 子类必须定义

    def __init__(self) -> None:
        self.mcp = FastMCP(
            self.CONFIG.server_name,
            version=self.CONFIG.server_version,
        )
        self.logger = logging.getLogger(self.CONFIG.server_name)
        self.progress = ProgressReporter(self.mcp)
        self.error_classifier = EDAErrorClassifier()
        self.registry = ToolRegistry()
        self._register_builtin_tools()
        self.register_tools()  # 子类实现

    def _register_builtin_tools(self) -> None:
        """注册每个 Server 都有的通用工具。"""

        @self.mcp.tool(description="检查 EDA Server 状态和工具可用性")
        def health_check() -> dict[str, Any]:
            return {
                "server": self.CONFIG.server_name,
                "version": self.CONFIG.server_version,
                "domain": self.CONFIG.domain,
                "tools_available": self.registry.check_required(self.CONFIG.required_tools),
                "registered_tools": self.registry.list_names(),
            }

    @abstractmethod
    def register_tools(self) -> None:
        """子类在此注册领域工具。"""
        ...

    def run(self, transport: str = "stdio") -> None:
        """启动 MCP Server。"""
        self.logger.info("Starting %s", self.CONFIG.server_name)
        self.mcp.run(transport=transport)
```

#### 1.2.3 ProgressReporter

长时 EDA 任务（综合、P&R、仿真）必须向 Claude 报告进度，避免超时。

```python
# auto_eda/base/progress.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP


@dataclass
class TaskProgress:
    task_id: str
    total_steps: int
    current_step: int = 0
    current_message: str = ""
    sub_messages: list[str] = field(default_factory=list)

    @property
    def percent(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return self.current_step / self.total_steps * 100


class ProgressReporter:
    """
    封装 MCP Context 的进度报告。
    支持：步骤推进、百分比、子消息追加。
    """

    def __init__(self, mcp: FastMCP) -> None:
        self._mcp = mcp
        self._tasks: dict[str, TaskProgress] = {}

    async def start_task(
        self, task_id: str, total_steps: int, initial_message: str = ""
    ) -> TaskProgress:
        progress = TaskProgress(
            task_id=task_id,
            total_steps=total_steps,
            current_message=initial_message,
        )
        self._tasks[task_id] = progress
        await self._emit(progress)
        return progress

    async def advance(
        self, task_id: str, message: str, sub_message: str | None = None
    ) -> None:
        progress = self._tasks[task_id]
        progress.current_step += 1
        progress.current_message = message
        if sub_message:
            progress.sub_messages.append(sub_message)
        await self._emit(progress)

    async def finish(self, task_id: str, final_message: str = "Done") -> None:
        progress = self._tasks.pop(task_id, None)
        if progress:
            progress.current_step = progress.total_steps
            progress.current_message = final_message
            await self._emit(progress)

    async def _emit(self, progress: TaskProgress) -> None:
        # MCP Context.report_progress() — 实际调用由 FastMCP Context 注入
        # 此处 placeholder，实现时通过 ctx: Context 参数注入
        pass

    async def stream_subprocess_output(
        self,
        task_id: str,
        stream: asyncio.StreamReader,
        step_keywords: dict[str, str],  # 关键字 → 步骤说明
    ) -> list[str]:
        """
        流式读取子进程 stdout，匹配关键字自动推进进度。
        返回完整输出行列表。
        """
        lines: list[str] = []
        async for line_bytes in stream:
            line = line_bytes.decode(errors="replace").rstrip()
            lines.append(line)
            for keyword, description in step_keywords.items():
                if keyword in line:
                    await self.advance(task_id, description, sub_message=line)
                    break
        return lines
```

#### 1.2.4 工具注册与动态发现机制

```python
# auto_eda/base/registry.py
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class ToolDescriptor:
    name: str                   # snake_case 工具名
    description: str
    domain: str                 # "pcb" | "digital_ic" | ...
    requires_binary: str | None  # 依赖的系统命令（None = 纯 Python）
    handler: Callable[..., Any]
    tags: list[str]             # 语义标签，供跨 Server 发现


class ToolRegistry:
    """
    维护本 Server 内所有工具的元数据。
    支持按 domain / tags 过滤，供 orchestrator 动态发现。
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDescriptor] = {}

    def register(self, descriptor: ToolDescriptor) -> None:
        self._tools[descriptor.name] = descriptor

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def find_by_tags(self, *tags: str) -> list[ToolDescriptor]:
        return [
            t for t in self._tools.values()
            if any(tag in t.tags for tag in tags)
        ]

    def check_required(self, binaries: list[str]) -> dict[str, bool]:
        """检测系统二进制工具是否可用（启动时诊断）。"""
        return {binary: shutil.which(binary) is not None for binary in binaries}

    def check_binary(self, name: str) -> bool:
        return shutil.which(name) is not None
```

### 1.3 各 MCP Server 内部模块划分

以 Yosys MCP Server 为例，展示标准模块划分：

```
auto_eda/servers/yosys/
├── __init__.py
├── server.py          # YosysServer(BaseEDAServer) — 入口
├── synthesizer.py     # 综合逻辑：run_synthesis, opt_passes
├── netlist.py         # 网表读写：read_verilog, write_blif/json
├── reporter.py        # 报告解析：parse_stat_report, parse_timing
├── models.py          # Pydantic 模型：SynthesisInput/Output
└── _pyosys.py         # Pyosys Python 绑定包装（隔离变动）
```

每个 Server 统一以 `server.py` 中的类作为唯一对外入口，`register_tools()` 中完成所有 `@mcp.tool` 注册。

---

## 2. 跨服务器数据流架构

### 2.1 完整数据流总览

```
自然语言指令
     │
     ▼
  Claude (推理层)
     │  决定工具调用序列
     ▼
┌────────────────────────────────────────────────────────┐
│                  Orchestrator MCP Server                │
│  - 接收高层意图（如 "RTL → GDSII"）                     │
│  - 分解为子任务 DAG                                     │
│  - 依次调用下游 Server，传递中间数据                    │
└───────────┬────────────────────────┬───────────────────┘
            │                        │
            ▼                        ▼
    Yosys MCP Server         KiCad MCP Server
    ┌────────────┐            ┌────────────┐
    │ Verilog 输入│            │ KiCad 工程 │
    │     ↓      │            │     ↓      │
    │ JSON 网表输出│            └────────────┘
    └─────┬──────┘
          │ SynthesisResult (JSON Schema)
          ▼
    OpenROAD MCP Server
    ┌────────────────┐
    │ DEF + SPEF 输出│
    └──────┬─────────┘
           │ PhysicalDesignResult (JSON Schema)
           ▼
    KLayout MCP Server
    ┌────────────────┐
    │ GDSII 生成     │
    │ DRC/LVS 验证   │
    │ 截图导出        │
    └────────────────┘
```

### 2.2 中间格式 Pydantic 模型规范

所有跨 Server 传递数据均使用 Pydantic 模型定义，置于 `auto_eda/base/models.py`。

```python
# auto_eda/base/models.py
from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class NetlistFormat(str, Enum):
    JSON = "json"
    BLIF = "blif"
    EDIF = "edif"
    VERILOG = "verilog"


class TimingConstraint(BaseModel):
    clock_name: str
    period_ns: float
    uncertainty_ns: float = 0.1
    input_delay_ns: float | None = None
    output_delay_ns: float | None = None


class SynthesisStatistics(BaseModel):
    num_cells: int
    num_wires: int
    num_ports: int
    cell_breakdown: dict[str, int]
    estimated_area_um2: float | None = None
    critical_path_ns: float | None = None


class SynthesisResult(BaseModel):
    """Yosys → OpenROAD 接口契约"""
    netlist_path: str
    netlist_format: NetlistFormat
    top_module: str
    cell_library: str
    timing_constraints: list[TimingConstraint]
    statistics: SynthesisStatistics
    warnings: list[str] = Field(default_factory=list)


class PPAMetrics(BaseModel):
    wns_ns: float | None = None
    tns_ns: float | None = None
    power_mw: float | None = None
    area_um2: float | None = None
    utilization_pct: float | None = None


class PhysicalDesignResult(BaseModel):
    """OpenROAD → KLayout 接口契约"""
    def_path: str
    lef_paths: list[str]
    spef_path: str | None = None
    gdsii_path: str | None = None
    ppa: PPAMetrics
    timing_report_path: str | None = None
    power_report_path: str | None = None


class DRCViolation(BaseModel):
    rule_name: str
    severity: Literal["error", "warning"]
    layer: str | None = None
    location: tuple[float, float] | None = None
    description: str


class DRCResult(BaseModel):
    """KLayout / KiCad DRC 统一输出"""
    tool: str
    design_file: str
    total_violations: int
    violations: list[DRCViolation]
    passed: bool
    run_timestamp: str
    screenshot_path: str | None = None
```

### 2.3 数据验证与转换层

```python
# auto_eda/base/pipeline.py
from __future__ import annotations
from pathlib import Path
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError
from .errors import DataValidationError

T = TypeVar("T", bound=BaseModel)


class DataPipeline:
    """
    跨 Server 数据流的验证与格式转换层。
    各 Server 调用此类验证上游数据，确保接口契约不被违反。
    """

    @staticmethod
    def validate(data: dict, model: Type[T]) -> T:
        try:
            return model.model_validate(data)
        except ValidationError as e:
            raise DataValidationError(
                f"数据不符合 {model.__name__} 规范",
                details=e.errors(),
            ) from e

    @staticmethod
    def ensure_file_exists(path: str, description: str) -> Path:
        p = Path(path)
        if not p.exists():
            raise DataValidationError(f"{description} 文件不存在: {path}")
        return p

---

## 3. 状态管理架构

### 3.1 设计原则

EDA 工具调用天然是有状态的（工程文件、PDK 配置、迭代历史），但 MCP 协议本身是无状态的 JSON-RPC。AUTO_EDA 通过三层状态机制解决此矛盾：

```
┌──────────────────────────────────────────────────────┐
│ L1: Session State（内存，单次 Claude 对话生命周期）    │
│  - 当前打开的工程路径                                  │
│  - 工具进程句柄（长时任务）                            │
│  - 临时中间文件路径                                    │
├──────────────────────────────────────────────────────┤
│ L2: Project State（磁盘，跨对话持久化）                │
│  - .auto_eda/project.json（工程元数据）                │
│  - .auto_eda/runs/（每次运行的输入/输出/报告快照）     │
│  - .auto_eda/workflow_history.json（工作流执行历史）   │
├──────────────────────────────────────────────────────┤
│ L3: Global Config（用户级，跨工程）                    │
│  - ~/.auto_eda/config.json（工具路径、PDK 位置）       │
│  - ~/.auto_eda/templates/（工作流模板）                │
└──────────────────────────────────────────────────────┘
```

### 3.2 项目状态持久化

```python
# auto_eda/base/state.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class RunRecord(BaseModel):
    run_id: str
    tool: str
    timestamp: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    status: str  # "success" | "failed" | "partial"
    duration_seconds: float | None = None
    error_message: str | None = None


class ProjectState(BaseModel):
    project_name: str
    project_dir: str
    created_at: str
    last_modified: str
    active_top_module: str | None = None
    cell_library: str | None = None
    pdk_name: str | None = None
    run_history: list[RunRecord] = Field(default_factory=list)
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class StateManager:
    """
    管理 .auto_eda/ 下的项目持久化状态。
    提供事务性写入（写临时文件后原子重命名），避免状态损坏。
    """

    STATE_DIR = ".auto_eda"
    STATE_FILE = "project.json"
    RUNS_DIR = "runs"

    def __init__(self, project_dir: str) -> None:
        self._root = Path(project_dir) / self.STATE_DIR
        self._root.mkdir(parents=True, exist_ok=True)
        (self._root / self.RUNS_DIR).mkdir(exist_ok=True)
        self._state_path = self._root / self.STATE_FILE

    def load_or_create(self, project_name: str) -> ProjectState:
        if self._state_path.exists():
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            return ProjectState.model_validate(data)
        now = datetime.utcnow().isoformat()
        state = ProjectState(
            project_name=project_name,
            project_dir=str(self._root.parent),
            created_at=now,
            last_modified=now,
        )
        self._write(state)
        return state

    def save(self, state: ProjectState) -> None:
        state.last_modified = datetime.utcnow().isoformat()
        self._write(state)

    def record_run(self, state: ProjectState, record: RunRecord) -> None:
        # 保留最近 100 条，防止无限增长
        state.run_history = (state.run_history + [record])[-100:]
        # 写全量运行记录到 runs/ 子目录
        run_path = self._root / self.RUNS_DIR / f"{record.run_id}.json"
        run_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        self.save(state)

    def _write(self, state: ProjectState) -> None:
        tmp = self._state_path.with_suffix(".tmp")
        tmp.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self._state_path)  # 原子重命名
```

### 3.3 工具进程生命周期管理

```python
# auto_eda/base/process.py
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ManagedProcess:
    proc_id: str
    proc: asyncio.subprocess.Process
    tool_name: str
    stdout_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)
    _cancelled: bool = False

    async def wait_with_timeout(self, timeout_seconds: float) -> int:
        try:
            return await asyncio.wait_for(self.proc.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            self.proc.kill()
            raise

    def cancel(self) -> None:
        self._cancelled = True
        if self.proc.returncode is None:
            self.proc.terminate()


class ProcessRunner:
    """
    统一子进程管理器。
    - 短时任务（< 30s）：run_sync — 阻塞等待，收集全部输出
    - 长时任务（> 30s）：run_async — 异步流式输出，支持进度回调
    """

    # 注册的运行中进程，供 orchestrator 取消
    _running: dict[str, ManagedProcess] = {}

    @classmethod
    async def run_sync(
        cls,
        cmd: list[str],
        cwd: str | None = None,
        timeout_seconds: float = 30.0,
        env: dict[str, str] | None = None,
    ) -> tuple[int, list[str], list[str]]:
        """返回 (returncode, stdout_lines, stderr_lines)"""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise
        stdout = stdout_bytes.decode(errors="replace").splitlines()
        stderr = stderr_bytes.decode(errors="replace").splitlines()
        return proc.returncode or 0, stdout, stderr

    @classmethod
    async def run_async(
        cls,
        cmd: list[str],
        cwd: str | None = None,
        timeout_seconds: float = 3600.0,
        env: dict[str, str] | None = None,
    ) -> AsyncIterator[str]:
        """异步生成器，逐行 yield stdout，供进度报告使用。"""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # 合并 stderr
            cwd=cwd,
            env=env,
        )
        proc_id = str(uuid.uuid4())[:8]
        managed = ManagedProcess(
            proc_id=proc_id, proc=proc, tool_name=cmd[0]
        )
        cls._running[proc_id] = managed
        try:
            assert proc.stdout is not None
            while True:
                line_bytes = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=timeout_seconds
                )
                if not line_bytes:
                    break
                line = line_bytes.decode(errors="replace").rstrip()
                managed.stdout_lines.append(line)
                yield line
            await proc.wait()
        finally:
            cls._running.pop(proc_id, None)

    @classmethod
    def cancel_all(cls) -> None:
        """Server 关闭时清理所有子进程。"""
        for mp in list(cls._running.values()):
            mp.cancel()
        cls._running.clear()
```

### 3.4 并发安全设计

| 场景 | 风险 | 策略 |
|------|------|------|
| 多工具同时写同一工程目录 | 文件覆盖/损坏 | 每次运行写独立子目录 `runs/{run_id}/` |
| Orchestrator 并发调度 | 状态竞争 | `asyncio.Lock` 保护 StateManager 写操作 |
| 长时进程被中断 | 残留子进程 | `ProcessRunner.cancel_all()` 注册 signal handler |
| 临时文件泄漏 | 磁盘占用 | `contextlib.AsyncExitStack` 统一清理 |
| 多个 Claude 对话同时操作 | 状态不一致 | ProjectState 写入使用原子重命名，读取加文件锁 |


---

## 4. 错误处理架构

### 4.1 EDA 工具错误分类体系

| 类别 | 错误码前缀 | 典型来源 | 是否可重试 |
|------|-----------|---------|----------|
| 工具级 | `tool_*` | 工具未安装、进程崩溃、超时 | 部分可重试（timeout） |
| 设计级 | `design_*` | 语法错误、DRC/LVS 违规、时序违规 | 否（需人工修复） |
| 数据流 | `data_*` | Pydantic 验证失败、上游文件缺失 | 否 |
| 配置级 | `config_*` | PDK 路径错误、Liberty 库缺失 | 否 |
| 系统级 | `system_*` | 磁盘/内存不足、权限问题 | 部分可重试 |

EDA 错误枚举（`EDAErrorCategory`）覆盖 16 种细分错误码，每种对应独立的用户提示字符串（`_HINTS` 字典）。`EDAError` 基类携带 `category`、`tool`、`details`、`retryable` 四个字段，`to_mcp_error()` 将其序列化为 Claude 可解析的 dict。

子类：`ToolNotFoundError`、`ToolTimeoutError`（`retryable=True`）、`DataValidationError`。

`EDAErrorClassifier` 按工具实现 `classify_yosys()` / `classify_openroad()` 等分类方法，将原始 returncode + stderr_lines 映射为具体 `EDAError`，统一在 `BaseEDAServer` 初始化时注入。

### 4.2 重试与回退策略

**`@retryable_eda_tool` 装饰器**：指数退避，仅对 `retryable=True` 的错误生效：

```
对 retryable=True 错误：sleep(backoff * attempt) 后重试，最多 max_attempts 次
对 retryable=False 错误（语法、DRC）：立即上抛，不重试
对 asyncio.TimeoutError：同指数退避逻辑
```

**工具降级回退链**：

| 失败场景 | 回退策略 |
|---------|----------|
| Pyosys API 失败 | 降级为 `yosys` CLI 子进程 |
| KiCad IPC 连接失败 | 降级为 `kicad-cli` Jobsets |
| OpenROAD Python 绑定失败 | 降级为 TCL CLI |
| 综合超时（retryable） | 指数退避最多 3 次 |
| 超过最大重试次数 | 上抛 `ToolTimeoutError`，提供人工干预建议 |

### 4.3 MCP 工具统一错误包装

`@safe_tool_call` 装饰器包装所有 `@mcp.tool` 函数，确保永远返回结构化 dict，Claude 可通过检查 `error` 字段决策后续行为：

```python
# 典型工具注册模式
@self.mcp.tool(description="综合 Verilog RTL")
@safe_tool_call
@retryable_eda_tool(max_attempts=2)
async def synthesize_rtl(verilog_path: str, top_module: str, target_lib: str) -> dict:
    rc, stdout, stderr = await ProcessRunner.run_sync(
        ["yosys", "-p", f"read_verilog {verilog_path}; synth -top {top_module}"],
        timeout_seconds=300.0,
    )
    if err := self.error_classifier.classify_yosys(rc, stderr):
        raise err
    return SynthesisResult(...).model_dump()
```

错误响应结构：

```json
{
  "error": true,
  "category": "design_syntax",
  "message": "Yosys 解析 Verilog 失败",
  "tool": "yosys",
  "retryable": false,
  "details": ["ERROR: syntax error at line 42"],
  "user_hint": "检查 HDL 语法，可用 lint_check 工具预验证"
}
```

---

## 5. 可扩展性设计

### 5.1 插件架构：社区添加新 EDA 工具

插件机制基于 Python 标准 `importlib.metadata` 入口点，无需修改核心代码即可注册新 MCP Server。

#### 5.1.1 入口点注册

```toml
# 第三方插件 pyproject.toml
[project.entry-points."auto_eda.servers"]
magic = "auto_eda_magic.server:MagicServer"
```

发现机制：

```python
# auto_eda/base/plugin.py
def discover_servers() -> dict[str, type[BaseEDAServer]]:
    servers = {}
    for ep in importlib.metadata.entry_points(group="auto_eda.servers"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, BaseEDAServer):
                servers[ep.name] = cls
                logger.info("已加载插件 Server: %s", ep.name)
        except Exception as exc:
            logger.error("加载插件 %s 失败: %s", ep.name, exc)
    return servers
```

#### 5.1.2 最小插件模板

社区开发者仅需继承 `BaseEDAServer`，声明 `CONFIG`，在 `register_tools()` 中注册工具即可发布一个新 EDA Server：

```python
# auto_eda_magic/server.py
class MagicServer(BaseEDAServer):
    CONFIG = ServerConfig(
        server_name="auto-eda-magic",
        server_version="0.1.0",
        domain="layout",
        required_tools=["magic"],
    )

    def register_tools(self) -> None:
        @self.mcp.tool(description="Magic VLSI DRC")
        @safe_tool_call
        async def run_magic_drc(gds_path: str, tech_file: str) -> dict:
            rc, stdout, _ = await ProcessRunner.run_sync(
                ["magic", "-T", tech_file, "-dnull", "-noconsole", gds_path],
                timeout_seconds=120.0,
            )
            if rc != 0:
                raise RuntimeError(f"Magic DRC 失败，退出码 {rc}")
            return {"returncode": rc, "output": stdout}
```

### 5.2 版本兼容性策略

#### 5.2.1 MCP Tool 接口变更规则

```
兼容变更（可不升版本）：
  + 添加有默认值的可选参数
  + 输出 dict 新增字段
  + 添加新工具

破坏性变更（必须升 minor 版本，CHANGELOG 记录迁移指南）：
  - 删除或重命名现有参数
  - 修改参数类型
  - 删除工具
  - 改变输出结构
```

#### 5.2.2 EDA 工具版本兼容矩阵

| MCP Server | 最低版本 | 检测命令 | 降级策略 |
|------------|---------|----------|----------|
| yosys | 0.25 | `yosys --version` | 旧版禁用 Pyosys，改用 CLI |
| openroad | 2.0 | `openroad -version` | 部分 API 用 TCL fallback |
| klayout | 0.28 | `klayout -v` | 旧版禁用截图 API |
| kicad | 8.0 | IPC handshake | v8 用 CLI Jobsets，v10 用 IPC API |
| ngspice | 38 | `ngspice -v` | 旧版改用 PySpice 间接调用 |

版本检测在 `BaseEDAServer.__init__` 中调用 `detect_tool_version()`，结果缓存在 `health_check` 响应中，供 Claude 和运维人员查阅。

### 5.3 配置管理

#### 5.3.1 配置层次（高优先级到低）

```
1. 工具调用参数（单次覆盖，最高优先）
2. 工程级配置  .auto_eda/project.json
3. 用户级配置  ~/.auto_eda/config.json
4. 内置默认值（最低优先）
```

#### 5.3.2 配置模型

```python
# auto_eda/base/config.py
class ToolPaths(BaseModel):
    yosys: str = "yosys"
    openroad: str = "openroad"
    klayout: str = "klayout"
    ngspice: str = "ngspice"
    verilator: str = "verilator"
    kicad_cli: str = "kicad-cli"


class PDKConfig(BaseModel):
    name: str = "sky130A"
    root_path: str = ""
    liberty_dir: str = ""
    lef_dir: str = ""
    tech_lef: str = ""


class GlobalConfig(BaseModel):
    tool_paths: ToolPaths = Field(default_factory=ToolPaths)
    pdk: PDKConfig = Field(default_factory=PDKConfig)
    default_timeout_seconds: float = 300.0
    max_retry_attempts: int = 3
    log_level: str = "INFO"
    enable_progress_reporting: bool = True

    @classmethod
    def load(cls) -> "GlobalConfig":
        config_path = pathlib.Path.home() / ".auto_eda" / "config.json"
        if config_path.exists():
            return cls.model_validate_json(config_path.read_text(encoding="utf-8"))
        return cls()

    def save(self) -> None:
        config_path = pathlib.Path.home() / ".auto_eda" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
```

#### 5.3.3 pyproject.toml 分层可选依赖

```toml
[project.optional-dependencies]
pcb  = ["kicad-skip", "kikit"]
ic   = ["gdstk", "pyverilog", "hdlConvertor"]
sim  = ["PySpice", "cocotb", "matplotlib"]
full = ["auto-eda[pcb,ic,sim]"]
```

用户按需安装，不强制引入与自身领域无关的 EDA 库。

---

## 附录：架构决策速查表

| 决策项 | 选择 | 核心理由 |
|--------|------|----------|
| MCP Server 语言 | Python + FastMCP | EDA 库生态唯一选择 |
| 参数验证 | Pydantic v2 | 运行时类型安全 + JSON Schema 自动生成 |
| 静态类型检查 | mypy strict | 编译期错误检测，弥补 Python 动态类型劣势 |
| 子进程管理 | asyncio.subprocess | 非阻塞，支持长时 EDA 任务流式输出 |
| 状态持久化 | JSON + 原子重命名 | 简单可靠，无外部依赖（无需 DB/Redis） |
| 错误策略 | 结构化 EDAError 分类 | Claude 可解析错误类型，自动决策重试/上报 |
| 插件机制 | importlib.metadata entry_points | Python 标准，零核心代码侵入 |
| 版本兼容 | 兼容变更免升版，破坏性变更升 minor | 明确契约，保护下游用户 |
| 配置管理 | 4 层优先级 + Pydantic 模型 | 覆盖全场景，类型安全，零魔法字符串 |