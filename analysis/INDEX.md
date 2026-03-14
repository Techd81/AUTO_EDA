[根目录](../CLAUDE.md) > [analysis](./CLAUDE.md) > **INDEX**

# analysis — 文档导航索引

> 按使用场景分类，快速定位所需文档。共 21 份文档。

---

## 开发前必读

> 开始编码前，这些文档提供项目的技术基础与直接执行规格。

| 优先级 | 文件 | 内容摘要 |
|--------|------|----------|
| ★★★ | [PLAN6_kickoff_guide.md](./PLAN6_kickoff_guide.md) | Day 1 启动手册：环境搭建、首个 Tool 上线的逐步指南 |
| ★★★ | [DA3_phase0_implementation_spec.md](./DA3_phase0_implementation_spec.md) | Phase 0 精确实现规格：文件结构、API 签名、验收标准 |
| ★★★ | [A7_tech_stack_decision.md](./A7_tech_stack_decision.md) | 技术栈决策：Python FastMCP + Pydantic + mypy strict 选型全过程 |
| ★★★ | [PLAN2_architecture_spec.md](./PLAN2_architecture_spec.md) | 代码架构规范：目录结构、命名约定、模块划分 |
| ★★★ | [PLAN1_phase0_development.md](./PLAN1_phase0_development.md) | Phase 0 开发计划：任务分解、时间线、验收标准 |
| ★★ | [DA1_architecture_deep_design.md](./DA1_architecture_deep_design.md) | 整体架构深化：分层设计、接口定义、扩展点 |
| ★★ | [A8_integration_roadmap.md](./A8_integration_roadmap.md) | 集成路线图：工具优先级矩阵、4 阶段里程碑 |
| ★★ | [A1_technical_feasibility.md](./A1_technical_feasibility.md) | 技术可行性：各 EDA 工具集成评分、3 大硬性阻断项 |

---

## 开发中参考

> 编码过程中遇到具体问题时查阅。

| 场景 | 文件 | 内容摘要 |
|------|------|----------|
| 测试编写 | [PLAN3_testing_strategy.md](./PLAN3_testing_strategy.md) | 四层测试架构、覆盖率目标、CI/CD 集成 |
| 风险规避 | [DA4_risk_mitigation_deep.md](./DA4_risk_mitigation_deep.md) | 各风险项具体缓解代码模式、技术债务预防清单 |
| 风险清单 | [A4_risk_assessment.md](./A4_risk_assessment.md) | 22 项风险评估矩阵（T7 LLM 幻觉、T1 KiCad API 不稳定为最高风险） |
| Claude 集成 | [DA5_claude_mcp_integration.md](./DA5_claude_mcp_integration.md) | Claude Code 通过 MCP 操控 EDA 软件的最优集成模式 |
| 工作流设计 | [A9_workflow_engine_design.md](./A9_workflow_engine_design.md) | DAG 引擎、工作流模板、跨工具数据传递方案 |
| 可视化反馈 | [DA2_visual_feedback_technical.md](./DA2_visual_feedback_technical.md) | 截图→LLM分析→修改→验证闭环完整技术实现 |
| EDA 知识 | [DA7_eda_knowledge_system.md](./DA7_eda_knowledge_system.md) | EDA 领域知识图谱，提升 AI 决策质量 |
| KiCad 专项 | [../research/kicad_mcp_integration_research.md](../research/kicad_mcp_integration_research.md) | KiCad IPC API、Python脚本API、CLI Jobsets 详细调研 |
| EDA Python API | [../research/NEW_R6_eda_python_apis.md](../research/NEW_R6_eda_python_apis.md) | 10 个 EDA 工具 Python API 成熟度、限制、MCP 封装难点 |
| MCP 最佳实践 | [../research/NEW_R3_mcp_quality_guide.md](../research/NEW_R3_mcp_quality_guide.md) | 高质量 MCP 服务器开发最佳实践完整指南 |
| MCP 协议 2025 | [../research/NEW_R7_mcp_protocol_2025.md](../research/NEW_R7_mcp_protocol_2025.md) | MCP 协议与 FastMCP 2025 最新进展 |
| 部署方案 | [../research/NEW_R9_eda_deployment.md](../research/NEW_R9_eda_deployment.md) | Docker化、跨平台、PyPI分发、CI/CD、PDK管理 |

---

## 规划参考

> 产品决策、路线图制定、社区建设时查阅。

| 场景 | 文件 | 内容摘要 |
|------|------|----------|
| 长期规划 | [P1_phase_roadmap_detailed.md](./P1_phase_roadmap_detailed.md) | Phase 1-3（Month 3-12）详细里程碑、KPI、资源需求 |
| 社区运营 | [PLAN4_community_ops.md](./PLAN4_community_ops.md) | 开源推广策略、贡献者激励、社区建设里程碑 |
| 竞争分析 | [DA6_competitive_deep_analysis.md](./DA6_competitive_deep_analysis.md) | MCP4EDA/商业EDA/ChipAgents 技术深度对比 |
| 差异化策略 | [A5_differentiation_strategy.md](./A5_differentiation_strategy.md) | 5 大 USP、5 大护城河、GTM 策略 |
| 市场定位 | [A2_market_positioning.md](./A2_market_positioning.md) | TAM/SAM/SOM、用户画像、竞争格局 |

---

## 调研背景

> 立项阶段的原始调研，提供决策依据和背景知识。

| 文件 | 主题 |
|------|------|
| [../research/R1_commercial_eda_vendors.md](../research/R1_commercial_eda_vendors.md) | 商业 EDA 厂商调研 |
| [../research/R2_opensource_eda_tools.md](../research/R2_opensource_eda_tools.md) | 开源 EDA 工具调研 |
| [../research/R3_eda_automation_apis.md](../research/R3_eda_automation_apis.md) | EDA 自动化 API 调研 |
| [../research/R4_existing_mcp_servers.md](../research/R4_existing_mcp_servers.md) | 现有 MCP 服务器调研 |
| [../research/R5_mcp_architecture.md](../research/R5_mcp_architecture.md) | MCP 架构调研 |
| [../research/R6_ai_eda_trends.md](../research/R6_ai_eda_trends.md) | AI-EDA 趋势调研 |
| [../research/R7_eda_file_formats.md](../research/R7_eda_file_formats.md) | EDA 文件格式调研 |
| [../research/R8_claude_mcp_patterns.md](../research/R8_claude_mcp_patterns.md) | Claude MCP 模式调研 |
| [../research/R9_eda_workflow_automation.md](../research/R9_eda_workflow_automation.md) | EDA 工作流自动化调研 |
| [../research/R10_eda_llm_competitors.md](../research/R10_eda_llm_competitors.md) | EDA LLM 竞争对手调研 |
| [../research/NEW_R1_commercial_eda_mcp_status.md](../research/NEW_R1_commercial_eda_mcp_status.md) | 商业 EDA MCP 现状（新） |
| [../research/NEW_R2_opensource_eda_mcp_status.md](../research/NEW_R2_opensource_eda_mcp_status.md) | 开源 EDA MCP 现状（新） |
| [../research/NEW_R8_eda_community.md](../research/NEW_R8_eda_community.md) | EDA 社区生态调研（新） |

---

## 快速决策导航

```
我要开始写代码              → PLAN6_kickoff_guide.md
我要了解项目结构规范         → PLAN2_architecture_spec.md
我要实现某个 Phase 0 功能   → DA3_phase0_implementation_spec.md
我要写测试                  → PLAN3_testing_strategy.md
我遇到了风险/不确定性        → DA4_risk_mitigation_deep.md
我要集成 KiCad              → research/kicad_mcp_integration_research.md
我要设计工作流引擎           → A9_workflow_engine_design.md
我要了解竞争对手             → DA6_competitive_deep_analysis.md
我要做长期规划               → P1_phase_roadmap_detailed.md
我要运营社区                 → PLAN4_community_ops.md
```

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始创建，索引 analysis/ 全部 21 份文档 |
