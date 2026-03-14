# AUDIT1: AUTO_EDA 技术方案交叉一致性审计报告

> 审计日期: 2026-03-14
> 审计师: 首席技术审计
> 审计范围: DA1、DA3、DA4、PLAN1、PLAN6（5份文档）
> 审计方法: 逐文档交叉比对 + 技术可行性推演

---

## 执行摘要

本次审计覆盖 AUTO_EDA 项目 Phase 0 全部技术规划文档，包含架构深化设计（DA1）、
Phase 0 实现规格（DA3）、风险缓解深度分析（DA4）、Phase 0 开发计划（PLAN1）和
启动手册（PLAN6）共 5 份文档，累计约 25 万字技术内容。

整体方案架构分层清晰、风险意识充分、代码示例质量高。发现 **2 项严重问题**、
**6 项警告**、**3 项建议**。严重问题集中在包路径命名冲突和 ProgressReporter
实现断层，必须在 Day 1 前解决，否则阻塞开发启动。

**总体评分: 6.5 / 10**

---

## 审计维度一：技术决策一致性

### 1.1 包结构命名冲突 [严重]

**问题描述**: 五份文档对共享基础层的包路径存在系统性不一致。

| 文档 | 基础层路径 | 错误处理模块 |
|------|-----------|------------|
| DA1 §1.2.1 目录树 | `auto_eda/base/` | `auto_eda/base/errors.py` |
| DA1 §1.2.2 代码示例 | `auto_eda/base/server.py` | `from .errors import EDAErrorClassifier` |
| DA3 §1.1 目录树 | `auto_eda/core/` | `auto_eda/core/errors.py` |
| PLAN1 Day2 任务 | `auto_eda/core/` | `src/auto_eda/core/errors.py` |
| PLAN6 §3.1 代码 | `auto_eda/core/` | `auto_eda/core/errors.py` |

DA1 全文使用 `auto_eda/base/`；DA3、PLAN1、PLAN6 三份文档全文使用 `auto_eda/core/`。
开发者若按 PLAN6 脚手架命令创建目录，DA1 的 `BaseEDAServer`、`ProgressReporter`
代码示例将因 import 路径错误无法运行。

**影响等级**: 严重 — 首日开发即产生阻塞

**修复建议**: 以多数文档（3:1）采用的 `auto_eda/core/` 为唯一标准，
更新 DA1 §1.2.1 目录树及全部代码示例的 import 路径。

---

### 1.2 ProgressReporter 实现为空 Placeholder [严重]

**问题描述**: DA1 §1.2.3 定义的 `ProgressReporter._emit` 方法体为空 `pass`，
注释说明「实现时通过 ctx: Context 参数注入」，但 DA3、PLAN1、PLAN6 均未给出
任何具体实现方案。FastMCP 的 `Context.report_progress()` 必须在 `@mcp.tool`
装饰函数内注入 `ctx: Context` 参数，而 `ProgressReporter` 作为独立类无法直接
访问该 Context 对象。

**影响**: 综合、DRC 等长时任务执行期间无法向 Claude 报告进度，Claude 客户端
将在默认 120s 超时后断开。DA4 §1.4 将长时任务超时列为高风险项（T5），其缓解
措施依赖 ProgressReporter 正常工作，形成循环依赖。

**修复建议**: DA1 补充 `_emit` 的可行实现方案：
- 方案 A：`ProgressReporter` 持有 `ctx: Context` 引用，每次工具调用时传入
- 方案 B：工具函数使用 `async for` yield 返回进度中间结果（FastMCP 原生支持）

---

### 1.3 Yosys Tool 数量规格不一致 [警告]

| 文档 | Yosys Tool 数 | 说明 |
|------|--------------|------|
| DA3 §4 精确规格 | 5 个 | synthesize/stat/check/write_netlist/show_rtl |
| PLAN1 §3.2 开发计划 | 10 个 | 上述 5 + read_verilog/read_liberty/opt_clean/opt_merge/write_blif |
| PLAN1 §1.1 交付目标 | 28-33（三 Server 合计） | 未细分到各 Server |

DA3 被标注为「精确实现规格」仅列 5 个工具，PLAN1 Week 3-4 却定义了 10 个工具
的完整 Pydantic 模型，工作量与文档描述失真。

**修复建议**: DA3 §4 补充后 5 个工具并标注「MVP 核心 5 + Phase 0 扩展 5」分层；
PLAN1 §1.1 细化各 Server 工具数量分布。

---

### 1.4 MCP SDK 版本上界约束不一致 [警告]

| 文档 | MCP SDK 版本约束 |
|------|----------------|
| DA3 §2 pyproject.toml | `mcp[cli]>=1.3.0`（无上界） |
| PLAN1 §2.3 版本锁定策略 | `mcp[cli]>=1.3.0,<2.0.0` |
| PLAN6 §2.2 pyproject.toml | `mcp[cli]>=1.3.0`（无上界） |

DA3 和 PLAN6 是「直接可执行」的操作型文档，开发者会直接复制其 pyproject.toml
内容，缺少上界约束将导致未来 mcp 2.0 发布时依赖解析失败。

**修复建议**: 统一所有文档示例为 `mcp[cli]>=1.3.0,<2.0.0`。

---

### 1.5 KiCad 版本与 CI 环境不对齐 [警告]

| 文档 | KiCad 版本要求 |
|------|---------------|
| DA4 §1.1 | v10 RC2，推荐 IPC_V10 模式 |
| PLAN6 §1.3 | 本地安装 `ppa:kicad/kicad-10.0-releases` |
| PLAN1 §1.3 范围外 | Phase 0 IPC API 为存根，不实际调用 |
| PLAN1 §2.4.3 CI Docker | `KiCad >= 7.0.0` |

CI Docker 接受 v7+，本地推荐安装 v10。kicad-cli DRC 输出格式在 v8/v9/v10 之间
存在字段差异，集成测试可能本地通过而 CI 失败。Phase 0 既然不实际调用 IPC API，
推荐安装 v10 的动机不清晰。

**修复建议**: CI Docker 锁定至 KiCad v10；或在 PLAN6 补充「Phase 0 任意 >=8
版本均可，IPC API 在 Phase 1 激活」说明。

---

### 1.6 Python 3.13 支持声明不一致 [警告]

| 文档 | Python 兼容版本 |
|------|---------------|
| DA3 §2 classifiers | 3.10 / 3.11 / 3.12（无 3.13） |
| PLAN1 §1.2 技术约束 | 3.10 / 3.11 / 3.12 / **3.13** |
| PLAN1 §2.4.1 CI 矩阵 | 3.10 / 3.11 / 3.12 / **3.13** |

DA3 的 classifiers 未包含 3.13，但 CI 矩阵测试 3.13。pyverilog、gdstk
对 3.13 兼容性未经核实，存在隐性依赖风险。

**修复建议**: DA3 补充 3.13 classifier；DA4 技术债务清单增加
「pyverilog/gdstk Python 3.13 兼容性验证」跟踪项。

---

### 1.7 AsyncIterator import 冗余导致 CI 失败 [警告]

DA1 §1.2.3 `progress.py` 代码示例第 3 行：`from typing import AsyncIterator`
该 import 在文件中从未使用（`stream_subprocess_output` 返回 `list[str]`
而非 `AsyncIterator`）。`ruff` F401 规则会将此报为错误导致 CI lint 失败。

**修复建议**: 删除该 import，或将 `stream_subprocess_output` 改为
`AsyncIterator[str]` 生成器（后者在流式场景下架构更优）。

---

## 审计维度二：实现可行性

### 2.1 Phase 0 工作量估算合理性 [通过]

**8周/30工具** 目标整体可行，但各阶段密度不均。

| 阶段 | 周期 | 工具数 | 评估 |
|------|------|--------|------|
| Week 1-2 基础框架 | 10天 | 0 | 合理，Day-by-Day 分解清晰 |
| Week 3-4 Yosys Server | 10天 | 10 | 合理，含集成测试日 |
| Week 5-6 KiCad Server | 10天 | 15 | 偏紧，任务密度过高 |
| Week 7-8 集成与发布 | 10天 | Verilog Utils+CI | 宽松，可消化 KiCad 溢出 |

KiCad 阶段（Week 5-6）需完成 15 个工具 + IPC 存根 + DRC 输出解析 + kicad-cli
Jobsets 集成，若同期实现 DA4 §1.1 版本探测适配器则压力更大。Verilog Utils
（Week 7-8）借助 pyverilog 封装复杂度低，时间明显富余。

**修复建议**: 将 Verilog Utils Server 提前至 Week 5（与 KiCad 并行开发），
KiCad Server 延展至 Week 6-7，Week 8 专注集成与发布。

---

### 2.2 Pyosys 双路径策略的可行性风险 [建议]

PLAN1 §3.3 要求 `YosysSynthesizer` 运行时动态选择 Pyosys 或 yosys-cli，
但 Phase 0 的 Pyosys 路径为 stub，引入风险大于收益：

- 测试复杂度翻倍：每个工具需覆盖两条路径，mock 策略复杂
- Pyosys ABI 不稳定：随 Yosys 主版本更新可能出现 ABI 变化
- Phase 0 实际价值低：节省 200ms/次对交互式 MCP 调用影响可忽略

**建议**: Phase 0 仅实现 yosys-cli 路径，Pyosys 路径推迟至 Phase 1。

---

## 审计维度三：架构完整性

### 3.1 错误处理链路完整性 [通过]

五份文档合并覆盖了完整的错误处理链路：

- DA1 §4 定义了三层错误分类（工具层 / 领域层 / 协议层）
- DA3 §9 定义了错误码命名空间（1xxx 通用 / 2xxx 工具可用性 / 3xxx Yosys / 4xxx KiCad / 5xxx Verilog）
- PLAN6 §3.1 `EDAError.to_mcp_error_text()` 实现了错误 → MCP 文本的格式化链路
- DA4 §1.1-1.4 覆盖了运行时错误的 fallback 策略

错误码命名空间在 DA3 §9 和 PLAN6 §3.1 之间完全一致，无矛盾。

---

### 3.2 测试覆盖完整性 [通过，有缺口]

| 测试层级 | 覆盖状态 | 说明 |
|----------|----------|------|
| 单元测试 | 完整 | Day-by-Day 任务包含每模块测试 |
| MCP 协议合规测试 | 完整 | `tests/mcp/` 目录，100% 覆盖要求 |
| 集成测试 | 完整 | `tests/integration/`，需 EDA 工具环境 |
| 端到端（Claude Code 真实调用） | 部分 | PLAN1 Day18 有描述，但无自动化方案 |
| 幻觉防护有效性测试 | 缺失 | DA4 §1.2 LLMSafetyGuard 无对应测试设计 |

---

## 审计维度四：技术债务风险

### 4.1 跨域 Pydantic 模型提前耦合 [建议]

DA1 §2.2 `base/models.py` 定义了 `SynthesisResult`（Yosys→OpenROAD 接口契约）
和 `PhysicalDesignResult`（OpenROAD→KLayout 接口契约）。OpenROAD 和 KLayout
均为 Phase 1 工具，在 Phase 0 基础层定义其接口模型会造成：

- Phase 0 发布的 `v0.1.0` 中包含未实现功能的公共接口，用户 import 后获得无法使用的类
- Phase 1 接口变更时需修改 `base/models.py`，违反「各层只修改自身」原则
- PyPI 包体包含多余的模型定义，误导早期用户

**建议**: Phase 0 `base/models.py` 仅包含通用基础类型（`DRCViolation`、`DRCResult`）；
`SynthesisResult`、`PhysicalDesignResult` 移至各自 Server 的 `models.py` 中，Phase 1 再合并提升。

---

## 审计维度五：缺口识别

### 5.1 重要遗漏内容

| 编号 | 缺口描述 | 影响 | 优先级 |
|------|----------|------|--------|
| G-01 | 无 Windows 原生路径说明 | PLAN1 仅说「支持 WSL」，未说明 Claude Desktop on Windows 如何配置 `.mcp.json` 的 WSL 内部路径 | 高 |
| G-02 | 无 MCP Server 优雅关闭设计 | stdio 传输中 SIGTERM/SIGINT 处理未定义，进程残留可能在重启后占用资源 | 中 |
| G-03 | 无日志轮转策略 | `AUTO_EDA_LOG_LEVEL` 有定义但日志文件位置、大小上限、轮转策略均未规定，长期运行存在磁盘耗尽风险 | 中 |
| G-04 | `.mcp.json` 使用相对路径 `cwd: "."` | 在不同 OS 工作目录启动时路径解析可能失效 | 中 |
| G-05 | Orchestrator Server 设计缺失 | DA1 §2.1 数据流图引用了 Orchestrator MCP Server，但 DA3/PLAN1 均未包含其 Phase 0 设计；跨工具工作流实现路径未定义 | 高 |
| G-06 | LLM 幻觉防护的测试验证方案缺失 | DA4 §1.2 定义了 `LLMSafetyGuard` 代码模式，但无测试设计；T7（最高风险项）的缓解有效性无法验证 | 高 |

---

### 5.2 DA4 风险缓解措施未映射至 PLAN1 执行任务

DA4 定义了多项缓解代码模式，但 PLAN1 的 40 天任务分解中无任何一天明确实现这些模式：

| DA4 缓解方案 | PLAN1 对应任务 | 状态 |
|-------------|--------------|------|
| §1.1.1 `KiCadApiMode` 版本探测 | — | 缺失 |
| §1.2 `LLMSafetyGuard` 幻觉防护层 | — | 缺失 |
| §1.4 长任务 Jobsets 超时包装 | — | 缺失 |
| §2 技术债务预防清单（6项） | — | 缺失 |

风险缓解措施存在于设计文档但未被纳入执行计划，实际开发中极可能被推迟至 Phase 1。

**修复建议**: PLAN1 Week 5-6 增加「实现 DA4 §1.1 KiCad 版本探测适配器」任务（1天）；
Week 3-4 增加「实现 DA4 §1.2 基础幻觉防护层骨架」任务（0.5天）。

---

## 审计总结

### 问题汇总表

| 编号 | 问题描述 | 严重度 | 所在文档 | 修复优先级 |
|------|----------|--------|----------|------------|
| S-01 | `auto_eda/base/` vs `auto_eda/core/` 命名冲突 | 严重 | DA1 vs DA3/PLAN1/PLAN6 | P0 — Day 1 前 |
| S-02 | `ProgressReporter._emit` 空实现，无可行方案 | 严重 | DA1 §1.2.3 | P0 — Week 3 前 |
| W-01 | Yosys Tool 数量规格不一致（5 vs 10） | 警告 | DA3 vs PLAN1 | P1 |
| W-02 | MCP SDK 版本上界约束缺失 | 警告 | DA3/PLAN6 | P1 |
| W-03 | KiCad 版本与 CI 环境不对齐 | 警告 | PLAN6 vs PLAN1 | P1 |
| W-04 | Python 3.13 支持声明不一致 | 警告 | DA3 vs PLAN1 | P2 |
| W-05 | `AsyncIterator` 冗余 import | 警告 | DA1 §1.2.3 | P2 |
| W-06 | DA4 缓解措施未映射至 PLAN1 任务日 | 警告 | DA4 vs PLAN1 | P1 |
| R-01 | Pyosys 双路径增加 Phase 0 维护成本 | 建议 | PLAN1 §3.3 | P2 |
| R-02 | Phase 0 `base/models.py` 包含 Phase 1 域模型 | 建议 | DA1 §2.2 | P2 |
| R-03 | KiCad 阶段缓冲时间不足，建议重排周次 | 建议 | PLAN1 Week 5-6 | P1 |

---

### 总体评分: 6.5 / 10

| 维度 | 得分 | 满分 | 说明 |
|------|------|------|------|
| 技术决策一致性 | 5.5 | 10 | 包路径命名冲突是严重系统性问题（-3分）；其余 5 项警告各 -0.3 |
| 实现可行性 | 7.0 | 10 | 工作量估算整体合理；KiCad 阶段密度偏高，Verilog Utils 偏松 |
| 架构完整性 | 7.0 | 10 | 错误处理链路完整；ProgressReporter 空实现是关键架构缺口 |
| 技术债务风险 | 6.0 | 10 | 主要债务已识别；Pyosys 双路径和跨域模型耦合将造成较高重构成本 |
| 缺口识别 | 6.0 | 10 | G-01/G-05/G-06 三个高优缺口（Windows 配置、Orchestrator、幻觉防护测试）将影响实际可用性 |

**结论**: 方案设计质量在同类开源项目规划中属中上水平，代码示例具有直接参考价值。
两项严重问题（S-01 包路径冲突、S-02 ProgressReporter 空实现）必须在开发启动前修复，
否则 Day 1 即产生阻塞性错误。其余警告建议在对应里程碑前完成修订。
KiCad 阶段（Week 5-6）建议增加 2 天缓冲或重排周次，以应对 v10 RC2 API 不稳定性风险。

---

*审计报告结束*
