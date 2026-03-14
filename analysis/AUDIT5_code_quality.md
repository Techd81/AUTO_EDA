# AUDIT5: AUTO_EDA Phase 0 代码质量审查清单

> 文档类型: 代码审查清单（执行前置版）
> 生成日期: 2026-03-14
> 审计状态: **待审计** — 源码尚未生成，本清单供 Agent 生成代码后对照检查
> 数据来源: DA3_phase0_implementation_spec.md · PLAN6_kickoff_guide.md

---

## 执行说明

本清单分为 6 个审计维度，每项均标注：
- **规范来源**：DA3 章节号或 PLAN6 章节号
- **检查方法**：可直接执行的命令或人工审阅说明
- **优先级**：P0（阻断发布）/ P1（重要）/ P2（建议）

审计时将每项结果标记为 `[PASS]` / `[FAIL]` / `[N/A]`。

---

## 维度 1：项目结构合规性

> 规范来源：DA3 §1.1 完整目录树、§1.2 模块职责边界

### 1.1 目录结构完整性

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 1.1.1 | `src/auto_eda/__init__.py` 存在且包含 `__version__` | P0 | `grep -n '__version__' src/auto_eda/__init__.py` | |
| 1.1.2 | `src/auto_eda/__main__.py` 存在且包含 `main()` 函数 | P0 | `grep -n 'def main' src/auto_eda/__main__.py` | |
| 1.1.3 | `core/` 下包含 4 个文件：`base_server.py`, `errors.py`, `process.py`, `result.py` | P0 | `ls src/auto_eda/core/` | |
| 1.1.4 | `models/` 下包含 3 个模型文件：`yosys.py`, `kicad.py`, `verilog.py` | P0 | `ls src/auto_eda/models/` | |
| 1.1.5 | `servers/yosys/` 下包含：`server.py`, `synthesizer.py`, `scripts.py`, `parser.py` | P0 | `ls src/auto_eda/servers/yosys/` | |
| 1.1.6 | `servers/kicad/` 下包含：`server.py`, `ipc_client.py`, `cli_fallback.py`, `version.py` | P0 | `ls src/auto_eda/servers/kicad/` | |
| 1.1.7 | `servers/verilog_utils/` 下包含：`server.py`, `parser.py`, `linter.py` | P0 | `ls src/auto_eda/servers/verilog_utils/` | |
| 1.1.8 | `tests/` 目录结构完整（`unit/`, `integration/`, `mcp/`, `fixtures/`） | P1 | `find tests/ -type d` | |
| 1.1.9 | `tests/fixtures/verilog/` 包含 4 个测试文件 | P1 | `ls tests/fixtures/verilog/` | |
| 1.1.10 | `pyproject.toml` 存在于项目根目录 | P0 | `ls pyproject.toml` | |
| 1.1.11 | `.mcp.json` 存在且包含 3 个 server 配置 | P1 | `python -m json.tool .mcp.json` | |

### 1.2 模块职责边界

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 1.2.1 | `core/errors.py` 不引用任何 EDA 库 | P0 | `grep -n 'import yosys\|import kicad\|import pyverilog' src/auto_eda/core/errors.py` 应无输出 | |
| 1.2.2 | `core/process.py` 不包含 EDA 特定输出解析逻辑 | P0 | 人工审阅：无 Yosys/KiCad 特定字符串匹配 | |
| 1.2.3 | `core/result.py` 不包含业务逻辑 | P1 | 人工审阅：应为纯数据类，无 if/else EDA 分支 | |
| 1.2.4 | `models/*.py` 不包含 subprocess 调用 | P0 | `grep -rn 'subprocess\|create_subprocess' src/auto_eda/models/` 应无输出 | |
| 1.2.5 | `servers/*/server.py` 不直接调用 EDA 工具 | P0 | `grep -n 'shutil.which\|subprocess' src/auto_eda/servers/yosys/server.py` 应无输出 | |

---

## 维度 2：类型注解完整性

> 规范来源：DA3 §2（pyproject.toml mypy strict 配置）、A7 技术栈决策

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 2.1 | `mypy --strict` 零错误通过 | P0 | `mypy src/auto_eda/` 输出 `Success: no issues found` | |
| 2.2 | 所有公共函数具备完整参数类型注解 | P0 | `mypy --strict` 覆盖此项；或 `grep -n 'def ' src/auto_eda/core/*.py` 人工确认 | |
| 2.3 | 所有公共函数具备返回值类型注解 | P0 | 同上，重点检查 `async def` 函数是否标注 `-> Coroutine` 或具体返回类型 | |
| 2.4 | `core/result.py` 中 `ToolSuccess.data` 使用 `dict[str, Any]` 而非裸 `dict` | P1 | `grep -n 'data:' src/auto_eda/core/result.py` | |
| 2.5 | Pydantic 模型字段均使用具体类型（无裸 `Any` 字段） | P1 | `grep -n ': Any' src/auto_eda/models/*.py` 应无输出（或有合理注释） | |
| 2.6 | `EDAErrorCode` 继承 `IntEnum`，所有成员有整数值 | P0 | `grep -n 'class EDAErrorCode' src/auto_eda/core/errors.py` | |
| 2.7 | `TypeVar` 使用规范（`F = TypeVar("F", bound=Callable[..., Any])`） | P1 | 人工审阅 `core/base_server.py` 中 TypeVar 定义 | |
| 2.8 | `from __future__ import annotations` 在所有模块首行（Python 3.10 兼容） | P1 | `grep -rL 'from __future__ import annotations' src/auto_eda/` 应无输出 | |
| 2.9 | mypy overrides 配置中列出了所有无 stub 的 EDA 库 | P1 | 对照 pyproject.toml `[tool.mypy.overrides]`，确认包含 `pyverilog.*`, `gdstk.*`, `kikit.*`, `sexpdata.*` | |

---

## 维度 3：错误处理完整性

> 规范来源：DA3 §3.1（errors.py）、§3.4（base_server.py 装饰器）、§9（错误码规范）

### 3.1 错误码体系

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 3.1.1 | `EDAErrorCode` 包含全部分段错误码：1xxx(通用)、2xxx(工具环境)、3xxx(Yosys)、4xxx(KiCad)、5xxx(Verilog) | P0 | `grep -n '= [0-9]' src/auto_eda/core/errors.py` 确认各段覆盖 | |
| 3.1.2 | `ToolNotFoundError` 和 `ToolTimeoutError` 子类存在且调用 `super().__init__` 传入正确 code | P0 | 人工审阅 `core/errors.py` | |
| 3.1.3 | `EDAError.to_mcp_error_text()` 截断 `tool_output` 至 2000 字符（防大输出淹没 MCP 响应） | P0 | `grep -n 'tool_output\[:' src/auto_eda/core/errors.py` 应见 `[:2000]` | |
| 3.1.4 | 错误消息国际化兼容（不含 Python 对象 repr，仅含 str） | P1 | 人工审阅所有 `EDAError` 子类的 `message` 参数 | |

### 3.2 异常传播与捕获

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 3.2.1 | `@eda_tool` 装饰器捕获 `EDAError` 并返回 `format_mcp_error(e)` 字符串（不 re-raise） | P0 | 人工审阅 `core/base_server.py` wrapper 函数 | |
| 3.2.2 | `@eda_tool` 装饰器捕获裸 `Exception` 作为兜底，记录 `logger.exception` | P0 | `grep -n 'except Exception' src/auto_eda/core/base_server.py` | |
| 3.2.3 | `core/process.py` 中 `FileNotFoundError` 转换为 `ToolNotFoundError`（不泄露系统路径） | P0 | 人工审阅 `run_tool()` 中 `except FileNotFoundError` 分支 | |
| 3.2.4 | `asyncio.TimeoutError` 触发子进程 `kill()` 后 `await proc.communicate()`（防僵尸进程） | P0 | `grep -A3 'TimeoutError' src/auto_eda/core/process.py` 确认有 `proc.kill()` + `await proc.communicate()` | |
| 3.2.5 | 无空 `except` 块（`except: pass` 或 `except Exception: pass`） | P0 | `grep -rn 'except.*pass' src/auto_eda/` 应无输出 | |
| 3.2.6 | 无裸 `raise` 重新抛出未包装异常（应转为 EDAError 子类） | P1 | `grep -rn '^\s*raise$' src/auto_eda/` 应无输出 | |
| 3.2.7 | Pydantic 验证失败（`ValidationError`）被捕获并转为 `EDAErrorCode.INVALID_INPUT` | P1 | 人工审阅各 server 入口函数对 `ValidationError` 的处理 | |

### 3.3 超时与资源清理

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 3.3.1 | 所有 `run_tool()` 调用均传入 `timeout_s` 参数（不使用默认 300s 作为隐式超时） | P1 | `grep -rn 'run_tool(' src/auto_eda/servers/` 确认均含 `timeout_s=` | |
| 3.3.2 | 临时文件使用 `tempfile.TemporaryDirectory` 或等效上下文管理器（防泄漏） | P1 | `grep -rn 'tempfile\|TemporaryDirectory\|mkdtemp' src/auto_eda/servers/` | |
| 3.3.3 | KiCad IPC 连接在 `finally` 块或 `__aexit__` 中关闭 | P0 | 人工审阅 `servers/kicad/ipc_client.py` 的连接生命周期管理 | |


---

## 维度 4：安全风险审查

> 规范来源：DA4_risk_mitigation_deep.md（T7 LLM 幻觉、T1 KiCad API 不稳定）、DA3 §3.2（process.py）

### 4.1 命令注入防御（最高优先级）

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 4.1.1 | `run_tool()` 使用 `asyncio.create_subprocess_exec(*args)` 而非 `shell=True` 或 `subprocess.run(cmd_string)` | P0 | `grep -rn 'shell=True\|subprocess.run\|os.system\|Popen.*shell' src/auto_eda/` 应无输出 | |
| 4.1.2 | 综合脚本模板（`scripts.py`）中用户输入仅用于填充 `.format()` 占位符，不拼接到 shell 命令字符串 | P0 | 人工审阅 `servers/yosys/scripts.py` — 脚本通过 stdin 传入 yosys，而非 shell 执行 | |
| 4.1.3 | 文件路径参数通过 `Path(user_input).resolve()` 规范化（防目录穿越 `../../etc/passwd`） | P0 | `grep -rn 'Path(' src/auto_eda/servers/' 确认路径参数被 resolve() 或 absolute()` | |
| 4.1.4 | 宏定义（`defines: dict[str, str]`）的键值均经过白名单验证（仅允许 `[A-Za-z0-9_]`） | P0 | 查看 `models/yosys.py` 中 `SynthesizeInput.defines` 是否有 `field_validator` 检查 | |
| 4.1.5 | 模块名（`top_module: str`）经过白名单验证（仅允许 Verilog 标识符字符） | P0 | 查看 `models/yosys.py` 中 `top_module` 是否有 validator（格式：`[A-Za-z_][A-Za-z0-9_]*`） | |

### 4.2 文件系统安全

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 4.2.1 | `output_dir` 不允许写入到系统路径（`/etc`, `/usr`, `/bin` 等） | P1 | 人工审阅 `SynthesizeInput.output_dir` 是否有路径黑名单或沙箱检查 | |
| 4.2.2 | 临时目录创建在系统 temp 路径下（`tempfile.gettempdir()`），而非用户指定的任意路径 | P1 | `grep -rn 'mkdtemp\|TemporaryDirectory' src/auto_eda/` 确认未使用用户路径作为 temp dir | |
| 4.2.3 | Yosys 日志输出截断至 50KB 后写入响应（防内存溢出） | P1 | `grep -n 'yosys_log\[:' src/auto_eda/` 或人工审阅 `SynthesizeOutput.yosys_log` 赋值逻辑 | |

### 4.3 依赖与供应链安全

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 4.3.1 | `pyproject.toml` 中所有依赖均指定下限版本（`>=x.y.z`），无无约束依赖（`*`） | P1 | `grep -n '"\*"\|>=0' pyproject.toml` 应无无约束依赖 | |
| 4.3.2 | 无已知 CVE 的依赖版本（mcp, pydantic, anyio） | P1 | `pip-audit` 或 `safety check`；或手动确认 pydantic>=2.6, mcp>=1.3 | |

---

## 维度 5：测试覆盖合理性

> 规范来源：DA3 §7（测试框架设计）、PLAN3_testing_strategy.md

### 5.1 测试文件覆盖

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 5.1.1 | `tests/unit/` 包含 DA3 规定的全部 10 个单元测试文件 | P0 | `ls tests/unit/` 对照：`test_errors.py`, `test_process.py`, `test_result.py`, `test_yosys_models.py`, `test_kicad_models.py`, `test_verilog_models.py`, `test_yosys_parser.py`, `test_yosys_scripts.py`, `test_kicad_version.py`, `test_verilog_parser.py` | |
| 5.1.2 | `tests/integration/` 包含 3 个集成测试文件 | P1 | `ls tests/integration/` 对照：`test_yosys_server.py`, `test_kicad_server.py`, `test_verilog_utils.py` | |
| 5.1.3 | `tests/mcp/` 包含 3 个 MCP 协议合规性测试文件 | P1 | `ls tests/mcp/` 对照：`test_yosys_mcp_protocol.py`, `test_kicad_mcp_protocol.py`, `test_verilog_mcp_protocol.py` | |
| 5.1.4 | `tests/conftest.py` 定义 `tmp_verilog_file`, `mock_process_result` 等全局 fixtures | P1 | `grep -n 'def ' tests/conftest.py` | |

### 5.2 单元测试质量

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 5.2.1 | `test_errors.py` 覆盖：`to_mcp_error_text()` 截断逻辑、`ToolNotFoundError` 消息格式 | P0 | 人工审阅 `tests/unit/test_errors.py` | |
| 5.2.2 | `test_process.py` 覆盖：timeout 触发时进程被 kill（使用 mock）、`FileNotFoundError` 转换 | P0 | 人工审阅 `tests/unit/test_process.py` | |
| 5.2.3 | `test_yosys_models.py` 覆盖：`verilog_files=[]` 时 Pydantic 验证失败 | P0 | `grep -n 'empty\|ValidationError' tests/unit/test_yosys_models.py` | |
| 5.2.4 | `test_yosys_scripts.py` 覆盖：脚本模板格式化后不含未替换的 `{placeholder}` | P1 | 人工审阅：测试应 assert 格式化结果不含 `{` 字符 | |
| 5.2.5 | 集成测试使用 `@pytest.mark.integration` 装饰，单元测试使用 `@pytest.mark.unit` | P1 | `grep -rn '@pytest.mark' tests/` 确认标记使用 | |
| 5.2.6 | 集成测试文件首行检查工具可用性（`pytest.importorskip` 或 `skipIf(not shutil.which("yosys"))`） | P1 | `grep -n 'skip\|which' tests/integration/test_yosys_server.py` | |

### 5.3 覆盖率指标

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 5.3.1 | 单元测试覆盖率 ≥80%（DA3 `fail_under = 80`） | P0 | `pytest --cov=src/auto_eda --cov-report=term-missing -m unit` | |
| 5.3.2 | `core/` 模块覆盖率 ≥90%（核心基础设施应高覆盖） | P1 | `pytest --cov=src/auto_eda/core --cov-report=term-missing -m unit` | |
| 5.3.3 | 无测试文件使用 `@pytest.mark.skip`（禁止跳过测试掩盖问题） | P0 | `grep -rn '@pytest.mark.skip\|pytest.skip(' tests/` 应无输出 | |


---

## 维度 6：代码风格与规范一致性

> 规范来源：DA3 §2（ruff 配置）、PLAN6 §5（开发规范速查卡）

### 6.1 格式化与 Lint

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 6.1.1 | `ruff check src/ tests/` 零错误（pycodestyle + pyflakes + bugbear + isort） | P0 | `ruff check src/ tests/` 输出应为空 | |
| 6.1.2 | `ruff format --check src/ tests/` 零 diff（统一引号和缩进） | P0 | `ruff format --check src/ tests/` 应输出 `All files are already formatted` | |
| 6.1.3 | 行长 ≤100 字符（DA3 `line-length = 100`） | P1 | 由 `ruff format` 自动处理；`ruff check` 规则 E501 已豁免 | |
| 6.1.4 | import 按 isort 规则排序（stdlib → third-party → local） | P1 | `ruff check --select I src/` 应无输出 | |

### 6.2 命名规范

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 6.2.1 | 类名使用 PascalCase（`EDAError`, `SynthesizeInput`, `ToolSuccess`） | P1 | `grep -rn '^class ' src/auto_eda/` 人工确认 | |
| 6.2.2 | 函数名和变量名使用 snake_case | P1 | `ruff check --select N` 覆盖此项 | |
| 6.2.3 | 常量使用 UPPER_SNAKE_CASE（如 `SYNTH_SCRIPT_FPGA`, `BACKEND`） | P1 | `grep -rn '^[A-Z_]\+ = ' src/auto_eda/servers/` 人工确认 | |
| 6.2.4 | MCP tool 名称使用下划线分隔（`synthesize_rtl` 而非 `synthesizeRTL`） | P0 | `grep -rn '@mcp.tool\|@server.tool' src/auto_eda/servers/` 确认命名格式 | |

### 6.3 文档字符串

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 6.3.1 | 所有 MCP tool 函数有 docstring（FastMCP 用 docstring 生成 tool 描述，直接暴露给 LLM） | P0 | `grep -B1 'async def' src/auto_eda/servers/*/server.py` 确认每个 tool 函数有 `"""` | |
| 6.3.2 | MCP tool docstring 描述包含：功能描述、主要参数说明、返回格式说明 | P0 | 人工审阅至少 3 个 tool 的 docstring 质量 | |
| 6.3.3 | Pydantic 模型字段使用 `Field(description=...)` 提供说明（用于 MCP schema 生成） | P1 | `grep -rn 'Field(' src/auto_eda/models/' 确认关键字段含 description=` | |

### 6.4 pyproject.toml 合规性

| # | 检查项 | 优先级 | 检查方法 | 结果 |
|---|--------|--------|----------|------|
| 6.4.1 | `requires-python = ">=3.10"` | P0 | `grep 'requires-python' pyproject.toml` | |
| 6.4.2 | `[build-system]` 使用 `hatchling>=1.21` | P0 | `grep -A2 'build-system' pyproject.toml` | |
| 6.4.3 | `[project.scripts]` 定义 4 个入口点（`auto-eda-yosys`, `auto-eda-kicad`, `auto-eda-verilog`, `auto-eda`） | P0 | `grep -A6 'project.scripts' pyproject.toml` | |
| 6.4.4 | `[project.optional-dependencies]` 包含 `pcb`, `ic`, `full`, `dev` 4 个分组 | P1 | `grep -n '\[project.optional' pyproject.toml` | |
| 6.4.5 | `[tool.coverage.report]` 设置 `fail_under = 80` | P0 | `grep 'fail_under' pyproject.toml` | |
| 6.4.6 | pytest markers 注册 4 个：`unit`, `integration`, `slow`, `mcp` | P1 | `grep -A6 'markers' pyproject.toml` | |

---

## 快速执行脚本

代码生成完成后，在项目根目录执行以下脚本进行自动化检查（需已激活 venv）：

```bash
#!/usr/bin/env bash
# AUDIT5 快速自动检查脚本
# 在项目根目录（包含 pyproject.toml）下执行

set -e
echo "=== AUDIT5: AUTO_EDA 代码质量快速检查 ==="
echo ""

echo "[1/6] 项目结构检查..."
for f in \
    src/auto_eda/__init__.py \
    src/auto_eda/__main__.py \
    src/auto_eda/core/errors.py \
    src/auto_eda/core/process.py \
    src/auto_eda/core/result.py \
    src/auto_eda/core/base_server.py \
    src/auto_eda/models/yosys.py \
    src/auto_eda/models/kicad.py \
    src/auto_eda/models/verilog.py \
    src/auto_eda/servers/yosys/server.py \
    src/auto_eda/servers/yosys/synthesizer.py \
    src/auto_eda/servers/yosys/scripts.py \
    src/auto_eda/servers/yosys/parser.py \
    src/auto_eda/servers/kicad/server.py \
    src/auto_eda/servers/kicad/ipc_client.py \
    src/auto_eda/servers/kicad/cli_fallback.py \
    src/auto_eda/servers/kicad/version.py \
    src/auto_eda/servers/verilog_utils/server.py \
    src/auto_eda/servers/verilog_utils/parser.py \
    src/auto_eda/servers/verilog_utils/linter.py \
    pyproject.toml \
    .mcp.json; do
  [ -f "$f" ] && echo "  PASS $f" || echo "  FAIL MISSING: $f"
done

echo ""
echo "[2/6] 安全检查：禁止 shell=True..."
if grep -rn 'shell=True\|os\.system\|subprocess\.run.*shell' src/auto_eda/ 2>/dev/null; then
  echo "  FAIL 发现 shell=True 或等效调用"
else
  echo "  PASS 无 shell=True"
fi

echo ""
echo "[3/6] 安全检查：禁止空 except..."
if grep -rn 'except.*:\s*$' src/auto_eda/ | grep -v '#' | xargs grep -l 'pass' 2>/dev/null; then
  echo "  WARN 请人工核查空 except 块"
else
  echo "  PASS 无明显空 except"
fi

echo ""
echo "[4/6] 模块边界检查：core/ 不引用 EDA 库..."
if grep -rn 'import yosys\|import kicad\|import pyverilog\|import gdstk' src/auto_eda/core/ 2>/dev/null; then
  echo "  FAIL core/ 模块引用了 EDA 库"
else
  echo "  PASS core/ 无 EDA 库引用"
fi

echo ""
echo "[5/6] Ruff lint 检查..."
ruff check src/ tests/ && echo "  PASS ruff check 通过" || echo "  FAIL ruff check 有错误"

echo ""
echo "[6/6] mypy 类型检查..."
mypy src/auto_eda/ && echo "  PASS mypy 通过" || echo "  FAIL mypy 有类型错误"

echo ""
echo "=== 自动检查完成。请人工核查标记 [FAIL] 的项目 ==="
```

将上述脚本保存为 `scripts/audit_check.sh`，执行前 `chmod +x scripts/audit_check.sh`。

---

## 审计总结模板

代码生成后填写此表格：

| 维度 | P0 项总数 | P0 通过 | P0 失败 | P1 项总数 | P1 通过 | P1 失败 | 结论 |
|------|-----------|---------|---------|-----------|---------|---------|------|
| 1. 项目结构 | 9 | | | 6 | | | |
| 2. 类型注解 | 4 | | | 5 | | | |
| 3. 错误处理 | 9 | | | 5 | | | |
| 4. 安全风险 | 5 | | | 4 | | | |
| 5. 测试覆盖 | 6 | | | 7 | | | |
| 6. 代码风格 | 8 | | | 9 | | | |
| **合计** | **41** | | | **36** | | | |

**发布门控条件**：所有 P0 项 PASS 方可进入 Week 2 迭代。P1 项允许带 issue 跟踪进入下一迭代。

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 初始清单，基于 DA3 + PLAN6 生成；源码尚未生成，为执行前置版 |
