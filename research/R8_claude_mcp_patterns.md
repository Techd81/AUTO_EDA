# R8: Claude Code + MCP 深度集成模式研究报告

> 研究日期: 2026-03-14
> 研究方法: 使用 grok-search MCP 工具进行多轮深度搜索
> 覆盖主题: 6大领域, 12+次深度搜索

---

## 目录

1. [Claude Code MCP 使用模式](#1-claude-code-mcp-使用模式)
2. [优秀 MCP Server 案例分析](#2-优秀-mcp-server-案例分析)
3. [复杂工作流 MCP 设计](#3-复杂工作流-mcp-设计)
4. [MCP 工具定义最佳实践](#4-mcp-工具定义最佳实践)
5. [MCP 与 GUI 应用集成](#5-mcp-与-gui-应用集成)
6. [MCP Server 测试和调试](#6-mcp-server-测试和调试)
7. [关键设计模式总结](#7-关键设计模式总结)
8. [对 AUTO_EDA MCP Server 设计的启示](#8-对-auto_eda-mcp-server-设计的启示)

---

## 1. Claude Code MCP 使用模式

### 1.1 Claude Code 概述

Claude Code 是 Anthropic 推出的终端 AI 编码助手（CLI），运行在本地项目目录中，拥有对文件系统的完整访问权限。通过 MCP（Model Context Protocol），Claude Code 从"单纯的编码工具"升级为可操控外部工具的完整 Agent。

### 1.2 MCP 协议核心概念

**MCP（Model Context Protocol）** 是 Anthropic 于 2024 年 11 月推出的开源标准，类似于"AI 的 USB-C 接口"：

```
┌─────────────────┐     JSON-RPC      ┌─────────────────┐
│   MCP Client    │ ◄──(stdio/HTTP)──►│   MCP Server    │
│  (Claude Code)  │                    │  (外部工具)      │
└─────────────────┘                    └─────────────────┘
```

**三大核心原语（Primitives）：**
- **Tools（工具）**: 可执行函数，AI 可调用（如 `click`, `screenshot`, `query_database`）
- **Resources（资源）**: 只读上下文数据，AI 可查询（如文件列表、数据库 schema）
- **Prompts（提示模板）**: 可复用的提示词模板

**实验性原语：**
- **Tasks（任务）**: 用于长时间运行的异步操作，支持状态追踪和延迟结果

### 1.3 Claude Code 如何发现和调用 MCP 工具

**自动发现机制：**
1. 启动时通过 `tools/list` 请求获取所有已注册 MCP Server 的工具列表
2. 工具 Schema（JSON Schema）被加载到上下文窗口
3. Claude 根据用户意图智能选择合适工具
4. 2026 年推出 **Tool Search** 功能：按需加载工具，节省高达 85% token

**调用流程：**
```
用户自然语言 → Claude 推理选择工具 → 生成 JSON-RPC 调用 → MCP Server 执行 → 返回结果 → Claude 解释结果
```

### 1.4 配置方式

**方式一：CLI 命令（推荐）**
```bash
# HTTP 远程服务器
claude mcp add notion --transport http https://mcp.notion.com/mcp

# stdio 本地服务器
claude mcp add my-tool --type stdio --command node /path/to/tool.js

# 管理命令
claude mcp list          # 列出所有服务器
claude mcp remove <name> # 移除服务器
```

**方式二：.mcp.json 配置文件（项目级，Git 友好）**

文件位置：项目根目录 `./.mcp.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"],
      "env": { "ALLOWED_PATHS": "/path1,/path2" }
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    },
    "postgres": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-postgres"],
      "env": { "DATABASE_URL": "${DB_URL}" }
    }
  }
}
```

**三种配置作用域：**

| 作用域 | 文件位置 | 用途 |
|--------|---------|------|
| Project | `./.mcp.json` | 团队共享，Git 版本控制 |
| User | `~/.claude.json` | 个人跨项目配置 |
| Local | `.claude/settings.json` | 本地特殊配置 |

### 1.5 权限模型和安全沙箱

- **用户确认门控**: 写入操作默认需要用户确认
- **环境变量引用**: 敏感信息通过 `${VAR}` 注入，不硬编码
- **服务器信任**: 只添加受信任的 MCP Server，防止 prompt injection
- **传输安全**: HTTP 传输支持 token 认证和 CORS 限制

### 1.6 传输协议类型

| 传输类型 | 适用场景 | 特点 |
|----------|---------|------|
| **stdio** | 本地进程 | 最简单，通过标准输入/输出通信 |
| **HTTP** | 远程/云端 | 推荐，支持认证和网络传输 |
| **Streamable HTTP** | 高性能场景 | 支持流式传输，适合大数据量 |

---

## 2. 优秀 MCP Server 案例分析

### 2.1 Chrome DevTools MCP - 浏览器控制典范

**GitHub**: `ChromeDevTools/chrome-devtools-mcp`
**架构**: 三层适配器模式

```
┌──────────────────────┐
│    MCP Server 层     │  ← JSON-RPC 协议处理、会话管理
│  (@mcp/sdk, Node.js) │
├──────────────────────┤
│   Tool Adapter 层    │  ← 工具定义映射、状态管理(McpContext)
│  (defineTool factory)│
├──────────────────────┤
│   Chrome Runtime 层  │  ← Puppeteer/CDP 实际执行
│ (Chrome DevTools     │
│  Protocol)           │
└──────────────────────┘
```

**设计原则：**
- **Agent 无关性**: 工具设计不绑定特定 AI Agent
- **Token 优化**: 返回语义摘要（如"LCP 为 3.2s"）而非原始 JSON
- **渐进复杂度**: 高层默认 + 可选高级参数
- **自愈错误**: 每个错误包含上下文和修复建议
- **引用而非值传递**: 重资产返回文件路径/URI

**工具分类（~26 个工具）：**
- Input（输入）: click, fill, hover, type_text, press_key
- Navigation（导航）: navigate_page, new_page, select_page
- Performance（性能）: performance_start_trace, lighthouse_audit
- Network（网络）: list_network_requests, get_network_request
- Debugging（调试）: list_console_messages, evaluate_script
- Emulation（模拟）: emulate, resize_page

**连接模式：**
- Launch 模式（默认）: 启动隔离 Chrome 实例
- Attach 模式: 连接已有实例（`--browser-url`, `--autoConnect`）
- Slim 模式: 仅暴露 3 个核心工具（轻量级）

### 2.2 Pencil MCP - 设计工具集成典范

**核心理念**: Design-as-Code（设计即代码）

**架构模式：**
- **Sidecar 模式**: MCP Server 作为独立本地进程，与 IDE 隔离
- **Adapter 模式**: 将内部向量画布操作转换为标准 MCP 工具签名
- **Facade 模式**: 统一入口隐藏批量操作、截图渲染等复杂性

**核心文件格式 .pen：**
```json
{
  "pages": [{
    "frames": [{
      "nodes": [
        { "type": "frame", "layout": "vertical", "children": [...] },
        { "type": "text", "content": "Hello" },
        { "type": "ref", "ref": "ComponentId" }
      ]
    }]
  }],
  "variables": { ... },
  "themes": { ... }
}
```

**关键设计决策：**

| 决策 | 选择 | 理由 |
|------|------|------|
| 文件格式 | JSON (.pen) | Git 友好，可 diff/merge |
| 操作模式 | 批量操作 (batch_design) | 减少 RPC 轮次，提高效率 |
| 截图反馈 | get_screenshot 工具 | 让 AI "看到"设计结果，形成反馈循环 |
| 组件系统 | ref 引用 + 实例覆盖 | 支持设计系统和组件复用 |
| 布局检查 | snapshot_layout | 检测重叠、裁剪等布局问题 |

**工具列表：**

| 工具 | 功能 | 粒度 |
|------|------|------|
| `batch_design` | 批量 CRUD（Insert/Copy/Update/Replace/Move/Delete/Image） | 粗粒度复合 |
| `batch_get` | 批量读取节点和搜索 | 粗粒度复合 |
| `get_screenshot` | 截取节点截图 | 原子操作 |
| `get_editor_state` | 获取编辑器当前状态 | 原子操作 |
| `snapshot_layout` | 检查布局结构 | 原子操作 |
| `get_variables` / `set_variables` | 变量/主题管理 | 原子操作 |
| `get_guidelines` | 获取设计规范 | 辅助工具 |
| `get_style_guide` | 获取风格指南 | 辅助工具 |
| `find_empty_space_on_canvas` | 查找画布空白区域 | 辅助工具 |
| `export_nodes` | 导出为图片/PDF | 原子操作 |

### 2.3 GitHub MCP Server - 开发工作流典范

**GitHub**: `github/github-mcp-server`（27.9k stars, Go 语言）
**定位**: AI 驱动的 GitHub 完整操作

**核心能力：**
- 创建/管理 Issues、PRs
- 代码分析、安全扫描
- Actions 工作流监控
- 仓库管理和搜索
- 支持只读/锁定模式（安全控制）
- 动态工具发现（beta）

**关键设计：**
- 远程托管版本（零配置）+ 本地 Docker 部署
- OAuth/PAT 认证
- 工具粒度：面向工作流的中等粒度

### 2.4 Filesystem MCP Server - 基础能力典范

**GitHub**: `modelcontextprotocol/servers` (参考实现)

**工具设计：**
- `read_file` / `write_file` / `edit_file`: 文件读写
- `list_directory` / `search_files`: 目录浏览和搜索
- `get_file_info`: 文件元数据

**安全设计：**
- 路径白名单：只允许访问指定目录
- 权限控制：可限制为只读模式
- 路径验证：防止目录遍历攻击

---

## 3. 复杂工作流 MCP 设计

### 3.1 MCP 协议的有状态性

MCP 在协议层面是有状态的（通过初始化握手和能力协商），但单个工具调用通常是无状态的。复杂多步骤工作流需要显式的服务器端状态管理。

### 3.2 状态管理策略

```
┌─────────────────────────────────────────────────────┐
│                 状态管理层级                          │
├─────────────────────┬───────────────────────────────┤
│ 进程内存储           │ Python dict / TS Map          │
│ (Session State)     │ TTL清理 + LRU历史缓冲         │
├─────────────────────┼───────────────────────────────┤
│ 持久化存储           │ Redis (JWT/Session Key)       │
│ (Cross-Instance)    │ 加密 + TTL + 跨实例共享       │
├─────────────────────┼───────────────────────────────┤
│ 工作流引擎状态       │ Temporal / AWS Step Functions │
│ (Durable State)     │ 事件溯源 + 自动重试 + 检查点   │
└─────────────────────┴───────────────────────────────┘
```

**推荐分层方案：**

| 层级 | 技术 | 适用场景 |
|------|------|---------|
| L1 进程内 | dict/Map + TTL | 快速会话数据（用户偏好、最近查询） |
| L2 Redis | 加密 + Session Key | 跨实例持久会话、合规要求 |
| L3 工作流引擎 | Temporal.io / Step Functions | 持久多步骤工作流、故障恢复 |

### 3.3 多步骤操作设计模式

**模式一：Orchestrator 编排器模式**
```
用户请求 → Planner 创建 Plan (DAG) → Executor 执行
                                    ├→ Step 1 (并行)
                                    ├→ Step 2 (并行)
                                    └→ Step 3 (依赖 1,2)
```

优点：支持动态规划、并行执行、失败重试
实现：mcp-agent 库的 Orchestrator 模式

**模式二：YAML 声明式工作流**
```yaml
workflow:
  name: "data_pipeline"
  steps:
    - id: extract
      tool: read_database
      params: { query: "SELECT * FROM users" }
    - id: transform
      tool: process_data
      depends_on: [extract]
    - id: load
      tool: write_file
      depends_on: [transform]
```

实现：cyanheads/workflows-mcp-server

**模式三：Temporal 持久工作流**
```python
@workflow.defn
class DataPipeline:
    @workflow.run
    async def run(self, params):
        data = await workflow.execute_activity(extract, params)
        result = await workflow.execute_activity(transform, data)
        await workflow.execute_activity(load, result)
```

优点：自动重试、持久状态、故障恢复
适用：生产级长时间运行任务

### 3.4 实验性 Tasks 原语

MCP 协议的实验性 Tasks 功能直接支持：
- **状态轮询**: `tasks/status` 检查执行进度
- **延迟结果**: 异步操作完成后获取结果
- **执行追踪**: Task ID 关联完整执行历史

```json
{
  "name": "execute_complex_workflow",
  "inputSchema": {
    "type": "object",
    "properties": {
      "workflow_name": { "type": "string" },
      "input": { "type": "object" }
    }
  }
}
```

### 3.5 长时间运行任务处理

| 方案 | 实现 | 优缺点 |
|------|------|--------|
| 同步阻塞 | 工具直接等待完成 | 简单但阻塞会话 |
| Tasks + 轮询 | 返回 Task ID，客户端轮询 | 非阻塞，需要客户端支持 |
| Notifications | Server 推送进度通知 | 实时反馈，需双向通道 |
| 外部引擎 | Temporal/Step Functions | 最可靠，需额外基础设施 |

---

## 4. MCP 工具定义最佳实践

### 4.1 工具粒度选择

**核心结论：倾向粗粒度/工作流驱动的设计**

```
                    粒度光谱
  ◄──────────────────────────────────────►
  细粒度                              粗粒度
  (getProfile,                  (getCustomerContext
   getOrders,                    → 聚合 profile+
   getPayments)                    orders+payments)

  更灵活但                         更高效但
  LLM推理复杂                      灵活性较低
```

**对比分析：**

| 维度 | 细粒度 | 粗粒度 | 混合推荐 |
|------|--------|--------|---------|
| LLM 推理 | 多步规划，错误累积（1%/步累积） | 声明式调用，1-2 步 | 常见路径用粗，边缘用细 |
| 性能成本 | 高延迟、多轮 token | 低延迟、少 token | 限制 5-15 工具/server |
| 灵活性 | 高组合性 | 边缘情况受限 | 提供两级 |
| 安全性 | 精细权限控制 | 需额外 RBAC 层 | 认证层与工具粒度分离 |
| 开发维度 | 映射简单但长期脆弱 | 需更多服务器逻辑 | 自顶向下设计 |

**实践建议：**
- **自顶向下设计**: 从用户意图/工作流出发，而非从 API 端点映射
- **好的例子**: `track_order(email)` 内部聚合三个 API 调用
- **坏的例子**: 暴露 `get_user`, `get_order`, `get_shipping` 三个独立工具
- **工具数量**: 每个 MCP Server 5-15 个工具为宜
- **输出优化**: 返回摘要/分页，不返回巨大 JSON

### 4.2 参数设计原则

**inputSchema 标准模板：**
```json
{
  "type": "object",
  "properties": {
    "parameterName": {
      "type": "string",
      "description": "清晰说明 + 示例，如：'城市名称或邮编 如 Beijing 100000'",
      "enum": ["option1", "option2"],
      "format": "email"
    }
  },
  "required": ["parameterName"],
  "additionalProperties": false
}
```

**核心规则：**

| 规则 | 说明 | 示例 |
|------|------|------|
| 类型明确 | 每个属性指定 type | `"type": "string"` |
| 描述详尽 | description 包含用途+示例 | `"城市名或坐标，如 Beijing"` |
| 枚举限制 | 有限选项用 enum | `"enum": ["celsius", "fahrenheit"]` |
| 格式约束 | 使用 format、pattern、min/max | `"format": "date-time"` |
| 必填标记 | required 数组声明 | `"required": ["location"]` |
| 严格验证 | additionalProperties: false | 拒绝未声明字段 |
| 零参数 | `{"type":"object","additionalProperties":false}` | 不接受任何输入 |

**JSON Schema 版本**: 默认 Draft 2020-12

### 4.3 工具命名规范

```
动词 + 资源名
├── list_users        (列表)
├── get_user_by_id    (获取)
├── create_order      (创建)
├── update_settings   (更新)
├── delete_file       (删除)
└── search_documents  (搜索)
```

**命名要求：**
- 唯一性：同一 Server 内不重复
- 动作导向：以动词开头
- 无空格：使用 snake_case 或 camelCase
- 描述性：名称能反映功能

### 4.4 返回值格式优化

**Token 优化策略：**

| 策略 | 做法 | 效果 |
|------|------|------|
| 语义摘要 | 返回 "LCP 为 3.2s" 而非原始 trace 数据 | 节省 90%+ token |
| 引用而非值 | 返回文件路径/URI 而非内容 | 避免上下文溢出 |
| 分页返回 | 大列表分页，返回 `{items, hasMore, nextPage}` | 控制单次数据量 |
| 格式选择 | 返回 Markdown/CSV 而非 raw JSON | LLM 更易理解 |
| 错误上下文 | 错误含修复建议 `{isError, message, suggestion}` | 减少重试次数 |

### 4.5 错误信息设计

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Failed to read file: Permission denied for /etc/shadow\nSuggestion: Check file permissions or use an allowed path."
    }
  ]
}
```

**错误设计原则：**
- 始终包含 `isError: true` 标识
- 提供可操作的修复建议
- 包含足够上下文（文件路径、参数值等）
- 不暴露内部实现细节

---

## 5. MCP 与 GUI 应用集成

### 5.1 GUI 自动化 MCP Server

**主流方案：**

| 方案 | 技术 | 平台 | 特点 |
|------|------|------|------|
| Windows-MCP | UI Automation API | Windows | 语义化元素控制，最准确 |
| PyAutoGUI MCP | PyAutoGUI | 跨平台 | 像素级控制，截图+OCR |
| Playwright MCP | Playwright | Web | 浏览器自动化，支持视觉 diff |
| RobotJS MCP | RobotJS | 跨平台 | 屏幕捕获 + 键鼠控制 |
| kwin-mcp | KDE Accessibility | Linux | KDE 桌面完整控制 |

### 5.2 GUI 自动化 vs API 调用对比

| 维度 | GUI 自动化 | API 调用 |
|------|-----------|---------|
| 适用范围 | 任何有界面的应用 | 需要程序提供 API |
| 可靠性 | 依赖 UI 稳定性 | 高度可靠 |
| 速度 | 较慢（需等待渲染） | 快速 |
| 维护性 | UI 变化可能导致失败 | API 稳定则不受影响 |
| 开发成本 | 低（不需要目标应用修改） | 需要 API 文档和集成 |
| 最佳场景 | 遗留系统、无 API 应用 | 现代应用、自有系统 |

**结论：优先 API，GUI 自动化作为补充**

### 5.3 截图和视觉反馈机制

**视觉反馈循环（Visual Feedback Loop）模式：**

```
          ┌──────────────────────────┐
          │    1. 截图 (screenshot)   │
          │    捕获当前 UI 状态       │
          └──────────┬───────────────┘
                     │
          ┌──────────▼───────────────┐
          │    2. 分析 (analyze)      │
          │    视觉模型识别问题       │
          └──────────┬───────────────┘
                     │
          ┌──────────▼───────────────┐
          │    3. 行动 (act)          │
          │    修改代码/注入 CSS      │
          └──────────┬───────────────┘
                     │
          ┌──────────▼───────────────┐
          │    4. 验证 (verify)       │
          │    重新截图 + 视觉 diff   │
          └──────────┬───────────────┘
                     │
                ┌────▼────┐
                │ 达标？   ├── 否 → 回到 Step 1
                └────┬────┘
                     │ 是
                  完成 ✓
```

**截图 MCP Server 架构（Strategy + Factory + Command 模式）：**

```
┌─────────────────────────────────┐
│  MCP Tool Layer (Command)       │
│  screenshot_capture_full        │
│  screenshot_capture_window      │
│  screenshot_capture_region      │
│  screenshot_list_displays       │
│  screenshot_list_windows        │
├─────────────────────────────────┤
│  Processing Layer               │
│  格式转换 (PNG/JPEG/WebP)      │
│  PII 遮蔽 (OCR + 正则)         │
│  质量调整                       │
├─────────────────────────────────┤
│  Capture Engine Layer (Strategy)│
│  macOS: screencapture           │
│  Windows: .NET/PowerShell       │
│  Linux: grim/maim               │
│  Web: Playwright/Puppeteer      │
└─────────────────────────────────┘
```

**关键设计要点：**
- 返回 base64 编码图片 + 元数据（尺寸、DPI 等）
- PII 自动遮蔽（通过 OCR 检测敏感信息）
- 速率限制防止过度截图
- 支持全屏、窗口、区域三种模式

---

## 6. MCP Server 测试和调试

### 6.1 分层测试策略

```
┌─────────────────────────────────────────────┐
│ Layer 4: AI 模拟端到端测试 (mcpjam)          │
│ 真实 AI Agent 调用工具的会话流测试            │
├─────────────────────────────────────────────┤
│ Layer 3: 交互式 RPC 测试 (MCP Inspector)     │
│ 实时可视化工具调用、参数检查、日志监控        │
├─────────────────────────────────────────────┤
│ Layer 2: 集成/协议测试 (SDK)                 │
│ JSON-RPC 消息流、tools/list 验证、传输层     │
├─────────────────────────────────────────────┤
│ Layer 1: 单元测试 (pytest/Jest)              │
│ 核心工具逻辑、参数验证、错误处理             │
└─────────────────────────────────────────────┘
```

### 6.2 Layer 1: 单元测试

**目标**: 80%+ 覆盖率，包含 LLM 特有边缘情况

```python
# Python 示例
import pytest
from your_mcp_server.tools import search_files

def test_search_files_basic():
    result = search_files(query="test", path="/tmp")
    assert isinstance(result, list)
    assert len(result) > 0

def test_search_files_sanitizes_dangerous_input():
    # LLM 可能生成危险输入
    result = search_files(query="*.js && rm -rf /", path="/tmp")
    assert result == []  # 或抛出安全异常
```

### 6.3 Layer 2: 集成测试

```typescript
// TypeScript 示例
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

test("tools/list returns valid schema", async () => {
  const client = new Client({ name: "test", version: "1.0" });
  await client.connect(
    new StdioClientTransport({ command: "node", args: ["dist/index.js"] })
  );
  const response = await client.request({ method: "tools/list" });
  expect(response.tools).toBeDefined();
  expect(response.tools.length).toBeGreaterThan(0);
});
```

### 6.4 Layer 3: MCP Inspector

**MCP Inspector** 是官方交互式开发者工具（React UI + Node.js 代理）。

**使用步骤（2025/2026 安全更新版）：**
```bash
# 1. 启动 MCP Server
uvicorn your_server:app --port 8000

# 2. 启动 Inspector
npx @modelcontextprotocol/inspector@latest
# 自动打开 http://localhost:6274 (随机认证 token)

# 3. 连接服务器
# 选择传输方式 (推荐 Streamable HTTP)
# 输入 Server URL: http://127.0.0.1:8000/mcp

# 4. 测试
# - Tools 标签: 列出 Schema → 输入参数 → 执行 → 查看结果
# - Resources: 验证列表和元数据
# - Notifications: 实时错误日志
```

**Inspector 功能：**
- 实时 JSON-RPC 消息日志
- 工具 Schema 可视化
- 参数输入和执行测试
- 资源和提示预览
- 通知监控

**安全注意**: 2025 年 3 月修复了 CVE-2025-49596（Inspector 需认证 token）

### 6.5 Layer 4: AI 模拟测试

```bash
# mcpjam Inspector - 模拟真实 AI Agent
npx @mcpjam/inspector
# 支持 Claude/GPT/Ollama 作为测试 Agent
```

### 6.6 CI/CD 集成

```yaml
# .github/workflows/mcp-test.yml
steps:
  - name: Unit Tests
    run: pytest --cov=your_mcp_server

  - name: Integration Tests
    run: npm test:integration

  - name: Contract Tests
    run: npx @haakco/mcp-testing-framework

  - name: Inspector Scripted Tests (可选)
    run: npx @modelcontextprotocol/inspector --headless --test-script ci-test.js
```

---

## 7. 关键设计模式总结

### 7.1 MCP Server 架构模式

| 模式 | 说明 | 适用场景 | 典型案例 |
|------|------|---------|---------|
| **Sidecar** | Server 作为独立进程与 Host 隔离 | 所有 MCP Server | Pencil MCP |
| **Adapter** | 将内部操作转换为标准 MCP 接口 | 已有系统集成 | Chrome DevTools MCP |
| **Facade** | 统一入口隐藏内部复杂性 | 复合操作 | 批量 API |
| **Factory** | 统一工具注册和创建 | 工具数量多 | Chrome DevTools defineTool |
| **Strategy** | 运行时选择具体实现 | 跨平台 | 截图引擎选择 |
| **Orchestrator** | 动态规划和执行多步骤 | 复杂工作流 | mcp-agent |
| **Toolhost** | 动态工具聚合和路由 | 多 Server 聚合 | MetaMCP |

### 7.2 工具设计模式

| 模式 | 特点 | 示例 |
|------|------|------|
| **原子工具** | 单一操作，高组合性 | click, screenshot, read_file |
| **批量工具** | 多操作聚合，减少 RPC | batch_design (25 ops/call) |
| **工作流工具** | 封装完整业务流程 | track_order(email) |
| **查询工具** | 灵活参数，返回结构化数据 | search_files(pattern, path) |
| **辅助工具** | 提供上下文/指南 | get_guidelines, get_editor_state |

### 7.3 反馈循环模式

```
Visual Feedback Loop:
  截图 → 分析 → 行动 → 验证 → 循环

Progressive Refinement:
  粗框架 → 填充内容 → 精细调整 → 验证

Observe-Act-Verify:
  观察状态 → 执行操作 → 验证结果 → 下一步
```

---

## 8. 对 AUTO_EDA MCP Server 设计的启示

### 8.1 架构建议

基于本次研究，AUTO_EDA MCP Server 应采用以下架构：

```
┌──────────────────────────────────────────┐
│           Claude Code (MCP Client)        │
├──────────────────────────────────────────┤
│           MCP Protocol Layer             │
│  (JSON-RPC over stdio/HTTP)              │
├──────────────────────────────────────────┤
│         EDA Tool Adapter Layer           │
│  ┌──────────┬──────────┬──────────┐     │
│  │ Schematic │  Layout  │ Simulate │     │
│  │  Tools    │  Tools   │  Tools   │     │
│  └──────────┴──────────┴──────────┘     │
├──────────────────────────────────────────┤
│         EDA Engine Layer                 │
│  ┌──────────┬──────────┬──────────┐     │
│  │  KiCad   │   ngspice │  Custom  │     │
│  │  Python  │   CLI    │  Engine  │     │
│  └──────────┴──────────┴──────────┘     │
└──────────────────────────────────────────┘
```

### 8.2 工具粒度建议

参照 Pencil MCP 和 Chrome DevTools MCP 的经验：

| 工具类别 | 粒度 | 示例 |
|---------|------|------|
| 核心操作 | 粗粒度批量 | `batch_schematic_edit` (批量原理图编辑) |
| 查询分析 | 中等粒度 | `analyze_circuit` (电路分析) |
| 状态检查 | 原子粒度 | `get_design_state`, `get_screenshot` |
| 仿真控制 | 工作流粒度 | `run_simulation` (完整仿真流程) |
| 导出操作 | 原子粒度 | `export_gerber`, `export_bom` |

### 8.3 视觉反馈机制

参照 Pencil 的 `get_screenshot` 和 Chrome DevTools 的 `take_screenshot`：

- 提供 `get_schematic_screenshot` 工具
- 提供 `get_layout_screenshot` 工具
- 支持局部区域截图（特定组件/网络）
- 返回 base64 + 元数据（尺寸、缩放级别等）
- 形成 "设计 → 截图 → AI 分析 → 修改 → 验证" 闭环

### 8.4 文件格式策略

参照 Pencil 的 .pen JSON 文件格式：

- EDA 文件使用标准开放格式（KiCad .kicad_sch / .kicad_pcb）
- 通过 MCP Server 提供结构化读写接口
- 支持增量修改（参照 batch_design 的 Insert/Update/Delete 操作）
- 文件 Git 友好，支持 diff/merge

### 8.5 配置和部署建议

**.mcp.json 示例：**
```json
{
  "mcpServers": {
    "auto-eda": {
      "command": "python",
      "args": ["-m", "auto_eda.mcp_server"],
      "env": {
        "EDA_PROJECT_PATH": "${PROJECT_ROOT}",
        "KICAD_PATH": "${KICAD_INSTALL_PATH}"
      }
    }
  }
}
```

### 8.6 测试策略建议

- **L1**: 对 EDA 解析/生成逻辑进行单元测试
- **L2**: 使用 MCP SDK 进行协议集成测试
- **L3**: 使用 MCP Inspector 进行交互式调试
- **L4**: 使用真实 Claude Code 会话进行端到端验证

---

## 参考资源

### 官方文档
- MCP 协议规范: https://modelcontextprotocol.io/specification/draft
- MCP 服务器概念: https://modelcontextprotocol.io/docs/learn/server-concepts
- MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector
- Claude Code MCP 文档: https://code.claude.com/docs/en/mcp

### 参考实现
- 官方参考服务器: https://github.com/modelcontextprotocol/servers
- GitHub MCP Server: https://github.com/github/github-mcp-server
- Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp
- Awesome MCP Servers: https://github.com/punkpeye/awesome-mcp-servers

### MCP SDK
- TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- Python SDK: https://github.com/modelcontextprotocol/python-sdk

### 工作流相关
- Temporal MCP: https://learn.temporal.io/tutorials/ai/building-mcp-tools-with-temporal/
- Workflows MCP Server: https://github.com/cyanheads/workflows-mcp-server
- mcp-agent Orchestrator: https://docs.mcp-agent.com/workflows/orchestrator

### 设计和测试
- Pencil.dev: https://www.pencil.dev/
- OpenPencil: https://github.com/ZSeven-W/openpencil
- MCP Testing Guide: https://agnost.ai/blog/testing-mcp-servers-complete-guide
- Block 设计指南: https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers

### 社区资源
- Phil Schmid MCP Best Practices: https://www.philschmid.de/mcp-best-practices
- Datadog MCP 经验: https://www.datadoghq.com/blog/engineering/mcp-server-agent-tools/
- a16z MCP Deep Dive: https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling/
