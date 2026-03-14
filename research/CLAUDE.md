[根目录](../CLAUDE.md) > **research**

# research — 背景调研文档

## 模块职责

19份背景调研，是 analysis/ 的原始信息来源。涵盖商业EDA市场、开源EDA工具、EDA API、MCP生态、AI趋势、文件格式、Claude+MCP模式、工作流、LLM竞争（R1-R10，10份）；新增调研（NEW_R1-R9，8份）；KiCad专项（1份）。

---

## 文档清单

### 原始调研（R1-R10）

| 文件 | 核心发现 |
|------|----------|
| R1 商业EDA厂商 | Synopsys $7B+、Cadence $5.3B；许可费$150K-$300K+/年 |
| R2 开源EDA工具 | KiCad/Yosys/OpenROAD/cocotb/KLayout/ngspice均有Python支持 |
| R3 EDA自动化API | KiCad IPC API、OpenROAD Python bindings为开源最佳 |
| R4 现有MCP服务器 | MCP4EDA(TypeScript/CLI)；EDA MCP生态极早期 |
| R5 MCP协议架构 | MCP v2025-11-25；stdio/Streamable HTTP；Python FastMCP推荐 |
| R6 AI-EDA趋势 | Cadence ChipStack、Synopsys AgentEngineer(L4)；AlphaChip |
| R7 EDA文件格式 | GDSII/LEF/DEF/Verilog/KiCad S-expr/Gerber；大文件挑战 |
| R8 Claude+MCP模式 | 5-15 Tools/Server；可视化反馈闭环是关键差异化 |
| R9 工作流自动化 | Qualcomm Airflow EDA编排；CI/CD for EDA；云EDA |
| R10 EDA+LLM竞争 | MCP4EDA/ChatEDA/RTLCoder；ChipBench Claude ~31% |

### 新增调研（NEW_R系列）

| 文件 | 主题 |
|------|------|
| NEW_R1 | 商业EDA MCP现状 |
| NEW_R2 | 开源EDA MCP现状 |
| NEW_R3 | MCP质量指南 |
| NEW_R5 | AI-EDA趋势2025 |
| NEW_R6 | EDA Python API |
| NEW_R7 | MCP协议2025 |
| NEW_R8 | EDA社区 |
| NEW_R9 | EDA部署 |

### KiCad专项

`kicad_mcp_integration_research.md` — KiCad v8/v9/v10 IPC API、Python脚本API、现有MCP实现、CLI Jobsets批处理。

---

## 关键结论

**竞争空白：** 开源+全栈覆盖(PCB+数字IC+模拟)+可视化反馈+多工具编排 = AUTO_EDA定位。

**EDA工具Python可行性：** Yosys/OpenROAD评分10.0，KLayout 9.5，KiCad 9.0，ngspice 6.5（无官方Python API）。

**MCP设计模式：** 每Server 5-15工具；工具返回错误信息需含足够上下文供LLM自我纠错；截图→分析→修改→验证闭环为最强差异化。

---

## 相关文件清单

```
research/
├── R1_commercial_eda_vendors.md
├── R2_opensource_eda_tools.md
├── R3_eda_automation_apis.md
├── R4_existing_mcp_servers.md
├── R5_mcp_architecture.md
├── R6_ai_eda_trends.md
├── R7_eda_file_formats.md
├── R8_claude_mcp_patterns.md
├── R9_eda_workflow_automation.md
├── R10_eda_llm_competitors.md
├── NEW_R1_commercial_eda_mcp_status.md
├── NEW_R2_opensource_eda_mcp_status.md
├── NEW_R3_mcp_quality_guide.md
├── NEW_R5_ai_eda_trends_2025.md
├── NEW_R6_eda_python_apis.md
├── NEW_R7_mcp_protocol_2025.md
├── NEW_R8_eda_community.md
├── NEW_R9_eda_deployment.md
├── kicad_mcp_integration_research.md
└── CLAUDE.md
```

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始文档，基于R1-R10全量阅读 |
| 2026-03-14 | 0.2.0 | 新增NEW_R系列+KiCad专项 |
| 2026-03-14 | 0.4.0 | 架构师增量扫描更新，与根CLAUDE.md同步 |
