# AUDIT3: AUTO_EDA 项目总统筹审计报告

> 文档编号: AUDIT3（北极星文档）
> 审计日期: 2026-03-14
> 审计范围: 全量文档（analysis/ 21份 + research/ 19份 + 根目录 CLAUDE.md）
> 状态: 完成

---

## 目录

1. [项目整体健康度评估](#1-项目整体健康度评估)
2. [关键成功因素](#2-关键成功因素)
3. [立即行动清单（本周内）](#3-立即行动清单本周内)
4. [30天里程碑](#4-30天里程碑)
5. [项目文档索引](#5-项目文档索引)
6. [总结性评价](#6-总结性评价)

---

## 1. 项目整体健康度评估

### 1.1 文档完整性

**已完成文档（40份）：**

| 层次 | 数量 | 覆盖内容 |
|------|------|----------|
| 基础调研（research/） | 19份 | EDA工具、MCP架构、市场竞争、文件格式、工作流、社区、API |
| 战略分析（analysis/ A系列） | 7份 | 可行性、市场、风险、差异化、技术栈、路线图、工作流引擎 |
| 深度分析（analysis/ DA系列） | 7份 | 架构设计、可视化反馈、Phase0规格、风险缓解、Claude集成、竞争、知识体系 |
| 规划文档（analysis/ PLAN系列） | 6份 | Phase0开发、架构规范、测试策略、社区运营、长期路线图、启动指南 |
| 根目录 | 1份 | 项目概览（CLAUDE.md） |

**缺失内容（开发尚未开始，属正常状态）：**
- 无任何可执行代码
- 无 pyproject.toml / 包结构
- 无 GitHub Actions CI 配置
- 无实际测试套件
- 无 Docker 环境配置
- `auto-eda` 包名未在 PyPI 占位（风险：被他人抢注）

**文档完整性评分：9/10**（规划层面接近完备，缺失均属开发层面，合理）

---

### 1.2 技术准备度

**可以立即开始开发吗？答：是，但有3个前置条件需先处理。**

| 维度 | 状态 | 说明 |
|------|------|------|
| 架构决策 | 完成 | Python FastMCP + Pydantic + mypy strict，无争议 |
| 工具优先级 | 完成 | Yosys(8.65) > KiCad(8.55) = OpenROAD(8.55) > cocotb(8.45) |
| 技术栈 | 完成 | uv + ruff + mypy + pytest，工具链已确定 |
| API可行性 | 完成 | Pyosys/pya/IPC API均已验证，ngspice限制已知 |
| 开发环境 | 未建立 | 需Linux环境（Windows开发EDA工具链阻力大） |
| 包脚手架 | 未建立 | 需uv init建立项目骨架 |
| EDA工具安装 | 未验证 | Yosys/KiCad/OpenROAD需在目标平台实际安装测试 |

**技术准备度评分：7/10**（策略层就绪，执行层待启动）

---

### 1.3 战略清晰度

**方向是否明确？答：极度清晰，是项目最强项。**

- 竞争定位清晰：全栈（PCB+IC+模拟）vs MCP4EDA（仅数字IC），差异化有理有据
- 护城河有序：可视化反馈闭环是当前最大差异化点，无竞品实现
- 技术路径清晰：L1→L2→L3 Agentic逐步提升，4阶段12个月节奏合理
- 商业逻辑清晰：开源引流 + 社区生态 + 知识飞轮，防御性布局完整
- 风险已量化：22项风险逐一评估，T7(LLM幻觉)和T1(KiCad API)为最高优先级

**战略清晰度评分：9.5/10**

---

## 2. 关键成功因素

### 2.1 TOP 5 必须做对的事情

**#1 — 第一个可运行的 Demo 必须震撼人心**

项目当前零代码、零用户，第一次公开露面（v0.1.0发布）是建立社区信任的关键时刻。ngspice MCP是当前市场唯一空白，KiCad MCP是用户基数最大的入口。Demo必须做到：用户看完30秒视频就能理解价值，无需解释。

**#2 — MCP Tool 返回格式必须从第一天设计正确**

每个工具的返回结构（`status` + `summary` + `suggested_next_steps` + `*_uri`引用）一旦确定，所有下游Claude推理都依赖此格式。DA5已给出完整设计原则，必须在Phase 0就严格执行——事后修改成本极高（破坏向后兼容）。

**#3 — KiCad API 适配层必须做封装隔离**

KiCad IPC API是全项目最高风险项（T1，风险分=20），v9→v10迁移已发生一次。必须在MCP Tool与KiCad API之间加一层`KiCadAdapter`抽象，让API变更只影响适配层，不波及MCP工具接口。

**#4 — 测试基础设施必须在写第一行业务代码前建好**

PLAN3测试策略已规划四层测试架构。必须在开发第一个MCP Server前完成：pytest配置、mock EDA工具的fixture、CI流水线。测试债务在EDA领域极难补偿。

**#5 — 社区冷启动必须有「种子用户」策略**

v0.1.0发布前必须私下联系5-10位KiCad论坛活跃用户和EDA领域GitHub活跃贡献者进行内测，获得真实反馈和首批Star。没有种子用户的冷启动极易陷入「没用户因为没Star，没Star因为没用户」的死循环。

---

### 2.2 TOP 3 最大风险

**风险#1 — LLM幻觉导致错误EDA操作（T7，风险分=20）**

Claude对PDK工艺参数、商业工具命令参数、Liberty具体数值存在极高幻觉风险（DA7红区）。缓解：所有MCP Tool必须验证返回值合法性范围；EDA专用System Prompt明确标注幻觉高发区；DA7错误诊断知识库在Phase 0就开始构建。

**风险#2 — 商业EDA厂商快速入场（C2，风险分=16）**

Synopsys/Cadence已有商业AI-EDA产品，MCP协议开放后技术门槛降低，大厂可能迅速推出开源MCP Server抢占生态位。缓解：Phase 0必须在2026年5月前完成；积极与OpenROAD社区合作，争取成为官方推荐集成方案。

**风险#3 — 开发资源不足（O1，风险分=16）**

12个月路线图覆盖11个MCP Server、150+个Tools，若核心开发者只有1-2人，Phase 2（OpenROAD）将成为瓶颈。缓解：Phase 0发布后立即招募社区贡献者；早期建立Maintainer Candidate机制。

---

### 2.3 TOP 3 最大机会

**机会#1 — ngspice MCP：全市场唯一空白**

当前所有已知MCP-EDA项目均无SPICE仿真能力（DA6验证）。第一个可用的ngspice MCP Server将获得「首发优势」，在所有EDA相关MCP列表中形成独特条目。

**机会#2 — 可视化反馈闭环：竞品零覆盖的差异化功能**

KLayout截图→Claude视觉分析→自动修复→验证闭环，当前无任何竞品实现。DA2已完成完整技术方案，Phase 1即可交付V1版本。「AI看着版图给你修DRC」是极具震撼力的演示。

**机会#3 — Tiny Tapeout社区：天然精准用户群**

Tiny Tapeout每轮有数百位参与者，全部使用开源EDA工具链，技术能力强、愿意尝鲜。一旦AUTO_EDA发布Tiny Tapeout端到端教程，可直接转化为忠实用户和贡献者。

---

## 3. 立即行动清单（本周内）

> 基准日期：2026-03-14  截止日期：2026-03-21

### 行动 #1：建立 Python 项目骨架

**负责人**：主开发者
**操作**：在 Linux/WSL2 环境执行 `uv init auto-eda`，建立 `src/auto_eda/servers/` 目录结构，配置 `pyproject.toml`（hatchling构建后端），安装 mcp、pydantic、fastmcp 及开发依赖 ruff、mypy、pytest-asyncio。
**验收标准**：`import auto_eda` 无报错；`ruff check .` 通过；GitHub 仓库已创建并推送初始 commit。

### 行动 #2：在 PyPI 占位包名

**负责人**：主开发者
**操作**：发布空的 v0.0.1 占位包到 PyPI（仅含 pyproject.toml + Coming Soon 说明），使用 `uv build && uv publish`。
**验收标准**：`pypi.org/project/auto-eda` 页面存在。若包名已被占用，立即切换 `autoeda` 备选并同步更新所有文档中的包名引用。

### 行动 #3：搭建 CI/CD 基础设施

**负责人**：主开发者
**操作**：创建 `.github/workflows/ci.yml`，包含三个 Job：`lint`（ruff + mypy strict）、`test-unit`（pytest --cov）、`release`（仅 tag 触发，uv publish）。
**验收标准**：向 main 推送空 commit 后 GitHub Actions 全部绿色通过。

### 行动 #4：实现第一个 MCP Tool（synthesize_rtl）

**负责人**：主开发者
**操作**：参照 DA3_phase0_implementation_spec.md 的精确规格，实现 Yosys MCP Server 的 `synthesize_rtl` 工具。返回格式严格遵循 DA5 设计原则：`status` + `summary` + `suggested_next_steps` + `netlist_uri`。同步编写单元测试（mock Yosys subprocess）。
**验收标准**：pytest 单元测试通过；MCP Inspector 验证 tool schema 合规；可在 Claude Code 中通过自然语言触发并返回正确结构。

### 行动 #5：建立种子用户联络清单

**负责人**：主开发者 / 社区负责人
**操作**：在 KiCad 论坛、r/KiCad、r/chipdesign、Tiny Tapeout Discord 中识别 5-10 位活跃技术用户，私信告知项目并邀请内测。
**验收标准**：内测名单至少 5 位联络人；至少 2 人明确表示愿意试用并提供反馈。

---

## 4. 30天里程碑

### Day 7（2026-03-21）：基础设施就绪

- GitHub 仓库已建立，包含完整目录结构和 README 占位
- PyPI 包名 `auto-eda` 已占位（v0.0.1）
- CI/CD 流水线绿色通过（ruff + mypy + pytest）
- 开发环境文档完成（Linux/WSL2 搭建指南）
- 第一个 MCP Tool `synthesize_rtl` 有单元测试通过
- 种子用户联络清单建立（5+ 人）

**判断标准**：能向种子用户发送「项目已启动」的通知邮件，附 GitHub 链接和预期时间表。

---

### Day 14（2026-03-28）：Yosys MCP Server 可用

- Yosys MCP Server 完整实现（8-10 个 Tools）
- 可通过 Claude Code 对话完成 Verilog 综合（计数器/加法器基准）
- 单元测试覆盖率 >= 80%
- MCP Inspector 验证全部通过
- Verilog 文件解析工具（parse_verilog、extract_modules）可用
- `.mcp.json` 示例配置文件完成，用户可一键接入

**判断标准**：录制第一个内部演示视频（Yosys RTL 综合 Demo），发给种子用户征求反馈。

---

### Day 30（2026-04-13）：KiCad MCP Server 可用 + MVP 接近完成

- KiCad MCP Server 基础版完整实现（10-12 个 Tools）
- KiCadAdapter 封装层已建立，隔离 IPC API 变更风险
- 可通过 Claude Code 完成：打开工程、列出元件、运行 DRC、导出 Gerber
- ngspice MCP Server 基础版（DC/AC/TRAN 分析，5+ Tools）
- 三个 Server 均通过 MCP Inspector 验证
- Phase 0 MVP 完成度 >= 70%（按 PLAN1 验收标准）
- GitHub 仓库公开（若尚未公开）
- Awesome-MCP 列表 PR 已提交

**判断标准**：可向 KiCad 论坛和 r/KiCad 发布内测招募帖，附真实 Demo 截图。距 v0.1.0 正式发布还有约 2 周。

---

## 5. 项目文档索引

> 按「开发时参考优先级」降序排列。第1组为开发必读，第2组为实现参考，第3组为背景知识。

### 第1组：开发必读（每次开始新 Server 前必须阅读）

| 优先级 | 文件路径 | 一句话用途 |
|--------|----------|------------|
| P0 | `D:/AUTO_EDA/CLAUDE.md` | 项目全局概览：架构、技术栈、编码规范、开发阶段入口 |
| P0 | `D:/AUTO_EDA/analysis/DA3_phase0_implementation_spec.md` | Phase 0 精确实现规格，含每个 Tool 的输入输出契约，可直接照着写代码 |
| P0 | `D:/AUTO_EDA/analysis/A8_integration_roadmap.md` | 工具集成优先级矩阵 + 4阶段里程碑，确定「先做什么」 |
| P0 | `D:/AUTO_EDA/analysis/DA5_claude_mcp_integration.md` | MCP Tool 返回格式设计原则，确保 Claude 能自主推进工作流 |
| P0 | `D:/AUTO_EDA/analysis/PLAN1_phase0_development.md` | Phase 0 完整开发计划，含每周任务分解和验收标准 |
| P0 | `D:/AUTO_EDA/analysis/PLAN6_kickoff_guide.md` | Day 1 可执行启动手册，环境搭建到第一个 Tool 的完整步骤 |

### 第2组：实现参考（遇到具体问题时查阅）

| 优先级 | 文件路径 | 一句话用途 |
|--------|----------|------------|
| P1 | `D:/AUTO_EDA/analysis/A7_tech_stack_decision.md` | 技术栈选型全过程，遇到「为什么用 X 不用 Y」时查阅 |
| P1 | `D:/AUTO_EDA/analysis/PLAN2_architecture_spec.md` | 代码架构与项目结构规范，建目录和命名时参考 |
| P1 | `D:/AUTO_EDA/analysis/PLAN3_testing_strategy.md` | 四层测试架构完整策略，写测试时参考 |
| P1 | `D:/AUTO_EDA/analysis/DA1_architecture_deep_design.md` | 整体架构深化设计，理解分层接口和扩展点 |
| P1 | `D:/AUTO_EDA/analysis/DA7_eda_knowledge_system.md` | EDA 领域知识图谱 + Claude 幻觉高发区，设计 System Prompt 时必读 |
| P1 | `D:/AUTO_EDA/analysis/DA2_visual_feedback_technical.md` | 可视化反馈闭环完整技术方案，实现 KLayout 截图功能时参考 |
| P1 | `D:/AUTO_EDA/analysis/A9_workflow_engine_design.md` | DAG 工作流引擎设计，Phase 2 编排器实现参考 |
| P1 | `D:/AUTO_EDA/analysis/DA4_risk_mitigation_deep.md` | 风险缓解方案，遇到技术难题时查阅对应缓解措施 |
| P1 | `D:/AUTO_EDA/analysis/P1_phase_roadmap_detailed.md` | Phase 1-3 长期路线图细化，每个 Server 的精确 Tool 清单 |
| P1 | `D:/AUTO_EDA/analysis/PLAN4_community_ops.md` | 开源社区建设与推广计划，发版和推广时参考 |

### 第3组：背景知识（立项依据，开发中不常翻阅）

| 优先级 | 文件路径 | 一句话用途 |
|--------|----------|------------|
| P2 | `D:/AUTO_EDA/analysis/A1_technical_feasibility.md` | 各 EDA 工具 MCP 集成可行性评分与3大硬性阻断项 |
| P2 | `D:/AUTO_EDA/analysis/A2_market_positioning.md` | 市场规模、用户画像、竞争格局，写 README 和融资材料时参考 |
| P2 | `D:/AUTO_EDA/analysis/A4_risk_assessment.md` | 22项风险评估矩阵，项目决策时查阅风险优先级 |
| P2 | `D:/AUTO_EDA/analysis/A5_differentiation_strategy.md` | 5大USP与5大护城河，对外传播差异化信息时参考 |
| P2 | `D:/AUTO_EDA/analysis/DA6_competitive_deep_analysis.md` | 竞争对手技术深度分析，了解 MCP4EDA 等项目的具体差距 |
| P2 | `D:/AUTO_EDA/research/R2_opensource_eda_tools.md` | 各开源 EDA 工具详细调研（API成熟度、许可证、社区规模） |
| P2 | `D:/AUTO_EDA/research/R5_mcp_architecture.md` | MCP 协议架构深度调研，理解 stdio 传输和 JSON-RPC 细节 |
| P2 | `D:/AUTO_EDA/research/R8_claude_mcp_patterns.md` | Claude MCP 最佳实践模式，Tool 设计参考 |
| P2 | `D:/AUTO_EDA/research/R4_existing_mcp_servers.md` | 现有 EDA MCP Server 调研，了解竞品现状和空白 |
| P2 | `D:/AUTO_EDA/research/NEW_R3_mcp_quality_guide.md` | MCP 质量指南，Tool 设计质量标准参考 |
| P2 | `D:/AUTO_EDA/research/R7_eda_file_formats.md` | EDA 文件格式全景，处理 GDSII/LEF/Liberty 时查阅 |
| P2 | `D:/AUTO_EDA/research/R10_eda_llm_competitors.md` | AI-EDA 竞争对手调研（ChatEDA、AgentEngineer 等） |
| P2 | `D:/AUTO_EDA/research/kicad_mcp_integration_research.md` | KiCad MCP 专项调研，实现 KiCad Server 前必读 |

---

## 6. 总结性评价

### 6.1 项目规划质量评分：8.5 / 10

| 维度 | 分数 | 说明 |
|------|------|------|
| 战略清晰度 | 9.5 | 定位、竞争、护城河、用户画像均有据可依，无模糊地带 |
| 技术深度 | 9.0 | DA系列文档对核心技术难题（MCP返回格式、可视化反馈、上下文管理）有具体解决方案 |
| 风险意识 | 8.5 | 22项风险量化评估，高风险项均有缓解方案，执行层风险识别到位 |
| 执行可操作性 | 8.0 | PLAN系列和DA3已达「可直接写代码」级别，但缺乏对开发者人数/背景的前提假设 |
| 文档一致性 | 8.0 | 40份文档整体一致，但部分文档间存在轻微优先级表述差异（可接受） |
| 社区运营规划 | 8.5 | PLAN4对发布渠道、贡献者激励、文档站点均有详细规划，比大多数开源项目更完备 |
| 速度意识 | 7.5 | 路线图12个月合理，但未明确说明「最小团队规模」前提，单人执行存在严重风险 |

---

### 6.2 最强项

**战略规划的完备性**是本项目的核心优势。从市场定位（A2）到技术可行性（A1）、从竞争分析（DA6）到风险量化（A4）、从工具优先级矩阵（A8）到每个 Tool 的输入输出契约（DA3），每一层都有对应的分析文档。这种规划深度在开源项目中极为罕见——大多数开源项目在「有个好想法」阶段就直接开始写代码，AUTO_EDA 已经把「为什么这样做」和「怎么做」都想清楚了。

特别值得肯定的是 DA5 对 MCP Tool 返回格式的设计（`suggested_next_steps` 字段引导 Claude 自主推进）和 DA7 对 Claude 幻觉高发区的系统性识别，这两点直接决定产品能否达到 L3 Agentic 自主度，是竞品缺乏的核心能力。

---

### 6.3 最弱项

**从「规划完成」到「第一行代码」的跨越尚未发生**，这是目前唯一实质性弱点。40份文档的投入已相当于一个完整的产品设计冲刺，但开发尚未启动。每推迟一个月，就给 MCP4EDA 等竞品多一个月追赶差异化功能的时间。

次要弱项：开发资源规模未在文档中明确假设。路线图基于「至少2名全职开发者」的隐含前提，若只有1人，Phase 2（OpenROAD，最高复杂度）将成为明显瓶颈，需要在启动时就制定「单人版精简路线图」备选方案。

---

### 6.4 给未来开发者的一句建议

**文档已经把路铺好了，现在最危险的事不是走错路，而是站在原地继续规划。**

打开 `analysis/PLAN6_kickoff_guide.md`，按 Day 1 清单执行，把第一个 `synthesize_rtl` Tool 写出来并通过 MCP Inspector——那一刻，项目就真正从「想法」变成了「产品」。

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|---------|
| 2026-03-14 | 1.0.0 | 初始版本，全量文档审计（40份），总统筹审计师生成 |

