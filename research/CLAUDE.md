[根目录](../CLAUDE.md) > **research**

# research — 背景调研文档

## 模块职责

本模块包含 AUTO_EDA 项目立项阶段的全部背景调研文档，共 10 份（R1-R10）。涵盖：商业 EDA 市场格局、开源 EDA 工具全景、EDA 自动化 API、现有 MCP 服务器生态、MCP 协议架构、AI-EDA 趋势、EDA 文件格式、Claude+MCP 设计模式、EDA 工作流自动化、EDA+LLM 竞争对手。所有文档为调研原始材料，是 analysis/ 分析文档的信息来源。

---

## 文档清单与核心发现

| 文件 | 主题 | 核心发现 |
|------|------|----------|
| [R1](./R1_commercial_eda_vendors.md) | 商业 EDA 厂商 | Synopsys $7B+、Cadence $5.3B、Siemens ~$2.2B；许可费 $150K-$300K+/席/年 |
| [R2](./R2_opensource_eda_tools.md) | 开源 EDA 工具全景 | KiCad、Yosys、OpenROAD、cocotb、Verilator、KLayout、ngspice 均有 Python 支持 |
| [R3](./R3_eda_automation_apis.md) | EDA 自动化 API | 商业 API 闭源；KiCad IPC API、OpenROAD Python bindings 为开源最佳选择 |
| [R4](./R4_existing_mcp_servers.md) | 现有 MCP 服务器 | MCP4EDA（TypeScript/CLI）；EDA MCP 生态极早期；Blender MCP 可借鉴 |
| [R5](./R5_mcp_architecture.md) | MCP 协议架构 | MCP v2025-11-25；stdio vs Streamable HTTP；Python FastMCP 推荐 |
| [R6](./R6_ai_eda_trends.md) | AI-EDA 趋势 | Cadence ChipStack、Synopsys AgentEngineer（L4）；AlphaChip；cuLitho |
| [R7](./R7_eda_file_formats.md) | EDA 文件格式 | GDSII/OASIS、LEF/DEF、Verilog/VHDL、KiCad S-expr、Gerber；大文件挑战 |
| [R8](./R8_claude_mcp_patterns.md) | Claude+MCP 设计模式 | 5-15 Tools/Server；可视化反馈闭环为关键模式 |
| [R9](./R9_eda_workflow_automation.md) | EDA 工作流自动化 | Qualcomm Airflow EDA 编排；CI/CD for EDA；云 EDA |
| [R10](./R10_eda_llm_competitors.md) | EDA+LLM 竞争对手 | MCP4EDA、ChatEDA、RTLCoder；ChipBench Claude ~31%；多域空白 |

---

## 商业 EDA 格局（R1）

| 厂商 | 年收入 | AI 产品 | 开放性 |
|------|--------|---------|--------|
| Synopsys | $7B+ | AgentEngineer（L4 自主） | 闭源，绑定自家工具 |
| Cadence | $5.3B | ChipStack（多 Agent） | 闭源，绑定自家工具 |
| Siemens EDA | ~$2.2B | Questa One Agentic | 闭源，绑定自家工具 |

商业 EDA AI 全部闭源、许可费 $150K-$300K+/席/年，中小团队和学术界无法负担。这正是 AUTO_EDA 的市场空间。

---

## 开源 EDA 工具全景（R2）

| 工具 | 领域 | Python 支持 | 活跃度 |
|------|------|-------------|--------|
| KiCad | PCB 设计 | IPC API（v9+） | 极高 |
| Yosys | RTL 综合 | Pyosys | 高，工业级 |
| OpenROAD | 物理设计 | Python bindings | 高，OpenLane 基础 |
| Verilator | HDL 仿真 | subprocess | 极高，最快开源仿真器 |
| cocotb | 验证框架 | 原生 Python | 高，业界标准 |
| KLayout | 版图/DRC | pya API | 高 |
| ngspice | SPICE 仿真 | PySpice 封装 | 中，无官方 Python API |

---

## MCP 协议与现有生态（R4、R5）

**MCP v2025-11-25：** stdio 传输（本地）、Streamable HTTP（远程）；三大原语 Tools/Resources/Prompts；JSON-RPC 2.0。Python FastMCP 装饰器语法，与 EDA Python 库无缝集成，推荐用于 AUTO_EDA。

**现有 EDA MCP 项目：**

| 项目 | 覆盖范围 | 语言 | 缺口 |
|------|----------|------|------|
| MCP4EDA | Yosys+OpenLane+KLayout+Icarus | TypeScript/CLI | 无 PCB、无 SPICE、无可视化 |
| kicad-mcp | KiCad 基本操作 | Python/TypeScript | 功能有限 |
| Blender MCP | 3D 建模 | Python | 可借鉴架构，~17.7k stars |

---

## AI-EDA 趋势（R6）

- **Synopsys AgentEngineer：** 宣称 L4 自主设计能力，闭源绑定 Synopsys 工具
- **Cadence ChipStack：** 多 Agent 协作，闭源
- **AlphaChip（Google）：** 强化学习布图规划，已用于 TPU 生产
- **NVIDIA cuLitho：** 计算光刻 GPU 加速，~40x 提速
- **ChipBench 基准：** Claude-4.5-opus ~31%（复杂设计），LLM 幻觉风险在全流程任务中显著

---

## EDA 文件格式与 MCP 挑战（R7）

| 格式 | 用途 | 典型大小 | 策略 |
|------|------|----------|------|
| GDSII/OASIS | 版图 | 100MB-10GB | 分块处理，不直接传入 LLM |
| LEF/DEF | 物理设计 | 1-100MB | 解析库处理，摘要传入 |
| Verilog/VHDL | HDL | 1KB-10MB | 直接传入，LLM 友好 |
| KiCad .kicad_pcb | PCB | 100KB-10MB | S-expression 可解析 |
| SPICE netlist | 电路仿真 | 1KB-10MB | 文本格式，LLM 可读 |

---

## Claude+MCP 设计模式（R8）

从 Chrome DevTools MCP、Pencil MCP、GitHub MCP 案例提炼：
1. **工具粒度：** 每个 Server 5-15 个 Tools，太多 LLM 难以选择
2. **可视化反馈闭环：** 截图 → LLM 分析 → 修改工具 → 再截图验证（AUTO_EDA 核心差异化）
3. **渐进式权限：** 危险操作（覆盖文件、执行仿真）需二次确认
4. **错误信息质量：** MCP Tool 返回的错误需包含足够上下文，帮助 LLM 自我纠错

---

## EDA 工作流自动化（R9）

- **Qualcomm 方案：** Apache Airflow 编排 EDA 工具链（综合→布局布线→签核），DAG 可复用
- **CI/CD for EDA：** RTL 提交触发仿真→综合→时序检查流水线，Jenkins/GitHub Actions
- **云 EDA：** AWS EC2 高内存实例 + EDA AMI；Azure HPC for EDA；弹性扩展解决仿真算力
- **对 AUTO_EDA 的启示：** 工作流模板（DAG）是核心资产，应支持导出/导入/社区共享

---

## EDA+LLM 竞争对手（R10）

| 项目/产品 | 类型 | 覆盖域 | 开放性 | 主要不足 |
|-----------|------|--------|--------|----------|
| MCP4EDA | 开源 MCP | 数字 IC | 开源 | 无 PCB、无模拟、无可视化 |
| ChatEDA | 学术 | 多域（研究） | 开源 | 无工具实际调用 |
| RTLCoder / VeriGen | 学术 LLM | RTL 生成 | 开源 | 仅代码生成，无工具集成 |
| AgentEngineer | 商业 | 数字 IC | 闭源 | 绑定 Synopsys，$150K+/年 |
| ChipStack | 商业 | 数字 IC | 闭源 | 绑定 Cadence |
| ChipAgents | 商业 SaaS | 验证 | 闭源 | $74M 融资，聚焦验证 |

**空白点：** 开源 + 全栈覆盖（PCB+数字IC+模拟）+ 可视化反馈 + 多工具编排 = AUTO_EDA 的定位

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
└── CLAUDE.md
```

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始文档，由架构师扫描自动生成（基于全量 10 份调研文档阅读） |
