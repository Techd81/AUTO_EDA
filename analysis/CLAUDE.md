[根目录](../CLAUDE.md) > **analysis**

# analysis — 技术分析与决策文档

## 模块职责

本模块包含 AUTO_EDA 项目从立项到开发启动前的全部技术分析与决策文档，共 21+ 份。涵盖技术可行性、市场定位、风险评估、技术栈决策、路线图（基础6份）；架构深化、可视化反馈、Phase 0规格、风险缓解、Claude-MCP集成、竞争深析、EDA知识体系（DA1-DA7）；工作流引擎（A9）；开发计划、架构规范、测试策略、社区运营、启动手册（PLAN1-6）；长期路线图（P1）；一致性/研究/总统筹/AI集成/代码质量审计（AUDIT1-5）。

---

## 文档清单与核心结论

| 文件 | 主题 | 核心结论 |
|------|------|----------|
| [A1](./A1_technical_feasibility.md) | 技术可行性 | 开源EDA MCP集成整体可行；Yosys/OpenROAD评分10.0；3大硬性阻断项 |
| [A2](./A2_market_positioning.md) | 市场定位 | TAM $4.27B(2026)；定位"开源EDA的AI能力层" |
| [A4](./A4_risk_assessment.md) | 风险评估 | 22项风险；最高：T7 LLM幻觉(20)、T1 KiCad API不稳定(20) |
| [A5](./A5_differentiation_strategy.md) | 差异化策略 | 5大USP + 5大护城河；全栈覆盖+可视化反馈闭环 |
| [A7](./A7_tech_stack_decision.md) | 技术栈决策 | Python FastMCP + Pydantic + mypy strict |
| [A8](./A8_integration_roadmap.md) | 集成路线图 | 4阶段12个月；Yosys 8.65 > KiCad 8.55 = OpenROAD 8.55 |
| [A9](./A9_workflow_engine_design.md) | 工作流引擎 | DAG引擎、工作流模板、跨工具数据传递 |
| [DA1](./DA1_architecture_deep_design.md) | 架构深化 | 多层架构详细设计、模块接口、扩展点 |
| [DA2](./DA2_visual_feedback_technical.md) | 可视化反馈 | 截图→LLM分析→修改→验证闭环完整方案 |
| [DA3](./DA3_phase0_implementation_spec.md) | Phase 0规格 | 直接可执行开发规格：文件结构、API签名、验收标准 |
| [DA4](./DA4_risk_mitigation_deep.md) | 风险缓解 | 代码级缓解方案、技术债务预防清单 |
| [DA5](./DA5_claude_mcp_integration.md) | Claude-MCP集成 | Claude Code通过MCP最大化操控EDA软件的集成模式 |
| [DA6](./DA6_competitive_deep_analysis.md) | 竞争深析 | MCP4EDA/商业EDA技术对比与应对策略 |
| [DA7](./DA7_eda_knowledge_system.md) | EDA知识体系 | EDA领域知识图谱，提升AI决策质量 |
| [P1](./P1_phase_roadmap_detailed.md) | 长期路线图 | Phase 1-3 Month 3-12里程碑、KPI、资源规划 |
| [PLAN1](./PLAN1_phase0_development.md) | Phase 0开发计划 | 可执行任务分解、时间线、验收标准 |
| [PLAN2](./PLAN2_architecture_spec.md) | 架构规范 | 目录结构、命名约定、编码标准 |
| [PLAN3](./PLAN3_testing_strategy.md) | 测试策略 | 四层测试、覆盖率>=80%、CI/CD集成 |
| [PLAN4](./PLAN4_community_ops.md) | 社区运营 | 开源推广策略、贡献者激励 |
| [PLAN6](./PLAN6_kickoff_guide.md) | 启动手册 | Day 1可执行：环境搭建到首个Tool上线 |
| [AUDIT1-5](./AUDIT3_master_report.md) | 审计报告 | 一致性/研究/总统筹/AI集成/代码质量 |

---

## 技术栈决策摘要（A7）

选定 Python FastMCP + Pydantic + mypy strict。核心理由：EDA生态绝大多数库为Python原生（gdstk、pyverilog、KLayout pya、OpenROAD bindings、cocotb）。

分发策略：PyPI 分层可选依赖 `auto-eda[pcb]`、`auto-eda[ic]`、`auto-eda[sim]`、`auto-eda[full]`。

## 集成优先级（A8）

| 排名 | 工具 | 评分 | 阶段 |
|------|------|------|------|
| 1 | Yosys | 8.65 | Phase 0 |
| 2 | KiCad | 8.55 | Phase 0 |
| 2 | OpenROAD | 8.55 | Phase 1 |
| 4 | cocotb | 8.45 | Phase 1 |
| 5 | KLayout | 8.40 | Phase 1 |

---

## 对外接口

纯文档模块，无代码接口。供开发者开发前阅读、Claude架构决策参考、项目管理里程碑跟踪。

---

## 常见问题 (FAQ)

**Q: 为什么选Python不选TypeScript？**
A: EDA核心库（gdstk、pyverilog、KLayout pya、OpenROAD bindings、cocotb）均为Python原生。详见A7。

**Q: KiCad API不稳定风险如何缓解？**
A: 在KiCad API和MCP Tool之间加适配器层隔离变更影响。详见A4 T1风险。

---

## 相关文件清单

```
analysis/
├── A1_technical_feasibility.md
├── A2_market_positioning.md
├── A4_risk_assessment.md
├── A5_differentiation_strategy.md
├── A7_tech_stack_decision.md
├── A8_integration_roadmap.md
├── A9_workflow_engine_design.md
├── DA1_architecture_deep_design.md
├── DA2_visual_feedback_technical.md
├── DA3_phase0_implementation_spec.md
├── DA4_risk_mitigation_deep.md
├── DA5_claude_mcp_integration.md
├── DA6_competitive_deep_analysis.md
├── DA7_eda_knowledge_system.md
├── P1_phase_roadmap_detailed.md
├── PLAN1_phase0_development.md
├── PLAN2_architecture_spec.md
├── PLAN3_testing_strategy.md
├── PLAN4_community_ops.md
├── PLAN6_kickoff_guide.md
├── AUDIT1_consistency.md
├── AUDIT2_research_strategy.md
├── AUDIT3_master_report.md
├── AUDIT4_ai_integration.md
├── AUDIT5_code_quality.md
├── INDEX.md
└── CLAUDE.md
```

> 编号跳过 A3、A6、PLAN5 为正常现象（预留编号）。

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始文档，架构师扫描自动生成（基础6份分析文档）|
| 2026-03-14 | 0.2.0 | 新增DA1-DA7、A9、PLAN1-6、P1，更新模块索引与文件清单 |
| 2026-03-14 | 0.3.0 | 补充AUDIT1-5审计报告，更新文件清单 |
| 2026-03-14 | 0.4.0 | 架构师增量扫描更新（v0.4.0），与根CLAUDE.md同步 |
