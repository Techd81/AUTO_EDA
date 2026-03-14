[根目录](../../../../CLAUDE.md) > [src/auto_eda](../../) > **core**

# core — 核心基础库

## 模块职责

`core/` 提供所有 MCP Server 共用的基础设施：错误体系、异步子进程管理、FastMCP 服务器工厂、结果格式化。不含任何 EDA 工具特定逻辑。

---

## 入口与启动

不直接运行，由各 Server 模块导入使用。

```python
from auto_eda.core.base_server import create_server, eda_tool
from auto_eda.core.errors import EDAError, EDAErrorCode
from auto_eda.core.process import run_tool, find_tool
from auto_eda.core.result import ToolSuccess, ToolFailure, format_mcp_error
```

---

## 对外接口

### errors.py

**`EDAErrorCode(IntEnum)`** — 错误码命名空间：
- `1xxx`：通用错误（UNKNOWN/INVALID_INPUT/FILE_NOT_FOUND/TIMEOUT 等）
- `2xxx`：工具环境错误（TOOL_NOT_FOUND/DEPENDENCY_MISSING 等）
- `3xxx`：Yosys 错误
- `4xxx`：KiCad 错误
- `5xxx`：Verilog 解析错误

**异常类层级：**
```
Exception
└── EDAError(code, message, detail, tool_output)
    ├── ToolNotFoundError(tool_name)
    ├── ToolTimeoutError(tool_name, timeout_s)  # 别名 EDATimeoutError
    ├── ToolExecutionError(tool_name, returncode, stderr)
    ├── FileNotFoundEDAError(file_path)
    └── DependencyMissingError(package_name)
```

`EDAError.to_mcp_error_text()` — 格式化为 MCP 工具错误文本（含 code、message、detail、tool_output 截断至 2000 字符）。

### process.py

**`find_tool(name: str) -> str`** — 在 PATH 查找可执行文件，未找到抛 `ToolNotFoundError`。

**`run_tool(args, *, timeout, cwd, env, check_input_file) -> ProcessResult`** — 异步子进程执行，含超时保护，返回 `ProcessResult(returncode, stdout, stderr, args)`。

### base_server.py

**`create_server(name, version) -> FastMCP`** — 创建统一配置的 FastMCP 实例。

**`@eda_tool`** — 装饰器，统一捕获 `EDAError` 和未预期异常，格式化为 MCP 错误文本，记录耗时日志。用法：`@mcp.tool()` 上方叠加 `@eda_tool`。

### result.py

**`ToolSuccess(success=True, data, warnings, tool_used, elapsed_s)`** — 成功返回包装。

**`ToolFailure(success=False, error_code, error_message, detail, tool_output)`** — 失败返回包装。

**`format_mcp_error(error: Exception) -> str`** — 将任意异常格式化为 MCP 工具错误文本。

---

## 关键依赖

- `mcp>=1.3.0`（FastMCP）
- `pydantic>=2.0`（ToolSuccess/ToolFailure 模型）
- Python 标准库：`asyncio`、`shutil`、`pathlib`、`logging`

---

## 测试与质量

`tests/test_core/test_errors.py` 含 10 个单元测试覆盖错误类层级和 `to_dict()` 方法。

> 注意：test_errors.py 中引用 `TimeoutError` 和 `TOOL_EXECUTION_FAILED` 与实际命名不一致（应为 `ToolTimeoutError`/`EDATimeoutError` 和 `EDAErrorCode.UNKNOWN`），需修复。

---

## 相关文件清单

```
src/auto_eda/core/
├── __init__.py
├── errors.py      # EDAErrorCode + EDAError 层级
├── process.py     # ProcessResult, find_tool(), run_tool()
├── base_server.py # create_server(), @eda_tool
└── result.py      # ToolSuccess, ToolFailure, format_mcp_error()
```

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 架构师扫描自动生成，基于全量代码阅读 |
