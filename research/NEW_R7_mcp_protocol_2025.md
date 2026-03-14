# MCP协议和FastMCP 2025最新进展调研报告

**调研日期**: 2026-03-14
**信息来源**: Cursor官方文档 (docs.cursor.com/context/mcp)、modelcontextprotocol.io

---

## 1. MCP协议最新规范变更总结

### 1.1 Cursor 当前支持的传输方式

| 传输方式 | 执行环境 | 部署方式 | 用户数 | 认证 |
|---------|---------|---------|-------|------|
| `stdio` | 本地 | Cursor托管 | 单用户 | 手动 |
| `SSE` | 本地/远程 | 自部署服务器 | 多用户 | OAuth |
| `Streamable HTTP` | 本地/远程 | 自部署服务器 | 多用户 | OAuth |

### 1.2 MCP协议能力矩阵

| 特性 | 支持状态 | 描述 |
|------|---------|------|
| **Tools** | 已支持 | AI模型可执行的函数 |
| **Prompts** | 已支持 | 模板化消息和工作流 |
| **Resources** | 已支持 | 可读取的结构化数据源 |
| **Roots** | 已支持 | URI/文件系统边界的服务器查询 |
| **Elicitation** | 已支持 | 服务器主动向用户请求附加信息 |
| **Apps (扩展)** | 已支持 | MCP工具返回交互式UI视图 |

### 1.3 MCP Apps 扩展说明

- MCP工具可以返回交互式UI，与标准工具输出并存
- 遵循**渐进增强**原则：宿主无法渲染UI时，工具依然通过标准MCP响应正常运行
- AUTO_EDA可利用此特性返回交互式图表面板

---

## 2. MCP服务器配置方法（mcp.json）

### 2.1 STDIO本地服务器（Python）

```json
{
  "mcpServers": {
    "auto-eda": {
      "command": "python",
      "args": ["${workspaceFolder}/mcp_server.py"],
      "env": { "API_KEY": "${env:EDA_API_KEY}" },
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

### 2.2 远程Streamable HTTP服务器

```json
{
  "mcpServers": {
    "auto-eda-remote": {
      "url": "http://localhost:8080/mcp",
      "headers": { "Authorization": "Bearer ${env:EDA_API_KEY}" }
    }
  }
}
```

### 2.3 静态OAuth凭据配置

```json
{
  "mcpServers": {
    "oauth-server": {
      "url": "https://api.example.com/mcp",
      "auth": {
        "CLIENT_ID": "${env:MCP_CLIENT_ID}",
        "CLIENT_SECRET": "${env:MCP_CLIENT_SECRET}",
        "scopes": ["read", "write"]
      }
    }
  }
}
```

| 字段 | 必填 | 描述 |
|------|------|------|
| `CLIENT_ID` | 是 | OAuth 2.0客户端ID |
| `CLIENT_SECRET` | 否 | 机密客户端时需要 |
| `scopes` | 否 | 请求的OAuth作用域（省略则自动发现）|

Cursor固定回调URL: `cursor://anysphere.cursor-mcp/oauth/callback`

---

## 3. STDIO配置字段参考

| 字段 | 必填 | 描述 | 示例 |
|------|------|------|------|
| `command` | 是 | 可执行命令 | `"python"`, `"npx"` |
| `args` | 否 | 参数数组 | `["server.py"]` |
| `env` | 否 | 环境变量 | `{"KEY": "${env:VAR}"}` |
| `envFile` | 否 | .env文件路径（仅STDIO支持）| `".env"` |

> `envFile`仅适用于STDIO服务器；远程服务器应使用系统环境变量或`headers`传递认证信息。

---

## 4. 图像内容返回（EDA图表）

MCP服务器可返回base64编码图像，Cursor会在聊天中渲染并可视觉分析：

```python
# Python / FastMCP示例
from fastmcp import FastMCP, Image

mcp = FastMCP("EDA-Server")

@mcp.tool()
def generate_histogram(csv_path: str) -> Image:
    """生成数据直方图并返回图像"""
    chart_bytes = create_histogram_bytes(csv_path)
    return Image(data=chart_bytes, format="png")
```

---

## 5. 安全考虑清单

- **验证来源**: 只从可信开发者和仓库安装MCP服务器
- **审查权限**: 检查服务器将访问哪些数据和API
- **限制API密钥**: 使用具有最小必要权限的受限API密钥
- **审计代码**: 对关键集成审查服务器源代码
- **使用环境变量**: 密钥通过`${env:VAR_NAME}`注入，**永不硬编码**
- **本地运行敏感服务器**: 敏感数据优先使用`stdio`传输
- **隔离环境**: 考虑在隔离环境中运行服务器

MCP服务器可代表用户访问外部服务并执行代码，安装前务必了解其行为。

---

## 6. AUTO_EDA项目建议配置

### 6.1 项目级配置（.cursor/mcp.json）

```json
{
  "mcpServers": {
    "auto-eda": {
      "command": "python",
      "args": ["${workspaceFolder}/src/mcp_server.py"],
      "env": {
        "DATA_DIR": "${workspaceFolder}/data",
        "LOG_LEVEL": "INFO"
      },
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

### 6.2 FastMCP影响分析

| AUTO_EDA模块 | 推荐做法 |
|-------------|----------|
| EDA核心工具 | 用`@mcp.tool()`装饰器注册，返回结构化dict |
| 图表可视化 | 返回`Image`对象，让Cursor直接在聊天中展示 |
| 进度反馈 | 长时分析用`ctx.report_progress(done, total)` |
| 调试/日志 | 用`ctx.info()`替代print，结构化输出 |
| 远程部署 | 切换至Streamable HTTP传输，弃用旧SSE |
| 多工具组合 | 用`mcp.mount()`组合子模块服务器 |

---

## 7. MCP服务器参考实现

| 项目 | Stars | 特点 | 对AUTO_EDA的借鉴 |
|------|-------|------|------------------|
| Blender MCP | ~17.7k | Python subprocess调用Blender API，截图反馈 | 可视化反馈闭环模式 |
| GitHub MCP | 官方 | REST API封装，工具粒度细（5-15个） | 工具分组策略 |
| MCP4EDA | 早期 | TypeScript/CLI调用Yosys/OpenLane | 数字IC工具链集成 |
| kicad-mcp | 早期 | KiCad IPC API Python封装 | PCB操作模式 |

---

## 8. Extension API程序化注册

`ExtMCPServerConfig` 是 `StdioServerConfig | RemoteServerConfig` 的联合类型：

```typescript
interface StdioServerConfig {
  name: string;
  server: { command: string; args: string[]; env: Record<string, string>; };
}

interface RemoteServerConfig {
  name: string;
  server: { url: string; headers?: Record<string, string>; };
}
```

```typescript
// 条件注册（防止重复）
if (!isServerRegistered("auto-eda")) {
  vscode.cursor.mcp.registerServer({
    name: "auto-eda",
    server: {
      command: "python",
      args: ["-m", "auto_eda.mcp_server"],
      env: { DATA_DIR: "/data", LOG_LEVEL: "INFO" },
    },
  });
}

// 清理时注销
vscode.cursor.mcp.unregisterServer("auto-eda");
```

适用场景：团队共享配置、MDM系统自动部署、CI环境动态注册。

---

## 9. 关键结论与行动项

| 优先级 | 行动项 | 影响范围 |
|--------|--------|----------|
| 高 | 将AUTO_EDA现有SSE传输迁移至Streamable HTTP | 兼容性、性能 |
| 高 | 利用`Image`返回类型输出EDA图表 | 用户体验 |
| 高 | 所有密钥通过`${env:VAR_NAME}`注入，禁止硬编码 | 安全 |
| 中 | 启用`ctx.report_progress()`提升长任务体验 | 可用性 |
| 中 | 评估MCP Apps扩展用于交互式仪表板 | 功能扩展 |
| 低 | 探索Extension API用于团队自动化部署 | 运维效率 |

---

**参考文档**:
- Cursor MCP配置: https://docs.cursor.com/context/mcp
- Cursor MCP Extension API: https://docs.cursor.com/context/mcp-extension-api
- MCP协议官网: https://modelcontextprotocol.io
- MCP Apps扩展: https://modelcontextprotocol.io/extensions/apps/overview
