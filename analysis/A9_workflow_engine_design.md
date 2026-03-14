# A9: AUTO_EDA 工作流引擎完整设计方案

> 分析日期: 2026-03-14
> 数据来源: A5 (USP-1, USP-4), A8 (Phase 2-3), R9 (EDA工作流自动化)
> 分析范围: DAG引擎设计、工作流模板、MCP工具接口、跨工具数据传递

---

## 目录

1. [工作流引擎核心架构](#1-工作流引擎核心架构)
2. [DAG数据结构设计](#2-dag数据结构设计)
3. [节点类型系统](#3-节点类型系统)
4. [执行引擎状态机](#4-执行引擎状态机)
5. [序列化格式规范](#5-序列化格式规范)
6. [预定义工作流模板](#6-预定义工作流模板)
7. [工作流MCP Tool接口](#7-工作流mcp-tool接口)
8. [跨工具数据传递机制](#8-跨工具数据传递机制)
9. [检查点与恢复机制](#9-检查点与恢复机制)
10. [实施路线图](#10-实施路线图)

---

## 1. 工作流引擎核心架构

### 1.1 设计原则

基于A5 USP-1（多工具统一编排）和R9（Qualcomm Airflow案例），工作流引擎遵循以下原则：

- **DAG驱动**: 所有工作流表达为有向无环图，节点为工具调用，边为数据依赖
- **声明式定义**: YAML/JSON格式描述工作流，引擎负责执行调度
- **幂等执行**: 每个节点执行结果可重复，支持安全重试
- **检查点优先**: 长时间EDA任务（综合/P&R数小时）必须支持断点续跑
- **MCP原生**: 工作流引擎本身作为MCP Server暴露，与现有MCP Tool生态无缝集成

### 1.2 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTO_EDA Workflow Engine                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │  Workflow Parser │    │  Template Library │                    │
│  │  (YAML/JSON→DAG)│    │  (内置+社区模板)  │                    │
│  └────────┬────────┘    └────────┬─────────┘                    │
│           │                      │                               │
│           ▼                      ▼                               │
│  ┌─────────────────────────────────────────┐                    │
│  │              DAG Engine                  │                    │
│  │  ┌──────────────┐  ┌─────────────────┐  │                    │
│  │  │  Scheduler   │  │  State Machine  │  │                    │
│  │  │ (拓扑排序+并行)│  │  (节点状态管理) │  │                    │
│  │  └──────────────┘  └─────────────────┘  │                    │
│  └───────────────────┬─────────────────────┘                    │
│                      │                                           │
│           ┌──────────┴──────────┐                               │
│           ▼                     ▼                               │
│  ┌────────────────┐   ┌─────────────────────┐                  │
│  │ Checkpoint Mgr │   │   Artifact Manager   │                  │
│  │ (SQLite状态持久)│   │  (中间产物文件管理)   │                  │
│  └────────────────┘   └──────────┬──────────┘                  │
│                                  │                              │
│           ┌──────────────────────┘                              │
│           ▼                                                      │
│  ┌─────────────────────────────────────────┐                    │
│  │           MCP Tool Dispatcher            │                    │
│  │  ┌──────┐ ┌──────────┐ ┌─────────────┐  │                    │
│  │  │Yosys │ │OpenROAD  │ │   KiCad     │  │                    │
│  │  │ MCP  │ │  MCP     │ │    MCP      │  │                    │
│  │  └──────┘ └──────────┘ └─────────────┘  │                    │
│  │  ┌──────┐ ┌──────────┐ ┌─────────────┐  │                    │
│  │  │KLayout│ │  cocotb │ │  ngspice    │  │                    │
│  │  │ MCP  │ │  MCP     │ │    MCP      │  │                    │
│  │  └──────┘ └──────────┘ └─────────────┘  │                    │
│  └─────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 组件职责

| 组件 | 职责 | 关键设计决策 |
|------|------|-------------|
| **Workflow Parser** | YAML/JSON → 内存DAG对象 | 严格验证，拒绝环路和悬空引用 |
| **Template Library** | 内置模板注册表 + 外部模板加载 | 版本化，支持参数覆盖 |
| **DAG Engine** | 拓扑排序、并行调度、依赖追踪 | 基于asyncio实现真正并行 |
| **State Machine** | 节点状态转换和工作流生命周期 | 事件驱动，支持外部查询 |
| **Checkpoint Manager** | 状态持久化、断点恢复 | SQLite本地存储，JSON序列化状态 |
| **Artifact Manager** | 中间产物文件命名、存储、清理 | 内容寻址存储，避免命名冲突 |
| **MCP Tool Dispatcher** | 将节点执行请求路由到对应MCP Server | 工具注册表，健康检查，超时处理 |

---

## 2. DAG数据结构设计

### 2.1 核心数据类型（Python实现）

```python
# workflow/models.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid


class NodeStatus(Enum):
    PENDING   = "pending"    # 等待依赖完成
    READY     = "ready"      # 依赖满足，等待调度
    RUNNING   = "running"    # 正在执行
    SUCCEEDED = "succeeded"  # 成功完成
    FAILED    = "failed"     # 执行失败
    SKIPPED   = "skipped"    # 条件分支跳过
    PAUSED    = "paused"     # 用户暂停


class WorkflowStatus(Enum):
    DRAFT     = "draft"
    RUNNING   = "running"
    PAUSED    = "paused"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"
    CANCELLED = "cancelled"


@dataclass
class PortRef:
    """引用另一节点的输出端口：用于数据依赖声明"""
    node_id: str       # 被引用节点的ID
    port:    str       # 输出端口名称


@dataclass
class NodeInput:
    """节点输入：可以是字面量或对另一节点输出的引用"""
    value: Union[Any, PortRef]  # 字面量 或 PortRef


@dataclass
class WorkflowNode:
    """DAG节点：表示一次工具调用或控制流结构"""
    id:          str
    type:        str                           # tool|condition|parallel|loop|checkpoint
    tool:        Optional[str]  = None         # MCP Server名称（tool节点专用）
    action:      Optional[str]  = None         # MCP Tool名称
    inputs:      Dict[str, NodeInput] = field(default_factory=dict)
    outputs:     List[str]      = field(default_factory=list)  # 输出端口名称列表
    depends_on:  List[str]      = field(default_factory=list)  # 显式依赖（无数据传递）
    retry:       int            = 0            # 最大重试次数
    timeout_sec: Optional[int]  = None         # 超时秒数
    condition:   Optional[str]  = None         # JMESPath条件表达式（condition节点）
    metadata:    Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEdge:
    """DAG边：表示节点间的执行顺序或数据流依赖"""
    from_node: str
    to_node:   str
    from_port: Optional[str] = None  # 数据流边需要指定端口
    to_port:   Optional[str] = None
    edge_type: str = "data"           # data | control | conditional


@dataclass
class WorkflowDAG:
    """完整的工作流DAG"""
    id:          str
    name:        str
    version:     str
    description: str
    nodes:       Dict[str, WorkflowNode]  # node_id → WorkflowNode
    edges:       List[WorkflowEdge]
    parameters:  Dict[str, Any]           # 工作流级参数（可被覆盖）
    metadata:    Dict[str, Any] = field(default_factory=dict)

    def topological_order(self) -> List[List[str]]:
        """返回按层次分组的拓扑排序，同层节点可并行执行"""
        # Kahn算法实现
        in_degree = {nid: 0 for nid in self.nodes}
        adjacency = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            adjacency[edge.from_node].append(edge.to_node)
            in_degree[edge.to_node] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        layers = []
        while queue:
            layers.append(queue[:])
            next_queue = []
            for nid in queue:
                for successor in adjacency[nid]:
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        next_queue.append(successor)
            queue = next_queue

        if sum(len(l) for l in layers) != len(self.nodes):
            raise ValueError("工作流DAG包含环路")
        return layers
```

### 2.2 运行时状态数据类型

```python
@dataclass
class NodeExecution:
    """节点单次执行的运行时记录"""
    node_id:      str
    attempt:      int           # 第几次尝试（从1开始）
    status:       NodeStatus
    started_at:   Optional[float] = None   # Unix时间戳
    finished_at:  Optional[float] = None
    inputs_used:  Dict[str, Any] = field(default_factory=dict)   # 实际输入值快照
    outputs:      Dict[str, Any] = field(default_factory=dict)   # 输出值
    error:        Optional[str]  = None
    artifact_ids: List[str]     = field(default_factory=list)    # 产生的产物ID


@dataclass
class WorkflowRun:
    """工作流一次完整运行的运行时状态"""
    run_id:       str
    workflow_id:  str
    status:       WorkflowStatus
    parameters:   Dict[str, Any]                          # 本次运行的参数值
    node_states:  Dict[str, NodeExecution]                # node_id → NodeExecution
    started_at:   float
    finished_at:  Optional[float] = None
    checkpoint_id: Optional[str]  = None                  # 最新检查点ID
```

---

## 3. 节点类型系统

### 3.1 节点类型概览

| 类型 | 用途 | 关键属性 |
|------|------|----------|
| `tool` | 调用单个MCP Tool | tool, action, inputs, outputs |
| `condition` | 条件分支（if/else） | condition (JMESPath), branches |
| `parallel` | 并行执行子图 | branches (List[List[node_id]]) |
| `loop` | 循环（for/while） | iterator, loop_body, max_iterations |
| `checkpoint` | 强制持久化检查点 | label |
| `transform` | 纯数据转换（无工具调用） | transform_expr (JMESPath/Python) |
| `validate` | 数据验证节点 | schema, on_failure |

### 3.2 Tool节点（最常用）

```yaml
# 示例：Yosys综合节点
- id: synthesize_rtl
  type: tool
  tool: auto-eda-yosys          # MCP Server名称
  action: synthesize             # MCP Tool名称
  inputs:
    verilog_files:
      ref: parse_result          # 引用parse_verilog节点的输出
      port: file_list
    top_module: { value: "{{ params.top_module }}" }   # 工作流参数
    liberty_file: { value: "{{ params.pdk_liberty }}" }
    optimize_for: { value: area }
  outputs:
    - netlist_json
    - synthesis_report
    - resource_utilization
  retry: 2
  timeout_sec: 3600
```

### 3.3 Condition节点（条件分支）

```yaml
- id: check_timing
  type: condition
  condition: "synthesis_report.wns >= -0.1"
  inputs:
    synthesis_report:
      ref: synthesize_rtl
      port: synthesis_report
  branches:
    true_branch:  [place_and_route]
    false_branch: [tighten_constraints]
```

**条件表达式引擎**：
- 使用 `jmespath` 库对节点输出JSON进行查询
- 支持比较运算符、逻辑运算符、数值运算
- 结果为布尔值，决定执行哪个分支

### 3.4 Parallel节点（并行执行）

```yaml
- id: ppa_sweep
  type: parallel
  branches:
    - [synth_area_opt]
    - [synth_timing_opt]
    - [synth_power_opt]
  join: all
  outputs:
    - ppa_results
```

**并行执行语义**：
- `join: all`：全部分支成功后合并输出（Barrier同步）
- `join: any`：任一分支成功即继续，其余分支取消
- `join: best`：全部运行，选取指定指标最优结果

### 3.5 Loop节点（循环）

```yaml
- id: timing_closure_loop
  type: loop
  max_iterations: 5
  loop_body: [place_design, cts, route_design, check_timing_sta]
  exit_condition: "sta_report.wns >= 0 and sta_report.tns >= 0"
  inputs:
    initial_netlist:
      ref: synthesize_rtl
      port: netlist_json
  outputs:
    - final_def
    - iteration_count
    - converged
```

**循环执行语义**：
- `exit_condition`：每轮结束后对loop_body最后一个节点的输出求值
- 满足条件则退出，否则进入下一轮（透传上一轮输出作为下一轮输入）
- 超过 `max_iterations` 后以 `FAILED` 状态退出并携带 `loop_exhausted` 错误码

### 3.6 Checkpoint节点（强制检查点）

```yaml
- id: after_synthesis_checkpoint
  type: checkpoint
  label: "synthesis_complete"
  depends_on: [synthesize_rtl]
```

---

## 4. 执行引擎状态机

### 4.1 节点级状态转换

```
          PENDING  ──依赖满足──▶  READY  ──调度器选中──▶  RUNNING
                                                            │
                                              ┌─────────────┴─────────────┐
                                              ▼                           ▼
                                          SUCCEEDED                    FAILED
                                                                          │
                                                               retry < max_retry
                                                                          │
                                                                          └──▶ RUNNING (重试)

  用户暂停: RUNNING ──pause──▶ PAUSED ──resume──▶ RUNNING
  条件跳过: PENDING ──分支未选中──▶ SKIPPED
```

### 4.2 工作流级状态转换

```
  DRAFT ──create──▶ RUNNING ──所有节点成功──▶ SUCCEEDED
                       │
                       ├──任一节点失败(重试耗尽)──▶ FAILED
                       ├──用户暂停──▶ PAUSED ──resume──▶ RUNNING
                       └──用户取消──▶ CANCELLED
```

### 4.3 执行引擎核心逻辑

```python
# workflow/engine.py
import asyncio, time
from typing import Set, Dict

class WorkflowEngine:
    async def run(self, wf_run: WorkflowRun, dag: WorkflowDAG) -> WorkflowRun:
        # 从检查点恢复时跳过已成功的节点
        completed: Set[str] = {
            nid for nid, ex in wf_run.node_states.items()
            if ex.status == NodeStatus.SUCCEEDED
        }
        running_tasks: Dict[str, asyncio.Task] = {}

        while True:
            ready = [
                nid for nid in dag.nodes
                if nid not in completed
                and nid not in running_tasks
                and self._deps_satisfied(nid, dag, completed, wf_run)
            ]
            for nid in ready:
                running_tasks[nid] = asyncio.create_task(
                    self._execute_node(nid, wf_run, dag)
                )
            if not running_tasks:
                break
            done, _ = await asyncio.wait(
                running_tasks.values(), return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                nid = next(k for k, v in running_tasks.items() if v is task)
                del running_tasks[nid]
                ex = wf_run.node_states[nid]
                if ex.status == NodeStatus.SUCCEEDED:
                    completed.add(nid)
                    await self.checkpoint_mgr.save(wf_run)
                elif ex.status == NodeStatus.FAILED:
                    if ex.attempt <= dag.nodes[nid].retry:
                        ex.status = NodeStatus.READY
                        ex.attempt += 1
                    else:
                        wf_run.status = WorkflowStatus.FAILED
                        await self._cancel_all(running_tasks)
                        return wf_run
        wf_run.status = WorkflowStatus.SUCCEEDED
        return wf_run

    def _deps_satisfied(self, nid, dag, completed, run) -> bool:
        node = dag.nodes[nid]
        # 控制依赖
        if not all(dep in completed for dep in node.depends_on):
            return False
        # 数据依赖（PortRef）
        for inp in node.inputs.values():
            if isinstance(inp.value, PortRef):
                if inp.value.node_id not in completed:
                    return False
        return True

    async def _execute_node(self, nid, run, dag):
        node = dag.nodes[nid]
        ex = run.node_states.setdefault(nid, NodeExecution(
            node_id=nid, attempt=1, status=NodeStatus.RUNNING,
            started_at=time.time()
        ))
        ex.status = NodeStatus.RUNNING
        try:
            resolved = self._resolve_inputs(node, run)
            ex.inputs_used = resolved
            handler = self._get_handler(node.type)
            outputs = await asyncio.wait_for(
                handler.execute(node, resolved, run),
                timeout=node.timeout_sec
            )
            ex.outputs = outputs
            ex.status = NodeStatus.SUCCEEDED
            ex.finished_at = time.time()
        except asyncio.TimeoutError:
            ex.status = NodeStatus.FAILED
            ex.error = f"超时：{node.timeout_sec}秒"
        except Exception as e:
            ex.status = NodeStatus.FAILED
            ex.error = str(e)
```

---

## 5. 序列化格式规范

### 5.1 YAML顶层结构

```yaml
apiVersion: auto-eda/v1
kind: Workflow
metadata:
  id: rtl-to-gdsii-sky130
  name: RTL to GDSII (SkyWater 130nm)
  version: "1.2.0"
  description: |
    完整数字IC RTL-to-GDSII流程，面向SkyWater 130nm PDK。
    包含综合、布局规划、放置、CTS、布线、时序签核和版图导出。
  tags: [digital-ic, rtl-to-gdsii, sky130]
  author: auto-eda-community

parameters:
  # 必填参数（无默认值）
  rtl_files:
    type: list[path]
    description: RTL Verilog/SystemVerilog源文件列表
  top_module:
    type: string
    description: 顶层模块名称
  # 可选参数（有默认值）
  pdk_root:
    type: path
    default: "${PDK_ROOT}"
  target_clock_mhz:
    type: float
    default: 100.0
  core_utilization:
    type: float
    default: 0.50
    description: 芯片核心面积利用率 (0.0-1.0)
  max_fanout:
    type: int
    default: 10

nodes:
  # 节点列表（详见第6节各模板）
  []

checkpoints:
  # 强制检查点标签（可选，覆盖节点内置检查点）
  - after_synthesis
  - after_floorplan
  - after_routing

artifacts:
  # 工作流最终输出产物声明
  outputs:
    - node: stream_gds
      port: gds_file
      label: final_gds
    - node: opensta_signoff
      port: timing_report
      label: timing_signoff_report
  work_dir: "./runs/{{ metadata.id }}/{{ run_id }}"
  keep_intermediates: false
```

### 5.2 参数引用语法

| 语法 | 含义 | 示例 |
|------|------|------|
| `{{ params.key }}` | 工作流参数 | `{{ params.top_module }}` |
| `{{ run_id }}` | 当前运行ID | `run_20260314_001` |
| `{{ work_dir }}` | 工作目录绝对路径 | `/tmp/auto-eda/runs/...` |
| `{{ env.VAR }}` | 环境变量 | `{{ env.PDK_ROOT }}` |
| `ref: <node_id>` + `port: <port>` | 引用节点输出 | 跨节点数据传递 |

### 5.3 JSON等价格式

YAML和JSON互相等价，引擎同时支持两种格式。JSON格式适用于程序生成的工作流。

```json
{
  "apiVersion": "auto-eda/v1",
  "kind": "Workflow",
  "metadata": { "id": "rtl-to-gdsii-sky130", "version": "1.2.0" },
  "parameters": { "top_module": { "type": "string" } },
  "nodes": []
}
```

### 5.4 格式验证规则

解析阶段必须通过的检查：

1. **唯一ID**: 所有节点ID在工作流内唯一
2. **无环检查**: `topological_order()` 不抛出异常
3. **引用完整性**: 所有 `ref` 引用的 `node_id` 和 `port` 必须存在
4. **参数覆盖**: 所有无默认值的参数在运行时必须提供
5. **工具存在性**: 所有 `tool` 字段引用的MCP Server已在注册表中注册


## 6. 预定义工作流模板

### 6.1 模板一：RTL→GDSII完整流程

```yaml
apiVersion: auto-eda/v1
kind: Workflow
metadata:
  id: rtl-to-gdsii-sky130
  name: RTL to GDSII (SkyWater 130nm)
  version: "1.0.0"
  tags: [digital-ic, rtl-to-gdsii, sky130]

parameters:
  rtl_files:         { type: list[path] }
  top_module:        { type: string }
  pdk_root:          { type: path, default: "${PDK_ROOT}" }
  target_clock_mhz:  { type: float, default: 100.0 }
  core_utilization:  { type: float, default: 0.50 }

nodes:
  # ── Step 1: 解析并验证RTL ──────────────────────────
  - id: parse_rtl
    type: tool
    tool: auto-eda-verilog-utils
    action: parse_verilog
    inputs:
      files: { value: "{{ params.rtl_files }}" }
    outputs: [module_list, port_map, hierarchy]
    timeout_sec: 120

  # ── Step 2: 生成SDC约束文件 ──────────────────────────
  - id: gen_sdc
    type: tool
    tool: auto-eda-yosys
    action: generate_sdc
    inputs:
      top_module:       { value: "{{ params.top_module }}" }
      clock_period_ns:  { value: "{{ 1000.0 / params.target_clock_mhz }}" }
    outputs: [sdc_file]
    depends_on: [parse_rtl]

  # ── Step 3: 逻辑综合 ──────────────────────────────────
  - id: synthesize
    type: tool
    tool: auto-eda-yosys
    action: synthesize
    inputs:
      verilog_files: { ref: parse_rtl, port: module_list }
      top_module:    { value: "{{ params.top_module }}" }
      liberty_file:  { value: "{{ params.pdk_root }}/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" }
      sdc_file:      { ref: gen_sdc, port: sdc_file }
    outputs: [netlist_json, synthesis_report, resource_utilization]
    retry: 1
    timeout_sec: 1800

  # ── Step 4: 检查综合结果 ──────────────────────────────
  - id: check_synthesis
    type: condition
    condition: "synthesis_report.critical_warnings == 0"
    inputs:
      synthesis_report: { ref: synthesize, port: synthesis_report }
    branches:
      true_branch:  [init_floorplan]
      false_branch: [report_synthesis_failure]

  - id: report_synthesis_failure
    type: tool
    tool: auto-eda-yosys
    action: explain_warnings
    inputs:
      report: { ref: synthesize, port: synthesis_report }
    outputs: [explanation]

  # ── Step 5: 检查点 ──────────────────────────────────────
  - id: cp_after_synthesis
    type: checkpoint
    label: after_synthesis
    depends_on: [check_synthesis]

  # ── Step 6: 布局规划 ──────────────────────────────────
  - id: init_floorplan
    type: tool
    tool: auto-eda-openroad
    action: init_floorplan
    inputs:
      netlist:          { ref: synthesize, port: netlist_json }
      pdk_root:         { value: "{{ params.pdk_root }}" }
      core_utilization: { value: "{{ params.core_utilization }}" }
      sdc_file:         { ref: gen_sdc, port: sdc_file }
    outputs: [floorplan_def, die_area]
    timeout_sec: 600

  # ── Step 7: 放置 ──────────────────────────────────────
  - id: place_design
    type: tool
    tool: auto-eda-openroad
    action: place_design
    inputs:
      floorplan_def: { ref: init_floorplan, port: floorplan_def }
    outputs: [placed_def, placement_report]
    timeout_sec: 3600

  # ── Step 8: 时钟树综合 ────────────────────────────────
  - id: clock_tree_synthesis
    type: tool
    tool: auto-eda-openroad
    action: cts
    inputs:
      placed_def: { ref: place_design, port: placed_def }
      sdc_file:   { ref: gen_sdc, port: sdc_file }
    outputs: [cts_def, cts_report]
    timeout_sec: 1800

  # ── Step 9: 布线 ──────────────────────────────────────
  - id: route_design
    type: tool
    tool: auto-eda-openroad
    action: route_design
    inputs:
      cts_def: { ref: clock_tree_synthesis, port: cts_def }
    outputs: [routed_def, routing_report, drc_count]
    timeout_sec: 7200

  # ── Step 10: 检查点 ─────────────────────────────────────
  - id: cp_after_routing
    type: checkpoint
    label: after_routing
    depends_on: [route_design]

  # ── Step 11: 时序签核（循环收敛）────────────────────────
  - id: timing_closure
    type: loop
    max_iterations: 3
    loop_body: [sta_check, eco_fix]
    exit_condition: "sta_report.wns >= -0.05 and sta_report.setup_violations == 0"
    inputs:
      routed_def: { ref: route_design, port: routed_def }
    outputs: [signed_off_def, final_sta_report, converged]

  - id: sta_check
    type: tool
    tool: auto-eda-opensta
    action: report_checks
    inputs:
      def_file:      { value: "{{ loop.current_def }}" }
      liberty_file:  { value: "{{ params.pdk_root }}/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" }
      sdc_file:      { ref: gen_sdc, port: sdc_file }
    outputs: [sta_report, critical_paths]

  - id: eco_fix
    type: tool
    tool: auto-eda-openroad
    action: repair_timing
    inputs:
      sta_report:    { ref: sta_check, port: sta_report }
      routed_def:    { value: "{{ loop.current_def }}" }
    outputs: [repaired_def]

  # ── Step 12: DRC验证 ──────────────────────────────────
  - id: drc_check
    type: tool
    tool: auto-eda-klayout
    action: run_drc
    inputs:
      def_file:     { ref: timing_closure, port: signed_off_def }
      pdk_root:     { value: "{{ params.pdk_root }}" }
    outputs: [drc_report, violation_count]
    depends_on: [timing_closure]

  # ── Step 13: GDSII流片 ────────────────────────────────
  - id: stream_gds
    type: tool
    tool: auto-eda-klayout
    action: stream_out_gds
    inputs:
      def_file: { ref: timing_closure, port: signed_off_def }
      pdk_root: { value: "{{ params.pdk_root }}" }
    outputs: [gds_file]
    depends_on: [drc_check]
    timeout_sec: 600

artifacts:
  outputs:
    - { node: stream_gds, port: gds_file, label: final_gds }
    - { node: timing_closure, port: final_sta_report, label: timing_report }
    - { node: drc_check, port: drc_report, label: drc_report }
    - { node: synthesize, port: resource_utilization, label: resource_report }
  work_dir: "./runs/{{ metadata.id }}/{{ run_id }}"
```


### 6.2 模板二：PCB设计流程（KiCad）

```yaml
apiVersion: auto-eda/v1
kind: Workflow
metadata:
  id: pcb-design-kicad
  name: PCB Design Flow (KiCad)
  version: "1.0.0"
  tags: [pcb, kicad, gerber]

parameters:
  project_file:     { type: path, description: KiCad .kicad_pro 文件路径 }
  board_layers:     { type: int, default: 4 }
  design_rules:     { type: path, description: .kicad_dru 设计规则文件 }
  output_dir:       { type: path, default: "./output" }

nodes:
  - id: open_project
    type: tool
    tool: auto-eda-kicad
    action: open_project
    inputs:
      project_file: { value: "{{ params.project_file }}" }
    outputs: [project_info, schematic_list, board_file]

  - id: parallel_checks
    type: parallel
    branches:
      - [run_erc]
      - [check_bom_completeness]
    join: all
    depends_on: [open_project]

  - id: run_erc
    type: tool
    tool: auto-eda-kicad
    action: run_erc
    inputs:
      schematic_list: { ref: open_project, port: schematic_list }
    outputs: [erc_report, erc_errors]

  - id: check_bom_completeness
    type: tool
    tool: auto-eda-kicad
    action: export_bom
    inputs:
      project_file: { value: "{{ params.project_file }}" }
    outputs: [bom_csv, missing_footprints]

  - id: check_erc_result
    type: condition
    condition: "erc_errors == 0"
    inputs:
      erc_errors: { ref: run_erc, port: erc_errors }
    branches:
      true_branch:  [update_pcb_netlist]
      false_branch: [report_erc_failure]

  - id: report_erc_failure
    type: tool
    tool: auto-eda-kicad
    action: explain_erc_errors
    inputs:
      erc_report: { ref: run_erc, port: erc_report }
    outputs: [explanation]

  - id: update_pcb_netlist
    type: tool
    tool: auto-eda-kicad
    action: update_pcb_from_schematic
    inputs:
      board_file: { ref: open_project, port: board_file }
    outputs: [updated_board, change_report]

  - id: run_drc
    type: tool
    tool: auto-eda-kicad
    action: run_drc
    inputs:
      board_file: { ref: update_pcb_netlist, port: updated_board }
      rules_file: { value: "{{ params.design_rules }}" }
    outputs: [drc_report, drc_violations]
    timeout_sec: 300

  - id: check_drc_result
    type: condition
    condition: "drc_violations == 0"
    inputs:
      drc_violations: { ref: run_drc, port: drc_violations }
    branches:
      true_branch:  [export_manufacturing]
      false_branch: [report_drc_failure]

  - id: report_drc_failure
    type: tool
    tool: auto-eda-kicad
    action: explain_drc_violations
    inputs:
      drc_report: { ref: run_drc, port: drc_report }
    outputs: [prioritized_fixes]

  - id: export_manufacturing
    type: parallel
    branches:
      - [export_gerber]
      - [export_drill]
      - [export_assembly_bom]
    join: all

  - id: export_gerber
    type: tool
    tool: auto-eda-kicad
    action: export_gerber
    inputs:
      board_file: { ref: update_pcb_netlist, port: updated_board }
      output_dir: { value: "{{ params.output_dir }}/gerber" }
    outputs: [gerber_files, layer_map]

  - id: export_drill
    type: tool
    tool: auto-eda-kicad
    action: export_drill
    inputs:
      board_file: { ref: update_pcb_netlist, port: updated_board }
      output_dir: { value: "{{ params.output_dir }}/drill" }
    outputs: [drill_files]

  - id: export_assembly_bom
    type: tool
    tool: auto-eda-kicad
    action: export_bom
    inputs:
      project_file: { value: "{{ params.project_file }}" }
      format: { value: csv }
    outputs: [bom_file]

artifacts:
  outputs:
    - { node: export_gerber, port: gerber_files, label: gerber }
    - { node: export_drill, port: drill_files, label: drill }
    - { node: export_assembly_bom, port: bom_file, label: bom }
    - { node: run_drc, port: drc_report, label: drc_report }
  work_dir: "{{ params.output_dir }}"
```

### 6.3 模板三：功能验证流程（Yosys + Verilator + cocotb）

```yaml
apiVersion: auto-eda/v1
kind: Workflow
metadata:
  id: functional-verification
  name: Functional Verification Flow
  version: "1.0.0"
  tags: [verification, cocotb, verilator]

parameters:
  rtl_files:      { type: list[path] }
  top_module:     { type: string }
  testbench_dir:  { type: path }
  coverage_goal:  { type: float, default: 0.90 }
  simulator:      { type: string, default: verilator }

nodes:
  - id: parallel_static
    type: parallel
    branches:
      - [lint_check]
      - [synth_check]
    join: all

  - id: lint_check
    type: tool
    tool: auto-eda-verilog-utils
    action: lint_check
    inputs:
      files:      { value: "{{ params.rtl_files }}" }
      top_module: { value: "{{ params.top_module }}" }
    outputs: [lint_report, lint_errors, lint_warnings]

  - id: synth_check
    type: tool
    tool: auto-eda-yosys
    action: check
    inputs:
      verilog_files: { value: "{{ params.rtl_files }}" }
      top_module:    { value: "{{ params.top_module }}" }
    outputs: [check_report, undriven_signals]

  - id: discover_tests
    type: tool
    tool: auto-eda-cocotb
    action: list_tests
    inputs:
      testbench_dir: { value: "{{ params.testbench_dir }}" }
    outputs: [test_list, test_count]
    depends_on: [parallel_static]

  - id: check_tests_exist
    type: condition
    condition: "test_count > 0"
    inputs:
      test_count: { ref: discover_tests, port: test_count }
    branches:
      true_branch:  [compile_rtl]
      false_branch: [generate_basic_tests]

  - id: generate_basic_tests
    type: tool
    tool: auto-eda-cocotb
    action: create_testbench
    inputs:
      rtl_files:     { value: "{{ params.rtl_files }}" }
      top_module:    { value: "{{ params.top_module }}" }
      output_dir:    { value: "{{ params.testbench_dir }}" }
      test_strategy: { value: basic_io }
    outputs: [generated_tests, test_list]

  - id: compile_rtl
    type: tool
    tool: auto-eda-verilator
    action: compile
    inputs:
      rtl_files:  { value: "{{ params.rtl_files }}" }
      top_module: { value: "{{ params.top_module }}" }
      coverage:   { value: true }
    outputs: [compiled_model, compile_log]
    timeout_sec: 600

  - id: run_regression
    type: tool
    tool: auto-eda-cocotb
    action: run_regression
    inputs:
      test_list:      { ref: discover_tests, port: test_list }
      compiled_model: { ref: compile_rtl, port: compiled_model }
      simulator:      { value: "{{ params.simulator }}" }
      testbench_dir:  { value: "{{ params.testbench_dir }}" }
    outputs: [regression_results, passed, failed, waveform_dir]
    timeout_sec: 3600

  - id: coverage_analysis
    type: tool
    tool: auto-eda-verilator
    action: coverage_report
    inputs:
      compiled_model: { ref: compile_rtl, port: compiled_model }
      waveform_dir:   { ref: run_regression, port: waveform_dir }
    outputs: [coverage_report, line_coverage, branch_coverage]
    depends_on: [run_regression]

  - id: check_coverage
    type: condition
    condition: "line_coverage >= params.coverage_goal"
    inputs:
      line_coverage: { ref: coverage_analysis, port: line_coverage }
    branches:
      true_branch:  [final_report]
      false_branch: [coverage_gap_report]

  - id: coverage_gap_report
    type: tool
    tool: auto-eda-cocotb
    action: analyze_coverage_gaps
    inputs:
      coverage_report: { ref: coverage_analysis, port: coverage_report }
      rtl_files:       { value: "{{ params.rtl_files }}" }
    outputs: [uncovered_lines, suggested_tests]

  - id: final_report
    type: tool
    tool: auto-eda-cocotb
    action: analyze_results
    inputs:
      regression_results: { ref: run_regression, port: regression_results }
      coverage_report:    { ref: coverage_analysis, port: coverage_report }
      lint_report:        { ref: lint_check, port: lint_report }
    outputs: [summary_report]

artifacts:
  outputs:
    - { node: final_report, port: summary_report, label: verification_summary }
    - { node: coverage_analysis, port: coverage_report, label: coverage_report }
    - { node: run_regression, port: regression_results, label: test_results }
```


## 7. 工作流MCP Tool接口

### 7.1 工作流引擎MCP Server工具列表

工作流引擎本身作为一个独立的MCP Server（`auto-eda-workflow`）暴露，提供以下工具：

| Tool名称 | 功能 | 关键参数 |
|---------|------|----------|
| `list_templates` | 列出所有可用工作流模板 | `tag_filter` |
| `get_template` | 获取模板详情和参数说明 | `template_id` |
| `create_workflow` | 从模板或自定义YAML创建工作流实例 | `template_id` 或 `workflow_yaml`, `parameters` |
| `validate_workflow` | 验证工作流YAML（不执行） | `workflow_yaml` |
| `run_workflow` | 启动工作流执行 | `workflow_id`, `parameters`, `async_mode` |
| `get_workflow_status` | 查询工作流和各节点状态 | `run_id`, `verbose` |
| `pause_workflow` | 暂停运行中的工作流 | `run_id` |
| `resume_workflow` | 恢复暂停的工作流 | `run_id` |
| `cancel_workflow` | 取消工作流（可选清理产物） | `run_id`, `cleanup` |
| `retry_node` | 重试指定失败节点 | `run_id`, `node_id` |
| `get_artifacts` | 获取工作流产物列表和下载路径 | `run_id`, `label_filter` |
| `list_runs` | 列出历史运行记录 | `workflow_id`, `status_filter`, `limit` |
| `diff_runs` | 对比两次运行的参数和结果差异 | `run_id_a`, `run_id_b` |

### 7.2 核心工具详细规范

#### `create_workflow`

```python
@mcp.tool()
async def create_workflow(
    template_id: Optional[str] = None,
    workflow_yaml: Optional[str] = None,
    parameters: Dict[str, Any] = {},
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    从模板ID或YAML字符串创建工作流实例。
    template_id 和 workflow_yaml 二选一，template_id优先。
    parameters 覆盖模板默认参数值。
    返回: { workflow_id, validation_result, parameter_summary }
    """
```

**使用示例（自然语言触发）**：
```
用户: 帮我对 counter.v 运行完整的RTL-to-GDSII流程，目标时钟100MHz
LLM → create_workflow(
    template_id="rtl-to-gdsii-sky130",
    parameters={
        "rtl_files": ["/path/to/counter.v"],
        "top_module": "counter",
        "target_clock_mhz": 100.0
    }
)
```

#### `run_workflow`

```python
@mcp.tool()
async def run_workflow(
    workflow_id: str,
    async_mode: bool = True,
    resume_from_checkpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    启动工作流执行。
    async_mode=True: 立即返回run_id，工作流后台运行
    async_mode=False: 阻塞直到完成（适合短工作流）
    resume_from_checkpoint: 从指定检查点标签恢复
    返回: { run_id, status, started_at, estimated_duration_sec }
    """
```

#### `get_workflow_status`

```python
@mcp.tool()
async def get_workflow_status(
    run_id: str,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    查询工作流运行状态。
    verbose=False: 返回整体状态和进度百分比
    verbose=True:  返回每个节点的详细状态、耗时、输入输出摘要
    返回: {
        run_id, status, progress_pct,
        completed_nodes, running_nodes, failed_nodes,
        elapsed_sec, estimated_remaining_sec,
        nodes: { node_id: { status, started_at, duration_sec, error? } }
    }
    """
```

### 7.3 进度报告机制

工作流引擎通过两种机制向LLM报告进度：

**机制一：轮询模式（推荐用于长流程）**
```
LLM → run_workflow(async_mode=True) → { run_id: "run_001" }

# 每30秒轮询一次
LLM → get_workflow_status(run_id="run_001")
     ← { status: running, progress_pct: 45,
         running_nodes: ["place_design"],
         completed_nodes: ["parse_rtl", "gen_sdc", "synthesize", "init_floorplan"],
         elapsed_sec: 1240, estimated_remaining_sec: 1500 }
```

**机制二：MCP Sampling回调（推荐用于交互式场景）**

引擎在关键节点完成时主动通过MCP `sampling/createMessage` 回调LLM：
```python
# 节点完成时触发
await mcp.sampling.create_message(
    messages=[{
        "role": "user",
        "content": f"[工作流进度] {node_id} 完成\n"
                   f"进度: {progress_pct}%\n"
                   f"输出摘要: {output_summary}"
    }]
)
```

触发回调的关键节点事件：
- 任意 `checkpoint` 节点完成
- 任意节点失败（附带错误诊断）
- `condition` 节点分支决策（报告选择了哪条路径及原因）
- `loop` 节点每轮完成（报告当前指标是否收敛）
- 工作流整体完成或失败

### 7.4 错误处理与诊断

节点失败时，MCP Tool返回结构化错误对象，供LLM理解并向用户解释：

```json
{
  "run_id": "run_001",
  "failed_node": "synthesize",
  "error_code": "SYNTHESIS_TIMING_UNMET",
  "error_message": "综合后时序无法满足：WNS = -2.3ns，目标时钟周期 10ns",
  "diagnostic": {
    "likely_cause": "目标时钟频率过高或RTL存在长组合逻辑路径",
    "critical_path": "counter_reg[7] → adder_out → counter_reg[0]",
    "suggestions": [
      "降低目标时钟频率至 80MHz 后重试",
      "在关键路径中插入流水线寄存器",
      "使用 optimize_for=timing 选项重新综合"
    ]
  },
  "recoverable": true,
  "checkpoint_available": null
}
```


## 8. 跨工具数据传递机制

### 8.1 设计原则

跨工具数据传递是AUTO_EDA护城河一（A5 §3.1）的核心实现。原则：

- **自动映射优先**：引擎根据节点输出类型和下一节点输入类型自动选择转换器
- **惰性转换**：仅在需要时执行格式转换，避免不必要的IO
- **内容寻址存储**：中间产物按SHA256哈希命名，相同内容不重复存储
- **语义保持**：格式转换必须保留设计语义（如Liberty时序弧、DEF坐标系）

### 8.2 数据类型系统

```python
# workflow/data_types.py
from enum import Enum

class ArtifactType(Enum):
    # HDL源文件
    VERILOG_SOURCE    = "verilog_source"       # .v / .sv
    VHDL_SOURCE       = "vhdl_source"          # .vhd
    # 网表
    YOSYS_JSON_NETLIST = "yosys_json_netlist"  # Yosys JSON格式
    BLIF_NETLIST      = "blif_netlist"         # .blif
    VERILOG_NETLIST   = "verilog_netlist"      # 门级Verilog网表
    # 物理设计
    DEF_FILE          = "def_file"             # .def
    LEF_FILE          = "lef_file"             # .lef
    GDSII_FILE        = "gdsii_file"           # .gds
    OASIS_FILE        = "oasis_file"           # .oas
    # 约束与时序
    SDC_FILE          = "sdc_file"             # .sdc
    LIBERTY_FILE      = "liberty_file"         # .lib
    SPEF_FILE         = "spef_file"            # .spef
    SDF_FILE          = "sdf_file"             # .sdf
    # PCB
    KICAD_PROJECT     = "kicad_project"        # .kicad_pro
    KICAD_PCB         = "kicad_pcb"            # .kicad_pcb
    GERBER_ARCHIVE    = "gerber_archive"       # .zip of gerbers
    # 仿真
    VCD_WAVEFORM      = "vcd_waveform"         # .vcd
    FST_WAVEFORM      = "fst_waveform"         # .fst
    SPICE_NETLIST     = "spice_netlist"        # .sp / .cir
    # 报告（结构化JSON）
    SYNTHESIS_REPORT  = "synthesis_report"
    TIMING_REPORT     = "timing_report"
    DRC_REPORT        = "drc_report"
    COVERAGE_REPORT   = "coverage_report"
    POWER_REPORT      = "power_report"
```

### 8.3 自动类型转换注册表

```python
# workflow/converters.py

CONVERTER_REGISTRY: Dict[Tuple[ArtifactType, ArtifactType], Callable] = {
    # Yosys JSON网表 → 门级Verilog网表
    (ArtifactType.YOSYS_JSON_NETLIST, ArtifactType.VERILOG_NETLIST):
        converters.yosys_json_to_verilog,

    # 门级Verilog网表 → BLIF（用于FPGA映射）
    (ArtifactType.VERILOG_NETLIST, ArtifactType.BLIF_NETLIST):
        converters.verilog_to_blif,

    # DEF → GDSII（通过KLayout Python API）
    (ArtifactType.DEF_FILE, ArtifactType.GDSII_FILE):
        converters.def_to_gdsii_via_klayout,

    # GDSII → OASIS
    (ArtifactType.GDSII_FILE, ArtifactType.OASIS_FILE):
        converters.gdsii_to_oasis_via_gdstk,

    # KiCad网表 → SPICE网表
    (ArtifactType.KICAD_PROJECT, ArtifactType.SPICE_NETLIST):
        converters.kicad_to_spice,

    # VCD → FST（压缩波形）
    (ArtifactType.VCD_WAVEFORM, ArtifactType.FST_WAVEFORM):
        converters.vcd_to_fst,
}

def find_conversion_path(
    src: ArtifactType,
    dst: ArtifactType
) -> Optional[List[Callable]]:
    """BFS搜索最短转换路径，支持多步转换"""
    if src == dst:
        return []
    # BFS实现...
```

### 8.4 中间产物管理（Artifact Manager）

```python
# workflow/artifact_manager.py
import hashlib, json
from pathlib import Path

class ArtifactManager:
    """
    内容寻址存储：文件按 SHA256(content) 命名存储，
    同一内容无论产生多少次只存储一份。
    """
    def __init__(self, store_root: Path):
        self.store_root = store_root
        self.db_path = store_root / "artifacts.sqlite"

    def store(self, content: bytes, artifact_type: ArtifactType,
              run_id: str, node_id: str, port: str) -> str:
        """存储产物，返回 artifact_id（SHA256前16位）"""
        sha = hashlib.sha256(content).hexdigest()
        artifact_id = sha[:16]
        dest = self.store_root / sha[:2] / sha
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes(content)
        self._record_metadata(artifact_id, artifact_type,
                              run_id, node_id, port, str(dest))
        return artifact_id

    def retrieve(self, artifact_id: str) -> Tuple[bytes, ArtifactType]:
        """按ID检索产物内容和类型"""
        meta = self._get_metadata(artifact_id)
        content = Path(meta["path"]).read_bytes()
        return content, ArtifactType(meta["type"])

    def get_path(self, artifact_id: str) -> Path:
        """获取产物文件路径（供工具直接访问文件）"""
        meta = self._get_metadata(artifact_id)
        return Path(meta["path"])

    def cleanup_run(self, run_id: str, keep_final: bool = True):
        """清理中间产物，可选保留最终输出"""
```

### 8.5 工具输出→输入自动映射流程

```
节点A执行完成
    │
    ▼
输出端口 netlist_json 产生 ArtifactType.YOSYS_JSON_NETLIST
    │
    ▼
引擎解析节点B的输入声明:
  inputs:
    netlist: { ref: nodeA, port: netlist_json }
    │
    ▼
查找节点B的 action 在MCP Server中的参数类型声明:
  init_floorplan.netlist 期望类型: VERILOG_NETLIST
    │
    ▼
类型匹配检查:
  YOSYS_JSON_NETLIST != VERILOG_NETLIST
    │
    ▼
find_conversion_path(YOSYS_JSON_NETLIST, VERILOG_NETLIST)
  → [yosys_json_to_verilog]
    │
    ▼
执行转换器，产生新产物 VERILOG_NETLIST
    │
    ▼
将转换后路径注入节点B的实际输入
```

### 8.6 工作目录管理

```
工作目录结构:
runs/
  {workflow_id}/
    {run_id}/
      params.json          # 本次运行参数快照
      state.sqlite         # 检查点状态数据库
      nodes/
        {node_id}/
          inputs/          # 输入产物软链接
          outputs/         # 输出产物
          logs/
            stdout.log
            stderr.log
      artifacts/           # 内容寻址存储
        {sha[:2]}/
          {sha256_full}    # 实际文件内容
      final/               # 声明为工作流输出的产物硬链接
        final_gds.gds
        timing_report.json
        drc_report.json
```

### 8.7 数据验证节点

在关键数据传递点插入 `validate` 节点，防止静默错误向下传播：

```yaml
- id: validate_netlist
  type: validate
  inputs:
    netlist: { ref: synthesize, port: netlist_json }
  schema:
    type: object
    required: [modules, cells, ports]
    properties:
      cells:
        type: array
        minItems: 1
        description: 网表至少包含一个门单元
  on_failure: abort    # abort | warn | skip
  depends_on: [synthesize]
```

**内置验证规则库**：

| 验证规则 | 适用场景 | 检查内容 |
|---------|---------|----------|
| `netlist_non_empty` | 综合后 | 网表包含至少1个单元 |
| `no_drc_violations` | DRC后 | drc_violations == 0 |
| `timing_met` | STA后 | wns >= 0 且 tns >= 0 |
| `coverage_threshold` | 验证后 | line_coverage >= threshold |
| `gds_non_empty` | 流片前 | GDS文件大小 > 1KB |
| `erc_clean` | PCB ERC后 | erc_errors == 0 |


## 9. 检查点与恢复机制

### 9.1 检查点存储设计

使用SQLite作为检查点数据库，保证原子写入和跨平台兼容：

```sql
-- workflow/schema.sql
CREATE TABLE workflow_runs (
    run_id       TEXT PRIMARY KEY,
    workflow_id  TEXT NOT NULL,
    status       TEXT NOT NULL,
    parameters   TEXT NOT NULL,
    started_at   REAL NOT NULL,
    finished_at  REAL,
    checkpoint_label TEXT
);

CREATE TABLE node_executions (
    run_id       TEXT NOT NULL,
    node_id      TEXT NOT NULL,
    attempt      INTEGER NOT NULL DEFAULT 1,
    status       TEXT NOT NULL,
    started_at   REAL,
    finished_at  REAL,
    inputs_used  TEXT,
    outputs      TEXT,
    error        TEXT,
    PRIMARY KEY (run_id, node_id)
);

CREATE TABLE artifacts (
    artifact_id   TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    run_id        TEXT NOT NULL,
    node_id       TEXT NOT NULL,
    port          TEXT NOT NULL,
    file_path     TEXT NOT NULL,
    size_bytes    INTEGER,
    created_at    REAL NOT NULL
);

CREATE TABLE checkpoints (
    checkpoint_id    TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    label            TEXT NOT NULL,
    created_at       REAL NOT NULL,
    completed_nodes  TEXT NOT NULL,
    UNIQUE(run_id, label)
);
```

### 9.2 检查点触发时机

1. **Checkpoint节点执行**：工作流中显式定义的 `type: checkpoint` 节点
2. **每个节点成功后**：轻量级检查点（仅更新 `node_executions` 表）
3. **Parallel节点join完成**：并行分支全部汇聚后
4. **Loop节点每轮结束**：保存当前迭代状态
5. **工作流完成/失败**：最终状态持久化

### 9.3 恢复流程

```python
class CheckpointManager:
    async def resume_from_label(
        self, run_id: str, checkpoint_label: str
    ) -> WorkflowRun:
        cp = self.db.get_checkpoint(run_id, checkpoint_label)
        run = self.db.get_run(run_id)
        completed_at_cp = set(json.loads(cp.completed_nodes))
        for node_id, ex in run.node_states.items():
            if node_id not in completed_at_cp:
                ex.status = NodeStatus.PENDING
                ex.error = None
                ex.outputs = {}
        run.status = WorkflowStatus.RUNNING
        return run

    async def save(self, run: WorkflowRun):
        with self.db.transaction():
            self.db.upsert_run(run)
            for node_id, ex in run.node_states.items():
                self.db.upsert_node_execution(run.run_id, ex)
```

### 9.4 恢复场景示例

**场景：RTL-to-GDSII流程在布线后断电**

```
恢复前（来自检查点 after_routing）:
  SUCCEEDED: parse_rtl, gen_sdc, synthesize, init_floorplan,
             place_design, clock_tree_synthesis, route_design
  PENDING:   timing_closure, drc_check, stream_gds

MCP调用:
  run_workflow(workflow_id="wf_001", resume_from_checkpoint="after_routing")

结果: 引擎跳过前7个节点，从 timing_closure 继续
节省: ~3-4小时（综合+布局+CTS+布线耗时）
```

### 9.5 检查点相关MCP工具

```python
@mcp.tool()
async def list_checkpoints(run_id: str) -> List[Dict]:
    """列出指定运行的所有可用检查点。
    返回: [{ checkpoint_id, label, created_at, completed_node_count }]"""

@mcp.tool()
async def resume_workflow(
    run_id: str,
    checkpoint_label: Optional[str] = None,
) -> Dict[str, Any]:
    """从检查点恢复工作流。checkpoint_label=None 从最新检查点恢复。
    返回: { new_run_id, resumed_from, skipped_nodes, pending_nodes }"""
```

---

## 10. 实施路线图

### 10.1 与A8 Phase 2-3的对应关系

| A8阶段 | 工作流引擎对应工作 | 时间 |
|--------|-------------------|------|
| Phase 2 (Month 5-6) | 引擎核心：DAG数据结构、状态机、SQLite检查点、YAML解析器 | Month 5 |
| Phase 2 (Month 7-8) | 模板一（RTL-to-GDSII）、模板二（PCB）、MCP Tool接口 | Month 6-7 |
| Phase 3 (Month 9-10) | 模板三（功能验证）、自动类型转换、Artifact Manager | Month 8 |
| Phase 3 (Month 11-12) | 并行执行引擎（asyncio）、Loop节点、设计空间探索模板 | Month 9-10 |

### 10.2 Phase 2实施细节（Month 5-8）

#### Month 5: 引擎基础层

**交付物**:
- `workflow/models.py`：DAG数据结构完整实现
- `workflow/parser.py`：YAML/JSON解析器 + 格式验证
- `workflow/engine.py`：顺序执行引擎（暂不支持并行）
- `workflow/checkpoint.py`：SQLite检查点管理器
- `auto-eda-workflow` MCP Server骨架（4个基础工具）

**验收标准**:
- [ ] 可解析本文档中所有YAML模板（无报错）
- [ ] 5节点线性工作流可端到端执行
- [ ] 中断后从检查点恢复不丢失已完成节点
- [ ] `get_workflow_status` 返回正确进度

#### Month 6-7: 模板层 + 并行执行

**交付物**:
- asyncio并行执行引擎（支持Parallel节点）
- Condition节点（JMESPath表达式引擎）
- 模板一（RTL-to-GDSII）完整验证（使用SkyWater 130nm PDK）
- 模板二（PCB）完整验证（使用KiCad示例工程）
- `auto-eda-workflow` MCP Server完整13个工具

**验收标准**:
- [ ] RTL-to-GDSII模板成功运行counter.v示例（端到端GDSII输出）
- [ ] PCB模板成功运行KiCad示例工程（Gerber输出）
- [ ] 并行节点实际并发执行（时间 < 串行总时间）
- [ ] 条件分支按照表达式正确选择路径

#### Month 8: 数据管道层

**交付物**:
- ArtifactType类型系统
- 自动类型转换注册表（10+转换对）
- ArtifactManager（内容寻址存储）
- 数据验证节点（Validate）
- 模板三（功能验证）完整验证

**验收标准**:
- [ ] Yosys JSON网表自动转换为门级Verilog（供OpenROAD使用）
- [ ] DEF自动转换为GDSII（通过KLayout）
- [ ] validate节点在网表为空时正确中止工作流
- [ ] 验证模板成功运行（cocotb测试通过，覆盖率>90%）

### 10.3 Phase 3实施细节（Month 9-12）

#### Month 9-10: Loop节点 + 设计空间探索

**交付物**:
- Loop节点（带exit_condition和max_iterations）
- 时序收敛循环模板（嵌入RTL-to-GDSII）
- 设计空间探索模板（PPA参数扫描）
- MCP Sampling回调进度报告

#### Month 11-12: 多Agent编排集成

**交付物**:
- 工作流引擎与多Agent框架集成（A8 §2.5.1）
- Agent角色到工作流子图的映射
- 跨工具PPA优化闭环（A8 §2.5.3）
- 社区模板贡献规范和注册表

### 10.4 依赖关系

```
工作流引擎依赖的MCP Server就绪时间线:

Month 1-2 (Phase 0):
  ✓ auto-eda-yosys
  ✓ auto-eda-kicad
  ✓ auto-eda-verilog-utils

Month 3-4 (Phase 1):
  ✓ auto-eda-verilator
  ✓ auto-eda-cocotb
  ✓ auto-eda-klayout

Month 5-8 (Phase 2, 与引擎并行开发):
  ✓ auto-eda-openroad      ← 模板一必需
  ✓ auto-eda-opensta       ← 时序签核必需
  ✓ auto-eda-openlane      ← 高层编排可选

Month 5开始引擎开发时，Phase 0工具已就绪，
可先用Yosys+KiCad+Verilog-utils验证引擎基础功能。
OpenROAD在Month 5-6期间并行就绪，恰好供Month 6-7模板一使用。
```

### 10.5 关键风险与缓解

| 风险 | 可能性 | 影响 | 缓解策略 |
|------|--------|------|----------|
| OpenROAD Python绑定API不稳定 | 中 | 高 | 提供TCL CLI fallback；锁定版本 |
| EDA工具执行时间超过LLM超时 | 高 | 中 | async_mode=True为默认；MCP Sampling回调保活 |
| YAML模板参数类型不匹配运行时错误 | 中 | 中 | 解析阶段严格类型检查；提供详细错误信息 |
| 并行节点资源竞争（CPU/内存）| 中 | 中 | 并行度限制参数（max_parallel_nodes）；资源感知调度 |
| 格式转换精度损失（如DEF→GDSII）| 低 | 高 | 每个转换器有单元测试；关键转换后插入validate节点 |

---

## 附录：工作流引擎技术选型汇总

| 组件 | 选型 | 理由 |
|------|------|------|
| 执行并发 | Python asyncio | 与FastMCP天然兼容；IO密集型EDA工具调用适合协程 |
| 条件表达式 | jmespath | 轻量级JSON查询；无安全风险（非eval） |
| 检查点存储 | SQLite | 零依赖；原子事务；跨平台 |
| YAML解析 | PyYAML + pydantic | 成熟生态；pydantic提供类型验证 |
| 参数模板渲染 | Jinja2 | 功能完整；`{{ params.x }}` 语法直观 |
| 内容寻址存储 | hashlib SHA256 | 标准库；与git对象模型概念一致 |
| 格式转换 | gdstk, pyverilog, liberty-parser | R7推荐的Python生态最优选择 |
| MCP Server框架 | FastMCP | R5/A8推荐；decorator-driven开发效率最高 |

---

## 总结

本文档完整定义了AUTO_EDA工作流引擎的设计方案，覆盖：

1. **DAG数据结构**：`WorkflowNode`、`WorkflowEdge`、`WorkflowDAG` 三层模型，支持拓扑排序和并行调度
2. **六种节点类型**：tool、condition、parallel、loop、checkpoint、validate，覆盖EDA流程所有控制流需求
3. **asyncio执行引擎**：事件驱动状态机，支持暂停/恢复/取消/重试
4. **YAML/JSON序列化规范**：声明式工作流定义，Jinja2参数模板，严格验证
5. **三个生产级模板**：RTL-to-GDSII（13步）、PCB设计（8步）、功能验证（10步）
6. **13个MCP Tool接口**：完整的创建/运行/查询/控制工具集，含MCP Sampling进度回调
7. **自动类型转换管道**：10+格式转换对，BFS最短路径搜索，内容寻址存储
8. **SQLite检查点机制**：4表数据库设计，支持标签化恢复，长流程断点续跑

该设计直接实现了A5 USP-1（多工具统一编排）和USP-4（跨EDA工作流自动化），是AUTO_EDA相对于MCP4EDA最核心的差异化能力，也是A8 Phase 2-3的核心交付物。
