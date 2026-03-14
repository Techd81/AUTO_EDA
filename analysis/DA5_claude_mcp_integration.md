# DA5: Claude Code通过MCP最大化操控EDA软件 — 深度集成分析

**文档编号**: DA5  
**日期**: 2026-03-14  
**依赖文档**: R8_claude_mcp_patterns.md, A7_tech_stack_decision.md  
**核心命题**: 如何让Claude Code通过MCP完成绝大部分EDA工作？

---

## 目录

1. [Claude Code MCP能力深度分析](#1-claude-code-mcp能力深度分析)
2. [EDA任务的Claude可自主完成度分析](#2-eda任务的claude可自主完成度分析)
3. [最大化Claude自主性的MCP工具设计原则](#3-最大化claude自主性的mcp工具设计原则)
4. [EDA专用System Prompt设计](#4-eda专用system-prompt设计)
5. [典型EDA任务的完整交互序列设计](#5-典型eda任务的完整交互序列设计)
6. [MCP Resources和Prompts的战略使用](#6-mcp-resources和prompts的战略使用)
7. [实现建议与优先级路线图](#7-实现建议与优先级路线图)

---

## 1. Claude Code MCP能力深度分析

### 1.1 tool_use机制的本质

Claude Code的MCP工具调用基于Anthropic tool_use协议。核心架构：

```
Claude推理引擎
    │
    ├─ 接收system prompt（含工具声明 + 领域知识）
    ├─ 分析用户意图
    ├─ 生成tool_use block（结构化JSON）
    │     {"type": "tool_use", "name": "run_simulation", "input": {...}}
    ├─ 等待tool_result（MCP服务器执行后返回）
    └─ 将tool_result纳入上下文，继续推理
```

**核心洞察**：Claude不是「执行工具」，而是「决策调用工具」。
工具返回值的质量和格式直接决定Claude下一步决策质量。

关键能力特性：
- 单次回复可发出多个**串行**tool_use（顺序依赖时）
- Claude Code支持**并行**tool_use（多个独立工具同时调用）
- tool_result可包含文本、图片、结构化数据
- 工具调用失败时Claude可**自主重试**或切换策略

### 1.2 多轮工具调用的上下文管理

```
上下文窗口结构（200k tokens）：

┌──────────────────────────────────────────────────────┐
│ System Prompt（EDA领域知识 + 工具声明）   ~8-15k tokens │
├──────────────────────────────────────────────────────┤
│ 对话历史累积                                           │
│   每次仿真日志返回：      ~2-5k tokens                 │
│   每次netlist读取：       ~5-20k tokens                │
│   每次timing report：    ~3-8k tokens                 │
│   一次完整RTL→GL流程：    ~50-100k tokens              │
└──────────────────────────────────────────────────────┘

上下文危机点：20-30轮工具调用后逼近限制
```

**缓解策略**：
1. 工具返回**摘要+关键指标**，原始数据存入Resource
2. 使用MCP Resources URI引用代替内联数据
3. 关键检查点主动调用`summarize_session`工具压缩
4. 按阶段分session（RTL仿真 / 综合 / 布局布线 各一session）

### 1.3 Claude Code vs Claude Desktop 能力差异

| 能力维度 | Claude Code | Claude Desktop |
|---------|-------------|----------------|
| MCP工具调用 | 完整支持 | 完整支持 |
| 并行工具调用 | 支持 | 支持 |
| 代码执行上下文 | 原生集成（bash/python） | 需MCP工具 |
| 文件系统访问 | 原生（Read/Write/Edit工具） | 需MCP |
| 长时任务监控 | 支持后台bash | 受限 |
| Subagent/Task | 支持（Task工具） | 不支持 |
| 费用模型 | API按token计费 | Pro订阅 |
| **EDA场景优势** | **原生代码+文件操作** | **图形界面交互** |

**AUTO_EDA战略选择**：Claude Code为主（自动化流程），Claude Desktop为辅（需要GUI交互的EDA工具）。

### 1.4 Sampling Primitive在EDA场景的应用

MCP Sampling允许MCP服务器**主动请求Claude推理**，无需用户干预：

```python
# EDA MCP服务器中的sampling应用场景
async def analyze_timing_violation(violation_data: dict):
    """当检测到timing violation时，主动请求Claude分析"""
    response = await mcp.sample({
        "messages": [{
            "role": "user",
            "content": f"Timing violation detected:\n{violation_data}\n"
                       f"Suggest fix strategy considering current constraints."
        }],
        "max_tokens": 1024,
        "system": EDA_EXPERT_SYSTEM_PROMPT
    })
    return response.content  # Claude的修复建议
```

**EDA高价值场景**：
- 仿真收敛失败时自动请求Claude诊断
- DRC违规批量分析（每批次调用sampling）
- 综合结果异常时请求Claude评估策略调整

---

## 2. EDA任务的Claude可自主完成度分析

### 五级自主度分类框架

```
L1 ─── 工具调用层    Claude 100%自主，单次调用即完成
L2 ─── 迭代优化层    Claude多轮推理，需要反馈循环
L3 ─── 流程编排层    Claude自主编排多工具EDA工作流
L4 ─── 决策确认层    需要人类确认的关键决策点
L5 ─── 创意设计层    当前Claude无法自主完成
```

### L1：Claude可100%自主完成的EDA操作（工具调用层）

这类操作有明确输入输出，Claude一次工具调用即可完成：

| 操作类别 | 具体任务 | MCP工具 | 自主度 |
|---------|---------|---------|-------|
| 文件操作 | 读取/解析Verilog文件 | `read_hdl_file` | 100% |
| 文件操作 | 生成testbench模板 | `generate_testbench` | 100% |
| 仿真控制 | 启动功能仿真 | `run_simulation` | 100% |
| 仿真控制 | 获取波形数据 | `get_waveform` | 100% |
| 报告解析 | 解析timing report | `parse_timing_report` | 100% |
| 报告解析 | 解析utilization report | `parse_util_report` | 100% |
| 约束管理 | 读取/验证XDC/SDC | `validate_constraints` | 100% |
| 网表操作 | 读取综合后netlist | `read_netlist` | 100% |
| 日志分析 | 提取错误/警告 | `parse_tool_log` | 100% |
| 版本控制 | 提交设计检查点 | `save_checkpoint` | 100% |

**关键特征**：这些操作Claude可在**零人工干预**下批量执行。

### L2：需要Claude多轮推理的EDA任务（迭代优化层）

这类任务需要「执行→观察→调整」循环，Claude自主迭代：

**示例：时序收敛优化**
```
轮次1: run_timing_analysis() → WNS=-2.3ns
轮次2: Claude分析关键路径 → 调整时序约束
轮次3: modify_constraints() → 重新综合
轮次4: run_timing_analysis() → WNS=-0.8ns
轮次5: 进一步调整 → WNS=+0.1ns（收敛）
```

| 任务 | 典型迭代轮次 | 终止条件 | Claude自主度 |
|-----|------------|---------|-------------|
| 时序收敛 | 3-8轮 | WNS>0 | 90%（极端情况需人介入） |
| 仿真调试 | 2-10轮 | 测试全通过 | 85% |
| 综合参数调优 | 3-6轮 | 面积/速度满足 | 90% |
| DRC违规修复 | 2-5轮 | 违规清零 | 75%（物理修复有限） |
| Lint检查修复 | 1-3轮 | 警告清零 | 95% |

### L3：Claude自主编排的EDA工作流（流程编排层）

Claude可**自主决定**工具调用顺序和条件分支：

**示例：RTL到门级网表的完整综合流程**
```
Claude自主编排序列：
1. validate_hdl_syntax()        # 先验证语法
2. IF errors: fix_syntax()      # 自主决定修复
3. run_elaboration()            # 展开设计
4. analyze_hierarchy()          # 分析层次
5. run_synthesis(strategy=...) # 选择综合策略
6. parse_synthesis_report()    # 评估结果
7. IF timing_fail: adjust_constraints() + re-synthesize
8. save_netlist()               # 保存结果
```

**Claude可自主编排的完整工作流**：
- RTL语法检查 → Lint → 功能仿真 → 覆盖率分析
- 逻辑综合 → 时序分析 → 约束优化
- 静态时序分析（STA）全流程
- 形式验证（等价性检查）流程
- FPGA实现全流程（综合→实现→比特流）

**不可自主编排（需到L4）**：
- 涉及流片决策的工作流
- 超过预算阈值的资源使用
- 变更已冻结的设计规范

### L4：需要人类确认的关键决策点（决策确认层）

这类决策涉及不可逆操作或重大资源承诺，AUTO_EDA必须暂停等待确认：

| 决策类型 | 触发条件 | 为何不能自主 |
|---------|---------|------------|
| 流片提交 | 准备提交GDS到foundry | 成本$50K-$500K，不可逆 |
| 设计规范变更 | 接口/时序规范修改 | 影响整个团队下游工作 |
| 工艺节点切换 | 换用不同PDK | 需重新评估全部约束 |
| 大规模重构 | 重新划分模块层次 | 影响验证计划和进度 |
| 第三方IP集成 | 引入商业IP核 | 许可证和法律问题 |
| 超预算计算 | 云端仿真费用预测>$1000 | 财务授权 |

**实现方式**：MCP工具返回`requires_human_approval: true`字段，Claude自动暂停并向用户说明原因。

### L5：当前Claude无法自主完成的EDA任务（创意设计层）

| 任务 | 原因 | 未来可能性 |
|-----|------|----------|
| 全新架构创意设计 | 需要系统级创造力，Claude只能在已有范式内优化 | 2-3年内部分可能 |
| 模拟电路拓扑选择 | 高度经验依赖，无法量化评估 | 需专用模拟设计数据集 |
| 物理设计直觉判断 | Floor plan美学+经验，无法形式化 | 需视觉推理突破 |
| 多目标全局最优 | NP-hard问题，Claude只能启发式 | 结合强化学习可能改善 |
| 跨域系统权衡 | 功耗/面积/速度/成本的全局最优 | 需多Agent协作 |

**务实结论**：L1-L3占EDA日常工作量的**70-80%**，这正是AUTO_EDA的核心价值域。

---

## 3. 最大化Claude自主性的MCP工具设计原则

### 3.1 工具粒度的黄金分割点

粒度过细（原子操作）会导致上下文爆炸（50+工具调用），粒度过粗（整流程）则失去灵活性。
最佳粒度是「**工作流步骤**」级别，每个Server 5-12个工具。

**最佳粒度判断标准**（来自R8研究）：
- 一个工具对应一个有意义的EDA工作流步骤
- 工具执行时间：30秒-10分钟（太短=原子操作，太长=超时风险）
- 工具返回的信息足够Claude做下一步决策
- 不超过每个Server 12个工具（超过LLM选择准确率下降）

```python
# 过细（错误）：每个Yosys pass一个工具 -> 导致20+次调用
@mcp.tool() async def run_synth_proc(): ...
@mcp.tool() async def run_flatten(): ...
@mcp.tool() async def run_techmap(): ...

# 过粗（错误）：整个RTL->GDSII一个工具 -> 无法干预中间步骤
@mcp.tool() async def run_full_flow(): ...

# 恰当（正确）：按工作流阶段划分
@mcp.tool() async def synthesize_rtl(top_module, target_library, strategy): ...
@mcp.tool() async def run_place_and_route(netlist, constraints, floorplan): ...
@mcp.tool() async def run_static_timing_analysis(design, sdc): ...
@mcp.tool() async def run_drc_check(gds, rules): ...
```

### 3.2 返回格式：结构化JSON vs 文本描述

**核心原则**：机器决策用JSON字段，人类展示用summary字段，两者必须同时提供。

```python
@mcp.tool()
async def run_synthesis(top_module: str, strategy: str) -> dict:
    result = await yosys.synthesize(...)
    return {
        # 1. 决策字段（Claude用于下一步判断）
        "status": "success",
        "timing_met": True,
        "wns_ns": 0.15,
        "cell_count": 4521,
        "warnings_count": 3,
        "critical_warnings": ["Latch inferred in module counter"],

        # 2. 摘要字段（Claude可直接向用户报告）
        "summary": "综合成功：4521个单元，WNS=+0.15ns，3条警告",

        # 3. 后续行动建议（引导Claude自主决策）
        "suggested_next_steps": ["run_timing_analysis", "check_warnings"],

        # 4. 大数据引用（避免内联，节省上下文）
        "full_report_uri": "eda://reports/synth_001",
        "netlist_uri": "eda://netlists/top_synth.v"
    }
```

`suggested_next_steps`字段是引导Claude自主推进的核心机制，Claude会优先参考工具建议形成自然的流程推进。

### 3.3 状态注入：通过工具返回值引导Claude决策

三种状态注入模式：

**模式A：显式建议**（最直接）
```json
{"suggested_next_steps": ["run_place_and_route"], "reason": "synthesis passed"}
```

**模式B：条件上下文**（提供决策信息，Claude自主推断）
```json
{"timing_violations": 12, "fixable_by_constraints": 8, "requires_rtl_change": 4}
```
Claude会自主推断：先修约束（成功率高），再改RTL（成本高）。

**模式C：设计状态快照**（完整上下文，支持断点恢复）
```json
{
  "design_state": {
    "stage": "post-synthesis",
    "completed_steps": ["lint", "sim", "synth"],
    "pending_steps": ["pnr", "sta", "drc"],
    "blocking_issues": []
  }
}
```
Claude可从任意断点恢复工作流，无需用户重新描述进度。

### 3.4 错误消息设计：让Claude能自主修复

错误消息必须包含四要素：具体原因、可尝试的修复方案（按成功概率排序）、相关文件位置、是否可重试。

```python
# 差的错误（Claude无法自主修复）
return {"status": "failed", "error": "Synthesis failed"}

# 好的错误（Claude可自主尝试修复）
return {
    "status": "failed",
    "error_code": "TIMING_VIOLATION",
    "error_message": "时序约束未满足：WNS=-3.2ns",
    "root_cause": "关键路径经过 alu_core/multiply_unit，组合逻辑深度过大",
    "suggested_fixes": [
        {"action": "tighten_clock_groups",    "success_probability": 0.7},
        {"action": "pipeline_critical_path",  "success_probability": 0.9},
        {"action": "reduce_clock_frequency",  "success_probability": 0.95}
    ],
    "related_files": ["constraints/top.sdc"],
    "retryable": True,
    "retry_with_params": {"strategy": "timing_driven"}
}
```

`suggested_fixes`按成功概率排序，Claude优先尝试高概率方案，形成有效的自主修复循环。

### 3.5 长时任务的Progress Reporting

EDA工具运行时间从秒级到小时级，需按任务时长选择不同策略：

| 任务时长 | 策略 | 实现方式 |
|---------|------|--------|
| <30秒 | 同步返回 | 直接await结果 |
| 30秒-10分钟 | 分阶段streaming | yield进度dict |
| >10分钟 | 异步任务句柄 | 返回job_id + poll工具 |

```python
# 异步任务模式（>10分钟的仿真/综合）
@mcp.tool()
async def start_long_simulation(testbench: str) -> dict:
    job_id = await sim_engine.submit(testbench)
    return {
        "job_id": job_id,
        "estimated_duration_minutes": 45,
        "poll_tool": "get_simulation_status",  # 告诉Claude用什么工具轮询
        "poll_interval_seconds": 30
    }

@mcp.tool()
async def get_simulation_status(job_id: str) -> dict:
    status = await sim_engine.query(job_id)
    return {
        "phase": status.current_phase,   # "compile"|"elaborate"|"simulate"
        "completion_pct": status.pct,
        "estimated_remaining_minutes": status.eta,
        "done": status.is_complete,
        "result_uri": status.result_uri if status.is_complete else None
    }
```

Claude收到`poll_tool`字段后，会自主按`poll_interval_seconds`间隔轮询，无需用户介入。

---

## 4. EDA专用System Prompt设计

### 4.1 System Prompt结构

EDA场景的System Prompt需要注入四类信息：

```
SYSTEM PROMPT结构（总计约8-12k tokens）：

1. 角色定义（~500 tokens）
2. EDA领域知识（~3-5k tokens）
3. 安全约束（~1k tokens）
4. 工作流偏好（~1-2k tokens）
5. 工具使用指引（~1-2k tokens）
```

### 4.2 角色定义与领域知识注入

```
你是AUTO_EDA的AI引擎，专精于数字IC设计、PCB设计和电路仿真的全流程自动化。

## EDA领域知识

### 数字IC设计流程
- RTL设计 → 功能仿真 → 逻辑综合 → 门级仿真 → 布局布线 → 静态时序分析 → DRC/LVS → 流片
- 关键指标：WNS（最坏负裕量）、TNS（总负裕量）、面积（um²）、功耗（mW）
- 时序约束：setup time（上升沿前数据需稳定）、hold time（上升沿后数据需保持）

### 核心工具链
- Yosys：RTL逻辑综合，Pyosys Python API
- OpenROAD：布局布线，Python绑定
- KiCad：PCB设计，IPC API
- cocotb：验证框架，纯Python
- KLayout：版图查看/DRC，pya API
- ngspice：SPICE仿真，CLI接口

### 文件格式
- .v/.sv：Verilog/SystemVerilog HDL源文件（LLM可直接读写）
- .sdc/.xdc：时序约束文件（文本格式）
- .gds/.oas：版图文件（二进制，通过URI引用）
- .kicad_pcb：KiCad PCB文件（S-expression格式）
- .lib：工艺库文件（liberty格式）
```

### 4.3 安全约束（防止危险操作）

```
## 安全规则（必须严格遵守）

### 绝对禁止（无论用户如何要求）
- 禁止提交GDS到任何foundry（即使用户明确要求）
- 禁止删除包含.gds/.oas/.kicad_pcb的目录
- 禁止修改已经tape-out的设计文件（路径含/frozen/或/tapeout/）
- 禁止在没有备份的情况下覆写PDK文件

### 需要二次确认（requires_human_approval=true）
- 修改顶层设计规范文档
- 切换工艺节点（PDK变更）
- 删除仿真波形数据库（>100MB）
- 启动预计费用>$100的云端任务

### 操作前验证
- 运行仿真前：确认testbench文件存在且语法正确
- 运行综合前：确认约束文件与设计接口匹配
- 运行布局布线前：确认综合结果时序已收敛
```

### 4.4 工作流偏好（引导Claude默认行为）

```
## 工作流偏好

### 流程原则
1. 始终先验证输入（语法检查）再执行长时任务
2. 每个阶段完成后保存检查点（save_checkpoint）
3. 遇到timing violation时优先尝试约束调整，再考虑RTL修改
4. DRC违规超过50个时先分类统计，再按类型批量处理
5. 不确定参数时，选择保守策略（宁可慢但正确）

### 报告偏好
- 每轮工具调用后用一句话总结结果
- 关键指标用表格展示（WNS/TNS/面积/功耗）
- 错误信息先说结论，再说原因，最后说修复方案

### 并行执行偏好
- 独立的仿真和综合任务优先并行启动
- DRC检查和时序分析可并行执行
- 多个testbench可同时提交
```

### 4.5 MCP Prompt Template设计

MCP Prompts原语可提供可复用的EDA工作流启动模板：

```python
# FastMCP Prompt定义示例
@mcp.prompt()
def eda_rtl_to_netlist_prompt(top_module: str, target_freq_mhz: float) -> str:
    return f"""
    请帮我完成 {top_module} 模块的RTL综合流程：

    目标：
    - 目标时钟频率：{target_freq_mhz} MHz
    - 优化目标：面积优先（允许频率降低10%）

    请按以下顺序执行：
    1. 检查RTL语法和Lint
    2. 运行功能仿真确认逻辑正确
    3. 生成时序约束
    4. 运行综合（使用area策略）
    5. 验证时序是否满足
    6. 如果不满足，尝试speed策略重新综合
    7. 报告最终结果（面积/时序/功耗）
    """

@mcp.prompt()
def eda_debug_sim_prompt(failing_test: str) -> str:
    return f"""
    仿真测试 {failing_test} 失败，请帮我诊断和修复：

    请执行：
    1. 获取失败的波形数据
    2. 识别第一个失败的断言
    3. 追踪信号传播路径
    4. 定位RTL中的问题
    5. 提出修复方案（不要直接修改，先征求确认）
    """
```

用户只需在Claude Code中输入 `/eda_rtl_to_netlist_prompt top=counter freq=100`，
Claude即获得完整的执行指引，无需重复描述流程。

---

## 5. 典型EDA任务的完整交互序列设计

### 5.1 序列一：「设计并验证一个4位计数器」

**用户输入**：「帮我设计一个4位同步计数器，支持同步复位，目标频率200MHz，用Yosys综合到sky130工艺」

**完整Claude+MCP交互序列**：

```
轮次 | Claude行为              | MCP工具调用                      | 上下文消耗
-----|------------------------|----------------------------------|----------
  1  | 分析需求，生成RTL代码     | write_hdl_file("counter.v")      | ~2k tokens
  2  | 生成testbench           | write_hdl_file("counter_tb.v")   | ~1.5k
  3  | 语法验证                | validate_hdl_syntax("counter.v") | ~0.5k
  4  | 启动功能仿真             | run_simulation("counter_tb.v")   | ~1k
  5  | 检查仿真结果             | get_simulation_results()         | ~2k
  6  | 生成时序约束             | write_sdc("counter.sdc", 200MHz) | ~0.5k
  7  | 运行Yosys综合            | synthesize_rtl("counter.v",      |
     |                        |   "sky130", "balanced")          | ~3k
  8  | 分析综合报告             | (结果内联返回，含WNS/面积)          | ~1k
  9  | WNS=+0.3ns，时序满足    | run_gate_sim(netlist, tb)        | ~1k
  10 | 验证门级仿真通过          | save_checkpoint("v1_complete")   | ~0.5k
  11 | 向用户报告最终结果        | (无工具调用)                       | ~1k
```

**统计**：
- 工具调用次数：10次
- 总上下文消耗：~14k tokens（含system prompt ~10k = 共~24k，远低于200k上限）
- 用户干预次数：0次（全自主）
- 预计耗时：3-5分钟
- Claude自主度：**100%**（标准流程无需人介入）

```
交互序列图：

用户                  Claude              Digital IC MCP Server
 |                      |                         |
 |-- "设计4位计数器" --> |                         |
 |                      |-- write_hdl_file ------> |
 |                      |<-- {uri, status} -------- |
 |                      |-- validate_syntax ------> |
 |                      |<-- {valid: true} --------- |
 |                      |-- run_simulation -------> |
 |                      |<-- {passed: 4/4} --------- |
 |                      |-- synthesize_rtl -------> |
 |                      |<-- {wns:+0.3, area:...} -- |
 |                      |-- run_gate_sim ---------> |
 |                      |<-- {passed: 4/4} --------- |
 |                      |-- save_checkpoint ------> |
 |<-- 「计数器设计完成」 |                         |
```

### 5.2 序列二：「帮我优化这个PCB的布局」

**用户输入**：「我的KiCad PCB有严重的EMI问题，帮我分析并优化去耦电容布局」

**完整交互序列**：

```
轮次 | Claude行为                    | MCP工具调用                        | 备注
-----|------------------------------|------------------------------------|---------
  1  | 读取PCB文件结构               | read_pcb_file("board.kicad_pcb")   |
  2  | 截图查看当前布局              | screenshot_pcb_layout()            | 可视化！
  3  | 分析电源网络拓扑              | analyze_power_nets()               |
  4  | 定位去耦电容位置              | find_components(type="capacitor")  |
  5  | 识别EMI问题（电容离IC太远）   | measure_component_distances()      |
  6  | 制定优化方案                 | (Claude推理，无工具)                |
  7  | 移动去耦电容到IC电源引脚旁    | move_components(caps, targets)     |
  8  | 截图验证新布局               | screenshot_pcb_layout()            | 可视化验证
  9  | Claude视觉分析新布局         | (分析截图，确认改善)                |
  10 | 运行DRC检查                 | run_drc()                          |
  11 | 检查无新增违规              | (DRC passed)                       |
  12 | 更新铜皮填充                | update_copper_fill()               |
  13 | 最终截图确认                | screenshot_pcb_layout()            |
  14 | 向用户报告改善结果          | (无工具调用)                        |
```

**关键特点**：此序列展示AUTO_EDA的核心差异化——**可视化反馈闭环**。
Claude通过截图工具获得PCB视觉信息，做出人类工程师级别的布局判断。

**统计**：工具调用次数13次，预计耗时5-8分钟，Claude自主度**90%**。

```
交互序列图（含可视化闭环）：

用户              Claude           PCB MCP Server      KiCad进程
 |                  |                    |                  |
 |-- "优化EMI" --> |                    |                  |
 |                  |-- read_pcb ------> |-- 解析文件 ------> |
 |                  |<-- {nets,comps} -- |                  |
 |                  |-- screenshot ----> |-- 渲染截图 ------> |
 |                  |<-- {image:b64} --- |                  |
 |                  | [Claude视觉分析]    |                  |
 |                  |-- move_comps ----> |-- 修改坐标 ------> |
 |                  |-- screenshot ----> |-- 渲染截图 ------> |
 |                  |<-- {image:b64} --- |                  |
 |                  | [Claude确认改善]    |                  |
 |<-- 「布局优化完成」|                   |                  |
```

### 5.3 序列三：「运行RTL到GDSII全流程」

**用户输入**：「帮我运行 uart_tx 模块的完整RTL到GDSII流程，目标sky130工艺，100MHz」

**分阶段交互序列**：

```
阶段1：RTL验证（5工具调用，~15min）
  1. validate_hdl_syntax()    -> 语法OK
  2. run_lint()               -> 2条警告，Claude自动修复RTL
  3. run_functional_sim()     -> 所有测试通过
  4. get_coverage_report()    -> 行覆盖率92%（可接受）
  5. save_checkpoint("rtl_ok")

阶段2：逻辑综合（6工具调用，~20min）
  6. generate_sdc(100MHz)     -> 生成时序约束
  7. synthesize_rtl(sky130)   -> WNS=-0.5ns（未收敛）
  [Claude分析：关键路径在uart_shift_reg，决定插入流水线]
  8. modify_rtl_pipeline()    -> 插入寄存器打断关键路径
  9. synthesize_rtl(sky130)   -> WNS=+0.2ns（收敛）
  10. save_checkpoint("synth_ok")

阶段3：布局布线（5工具调用，~45min）
  11. create_floorplan(util=60%)
  12. run_place_and_route()   -> [异步提交，约30分钟]
  13. get_pnr_status()        -> 轮询3次后完成
  14. run_sta_post_pnr()      -> WNS=+0.05ns（收敛）
  15. save_checkpoint("pnr_ok")

阶段4：签核检查（6工具调用，~15min）
  16. run_drc(sky130_rules)   -> 3个金属间距违规
  17. fix_spacing_violations() -> 自动修复
  18. run_drc()               -> 0违规
  19. run_lvs()               -> LVS通过
  20. export_gds()            -> GDS导出成功

阶段5：流片确认（人工介入，必须）
  21. [requires_human_approval: true]
      -> "GDS已就绪，确认提交流片？费用约$XX，不可逆。"
```

**统计**：
- 工具调用次数：~21次（含1次自动迭代综合）
- 总上下文消耗：~80-120k tokens
- 建议分4个Session执行（每Session 20-30k tokens）
- 用户干预次数：1次（流片确认）
- 预计耗时：90-120分钟
- Claude自主度：**95%**

```
多Session策略（避免上下文溢出）：

Session A  RTL验证    ~20k tokens
    |
Session B  逻辑综合   ~30k tokens  (--resume Session_A_id)
    |
Session C  布局布线   ~40k tokens  (--resume Session_B_id)
    |
Session D  签核+GDS   ~25k tokens  (--resume Session_C_id)
```

---

## 6. MCP Resources和Prompts的战略使用

### 6.1 EDA设计数据作为Resource暴露

MCP Resources是只读数据源，Claude按需读取，不自动占用上下文：

```python
@mcp.resource("eda://project/{project_id}/files")
async def list_project_files(project_id: str) -> dict:
    return {
        "rtl": list_files(f"{project_id}/rtl/*.v"),
        "constraints": list_files(f"{project_id}/constraints/*.sdc"),
        "reports": list_files(f"{project_id}/reports/*.rpt"),
    }

@mcp.resource("eda://reports/{report_id}")
async def get_report(report_id: str) -> str:
    """完整报告文本，仅Claude主动请求时加载"""
    return read_report_file(report_id)

@mcp.resource("eda://design/{design_id}/hierarchy")
async def get_hierarchy(design_id: str) -> dict:
    return {
        "top_module": "uart_tx",
        "submodules": ["baud_gen", "shift_reg", "state_machine"],
        "port_count": 8,
        "line_count": 245
    }
```

**Resource vs 工具内联数据选择原则**：

| 数据类型 | 大小估计 | 推荐策略 |
|---------|---------|--------|
| 综合摘要（WNS/面积/功耗） | <500 tokens | 工具返回内联 |
| 完整timing report | 5-20k tokens | Resource URI引用 |
| Verilog源文件（<200行） | <3k tokens | 工具返回内联 |
| 大型Verilog文件 | >5k tokens | Resource URI引用 |
| GDS/OASIS版图 | MB-GB | Resource URI + 摘要工具 |
| 仿真波形数据库 | MB级 | Resource URI + 信号查询工具 |

### 6.2 EDA工作流模板作为Prompt

MCP Prompts提供标准化的EDA工作流入口，降低用户使用门槛：

```python
@mcp.prompt()
def rtl_to_netlist(top_module: str, target_library: str, clock_mhz: float) -> str:
    return (
        f"请完成 {top_module} 的RTL综合流程，目标库 {target_library}，"
        f"时钟 {clock_mhz}MHz。\n"
        f"顺序：语法检查 -> Lint -> 功能仿真 -> 综合 -> 时序验证 -> 保存检查点。"
    )

@mcp.prompt()
def debug_simulation(failing_testbench: str, failure_message: str) -> str:
    return (
        f"仿真 {failing_testbench} 失败：{failure_message}\n"
        f"请：1)获取失败波形 2)识别第一个失败断言 "
        f"3)追踪信号路径 4)定位RTL问题 5)提出修复方案（需确认后再改）"
    )

@mcp.prompt()
def timing_closure(design: str, current_wns: float, target_freq_mhz: float) -> str:
    return (
        f"{design} WNS={current_wns}ns，目标{target_freq_mhz}MHz。\n"
        f"按优先级尝试：约束调整 -> 综合策略切换 -> RTL流水线插入。"
    )
```

用户在Claude Code输入 `/rtl_to_netlist top=uart_tx lib=sky130 clock_mhz=100`，
Claude即获得完整执行指引，无需每次重复描述流程细节。

### 6.3 动态资源订阅：实时仿真进度推送

MCP 2025-11-25协议支持资源变更通知，实现仿真进度实时推送：

```python
@mcp.resource("eda://sim/{job_id}/progress", subscribe=True)
async def get_sim_progress(job_id: str) -> dict:
    """Claude订阅后，进度更新自动推送，无需主动轮询"""
    s = sim_engine.get_status(job_id)
    return {
        "phase": s.phase,          # compile/elaborate/simulate/done
        "completion_pct": s.pct,
        "elapsed_minutes": s.elapsed,
        "current_time_ns": s.sim_time,
        "errors_found": s.error_count,
    }

# 仿真引擎每完成1%进度时调用
async def on_sim_progress_update(job_id: str):
    await mcp.notify_resource_changed(f"eda://sim/{job_id}/progress")
```

**效果**：Claude订阅后无需主动轮询，仿真引擎推送进度更新，Claude实时向用户报告，
并在检测到仿真停滞（进度超时不更新）时自动干预诊断。

---

## 7. 实现建议与优先级路线图

### 7.1 核心实现建议汇总

| 编号 | 建议 | 优先级 | 影响域 |
|-----|------|--------|-------|
| R1 | 所有工具返回`suggested_next_steps`字段 | P0 | Claude自主度 |
| R2 | 大型EDA报告只返回URI，不内联 | P0 | 上下文管理 |
| R3 | 错误消息含`suggested_fixes`（按成功概率排序） | P0 | 自主修复 |
| R4 | 危险操作返回`requires_human_approval: true` | P0 | 安全性 |
| R5 | 长时任务使用job_id+poll模式 | P1 | 用户体验 |
| R6 | 每个Server不超过12个工具 | P1 | LLM选择准确率 |
| R7 | 实现`design_state`快照支持断点恢复 | P1 | 鲁棒性 |
| R8 | PCB/版图工具必须实现screenshot工具 | P1 | 差异化核心 |
| R9 | 使用MCP Sampling实现异常自动诊断 | P2 | 自主度提升 |
| R10 | 实现Resource订阅推送仿真进度 | P2 | 体验提升 |

### 7.2 EDA任务Claude自主度预测（完整实施后）

```
任务类型                              预计自主度   典型工具调用次数
------------------------------------+-----------+---------------
RTL语法检查 + Lint修复               |    95%    |    3-5次
功能仿真 + 失败调试                   |    85%    |    5-15次
逻辑综合 + 时序收敛                   |    90%    |    5-10次
RTL到GDSII全流程                     |    85%    |   20-25次
PCB布局EMI优化（含可视化）             |    80%    |   10-15次
DRC违规批量分析修复                   |    75%    |    5-10次
模拟电路SPICE仿真调试                 |    70%    |    5-10次
形式验证（等价性检查）                 |    90%    |    3-6次
全新模块架构设计                      |    30%    |   N/A（需人主导）
```

### 7.3 按路线图阶段的MCP工具开发优先级

```
Phase 0 MVP（Month 1-2）：建立Claude自主度基础
  必须实现：
  - 工具返回格式规范（R1/R2/R3/R4全部实施）
  - Digital IC Server：synthesize_rtl, run_simulation,
    parse_reports, validate_hdl_syntax, save_checkpoint
  - System Prompt v1：数字IC领域知识 + 安全约束
  - 5个MCP Prompt模板（rtl_to_netlist, debug_sim等）
  预期效果：4位计数器到GDSII全自主完成率 >85%

Phase 1 核心（Month 3-4）：扩展覆盖域
  新增：
  - PCB Server：read_pcb, screenshot_layout, move_components,
    run_drc, update_copper_fill
  - Sim Server：run_cocotb, get_coverage, run_spice
  - 长时任务异步模式（R5实施）
  预期效果：PCB布局优化自主完成率 >75%

Phase 2 全流程（Month 5-8）：完善EDA流水线
  新增：
  - Layout Server（KLayout）：run_drc, run_lvs, view_gds
  - Orchestrator：跨Server工作流编排
  - Resource订阅推送（R10实施）
  - MCP Sampling异常诊断（R9实施）
  预期效果：RTL到GDSII全流程自主完成率 >80%

Phase 3 智能化（Month 9-12）：最大化自主度
  新增：
  - design_state快照系统（R7实施）
  - 多Session断点恢复
  - 可视化反馈闭环完整实现（R8全部工具）
  - ChipBench基准测试集成
  预期效果：Claude自主度从当前~31%提升到 >70%（ChipBench）
```

### 7.4 关键风险与缓解

| 风险 | 描述 | 缓解措施 |
|-----|------|--------|
| 上下文溢出 | 长流程超过200k token限制 | 多Session策略 + Resource URI引用 |
| LLM幻觉（A4 T7风险） | Claude生成错误Verilog/约束 | 每步工具验证 + 沙箱执行 |
| 工具选择错误 | 12+工具时Claude选错工具 | 每Server限12工具 + 清晰描述 |
| 无限迭代循环 | Claude在修复失败时陷入循环 | 工具返回`max_retries`字段，超限升级到L4 |
| 截图质量差 | PCB截图无法被Claude分析 | 指定分辨率+缩放，关键区域高亮 |

---

## 总结：AUTO_EDA的Claude自主度实现路径

本文档的核心结论：

1. **工具返回格式是关键杠杆**：`suggested_next_steps` + `design_state` + `suggested_fixes`
   三个字段是提升Claude自主度的最高ROI设计决策。

2. **L1-L3覆盖70-80%的EDA工作量**：Claude可完全自主处理语法验证、功能仿真、
   逻辑综合、时序收敛、DRC修复等核心流程。L4只需在流片等不可逆操作时介入。

3. **可视化反馈闭环是核心差异化**：截图工具让Claude能分析PCB/版图布局，
   这是MCP4EDA等竞品完全缺失的能力，也是AUTO_EDA最重要的护城河之一。

4. **上下文管理需从设计阶段解决**：Resource URI引用 + 多Session策略是必须内置
   的架构设计，不能留到出现问题时再补救。

5. **MCP三原语各司其职**：
   - Tools：驱动EDA工具执行（主战场）
   - Resources：管理大型EDA文件（上下文节省）
   - Prompts：标准化工作流入口（用户体验）
   - Sampling：主动诊断异常（自主度提升）

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 1.0.0 | 初版，基于R8/A7/CLAUDE.md深度分析，含完整交互序列图和实现建议 |