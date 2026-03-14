# A8: AUTO_EDA 集成优先级与实施路线图分析报告

> 分析日期: 2026-03-14
> 数据来源: R1-R10 Phase 1 研究报告综合分析
> 分析范围: 工具集成优先级评估、分阶段实施路线图、依赖关系图、资源估算、成功指标

---

## 目录

1. [工具集成优先级矩阵](#1-工具集成优先级矩阵)
2. [分阶段实施路线图](#2-分阶段实施路线图)
3. [各阶段交付物清单](#3-各阶段交付物清单)
4. [依赖关系图与关键路径分析](#4-依赖关系图与关键路径分析)
5. [资源需求估算](#5-资源需求估算)
6. [成功指标与KPI定义](#6-成功指标与kpi定义)
7. [风险评估与缓解策略](#7-风险评估与缓解策略)
8. [附录](#8-附录)

---

## 1. 工具集成优先级矩阵

### 1.1 评估维度定义

| 维度 | 权重 | 说明 |
|------|------|------|
| **用户需求 (User Demand)** | 25% | 目标用户群体大小、使用频率、市场需求强度 |
| **技术可行性 (Tech Feasibility)** | 20% | API成熟度、文档质量、集成难度 |
| **API成熟度 (API Maturity)** | 15% | Python/CLI/TCL接口完善程度、脚本化能力 |
| **竞争差异化 (Differentiation)** | 15% | 与现有MCP-EDA方案的差异性、独特价值 |
| **实现难度逆值 (Ease, inverse)** | 10% | 实现工作量的逆指标，越容易得分越高 |
| **生态影响 (Ecosystem Impact)** | 15% | 对整体AUTO_EDA生态的连接效应和乘数价值 |

### 1.2 开源EDA工具评分矩阵

| 工具 | 用户需求 (25%) | 技术可行性 (20%) | API成熟度 (15%) | 竞争差异化 (15%) | 实现容易度 (10%) | 生态影响 (15%) | **加权总分** | **排名** |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Yosys** (综合) | 9 | 9 | 10 | 6 | 8 | 10 | **8.65** | **1** |
| **KiCad** (PCB设计) | 10 | 8 | 8 | 7 | 7 | 9 | **8.55** | **2** |
| **OpenROAD** (数字后端) | 8 | 9 | 9 | 8 | 7 | 10 | **8.55** | **2** |
| **cocotb** (Python验证) | 8 | 9 | 10 | 7 | 9 | 8 | **8.45** | **4** |
| **Verilator** (HDL仿真) | 8 | 8 | 8 | 6 | 8 | 9 | **7.90** | **5** |
| **KLayout** (版图查看) | 7 | 9 | 9 | 8 | 8 | 7 | **7.85** | **6** |
| **OpenLane/LibreLane** (自动流程) | 7 | 8 | 9 | 5 | 7 | 9 | **7.55** | **7** |
| **ngspice** (SPICE仿真) | 7 | 7 | 6 | 9 | 6 | 7 | **7.20** | **8** |
| **OpenSTA** (时序分析) | 6 | 7 | 7 | 8 | 7 | 8 | **7.10** | **9** |
| **Magic** (版图编辑) | 5 | 6 | 6 | 7 | 6 | 6 | **5.95** | **10** |
| **Xyce** (并行仿真) | 4 | 6 | 6 | 8 | 5 | 5 | **5.50** | **11** |
| **CIRCT** (编译器基础设施) | 4 | 7 | 7 | 6 | 5 | 6 | **5.65** | **12** |

### 1.3 文件格式解析器评分矩阵

| 格式/解析器 | 用户需求 (25%) | 技术可行性 (20%) | API成熟度 (15%) | 竞争差异化 (15%) | 实现容易度 (10%) | 生态影响 (15%) | **加权总分** | **排名** |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Verilog/SV 解析** | 9 | 8 | 8 | 6 | 7 | 9 | **8.00** | **1** |
| **GDSII/OASIS 读写** | 8 | 9 | 9 | 7 | 8 | 8 | **8.20** | **2** |
| **Liberty (.lib) 解析** | 7 | 7 | 7 | 8 | 7 | 8 | **7.35** | **3** |
| **LEF/DEF 解析** | 7 | 7 | 7 | 7 | 7 | 8 | **7.20** | **4** |
| **Gerber/Excellon** | 8 | 7 | 7 | 6 | 7 | 6 | **7.00** | **5** |
| **KiCad S-expr** | 7 | 8 | 7 | 5 | 8 | 6 | **6.85** | **6** |
| **SPEF/SDF** | 5 | 6 | 6 | 8 | 6 | 7 | **6.20** | **7** |
| **SPICE 网表** | 6 | 6 | 5 | 8 | 6 | 6 | **6.15** | **8** |
| **ODB++/IPC-2581** | 4 | 5 | 4 | 7 | 4 | 5 | **4.80** | **9** |

### 1.4 评分依据要点

**Yosys (排名第1)**:
- Pyosys (pybind11) 提供原生Python绑定，TCL接口成熟 (R2: ★★★★★)
- 被称为"硬件的GCC"，4,300+ GitHub stars，290位贡献者 (R2)
- MCP4EDA已有初步集成但功能有限 (R4)，差异化空间在于深度综合参数控制和报告解析
- 是OpenLane/OpenROAD流程的核心引擎，生态乘数效应极高

**KiCad (排名第2)**:
- 最大开源PCB用户群体，v10 IPC API提供成熟Python接口 (R2: ★★★★☆)
- 已有4+个MCP实现但质量参差不齐 (R4)，整合和标准化是差异化方向
- PCB设计是EDA用户基数最广的领域，直接影响用户获取

**OpenROAD (排名第2，并列)**:
- Python/TCL双接口，1,800+ stars，600+流片验证 (R2: ★★★★★)
- 完整RTL-to-GDSII能力，是开源数字IC设计的核心基础设施
- 已有OpenROAD Agent (L2-L3级)，但缺乏MCP标准化接口 (R10)
- 对数字IC全流程自动化具有决定性的生态影响

**ngspice (排名第8, 但差异化最高)**:
- 目前零MCP覆盖 (R4: "no SPICE MCP" gap)
- PySpice外部集成，原生API有限 (R2: ★★★☆☆)
- SPICE仿真是硬件验证不可替代的环节，填补这一空白具有独特竞争价值

---

## 2. 分阶段实施路线图

### 2.1 路线图总览

```
Phase 0: MVP基础 (Month 1-2)
  ├── 核心MCP框架搭建
  ├── Yosys MCP Server (综合)
  ├── KiCad MCP Server (PCB基础)
  └── Verilog文件解析工具

Phase 1: 核心工具链 (Month 3-4)
  ├── Verilator/Icarus MCP Server (仿真)
  ├── cocotb MCP Server (验证)
  ├── KLayout MCP Server (版图)
  ├── GDSII/OASIS文件工具
  └── 综合→仿真闭环

Phase 2: 全流程集成 (Month 5-8)
  ├── OpenROAD MCP Server (物理设计)
  ├── OpenSTA MCP Server (时序)
  ├── ngspice MCP Server (SPICE)
  ├── OpenLane/LibreLane 编排 MCP
  ├── LEF/DEF + Liberty 文件工具
  └── RTL→GDSII完整闭环

Phase 3: 智能化与自主化 (Month 9-12)
  ├── 多Agent编排框架
  ├── AI辅助设计空间探索
  ├── 跨工具PPA优化闭环
  ├── 商业EDA桥接层（实验性）
  └── 自主设计工作流原型
```

### 2.2 Phase 0: MVP基础 (Month 1-2)

**目标**: 建立MCP框架和最小可用产品，验证核心技术路线

**核心原则**:
- 使用Python FastMCP SDK（R5推荐，decorator-driven开发效率最高）
- 每个MCP Server遵循单一职责原则，5-15个tools（R8设计模式）
- stdio传输层优先（Claude Code原生支持，R5）

#### 2.2.1 MCP框架基础设施

| 组件 | 说明 | 技术选型 |
|------|------|----------|
| MCP Server模板 | 标准化项目脚手架 | Python FastMCP + uv包管理 |
| 错误处理框架 | 统一异常和结果格式 | Result-oriented工具设计模式 (R8) |
| 测试框架 | 4层测试策略 | pytest + MCP Inspector + AI模拟 (R8) |
| 日志/可观测性 | 结构化日志 | Python logging + JSON格式 |
| CI/CD模板 | 自动化测试和发布 | GitHub Actions |

#### 2.2.2 Yosys MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | Pyosys Python绑定 (pybind11) + CLI fallback |
| **核心Tools** | `synthesize` (RTL综合), `read_verilog` (读取HDL), `show_rtl` (查看电路图), `stat` (统计报告), `opt` (优化), `write_netlist` (输出网表) |
| **Resources** | 综合报告(JSON), 网表文件, 资源利用率数据 |
| **Tools数量** | 8-12个 |
| **对应文件格式** | Verilog/SV输入, JSON网表/BLIF/EDIF输出 |

#### 2.2.3 KiCad MCP Server (基础版)

| 属性 | 详情 |
|------|------|
| **集成方式** | IPC API (v10 Pythonic接口, R2) + CLI Jobsets (R2) |
| **核心Tools** | `open_project` (打开工程), `list_components` (元件列表), `run_drc` (设计规则检查), `export_gerber` (导出制造文件), `export_bom` (BOM导出), `get_netlist` (网表) |
| **Resources** | 工程文件结构, DRC报告, BOM数据 |
| **Tools数量** | 10-15个 |
| **对应文件格式** | KiCad S-expression, Gerber/Excellon输出 |

#### 2.2.4 Verilog文件解析工具

| 属性 | 详情 |
|------|------|
| **实现方式** | pyverilog + hdlConvertor (R7推荐) |
| **核心功能** | HDL解析, AST提取, 模块层次分析, 端口/参数提取 |
| **Tools** | `parse_verilog` (解析), `extract_modules` (模块提取), `analyze_hierarchy` (层次分析), `lint_check` (语法检查) |

### 2.3 Phase 1: 核心工具链 (Month 3-4)

**目标**: 完成综合→仿真→验证闭环，覆盖数字设计前端核心流程

#### 2.3.1 Verilator/Icarus MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | CLI wrapper (Verilator编译+运行) + 波形解析 |
| **核心Tools** | `compile` (编译HDL到C++), `simulate` (运行仿真), `lint` (检查), `parse_waveform` (VCD/FST解析), `coverage_report` (覆盖率) |
| **Tools数量** | 8-10个 |
| **关键挑战** | Verilator编译为C++需要编译环境管理; Icarus Verilog作为事件驱动仿真补充 |

#### 2.3.2 cocotb MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | 纯Python API (核心框架, R2: ★★★★★) + pytest集成 |
| **核心Tools** | `create_testbench` (生成测试台), `run_test` (执行测试), `analyze_results` (结果分析), `generate_coverage` (覆盖率), `list_tests` (测试列表) |
| **Tools数量** | 6-8个 |
| **独特价值** | Python原生验证框架，与LLM代码生成天然契合 |

#### 2.3.3 KLayout MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | Python pya模块 (R2: ★★★★★) + Ruby脚本 |
| **核心Tools** | `open_gds` (打开版图), `run_drc` (DRC检查), `run_lvs` (LVS验证), `export_image` (截图导出), `cell_info` (单元信息), `layer_operations` (图层操作) |
| **Tools数量** | 10-12个 |
| **对应文件格式** | GDSII/OASIS输入输出 |

#### 2.3.4 GDSII/OASIS文件工具

| 属性 | 详情 |
|------|------|
| **实现方式** | gdstk库 (R7推荐，C++后端高性能) |
| **核心Tools** | `read_gds` (读取), `write_gds` (写入), `cell_list` (单元列表), `layer_summary` (图层摘要), `area_calc` (面积计算), `convert_format` (GDSII↔OASIS转换) |

### 2.4 Phase 2: 全流程集成 (Month 5-8)

**目标**: 实现完整的RTL-to-GDSII闭环，覆盖物理设计和分析环节

#### 2.4.1 OpenROAD MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | Python绑定 + TCL CLI (R2/R3: ★★★★★) |
| **核心Tools** | `init_floorplan` (初始化布局规划), `place_design` (放置), `cts` (时钟树综合), `route_design` (布线), `report_timing` (时序报告), `report_power` (功耗报告), `report_area` (面积报告) |
| **Tools数量** | 12-15个 |
| **复杂度** | 最高——涉及PDK配置、Liberty库、约束文件管理 |

#### 2.4.2 OpenSTA MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | TCL CLI (核心接口, R2) |
| **核心Tools** | `read_design` (读取设计), `read_sdc` (读取约束), `report_checks` (时序报告), `report_worst_slack` (最差余量), `find_critical_paths` (关键路径), `set_timing_derate` (时序降额) |
| **Tools数量** | 8-10个 |
| **依赖** | 需要Liberty库(.lib)和网表，与OpenROAD/Yosys产出对接 |

#### 2.4.3 ngspice MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | CLI交互 + PySpice外部库 (R2: ★★★☆☆) |
| **核心Tools** | `load_circuit` (加载电路), `run_dc` (直流分析), `run_ac` (交流分析), `run_tran` (瞬态分析), `plot_results` (绘图), `measure` (测量), `export_data` (数据导出) |
| **Tools数量** | 8-10个 |
| **竞争差异化** | 目前零MCP覆盖(R4)，填补重要空白 |

#### 2.4.4 OpenLane/LibreLane 编排MCP Server

| 属性 | 详情 |
|------|------|
| **集成方式** | LibreLane Python模块化架构 (R2: ★★★★★) |
| **核心Tools** | `configure_flow` (配置流程), `run_flow` (执行全流程), `run_step` (执行单步), `get_status` (流程状态), `get_reports` (汇总报告), `compare_runs` (对比运行) |
| **Tools数量** | 8-10个 |
| **定位** | 高层编排器，调用底层Yosys/OpenROAD/KLayout |

#### 2.4.5 LEF/DEF + Liberty文件工具

| 属性 | 详情 |
|------|------|
| **LEF/DEF** | 使用OpenROAD内置解析器或独立Python库 |
| **Liberty** | liberty-parser Python库 (R7) |
| **核心Tools** | `parse_lef` (解析LEF), `parse_def` (解析DEF), `parse_liberty` (解析Liberty), `extract_cell_info` (提取单元信息), `timing_summary` (时序摘要) |

### 2.5 Phase 3: 智能化与自主化 (Month 9-12)

**目标**: 构建AI驱动的多Agent协作框架，实现设计空间探索和自主优化

#### 2.5.1 多Agent编排框架

| 属性 | 详情 |
|------|------|
| **参考架构** | ChatEDA (L3, R10), AgentEngineer (L4, R10) |
| **Agent角色** | Design Agent (RTL编写), Verification Agent (测试生成/运行), Optimization Agent (PPA参数调优), Debug Agent (错误诊断/修复) |
| **编排模式** | MCP Sampling primitives + Agent状态机 |
| **通信** | MCP协议内Agent间消息传递 |

#### 2.5.2 AI辅助设计空间探索

| 属性 | 详情 |
|------|------|
| **方法** | 参数化综合扫描 + PPA Pareto分析 |
| **工具** | 调用Yosys/OpenROAD MCP进行批量实验 |
| **输出** | PPA Pareto曲面, 最优配置推荐 |

#### 2.5.3 跨工具PPA优化闭环

```
自然语言规格
    ↓
LLM生成RTL (Verilog MCP)
    ↓
综合 (Yosys MCP) → 时序分析 (OpenSTA MCP)
    ↓                    ↓ (反馈)
布局布线 (OpenROAD MCP)
    ↓
DRC/LVS (KLayout MCP)
    ↓
PPA评估 → 不达标 → 参数调整 → 重新迭代
    ↓ (达标)
GDSII输出
```

#### 2.5.4 商业EDA桥接层（实验性）

| 目标工具 | 桥接方式 | 可行性 | 备注 |
|----------|----------|--------|------|
| Synopsys (DC/PT) | TCL脚本生成+执行 | 中等 | 需用户提供许可证，脚本注入模式 |
| Cadence (Genus/Innovus) | SKILL/TCL脚本生成 | 中等 | SKILL语言复杂度高 |
| Siemens (Calibre) | Calibre svrf脚本 | 低-中 | DRC/LVS脚本模式相对标准化 |

**注意**: 商业工具MCP需要用户自行提供许可证和工具安装环境。AUTO_EDA仅提供脚本生成和结果解析层。

---

## 3. 各阶段交付物清单

### 3.1 Phase 0 交付物 (Month 1-2)

#### MCP Tools

| MCP Server | Tools列表 | 文件格式支持 |
|------------|-----------|-------------|
| **auto-eda-yosys** | `synthesize`, `read_verilog`, `read_liberty`, `show_rtl`, `stat`, `opt_clean`, `opt_merge`, `write_netlist`, `write_blif`, `check` | Verilog/SV (输入), BLIF/JSON (输出) |
| **auto-eda-kicad** | `open_project`, `list_components`, `get_schematic_info`, `run_erc`, `run_drc`, `export_gerber`, `export_bom`, `get_netlist`, `place_component`, `route_track` | KiCad S-expr, Gerber, BOM (CSV) |
| **auto-eda-verilog-utils** | `parse_verilog`, `extract_modules`, `analyze_hierarchy`, `lint_check`, `extract_ports`, `format_code` | Verilog/SystemVerilog |

**总计**: 3个MCP Server, ~28-33个Tools

#### 测试用例

| 测试类别 | 测试场景 | 数量 |
|----------|----------|------|
| **单元测试** | 每个Tool的输入/输出/错误处理 | ~60个 |
| **集成测试** | Yosys综合完整流程(计数器/加法器) | 5个 |
| **集成测试** | KiCad工程操作完整流程 | 5个 |
| **MCP协议测试** | MCP Inspector验证 | 3个 |
| **AI交互测试** | Claude Code端到端测试 | 3个 |

#### 里程碑

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| M0.1: 框架就绪 | Week 2 | MCP模板可用，CI/CD通过，文档齐全 |
| M0.2: Yosys MCP可用 | Week 4 | 可通过Claude对话完成Verilog综合 |
| M0.3: KiCad MCP可用 | Week 6 | 可通过Claude对话进行DRC检查和Gerber导出 |
| M0.4: Verilog工具可用 | Week 7 | 可解析Verilog文件并提取模块信息 |
| M0.5: MVP发布 | Week 8 | 3个Server全部通过测试，README和使用文档完成 |

#### 验收标准

- [ ] 所有MCP Server可通过Claude Code的`.mcp.json`配置并正常连接
- [ ] Yosys MCP可综合至少3种基准设计(计数器、加法器、FIFO)
- [ ] KiCad MCP可打开工程、运行DRC、导出Gerber
- [ ] Verilog解析工具可处理SkyWater PDK标准单元Verilog
- [ ] 单元测试覆盖率 >= 80%
- [ ] MCP Inspector验证全部通过
- [ ] 使用文档和快速入门指南完成

### 3.2 Phase 1 交付物 (Month 3-4)

#### MCP Tools

| MCP Server | Tools列表 | 文件格式支持 |
|------------|-----------|-------------|
| **auto-eda-verilator** | `compile`, `simulate`, `lint`, `parse_vcd`, `parse_fst`, `coverage_report`, `wave_extract`, `clean` | Verilog/SV (输入), VCD/FST (输出) |
| **auto-eda-cocotb** | `create_testbench`, `run_test`, `run_regression`, `analyze_results`, `generate_coverage`, `list_tests` | Python testbench, 覆盖率报告 |
| **auto-eda-klayout** | `open_gds`, `run_drc`, `run_lvs`, `export_image`, `cell_info`, `layer_summary`, `cell_operations`, `pcell_create`, `diff_layouts`, `export_report` | GDSII/OASIS |
| **auto-eda-gds-utils** | `read_gds`, `write_gds`, `read_oasis`, `cell_list`, `layer_summary`, `area_calc`, `convert_gds_oasis`, `merge_gds` | GDSII, OASIS |

**总计**: 4个MCP Server, ~32-36个Tools; 累计7个Server, ~60-69个Tools

#### 测试用例

| 测试类别 | 测试场景 | 数量 |
|----------|----------|------|
| **单元测试** | 每个Tool | ~70个 |
| **集成测试** | Yosys综合→Verilator仿真闭环 | 3个 |
| **集成测试** | cocotb测试台生成→运行→结果解析 | 3个 |
| **集成测试** | KLayout DRC/LVS完整流程 | 3个 |
| **跨Server测试** | Yosys→Verilator→cocotb链路 | 2个 |
| **AI交互测试** | 自然语言驱动综合+仿真闭环 | 3个 |

#### 里程碑

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| M1.1: Verilator MCP | Week 10 | 可编译并仿真Verilog设计 |
| M1.2: cocotb MCP | Week 12 | 可生成和运行Python测试台 |
| M1.3: KLayout MCP | Week 14 | 可读取GDS并运行DRC |
| M1.4: 综合→仿真闭环 | Week 15 | Yosys综合输出可直接作为Verilator仿真输入 |
| M1.5: Phase 1发布 | Week 16 | 7个Server全部可用，闭环验证通过 |

#### 验收标准

- [ ] Verilator可编译SkyWater PDK参考设计并运行仿真
- [ ] cocotb可生成针对标准设计的测试台并获取覆盖率报告
- [ ] KLayout可对OpenROAD输出的GDSII进行DRC检查
- [ ] 自然语言指令"综合这个Verilog设计并仿真验证"可完整执行
- [ ] GDSII/OASIS文件读写和转换功能正常
- [ ] 跨Server数据流无需人工介入

### 3.3 Phase 2 交付物 (Month 5-8)

#### MCP Tools

| MCP Server | Tools列表 | 文件格式支持 |
|------------|-----------|-------------|
| **auto-eda-openroad** | `init_floorplan`, `place_design`, `cts`, `route_design`, `report_timing`, `report_power`, `report_area`, `report_drc`, `optimize_design`, `write_def`, `write_gds`, `set_pdk`, `read_constraints` | LEF/DEF, Liberty, SDC, GDSII |
| **auto-eda-opensta** | `read_design`, `read_sdc`, `read_lib`, `report_checks`, `report_worst_slack`, `find_critical_paths`, `report_clock_skew`, `set_timing_derate` | Verilog网表, Liberty, SDC, SPEF |
| **auto-eda-ngspice** | `load_circuit`, `run_dc`, `run_ac`, `run_tran`, `run_noise`, `plot_results`, `measure`, `export_data`, `set_model` | SPICE网表, 仿真数据 |
| **auto-eda-openlane** | `configure_flow`, `run_flow`, `run_step`, `get_status`, `get_reports`, `compare_runs`, `set_pdk`, `list_designs` | 配置文件, 各阶段报告 |
| **auto-eda-lef-def-utils** | `parse_lef`, `parse_def`, `lef_summary`, `def_summary`, `extract_cell_info` | LEF, DEF |
| **auto-eda-liberty-utils** | `parse_liberty`, `timing_summary`, `cell_list`, `power_summary`, `compare_libs` | Liberty (.lib) |

**总计**: 6个MCP Server, ~52-58个Tools; 累计13个Server, ~112-127个Tools

#### 测试用例

| 测试类别 | 测试场景 | 数量 |
|----------|----------|------|
| **单元测试** | 每个Tool | ~100个 |
| **集成测试** | OpenROAD布局布线完整流程 | 5个 |
| **集成测试** | OpenSTA时序分析+约束处理 | 3个 |
| **集成测试** | ngspice DC/AC/Tran仿真 | 5个 |
| **端到端测试** | RTL→GDSII完整流程 (OpenLane) | 3个 |
| **跨Server测试** | Yosys→OpenROAD→OpenSTA→KLayout链路 | 3个 |
| **PDK兼容性测试** | SkyWater130 + GF180 | 4个 |
| **AI交互测试** | 自然语言驱动完整P&R流程 | 3个 |

#### 里程碑

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| M2.1: OpenROAD MCP | Week 22 | 可完成基准设计的布局布线 |
| M2.2: OpenSTA MCP | Week 24 | 可进行时序分析并报告关键路径 |
| M2.3: ngspice MCP | Week 26 | 可加载SPICE网表并运行三种分析 |
| M2.4: OpenLane编排 | Week 28 | 可运行完整RTL→GDSII流程 |
| M2.5: LEF/DEF/Liberty工具 | Week 30 | 文件解析和信息提取功能完整 |
| M2.6: RTL→GDSII闭环 | Week 32 | 自然语言驱动完整流程可执行 |

#### 验收标准

- [ ] OpenROAD MCP可用SkyWater130 PDK完成参考设计的P&R
- [ ] RTL→GDSII闭环可在Claude对话中一键触发并获取PPA报告
- [ ] ngspice可对提取的SPICE网表进行后仿真
- [ ] 时序分析结果与OpenROAD内部一致
- [ ] 支持至少2个PDK (SkyWater130, GF180MCU)
- [ ] 跨Server工作流无需手动文件传递

### 3.4 Phase 3 交付物 (Month 9-12)

#### MCP Tools

| MCP Server | Tools列表 | 文件格式支持 |
|------------|-----------|-------------|
| **auto-eda-orchestrator** | `create_workflow`, `run_workflow`, `get_workflow_status`, `define_agent`, `assign_task`, `collect_results`, `optimize_ppa`, `explore_design_space` | 工作流定义(YAML/JSON) |
| **auto-eda-commercial-bridge** (实验性) | `generate_tcl_script`, `parse_report`, `translate_constraints`, `adapt_flow` | TCL脚本, 报告文件 |

**总计**: 2个MCP Server, ~14-18个Tools; 累计15个Server, ~126-145个Tools

#### 测试用例

| 测试类别 | 测试场景 | 数量 |
|----------|----------|------|
| **单元测试** | 编排器核心逻辑 | ~30个 |
| **集成测试** | 多Agent协作流程 | 5个 |
| **端到端测试** | NL规格→RTL→GDSII自主流程 | 3个 |
| **性能测试** | 并发Agent任务调度 | 3个 |
| **PPA优化测试** | 设计空间探索收敛性 | 3个 |

#### 里程碑

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| M3.1: 编排框架可用 | Week 38 | 可定义和执行多步骤工作流 |
| M3.2: 多Agent协作 | Week 42 | 设计+验证Agent可协同工作 |
| M3.3: PPA优化闭环 | Week 46 | 自动PPA优化可改善至少10%指标 |
| M3.4: 商业桥接原型 | Week 48 | TCL脚本生成可用于Synopsys DC |
| M3.5: v1.0发布 | Week 48-52 | 全系统集成测试通过，文档完整 |

#### 验收标准

- [ ] 多Agent工作流可自主完成中等复杂度设计（如8位CPU）
- [ ] PPA优化Agent可在给定约束下自动探索并推荐最优配置
- [ ] 编排框架支持自定义工作流定义
- [ ] 商业EDA桥接层可生成语法正确的TCL脚本
- [ ] 系统整体可用性达到MTBF > 100次操作

---

## 4. 依赖关系图与关键路径分析

### 4.1 工具间依赖关系

```
依赖关系图 (→ 表示依赖方向: A→B 表示 B 依赖 A)

[MCP框架基础] ──→ [所有MCP Server]

Phase 0:
  [MCP框架] ──→ [Yosys MCP]
  [MCP框架] ──→ [KiCad MCP]
  [MCP框架] ──→ [Verilog解析工具]

Phase 1:
  [Yosys MCP] ──→ [Verilator MCP] (综合输出作为仿真输入)
  [Verilator MCP] ──→ [cocotb MCP] (仿真引擎作为cocotb后端)
  [MCP框架] ──→ [KLayout MCP] (独立)
  [MCP框架] ──→ [GDSII工具] (独立)

Phase 2:
  [Yosys MCP] ──→ [OpenROAD MCP] (网表输入)
  [OpenROAD MCP] ──→ [OpenSTA MCP] (设计数据库共享)
  [OpenROAD MCP] ──→ [KLayout MCP] (GDSII DRC)
  [MCP框架] ──→ [ngspice MCP] (独立)
  [Yosys MCP] + [OpenROAD MCP] ──→ [OpenLane MCP] (编排底层工具)
  [MCP框架] ──→ [LEF/DEF/Liberty工具] (独立)

Phase 3:
  [所有Phase 0-2 Server] ──→ [编排框架]
  [编排框架] ──→ [多Agent系统]
  [编排框架] ──→ [PPA优化闭环]
  [MCP框架] ──→ [商业桥接层] (独立)
```

### 4.2 关键路径分析

**关键路径** (决定整体项目最短完成时间的路径):

```
MCP框架 → Yosys MCP → Verilator MCP → OpenROAD MCP → OpenLane编排 → 编排框架 → v1.0
   2周       4周         2周            6周            4周           4周      = 22周
```

**次关键路径**:

```
MCP框架 → Yosys MCP → OpenROAD MCP → OpenSTA MCP → PPA优化闭环
   2周       4周          6周           2周          4周        = 18周
```

### 4.3 并行开发机会

| 并行组 | 可并行的工作 | 依赖条件 |
|--------|-------------|----------|
| **P0并行** | KiCad MCP ∥ Verilog工具 | 仅依赖MCP框架 |
| **P1并行** | KLayout MCP ∥ GDSII工具 ∥ (Verilator→cocotb串行) | KLayout和GDSII无互相依赖 |
| **P2并行** | ngspice MCP ∥ LEF/DEF/Liberty工具 ∥ (OpenROAD→OpenSTA串行) | ngspice和文件工具独立 |
| **P3并行** | 商业桥接层 ∥ 多Agent系统 | 桥接层不依赖编排框架 |

### 4.4 风险缓冲建议

| 阶段 | 最高风险项 | 缓冲建议 |
|------|-----------|----------|
| Phase 0 | KiCad IPC API v10尚在RC阶段 | 预留v9 CLI fallback方案，+1周缓冲 |
| Phase 1 | Verilator C++编译环境跨平台问题 | Docker容器化部署，+2周缓冲 |
| Phase 2 | OpenROAD PDK配置复杂度 | 预置SkyWater130 Docker镜像，+3周缓冲 |
| Phase 3 | 多Agent协调的不确定性 | 降级为单Agent顺序执行作为fallback |

---

## 5. 资源需求估算

### 5.1 开发团队配置

#### Phase 0 (Month 1-2): 2-3人

| 角色 | 数量 | 关键技能 | 工作内容 |
|------|------|----------|----------|
| **MCP架构师** | 1 | Python, MCP协议, FastMCP | 框架设计, Yosys MCP |
| **EDA集成工程师** | 1 | KiCad, PCB设计, Python | KiCad MCP, Verilog工具 |
| **QA/DevOps** | 0.5 | pytest, CI/CD, Docker | 测试框架, 自动化 |

#### Phase 1 (Month 3-4): 3-4人

| 角色 | 数量 | 关键技能 | 工作内容 |
|------|------|----------|----------|
| **MCP架构师** | 1 | 延续 | Verilator MCP, 跨Server集成 |
| **验证工程师** | 1 | cocotb, Verilator, Python | cocotb MCP, 仿真工具 |
| **版图工程师** | 1 | KLayout, GDSII, Python | KLayout MCP, GDS工具 |
| **QA/DevOps** | 0.5 | 延续 | 集成测试, 跨Server测试 |

#### Phase 2 (Month 5-8): 4-5人

| 角色 | 数量 | 关键技能 | 工作内容 |
|------|------|----------|----------|
| **MCP架构师** | 1 | 延续 | OpenLane编排, 系统集成 |
| **后端设计工程师** | 1 | OpenROAD, P&R, TCL | OpenROAD MCP, OpenSTA MCP |
| **模拟工程师** | 1 | ngspice, SPICE, PySpice | ngspice MCP |
| **文件格式工程师** | 1 | LEF/DEF, Liberty, 数据解析 | 格式工具Server |
| **QA/DevOps** | 1 | 完整测试体系 | 端到端测试, PDK测试 |

#### Phase 3 (Month 9-12): 4-6人

| 角色 | 数量 | 关键技能 | 工作内容 |
|------|------|----------|----------|
| **AI/Agent架构师** | 1 | LLM, Agent设计, MCP | 多Agent编排框架 |
| **MCP架构师** | 1 | 延续 | 编排器, 系统优化 |
| **EDA领域专家** | 1 | 芯片设计全流程, PPA优化 | 优化策略, 商业桥接 |
| **后端工程师** | 1 | 延续 | PPA闭环优化 |
| **QA/文档** | 1 | 技术写作, 测试 | 完整文档, 性能测试 |

### 5.2 关键技能矩阵

| 技能 | 重要性 | 稀缺度 | 获取建议 |
|------|--------|--------|----------|
| **Python + MCP协议** | 极高 | 中 | 核心团队必备，参考MCP SDK文档 |
| **EDA工具使用经验** | 极高 | 高 | 至少1名有IC设计经验的工程师 |
| **Verilog/SystemVerilog** | 高 | 中 | 基准设计和测试需要 |
| **TCL脚本** | 高 | 低 | OpenROAD/OpenSTA/Yosys的基础语言 |
| **Docker/容器化** | 中 | 低 | 开发和部署环境标准化 |
| **LLM/Agent设计** | 中(Phase 3高) | 高 | Phase 3引入AI/Agent专家 |
| **PCB设计** | 中 | 中 | KiCad集成需要 |
| **SPICE仿真** | 中 | 中 | ngspice集成需要 |

### 5.3 基础设施需求

| 资源 | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|---------|
| **开发机** | 2台Linux workstation | 3台 | 4台 | 5台 |
| **CI/CD** | GitHub Actions (免费) | 同左 | 同左 + self-hosted runner | 同左 |
| **Docker Registry** | Docker Hub (免费) | 同左 | 同左 | 同左 |
| **EDA工具环境** | Docker镜像 (Yosys, KiCad) | +Verilator, KLayout | +OpenROAD, ngspice, OpenLane | +GPU (可选) |
| **PDK** | SkyWater 130nm | 同左 | +GF180MCU | 同左 |
| **测试服务器** | 1台 (CI) | 1台 | 2台 (P&R需高内存) | 2-3台 |
| **存储** | 50GB | 100GB | 500GB (GDS文件) | 1TB |
| **预估月成本(云)** | $200-500 | $500-1000 | $1000-2000 | $1500-3000 |

### 5.4 外部依赖

| 依赖项 | 用途 | 风险 | 缓解 |
|--------|------|------|------|
| **SkyWater PDK** | 开源130nm工艺库 | 低 (Apache 2.0) | 已稳定，Google维护 |
| **GF180MCU PDK** | 开源180nm工艺库 | 低 | 次选PDK |
| **Anthropic MCP SDK** | MCP协议实现 | 低-中 | 活跃开发中，API可能变化 |
| **FastMCP** | Python MCP框架 | 中 | 如不稳定可回退到裸SDK |
| **Claude API** | AI交互测试 | 低 | 可用Claude Code本地测试 |

---

## 6. 成功指标与KPI定义

### 6.1 Phase 0 KPIs (MVP)

| 指标类别 | KPI | 目标值 | 测量方式 |
|----------|-----|--------|----------|
| **功能完整性** | MCP Server可用率 | 3/3 (100%) | 所有Server通过MCP Inspector验证 |
| **技术质量** | 单元测试覆盖率 | >= 80% | pytest coverage |
| **技术质量** | MCP协议合规性 | 100% | MCP Inspector全部检查通过 |
| **用户体验** | 首次使用到完成任务时间 | < 15分钟 | 新用户测试(配置+运行第一个综合) |
| **可靠性** | Tool调用成功率 | >= 95% | 日志统计 |
| **文档** | 快速入门指南完整度 | 100% | 覆盖安装、配置、基本使用 |

### 6.2 Phase 1 KPIs (核心工具链)

| 指标类别 | KPI | 目标值 | 测量方式 |
|----------|-----|--------|----------|
| **功能完整性** | 累计MCP Server | 7/7 (100%) | 全部通过验证 |
| **闭环能力** | 综合→仿真闭环成功率 | >= 90% | 基准设计测试 |
| **技术质量** | 跨Server数据流完整性 | 100% | 集成测试验证 |
| **性能** | 综合+仿真端到端时间 | < 5分钟 (中等设计) | 计时测试 |
| **用户采纳** | GitHub Stars | >= 50 | GitHub统计 |
| **用户采纳** | 活跃issue/PR | >= 10 | GitHub统计 |
| **生态** | 支持的文件格式数 | >= 5 | Verilog, GDSII, OASIS, VCD, Gerber |

### 6.3 Phase 2 KPIs (全流程)

| 指标类别 | KPI | 目标值 | 测量方式 |
|----------|-----|--------|----------|
| **功能完整性** | 累计MCP Server | 13/13 (100%) | 全部通过验证 |
| **闭环能力** | RTL→GDSII成功率 | >= 80% | SkyWater130基准设计 |
| **闭环能力** | PDK兼容性 | 2+ PDK | SkyWater130 + GF180MCU |
| **技术质量** | PPA报告准确性 | 与独立工具对比误差 < 5% | 对照验证 |
| **性能** | 全流程端到端时间 | < 30分钟 (小设计) | 计时测试 |
| **用户采纳** | GitHub Stars | >= 200 | GitHub统计 |
| **用户采纳** | npm/pip安装量 | >= 100/月 | 包管理器统计 |
| **生态** | 支持的文件格式数 | >= 10 | +LEF, DEF, Liberty, SDC, SPEF, SPICE |
| **竞争力** | 与MCP4EDA功能对比 | 覆盖其全部功能+额外50% | 功能清单对照 |

### 6.4 Phase 3 KPIs (智能化)

| 指标类别 | KPI | 目标值 | 测量方式 |
|----------|-----|--------|----------|
| **功能完整性** | 累计MCP Server | 15/15 (100%) | 全部通过验证 |
| **自主能力** | 多Agent工作流成功率 | >= 70% | 标准设计任务测试 |
| **优化效果** | PPA自动优化改善幅度 | >= 10% (任一指标) | 与基线对比 |
| **用户采纳** | GitHub Stars | >= 500 | GitHub统计 |
| **用户采纳** | 月活跃用户(MAU) | >= 50 | 使用统计 |
| **社区** | 外部贡献者数量 | >= 5 | GitHub统计 |
| **可靠性** | 系统MTBF | >= 100次操作 | 故障日志 |
| **文档** | API文档覆盖率 | 100% | 所有public Tool有文档 |

### 6.5 用户采纳目标

```
用户增长目标曲线:

Phase 0 (Month 2):  ~10 早期测试用户 (团队内部+友好用户)
Phase 1 (Month 4):  ~30-50 用户 (开源社区早期采纳者)
Phase 2 (Month 8):  ~100-200 用户 (PCB+数字IC设计师)
Phase 3 (Month 12): ~300-500 用户 (多领域覆盖)

目标用户画像:
├── FPGA/数字设计工程师 (40%)
├── PCB设计工程师 (25%)
├── 高校学生/研究者 (20%)
├── IC设计初创公司 (10%)
└── 模拟/混合信号工程师 (5%)
```

### 6.6 技术质量基线

| 质量维度 | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|----------|---------|---------|---------|---------|
| 单元测试覆盖率 | >= 80% | >= 80% | >= 85% | >= 85% |
| 集成测试覆盖率 | >= 60% | >= 70% | >= 75% | >= 80% |
| Tool调用成功率 | >= 95% | >= 95% | >= 97% | >= 97% |
| 平均响应时间 | < 5s | < 5s | < 10s | < 15s |
| 错误信息可操作性 | >= 80% | >= 90% | >= 90% | >= 95% |
| 文档完整度 | >= 90% | >= 90% | >= 95% | >= 98% |

---

## 7. 风险评估与缓解策略

### 7.1 技术风险

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| **MCP SDK breaking changes** | 中 | 高 | 抽象层隔离SDK细节; 跟踪MCP规范变更 |
| **EDA工具API不稳定** | 中 | 中 | 版本锁定; Docker镜像固化环境; 写适配器层 |
| **OpenROAD PDK配置复杂** | 高 | 高 | 预置Docker镜像; 详细配置文档; PDK安装脚本 |
| **跨平台兼容性** | 中 | 中 | Docker优先; Linux/macOS主要支持; Windows WSL |
| **LLM幻觉导致错误代码** | 高 | 高 | 工具层验证(DRC/LVS检查); 不信任生成结果直接签核 |
| **大规模设计性能瓶颈** | 中 | 中 | 异步Task机制; 超时配置; 增量式结果返回 |

### 7.2 项目风险

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| **EDA领域人才招聘困难** | 高 | 高 | 社区招募; 高校合作; 远程工作 |
| **范围蔓延** | 中 | 中 | 严格Phase gate; 每Phase明确交付物 |
| **竞品快速追赶** | 中 | 中 | 专注差异化(开源+MCP标准化); 社区先发优势 |
| **用户采纳不及预期** | 中 | 高 | 早期用户反馈循环; 降低入门门槛; 丰富示例 |

### 7.3 市场风险

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| **商业EDA厂商推出类似MCP方案** | 中 | 高 | 差异化定位在开源生态; 社区建设 |
| **MCP协议被竞争标准替代** | 低 | 极高 | 抽象层设计; 关注Tool Server Agent (IETF)等新标准 |
| **开源EDA工具发展方向变化** | 低 | 中 | 参与上游社区; 多工具支持降低单点风险 |

---

## 8. 附录

### 8.1 数据来源映射

| 分析维度 | 主要数据来源 |
|----------|-------------|
| 工具API成熟度 | R2 (开源EDA工具), R3 (自动化API) |
| 技术可行性 | R3 (自动化API), R5 (MCP架构) |
| 竞争差异化 | R4 (现有MCP Server), R10 (竞品分析) |
| 用户需求 | R1 (商业EDA), R6 (AI趋势), R10 (市场) |
| 实现难度 | R3 (API难度评级), R5 (SDK对比), R8 (实现模式) |
| 生态影响 | R2 (工具关系), R9 (工作流), R7 (文件格式) |
| 路线图设计 | R4 (差距分析), R9 (工作流优先级), R10 (战略建议) |

### 8.2 竞品差距对照表

| 能力 | MCP4EDA | KiCad MCP (现有) | AUTO_EDA (目标) |
|------|---------|-----------------|-----------------|
| Yosys综合 | 基础 | - | 深度(参数控制+报告) |
| Verilator仿真 | 基础 | - | 完整(波形+覆盖率) |
| OpenLane流程 | 基础 | - | 完整(分步+编排) |
| KiCad操作 | - | 基础(多实现) | 标准化+完整 |
| KLayout版图 | - | - | 完整(DRC/LVS) |
| OpenROAD P&R | - | - | 深度(PPA优化) |
| ngspice仿真 | - | - | 全新(无竞品) |
| OpenSTA时序 | - | - | 全新(无竞品) |
| 文件格式工具 | 有限 | KiCad格式 | 10+格式全覆盖 |
| 多Agent编排 | - | - | 创新(L3-L4级) |
| 商业EDA桥接 | - | - | 实验性 |

### 8.3 Python库技术选型总结

| 用途 | 推荐库 | 备选 | 理由 |
|------|--------|------|------|
| MCP Server框架 | FastMCP | mcp SDK直接使用 | Decorator驱动，开发效率高 (R5) |
| Verilog解析 | pyverilog + hdlConvertor | slang (C++) | Python原生，易集成 (R7) |
| GDSII/OASIS | gdstk | gdspy (维护中) | C++后端高性能，活跃维护 (R7) |
| Liberty解析 | liberty-parser | 自研 | 已有Python库 (R7) |
| SPICE接口 | PySpice | 自研CLI wrapper | 最成熟的Python-SPICE桥接 (R7) |
| cocotb集成 | cocotb原生 | - | 纯Python，直接使用 (R2) |
| KiCad接口 | IPC API (v10) | kicad-python旧API | 官方新API，Pythonic (R2) |
| KLayout接口 | pya模块 | Ruby绑定 | 官方Python绑定 (R2) |

### 8.4 参考架构模式

基于R8 (Claude MCP设计模式)的架构建议:

```
AUTO_EDA MCP 架构层次:

┌─────────────────────────────────┐
│       Claude / LLM Agent        │  (AI层)
├─────────────────────────────────┤
│       MCP Orchestrator          │  (编排层 - Phase 3)
├─────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │Yosys │ │KiCad │ │OpenRD│   │
│  │ MCP  │ │ MCP  │ │ MCP  │   │  (工具MCP层)
│  └──────┘ └──────┘ └──────┘   │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │Veril.│ │cocotb│ │KLay. │   │
│  │ MCP  │ │ MCP  │ │ MCP  │   │
│  └──────┘ └──────┘ └──────┘   │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ngSPI │ │OpenST│ │OpenL.│   │
│  │ MCP  │ │ MCP  │ │ MCP  │   │
│  └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────┤
│  ┌──────────────────────────┐   │
│  │ 文件格式工具 (Utils层)    │   │  (工具层)
│  │ Verilog | GDSII | Liberty │   │
│  │ LEF/DEF | SPICE | Gerber  │   │
│  └──────────────────────────┘   │
├─────────────────────────────────┤
│       EDA工具 (原生安装)         │  (基础设施层)
│  Yosys | KiCad | OpenROAD ...   │
├─────────────────────────────────┤
│       Docker / PDK / OS         │  (环境层)
└─────────────────────────────────┘
```

**设计原则** (R5/R8总结):

1. **单一职责**: 每个MCP Server对应一个EDA工具或文件格式组
2. **结果导向**: Tool返回结构化结果，不返回原始工具输出
3. **防御性设计**: 输入验证、超时处理、错误恢复
4. **扁平参数**: 避免深层嵌套的JSON参数，LLM更容易正确调用
5. **精选工具集**: 每Server 5-15个Tools，避免工具膨胀
6. **stdio传输优先**: Claude Code原生支持，最简部署

---

*分析报告完成。基于R1-R10共10份Phase 1研究报告的综合数据分析。*
*所有评分和估算基于2026年3月公开可用的项目数据和市场信息。*
