# R5: MCP协议架构与高质量MCP Server开发最佳实践

> 研究时间: 2026-03-14
> 研究员: researcher-5-mcp-architecture
> 状态: 完成

---

## 目录

1. [MCP协议规范](#1-mcp协议规范)
2. [MCP Server核心概念](#2-mcp-server核心概念)
3. [MCP Server开发SDK](#3-mcp-server开发sdk)
4. [高质量MCP Server设计模式](#4-高质量mcp-server设计模式)
5. [MCP Server性能优化](#5-mcp-server性能优化)
6. [MCP与Claude Code集成](#6-mcp与claude-code集成)
7. [总结与建议](#7-总结与建议)

---

## 1. MCP协议规范

### 1.1 什么是MCP

**MCP (Model Context Protocol)** 是由Anthropic于2024年11月推出的开放协议标准，用于标准化LLM应用（客户端/宿主）如何发现、请求和接收来自外部MCP服务器的上下文数据、工具、提示和资源。

**核心类比**: MCP就像"AI的USB-C"——一个通用接口，替代了数十个自定义适配器。

### 1.2 协议版本与演进历史

| 版本 | 发布日期 | 关键变更 |
|------|----------|----------|
| `2024-11-05` | 2024年11月 | 初始发布（Anthropic） |
| `2025-03-26` | 2025年3月 | 早期生产强化 |
| `2025-06-18` | 2025年6月 | 重大安全更新 + Streamable HTTP引入 |
| **`2025-11-25`** | 2025年11月 | **当前最新稳定版** |

- 版本字符串格式: `YYYY-MM-DD`
- 版本在初始化握手期间协商
- 2026年路线图: 传输层扩展性和会话改进（Linux Foundation治理下）
- 截至2026年3月14日，尚无新版本发布

### 1.3 协议基础架构

MCP基于 **JSON-RPC 2.0** 客户端-服务器协议:

```
┌─────────────────────────────────────────────┐
│                  MCP Host                    │
│            (AI应用: Claude, VS Code等)        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ MCP      │  │ MCP      │  │ MCP      │  │
│  │ Client 1 │  │ Client 2 │  │ Client 3 │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼──────────────┼──────────────┼────────┘
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ MCP     │   │ MCP     │   │ MCP     │
   │ Server  │   │ Server  │   │ Server  │
   │   A     │   │   B     │   │   C     │
   └─────────┘   └─────────┘   └─────────┘
```

**三层参与者**:
- **MCP Host**: AI应用（如Claude Desktop, VS Code），管理所有客户端
- **MCP Client**: 每个服务器对应一个，在Host中创建，维护专用连接
- **MCP Server**: 暴露工具/资源/提示等能力的程序

**两个协议层**:
1. **数据层 (Data Layer)**: JSON-RPC 2.0消息，处理生命周期（初始化、能力协商）、原语和通知
2. **传输层 (Transport Layer)**: 承载消息的物理通道

### 1.4 传输层详解

所有MCP消息均为UTF-8编码的JSON-RPC 2.0格式。规范定义了两种标准传输方式，客户端**应当(SHOULD)**同时支持。

#### 1.4.1 stdio传输（本地/子进程）

```
Client ──stdin──> Server
Client <──stdout── Server
         (stderr用于日志)
```

- 客户端将服务器作为子进程启动
- 消息通过stdin（客户端→服务器）和stdout（服务器→客户端）传输
- 每个JSON-RPC消息为单行，以换行符(`\n`)结束
- 消息中**不得(MUST NOT)**包含嵌入的换行符
- 服务器**可以(MAY)**通过stderr输出日志
- 零网络开销，适用于本地工具、IDE插件、桌面代理

#### 1.4.2 Streamable HTTP传输（远程/生产环境）

替代了2024-11-05版本中已弃用的HTTP+SSE传输。

**端点**: 单一HTTP路径（如 `https://example.com/mcp`），接受POST和GET。

**客户端→服务器 (POST)**:
- 每个JSON-RPC消息 = 一个HTTP POST
- 必需头部:
  - `Accept: application/json, text/event-stream`
  - `MCP-Protocol-Version: 2025-11-25`（初始化后强制）
- 服务器返回:
  - `Content-Type: application/json`（单个响应）
  - `Content-Type: text/event-stream`（SSE流，用于渐进结果/通知/服务器发起的请求）

**服务器→客户端 (GET/SSE)**:
- 客户端可通过GET打开长连接SSE流，接收未请求的消息
- 通过`retry:`字段和`Last-Event-ID`头部支持可恢复性

**会话管理（2025-11-25新增）**:
- 服务器在`initialize`结果中返回`MCP-Session-Id`头部
- 客户端**必须(MUST)**在后续所有请求中回传此头部
- 支持有状态远程服务器，同时保持REST友好

**安全要求（强制）**:
- 验证`Origin`头部以阻止DNS重绑定攻击
- 本地服务器**应当(SHOULD)**仅绑定到127.0.0.1
- 生产环境需适当认证（OAuth 2.0资源服务器模型）

**向后兼容**:
- 服务器可同时保留旧HTTP+SSE端点和新的Streamable HTTP端点
- 客户端通过Accept头部响应码检测版本

### 1.5 生命周期流程

```
Client                          Server
  │                                │
  │──── initialize (版本+能力) ────>│
  │                                │
  │<──── initialize result ────────│
  │      (支持的特性)               │
  │                                │
  │── notifications/initialized ──>│
  │                                │
  │──── */list (发现工具等) ───────>│
  │<──── 列表结果 ─────────────────│
  │                                │
  │──── */call (调用工具) ────────>│
  │<──── 调用结果 ─────────────────│
  │                                │
  │<── notifications (更新通知) ───│
  │                                │
```

### 1.6 关键规范链接

| 资源 | URL |
|------|-----|
| 完整规范 (2025-11-25) | https://modelcontextprotocol.io/specification/2025-11-25 |
| 传输层规范 | https://modelcontextprotocol.io/specification/2025-11-25/basic/transports |
| GitHub仓库 | https://github.com/modelcontextprotocol/modelcontextprotocol |
| 2026路线图 | https://modelcontextprotocol.io/development/roadmap |

---

## 2. MCP Server核心概念

MCP Server通过四个核心原语（Primitives）暴露能力:

### 2.1 Tools（工具）— "动词"

**定义**: 服务器暴露的可执行函数，LLM可以发现并调用以在外部世界执行操作。

**类比**: 工具就像智能手机上的App——AI决定"我需要天气数据"，服务器运行对应代码。

**协议操作**:
- 发现: `tools/list`（分页，包含JSON Schema输入定义）
- 调用: `tools/call`（名称 + 参数；返回text/image/audio或structuredContent）
- 变更通知: `notifications/tools/list_changed`

**JSON Schema示例**:
```json
{
  "name": "get_weather",
  "description": "获取当前天气信息",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": { "type": "string", "description": "城市名称" }
    },
    "required": ["location"]
  }
}
```

**关键特性**:
- 需要用户批准才能执行（安全设计）
- 支持structuredContent和outputSchema（2025-06-18+）
- 支持进度报告和取消

### 2.2 Resources（资源）— "名词"

**定义**: 服务器暴露的只读数据源（文件、数据库记录、API响应、图像），通过URI标识。

**类比**: 资源就像无限的图书馆书架——AI只借出需要的那本书，而不是下载整个图书馆。

**协议操作**:
- 列表: `resources/list`
- 读取: `resources/read`
- 模板: 支持动态URI（如 `file:///{path}`）
- 订阅: `notifications/resources/updated`（可选实时更新）

**使用场景**:
- 提供文件内容给LLM上下文
- 暴露数据库Schema信息
- 提供API文档
- 共享配置数据

### 2.3 Prompts（提示模板）— "剧本"

**定义**: 服务器提供的结构化消息模板，用于标准化LLM交互（如"代码审查"或"会议总结"工作流）。

**类比**: 提示就像菜谱卡——服务器给AI一套现成的烹饪指令，而不是让它每步都即兴发挥。

**协议操作**:
- 发现: `prompts/list`
- 获取: `prompts/get`

**结构**: 名称 + 可选参数 + 消息数组（user/assistant角色，支持text/image/audio/resource内容）

**使用场景**:
- 斜杠命令（/code-review, /summarize）
- 专业化系统提示
- 多步骤工作流模板

### 2.4 Sampling（采样）— "反向思考"

**定义**: 独特的"反向"功能——**服务器**可以请求**客户端**的LLM生成补全（文本/音频/图像），用于嵌套推理。

**类比**: 正常流程是AI向服务器请求数据。Sampling是服务器问AI"我下一步该做什么？"——非常适合复杂代理场景。

**工作流程**:
1. 服务器发送 `sampling/createMessage`（消息 + 模型偏好 + 系统提示）
2. 客户端审查（可能需要用户批准），从其LLM采样，返回结果
3. 启用服务器内部的代理循环

**关键约束**:
- 服务器不需要自己的API密钥
- 客户端控制模型选择和权限
- 支持人工审查（安全保障）

### 2.5 其他核心概念

| 概念 | 说明 |
|------|------|
| **Notifications** | 实时推送更新（无需轮询） |
| **Capabilities** | 双向在启动时声明支持的特性 |
| **Elicitation** | 服务器请求用户输入（人机交互） |
| **Roots** | 入口点目录（文件类服务器） |
| **Progress Reporting** | 长时间操作的进度报告 |

---

## 3. MCP Server开发SDK

### 3.1 官方SDK概览

| 维度 | TypeScript SDK | Python SDK |
|------|---------------|------------|
| **包名** | `@modelcontextprotocol/sdk` | `mcp` (PyPI) |
| **GitHub** | modelcontextprotocol/typescript-sdk | modelcontextprotocol/python-sdk |
| **文档** | https://ts.sdk.modelcontextprotocol.io | https://py.sdk.modelcontextprotocol.io |
| **级别** | Tier 1 (官方) | Tier 1 (官方) |
| **运行时** | Node.js / Bun / Deno | Python 3.10+ |
| **高级API** | McpServer | FastMCP |
| **Schema验证** | Zod | Type hints + Pydantic |
| **传输** | stdio, Streamable HTTP | stdio, Streamable HTTP |
| **认证** | OAuth 2.1 | OAuth 2.1 |
| **风格** | 显式注册 | 装饰器驱动 |

### 3.2 TypeScript SDK详解

#### 安装

```bash
# 完整SDK
npm install @modelcontextprotocol/sdk zod

# 仅服务器
npm install @modelcontextprotocol/server zod

# 仅客户端
npm install @modelcontextprotocol/client zod

# 可选HTTP中间件
npm install @modelcontextprotocol/node @modelcontextprotocol/express
```

> 注意: 主分支为v2预览版（2026 Q1稳定），v1为当前推荐稳定版。

#### 基础Server示例

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "demo-server",
  version: "1.0.0"
});

// 注册工具
server.registerTool(
  "add",
  {
    title: "Add Numbers",
    description: "将两个数字相加",
    inputSchema: z.object({
      a: z.number().describe("第一个数字"),
      b: z.number().describe("第二个数字")
    }),
    outputSchema: z.object({ result: z.number() })
  },
  async ({ a, b }) => ({
    content: [{ type: "text", text: `结果: ${a + b}` }],
    structuredContent: { result: a + b }
  })
);

// 注册资源
server.registerResource(
  "greeting",
  "greeting://hello",
  { title: "问候", mimeType: "text/plain" },
  async () => ({
    contents: [{
      uri: "greeting://hello",
      text: "Hello from MCP!"
    }]
  })
);

// 连接传输层
const transport = new StdioServerTransport();
await server.connect(transport);
```

#### Streamable HTTP传输

```typescript
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express from "express";

const app = express();
const transport = new NodeStreamableHTTPServerTransport({ ... });
// 使用 createMcpExpressApp() 集成
```

#### 基础Client示例

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const client = new Client({ name: "demo-client", version: "1.0.0" });
const transport = new StdioClientTransport({ command: "node", args: ["server.js"] });
await client.connect(transport);

// 使用
const tools = await client.listTools();
const result = await client.callTool({ name: "add", arguments: { a: 1, b: 2 } });
```

### 3.3 Python SDK详解

#### 安装

```bash
# 推荐使用uv
uv init mcp-demo && cd mcp-demo
uv venv && source .venv/bin/activate
uv add "mcp[cli]" httpx

# 或pip
pip install "mcp[cli]"
```

#### 基础Server示例（FastMCP）

```python
from mcp.server.fastmcp import FastMCP
import httpx
from typing import Any

mcp = FastMCP("weather-demo")

@mcp.tool()
async def get_alerts(state: str) -> str:
    """获取美国州的天气警报。

    Args:
        state: 两字母美国州代码（如 CA, NY）
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.gov/alerts?area={state}"
        )
        data = response.json()
        alerts = data.get("features", [])
        if not alerts:
            return f"{state} 无活跃警报"
        return "\n".join(
            f"- {a['properties']['headline']}" for a in alerts[:5]
        )

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """获取5天天气预报。"""
    # NWS API 逻辑
    return "晴天, 72°F"

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """个性化问候资源"""
    return f"你好, {name}!"

@mcp.prompt(title="代码审查")
def review_code(code: str) -> str:
    """生成代码审查提示"""
    return f"请审查以下代码:\n{code}"

if __name__ == "__main__":
    mcp.run(transport="stdio")  # 或 "streamable-http"
```

#### Python Client示例

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

async def main():
    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(
            stdio_client(server_params)
        )
        session = await stack.enter_async_context(
            ClientSession(read, write)
        )
        await session.initialize()

        tools = await session.list_tools()
        result = await session.call_tool("get_alerts", {"state": "CA"})
```

### 3.4 SDK特性对比

| 特性 | TypeScript | Python |
|------|-----------|--------|
| Schema定义 | Zod（显式） | Type hints（自动推断） |
| 上手难度 | 中等 | 简单（装饰器语法） |
| 异步支持 | async/await | asyncio |
| 类型安全 | 编译时检查 | 运行时 + Pydantic |
| Web集成 | Express/Hono原生 | 需额外框架 |
| 测试工具 | MCP Inspector | MCP Inspector + `mcp dev` |
| 生产部署 | Docker + Node | Docker + uv/pip |
| 社区生态 | 丰富（Node生态） | 丰富（Python AI生态） |

### 3.5 测试工具

```bash
# MCP Inspector（通用，可视化测试）
npx @modelcontextprotocol/inspector

# Python开发模式
uv run mcp dev server.py

# Claude Desktop配置测试
# 编辑 ~/Library/Application Support/Claude/claude_desktop_config.json
```

---

## 4. 高质量MCP Server设计模式

### 4.1 架构设计原则

#### 原则1: 单一职责 (Single Responsibility)

每个MCP服务器处理**一个**明确的领域:
- 专注的GitHub服务器，而不是混合一切的巨型服务器
- 隔离故障、简化扩展、改善团队所有权

```
❌ 错误: mega-server (GitHub + Slack + DB + 文件系统)
✅ 正确: github-server, slack-server, db-server, fs-server
```

#### 原则2: 纵深防御 (Defense-in-Depth)

分层安全:
- 网络隔离（绑定127.0.0.1）
- JWT认证
- 基于能力的ACL
- 输入验证
- 输出净化
- 全面审计日志

#### 原则3: 故障安全 (Fail-Safe Design)

- 断路器模式 (Circuit Breaker)
- 缓存降级
- 速率限制
- 向代理返回优雅的降级消息:
  - `"服务暂时不可用——请在60秒后重试"` 而不是崩溃

### 4.2 工具设计模式

#### 模式1: 面向结果（非面向操作）

```
❌ 操作导向 (Bad):
  get_user(email) → list_orders(user_id) → get_status(order_id)

✅ 结果导向 (Good):
  track_latest_order(email) → 完整的订单追踪信息
```

**原则**: 在服务器端完成编排，让AI只需一次调用。减少多步骤编排的token消耗和上下文膨胀。

#### 模式2: 扁平化参数

```python
# ❌ 嵌套字典（AI容易产生幻觉）
@mcp.tool()
async def create_issue(config: dict):
    """config: {repo: str, title: str, body: str, labels: [str]}"""
    ...

# ✅ 简单原语类型（清晰明确）
@mcp.tool()
async def create_issue(
    repo: str,
    title: str,
    body: str = "",
    labels: str = ""  # 逗号分隔
) -> str:
    """创建GitHub Issue"""
    ...
```

#### 模式3: 精简策展 (Curate Ruthlessly)

- 每个服务器 **5-15个工具** 为最佳
- 管理"工具预算"（Tool Budget）
- 超过15个工具时考虑拆分服务器
- 使用分页处理大型结果集（`has_more` + `total_count`）

#### 模式4: 可发现命名

```
# 命名规范: service_action_resource
github_create_issue
github_list_repos
slack_send_message
db_query_table
```

#### 模式5: 工具宿主模式 (Toolhost Pattern)

大型工具列表的中央调度器 + 中间件:
- 减少多工具存在时的上下文负担
- 支持路由、速率限制、日志等中间件

### 4.3 错误处理最佳实践

```python
# 结构化错误分类
class McpErrorCategory:
    CLIENT_ERROR = "client_error"      # 用户输入问题
    SERVER_ERROR = "server_error"      # 服务器内部问题
    EXTERNAL_ERROR = "external_error"  # 外部API问题

@mcp.tool()
async def query_database(sql: str) -> str:
    """执行SQL查询"""
    try:
        result = await db.execute(sql)
        return format_result(result)
    except SyntaxError as e:
        # 指导性错误消息，帮助LLM自我修正
        return f"SQL语法错误: {e}。请检查表名和列名是否正确。可用的表: users, orders, products"
    except ConnectionError:
        return "数据库连接暂时不可用。请稍后重试。"
    except Exception as e:
        return f"服务器内部错误: {type(e).__name__}。请简化查询后重试。"
```

### 4.4 安全最佳实践（生产环境必须）

| 要求 | 说明 |
|------|------|
| 认证 | HTTP服务器使用OAuth 2.1，不使用会话认证 |
| 会话ID | 安全的非确定性会话ID，绑定用户数据 |
| 最小权限 | 仅授予必需的权限范围 |
| SSRF防护 | 阻止私有IP访问 |
| 混淆代理防护 | 实施每客户端同意注册表 |
| CSRF防护 | 使用单次加密随机state参数 |
| 重定向URI | 精确匹配验证 |
| 输入验证 | 所有请求服务器端验证 |
| 沙箱 | 本地服务器沙箱隔离 |
| DNS重绑定 | 验证Origin头部 |

### 4.5 JSON Schema工具定义最佳实践

```json
{
  "name": "search_documents",
  "description": "在文档库中搜索相关文档。返回匹配的文档标题和摘要。支持全文搜索和模糊匹配。",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "搜索关键词或短语"
      },
      "limit": {
        "type": "integer",
        "description": "返回结果数量上限",
        "default": 10,
        "minimum": 1,
        "maximum": 100
      },
      "category": {
        "type": "string",
        "enum": ["technical", "business", "legal"],
        "description": "文档类别筛选"
      }
    },
    "required": ["query"]
  }
}
```

**最佳实践要点**:
1. description要详尽——这是LLM的主要决策依据
2. 使用enum约束有限选项
3. 提供合理的default值
4. 设置minimum/maximum边界
5. 每个属性都要有description
6. required只包含真正必需的参数

---

## 5. MCP Server性能优化

### 5.1 长时间运行操作处理

#### SEP-1686 Task原语: "立即调用，稍后获取"模式

**问题**: 传统同步MCP服务器中，长时间操作（秒到小时级别）会占住客户端连接、耗尽超时、阻止其他请求处理。

**解决方案**: 首个类任务(task)原语

```
工作流程:
1. 客户端发送 tools/call（带 _meta.task 标志）
2. 服务器立即返回 taskId
3. 工作在后台排队执行
4. 服务器通过 notifications/tasks/created 通知客户端
5. 客户端轮询 tasks/get 获取进度
6. 客户端通过 tasks/result 获取最终结果
```

**类比**: 在繁忙餐厅点餐。不是站在柜台等45分钟（阻塞所有人），而是立即获得一个号码牌，坐下来，偶尔查看状态屏，准备好时取餐。

#### 实现示例

```python
from fastmcp import FastMCP
import asyncio
import uuid

mcp = FastMCP("OptimizedServer")

@mcp.tool()
async def analyze_large_dataset(dataset_id: str) -> dict:
    """分析大型数据集（可能需要几分钟）"""
    task_id = f"task_{uuid.uuid4()}"

    # 立即返回任务ID
    asyncio.create_task(
        _background_analysis(dataset_id, task_id)
    )

    return {"taskId": task_id, "status": "submitted"}

async def _background_analysis(dataset_id: str, task_id: str):
    """后台执行实际分析"""
    for i in range(100):
        # 报告进度
        await mcp.notify("tasks/progress", {
            "taskId": task_id,
            "completed": i,
            "total": 100
        })
        await asyncio.sleep(0.1)

    # 完成通知
    await mcp.notify("tasks/completed", {
        "taskId": task_id,
        "result": {"summary": "分析完成", "rows_processed": 1000000}
    })
```

### 5.2 流式响应

#### Streamable HTTP + SSE

```python
@mcp.tool(stream=True)
async def stream_large_query(query: str):
    """流式返回大型查询结果"""
    async for chunk in db.execute_stream(query):
        yield {"type": "text", "text": chunk}
```

**配置要点**:
- 客户端初始化会话后，每个后续`tools/call`包含`Mcp-Session-Id`头部
- 设置`Accept: text/event-stream`头部
- 服务器以SSE事件响应，发送部分结果、进度更新或日志
- AI代理可以实时基于流式数据做出决策

### 5.3 并发请求处理

#### 异步I/O架构

```python
import asyncio
import httpx

@mcp.tool()
async def parallel_search(queries: list[str]) -> str:
    """并行搜索多个查询"""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"https://api.example.com/search?q={q}") for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return format_results(results)
```

**关键优化**:
- 每个外部I/O调用使用`await`和`asyncio.gather()`
- 单个Python进程可处理数百个并发AI代理请求
- 不会产生线程爆炸问题

#### 连接池

```python
import asyncpg

# 连接池配置
pool = await asyncpg.create_pool(
    dsn="postgresql://...",
    min_size=5,
    max_size=20
)

@mcp.tool()
async def query_db(sql: str) -> str:
    async with pool.acquire() as conn:
        result = await conn.fetch(sql)
        return format_result(result)
```

### 5.4 缓存策略

```python
from functools import lru_cache
import time

# 多级缓存
class McpCache:
    def __init__(self):
        self._memory_cache = {}  # L1: 内存缓存
        self._redis = None       # L2: Redis缓存

    async def get(self, key: str, ttl: int = 300):
        # L1检查
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry["time"] < ttl:
                return entry["value"]

        # L2检查
        if self._redis:
            value = await self._redis.get(key)
            if value:
                self._memory_cache[key] = {"value": value, "time": time.time()}
                return value

        return None
```

**实测数据**: 对重复查询可实现高达 **41倍** 的延迟降低。

### 5.5 性能优化清单

| 优化项 | 技术 | 效果 |
|--------|------|------|
| 异步I/O | asyncio + httpx/aiohttp | 消除阻塞等待 |
| 连接池 | asyncpg/aiomysql | 减少连接建立开销 |
| 多级缓存 | 内存 + Redis | 最高41x延迟降低 |
| 任务队列 | Celery/Temporal/Redis | 解耦长时间操作 |
| SSE流 | Streamable HTTP | 增量结果交付 |
| 负载均衡 | 会话亲和（SSE）或无状态 | 水平扩展 |
| 超时控制 | asyncio.wait_for(30s) | 防止连接泄漏 |
| 分页 | has_more + total_count | 控制响应大小 |
| 载荷最小化 | 仅返回必需字段 | 减少token消耗 |
| 工具预算 | 5-15个工具/服务器 | 减少上下文膨胀 |

---

## 6. MCP与Claude Code集成

### 6.1 概述

**Claude Code** 是Anthropic的AI驱动编码助手（终端优先的IDE环境），它作为MCP **客户端**运行，调用MCP **服务器**暴露的工具。

### 6.2 .mcp.json配置

#### 配置文件位置与作用域

| 作用域 | 位置 | 用途 | 优先级 |
|--------|------|------|--------|
| **Local** | `~/.claude.json` | 个人+项目私有 | 最高 |
| **Project** | 项目根目录 `.mcp.json` | 团队共享（可提交git） | 中 |
| **User** | `~/.claude.json` 顶层 | 全局用户设置 | 最低 |

#### .mcp.json标准格式

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/safe/path1", "/safe/path2"],
      "env": {}
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "remote-api": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    }
  }
}
```

**关键要点**:
- 秘密信息通过`${ENV_VAR}`环境变量扩展，保持git安全
- `type`支持 `"stdio"`（本地）和 `"http"`（远程）
- 文件系统服务器**必须**限制到明确的路径

#### CLI管理命令

```bash
# 添加项目级MCP服务器
claude mcp add --scope project --transport stdio my-server -- npx -y @my-mcp-package

# 添加HTTP服务器
claude mcp add --scope project --transport http my-api https://api.example.com/mcp

# 列出所有配置的MCP服务器
claude mcp list

# 移除MCP服务器
claude mcp remove my-server

# 在Claude Code内查看/管理
/mcp
```

### 6.3 权限模型

#### 权限评估顺序

```
deny → ask → allow
```

#### 配置示例 (settings.json)

```json
{
  "permissions": {
    "allow": [
      "mcp__github__*",
      "mcp__filesystem__read_file"
    ],
    "ask": [
      "mcp__filesystem__write_file",
      "mcp__database__*"
    ],
    "deny": [
      "mcp__dangerous-server",
      "mcp__filesystem__delete_file"
    ]
  }
}
```

#### 权限语法

| 模式 | 含义 |
|------|------|
| `mcp__servername` | 该服务器所有工具 |
| `mcp__servername__*` | 该服务器所有工具（通配符） |
| `mcp__servername__toolname` | 特定工具 |

#### 企业管控

```json
// managed-mcp.json（管理员锁定）
{
  "allowManagedMcpServersOnly": true,
  "allowedMcpServers": ["github", "filesystem"],
  "deniedMcpServers": ["untrusted-server"]
}
```

### 6.4 安全模型

#### 多层防御架构

```
┌─────────────────────────────────────────┐
│  Layer 1: 显式用户批准                    │
│  - 每个新MCP服务器需要信任/批准            │
│  - 每个敏感操作触发同意提示                │
├─────────────────────────────────────────┤
│  Layer 2: 沙箱隔离                       │
│  - stdio服务器和Bash工具在OS容器中运行     │
│  - 受限的网络/文件系统权限                 │
├─────────────────────────────────────────┤
│  Layer 3: OAuth 2.0 + 作用域令牌          │
│  - HTTP服务器自动令牌刷新                  │
│  - 永不硬编码密钥（使用${VAR}）            │
├─────────────────────────────────────────┤
│  Layer 4: 管理锁定                       │
│  - 组织管理员可强制allowManagedOnly       │
│  - 用户无法添加未批准的服务器              │
├─────────────────────────────────────────┤
│  Layer 5: 最小权限原则                    │
│  - 仅授予所需的确切路径/工具               │
│  - Anthropic不审计第三方MCP服务器          │
└─────────────────────────────────────────┘
```

### 6.5 安全检查清单

- [ ] 永不设置 `enableAllProjectMcpServers: true`
- [ ] 文件系统服务器仅限明确路径
- [ ] 使用OAuth作用域，而非完整令牌
- [ ] 在专用开发容器中运行
- [ ] 定期使用 `/permissions` 和 `claude mcp list` 审查
- [ ] 秘密信息使用环境变量，不硬编码
- [ ] 第三方MCP服务器视为不受信任的插件

---

## 7. 总结与建议

### 7.1 AUTO_EDA项目MCP Server开发建议

基于以上调研，为AUTO_EDA项目开发MCP Server提出以下建议:

#### 技术选型

| 选项 | 建议 | 理由 |
|------|------|------|
| **语言** | TypeScript | Node.js生态成熟，与Claude Code集成紧密 |
| **SDK** | @modelcontextprotocol/sdk | Tier 1官方SDK，完整功能支持 |
| **传输** | stdio（开发）+ Streamable HTTP（生产） | 兼顾开发体验和生产部署 |
| **Schema** | Zod | 编译时类型安全，自动生成JSON Schema |

#### 架构设计

1. **单一职责**: 按EDA功能域拆分MCP服务器
   - `eda-analysis-server`: 数据分析工具（统计、相关性、分布等）
   - `eda-visualization-server`: 图表生成工具
   - `eda-data-server`: 数据加载/转换资源
   - `eda-report-server`: 报告生成工具

2. **面向结果设计工具**:
   - `analyze_dataset(file_path)` → 完整的EDA摘要报告
   - `detect_anomalies(column)` → 异常值分析 + 建议
   - 而不是暴露底层pandas/numpy API

3. **扁平化参数**: 使用简单类型（string, number, boolean），避免嵌套对象

4. **精简策展**: 每个服务器5-15个核心工具

#### 性能考虑

- 大数据集分析使用Task原语（异步后台处理）
- 图表生成使用流式响应
- 重复分析结果使用多级缓存
- 数据库连接使用连接池

#### 安全配置

```json
// .mcp.json 示例
{
  "mcpServers": {
    "eda-analysis": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@auto-eda/analysis-server"],
      "env": {
        "DATA_DIR": "${EDA_DATA_DIR}",
        "MAX_FILE_SIZE": "100MB"
      }
    }
  }
}
```

### 7.2 关键参考资源

| 资源 | URL |
|------|-----|
| MCP规范 (最新) | https://modelcontextprotocol.io/specification/2025-11-25 |
| 构建MCP Server教程 | https://modelcontextprotocol.io/docs/develop/build-server |
| TypeScript SDK文档 | https://ts.sdk.modelcontextprotocol.io |
| Python SDK文档 | https://py.sdk.modelcontextprotocol.io |
| MCP安全最佳实践 | https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices |
| Claude Code MCP集成 | https://code.claude.com/docs/en/mcp |
| Claude Code权限 | https://code.claude.com/docs/en/permissions |
| GitHub: 官方MCP服务器 | https://github.com/modelcontextprotocol/servers |
| 15个生产最佳实践 | https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/ |
| Docker MCP最佳实践 | https://www.docker.com/blog/mcp-server-best-practices/ |

---

> 本研究报告基于截至2026年3月14日的最新信息编制。MCP协议仍在积极演进中，建议定期检查官方规范更新。
