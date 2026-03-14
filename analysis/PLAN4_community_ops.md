# PLAN4: AUTO_EDA 开源社区建设与推广计划

> 规划日期: 2026-03-14
> 规划师: 开源运营规划师
> 数据来源: A2_market_positioning + A5_differentiation_strategy + DA6_competitive_deep_analysis + NEW_R1_commercial_eda_mcp_status
> 状态: 完成

---

## 目录

1. [GitHub 仓库建设规划](#1-github-仓库建设规划)
2. [发布策略](#2-发布策略)
3. [推广渠道计划](#3-推广渠道计划)
4. [文档计划](#4-文档计划)
5. [贡献者激励机制](#5-贡献者激励机制)
6. [与 MCP4EDA 的差异化发布定位](#6-与-mcp4eda-的差异化发布定位)

---

## 1. GitHub 仓库建设规划

### 1.1 README.md 内容规划

**设计原则**: 面向三类读者——10秒扫描者（标题+徽章+一句话价值主张）、5分钟评估者（功能截图+快速开始）、深度研究者（架构+贡献指南）。

**结构规划**:

```
README.md 结构

[1] 标题 + 徽章行
    AUTO_EDA — AI-Powered Open-Source EDA via MCP
    徽章: PyPI版本 | Python版本 | License | CI | 文档 | Discord

[2] 一句话价值主张
    "The AI capability layer for open-source EDA —
     connect KiCad, Yosys, OpenROAD, ngspice to any LLM via MCP."

[3] 演示截图区（3张核心截图）
    截图1: Claude Desktop 驱动 KiCad PCB 原理图设计对话
    截图2: 自然语言触发 Yosys→OpenROAD RTL-to-GDSII 全流程
    截图3: ngspice 仿真波形 → LLM 分析 → 自动修正参数

[4] 覆盖范围对比表（vs MCP4EDA vs 商业工具）

[5] 5分钟快速开始
    pip install auto-eda[full] + mcp_config.json 示例

[6] 功能矩阵（PCB / 数字IC / 仿真验证 三列）

[7] 架构图（ASCII）
    LLM ↔ AUTO_EDA Orchestrator ↔ MCP Servers ↔ EDA 工具

[8] 文档链接 + 社区链接

[9] 许可证声明（Apache 2.0）
```

**徽章设计**（shields.io）:

```markdown
[![PyPI version](https://badge.fury.io/py/auto-eda.svg)](https://pypi.org/project/auto-eda/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![CI](https://github.com/YOUR_ORG/auto-eda/actions/workflows/ci.yml/badge.svg)]()
[![Docs](https://img.shields.io/badge/docs-auto--eda.dev-blue)](https://auto-eda.dev)
[![Discord](https://img.shields.io/discord/XXXX?label=Discord&logo=discord)]()
[![Awesome MCP](https://img.shields.io/badge/listed-Awesome--MCP-red)]()
```

### 1.2 CONTRIBUTING.md 规范

**文档结构**:

```
1. 欢迎与贡献类型
   - 新 EDA 工具 MCP Server（最受欢迎）
   - Bug 修复 / 文档改进 / 工作流模板 / 测试用例

2. 开发环境搭建（< 5 分钟）
   git clone → pip install -e ".[dev]" → pre-commit install

3. 项目架构说明（一图理解代码组织）

4. 新 MCP Server 贡献指南（重点）
   - Server 模板文件（复制即用）
   - 必须实现的接口规范
   - 工具命名约定：动词_对象 格式（如 synthesize_rtl）
   - 错误处理规范：返回结构化错误，不抛异常
   - 测试要求：>= 80% 覆盖率，含集成测试

5. PR 流程
   - 标题格式：[server/area] 简短描述
   - 必须通过 CI（ruff + mypy + pytest）
   - 需要一位 Reviewer 批准
   - CHANGELOG.md 更新要求

6. 代码风格（ruff + mypy strict，配置已内置）

7. 行为准则链接（CODE_OF_CONDUCT.md）

8. 贡献者积分说明（链接至 CREDITS.md）
```

### 1.3 Issue 模板设计

路径: `.github/ISSUE_TEMPLATE/`，共三个模板。

**Bug Report** (`bug_report.yml`) 必填字段:
- 受影响的 MCP Server（下拉: kicad/yosys/openroad/ngspice/klayout/cocotb/orchestrator）
- AUTO_EDA 版本
- 问题描述 + 复现步骤
- 环境信息（OS / Python / EDA工具版本 / LLM客户端）

**Feature Request** (`feature_request.yml`) 必填字段:
- 功能领域（下拉: PCB/数字IC/仿真/编排/可视化/部署/文档）
- 动机与使用场景
- 建议方案（可选）
- 贡献意愿复选框

**EDA Tool Integration Request** (`eda_tool_request.yml`) 必填字段:
- 工具名称与主页
- 设计领域（下拉）
- Python/脚本接口情况
- 许可证类型
- 预估用户规模（GitHub Stars 等）
- 贡献意愿：愿意实现 Server / 愿意提供测试用例

### 1.4 PR 模板

路径: `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## 变更类型
- [ ] 新 MCP Server（新 EDA 工具集成）
- [ ] 现有 Server 功能增强
- [ ] Bug 修复
- [ ] 文档改进
- [ ] 测试用例
- [ ] 工作流模板

## 变更描述
<!-- 简述做了什么，为什么这样做 -->

## 受影响的 Server
<!-- 列出受影响的 MCP Server 名称 -->

## 测试情况
- [ ] 已通过 `pytest` 本地测试
- [ ] 已通过 `mypy --strict` 类型检查
- [ ] 已通过 `ruff check` lint
- [ ] 新功能有对应测试用例（覆盖率 >= 80%）

## 相关 Issue
Closes #

## 截图（如适用）
<!-- 对 EDA 工具集成 PR，附上实际运行截图 -->

## CHANGELOG 更新
- [ ] 已在 CHANGELOG.md 添加条目
```

### 1.5 GitHub Actions CI 设计

路径: `.github/workflows/ci.yml`

触发条件: push to main / PR to main

**三个 Job**:

| Job | 内容 | 耗时估算 |
|-----|------|----------|
| `lint` | ruff check + ruff format --check + mypy --strict | < 2 min |
| `test-unit` | pytest tests/unit/ -x --cov | < 5 min |
| `test-integration` | pytest tests/integration/（需 EDA 工具 Docker 环境） | < 15 min |

**发布 Job** (仅 push tag v*):
- build wheel + sdist
- 发布至 PyPI（使用 trusted publisher，无需 API key 存储）
- 创建 GitHub Release，自动填充 CHANGELOG 内容

### 1.6 GitHub Discussions 版块设计

```
Discussions 分类（建议）:

[公告] Announcements
  - 仅维护者发布，版本发布/路线图更新
  - 所有人可回复

[Q&A] Help & Support
  - 安装问题、工具集成调试、LLM配置
  - 标签: kicad / yosys / openroad / ngspice / mcp-config

[展示] Show & Tell
  - 用户分享 AUTO_EDA 使用案例
  - 优秀案例将加入官方文档案例库

[想法] Ideas
  - 新功能想法讨论（比 Feature Request Issue 更轻量）
  - 有足够票数后转换为正式 Issue

[工作流模板] Workflow Templates
  - 社区分享和讨论 EDA 工作流模板
  - 格式: YAML 工作流文件 + 说明 + 截图

[学术/研究] Academic & Research
  - 论文引用、课程采用、研究合作讨论
  - 目标: 学术用户社群建设
```

---

## 2. 发布策略

### 2.1 v0.1.0 发布目标

**目标里程碑**: 对应 A8 集成路线图 Phase 0 MVP 完成节点（Month 2）

**v0.1.0 包含内容**:

| Server | 工具 | 核心工具数 |
|--------|------|----------|
| `auto_eda.servers.digital` | Yosys RTL 综合 | ~10 |
| `auto_eda.servers.pcb` | KiCad 原理图+PCB 基础操作 | ~10 |
| `auto_eda.servers.sim` | ngspice SPICE 仿真（基础） | ~8 |

**v0.1.0 发布 KPI**:
- [ ] `pip install auto-eda` 一键安装
- [ ] Yosys RTL→网表成功率 > 90%（标准基准测试）
- [ ] KiCad 原理图读取/查询功能可用
- [ ] 完整 README + 快速开始文档
- [ ] 3 个演示视频上线

**目标时间**: A8 路线图 Month 2 末（约 2026-05-14）

### 2.2 PyPI 包命名策略

**推荐包名: `auto-eda`**

理由:
- 简洁、可记忆，`pip install auto-eda` 语义清晰
- `auto_eda`（下划线）作为 Python import 名，遵循 PEP 8
- 避免 `kicad-mcp` 等工具特定名（项目定位是全栈，非单一工具）
- 避免 `mcp-eda`（MCP 只是协议，不是产品定位核心）

**分层可选依赖**（A7 决策）:
```bash
pip install auto-eda          # 核心框架，无 EDA 工具绑定
pip install auto-eda[pcb]     # + KiCad 集成依赖
pip install auto-eda[ic]      # + Yosys/OpenROAD/OpenSTA
pip install auto-eda[sim]     # + ngspice/cocotb/Verilator
pip install auto-eda[full]    # 全部依赖
```

**包名备选方案（若 `auto-eda` 已占用）**:
- `autoeda` — 可接受
- `eda-mcp` — 可接受，强调 MCP 定位
- `openeda-mcp` — 次选，强调开源

### 2.3 版本发布节奏

```
v0.1.x (Phase 0-1, Month 1-4): 每 2-3 周一个 patch，快速迭代
  v0.1.0  — MVP: Yosys + KiCad + ngspice 基础
  v0.1.1  — Bug 修复 + 文档补充
  v0.1.2  — OpenROAD 集成 (Phase 1 开始)

v0.2.x (Phase 1-2, Month 3-8): 每 4 周一个 minor，新 Server 上线
  v0.2.0  — cocotb + KLayout + OpenSTA 上线
  v0.2.1  — 多工具编排 Orchestrator v1
  v0.3.0  — 可视化反馈闭环 v1

v0.x.x → v1.0.0 (Phase 3 末, Month 12):
  满足以下条件后发布 v1.0.0:
  - 全部 4 阶段 Server 稳定运行
  - 社区贡献 >= 10 位外部 Contributor
  - 文档覆盖率 >= 90%
  - 用户数 >= 1000 Stars
```

**版本语义**: 严格遵循 SemVer。0.x 阶段 minor 版本号可含 breaking changes（提前在 CHANGELOG 标注）。

### 2.4 Changelog 自动生成

**工具链**: `git-cliff`（Rust 写的 changelog 生成器，配置灵活）

**提交信息约定**（Conventional Commits）:
```
feat(kicad): add schematic export tool
fix(yosys): handle missing liberty file gracefully
docs: update quick start guide
test(ngspice): add DC sweep integration test
chore: bump fastmcp to 0.9.0
```

**git-cliff 配置**（`cliff.toml`）:
- 按 Server 分组（`[kicad]`, `[yosys]`, `[openroad]` 等）
- 自动提取 PR 编号和作者
- 输出 Markdown 格式，直接用于 GitHub Release Notes

**发布流程**:
```bash
git tag v0.1.0
git-cliff --tag v0.1.0 -o CHANGELOG.md
git push origin v0.1.0
# GitHub Actions 自动触发 PyPI 发布 + Release 创建
```

### 2.5 发布公告模板

**v0.1.0 发布公告**（用于 Reddit/X/KiCad 论坛）:

```
标题: AUTO_EDA v0.1.0 — 开源 EDA 的 AI 能力层，支持 KiCad/Yosys/ngspice MCP 集成

正文:
AUTO_EDA 是一个开源项目，通过 MCP 协议将 KiCad、Yosys、ngspice
等工具连接至 Claude/GPT 等 LLM，让工程师用自然语言驱动 EDA 工作流。

✨ v0.1.0 亮点:
• KiCad PCB/原理图 AI 辅助（首个完整 IPC API 集成）
• Yosys RTL 综合 MCP（Python Pyosys 原生集成）
• ngspice SPICE 仿真（首个开源 SPICE MCP Server）
• pip install auto-eda[full] 一键安装

与 MCP4EDA 相比:
• 支持 PCB 设计（MCP4EDA 不支持）
• 首创 ngspice MCP（无任何项目有此能力）
• Python 原生（非 TypeScript CLI 封装）

快速开始: https://auto-eda.dev/quickstart
GitHub: https://github.com/YOUR_ORG/auto-eda
```

---

## 3. 推广渠道计划

### 3.1 EDA 专业社区

**KiCad 论坛** (forum.kicad.info)
- 目标版块: Development / Third Party Tools
- 发布时机: v0.1.0 发布后第一周
- 内容策略: 聚焦 KiCad MCP Server，展示 IPC API 深度集成
- 差异化信息: 与 Seeed-Studio kicad-mcp-server 相比，完整 IPC API 集成而非基础封装
- 注意事项: 论坛氛围保守，强调工具辅助而非替代工程师

**OpenROAD GitHub Discussions** (github.com/The-OpenROAD-Project)
- 目标版块: Show & Tell
- 发布时机: v0.2.0（OpenROAD MCP Server 上线后）
- 内容策略: 与 OpenROAD Agent 对比，展示 MCP 标准化优势
- 合作机会: 提议将 AUTO_EDA OpenROAD MCP Server 合并入官方 OpenROAD-flow-scripts

**EEVblog 论坛** (eevblog.com/forum)
- 目标版块: EDA / PCB / Homebrew
- 受众: 电子爱好者、硬件工程师（偏 PCB）
- 内容策略: 演示 KiCad + Claude 全流程，降低门槛叙事（不需要记命令行）
- 注意事项: 受众实用主义倾向，强调节省时间的具体数据

### 3.2 Reddit

| Subreddit | 规模 | 发布内容 | 时机 |
|-----------|------|---------|------|
| r/KiCad | ~50K 成员 | KiCad MCP Server 演示帖 | v0.1.0 发布时 |
| r/ECE | ~200K 成员 | 全栈 EDA AI 能力介绍 | v0.2.0 发布时 |
| r/chipdesign | ~30K 成员 | 数字IC MCP 工作流演示 | v0.2.0 发布时 |
| r/ClaudeAI | ~100K 成员 | AUTO_EDA 作为 MCP 生态案例 | v0.1.0 发布时 |
| r/MachineLearning | ~2.5M 成员 | AI-EDA 技术文章（非直接推广） | v1.0 前后 |
| r/FPGA | ~100K 成员 | Yosys + FPGA 工作流演示 | v0.2.0 发布时 |

**Reddit 发布规范**:
- 技术演示帖优先于纯推广帖（社区更接受）
- 附带 GIF/视频演示，文字说明保持简洁
- 作者在评论区积极回复，建立信任
- 遵循各 subreddit 规则，避免被标记为 spam

### 3.3 Twitter/X EDA 社区

**目标账号互动策略**:
- 关注并引用 @kicad_pcb、@OpenROAD_EDA、@YosysHQ 等官方账号
- 参与 #EDA、#OpenSourceEDA、#KiCad、#ChipDesign 话题标签
- 每个版本发布配套发布线程（Thread）：功能亮点 + 演示 GIF + 安装命令

**内容节奏建议**:
- 平时: 每周 2-3 条技术内容（EDA 工具使用技巧、MCP 协议介绍）
- 发版: 发布日集中发布 5-10 条线程
- 互动: 遇到 EDA+AI 相关讨论主动回复，建立专家形象

**关键 KOL 列表**（建议关注与互动）:
- EDA 工具维护者：Yosys、OpenROAD、KiCad 官方账号
- AI-EDA 研究者：发布 MCP4EDA/ChatEDA 等论文的作者
- 硬件设计博主：EEVblog、Andreas Spiess 等

### 3.4 Awesome-MCP 列表提交

**目标仓库**:
1. `punkpeye/awesome-mcp-servers`（最大 MCP 列表，10K+ stars）
2. `appcypher/awesome-mcp-servers`
3. `TechXplainator/awesome-mcp-servers`

**提交时机**: v0.1.0 发布后立即提交 PR

**提交信息模板**:
```
### EDA & Hardware Design
- [AUTO_EDA](https://github.com/YOUR_ORG/auto-eda) -
  Full-stack open-source EDA MCP servers: KiCad PCB design,
  Yosys RTL synthesis, OpenROAD P&R, ngspice SPICE simulation.
  Python-native, supports any MCP-compatible LLM client.
```

**维护 Awesome 列表**:
- 将 AUTO_EDA 所有子 Server 分别提交到相关工具的 Awesome 列表
- 如：kicad-mcp-server 提交至 `awesome-kicad` 列表

### 3.5 Hacker News 发布策略

**发布时机**: v0.1.0 发布约 2 周后（让项目先积累一些 GitHub stars 和真实用户反馈）

**标题策略**（HN 标题风格）:
- 推荐: "AUTO_EDA: MCP servers connecting KiCad, Yosys, and ngspice to LLMs"
- 避免: 含有营销词汇（"revolutionary"、"game-changing"）
- 可选: "Show HN: AUTO_EDA – open-source EDA tools for Claude/GPT via MCP"

**发布时间**: 工作日 UTC 14:00-18:00（美国东海岸早上，HN 流量高峰）

**评论区准备**:
- 准备好技术深度问题的回答（MCP 协议细节、EDA 工具 API 原理）
- 准备与 MCP4EDA 差异化的清晰表述
- 对负面评论保持专业、不防御性地回应

**预期效果**: 成功的 HN 帖子可带来 500-2000 GitHub stars，是最高 ROI 的单次推广活动。

### 3.6 学术社区

**DAC / ICCAD 相关渠道**:
- DAC（Design Automation Conference）: 每年 6 月，2027 目标提交 Demo Paper 或 Work-in-Progress
- ICCAD: 每年 11 月，2026 目标提交 Tool Demo
- arXiv 技术报告: 在 v0.3.0 后发布 AUTO_EDA 架构论文（cs.AR 或 eess.SP 分类）
- 引用链接: 在论文中明确对比 MCP4EDA（arXiv:2507.19570），指出覆盖范围和架构扩展

**高校合作策略**:
- 目标课程: VLSI 设计、数字集成电路、EDA 算法等课程
- 合作形式: 提供课程材料、Guest Lecture、学生项目支持
- 优先目标学校: 在 GitHub 上有 EDA 相关课程仓库的高校
- 激励: 提供教育账号的优先支持，课程采用列入官方文档

**Tiny Tapeout 社区**:
- Tiny Tapeout 用户是 AUTO_EDA 的天然用户（开源工具流片）
- 在 Tiny Tapeout Discord 和论坛发布集成指南
- 提供 Tiny Tapeout + AUTO_EDA 端到端教程

---

## 4. 文档计划

### 4.1 文档架构

```
auto-eda.dev 文档站点结构

/                        首页（价值主张 + 快速演示）
/quickstart              5分钟快速开始
  /install               安装指南（pip / Docker）
  /first-design          第一个设计：KiCad PCB 示例
  /configure-llm         LLM 客户端配置（Claude Desktop / Cursor）

/tutorial                分领域教程
  /pcb                   PCB 设计教程系列
    /kicad-basics        KiCad MCP 基础操作
    /drc-assistant       AI 辅助 DRC 检查
    /bom-management      BOM 管理自动化
  /digital-ic            数字 IC 教程系列
    /rtl-synthesis       Yosys RTL 综合入门
    /place-and-route     OpenROAD 布局布线
    /timing-analysis     OpenSTA 时序分析
  /simulation            仿真教程系列
    /spice-basics        ngspice SPICE 仿真
    /cocotb-testing      cocotb Python 验证
  /workflows             多工具工作流教程
    /rtl-to-gdsii        RTL-to-GDSII 全流程
    /pcb-to-gerber       PCB 全流程到 Gerber

/api-reference           API 参考（自动生成自 docstring）
  /servers               各 MCP Server 工具列表
  /orchestrator          编排器 API
  /data-types            Pydantic 数据模型

/examples                案例库
  /counter               8位计数器 RTL→GDSII
  /blinky                LED Blinky PCB 设计
  /alu                   简单 ALU 设计验证
  /rc-filter             RC 滤波器 SPICE 仿真

/contributing            贡献指南
/changelog               版本历史
/roadmap                 开发路线图（公开）
```

### 4.2 文档工具选型

**推荐: MkDocs + Material for MkDocs**

| 工具 | 优点 | 缺点 | 适用性 |
|------|------|------|--------|
| MkDocs + Material | Python 生态原生，配置简单，搜索优秀，免费托管 GitHub Pages | 定制化不如 Docusaurus | 强烈推荐 |
| Docusaurus | React 生态，功能强大，i18n 支持好 | 需要 Node.js，对 Python 项目略显陌生 | 备选 |
| Sphinx | Python 传统文档工具，autodoc 强大 | 样式老旧，配置复杂 | 不推荐（除非纯 API 文档） |

**MkDocs 关键插件**:
- `mkdocs-material`: 主题（免费版功能已足够）
- `mkdocstrings[python]`: 从 docstring 自动生成 API 参考
- `mkdocs-git-revision-date-localized`: 自动显示文档最后更新时间
- `mkdocs-minify-plugin`: 压缩 HTML/CSS/JS

**托管方案**: GitHub Pages（免费，自动从 `gh-pages` 分支部署，CI 触发）

### 4.3 视频教程计划

计划制作 3 个核心演示视频，用于 README 展示和推广渠道传播。每个视频时长 3-5 分钟，无需旁白（字幕+操作演示）。

**视频 1: KiCad PCB 设计 AI 辅助**

```
脚本大纲:
0:00 - 0:20  开场：展示 Claude Desktop 界面 + KiCad 界面并排
0:20 - 1:00  演示1: 用自然语言查询 PCB 设计规则
             "What are the clearance rules for this PCB?"
             → AUTO_EDA 返回 KiCad DRC 规则摘要
1:00 - 2:00  演示2: 请求 DRC 检查并解释错误
             "Run DRC and explain any errors in plain English"
             → 自动运行 DRC → LLM 解释违规原因和修复建议
2:00 - 3:00  演示3: 元器件信息查询
             "Find all capacitors on this board and their values"
             → KiCad IPC API 查询 → 返回 BOM 摘要
3:00 - 4:00  演示4: 可视化反馈（若 v0.2+ 功能）
             截图 PCB → LLM 分析布局密度 → 提出优化建议
4:00 - 5:00  结尾：GitHub 链接 + pip install 命令
```

**视频 2: Yosys RTL 综合全流程**

```
脚本大纲:
0:00 - 0:15  开场：展示一个简单的 Verilog 计数器代码
0:15 - 1:00  演示1: 自然语言触发综合
             "Synthesize this counter module targeting SkyWater 130nm"
             → Yosys 运行 → 显示综合报告（面积/时序统计）
1:00 - 2:00  演示2: 综合结果分析
             "What's the critical path and how can I optimize it?"
             → LLM 分析综合报告 → 给出优化建议
2:00 - 3:30  演示3: 参数调优迭代
             "Try optimizing for speed instead of area"
             → 重新综合 → 对比前后结果
3:30 - 5:00  演示4: 生成 OpenROAD 输入
             "Prepare the netlist for place-and-route"
             → 输出 .v netlist + .sdc constraints
```

**视频 3: 多工具编排 RTL-to-GDSII**

```
脚本大纲（v0.3+ 功能，Phase 2 后制作）:
0:00 - 0:20  开场：展示目标「从 Verilog 到 GDSII 全自动」
0:20 - 2:00  演示: 单条指令触发全流程
             "Take this ALU design through the complete RTL-to-GDSII flow"
             → 自动编排：Yosys 综合 → OpenSTA 时序 → OpenROAD P&R
             → KLayout DRC → GDSII 导出
2:00 - 3:30  中间步骤：展示各阶段日志和结果摘要（无需用户干预）
3:30 - 4:30  结果展示：KLayout 中打开最终 GDSII 版图截图
4:30 - 5:00  结尾：强调「15分钟完成过去需要数小时的流程」
```

**制作工具**: OBS Studio（录制）+ DaVinci Resolve（剪辑，免费版足够）
**发布渠道**: YouTube（主渠道）+ 嵌入文档站点 + 发版公告中引用

---

## 5. 贡献者激励机制

### 5.1 贡献者积分体系

**积分规则**（记录在 `CREDITS.md` 中，每个 Release 更新）:

| 贡献类型 | 积分 | 说明 |
|----------|------|------|
| 新 EDA 工具 MCP Server（完整实现） | 100 | 包含测试和文档 |
| 重大功能增强（>200行代码） | 50 | 经 Reviewer 认可 |
| Bug 修复（影响核心功能） | 20 | |
| Bug 修复（一般） | 10 | |
| 文档改进（新增教程） | 20 | |
| 文档修复/改善 | 5 | |
| 工作流模板贡献 | 15 | |
| Issue 报告（有效且详细） | 5 | |
| 帮助其他用户解决问题（被标记 Accepted Answer） | 3 | |

**积分等级与权益**:

| 等级 | 积分门槛 | 称号 | 权益 |
|------|----------|------|------|
| Bronze | 10+ | Contributor | 名字列入 CREDITS.md |
| Silver | 50+ | Core Contributor | README 贡献者墙 + Discord 特殊角色 |
| Gold | 200+ | Maintainer Candidate | 邀请担任 Reviewer + 路线图讨论参与权 |
| Platinum | 500+ | Core Maintainer | 仓库写权限 + 版本决策参与权 |

### 5.2 新工具贡献指南

贡献新 EDA 工具 MCP Server 是最受欢迎的贡献类型。流程设计要降低门槛。

**一键脚手架**（v0.2.0 后提供）:
```bash
uvx auto-eda new-server --name magic_vlsi --domain layout
# 自动生成:
#   src/auto_eda/servers/magic_vlsi/
#     __init__.py
#     server.py     <- 包含示例工具实现
#     models.py     <- Pydantic 数据模型
#     tests/
#       test_server.py
#     README.md
```

**新 Server 验收标准**（PR Checklist）:
1. 至少实现 3 个有意义的 MCP 工具
2. 所有工具有完整 docstring（工具描述 + 参数说明）
3. 单元测试覆盖率 >= 80%
4. 至少 1 个集成测试（实际调用工具）
5. Server README 说明：工具安装要求、支持平台、已知限制
6. 工具命名遵循约定：`verb_noun` 格式（如 `synthesize_module`）
7. 错误处理：所有工具返回结构化错误，不抛出未捕获异常

### 5.3 社区维护者制度

**维护者职责**:
- 审查 PR（目标: 48 小时内初步响应）
- 分类和优先级排序 Issue
- 参与路线图讨论
- 帮助新贡献者上手

**Domain Maintainer 制度**（每个 EDA 领域一位维护者）:

| 领域 | 负责 Server | 招募时机 |
|------|------------|----------|
| PCB | kicad | v0.1.0 发布后，从活跃贡献者中招募 |
| 数字IC | yosys, openroad, opensta | v0.2.0 后 |
| 仿真验证 | ngspice, cocotb, verilator | v0.2.0 后 |
| 版图 | klayout, magic | v0.2.0 后 |
| 编排 | orchestrator | v0.3.0 后 |

**维护者招募流程**:
1. 在某领域积累 Gold 级积分（200+）
2. 维护者团队邀请或本人申请
3. 1个月试用期（辅助现有维护者）
4. 正式授权：仓库写权限 + Domain Maintainer 徽章

**退出机制**: 连续 3 个月无贡献自动转为 Emeritus（荣誉维护者），保留积分和称号。

---

## 6. 与 MCP4EDA 的差异化发布定位

### 6.1 发布信息设计

**核心叙事框架**: "从工具原型到完整平台"

MCP4EDA 验证了 EDA+MCP 的可行性，AUTO_EDA 将这一概念扩展为完整的工程平台。这一叙事避免了直接对抗（尊重 MCP4EDA 的先驱价值），同时清晰传达了升级价值。

**五个清晰的超越点（对外传播版）**:

1. **覆盖范围**: MCP4EDA 支持数字 IC 综合流程（6个工具）。AUTO_EDA 支持 PCB + 数字IC + SPICE仿真的完整工作流（12+工具）。
2. **首创 ngspice MCP**: 目前没有任何开源项目提供 SPICE 仿真 MCP Server。
3. **首创 KiCad 完整集成**: 通过 KiCad v9/v10 IPC API 实现深度集成，而非 CLI 封装。
4. **多工具编排**: 内置编排层，单条指令可触发跨工具工作流（如 RTL→综合→P&R→时序分析）。
5. **Python 原生**: 所有 Server 均为 Python，与 EDA 生态（gdstk、pyverilog、PySpice）无缝集成，无需 Node.js/TypeScript。

**禁忌表述**（避免在推广中使用）:
- "MCP4EDA 的替代品"（显得对抗）
- "MCP4EDA 很差"（不尊重先驱）
- "完全重写了 MCP4EDA"（不准确）

**推荐表述**:
- "在 MCP4EDA 奠定基础之上，AUTO_EDA 扩展至全栈 EDA"
- "AUTO_EDA 是面向 PCB 工程师、IC 工程师和仿真工程师的统一平台"

### 6.2 迁移指南设计

文档路径: `/docs/migration/from-mcp4eda.md`

**迁移指南结构**:

```
1. 为什么考虑迁移
   - 如果你只做数字IC综合，MCP4EDA 仍然是好选择
   - 如果你需要 PCB / ngspice / 多工具编排，AUTO_EDA 是更好选择

2. 功能对应关系
   MCP4EDA Tool          → AUTO_EDA 等价工具
   yosys_synthesize()    → synthesize_rtl() in digital server
   iverilog_simulate()   → simulate_rtl() in sim server
   verilator_compile()   → compile_verilator() in sim server
   openlane_run()        → run_flow() in digital server
   klayout_view()        → view_layout() in layout server
   gtkwave_open()        → open_waveform() in sim server

3. Claude Desktop 配置迁移
   替换 mcp_config.json 中的 server 配置块
   （提供完整的 before/after 配置示例）

4. 常见问题
   Q: MCP4EDA 的 Docker 环境能继续用吗？
   A: AUTO_EDA 提供独立 Docker 镜像，无需保留 MCP4EDA 环境。

   Q: 我的 MCP4EDA 自定义脚本能迁移吗？
   A: 工具命名约定有差异，参考上方对应表转换工具调用名称。
```

### 6.3 对比表格设计

**用于 README 和推广材料的对比表**:

| 功能 | AUTO_EDA | MCP4EDA | 商业 AI-EDA |
|------|----------|---------|-------------|
| PCB 设计 (KiCad) | 完整支持 | 不支持 | 部分支持（Siemens） |
| RTL 综合 (Yosys) | 支持 | 支持 | 支持（绑定自家工具） |
| 物理设计 (OpenROAD) | 支持 | 支持（OpenLane） | 支持（绑定自家工具） |
| 时序分析 (OpenSTA) | 支持 | 不支持 | 支持 |
| SPICE 仿真 (ngspice) | 支持（首创） | 不支持 | 支持（闭源） |
| Python 验证 (cocotb) | 支持 | 不支持 | 不支持（开源） |
| 多工具编排 | 内置编排层 | 无 | 有（闭源） |
| 可视化反馈闭环 | 支持（v0.3+） | 不支持 | 部分支持 |
| 实现语言 | Python（原生） | TypeScript/CLI | 专有 |
| 部署方式 | pip / Docker | Docker | SaaS / Cloud |
| 许可证 | Apache 2.0 | 开源 | 商业许可 |
| 年费用 | 免费 | 免费 | $100K-$500K+ |
| LLM 支持 | 任意 MCP 客户端 | Claude Desktop/Cursor | 专有/绑定 |

**表格使用场景**:
- README 中以折叠块形式展示（避免 README 过长）
- 推广帖子中以截图形式附上
- 文档站点独立页面 `/docs/comparison`

### 6.4 与 MCP4EDA 的关系定位时间线

| 阶段 | 关系定位 | 策略 |
|------|----------|------|
| v0.1.0 发布 | "互补"定位 | 强调不重叠的 PCB/ngspice 能力，主动在 MCP4EDA Issue 中友好提及 AUTO_EDA |
| v0.2.0 发布 | "扩展"定位 | 发布迁移指南，在对比文档中保持客观 |
| v0.3.0+ | "平台"定位 | 编排层和可视化闭环建立显著技术差距，自然形成差异化 |
| v1.0.0 | 行业标准定位 | 争取成为 "Awesome-MCP-EDA" 类列表的首推项目 |

---

## 附录：社区建设关键指标（OKR）

### Year 1 目标（2026-05 至 2027-05）

**O1: 建立活跃开源社区**
- KR1: GitHub Stars >= 1000（v1.0.0 发布前）
- KR2: 外部 Contributor >= 15 人
- KR3: Discord 成员 >= 500
- KR4: 月活跃 Issue/PR >= 20

**O2: 确立技术领导地位**
- KR1: 列入 3+ 主流 Awesome-MCP 列表
- KR2: 被 2+ 学术论文引用或使用
- KR3: 被 1+ 高校课程采用
- KR4: PyPI 月下载量 >= 2000

**O3: 覆盖范围全面超越 MCP4EDA**
- KR1: v0.2.0 支持 10+ EDA 工具（MCP4EDA: 6）
- KR2: 覆盖 PCB + 数字IC + 仿真三个领域（MCP4EDA: 仅数字IC）
- KR3: 工作流模板库 >= 5 个社区贡献模板

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始版本，基于 A2/A5/DA6/NEW_R1 综合规划 |