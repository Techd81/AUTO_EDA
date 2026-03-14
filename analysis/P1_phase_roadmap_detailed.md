# P1: AUTO_EDA Phase 1-3 长期路线图细化

> 文档编号: P1
> 日期: 2026-03-14
> 作者: 产品规划团队
> 依赖文档: A8_integration_roadmap.md, A9_workflow_engine_design.md, DA2_visual_feedback_technical.md, DA5_claude_mcp_integration.md, DA6_competitive_deep_analysis.md
> 状态: 完成

---

## 目录

1. [Phase 1 细化（Month 3-4）](#1-phase-1-细化month-3-4)
2. [Phase 2 细化（Month 5-8）](#2-phase-2-细化month-5-8)
3. [Phase 3 细化（Month 9-12）](#3-phase-3-细化month-9-12)
4. [技术债务管理计划](#4-技术债务管理计划)
5. [与竞争对手的时间赛跑](#5-与竞争对手的时间赛跑)
6. [12个月关键里程碑时间线](#6-12个月关键里程碑时间线)

---

## 1. Phase 1 细化（Month 3-4）

### 1.1 Verilator MCP Server 详细规格

**定位**: 编译型仿真引擎，为 Phase 1 提供高性能 HDL 仿真能力（补充 Icarus Verilog 的事件驱动仿真）。

**集成方式**: CLI subprocess wrapper + VCD/FST 波形解析库（`pyDigitalWaveTools`）

**工具清单（9个）**:

| Tool 名称 | 功能 | 关键参数 | 返回类型 |
|-----------|------|----------|----------|
| `verilator_lint` | 静态语法/语义检查 | `verilog_files`, `top_module` | 结构化警告/错误列表 |
| `verilator_compile` | 编译 HDL 到 C++ 仿真模型 | `verilog_files`, `top_module`, `trace`, `coverage` | 编译状态、可执行路径 |
| `verilator_simulate` | 运行编译后的仿真模型 | `sim_binary`, `timeout_s`, `vcd_output` | 仿真日志摘要、VCD 路径 |
| `parse_vcd` | 解析 VCD 波形文件 | `vcd_file`, `signals`, `time_range` | 信号时序数据（JSON） |
| `parse_fst` | 解析 FST 波形文件（更高效） | `fst_file`, `signals` | 信号时序数据（JSON） |
| `coverage_report` | 生成代码覆盖率报告 | `coverage_db_path` | 行/分支/翻转覆盖率 |
| `waveform_to_image` | 波形可视化导出为 PNG | `vcd_file`, `signals`, `width_px` | base64 PNG（供 Claude 视觉分析） |
| `extract_signal_transitions` | 提取指定信号的所有跳变 | `vcd_file`, `signal_name` | 跳变时间序列 |
| `compare_simulations` | 对比两次仿真的波形差异 | `vcd_a`, `vcd_b`, `signals` | 差异报告 |

**cocotb MCP Server 详细规格**:

**定位**: Python 原生验证框架，与 LLM 代码生成天然契合，是 AUTO_EDA 验证层的核心差异化工具。

**集成方式**: 纯 Python API（cocotb 核心框架，API 成熟度 ★★★★★）+ pytest 集成

**工具清单（8个）**:

| Tool 名称 | 功能 | 关键参数 | 返回类型 |
|-----------|------|----------|----------|
| `cocotb_create_testbench` | 生成 Python 测试台模板 | `dut_name`, `ports`, `test_scenarios` | Python 测试文件内容 |
| `cocotb_run_test` | 执行单个 cocotb 测试 | `testbench_path`, `dut_verilog`, `simulator` | 测试结果、波形路径 |
| `cocotb_run_regression` | 批量执行测试套件 | `test_dir`, `parallel`, `timeout_s` | 通过/失败统计、失败详情 |
| `cocotb_analyze_failure` | 分析测试失败根因 | `test_log`, `waveform_path` | 失败原因分析（结构化） |
| `cocotb_generate_coverage` | 生成功能覆盖率报告 | `regression_results` | 覆盖率矩阵 |
| `cocotb_list_tests` | 列出目录下所有测试 | `test_dir` | 测试名称、描述列表 |
| `cocotb_scaffold_project` | 创建完整验证工程结构 | `project_name`, `dut_list` | 目录结构 + Makefile |
| `cocotb_port_to_uvm` | 将 cocotb 测试转换为 UVM 模板 | `testbench_path` | UVM SystemVerilog 代码 |

### 1.2 KLayout MCP Server 详细规格

**定位**: 版图查看、DRC/LVS 检查、版图截图（可视化反馈 V1 核心工具），Phase 1 最复杂的 MCP Server。

**集成方式**: `klayout.db` Python API（`pya` 模块，API 成熟度 ★★★★★）

**工具清单（12个）**:

| Tool 名称 | 功能 | 关键参数 | 返回类型 |
|-----------|------|----------|----------|
| `klayout_open_gds` | 打开 GDSII/OASIS 文件 | `gds_path`, `pdk_path` | 顶层单元列表、层次统计 |
| `klayout_run_drc` | 执行 DRC 规则检查 | `gds_path`, `drc_script`, `cell_name` | 违规列表（坐标+规则名） |
| `klayout_run_lvs` | 执行 LVS 版图网表对比 | `gds_path`, `netlist_path`, `pdk_path` | LVS 通过/失败、差异列表 |
| `klayout_export_image` | 导出版图截图（可视化反馈核心） | `gds_path`, `cell_name`, `layers`, `width_px` | base64 PNG |
| `klayout_export_layer_image` | 按图层导出截图 | `gds_path`, `layer_spec`, `resolution` | base64 PNG per layer |
| `klayout_cell_info` | 获取单元详细信息 | `gds_path`, `cell_name` | 边界框、实例数、层列表 |
| `klayout_layer_summary` | 汇总所有图层使用情况 | `gds_path` | 图层号、名称、形状数量 |
| `klayout_measure_area` | 测量指定图层面积 | `gds_path`, `cell_name`, `layer_spec` | 面积（µm²） |
| `klayout_diff_layouts` | 对比两个版图差异 | `gds_a`, `gds_b`, `cell_name` | 差异区域列表 |
| `klayout_edit_cell` | 简单版图编辑（添加/删除形状） | `gds_path`, `cell_name`, `operation` | 修改后版图路径 |
| `klayout_run_script` | 执行任意 KLayout Python 脚本 | `script_code`, `gds_path` | 脚本输出 + 返回值 |
| `klayout_markers_to_json` | 将 DRC marker 数据库导出为 JSON | `marker_db_path` | 结构化违规数据 |

**可视化反馈集成要点**:
- `klayout_export_image` 返回 base64 PNG，直接嵌入 MCP tool_result 的 `image` 类型字段
- Claude 接收图像后可自主分析布线拥塞、DRC 标记位置、版图对称性
- MCP Sampling 触发：DRC 违规数 > 阈值时，主动请求 Claude 分析违规分布并建议修复策略

### 1.3 综合→仿真闭环具体实现方案

```
综合→仿真闭环数据流（Phase 1 核心交付）:

用户: "给我验证这个计数器的 Verilog"
          │
          ▼
[Yosys MCP] yosys_lint_check()     → 语法错误? 自动修复
          │
          ▼
[Yosys MCP] yosys_synthesize()     → 输出: gate-level netlist (JSON)
          │
          ▼
[cocotb MCP] cocotb_create_testbench() → 输出: counter_tb.py
          │
          ▼
[Verilator MCP] verilator_compile()    → 输出: sim binary
          │
          ▼
[Verilator MCP] verilator_simulate()   → 输出: sim.vcd + 日志
          │
          ▼
[Verilator MCP] waveform_to_image()    → 输出: waveform.png (base64)
          │
          ▼
Claude 视觉分析波形图: "计数器在第 15 个时钟周期后停止，怀疑是溢出问题"
          │
          ▼
[cocotb MCP] cocotb_run_regression()  → 运行覆盖率测试
          │
          ▼
 Claude 生成报告: 功能验证通过，覆盖率 78%，建议增补边界测试用例
```

**闭环关键接口契约**:

| 上游工具 | 输出格式 | 下游工具 | 接收格式 |
|----------|----------|----------|----------|
| Yosys `synthesize` | `netlist.json` | Verilator `compile` | Verilog门级网表 |
| Yosys `synthesize` | `netlist.v` | cocotb `create_testbench` | DUT端口描述 |
| Verilator `simulate` | `sim.vcd` | `waveform_to_image` | VCD文件路径 |
| `waveform_to_image` | base64 PNG | Claude视觉分析 | MCP image内容块 |
| cocotb `run_regression` | JSON结果 | Claude分析 | 结构化测试报告 |

### 1.4 可视化反馈 V1（先接入哪些工具）

**V1 范围（Phase 1，Month 3-4）**: 以最小实现取得最大差异化效果。

| 工具 | 视觉内容 | 优先级 | 实现方式 | Claude分析价值 |
|------|----------|--------|----------|----------------|
| **Verilator波形** | 信号时序图 | P0 | VCD → matplotlib PNG | 功能验证、竞争冒险检测 |
| **KLayout版图截图** | GDSII版图图像 | P0 | `pya.LayoutView.save_image()` | DRC违规位置、布线拥塞 |
| **Yosys RTL图** | 电路原理图 | P1 | `yosys show -format svg` → PNG | 电路结构理解 |
| **cocotb覆盖率热图** | 覆盖率矩阵 | P1 | Python matplotlib | 测试盲区识别 |

**V1 不纳入范围（推迟到V2）**: KiCad PCB截图（IPC API复杂度高，Phase 2处理）、ngspice波形（Phase 2工具）。

**V1 技术实现约束**:
- 图像分辨率上限: 1920×1080（超大版图自动裁剪至关键区域）
- base64编码后大小上限: 5MB（约3.75MB原始PNG，超出则降采样）
- MCP tool_result格式: `{"type": "image", "data": "<base64>", "mimeType": "image/png"}`
- Claude视觉分析触发条件: DRC违规 > 0 或 仿真失败 时自动附加截图

### 1.5 Phase 1 发布目标和 KPI

**发布目标**: "数字设计前端完整闭环" — 用户可通过自然语言完成从RTL到门级验证的全流程。

**里程碑节点**:

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| M1.1: Verilator+cocotb可用 | Month 3, Week 2 | 可仿真标准基准设计（计数器/FIFO/ALU） |
| M1.2: KLayout MCP可用 | Month 3, Week 4 | 可打开SkyWater PDK版图并运行DRC |
| M1.3: 可视化反馈V1上线 | Month 4, Week 2 | 波形图和版图截图可传递给Claude分析 |
| M1.4: 综合→仿真闭环验证 | Month 4, Week 3 | 端到端自然语言驱动无需人工干预 |
| M1.5: Phase 1正式发布 | Month 4, Week 4 | 全部KPI达标，文档齐全 |

**Phase 1 KPI**:

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| Verilator仿真成功率 | ≥85% | 10个基准设计测试套件 |
| cocotb测试台自动生成准确率 | ≥80% | Claude生成+人工评审 |
| KLayout DRC运行成功率 | ≥90% | SkyWater 130nm PDK测试 |
| 可视化反馈图像质量 | ≥4/5分 | 5名EDA工程师盲评 |
| 综合→仿真闭环端到端成功率 | ≥75% | 5个典型设计场景 |
| 新增MCP Tools数量 | ≥32个 | 代码合并计数 |
| 单元测试覆盖率 | ≥80% | pytest-cov |
| 累计GitHub Stars增量 | +200 | GitHub API |

---

## 2. Phase 2 细化（Month 5-8）

### 2.1 OpenROAD MCP Server 优先级（最复杂，最高价值）

**战略定位**: Phase 2 的技术核心，是实现 RTL→GDSII 完整闭环的决定性工具。复杂度最高（PDK管理、多步骤物理设计、数小时运行时间），价值也最高（开源数字IC设计不可替代）。

**四周分步实施计划**:

```
Week 1-2（Month 5）: 基础框架 + Floorplan
  ├── OpenROAD Python绑定环境搭建和版本锁定
  ├── PDK配置管理模块（SkyWater 130nm, GF180MCU）
  ├── openroad_init_design()    — 读取网表+SDC+LEF
  ├── openroad_floorplan()      — 芯片面积规划
  └── openroad_io_placement()   — IO引脚放置

Week 3-4（Month 5-6）: 放置阶段
  ├── openroad_place_design()   — 全局+详细放置
  ├── openroad_cts()            — 时钟树综合
  ├── openroad_report_timing()  — 时序报告（与OpenSTA协同）
  └── 检查点机制: 每步骤保存ODB数据库

Week 5-6（Month 6）: 布线阶段
  ├── openroad_global_route()   — 全局布线
  ├── openroad_detailed_route() — 详细布线
  ├── openroad_run_drc()        — 布线后DRC
  └── openroad_export_gds()     — 输出GDSII

Week 7-8（Month 6-7）: 分析与优化
  ├── openroad_report_power()   — 功耗分析
  ├── openroad_report_area()    — 面积统计
  ├── openroad_optimize_placement() — 时序驱动优化
  └── 与KLayout MCP集成: 导出版图截图供Claude分析
```

**OpenROAD MCP Server 完整工具清单（14个）**:

| Tool 名称 | 物理设计阶段 | 关键输入 | 关键输出 |
|-----------|------------|----------|----------|
| `openroad_init_design` | 初始化 | netlist.v, pdk_path, sdc | ODB数据库 |
| `openroad_floorplan` | 布图规划 | die_area, core_area, utilization | 布图规划ODB |
| `openroad_io_placement` | IO放置 | io_constraints | 带IO的ODB |
| `openroad_place_design` | 单元放置 | ODB, placement_density | 放置后ODB |
| `openroad_cts` | 时钟树综合 | ODB, clock_nets | CTS后ODB |
| `openroad_global_route` | 全局布线 | ODB, routing_layers | 全局布线ODB |
| `openroad_detailed_route` | 详细布线 | ODB | 详细布线ODB |
| `openroad_report_timing` | 时序分析 | ODB | WNS/TNS/时序报告 |
| `openroad_report_power` | 功耗分析 | ODB, activity_file | 静态/动态功耗 |
| `openroad_report_area` | 面积统计 | ODB | 单元面积、线网长度 |
| `openroad_run_drc` | DRC检查 | ODB/GDS | 违规列表 |
| `openroad_export_gds` | 导出 | ODB, pdk_path | GDSII文件 |
| `openroad_run_script` | 通用TCL | tcl_script, odb_path | 脚本输出 |
| `openroad_compare_runs` | 运行对比 | run_a_dir, run_b_dir | PPA对比表 |

**复杂度管理策略**:
- PDK路径通过环境变量统一管理，不硬编码
- 每个物理设计步骤保存ODB检查点，支持断点续跑（A9工作流引擎检查点机制）
- 超时处理: 全局布线/详细布线默认超时4小时，可配置
- 异步执行: 长时任务通过后台进程运行，MCP轮询状态

### 2.2 工作流引擎 V1 实现计划

**目标**: 基于 A9 设计方案，在 Phase 2 实现可用的 DAG 驱动工作流引擎，支撑 RTL→GDSII 全流程编排。

**V1 范围界定**（不做过度设计）:
- DAG 引擎: YAML定义工作流，Python执行调度
- 状态机: PENDING → RUNNING → COMPLETED/FAILED/SKIPPED
- 检查点: 每个节点完成后持久化到 `.workflow/checkpoints/`
- MCP接口: `workflow_run`, `workflow_status`, `workflow_resume` 三个核心工具
- 不含: 分布式执行、云调度、UI界面（Phase 3考虑）

**Month 5 实现计划**:

```
Week 1: DAG核心数据结构
  ├── WorkflowNode: id, tool, params, depends_on, status
  ├── WorkflowDAG: nodes, edges, topological_sort()
  └── YAML解析器: workflow.yaml → WorkflowDAG

Week 2: 执行引擎
  ├── DAGExecutor: 按拓扑序调度节点
  ├── 并行执行: 无依赖节点并发运行（asyncio）
  └── 错误处理: 节点失败 → 标记下游SKIPPED或触发重试

Week 3: 检查点 + MCP接口
  ├── CheckpointManager: 序列化/反序列化工作流状态
  ├── workflow_run MCP Tool
  ├── workflow_status MCP Tool
  └── workflow_resume MCP Tool

Week 4: 预置工作流模板
  ├── rtl_to_netlist.yaml  (Yosys综合流程)
  ├── simulation_flow.yaml (Verilator+cocotb)
  └── rtl_to_gdsii.yaml   (完整后端流程，Month 7交付)
```

**预置工作流模板（rtl_to_gdsii.yaml 骨架）**:

```yaml
name: RTL_to_GDSII
version: "1.0"
description: 完整数字IC实现流程

nodes:
  - id: lint
    tool: yosys_mcp.lint_check
    params: {verilog_files: "${INPUT_RTL}"}

  - id: synthesize
    tool: yosys_mcp.synthesize
    depends_on: [lint]
    params: {top_module: "${TOP_MODULE}", liberty: "${PDK_LIB}"}
    checkpoint: true

  - id: sta_pre_layout
    tool: opensta_mcp.report_checks
    depends_on: [synthesize]
    params: {netlist: "${synthesize.output.netlist}"}

  - id: floorplan
    tool: openroad_mcp.floorplan
    depends_on: [synthesize]
    params: {utilization: 0.5}
    checkpoint: true

  - id: place
    tool: openroad_mcp.place_design
    depends_on: [floorplan]
    checkpoint: true

  - id: cts
    tool: openroad_mcp.cts
    depends_on: [place]
    checkpoint: true

  - id: route
    tool: openroad_mcp.detailed_route
    depends_on: [cts]
    checkpoint: true
    timeout_hours: 4

  - id: export_gds
    tool: openroad_mcp.export_gds
    depends_on: [route]

  - id: drc_check
    tool: klayout_mcp.run_drc
    depends_on: [export_gds]

  - id: layout_screenshot
    tool: klayout_mcp.export_image
    depends_on: [export_gds]
```

### 2.3 ngspice 集成方案

**战略价值**: 当前市场零 MCP 覆盖（DA6验证），填补 SPICE 仿真空白是 Phase 2 最重要的差异化功能。

**集成路径选择**:

| 路径 | 方式 | 优势 | 劣势 | 选择 |
|------|------|------|------|------|
| CLI subprocess | 调用 `ngspice -b circuit.sp` | 零依赖，ngspice原装 | 输出解析复杂，无交互 | **主路径** |
| PySpice | Python封装库 | API友好 | 维护不活跃，部分功能缺失 | 辅助/抽象层 |
| ngspice共享库 | `libngspice.so` Python绑定 | 最强集成 | 编译复杂，平台差异大 | Phase 3考虑 |

**ngspice MCP Server 工具清单（9个）**:

| Tool 名称 | 功能 | 关键参数 | 返回类型 |
|-----------|------|----------|----------|
| `ngspice_load_circuit` | 加载SPICE网表 | `spice_file` | 电路节点/元件统计 |
| `ngspice_run_dc` | 直流工作点/扫描分析 | `source`, `start`, `stop`, `step` | 节点电压/支路电流 |
| `ngspice_run_ac` | 交流频率响应分析 | `fstart`, `fstop`, `points` | 幅频/相频数据 |
| `ngspice_run_tran` | 瞬态时域仿真 | `tstop`, `tstep`, `tstart` | 时域波形数据 |
| `ngspice_run_op` | 静态工作点分析 | — | 所有节点电压 |
| `ngspice_measure` | 从仿真结果测量参数 | `measure_expr` | 测量值（上升时间/带宽等） |
| `ngspice_plot_to_image` | 将仿真结果绘图导出PNG | `signals`, `analysis_type` | base64 PNG |
| `ngspice_export_csv` | 导出仿真数据为CSV | `signals` | CSV文件路径 |
| `ngspice_run_montecarlo` | Monte Carlo参数扫描 | `param`, `distribution`, `runs` | 统计分布数据 |

**与数字设计流程的集成点**:
- KLayout 导出的器件版图参数 → ngspice 后仿真（寄生参数提取后）
- Phase 3: 与 OpenROAD 寄生参数提取（SPEF）集成，支持后仿真时序验证

### 2.4 RTL→GDSII 闭环里程碑

**Month 5**: 工作流引擎V1 + OpenROAD基础（floorplan/place）
**Month 6**: OpenROAD完整布线 + OpenSTA深度集成 → 第一次完整RTL→GDSII跑通（SkyWater 130nm，计数器设计）
**Month 7**: ngspice集成 + 流程稳定性优化 + 多PDK支持（GF180MCU）
**Month 8**: KPI验证 + 性能优化 + Phase 2发布

**RTL→GDSII 闭环验收基准设计**:

| 基准设计 | 规模 | 验收标准 | 目标月份 |
|----------|------|----------|----------|
| 8位计数器 | <100个门 | 全流程跑通，DRC/LVS通过 | Month 6 |
| 32位加法器 | ~500个门 | PPA报告生成，时序收敛 | Month 6 |
| FIFO（16深度） | ~2000个门 | 综合→P&R→DRC全自动 | Month 7 |
| RISC-V子模块 | ~5000个门 | 工作流引擎编排，断点续跑 | Month 8 |

### 2.5 Phase 2 发布目标

**发布目标**: "RTL→GDSII 全流程自动化" — 用户从自然语言规格出发，通过工作流引擎自动完成完整物理设计，无需手动执行任何EDA命令。

**Phase 2 KPI**:

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| RTL→GDSII全流程成功率 | ≥80% | 4个基准设计 × 2个PDK |
| 时序收敛率（WNS≥0） | ≥70% | 标准约束下自动综合 |
| ngspice仿真准确率 | ≥90% | 对比参考SPICE结果 |
| 工作流引擎断点续跑成功率 | ≥95% | 人为中断后恢复测试 |
| OpenROAD单步执行成功率 | ≥85% | 标准PDK+基准设计 |
| 累计MCP Tools数量 | ≥100个 | 代码合并计数 |
| GitHub Stars累计 | ≥1000 | GitHub API |
| 活跃用户数 | ≥500 | 安装遥测/Discord活跃 |
| 企业/学术用户案例 | ≥5个 | 用户报告 |

---

## 3. Phase 3 细化（Month 9-12）

### 3.1 多Agent编排框架设计

**定位**: 从「单Claude实例调用MCP工具」升级为「多Claude实例协作完成复杂EDA任务」。参照 NL2GDS 多Agent分工架构（DA6）和 AgentEngineer L4 级别（DA6），实现 AUTO_EDA 的 L4 自主能力。

**Agent角色定义**:

```
OrchestratorAgent（编排者）
  │ 接收用户高层规格，分解为子任务，调度专家Agent
  │ 监控整体进度，处理Agent间冲突
  │
  ├─► DesignAgent（设计者）
  │     职责: RTL代码生成、模块划分、参数化设计
  │     工具: Yosys MCP (lint/elaborate), Verilog Parser MCP
  │     触发: 收到RTL规格后启动
  │
  ├─► VerificationAgent（验证者）
  │     职责: 测试台生成、仿真执行、覆盖率分析、Bug定位
  │     工具: cocotb MCP, Verilator MCP
  │     触发: DesignAgent输出RTL后启动
  │
  ├─► ImplementationAgent（实现者）
  │     职责: 综合参数优化、物理设计迭代、PPA调优
  │     工具: Yosys MCP, OpenROAD MCP, OpenSTA MCP
  │     触发: VerificationAgent验证通过后启动
  │
  └─► DebugAgent（调试者）
        职责: 错误根因分析、修复建议、回归验证
        工具: 所有MCP Server + 可视化反馈
        触发: 任意Agent遇到错误时召唤
```

**技术实现方式**（利用 Claude Code 原生能力）:

| 机制 | 用途 | 实现方式 |
|------|------|----------|
| MCP Sampling Primitive | MCP Server主动请求Claude推理 | `mcp.sample()` 调用专家Agent |
| Claude Task工具 | 启动子Agent实例 | `Task({subagent_type, prompt})` |
| 共享MCP Resources | Agent间数据传递 | `eda://session/{id}/artifacts/` URI |
| 工作流引擎状态机 | Agent协调和进度跟踪 | A9 DAG Engine + Agent状态节点 |

**Agent通信协议**:
```
Agent消息格式:
{
  "from": "VerificationAgent",
  "to": "DesignAgent",
  "type": "error_report",
  "payload": {
    "test_name": "counter_overflow_test",
    "failure_signal": "out[7:0]",
    "expected": "0x00",
    "actual": "0xFF",
    "waveform_uri": "eda://session/42/waveforms/sim_001.vcd"
  }
}
```

**Phase 3 实施计划**:
- Month 9: OrchestratorAgent框架 + DesignAgent
- Month 10: VerificationAgent + DebugAgent
- Month 11: ImplementationAgent + 完整多Agent流程集成测试
- Month 12: 性能优化 + 用户案例验证 + 正式发布

### 3.2 可视化反馈 V2（完整闭环）

**V2 在 V1 基础上新增的能力**:

| 新增能力 | 工具 | 技术实现 | 商业价值 |
|----------|------|----------|----------|
| KiCad PCB截图 | KiCad IPC API | `board.plot()` → PNG | PCB用户视觉验证 |
| ngspice波形图 | matplotlib | 仿真数据 → 专业波形图 | 模拟设计验证 |
| 版图热力图 | KLayout pya | 拥塞/时序违规热力图 | P&R优化指导 |
| 多帧对比分析 | Claude多图分析 | 优化前后版图并排 | 设计迭代效果展示 |
| 自动标注 | Claude视觉+文本 | 在图像上标注违规位置 | 调试效率提升 |

**完整可视化反馈闭环（V2）**:

```
[用户] "优化这个设计的布线拥塞"
    │
    ▼
[KLayout MCP] export_image() → 当前版图截图
    │
    ▼
[Claude视觉分析] 识别拥塞区域坐标 → 建议增大该区域间距
    │
    ▼
[OpenROAD MCP] 调整布线约束 → 重新详细布线
    │
    ▼
[KLayout MCP] export_image() → 优化后版图截图
    │
    ▼
[Claude视觉对比] 并排分析前后两张截图 → 确认拥塞改善
    │
    ▼
[用户] 收到: 优化前后对比图 + 定量改善报告
```

**V2 图像质量标准**:
- 分辨率: 最高 4K (3840×2160)，按设计复杂度自适应
- 关键区域自动放大: DRC违规位置自动裁剪 2×放大图
- 热力图叠加: 在版图截图上叠加拥塞/时序违规热力层
- 多图布局: 最多4张图拼接为一张传递给Claude（节省token）

### 3.3 领域知识飞轮启动

**核心机制**: 每次用户交互都增强 AUTO_EDA 的领域知识，形成竞争对手难以复制的数据护城河。

**飞轮三环**:

```
用户使用 AUTO_EDA
    │
    ▼ 产生
工作流执行数据 + 错误修复案例 + PPA优化轨迹
    │
    ▼ 积累为
领域知识库（EDA最佳实践、常见错误模式、PDK特性）
    │
    ▼ 提升
Claude的EDA决策质量（更准确的综合参数、更快的时序收敛）
    │
    ▼ 带来
更好的用户体验 → 更多用户使用
    └──────────────────────────────┘ 飞轮闭环
```

**知识库构建计划（Month 9-12）**:

| 知识类型 | 数据来源 | 存储方式 | 使用方式 |
|----------|----------|----------|----------|
| EDA工具最佳实践 | 用户工作流日志（匿名）| 结构化JSON | MCP Resources注入System Prompt |
| 常见错误模式库 | 错误日志+修复案例 | 向量数据库（RAG） | DebugAgent检索 |
| PDK特性知识 | SkyWater/GF180文档解析 | Markdown知识库 | OpenROAD Agent参考 |
| PPA优化案例 | 成功设计的参数轨迹 | 时序数据库 | ImplementationAgent参考 |
| 工作流模板社区 | 用户贡献 + 官方验证 | GitHub仓库 | 工作流引擎直接加载 |

**隐私保护设计**:
- 所有遥测数据完全匿名化，不收集设计内容
- 仅收集：工具调用序列、成功/失败状态、执行时长、参数范围
- 用户可选择完全离线模式（opt-out）

**Month 11-12 实施**:
- 部署向量数据库（Chroma/Qdrant）存储错误修复案例
- 实现 RAG 检索接口，DebugAgent 优先查询历史案例
- 建立社区工作流模板仓库（auto-eda-workflows GitHub组织）
- 发布首个 EDA 最佳实践知识包

### 3.4 商业EDA桥接层（可选）

**战略定位**: 不是核心路径，是高价值加分项。目标用户是同时拥有开源EDA和商业EDA工具的混合环境团队。

**可行性评估（基于DA6分析）**:

| 商业工具 | 桥接方式 | 可行性 | 实现时间 | 价值 |
|----------|----------|--------|----------|------|
| Synopsys DC/PT | TCL脚本生成+注入 | 中（需用户提供License） | 3周 | 高（企业用户） |
| Cadence Genus/Innovus | SKILL/TCL脚本生成 | 中 | 4周 | 高 |
| Siemens Calibre | Calibre svrf脚本生成 | 中高（有Python API） | 2周 | 中（DRC专用） |

**实现原则**:
- AUTO_EDA 仅提供「脚本生成层」和「结果解析层」，不接触商业工具的二进制
- 用户自行提供工具许可证和安装路径
- 通过环境变量注入工具路径，零硬编码
- 法律边界：仅生成标准TCL/Python脚本，不逆向工程商业工具

**Month 11-12 交付**（如资源允许）:
- Synopsys DC TCL脚本生成工具（MCP Tool: `synopsys_gen_synthesis_script`）
- 商业工具结果解析器（timing report、area report格式兼容）
- 开源↔商业工具数据格式转换（LEF/DEF/Liberty互操作）

### 3.5 Phase 3 发布目标

**发布目标**: "AI-Native EDA 平台" — 多Agent自主完成从规格到GDSII的全流程，可视化反馈闭环，领域知识持续增强。

**Phase 3 KPI**:

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 多Agent端到端流程成功率 | ≥65% | NL规格→GDSII全自动，5个基准设计 |
| 可视化反馈闭环轮次 | ≤3轮自动修复DRC违规 | DRC自动修复测试 |
| DebugAgent错误解决率 | ≥70% | 历史错误库回归测试 |
| 知识库错误修复案例数 | ≥1000条 | 数据库记录数 |
| 工作流模板社区贡献 | ≥50个社区模板 | GitHub仓库 |
| GitHub Stars累计 | ≥3000 | GitHub API |
| 活跃用户数 | ≥2000 | 安装遥测 |
| 商业用户/付费支持 | ≥10个 | 合同/支持票据 |
| 引用/论文/博客 | ≥20篇 | Google Scholar + 手动统计 |

---

## 4. 技术债务管理计划

### 4.1 每个Phase结束的债务清理Sprint

每个Phase结束前预留 **2周清理Sprint**，不开发新功能，专注质量提升。

**Phase 0结束（Month 2, Week 7-8）清理内容**:

| 债务类型 | 具体项目 | 优先级 |
|----------|----------|--------|
| 接口不一致 | 统一所有MCP Tool的返回格式（Result类型标准化） | P0 |
| 测试缺口 | 补足覆盖率至80%（初版往往只有60%） | P0 |
| 文档欠缺 | 每个Tool的docstring + 使用示例 | P1 |
| 错误处理 | 替换所有裸except为具体错误类型 | P1 |
| 依赖锁定 | 所有EDA工具版本在pyproject.toml中锁定 | P0 |

**Phase 1结束（Month 4, Week 7-8）清理内容**:

| 债务类型 | 具体项目 | 优先级 |
|----------|----------|--------|
| 跨Server接口 | 验证综合→仿真数据契约，修复格式不兼容 | P0 |
| 性能瓶颈 | 剖析工具调用延迟，优化VCD解析（大文件） | P1 |
| 错误消息质量 | 所有错误消息必须包含修复建议 | P1 |
| 集成测试 | 添加端到端跨Server测试（当前只有单Server测试） | P0 |
| 可视化稳定性 | 修复大版图截图OOM问题 | P0 |

**Phase 2结束（Month 8, Week 7-8）清理内容**:

| 债务类型 | 具体项目 | 优先级 |
|----------|----------|--------|
| 工作流引擎 | 修复发现的DAG调度边界问题 | P0 |
| OpenROAD稳定性 | 修复PDK路径相关的不确定性bug | P0 |
| 上下文管理 | 实现自动上下文压缩（长流程超出200k限制） | P1 |
| API版本兼容 | 测试 OpenROAD/KLayout 新版本兼容性 | P1 |
| 安全审查 | subprocess调用沙箱隔离检查 | P0 |

### 4.2 债务跟踪机制

**工具**: GitHub Issues + 标签系统

```
标签体系:
tech-debt/interface    — API/接口不一致
tech-debt/test         — 测试覆盖不足
tech-debt/perf         — 性能问题
tech-debt/security     — 安全相关
tech-debt/docs         — 文档欠缺
tech-debt/stability    — 稳定性/容错

严重级别:
debt-critical  — 阻塞Phase推进
debt-major     — 清理Sprint必须处理
debt-minor     — 下个Phase自然解决
```

**度量指标**（每双周统计）:
- 债务Issue总数、新增数、关闭数
- 测试覆盖率趋势
- `mypy --strict` 类型错误数趋势
- `ruff` lint警告数趋势

### 4.3 重构决策标准

**触发重构的条件**（满足任意2条）:
1. 同一模块在1个月内出现3次以上的bug修复
2. 添加新功能需要修改超过5个文件
3. 单元测试覆盖率下降超过10%且无法快速补足
4. 新工程师理解某模块需要超过2天
5. 性能基准下降超过20%

**禁止重构的时机**: Phase进行中（除非阻塞性bug）、发布前2周、无充分测试覆盖保护时。

**重构范围原则**: 每次重构只改一件事，保持接口向后兼容，先写测试再重构。

---

## 5. 与竞争对手的时间赛跑

### 5.1 MCP4EDA 可能的追赶路径

**当前差距分析（DA6基准）**:

| 维度 | MCP4EDA现状 | AUTO_EDA目标（Month 12） | 差距 |
|------|------------|--------------------------|------|
| 工具覆盖 | 6个工具（仅数字IC） | 13+个工具（PCB+IC+模拟） | AUTO_EDA领先 |
| 架构 | 单体无状态 | DAG工作流引擎 | AUTO_EDA领先 |
| 可视化反馈 | 无 | 完整V2闭环 | AUTO_EDA独有 |
| 部署体验 | Docker+手动（2-4小时） | pip install（<10分钟） | AUTO_EDA领先 |
| 社区生态 | 个人项目，低活跃 | 工作流模板社区 | AUTO_EDA领先 |

**MCP4EDA最可能的追赶动作**（按概率排序）:
1. 添加KiCad支持（高概率，PCB需求明显）— 预计6-9个月
2. 改善部署体验（中高概率）— 预计3-6个月
3. 添加ngspice（中概率）— 预计6-12个月
4. 实现工作流编排（低概率，架构复杂度高）— 预计12个月+
5. 可视化反馈（低概率，需要多模态深度集成）— 预计12个月+

**结论**: MCP4EDA最快能在6-9个月内追上AUTO_EDA的工具覆盖广度，但工作流引擎和可视化反馈是结构性优势，难以快速复制。**必须在Month 6前完成工作流引擎V1，在Month 4前完成可视化反馈V1，建立先发壁垒。**

### 5.2 需要快速建立壁垒的功能

**立即建立（Month 1-4，最高优先级）**:

| 壁垒功能 | 建立时间 | 为何难以复制 | 行动项 |
|----------|----------|------------|--------|
| 可视化反馈V1（波形+版图截图） | Month 4 | 需要多模态LLM深度集成+EDA工具截图API | Phase 1核心交付，不可延期 |
| 综合→仿真闭环 | Month 4 | 跨工具数据契约复杂 | Phase 1核心交付 |
| pip install体验 | Month 2 | 工程投入，MCP4EDA无动力做 | Phase 0优先级P0 |

**快速建立（Month 5-8）**:

| 壁垒功能 | 建立时间 | 为何难以复制 | 行动项 |
|----------|----------|------------|--------|
| ngspice MCP（首个SPICE MCP） | Month 7 | 市场首发效应 | Phase 2必交付 |
| 工作流引擎V1 | Month 5 | 需要从0设计DAG引擎，架构复杂 | Phase 2首月 |
| RTL→GDSII完整闭环 | Month 6 | 需要OpenROAD深度集成+PDK管理 | Phase 2里程碑 |

**持续强化（Month 9-12）**:

| 壁垒功能 | 为何是护城河 |
|----------|--------------|
| 领域知识飞轮 | 数据积累随用户增长，复利效应 |
| 工作流模板社区 | 社区贡献形成锁定效应 |
| 多Agent框架 | 技术复杂度极高，需要长期投入 |

### 5.3 开源生态卡位策略

**策略一: 成为 OpenROAD 生态的 MCP 标准**
- 目标: 让 OpenROAD 社区认可 AUTO_EDA 的 MCP Server 为官方推荐接口
- 行动: 向 OpenROAD 仓库提交 MCP 集成文档和示例，参与 OpenROAD Workshop
- 时间: Month 6（RTL→GDSII跑通后有足够可信度）
- 参照: 可考虑与 OpenROAD Agent 项目合并或合作（DA6已分析）

**策略二: 成为 KiCad 插件生态的 AI 入口**
- 目标: 在 KiCad 插件市场发布官方 AUTO_EDA 插件
- 行动: 利用 KiCad IPC API，将 AUTO_EDA 嵌入 KiCad GUI 菜单
- 时间: Month 3（KiCad用户基数~50万，插件市场曝光量极大）

**策略三: 学术用户快速渗透**
- 目标: 在 DAC/ICCAD/DATE 等顶会发表 AUTO_EDA 工具论文
- 行动: Month 8 结束时整理 Phase 1-2 成果，投稿 DAC 2027
- 价值: 学术认可带来高校采用，高校学生是未来工程师，形成长期用户源

**策略四: 开源社区差异化叙事**
- 口号: "The open-source EDA toolkit that actually works with Claude"
- 与 MCP4EDA 叙事区分: MCP4EDA = 工具封装层，AUTO_EDA = AI-Native EDA 工作流平台
- 行动: 每个Phase发布技术博客，在 Hacker News / r/electronics / EDA社区发帖

---

## 6. 12个月关键里程碑时间线

### 6.1 Gantt 风格文字时间线

```
月份   │  1    2    3    4    5    6    7    8    9   10   11   12
───────┼──────────────────────────────────────────────────────────
Yosys  │ ████ done
KiCad  │ ████ done
Veril. │           ████ done
cocotb │           ████ done
KLayout│           ████ done
Vis V1 │                ████ done
闭环1  │                ████ done  (综合→仿真)
WF引擎 │                     ████ done
OpenRD │                     ████████ done
OpenSTA│                          ████ done
ngspice│                               ████ done
闭环2  │                          ████████ done  (RTL→GDSII)
Vis V2 │                                    ████████
多Agent│                                    ████████
知识库 │                                              ████
商业桥 │                                              ████
───────┼──────────────────────────────────────────────────────────
发布   │     P0  │    P1   │         P2        │      P3       │
```

**图例**: WF引擎=工作流引擎，OpenRD=OpenROAD，Vis=可视化反馈

### 6.2 关键里程碑节点

| 编号 | 里程碑 | 目标时间 | 验收标准 | 战略意义 |
|------|--------|----------|----------|----------|
| M0 | MVP基础发布 | Month 2末 | Yosys+KiCad可用，pip install<10min | 项目存在感建立 |
| M1 | 可视化反馈V1 | Month 4 W2 | Claude可分析波形图和版图截图 | 首个EDA可视化MCP |
| M2 | 数字前端闭环 | Month 4末 | 综合→仿真→可视化全自动 | 超越MCP4EDA核心功能 |
| M3 | 工作流引擎V1 | Month 5末 | YAML工作流可执行，支持断点续跑 | 编排层壁垒建立 |
| M4 | RTL→GDSII首跑 | Month 6末 | 计数器全流程跑通（SkyWater 130nm） | 里程碑式技术验证 |
| M5 | ngspice上线 | Month 7末 | 首个SPICE MCP，AC/DC/瞬态可用 | 填补市场空白 |
| M6 | Phase 2发布 | Month 8末 | RTL→GDSII成功率≥80%，Stars≥1000 | 完整开源IC流程 |
| M7 | 多Agent框架 | Month 10末 | 4个专家Agent协作完成RTL→仿真 | L4自主能力起点 |
| M8 | 可视化反馈V2 | Month 10末 | DRC自动修复闭环≤3轮 | 完整AI-EDA体验 |
| M9 | 知识飞轮启动 | Month 11末 | RAG知识库上线，1000+修复案例 | 数据护城河建立 |
| M10 | Phase 3发布 | Month 12末 | 多Agent成功率≥65%，Stars≥3000 | AI-Native EDA平台 |

### 6.3 资源配置建议

| Phase | 核心人力 | 重点投入 | 风险缓冲 |
|-------|----------|----------|----------|
| Phase 1（Month 3-4） | 2名工程师 | Verilator+KLayout+可视化反馈 | 1周（KLayout截图API）|
| Phase 2（Month 5-8） | 3名工程师 | OpenROAD需1人专注 | 2周（P&R稳定性）|
| Phase 3（Month 9-12） | 3-4名工程师 | 多Agent框架+知识飞轮 | 1个月（Agent协调复杂度）|

### 6.4 Go/No-Go 决策门

| 时间点 | Go条件 | No-Go动作 |
|--------|--------|----------|
| Phase 1结束（Month 4） | 闭环成功率≥75% AND KLayout DRC可用 | 延期1个月修复，推迟Phase 2 |
| Phase 2结束（Month 8） | RTL→GDSII成功率≥70% AND 活跃用户≥300 | 延期6周，降低Phase 3范围 |
| Phase 3中期（Month 10） | 多Agent单流程成功率≥50% | 放弃多Agent，专注工作流引擎增强 |

---

## 附录: 关键依赖与外部风险

| 外部依赖 | 风险事件 | 影响Phase | 缓解措施 |
|----------|----------|-----------|----------|
| KiCad IPC API | v10 API 变更 | Phase 0-1 | 适配器层隔离，关注KiCad发版 |
| OpenROAD Python绑定 | 版本不兼容 | Phase 2 | 版本锁定，定期兼容性测试 |
| MCP协议规范 | Anthropic更新协议 | 全程 | 抽象MCP层，快速跟进更新 |
| Claude视觉能力 | 多模态分析质量下降 | Phase 1-3 | 备选: GPT-4V/Gemini Vision |
| SkyWater PDK | 规则更新 | Phase 2 | 冻结测试版本，使用PDK版本管理 |
| ngspice CLI接口 | 版本输出格式变化 | Phase 2 | 输出解析器版本化，添加回归测试 |

---

> 文档版本: 0.1.0 | 下次审查: Month 2末（Phase 0完成后）
> 变更记录: 2026-03-14 初版，基于A8/A9/DA2/DA5/DA6综合规划
