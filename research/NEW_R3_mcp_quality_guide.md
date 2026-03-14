# 高质量MCP服务器开发最佳实践完整指南

> 调研日期：2026-03-14 | 覆盖：MCP规范 2024-2025、FastMCP 2.x、生产级设计模式

---

## 目录

1. [MCP协议核心架构](#1-mcp协议核心架构)
2. [FastMCP Python框架深度指南](#2-fastmcp-python框架深度指南)
3. [工具设计规范](#3-工具设计规范)
4. [Resources vs Tools vs Prompts最佳用法](#4-resources-vs-tools-vs-prompts最佳用法)
5. [错误处理和类型安全方案](#5-错误处理和类型安全方案)
6. [测试策略完整指南](#6-测试策略完整指南)
7. [性能优化技巧](#7-性能优化技巧)
8. [安全性检查清单](#8-安全性检查清单)
9. [生产部署指南](#9-生产部署指南)
10. [Claude Code最大化利用MCP工具](#10-claude-code最大化利用mcp工具)
11. [高质量MCP服务器案例分析](#11-高质量mcp服务器案例分析)
12. [AUTO_EDA项目MCP设计建议](#12-auto_eda项目mcp设计建议)

---

## 1. MCP协议核心架构

### 1.1 协议概述

Model Context Protocol (MCP) 是Anthropic于2024年底开源的标准化协议，用于AI模型与外部工具/数据源的通信。2025年协议已成为行业标准，被OpenAI、Google等主要AI厂商采用。

**核心设计理念：**
- **安全沙箱**：工具在隔离环境执行，不直接访问模型内部
- **声明式接口**：通过JSON Schema明确定义工具能力边界
- **双向通信**：支持服务器向客户端推送通知（采样、日志等）
- **传输无关**：同一服务器代码可跑在stdio、HTTP/SSE、WebSocket上

### 1.2 协议三层结构

```
┌─────────────────────────────────────────────┐
│              MCP Client (AI Host)            │
│  Claude Desktop / Claude Code / Cursor       │
├─────────────────────────────────────────────┤
│              MCP Protocol Layer              │
│  JSON-RPC 2.0 over stdio / HTTP+SSE / WS    │
├─────────────────────────────────────────────┤
│              MCP Server                      │
│  Tools + Resources + Prompts                 │
└─────────────────────────────────────────────┘
```

### 1.3 传输机制选择

| 传输方式 | 适用场景 | 优点 | 缺点 |
|---------|---------|------|------|
| **stdio** | 本地工具、CLI集成 | 最简单、无网络开销、天然隔离 | 仅限单进程 |
| **HTTP+SSE** | 远程服务、多客户端 | 可横向扩展、支持认证 | 更复杂的部署 |
| **StreamableHTTP** | 生产级远程服务 | 双向流、高性能 | 需HTTP/2支持 |

**最佳实践：** 开发阶段用stdio，生产环境用HTTP+SSE或StreamableHTTP。

### 1.4 协议能力声明

服务器初始化时必须声明能力，客户端据此决定可用功能：

```python
# FastMCP自动处理能力声明
# 显式声明示例（低级API）
Capabilities(
    tools=ToolsCapability(listChanged=True),
    resources=ResourcesCapability(subscribe=True, listChanged=True),
    prompts=PromptsCapability(listChanged=True),
    logging=LoggingCapability()
)
```

---

## 2. FastMCP Python框架深度指南

### 2.1 框架概述

FastMCP是目前最流行的Python MCP服务器框架，由Jeremy Howard团队开发，受FastAPI启发。

**关键特性（2025版本）：**
- 零样板代码：基于Python装饰器自动生成JSON Schema
- 类型推断：从函数签名自动提取参数类型
- 生命周期管理：async context manager支持启动/关闭资源
- 内置测试客户端：无需外部服务器即可测试
- 依赖注入：类似FastAPI的Depends模式
- 支持stdio、HTTP、SSE三种传输

### 2.2 基础结构

```python
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Any
import asyncio

# 推荐：使用lifespan管理资源生命周期
@asynccontextmanager
async def lifespan(server: FastMCP):
    # 启动时：初始化数据库连接、加载配置等
    db = await create_db_pool()
    cache = await create_redis_connection()
    server.state.db = db
    server.state.cache = cache

    yield  # 服务器运行期间

    # 关闭时：清理资源
    await db.close()
    await cache.close()

mcp = FastMCP(
    name="my-production-server",
    instructions="This server provides...",  # 告诉AI如何使用
    lifespan=lifespan,
)
```

### 2.3 工具注册完整示例

```python
from pydantic import BaseModel, Field
from typing import Annotated

class AnalysisRequest(BaseModel):
    """数据分析请求参数"""
    file_path: str = Field(description="CSV文件路径")
    target_column: str = Field(description="目标列名")
    method: str = Field(
        default="pearson",
        description="相关性计算方法",
        enum=["pearson", "spearman", "kendall"]
    )
    max_rows: int = Field(
        default=10000,
        ge=100,
        le=1000000,
        description="最大处理行数"
    )

@mcp.tool()
async def analyze_correlation(
    request: AnalysisRequest,
    ctx: Context  # FastMCP注入上下文
) -> str:
    """
    分析数据集中目标列与其他列的相关性。

    返回相关系数矩阵，支持Pearson、Spearman、Kendall三种方法。
    数据量超过max_rows时自动采样。
    """
    await ctx.info(f"开始分析 {request.file_path}")

    # 使用lifespan注入的资源
    db = ctx.fastmcp.state.db

    # 进度报告（大任务必须）
    await ctx.report_progress(0, 100, "加载数据")

    result = await _do_analysis(request, db)

    await ctx.report_progress(100, 100, "完成")
    return result
```

###
### 2.4 Context对象使用

```python
from fastmcp import FastMCP, Context

@mcp.tool()
async def process_data(file_path: str, ctx: Context) -> str:
    """处理数据文件"""
    # 日志（客户端可见）
    await ctx.info(f"开始处理: {file_path}")
    await ctx.debug("调试信息：加载文件")
    await ctx.warning("警告：文件较大，处理可能较慢")

    # 进度报告（流式任务必备）
    await ctx.report_progress(0, 100, "初始化")

    # 读取其他资源
    config = await ctx.read_resource("config://app-settings")

    # 请求ID用于追踪
    request_id = ctx.request_id

    await ctx.report_progress(50, 100, "处理中")
    result = await _process(file_path, config)

    await ctx.report_progress(100, 100, "完成")
    return result
```

### 2.5 服务器组合（FastMCP 3.x特性）

```python
# 将多个小服务器组合成一个大服务器
from fastmcp import FastMCP

# 各功能模块独立定义
data_server = FastMCP("DataTools")
analysis_server = FastMCP("AnalysisTools")
visualization_server = FastMCP("VisualizationTools")

# 主服务器组合所有模块
main_server = FastMCP("AUTO_EDA_Server")
main_server.mount("data", data_server)     # 前缀：data_*
main_server.mount("analysis", analysis_server)  # 前缀：analysis_*
main_server.mount("viz", visualization_server)  # 前缀：viz_*
```

---

## 3. 工具设计规范

### 3.1 命名规范

**黄金法则：工具名即合同——AI靠它决定何时调用**

```
推荐格式：{动词}_{名词}[_{修饰语}]

好的命名：
- analyze_correlation       # 清晰的动作+对象
- load_csv_file             # 具体的操作
- generate_eda_report       # 明确的输出
- detect_outliers_zscore    # 动作+方法修饰

糟糕的命名：
- process                   # 太模糊
- do_stuff                  # 无意义
- analyzeCorrelationData    # 混合风格
- tool_1                    # 无描述性
```

**命名规则：**
- 使用snake_case（90%的生产MCP服务器标准）
- 动词前缀：`get_`, `list_`, `create_`, `analyze_`, `detect_`, `generate_`, `load_`, `save_`, `search_`
- 长度：1-64字符，仅字母数字和下划线
- 同一服务器内唯一

### 3.2 工具粒度设计

**粒度选择决策树：**

```
问题：这个操作有多复杂？
│
├── 单一、原子操作 → 细粒度工具（推荐默认）
│   例：load_dataframe, calculate_statistics
│
├── 高频复合流程 → 粗粒度工具
│   例：run_full_eda（内部调用多个步骤）
│
└── 两者都需要 → 提供两个层级（最佳实践）
    细粒度用于定制，粗粒度用于快速完成
```

**实际示例（AUTO_EDA场景）：**

```python
# 细粒度（可组合）
@mcp.tool()
def load_csv(file_path: str) -> str: ...
@mcp.tool()
def calculate_basic_stats(df_id: str) -> str: ...
@mcp.tool()
def detect_missing_values(df_id: str) -> str: ...
@mcp.tool()
def plot_distribution(df_id: str, column: str) -> Image: ...

# 粗粒度（快速完成）
@mcp.tool()
def run_complete_eda(file_path: str) -> str:
    """执行完整的EDA分析：加载→统计→缺失值→分布→相关性"""
    ...
```

### 3.3 参数设计最佳实践

```python
from pydantic import BaseModel, Field
from typing import Annotated, Literal

# 好的参数设计：描述清晰、类型精确、有约束
@mcp.tool()
def analyze_data(
    # 字符串参数：说明格式和示例
    file_path: Annotated[str, Field(
        description="CSV文件的绝对路径，例如：/data/sales.csv"
    )],
    # 枚举类型：限制有效值，防止AI幻觉
    method: Literal["pearson", "spearman", "kendall"] = "pearson",
    # 数值约束：明确范围
    max_rows: Annotated[int, Field(
        ge=100, le=1_000_000,
        description="最大处理行数（100-1000000）"
    )] = 10_000,
    # 可选参数有合理默认值
    include_plots: bool = True,
) -> str:
    """分析CSV文件中的数据相关性。"""
    ...
```

**参数设计检查清单：**
- [ ] 每个参数都有清晰的description
- [ ] 枚举/有限选项使用Literal类型
- [ ] 数值有合理的ge/le约束
- [ ] 可选参数有合理默认值
- [ ] 避免深层嵌套结构（最多2层）
- [ ] 参数名使用snake_case，名词+形容词风格

### 3.4 工具文档字符串规范

```python
@mcp.tool()
async def detect_outliers(
    df_id: str,
    method: Literal["zscore", "iqr", "isolation_forest"] = "zscore",
    threshold: float = 3.0,
) -> str:
    """
    检测数据集中的异常值。

    支持三种检测方法：
    - zscore：适合正态分布数据，threshold通常设3.0
    - iqr：适合偏态分布，threshold通常设1.5
    - isolation_forest：适合高维数据，threshold为污染率(0.01-0.5)

    返回：
    - JSON格式的异常值报告，包含行索引、列名和异常得分
    - 示例：{"outliers": [{"row": 42, "column": "price", "score": 4.2}]}

    前提条件：df_id必须是通过load_csv或load_dataframe已加载的数据集ID
    """
```

**文档字符串必须包含：**
1. 一句话功能描述
2. 参数说明（特别是非显而易见的参数）
3. 返回值格式示例
4. 前提条件（如果有依赖）

---

## 4. Resources vs Tools vs Prompts最佳用法

### 4.1 三者对比

| 维度 | Tools | Resources | Prompts |
|------|-------|-----------|--------|
| **控制方** | AI模型自主决定 | 应用/客户端控制 | 用户/应用触发 |
| **是否执行** | 是（可有副作用） | 否（只读） | 否（模板） |
| **调用方式** | `tools/call` | `resources/read` | `prompts/get` |
| **典型用途** | 执行操作、计算 | 提供上下文数据 | 标准化工作流 |
| **副作用** | 允许 | 不允许 | 不适用 |

### 4.2 决策规则

```
需要AI执行操作？
  → YES: Tool

需要提供只读数据/上下文？
  → YES: Resource

需要标准化重复工作流？
  → YES: Prompt
```

### 4.3 AUTO_EDA场景示例

```python
# ✅ Tool：执行操作
@mcp.tool()
def load_csv(file_path: str) -> str:        # 加载数据
    ...

@mcp.tool()
def generate_plot(df_id: str) -> Image:     # 生成图表
    ...

# ✅ Resource：提供只读配置/状态
@mcp.resource("eda://loaded-datasets")
def list_loaded_datasets() -> str:
    """当前已加载的数据集列表"""
    return json.dumps(dataset_registry)

@mcp.resource("config://eda-settings")
def get_eda_config() -> str:
    """EDA分析的全局配置"""
    return json.dumps(config)

@mcp.resource("schema://{dataset_id}")
def get_dataset_schema(dataset_id: str) -> str:
    """获取已加载数据集的Schema信息"""
    return json.dumps(schemas[dataset_id])

# ✅ Prompt：标准化工作流模板
@mcp.prompt
def eda_analysis_workflow(file_path: str, target_column: str) -> str:
    return f"""请对 {file_path} 进行完整的探索性数据分析：
1. 使用 load_csv 加载数据
2. 使用 get_basic_statistics 查看基本统计量
3. 使用 detect_missing_values 检测缺失值
4. 重点分析 {target_column} 列与其他列的关系
5. 使用 generate_eda_report 生成最终报告"""
```

### 4.4 Resource模板（动态URI）

```python
# 支持URI参数化，实现动态资源
@mcp.resource("dataset://{dataset_id}/column/{column_name}")
async def get_column_stats(dataset_id: str, column_name: str) -> str:
    """获取特定数据集特定列的统计信息"""
    stats = await compute_column_stats(dataset_id, column_name)
    return json.dumps(stats, ensure_ascii=False)
```

---

## 5. 错误处理和类型安全方案

### 5.1 错误处理层次

```python
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError, ResourceError
from pydantic import ValidationError
import traceback

# 第1层：参数验证（Pydantic自动处理）
# 第2层：业务逻辑错误（ToolError，信息传给AI）
# 第3层：系统错误（记录日志，返回通用提示）

@mcp.tool()
async def load_csv(file_path: str, ctx: Context) -> str:
    # 第2层：业务逻辑验证
    if not file_path.endswith(('.csv', '.tsv')):
        raise ToolError(
            f"不支持的文件格式。请提供CSV或TSV文件。"
            f"提供的路径：{file_path}"
        )

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        # AI友好的错误：说明问题+给出建议
        raise ToolError(
            f"文件未找到：{file_path}\n"
            f"建议：请检查文件路径是否正确，使用绝对路径"
        )
    except pd.errors.EmptyDataError:
        raise ToolError(f"文件为空：{file_path}")
    except Exception as e:
        # 第3层：意外系统错误
        await ctx.error(f"加载CSV时发生意外错误: {traceback.format_exc()}")
        raise ToolError(f"加载文件时发生内部错误，请检查日志") from e

    return json.dumps({"dataset_id": register_df(df), "shape": df.shape})
```

### 5.2 LLM友好的错误设计原则

```python
# 糟糕的错误（AI无法自愈）
raise ValueError("KeyError: 'price'")

# 优秀的错误（AI可自愈）
raise ToolError(
    "列 'price' 在数据集中不存在。"
    f"可用的列：{', '.join(df.columns.tolist())}。"
    "请使用 list_columns
 工具查看完整列名列表"
)
```

**AI友好错误的四要素：**
1. **说明问题**：发生了什么
2. **提供上下文**：当前状态（可用值、范围等）
3. **给出建议**：下一步怎么做
4. **避免技术栈泄露**：不暴露内部实现细节

### 5.3 类型安全

使用 `Literal` 约束枚举参数，`Annotated[int, Field(ge=0, le=100)]` 约束数值范围，自定义类型做前缀验证（如 `ds_` 开头的数据集ID）。Pydantic在工具调用时自动验证所有参数并返回清晰的验证错误。

---

## 6. 测试策略完整指南

### 6.1 测试分层

| 层级 | 工具 | 覆盖目标 | 频率 |
|------|------|---------|------|
| 单元测试 | pytest + 直接函数调用 | 业务逻辑 | 每次提交 |
| 协议测试 | FastMCP Client | MCP握手、Schema | 每次构建 |
| 功能测试 | FastMCP Client | 工具端到端 | 每次构建 |
| 交互测试 | MCP Inspector | Schema可视化验证 | 开发时 |
| CI验证 | Inspector CLI | 回归测试 | 每次PR |

### 6.2 FastMCP内置测试客户端

FastMCP提供 `Client` 类直接测试服务器，无需启动外部进程：

```python
import pytest, json
from fastmcp import Client

@pytest.mark.asyncio
async def test_load_csv_success(tmp_path, mcp_server):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b,c\n1,2,3\n4,5,6")
    async with Client(mcp_server) as client:
        result = await client.call_tool("load_csv", {"file_path": str(csv_file)})
        data = json.loads(result[0].text)
        assert data["rows"] == 2

@pytest.mark.asyncio
async def test_load_csv_file_not_found(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("load_csv", {"file_path": "/nonexistent.csv"})
        assert result[0].is_error
        assert "文件未找到" in result[0].text

@pytest.mark.asyncio
async def test_list_tools(mcp_server):
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        assert "load_csv" in [t.name for t in tools]
```

**conftest.py 模板：**
```python
import pytest
from your_server import create_mcp_server

@pytest.fixture
def mcp_server():
    return create_mcp_server(test_mode=True)
```

### 6.3 MCP Inspector使用指南

**启动方式：**
```bash
# stdio服务器
npx @modelcontextprotocol/inspector python server.py
# uvx包
npx @modelcontextprotocol/inspector uvx my-mcp-server
# 浏览器访问: http://localhost:6274
```

**Inspector功能：**
- **Tools标签**：测试工具调用、查看JSON Schema、验证输入输出
- **Resources标签**：浏览列表、读取内容、测试模板URI
- **Prompts标签**：测试Prompt模板渲染
- **Notifications面板**：实时查看服务器日志和进度通知

**开发工作流：**
1. 启动Inspector连接服务器，验证能力协商
2. 逐一检查所有工具的JSON Schema是否正确生成
3. 测试正常路径（valid inputs）
4. 测试边界情况（invalid inputs、空值、超大输入）
5. 修改代码 → 重启 → 重新连接 → 回归测试

**CI/CD自动化（CLI模式）：**
```bash
npx @modelcontextprotocol/inspector --cli python server.py \
  --method tools/call \
  --tool-name load_csv \
  --tool-arg file_path=/data/test.csv
```

### 6.4 测试检查清单

- [ ] 每个工具至少3个测试（成功路径、失败路径、边界值）
- [ ] 参数验证测试（错误类型、超范围值、缺失必填项）
- [ ] Resource读取和模板URI测试
- [ ] Prompt渲染测试
- [ ] 并发调用测试（多客户端同时请求）
- [ ] 超时测试（大文件、慢操作）
- [ ] Lifespan测试（startup/shutdown正确执行）
- [ ] MCP Inspector手动验证所有Schema
- [ ] CI中Inspector CLI自动化回归

---

## 7. 性能优化技巧

### 7.1 多级缓存策略

```python
import time

class MCPCache:
    def __init__(self, max_size=1000, default_ttl=60):
        self._store: dict = {}
        self._max = max_size
        self._ttl = default_ttl

    def get(self, key: str):
        if key in self._store:
            value, expire = self._store[key]
            if time.time() < expire:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value, ttl: int = None):
        if len(self._store) >= self._max:
            del self._store[next(iter(self._store))]
        self._store[key] = (value, time.time() + (ttl or self._ttl))

cache = MCPCache()

@mcp.tool()
async def get_dataset_stats(dataset_id: str) -> str:
    if cached := cache.get(f"stats:{dataset_id}"):
        return cached
    result = await _compute_stats(dataset_id)
    cache.set(f"stats:{dataset_id}", result, ttl=300)
    return result
```

缓存收益：重复工具调用减少40-70% token消耗和延迟。

### 7.2 大文件分块处理

```python
@mcp.tool()
async def analyze_large_csv(file_path: str, chunk_size: int = 10_000, ctx: Context = None) -> str:
    """分块处理大型CSV（>100MB），避免内存溢出"""
    import pandas as pd
    results, total = [], 0
    for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
        total += len(chunk)
        results.append(_process_chunk(chunk))
        if ctx and i % 10 == 0:
            await ctx.report_progress(total, None, f"已处理 {total} 行")
    return json.dumps(_merge_results(results))
```

### 7.3 异步并发处理

```python
import asyncio

@mcp.tool()
async def batch_analyze_files(file_paths: list[str], ctx: Context) -> str:
    """并发分析多个文件，使用Semaphore控制并发数"""
    sem = asyncio.Semaphore(5)
    async def analyze_one(path: str):
        async with sem:
            return await _analyze_file_async(path)
    results = await asyncio.gather(*[analyze_one(p) for p in file_paths], return_exceptions=True)
    ok = [r for r in results if not isinstance(r, Exception)]
    err = [str(r) for r in results if isinstance(r, Exception)]
    return json.dumps({"results": ok, "errors": err})
```

### 7.4 连接池管理

在 `lifespan` 中初始化连接池（asyncpg/aiohttp等），通过 `ctx.fastmcp.state` 在所有工具间共用。
参数建议：min_size=5, max_size=20, command_timeout=30。

### 7.5 长时任务模式

长时任务使用 `await ctx.report_progress(current, total, message)` 定期推送进度。
将中间状态存入Resource（`jobs://{job_id}/status`），AI可随时读取状态而无需阻塞等待。

### 7.6 性能检查清单

- [ ] IO密集型操作全部使用 `async def`
- [ ] 大文件分块处理，避免一次性加载入内存
- [ ] 高频读取数据使用内存缓存
- [ ] 外部连接使用连接池（数据库、HTTP）
- [ ] 长任务定期调用 `report_progress`
- [ ] 并发操作使用 `asyncio.gather` + Semaphore
- [ ] 工具装饰器设置合理的 `timeout` 参数
- [ ] 响应内容精简（只返回AI需要的信息）

---

## 8. 安全性检查清单

### 8.1 输入验证与注入防护

```python
from pathlib import Path

ALLOWED_BASE = Path("/data/eda").resolve()

def safe_path(user_input: str) -> Path:
    """防止路径遍历攻击（../../../etc/passwd）"""
    resolved = (ALLOWED_BASE / user_input).resolve()
    if not str(resolved).startswith(str(ALLOWED_BASE)):
        raise ToolError("访问被拒绝：路径必须在允许目录内")
    return resolved

# SQL注入防护：白名单验证表名 + 参数化查询
ALLOWED_TABLES = {"designs", "simulations", "reports"}

async def query_table(table: str, limit: int = 100) -> str:
    if table not in ALLOWED_TABLES:
        raise ToolError(f"不允许的表名。可用：{sorted(ALLOWED_TABLES)}")
    rows = await db.fetch(f"SELECT * FROM {table} LIMIT $1", limit)
    return json.dumps([dict(r) for r in rows])
```

### 8.2 安全配置

```python
# 防止内部错误信息泄露
mcp = FastMCP("SecureServer", mask_error_details=True)

# 密钥从环境变量读取，永不硬编码
import os
API_KEY = os.environ["EDA_API_KEY"]
```

Prompt注入防护：永远不要将用户输入直接嵌入到发给LLM的指令字符串中，将用户数据和系统指令分离传递。

### 8.3 完整安全检查清单

**输入安全：**
- [ ] 文件路径验证在白名单目录内（防路径遍历）
- [ ] SQL使用参数化查询（防SQL注入）
- [ ] 命令执行使用参数列表而非字符串拼接（防命令注入）
- [ ] 用户输入大小限制（防DoS）
- [ ] 启用 `mask_error_details=True`（防信息泄露）

**认证授权：**
- [ ] HTTP传输模式使用OAuth2/JWT认证
- [ ] 危险操作（删除、覆盖、执行仿真）有额外权限检查
- [ ] 遵循最小权限原则
- [ ] 使用 `mcp.disable(tags={"dangerous"})` 按环境禁用危险工具

**密钥管理：**
- [ ] 所有密钥从环境变量读取
- [ ] 敏感信息不出现在日志中
- [ ] 错误信息不泄露内部路径/版本信息

**运行时安全：**
- [ ] 仿真/脚本执行在沙箱或容器中进行
- [ ] 设置资源限制（内存、CPU、文件大小上限）
- [ ] 速率限制防止滥用

---

## 9. 生产部署指南

### 9.1 Dockerfile（多阶段构建）

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv pip install --system -r pyproject.toml

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/ ./src/
# 非root用户运行
RUN useradd -m appuser && chown -R appuser /app
USER appuser
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "src.server"]
```

### 9.2 运行模式选择

```python
# server.py
if __name__ == "__main__":
    import os
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http":
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        mcp.run()  # stdio默认
```

```bash
# 开发：stdio
python server.py

# 生产：HTTP
MCP_TRANSPORT=http python server.py

# 或使用FastMCP CLI
fastmcp run server.py:mcp --transport http --port 8000
```

### 9.3 可观测性

```python
import structlog
import logging

# 结构化JSON日志
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# 在工具中使用
@mcp.tool()
async def load_csv(file_path: str, ctx: Context) -> str:
    logger.info("tool_called", tool="load_csv", file=file_path, request_id=ctx.request_id)
    # ...
```

**完整可观测性栈（推荐）：**
- 日志：structlog → Loki
- 指标：prometheus-client → Prometheus → Grafana
- 链路：OpenTelemetry → Tempo

### 9.4 健康检查（HTTP模式）

```python
from fastmcp.apps import FastMCP
from starlette.routing import Route
from starlette.responses import JSONResponse

async def health(request):
    return JSONResponse({"status": "ok", "version": "1.0.0"})

# 挂载到FastMCP的HTTP应用
app = mcp.http_app()
app.routes.append(Route("/health", health))
```

---

## 10. Claude Code最大化利用MCP工具

### 10.1 核心策略：程序化工具调用

Claude Code最强大的MCP使用模式是**程序化工具调用**：让Claude编写Python代码来编排多个MCP工具，而非逐一调用。

```python
# Claude生成的编排代码示例
# 场景：分析10个CSV文件并生成汇总报告

files = [f"/data/quarter_{i}.csv" for i in range(1, 11)]
results = []

for file in files:
    # 调用MCP工具
    load_result = load_csv(file_path=file)
    ds_id = json.loads(load_result)["dataset_id"]

    stats = get_basic_statistics(dataset_id=ds_id)
    outliers = detect_outliers(dataset_id=ds_id, method="iqr")

    results.append({"file": file, "stats": stats, "outliers": outliers})

# 最后一次性生成报告
report = generate_summary_report(data=json.dumps(results))
```

**优势：** 减少50-90% token消耗，避免中间推理步骤占用上下文窗口。

### 10.2 MCP服务器数量控制

| 场景 | 推荐活跃服务器数 | 原因 |
|------|---------------|------|
| 日常编码 | 2-3个 | 保留上下文窗口给代码 |
| 专项EDA任务 | 1个专用服务器 | 工具聚焦，减少选择混乱 |
| 复杂跨系统任务 | 最多5个 | 超过此数量AI选择质量下降 |

**原则：** 按任务按需激活，不使用时禁用。

### 10.3 CLAUDE.md集成MCP工具使用指南

在项目的 `CLAUDE.md` 中明确记录MCP工具使用规范：

```markdown
## MCP工具使用规范

### 数据加载
- 始终使用 `load_csv` 加载数据，获得dataset_id
- dataset_id格式：`ds_xxxxxxxx`，必须传给后续分析工具

### 分析流程
1. load_csv → 获取dataset_id
2. get_basic_statistics → 了解数据概况
3. detect_missing_values → 检查数据质量
4. 按需：detect_outliers / analyze_correlation / plot_distribution
5. generate_eda_report → 最终报告

### 注意事项
- 大文件（>50MB）使用 analyze_large_csv 而非 load_csv
- 生成图表后使用截图工具验证结果
```

### 10.4 最大化工具效能的设计原则

1. **工具数量控制**：每个MCP服务器5-15个工具，超过15个时AI选择准确率显著下降
2. **工具描述即合同**：docstring要让AI在0.5秒内理解何时使用该工具
3. **返回值可组合**：工具返回结构化JSON，便于Claude在后续步骤中解析使用
4. **提供Prompt模板**：用 `@mcp.prompt` 封装常见工作流，让Claude直接调用
5. **进度可见**：长任务用 `report_progress` 让Claude知道执行状态

### 10.5 多步骤工作流设计

```python
# 设计工具时考虑Claude的使用链
# 工具A的输出 → 工具B的输入

@mcp.tool()
def load_csv(file_path: str) -> str:
    # 返回包含dataset_id的JSON
    return json.dumps({"dataset_id": "ds_abc123", "rows": 1000, "cols": 10})

@mcp.tool()
def analyze_correlation(
    dataset_id: str,  # 直接接收上一步的输出
    method: str = "pearson"
) -> str:
    # dataset_id来自load_csv的返回值
    ...
```

---

## 11. 高质量MCP服务器案例分析

### 11.1 Filesystem MCP（官方参考实现）

**仓库：** `github.com/modelcontextprotocol/servers/src/filesystem`

**设计亮点：**
- **Roots机制**：通过配置允许访问的根目录白名单，防止路径遍历
- **工具聚焦**：仅8个工具（read_file, write_file, create_directory, list_directory, move_file, search_files, get_file_info, read_multiple_files）
- **错误信息质量**：每个错误都包含操作类型、路径和原因
- **类型安全**：TypeScript实现，Zod schema验证

**启动方式：**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
    }
  }
}
```

### 11.2 Chrome DevTools MCP（可视化反馈标杆）

**仓库：** `github.com/ChromeDevTools/chrome-devtools-mcp`

**设计亮点：**
- **截图反馈循环**：操作 → 截图 → LLM分析 → 再操作，实现视觉验证
- **工具分层**：基础操作（click, fill, navigate）+ 高层工具（lighthouse_audit, performance_trace）
- **状态管理**：页面选择器维护多标签状态
- **丰富的上下文**：每个操作返回DOM快照或截图，让AI知道当前页面状态

**对AUTO_EDA的启示：** EDA工具也应实现「生成图表 → 截图 → AI分析图表质量 → 调整参数」的反馈循环。

### 11.3 Blender MCP（复杂状态管理参考）

**设计亮点：**
- **场景状态Resource**：当前3D场景状态作为Resource持续暴露给AI
- **操作粒度适中**：不是每个参数一个工具，而是按操作语义分组
- **17.7k stars**：证明可视化创作类MCP的巨大需求
- **错误恢复**：操作失败时提供撤销能力

### 11.4 案例共性总结

| 优秀实践 | Filesystem | Chrome DevTools | Blender |
|---------|-----------|----------------|--------|
| 工具数量 <15 | 8个 | ~20个 | ~15个 |
| 有状态Resource | roots配置 | 页面快照 | 场景状态 |
| AI友好错误 | Yes | Yes | Yes |
| 可视化反馈 | No | Yes（截图） | Yes（渲染） |
| 文档字符串完整 | Yes | Yes | Yes |

---

## 12. AUTO_EDA项目MCP设计建议

### 12.1 服务器架构建议

基于调研，AUTO_EDA建议采用**模块化多服务器**架构：

```
auto_eda/
├── server.py              # 主服务器（组合所有模块）
├── tools/
│   ├── data_loading.py    # 数据加载工具（3-4个）
│   ├── statistics.py      # 统计分析工具（4-5个）
│   ├── visualization.py   # 可视化工具（4-5个）
│   ├── ml_analysis.py     # ML辅助分析（3-4个）
│   └── reporting.py       # 报告生成（2-3个）
├── resources/
│   ├── datasets.py        # 已加载数据集状态
│   └── config.py          # EDA配置
├── prompts/
│   └── workflows.py       # 标准EDA工作流模板
└── tests/
    └── test_*.py
```

**总工具数建议：15-20个**（按EDA领域，分布在5个模块中，每模块3-5个）

### 12.2 核心工具清单

**数据加载（data_loading.py）：**
- `load_csv` - 加载CSV/TSV文件
- `load_excel` - 加载Excel文件
- `list_datasets` - 列出已加载数据集
- `get_dataset_preview` - 预览数据集前N行

**统计分析（statistics.py）：**
- `get_basic_statistics` - 基本统计量（均值、中位数、标准差等）
- `detect_missing_values` - 缺失值检测与分析
- `analyze_correlation` - 相关性分析
- `detect_outliers` - 异常值检测
- `analyze_distribution` - 分布特征分析

**可视化（visualization.py）：**
- `plot_distribution` - 分布图（直方图/KDE）
- `plot_correlation_heatmap` - 相关性热图
- `plot_scatter_matrix` - 散点图矩阵
- `plot_time_series` - 时序图（如适用）

**报告（reporting.py）：**
- `generate_eda_report` - 生成完整EDA报告（Markdown/HTML）

### 12.3 关键Resource设计

```python
@mcp.resource("eda://datasets")
def list_loaded_datasets() -> str:
    """当前会话中已加载的所有数据集"""
    ...

@mcp.resource("eda://dataset/{dataset_id}/schema")
def get_schema(dataset_id: str) -> str:
    """数据集的列名、类型、非空数量"""
    ...

@mcp.resource("eda://dataset/{dataset_id}/sample")
def get_sample(dataset_id: str) -> str:
    """数据集前10行样本"""
    ...
```

**Resource的价值：** Claude在调用分析工具前，可先读取schema了解列名和类型，避免传入错误的列名。

### 12.4 可视化反馈闭环（差异化关键）

```python
@mcp.tool()
async def plot_distribution(
    dataset_id: str,
    column: str,
    ctx: Context
) -> Image:
    """
    绘制指定列的分布图。
    返回PNG图像，可直接在支持图像的MCP客户端中显示。
    Claude可分析图像质量并决定是否需要调整参数。
    """
    fig = _create_distribution_plot(dataset_id, column)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    return Image(data=buf.getvalue(), format="png")
```

**反馈循环：**
1. Claude调用 `plot_distribution` 生成图表
2. 图表以Image形式返回，Claude直接分析图像内容
3. Claude判断分布特征（偏态、多峰等），决定下一步分析方向
4. 必要时调整参数重新生成

### 12.5 AUTO_EDA MCP实施优先级

| 优先级 | 内容 | 原因 |
|--------|------|------|
| P0 | 数据加载 + 基本统计工具 | 核心功能，验证MCP框架可行性 |
| P0 | FastMCP lifespan + 数据集注册表 | 跨工具共享状态的基础 |
| P1 | 可视化工具（返回Image类型） | 差异化特性，验证视觉反馈闭环 |
| P1 | Resource（schema/sample） | 减少AI错误调用，提升体验 |
| P1 | 错误处理标准化 | 生产质量基础 |
| P2 | Prompt工作流模板 | 提升Claude使用效率 |
| P2 | 完整测试套件 | 长期维护保障 |
| P3 | 缓存优化 | 性能提升 |
| P3 | HTTP传输 + 认证 | 多用户/云部署 |

---

## 附录：快速参考卡片

### FastMCP最小生产模板

```python
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from contextlib import asynccontextmanager
from typing import Annotated, Literal
from pydantic import Field
import json

@asynccontextmanager
async def lifespan(server: FastMCP):
    # 启动：初始化共享资源
    server.state.dataset_registry = {}
    yield
    # 关闭：清理资源
    server.state.dataset_registry.clear()

mcp = FastMCP(
    name="auto-eda",
    instructions="EDA分析服务器。先用load_csv加载数据，再调用分析工具。",
    lifespan=lifespan,
    mask_error_details=False,  # 开发时False，生产时True
)

@mcp.tool()
async def load_csv(
    file_path: Annotated[str, Field(description="CSV文件绝对路径")],
    ctx: Context,
) -> str:
    """
    加载CSV文件到内存，返回dataset_id供后续工具使用。
    支持.csv和.tsv格式，自动检测编码。
    """
    import pandas as pd
    if not file_path.endswith(('.csv', '.tsv')):
        raise ToolError(f"不支持的格式。请提供.csv或.tsv文件，收到：{file_path}")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise ToolError(f"文件未找到：{file_path}\n建议：使用绝对路径")
    except Exception as e:
        raise ToolError(f"读取文件失败：{e}") from e

    ds_id = f"ds_{abs(hash(file_path)):08x}"
    ctx.fastmcp.state.dataset_registry[ds_id] = df
    await ctx.info(f"已加载：{file_path} → {ds_id}")
    return json.dumps({"dataset_id": ds_id, "rows": len(df), "cols": len(df.columns),
                       "columns": df.columns.tolist()})

@mcp.resource("eda://datasets")
def list_datasets() -> str:
    """列出当前会话中已加载的所有数据集"""
    registry = mcp.state.dataset_registry if hasattr(mcp, 'state') else {}
    return json.dumps([{"id": k, "shape": list(v.shape)}
                       for k, v in registry.items()])

@mcp.prompt
def eda_quickstart(file_path: str) -> str:
    return (f"请对 {file_path} 进行EDA分析：\n"
            "1. load_csv加载数据\n2. get_basic_statistics查看统计量\n"
            "3. detect_missing_values检查缺失值\n4. analyze_correlation分析相关性")

if __name__ == "__main__":
    mcp.run()
```

### MCP协议版本速查

| 版本 | 日期 | 关键变化 |
|------|------|--------|
| 2024-11-05 | 2024-11 | 初始版本，HTTP+SSE传输 |
| 2025-03-26 | 2025-03 | 引入Streamable HTTP，替代SSE |
| 2025-06-18 | 2025-06 | 结构化数据、安全增强 |
| **2025-11-25** | 2025-11 | **当前最新**，生产级认证、任务管理 |

### 错误类型速查

| 错误类 | 何时使用 | 是否传给AI |
|--------|---------|----------|
| `ToolError` | 业务逻辑错误、可预期失败 | 是（始终） |
| `ResourceError` | 资源读取失败 | 是（始终） |
| 其他异常 | 系统错误 | 取决于 `mask_error_details` |

---

*文档版本：1.0.0 | 调研日期：2026-03-14 | 覆盖FastMCP 3.x、MCP规范2025-11-25*
