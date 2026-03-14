[根目录](../CLAUDE.md) > **analysis**

# analysis — 技术分析与决策文档

## 模块职责

本模块包含 AUTO_EDA 项目从立项到开发启动前的全部技术分析与决策文档，共 **21 份**。涵盖：技术可行性评估、市场定位与竞争分析、风险评估、差异化策略、技术栈选型决策、工具集成优先级路线图（基础 6 份）；架构深化设计、可视化反馈、Phase 0 实现规格、风险缓解、Claude-MCP 集成、竞争深析、EDA 知识体系（深度分析 DA1-DA7 共 7 份）；工作流引擎设计（A9）；Phase 0 开发计划、代码架构规范、测试策略、社区运营、启动手册（PLAN1-6 共 5 份）；Phase 1-3 长期路线图（P1）。所有文档均为后续开发阶段的决策依据，不含可执行代码。

---

## 文档清单与核心结论

| 文件 | 主题 | 核心结论 |
|------|------|----------|
| [A1_technical_feasibility.md](./A1_technical_feasibility.md) | 技术可行性 | 开源 EDA 工具 MCP 集成整体可行；Yosys/OpenROAD 评分 10.0，ngspice 6.5；3 大硬性阻断项已识别 |
| [A2_market_positioning.md](./A2_market_positioning.md) | 市场定位 | TAM $4.27B（2026）→ $15.85B（2032）；SAM ~$500M；5 大用户画像；定位"开源 EDA 的 AI 能力层" |
| [A4_risk_assessment.md](./A4_risk_assessment.md) | 风险评估 | 22 项风险（5 类）；最高风险：T7 LLM 幻觉（20分）、T1 KiCad API 不稳定（20分） |
| [A5_differentiation_strategy.md](./A5_differentiation_strategy.md) | 差异化策略 | 5 大 USP + 5 大护城河；核心：全栈覆盖（PCB+IC+模拟）+ 可视化反馈闭环 |
| [A7_tech_stack_decision.md](./A7_tech_stack_decision.md) | 技术栈决策 | 选定 Python FastMCP + Pydantic + mypy strict；EDA 生态 Python 原生是核心理由 |
| [A8_integration_roadmap.md](./A8_integration_roadmap.md) | 集成路线图 | 4 阶段 12 个月；优先级 Yosys 8.65 > KiCad 8.55 = OpenROAD 8.55 > cocotb 8.45 |

### 深度分析文档（DA 系列）

| 文件 | 主题 | 核心结论 |
|------|------|----------|
| [DA1_architecture_deep_design.md](./DA1_architecture_deep_design.md) | 架构深化设计 | 多层架构详细设计、模块接口定义、扩展点规划 |
| [DA2_visual_feedback_technical.md](./DA2_visual_feedback_technical.md) | 可视化反馈技术 | 截图→LLM分析→自动修改→验证闭环完整技术方案 |
| [DA3_phase0_implementation_spec.md](./DA3_phase0_implementation_spec.md) | Phase 0 实现规格 | 直接可执行的开发规格：文件结构、API签名、验收标准 |
| [DA4_risk_mitigation_deep.md](./DA4_risk_mitigation_deep.md) | 风险缓解深度分析 | 各风险项代码级缓解方案、技术债务预防清单 |
| [DA5_claude_mcp_integration.md](./DA5_claude_mcp_integration.md) | Claude-MCP 集成 | Claude Code 通过 MCP 最大化操控 EDA 软件的集成模式 |
| [DA6_competitive_deep_analysis.md](./DA6_competitive_deep_analysis.md) | 竞争深度分析 | MCP4EDA/商业EDA/ChipAgents 技术对比与应对策略 |
| [DA7_eda_knowledge_system.md](./DA7_eda_knowledge_system.md) | EDA 知识体系 | EDA 领域知识图谱构建，提升 AI 决策质量 |

### 工作流引擎（A9）

| 文件 | 主题 | 核心结论 |
|------|------|----------|
| [A9_workflow_engine_design.md](./A9_workflow_engine_design.md) | 工作流引擎设计 | DAG 引擎、工作流模板体系、跨工具数据传递方案 |

### 开发规划文档（PLAN 系列）

| 文件 | 主题 | 核心结论 |
|------|------|----------|
| [PLAN1_phase0_development.md](./PLAN1_phase0_development.md) | Phase 0 开发计划 | 可执行任务分解、时间线、里程碑与验收标准 |
| [PLAN2_architecture_spec.md](./PLAN2_architecture_spec.md) | 代码架构规范 | 目录结构、命名约定、模块划分、编码标准 |
| [PLAN3_testing_strategy.md](./PLAN3_testing_strategy.md) | 测试策略 | 四层测试架构、覆盖率目标（≥80%）、CI/CD 集成 |
| [PLAN4_community_ops.md](./PLAN4_community_ops.md) | 社区运营计划 | 开源推广策略、贡献者激励、社区建设里程碑 |
| [PLAN6_kickoff_guide.md](./PLAN6_kickoff_guide.md) | 启动手册 | Day 1 可执行：环境搭建到首个 Tool 上线的逐步指南 |

### 长期路线图（P 系列）

| 文件 | 主题 | 核心结论 |
|------|------|----------|
| [P1_phase_roadmap_detailed.md](./P1_phase_roadmap_detailed.md) | Phase 1-3 路线图 | Month 3-12 详细里程碑、KPI、资源需求规划 |

---

## 技术可行性摘要（A1）

**MCP 集成评分（满分 10）：**

| EDA 工具 | 评分 | 集成方式 |
|----------|------|----------|
| Yosys | 10.0 | Pyosys Python API 直接调用 |
| OpenROAD | 10.0 | OpenROAD Python 绑定 |
| KLayout | 9.5 | pya 官方 Python API + klayout CLI |
| cocotb | 9.5 | Python 框架原生 |
| KiCad | 9.0 | IPC API（v9+）+ kicad-cli Jobsets |
| Verilator | 9.0 | subprocess + Python 封装 |
| ngspice | 6.5 | CLI subprocess，无官方 Python API |

**3 大硬性阻断项：**
- HB-1：商业 EDA 闭源 API，无法集成
- HB-2：GDSII 大文件（>1GB）超出 MCP 上下文限制
- HB-3：EDA 仿真实时性要求（<1ms）超出 MCP 响应延迟

**推荐架构：** 按 EDA 设计域划分独立 MCP Server（PCB / Digital IC / Sim+Verif / File+Report）

---

## 市场定位摘要（A2）

**市场规模：** TAM $4.27B（2026）→ $15.85B（2032），CAGR 20.5%；SAM ~$500M（开源 EDA 用户群）；SOM Year 1 目标 2000-5000 活跃用户

**5 大目标用户画像：**
1. PCB 工程师（主要用户，KiCad 用户群 ~50 万）
2. 数字 IC 工程师（学术/初创，Yosys+OpenROAD 用户群）
3. FPGA 开发者（Yosys 前端用户，~20 万）
4. 学术研究者（高校 EDA 课程，低门槛需求强烈）
5. 半导体初创公司（预算有限，开源 EDA 降本需求）

**核心定位：** "AUTO_EDA 是开源 EDA 的 AI 能力层"

---

## 风险评估摘要（A4）

**22 项风险分布：**

| 类别 | 数量 | 最高风险项 |
|------|------|------------|
| 技术风险 | 8 | T7 LLM 幻觉（影响5×概率4=20）、T1 KiCad API 不稳定（20） |
| 竞争风险 | 4 | C2 商业 EDA 厂商入场（16）、C1 MCP4EDA 扩张（12） |
| 生态风险 | 4 | E1 MCP 协议变更（12）、E2 EDA 工具 API 变更（12） |
| 法律风险 | 3 | L2 商业 EDA ToS 违规（16）、L1 开源许可证冲突（12） |
| 运营风险 | 3 | O1 人力不足（16）、O2 社区采用慢（9） |

**高优先级缓解措施：** 工具调用沙箱隔离（T7）、KiCad IPC API 封装层（T1）、法律咨询（L2）

---

## 差异化策略摘要（A5）

**5 大 USP（独特销售主张）：**
1. 多工具编排：跨 PCB/IC/仿真工具的统一工作流（竞品均单域）
2. 全栈覆盖：PCB + 数字 IC + 模拟仿真三域（MCP4EDA 仅数字 IC）
3. 可视化反馈闭环：EDA 界面截图 → LLM 分析 → 自动修改 → 验证
4. 跨工具工作流自动化：多步骤 EDA 操作一键完成
5. 自然语言驱动设计：零 EDA 命令记忆成本

**5 大护城河：** 跨工具数据管道、可视化反馈引擎、工作流模板生态、领域知识飞轮、社区锁定效应

---

## 技术栈决策摘要（A7）

**最终选型：Python FastMCP + Pydantic + mypy strict**

选择 Python 而非 TypeScript 的核心理由：EDA 生态绝大多数库为 Python 原生
- gdstk（GDSII）、pyverilog（Verilog AST）、PySpice（SPICE）、KLayout pya、OpenROAD bindings、cocotb 全部 Python
- TypeScript 需额外封装层，引入不必要复杂度

**依赖分层：**
- MCP 层：fastmcp、mcp[cli]、pydantic
- EDA 核心层：gdstk、pyverilog、PySpice、kicad-python
- EDA 扩展层：yowasp-yosys、openroad-python、klayout
- 辅助层：pytest、pytest-asyncio、ruff、mypy

**分发策略：** PyPI 分层可选依赖，用户按需安装 `auto-eda[pcb]`、`auto-eda[ic]`、`auto-eda[sim]`、`auto-eda[full]`

**部署：** Docker 多阶段构建，EDA 工具预装镜像

---

## 集成路线图摘要（A8）

**加权优先级矩阵（Top 5）：**

| 排名 | 工具 | 综合评分 | 纳入阶段 |
|------|------|----------|----------|
| 1 | Yosys | 8.65 | Phase 0 |
| 2 | KiCad | 8.55 | Phase 0 |
| 2 | OpenROAD | 8.55 | Phase 1 |
| 4 | cocotb | 8.45 | Phase 1 |
| 5 | KLayout | 8.40 | Phase 1 |

**4 阶段里程碑：**

| 阶段 | 周期 | Server 数 | Tool 数 | 关键 KPI |
|------|------|-----------|---------|----------|
| Phase 0 MVP | Month 1-2 | 3 | ~30 | RTL→网表成功率 >90% |
| Phase 1 核心 | Month 3-4 | +4 | ~60 | 仿真通过率 >85% |
| Phase 2 全流程 | Month 5-8 | +4 | ~100 | RTL→GDSII 全流程成功率 >80% |
| Phase 3 智能化 | Month 9-12 | +跨域 | ~150+ | 可视化闭环验收通过率 >70% |

---

## 对外接口

本模块为纯文档模块，无代码接口。所有文档以 Markdown 格式存储，供以下消费方使用：
- 开发者：开发前阅读 A7（技术栈）和 A8（路线图）确定实现方向
- AI（Claude）：作为架构决策上下文，规避已知风险
- 项目管理：A8 路线图作为里程碑跟踪依据

---

## 常见问题 (FAQ)

**Q: 为什么选 Python 不选 TypeScript？**
A: EDA 生态核心库（gdstk、pyverilog、KLayout pya、OpenROAD bindings、cocotb）均为 Python 原生，TypeScript 需额外封装层。详见 A7_tech_stack_decision.md。

**Q: ngspice 评分为何仅 6.5？**
A: ngspice 无官方 Python API，只能通过 CLI subprocess 调用，集成复杂度高、输出解析困难。PySpice 是最佳封装选择但维护不活跃。详见 A1_technical_feasibility.md。

**Q: MCP4EDA 是否是严重威胁？**
A: 直接竞争但差距明显。MCP4EDA 仅覆盖数字 IC（TypeScript CLI 方式），无 PCB、无 SPICE、无可视化反馈、无多工具编排。AUTO_EDA 全栈覆盖形成差异化。详见 A5_differentiation_strategy.md。

**Q: KiCad API 不稳定风险如何缓解？**
A: KiCad v9 IPC API 仍在演进，建议在 KiCad API 和 MCP Tool 之间加一层适配器，隔离 API 变更影响。详见 A4_risk_assessment.md T1 风险。

---

## 相关文件清单

```
analysis/
├── A1_technical_feasibility.md      # EDA 工具 MCP 集成可行性评分与硬性阻断项
├── A2_market_positioning.md         # 市场规模、用户画像、竞争格局、定位策略
├── A4_risk_assessment.md            # 22 项风险评估矩阵与缓解措施
├── A5_differentiation_strategy.md   # 5 大 USP 与 5 大护城河
├── A7_tech_stack_decision.md        # Python vs TypeScript 技术栈决策全过程
├── A8_integration_roadmap.md        # 工具集成优先级矩阵与 4 阶段路线图
├── A9_workflow_engine_design.md     # DAG 引擎设计、工作流模板、跨工具数据传递
├── DA1_architecture_deep_design.md  # 整体架构深化设计（分层、接口、扩展点）
├── DA2_visual_feedback_technical.md # 可视化反馈闭环完整技术方案
├── DA3_phase0_implementation_spec.md# Phase 0 MVP 精确实现规格（直接可执行）
├── DA4_risk_mitigation_deep.md      # 风险缓解方案与技术债务预防深度分析
├── DA5_claude_mcp_integration.md    # Claude Code 通过 MCP 最大化操控 EDA 软件
├── DA6_competitive_deep_analysis.md # 竞争对手技术深度分析报告
├── DA7_eda_knowledge_system.md      # EDA 领域知识体系构建
├── P1_phase_roadmap_detailed.md     # Phase 1-3 长期路线图细化（Month 3-12）
├── PLAN1_phase0_development.md      # Phase 0 MVP 完整开发计划（可执行）
├── PLAN2_architecture_spec.md       # 代码架构与项目结构规范
├── PLAN3_testing_strategy.md        # 完整测试策略与质量保证计划
├── PLAN4_community_ops.md           # 开源社区建设与推广计划
├── PLAN6_kickoff_guide.md           # 项目启动手册（Day 1 可执行版）
├── INDEX.md                         # 文档导航索引（按使用场景分类）
└── CLAUDE.md                        # 本文档
```

> 注：编号跳过 A3、A6、PLAN5 为正常现象（文档编号预留）。

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始文档，由架构师扫描自动生成（基于全量 6 份分析文档阅读） |
| 2026-03-14 | 0.2.0 | 新增 DA1-DA7 深度分析、A9 工作流引擎、PLAN1-6 开发规划、P1 长期路线图，更新模块索引与文件清单 |
