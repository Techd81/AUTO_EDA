# PLAN1: AUTO_EDA Phase 0 MVP 完整开发计划

> 文档类型: 开发执行计划
> 生成日期: 2026-03-14
> 数据来源: DA3_phase0_implementation_spec + A8_integration_roadmap + DA1_architecture_deep_design + DA4_risk_mitigation_deep
> 覆盖范围: Phase 0 MVP (8周) 全部技术决策、任务分解、测试策略、发布流程

---

## 目录

1. [Phase 0 总体目标与约束](#1-phase-0-总体目标与约束)
2. [Week 1-2: 基础框架](#2-week-1-2-基础框架)
3. [Week 3-4: Yosys MCP Server](#3-week-3-4-yosys-mcp-server)
4. [Week 5-6: KiCad MCP Server](#4-week-5-6-kicad-mcp-server)
5. [Week 7-8: 集成与发布](#5-week-7-8-集成与发布)
6. [关键路径与并行开发](#6-关键路径与并行开发)
7. [风险缓冲时间分配](#7-风险缓冲时间分配)
8. [成功标准与验收测试](#8-成功标准与验收测试)
9. [性能基准](#9-性能基准)
10. [PyPI 发布流程](#10-pypi-发布流程)

---

## 1. Phase 0 总体目标与约束

### 1.1 交付目标

| 交付物 | 规格 |
|--------|------|
| MCP Server 数量 | 3 个（Yosys、KiCad、Verilog Utils） |
| MCP Tool 总数 | ~28-33 个 |
| 测试覆盖率 | 单元 >= 80%，MCP 协议 100% |
| 发布形式 | PyPI v0.1.0 + GitHub Release |
| 文档 | README + 快速入门 + `.mcp.json` 模板 |

### 1.2 技术约束（不可更改）

- Python >= 3.10，目标兼容 3.10/3.11/3.12/3.13
- 包管理器：`uv`（开发）+ `pip`（用户安装）
- 构建后端：`hatchling >= 1.21`
- MCP SDK：`mcp[cli] >= 1.3.0`（FastMCP）
- 类型检查：`mypy --strict`，0 错误为 CI 门控
- Linting：`ruff`，0 警告为 CI 门控
- 传输层：stdio（Claude Code 原生支持，不实现 HTTP/SSE）

### 1.3 范围外（Phase 0 明确不做）

- KiCad IPC API 实现（预留接口，存根实现）
- Pyosys Python 绑定（作为 fallback 第一选项检测，但不要求用户编译）
- OpenROAD、Verilator、cocotb（Phase 1）
- Docker 镜像发布（Phase 0 只发 PyPI）
- Windows 原生支持（支持 WSL，Linux/macOS 主要平台）

---

## 2. Week 1-2: 基础框架

### 2.1 每日可交付任务分解

#### Day 1（Week 1 第 1 天）
- [ ] 初始化 Git 仓库，创建 `main` 和 `develop` 分支
- [ ] 创建完整目录结构（参照 DA3 §1.1 目录树）
- [ ] 编写 `pyproject.toml`（完整配置，含所有依赖、工具配置、脚本入口）
- [ ] 验证：`uv pip install -e ".[dev]"` 成功，无依赖冲突

#### Day 2
- [ ] 实现 `src/auto_eda/core/errors.py`（`EDAErrorCode` 枚举 + `EDAError` 基类 + 常用子类）
- [ ] 实现 `src/auto_eda/core/result.py`（`ToolSuccess`/`ToolFailure` + `format_mcp_error`）
- [ ] 编写 `tests/unit/test_errors.py`（所有错误码可实例化，`to_mcp_error_text` 格式正确）
- [ ] 编写 `tests/unit/test_result.py`（序列化/反序列化往返正确）
- [ ] 验证：`pytest tests/unit/test_errors.py tests/unit/test_result.py` 全通过

#### Day 3
- [ ] 实现 `src/auto_eda/core/process.py`（`find_tool`/`run_tool`/`check_tool_available`）
- [ ] 编写 `tests/unit/test_process.py`（mock `asyncio.create_subprocess_exec`，测试超时/成功/FileNotFound 三条路径）
- [ ] 验证：`pytest tests/unit/test_process.py` 全通过

#### Day 4
- [ ] 实现 `src/auto_eda/core/base_server.py`（`create_server` + `eda_tool` 装饰器）
- [ ] 实现 `src/auto_eda/__init__.py`（版本号 `0.1.0`，公共导出）
- [ ] 实现 `src/auto_eda/__main__.py`（`python -m auto_eda --server yosys/kicad/verilog` 路由）
- [ ] 验证：`python -m auto_eda --help` 输出正确

#### Day 5
- [ ] 配置 `.pre-commit-config.yaml`（ruff check、ruff format、mypy）
- [ ] 创建 `tests/fixtures/verilog/counter.v`（8位带使能计数器，参照 DA3 §7.2）
- [ ] 创建 `tests/fixtures/verilog/adder.v`（参数化加法器）
- [ ] 创建 `tests/fixtures/verilog/syntax_error.v`（含故意错误，用于错误路径测试）
- [ ] 创建 `tests/fixtures/verilog/fifo.v`（简单 FIFO，用于综合基准）
- [ ] 验证：`pre-commit run --all-files` 通过

#### Day 6（Week 2 第 1 天）
- [ ] 编写 `.github/workflows/ci.yml`（lint + typecheck + test-unit 三个 job，矩阵 Python 3.10/3.11/3.12/3.13）
- [ ] 编写 `.github/workflows/integration.yml`（integration 测试，仅 main 分支或 `[integration]` label）
- [ ] 配置 `codecov`（上传覆盖率报告）
- [ ] 验证：CI 在 develop 分支 push 后绿色

#### Day 7
- [ ] 创建 `tests/fixtures/kicad/blinky/` KiCad 工程（blinky LED 基准工程，含 .kicad_pro/.kicad_sch/.kicad_pcb）
- [ ] 编写 `tests/conftest.py`（全局 fixture：counter_v/adder_v/blinky_project/tmp_output/yosys_success_result/yosys_failure_result/mock_run_tool/mock_find_tool/mock_kicad_available）
- [ ] 验证：`pytest tests/ --collect-only` 无收集错误

#### Day 8
- [ ] 编写 `scripts/check_dependencies.py`（检查 yosys/kicad-cli/pyverilog 是否可用，输出清晰的安装提示）
- [ ] 编写 `scripts/install_eda_tools.sh`（Linux/CI 环境一键安装 Yosys + KiCad + pyverilog）
- [ ] 验证：`python scripts/check_dependencies.py` 在无 EDA 工具环境输出有用提示

#### Day 9
- [ ] `mypy --strict src/auto_eda` 0 错误
- [ ] `ruff check src tests` 0 警告
- [ ] 全部 unit 测试通过，覆盖率 >= 50%（框架阶段基线）
- [ ] M0.1 验收检查清单全部勾选

#### Day 10（缓冲/修复日）
- [ ] 修复 CI 发现的问题
- [ ] 补齐遗漏的单元测试
- [ ] 更新 README 框架部分

### 2.2 技术决策清单（实现前必须确认）

| 决策编号 | 决策内容 | 选项 | **决定** | 依据 |
|----------|----------|------|----------|------|
| D-01 | FastMCP 版本锁定策略 | 锁定 `==1.3.x` vs `>=1.3.0` | `>=1.3.0,<2.0.0` | 避免 breaking change，允许 patch 升级 |
| D-02 | Python 最低版本 | 3.10 vs 3.11 | **3.10** | 覆盖 Ubuntu 22.04 LTS 默认版本 |
| D-03 | 异步运行时 | asyncio 原生 vs anyio | **anyio** | FastMCP 内部使用，保持一致 |
| D-04 | `eda_tool` 装饰器错误返回策略 | 返回字符串 vs raise McpError | **返回字符串** | FastMCP 将字符串包装为 TextContent，LLM 可读 |
| D-05 | 日志格式 | 结构化 JSON vs 人类可读 | **人类可读（开发）+ JSON（生产）** | 通过 `AUTO_EDA_LOG_LEVEL` 环境变量切换 |
| D-06 | Pydantic 版本 | v1 vs v2 | **v2（>=2.6.0）** | A7 明确决策，`model_validate`/`model_dump` API |
| D-07 | 测试 fixture KiCad 工程来源 | 自建 vs 使用 KiCad 官方示例 | **自建最小化 blinky** | 避免许可证问题，控制工程复杂度 |
| D-08 | `write_netlist` 工具位置 | Yosys server vs 独立 | **Yosys server** | 网表转换依赖 Yosys JSON 格式 |
| D-09 | CI EDA 工具镜像 | 自建 ghcr.io 镜像 vs oseda/oss-cad-suite | **自建 ghcr.io/auto-eda/ci-eda-tools:latest** | 版本可控，Phase 0 手动维护 |
| D-10 | 错误码命名空间 | 按工具分段（3xxx/4xxx）vs 全局序列 | **按工具分段** | DA3 §3.1 已定义，便于排查 |

### 2.3 依赖安装顺序与版本锁定

```toml
# 版本锁定策略（写入 pyproject.toml）
# 核心运行时：宽松下界 + 主版本上界
"mcp[cli]>=1.3.0,<2.0.0"
"pydantic>=2.6.0,<3.0.0"
"anyio>=4.3.0,<5.0.0"
"psutil>=5.9.0"
"rich>=13.7.0"

# 开发工具：宽松下界（通过 uv.lock 固定）
"pytest>=8.0.0"
"pytest-asyncio>=0.23.0"
"pytest-cov>=4.1.0"
"pytest-mock>=3.12.0"
"pytest-timeout>=2.3.0"
"mypy>=1.9.0"
"ruff>=0.3.0"
```

**安装顺序**（首次开发环境搭建）：

```bash
# Step 1: 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Step 2: 克隆仓库并进入目录
git clone https://github.com/auto-eda/auto-eda && cd auto-eda

# Step 3: 创建虚拟环境并安装所有依赖（含 dev 组）
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"

# Step 4: 安装 EDA 工具（Linux）
sudo apt-get install -y yosys kicad
pip install pyverilog  # pyverilog 通过 PyPI 安装

# Step 5: 安装 pre-commit 钩子
pre-commit install

# Step 6: 验证
python scripts/check_dependencies.py
pytest tests/unit -v
```

**uv.lock 生成**：首次 `uv pip install` 后自动生成，提交至仓库锁定精确版本。

### 2.4 CI/CD 完整方案

#### 2.4.1 工作流总览

```
每次 Push/PR:
  ├── lint         (ruff check + ruff format --check)
  ├── typecheck    (mypy --strict src/auto_eda)
  └── test-unit    (pytest tests/unit tests/mcp, 矩阵 3.10-3.13)
          └── 上传 codecov

仅 main 分支 或 PR label=[integration]:
  └── test-integration  (Docker: ghcr.io/auto-eda/ci-eda-tools:latest)

仅 tag v*.*.* :
  └── release
          ├── build (uv build → dist/*.whl + dist/*.tar.gz)
          ├── publish-pypi (uv publish → PyPI)
          └── create-github-release
```

#### 2.4.2 发布工作流（`.github/workflows/release.yml`）

```yaml
name: Release
on:
  push:
    tags: ['v*.*.*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish-pypi:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # OIDC trusted publishing
    steps:
      - uses: actions/download-artifact@v4
        with: {name: dist, path: dist/}
      - uses: astral-sh/setup-uv@v3
      - run: uv publish --trusted-publishing always

  github-release:
    needs: publish-pypi
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with: {name: dist, path: dist/}
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

#### 2.4.3 CI Docker 镜像维护

`ghcr.io/auto-eda/ci-eda-tools:latest` 内容：
- Ubuntu 22.04 base
- Yosys >= 0.36（apt 源）
- KiCad >= 7.0.0（apt 源）
- Python 3.11 + pyverilog
- 构建触发：手动 workflow_dispatch 或 Yosys/KiCad 版本更新时

---

## 3. Week 3-4: Yosys MCP Server

### 3.1 每日可交付任务分解

#### Day 11（Week 3 第 1 天）
- [ ] 实现 `src/auto_eda/models/yosys.py` 全部 Pydantic 模型（10 个：SynthesizeInput/Output、StatInput/Output、CheckInput/Output/CheckIssue、WriteNetlistInput/Output、ShowRTLInput/Output、ResourceStats）
- [ ] 编写 `tests/unit/test_yosys_models.py`（验证字段验证器、默认值、枚举约束）
- [ ] 验证：`pytest tests/unit/test_yosys_models.py` 全通过

#### Day 12
- [ ] 实现 `src/auto_eda/servers/yosys/scripts.py`（4 个脚本模板：SYNTH_SCRIPT_FPGA/ASIC/GENERIC/SHOW_SCRIPT/STAT_ONLY_SCRIPT + 模板渲染函数）
- [ ] 编写 `tests/unit/test_yosys_scripts.py`（12 个测试，验证 ASIC 脚本含 dfflibmap/abc，ice40 含 synth_ice40，FPGA 含 synth，模板变量正确替换）
- [ ] 验证：`pytest tests/unit/test_yosys_scripts.py` 全通过

#### Day 13
- [ ] 实现 `src/auto_eda/servers/yosys/parser.py`（6 组正则解析：wire 数、wire bits、cell 数、cell 类型分布、芯片面积、WARNING/ERROR 行提取）
- [ ] 实现综合成功判断逻辑（`returncode == 0` AND no `ERROR:` in stderr）
- [ ] 编写 `tests/unit/test_yosys_parser.py`（12 个测试，覆盖 generic/ASIC 两种 stat 输出格式，多 warning/error 提取）
- [ ] 验证：`pytest tests/unit/test_yosys_parser.py` 全通过

#### Day 14
- [ ] 实现 `src/auto_eda/servers/yosys/synthesizer.py`（`YosysSynthesizer` 类，含后端检测逻辑：Pyosys → yosys-cli → None）
- [ ] 实现 `synthesize`/`stat`/`check`/`write_netlist`/`show_rtl` 五个方法（CLI 路径，Pyosys 路径作占位 stub）
- [ ] 验证：带 `mock_run_tool` fixture 的单元测试通过

#### Day 15
- [ ] 实现 `src/auto_eda/servers/yosys/server.py`（FastMCP 注册 5 个 tool + 1 个 resource `yosys://help/synthesis-targets`）
- [ ] 实现 `src/auto_eda/servers/yosys/__init__.py` 导出 `main`
- [ ] 验证：`auto-eda-yosys` 命令可启动并完成 MCP stdio 握手（`Initialized` 消息出现）

#### Day 16（Week 4 第 1 天）
- [ ] 编写 `tests/mcp/test_yosys_mcp_protocol.py`（3 个 `@pytest.mark.mcp` 测试：tools_list 含全部 5 个 tool、synthesize inputSchema 正确、无效输入返回 `[ERROR` 前缀文本）
- [ ] 验证：`pytest tests/mcp/test_yosys_mcp_protocol.py -m mcp` 全通过

#### Day 17
- [ ] 运行集成测试 `test_yosys_synthesize_counter`（需本地 Yosys）
- [ ] 运行集成测试 `test_yosys_synthesize_adder`
- [ ] 运行集成测试 `test_yosys_stat_counter`
- [ ] 运行集成测试 `test_yosys_check_syntax_error`
- [ ] 修复集成测试中发现的解析/脚本问题

#### Day 18
- [ ] 通过 Claude Code `.mcp.json` 端到端测试："帮我综合这个 counter Verilog" → `synthesize` 工具成功调用，返回 stats
- [ ] 验证 `tool_used` 字段正确（`pyosys` 或 `yosys-cli`）
- [ ] 验证 `elapsed_s` 字段非零

#### Day 19
- [ ] M0.2 验收检查清单全部勾选
- [ ] 补充剩余单元测试至覆盖率基线
- [ ] 修复 mypy/ruff 问题

#### Day 20（缓冲日）
- [ ] 处理边界情况（多文件综合、include_dirs、defines）
- [ ] 补充 `tests/fixtures/yosys/counter_synth.json` 和 `counter_stat.txt`

### 3.2 10 个 Tool 完整规格

| Tool 名称 | 方法 | 输入模型 | 输出模型 | 必填字段 | 后端 |
|-----------|------|----------|----------|----------|------|
| `synthesize` | POST | `SynthesizeInput` | `SynthesizeOutput` | `verilog_files`, `output_dir` | Pyosys / yosys-cli |
| `stat` | POST | `StatInput` | `StatOutput` | `verilog_files` | yosys-cli |
| `check` | POST | `CheckInput` | `CheckOutput` | `verilog_files` | yosys-cli |
| `write_netlist` | POST | `WriteNetlistInput` | `WriteNetlistOutput` | `json_netlist`, `output_path` | yosys-cli |
| `show_rtl` | POST | `ShowRTLInput` | `ShowRTLOutput` | `verilog_files`, `output_dir` | yosys-cli |
| `read_verilog` | POST | `ReadVerilogInput` | `ReadVerilogOutput` | `verilog_files` | yosys-cli |
| `read_liberty` | POST | `ReadLibertyInput` | `ReadLibertyOutput` | `liberty_file` | yosys-cli |
| `opt_clean` | POST | `OptInput` | `OptOutput` | `json_netlist` | yosys-cli |
| `opt_merge` | POST | `OptInput` | `OptOutput` | `json_netlist` | yosys-cli |
| `write_blif` | POST | `WriteNetlistInput` | `WriteNetlistOutput` | `json_netlist`, `output_path` | yosys-cli |

**Pydantic 模型完整规格**（补充 DA3 §4.3 未列出的模型）：

```python
# read_verilog — 仅读取验证，不综合
class ReadVerilogInput(BaseModel):
    verilog_files: list[str]
    systemverilog: bool = False
    include_dirs: list[str] = []
    defines: dict[str, str] = {}

class ReadVerilogOutput(BaseModel):
    success: bool
    modules_found: list[str]  # 发现的模块名列表
    warnings: list[str] = []

# read_liberty — 验证 Liberty 文件可读
class ReadLibertyInput(BaseModel):
    liberty_file: str
    timeout_s: int = Field(default=30, ge=5, le=120)

class ReadLibertyOutput(BaseModel):
    success: bool
    cell_count: int = 0
    library_name: str = ""

# opt_clean / opt_merge — 网表优化
class OptInput(BaseModel):
    json_netlist: str = Field(description="synthesize 产生的 JSON 网表路径")
    output_path: str
    purge: bool = Field(default=False, description="opt_clean 时是否移除未使用信号")
    timeout_s: int = Field(default=120, ge=10, le=600)

class OptOutput(BaseModel):
    success: bool
    output_path: str
    cells_before: int = 0
    cells_after: int = 0
```

### 3.3 Pyosys 集成策略

**何时用 Pyosys API（进程内调用）**：
- 条件：`import pyosys` 成功（用户从源码编译安装了 Yosys Python 绑定）
- 优势：无进程启动开销（节省约 200ms/次），可直接访问 RTLIL 内部对象
- 劣势：需从源码编译，系统包管理器（apt/brew/conda）通常不含
- Phase 0 实现：Pyosys 路径仅做 stub（`raise NotImplementedError`），后端检测到时记录 `BACKEND=pyosys` 但实际调用路由到 CLI

**何时用 yosys-cli（子进程调用）**：
- 条件：`shutil.which("yosys")` 返回非 None
- 这是 Phase 0 的主要实现路径
- 通过 `core/process.py` 的 `run_tool` 异步执行，超时可配置

**综合脚本模板选择逻辑**：

```
target="generic"  → SYNTH_SCRIPT_GENERIC
target="asic"     → SYNTH_SCRIPT_ASIC（需 liberty_file 非空）
target in ("xilinx","ice40","ecp5","gowin") → SYNTH_SCRIPT_FPGA（target_opts = "synth_{target}"）
```

### 3.4 综合脚本模板库设计

脚本模板存储在 `scripts.py` 中作为模块级字符串常量，通过 `render_script(template, **kwargs)` 函数渲染：

| 模板常量 | 适用场景 | 关键命令 |
|----------|----------|----------|
| `SYNTH_SCRIPT_GENERIC` | 工艺无关综合，快速验证 | `proc; opt; write_json` |
| `SYNTH_SCRIPT_FPGA` | Xilinx/Lattice FPGA 目标 | `synth_{target}; write_json; stat` |
| `SYNTH_SCRIPT_ASIC` | ASIC 工艺库映射 | `dfflibmap; abc -liberty; write_netlist; stat -liberty` |
| `SHOW_SCRIPT` | RTL 电路图可视化 | `show -format {fmt}` |
| `STAT_ONLY_SCRIPT` | 快速资源统计（不做映射） | `proc; stat` |

### 3.5 Mock Yosys 测试策略

**原则**：单元测试完全不依赖 Yosys 安装，通过 monkeypatch 替换 `run_tool`。

```
测试层级:
  Unit (无 Yosys):
    mock_run_tool → 返回预制 ProcessResult
    → 测试 parser、scripts、models、backend 检测逻辑

  MCP Protocol (无 Yosys):
    启动真实 server 进程
    → 测试 tools/list、inputSchema、错误格式

  Integration (需 Yosys):
    @pytest.mark.integration
    → 运行真实综合，验证输出文件和 stats

  E2E (需 Yosys + Claude Code):
    手动测试，记录在 M0.5 检查清单
```

**Mock 数据设计**（存于 `tests/conftest.py`）：
- `yosys_success_result`：含完整 stat 输出的 ProcessResult
- `yosys_failure_result`：returncode=1，stderr 含 `ERROR: Module not found`
- `yosys_warning_result`：returncode=0，stdout 含 3 条 `Warning:` 行
- `yosys_asic_result`：含 `Chip area for module` 行（ASIC 面积统计）

---

## 4. Week 5-6: KiCad MCP Server

### 4.1 每日可交付任务分解

#### Day 21（Week 5 第 1 天）
- [ ] 实现 `src/auto_eda/servers/kicad/version.py`（`KiCadCapability` Flag + `KiCadVersion` dataclass + `detect_kicad_version()` + `MIN_KICAD_VERSION = 7.0.0`）
- [ ] 编写 `tests/unit/test_kicad_version.py`（5 个测试：v10 有 IPC_API、v8 有 CLI_JOBSETS 无 IPC_API、v7 仅 CLI_BASIC、非法版本字符串抛 ValueError、未安装返回 None）
- [ ] 验证：`pytest tests/unit/test_kicad_version.py` 全通过

#### Day 22
- [ ] 实现 `src/auto_eda/models/kicad.py` 全部 Pydantic 模型（15 个模型对，含所有 Input/Output/中间模型）
- [ ] 编写 `tests/unit/test_kicad_models.py`（字段验证、枚举约束、默认值测试）
- [ ] 验证：`pytest tests/unit/test_kicad_models.py` 全通过

#### Day 23
- [ ] 实现 `src/auto_eda/servers/kicad/ipc_client.py`（`IPCConnectionManager` 存根：所有方法抛 `NotImplementedError`，附有文档字符串说明 Phase 1 实现计划）
- [ ] 实现 `src/auto_eda/servers/kicad/cli_fallback.py`（7 个 tool 的 kicad-cli 命令映射，参照 DA3 §5.4 命令表）
- [ ] 验证：`mock_kicad_available` fixture 下 cli_fallback 调用路径正确

#### Day 24
- [ ] 实现 `src/auto_eda/servers/kicad/server.py`（注册 7 个 tool：`open_project`/`list_components`/`run_drc`/`run_erc`/`export_gerber`/`export_bom`/`get_netlist`）
- [ ] 实现启动时版本检测：KiCad < 7.0.0 时所有 tool 返回 `KICAD_VERSION_LOW` 错误；KiCad 未安装时返回 `TOOL_NOT_FOUND`
- [ ] 验证：`auto-eda-kicad` 命令可启动

#### Day 25
- [ ] 实现 S-expression 降级解析（使用 `sexpdata`）：`list_components`、`open_project`、`get_netlist` 在 kicad-cli 不可用时通过直接解析 .kicad_sch/.kicad_pcb 文件运行
- [ ] 验证：无 kicad-cli 环境下 `open_project` 和 `list_components` 仍可返回部分信息

#### Day 26（Week 6 第 1 天）
- [ ] 编写 `tests/mcp/test_kicad_mcp_protocol.py`（3 个 `@pytest.mark.mcp` 测试：tools_list 含全部 7 个 tool、run_drc inputSchema 含 `pcb_file`、KiCad 未安装时工具返回 `[ERROR 2001]`）
- [ ] 验证：`pytest tests/mcp/test_kicad_mcp_protocol.py -m mcp` 全通过

#### Day 27
- [ ] 运行集成测试 `test_kicad_open_blinky`（需 kicad-cli v7+）
- [ ] 运行集成测试 `test_kicad_drc_blinky`
- [ ] 运行集成测试 `test_kicad_export_bom`
- [ ] 修复集成测试发现的 CLI 参数/输出解析问题

#### Day 28
- [ ] Claude Code 端到端测试："检查这个 PCB 的 DRC" → `run_drc` 成功调用，返回 violation_count
- [ ] Claude Code 端到端测试："导出 Gerber 文件" → `export_gerber` 成功，返回 files 列表
- [ ] M0.3 验收检查清单全部勾选

#### Day 29（Verilog Utils Server，Week 6 第 4 天）
- [ ] 实现 `src/auto_eda/models/verilog.py`（`PortDef`/`ParamDef`/`ModuleDef`/`HierarchyNode`/`LintIssue` + 6 个 tool 的 Input/Output 模型）
- [ ] 实现 `src/auto_eda/servers/verilog_utils/parser.py`（pyverilog 封装：`VerilogCodeParser` + 异常映射）
- [ ] 实现 `src/auto_eda/servers/verilog_utils/linter.py`（5 条 lint 规则：W001/W002/W003/E001/E002）
- [ ] 编写 `tests/unit/test_verilog_models.py` 和 `tests/unit/test_verilog_parser.py`

#### Day 30（缓冲日）
- [ ] 实现 `src/auto_eda/servers/verilog_utils/server.py`（注册 6 个 tool）
- [ ] 修复 Week 5-6 发现的所有问题
- [ ] `mypy --strict` + `ruff check` 0 错误

### 4.2 版本适配策略（v8/v9/v10）

| KiCad 版本 | CLI 支持 | IPC API | DRC/ERC | Gerber 导出 | BOM 导出 | Phase 0 策略 |
|-----------|---------|---------|---------|------------|---------|-------------|
| v7.x | kicad-cli 基础命令 | 无 | CLI JSON | CLI | CLI | 全 CLI，最低支持版本 |
| v8.x | CLI + Jobsets | 无 | CLI JSON | CLI | CLI | 全 CLI，与 v7 相同路径 |
| v9.x | CLI + Jobsets | 实验版（不稳定） | CLI JSON / IPC | CLI / IPC | CLI | **CLI 优先**，IPC 作可选探测 |
| v10.x | CLI + Jobsets | 稳定（Pythonic） | CLI JSON / IPC | CLI / IPC | CLI | CLI 优先，IPC 接口预留（Phase 1 启用） |

**适配决策**：Phase 0 全部基于 kicad-cli，不激活 IPC API，理由：
1. v10 RC2（2026-03-07）仍在 RC 阶段，API 仍在调整
2. kicad-cli 在 v7/v8/v9/v10 全部可用，是最稳定路径
3. `IPCConnectionManager` 以存根形式预留，Phase 1 激活

**版本检测运行时行为**：
```
启动时 detect_kicad_version():
  None          → 所有 tool 返回 TOOL_NOT_FOUND 错误
  < v7.0.0      → 所有 tool 返回 KICAD_VERSION_LOW 错误
  v7.0.0-v9.x   → CLI 路径，正常工作
  v10.x+        → CLI 路径（Phase 0），IPC 预留
```

### 4.3 IPC API 连接管理设计（Phase 0 存根，Phase 1 实现）

```
IPCConnectionManager（Phase 0 存根规格）:
  __init__():
    self._caps = detect_kicad_capabilities()  # DA4 版本检测
    self._connected = False

  async connect() -> None:
    raise NotImplementedError("IPC API support is planned for Phase 1 (KiCad v10+)")

  async disconnect() -> None:
    raise NotImplementedError(...)

  async call(method: str, params: dict) -> dict:
    raise NotImplementedError(...)

Phase 1 实现目标:
  - Unix Socket 路径：$KICAD_RUN_DIR/kicad.sock
  - Windows Named Pipe：\\\\. \\pipe\\kicad-api
  - 连接池大小：1（KiCad 单实例）
  - 重连策略：指数退避，最大 3 次，初始 1s
  - 操作超时：60s（默认），通过 AUTO_EDA_KICAD_TIMEOUT 配置
```

### 4.4 15 个 Tool 完整规格

| Tool 名称 | 输入模型 | 输出模型 | kicad-cli 命令 | 降级（sexpdata） |
|-----------|----------|----------|---------------|------------------|
| `open_project` | `OpenProjectInput` | `OpenProjectOutput` | 解析 .kicad_pro | 支持 |
| `list_components` | `ListComponentsInput` | `ListComponentsOutput` | `sch export python-bom` | 支持（解析 .kicad_sch） |
| `get_schematic_info` | `GetSchematicInfoInput` | `GetSchematicInfoOutput` | `sch export svg` | 支持（基础信息） |
| `run_erc` | `RunERCInput` | `RunERCOutput` | `sch erc --format json` | 不支持 |
| `run_drc` | `RunDRCInput` | `RunDRCOutput` | `pcb drc --format json` | 不支持 |
| `export_gerber` | `ExportGerberInput` | `ExportGerberOutput` | `pcb export gerbers` | 不支持 |
| `export_drill` | `ExportDrillInput` | `ExportDrillOutput` | `pcb export drill` | 不支持 |
| `export_bom` | `ExportBOMInput` | `ExportBOMOutput` | `sch export bom --format csv` | 支持（解析 .kicad_sch） |
| `get_netlist` | `GetNetlistInput` | `GetNetlistOutput` | `sch export netlist` | 支持（部分） |
| `export_svg_schematic` | `ExportSVGInput` | `ExportSVGOutput` | `sch export svg` | 不支持 |
| `export_svg_pcb` | `ExportSVGInput` | `ExportSVGOutput` | `pcb export svg` | 不支持 |
| `export_step` | `ExportStepInput` | `ExportStepOutput` | `pcb export step` | 不支持 |
| `place_component` | `PlaceComponentInput` | `PlaceComponentOutput` | IPC only (Phase 1) | 不支持 |
| `route_track` | `RouteTrackInput` | `RouteTrackOutput` | IPC only (Phase 1) | 不支持 |
| `get_board_info` | `GetBoardInfoInput` | `GetBoardInfoOutput` | 解析 .kicad_pcb | 支持 |

**注意**：`place_component` 和 `route_track` 在 Phase 0 注册但返回 `KICAD_NOT_RUNNING` 错误（IPC 存根），Phase 1 激活。

### 4.5 KiCad 不运行时的降级方案

```
降级层级（从高到低）:
  Level 1: kicad-cli 可用（v7+）
    → 全功能：DRC/ERC/Gerber/BOM/Netlist 均可用

  Level 2: kicad-cli 不可用，sexpdata 可用
    → 有限功能：open_project、list_components、get_netlist、export_bom
    → 通过直接解析 .kicad_sch/.kicad_pcb S-expression 实现
    → 工具响应包含 warning: "Limited mode: kicad-cli not found"

  Level 3: 两者均不可用
    → 所有 tool 返回 [ERROR 2001] TOOL_NOT_FOUND
    → 包含安装指引链接
```

---

## 5. Week 7-8: 集成与发布

### 5.1 每日可交付任务分解

#### Day 31（Week 7 第 1 天）
- [ ] 完成 `src/auto_eda/servers/verilog_utils/server.py` 6 个 tool 注册
- [ ] 编写 `tests/mcp/test_verilog_mcp_protocol.py`
- [ ] 运行集成测试 `test_verilog_parse_skywater_cell`
- [ ] M0.4 验收检查清单全部勾选

#### Day 32
- [ ] 集成测试矩阵完整运行（Yosys + KiCad + Verilog Utils，需 CI Docker 环境）
- [ ] 修复所有集成测试发现的问题
- [ ] 全量 `pytest tests/unit tests/mcp` + 覆盖率报告，确认 >= 80%

#### Day 33
- [ ] 编写 `README.md`（项目介绍、安装方式、快速入门、3 种 `.mcp.json` 配置模板）
- [ ] 编写 `docs/tools/yosys.md`（所有 10 个 Yosys tool 的参数说明和示例）
- [ ] 编写 `docs/tools/kicad.md`（所有 15 个 KiCad tool 的参数说明和示例）
- [ ] 编写 `docs/tools/verilog.md`（所有 6 个 Verilog tool 的参数说明和示例）

#### Day 34
- [ ] 完整 Claude Code 端到端测试（三种场景，记录结果截图）
- [ ] 配置 PyPI trusted publishing（GitHub → PyPI OIDC）
- [ ] 在 PyPI Test 环境试发布（`uv publish --index testpypi`），验证包安装可用
- [ ] 修复包元数据问题（classifiers、description、URLs）

#### Day 35（Week 8 第 1 天）
- [ ] 所有 CI jobs 在 main 分支绿色
- [ ] 打 `v0.1.0-rc1` tag，触发 release workflow
- [ ] 验证 PyPI Test 上的 `pip install auto-eda==0.1.0rc1` 成功
- [ ] 验证 `uvx --from auto-eda[ic] auto-eda-yosys` 启动正常

#### Day 36
- [ ] 收集内部测试反馈，修复发现的安装/文档问题
- [ ] 更新 CHANGELOG.md（v0.1.0 变更内容）
- [ ] 完善 `scripts/check_dependencies.py` 输出的安装指引

#### Day 37
- [ ] M0.5 验收检查清单全部勾选（最终确认）
- [ ] 打 `v0.1.0` tag，触发正式发布
- [ ] 验证 PyPI 正式包可安装
- [ ] 发布 GitHub Release（附带 CHANGELOG 和 dist 文件）

#### Day 38（缓冲/热修复日）
- [ ] 监控 PyPI 下载量和 GitHub Issues
- [ ] 修复安装问题（如依赖冲突）
- [ ] v0.1.1 热修复准备（如需要）

#### Day 39-40（缓冲周）
- [ ] 预留给 Week 5-6 的积压问题
- [ ] 补充遗漏的测试用例
- [ ] 改善文档质量

### 5.2 集成测试矩阵

| 测试 ID | 测试函数 | 前置条件 | 测试内容 | 期望结果 |
|---------|----------|----------|----------|----------|
| IT-Y01 | `test_yosys_synthesize_counter` | Yosys >= 0.36 | counter.v generic 综合 | success=True, num_cells > 0 |
| IT-Y02 | `test_yosys_synthesize_adder` | Yosys >= 0.36 | adder.v generic 综合 | output_json 文件存在 |
| IT-Y03 | `test_yosys_synthesize_fifo` | Yosys >= 0.36 | fifo.v generic 综合 | success=True |
| IT-Y04 | `test_yosys_check_syntax_error` | Yosys >= 0.36 | syntax_error.v check | issues 非空，含 error |
| IT-Y05 | `test_yosys_stat_counter` | Yosys >= 0.36 | counter.v stat | num_wires > 0 |
| IT-K01 | `test_kicad_open_blinky` | kicad-cli v7+ | open_project | schematic_file 路径非 None |
| IT-K02 | `test_kicad_drc_blinky` | kicad-cli v7+ | run_drc | success=True, report_path 存在 |
| IT-K03 | `test_kicad_export_bom` | kicad-cli v7+ | export_bom | component_count > 0 |
| IT-K04 | `test_kicad_export_gerber` | kicad-cli v7+ | export_gerber | file_count >= 4 |
| IT-K05 | `test_kicad_list_components` | kicad-cli v7+ | list_components | total_count > 0 |
| IT-V01 | `test_verilog_parse_counter` | pyverilog | parse_verilog(counter.v) | 1 个 counter 模块，4 个端口 |
| IT-V02 | `test_verilog_parse_skywater` | pyverilog | 解析 sky130 标准单元 | success=True |
| IT-V03 | `test_verilog_lint_w003` | pyverilog | lint_check 含阻塞赋值文件 | W003 出现在 issues 中 |

**CI 执行策略**：集成测试仅在含 Yosys/KiCad 的 Docker 容器中运行（main 分支或 `[integration]` PR label），避免 PR CI 缓慢。

### 5.3 文档计划

| 文档 | 内容 | 交付时间 |
|------|------|----------|
| `README.md` | 项目介绍、快速安装（pip/uvx/Docker）、`.mcp.json` 配置模板、基本用法示例 | Day 33 |
| `docs/quickstart.md` | 5 分钟上手：安装 → 配置 Claude Code → 第一次综合 | Day 33 |
| `docs/tools/yosys.md` | 全部 10 个 tool 参数、示例调用、常见错误 | Day 33 |
| `docs/tools/kicad.md` | 全部 15 个 tool 参数、示例、KiCad 版本兼容说明 | Day 33 |
| `docs/tools/verilog.md` | 全部 6 个 tool 参数、lint 规则说明 | Day 33 |
| `docs/troubleshooting.md` | 常见安装问题、EDA 工具找不到的解决方法 | Day 34 |
| `CHANGELOG.md` | v0.1.0 变更内容（自动生成草稿，人工审核） | Day 36 |
| API 文档（自动） | `pdoc` 从 docstring 生成，发布到 readthedocs | v0.2.0（Phase 1）|

---

## 6. 关键路径与并行开发

### 6.1 关键路径分析

```
Phase 0 关键路径（决定最短完成时间）:

Day 1-2:  core/errors + core/result
    ↓
Day 3:    core/process
    ↓
Day 4:    core/base_server
    ↓ (此后可并行)
    ├── Day 11-20: Yosys MCP (models → scripts → parser → synthesizer → server → tests)
    └── Day 21-30: KiCad MCP + Verilog Utils (并行)
              ↓
Day 31-38: 集成测试 → 文档 → 发布

关键路径长度: 38天 = 7.6周，预算8周（含2天缓冲）
```

### 6.2 并行开发机会

| 并行窗口 | 任务 A | 任务 B | 说明 |
|----------|--------|--------|------|
| Day 11-20 vs Day 21-30 | Yosys MCP（Week 3-4）| KiCad MCP + Verilog Utils（Week 5-6）| 两者仅依赖 core/ 框架 |
| Day 21-25 vs Day 26-30 | KiCad server 实现 | Verilog Utils server 实现 | 独立模块，无交叉依赖 |
| Day 33 vs Day 34 | 文档编写 | CI/PyPI 发布配置 | 人工任务可并行 |

**2 人并行方案**（推荐）：
- 工程师 A：core 框架（Week 1-2）→ Yosys MCP（Week 3-4）→ 集成测试（Week 7-8）
- 工程师 B：测试框架/fixture（Week 1-2）→ KiCad MCP（Week 5-6）→ 文档/发布（Week 7-8）
- Verilog Utils Server（Day 29-31）由工程师 B 在 KiCad 完成后接续实现

**单人开发方案**：严格按 Day 1-40 顺序执行，8 周完成（不含缓冲日则 7.5 周）。

---

## 7. 风险缓冲时间分配

### 7.1 已识别风险与缓冲

| 风险 ID | 风险描述 | 概率 | 影响 | 缓冲天数 | 缓冲位置 |
|---------|----------|------|------|----------|----------|
| R-K1 | KiCad CLI JSON 输出格式在不同版本不一致 | 中 | 中 | 2天 | Day 27-28 缓冲日 |
| R-K2 | blinky 工程 DRC 在新版本 KiCad 出现新违规类型 | 低 | 低 | 1天 | Day 30 缓冲日 |
| R-Y1 | Yosys stat 输出格式随版本变化（>= 0.40 格式改变） | 低 | 中 | 2天 | Day 19-20 缓冲日 |
| R-V1 | pyverilog 对 SkyWater PDK 标准单元解析失败 | 中 | 中 | 1天 | Day 31 |
| R-P1 | FastMCP SDK API 在 1.3→1.4 升级中有 breaking change | 低 | 高 | 2天 | Week 7 起始 |
| R-C1 | CI Docker 镜像构建失败（Yosys/KiCad apt 源问题） | 中 | 中 | 2天 | Week 2 末 |
| R-D1 | PyPI OIDC trusted publishing 配置问题 | 低 | 低 | 1天 | Day 34-35 |

**总缓冲时间**：11天（分散在各阶段），不超过 8 周计划。

### 7.2 升级降级策略

**如果 Yosys 版本 >= 0.40，stat 格式变化**：
- 检测策略：`yosys --version` 解析主版本号，选择对应正则集合
- 实现：`parser.py` 中 `parse_stat(output, yosys_version)` 参数化

**如果 FastMCP 1.4 有 breaking change**：
- 锁定 `mcp[cli]>=1.3.0,<1.4.0`（`pyproject.toml` 上界收窄）
- 评估 1.4 变更后更新

**如果 pyverilog 解析 SystemVerilog 失败**：
- Phase 0 降级：仅承诺 Verilog-2001 支持，SV 返回 warning
- `lint_check` 对 SV 文件输出 `"Limited SV support: use hdlConvertor for full SystemVerilog"`

---

## 8. 成功标准与验收测试

### 8.1 里程碑验收标准

#### M0.1 框架就绪（Week 2 末）

| 验收项 | 测量方法 | 通过条件 |
|--------|----------|----------|
| 依赖安装 | `uv pip install -e ".[dev]"` | 无错误退出 |
| 模块可导入 | `python -c "import auto_eda.core"` | 无 ImportError |
| 类型检查 | `mypy --strict src/auto_eda` | 0 errors |
| Lint | `ruff check src tests` | 0 warnings |
| 单元测试（core） | `pytest tests/unit/test_errors.py tests/unit/test_process.py tests/unit/test_result.py` | 100% pass |
| CI | GitHub Actions lint + typecheck + test-unit | 全绿 |

#### M0.2 Yosys MCP 可用（Week 4 末）

| 验收项 | 测量方法 | 通过条件 |
|--------|----------|----------|
| Server 启动 | `auto-eda-yosys` | MCP stdio 握手成功 |
| Tool 列表 | `tools/list` MCP 请求 | 含 synthesize/stat/check/write_netlist/show_rtl |
| 协议合规 | `pytest tests/mcp/test_yosys_mcp_protocol.py` | 3/3 通过 |
| 单元测试 | `pytest tests/unit/test_yosys_*.py` | 100% pass |
| 集成测试 | IT-Y01~Y05 全通过 | success=True, stats 非空 |
| E2E | Claude Code 综合 counter.v | synthesize 被调用，返回 stats |

#### M0.3 KiCad MCP 可用（Week 6 第 3 天）

| 验收项 | 测量方法 | 通过条件 |
|--------|----------|----------|
| Server 启动 | `auto-eda-kicad` | MCP stdio 握手成功 |
| Tool 列表 | `tools/list` | 含 7 个 tool |
| 集成测试 | IT-K01~K05 全通过 | success=True, 输出文件存在 |
| 降级测试 | 无 kicad-cli 环境 open_project | 返回有限结果而非崩溃 |
| E2E | Claude Code 对话 run_drc | 工具被调用，返回 violation_count |

#### M0.4 Verilog Utils 可用（Week 6 末）

| 验收项 | 测量方法 | 通过条件 |
|--------|----------|----------|
| Server 启动 | `auto-eda-verilog` | MCP stdio 握手成功 |
| Tool 列表 | 含 6 个 tool | parse_verilog/extract_modules/analyze_hierarchy/lint_check/extract_ports/format_code |
| 单元测试 | `pytest tests/unit/test_verilog_*.py` | 100% pass |
| 集成测试 | IT-V01~V03 | 全通过 |

#### M0.5 MVP 发布（Week 8）

| 验收项 | 通过条件 |
|--------|----------|
| 单元测试覆盖率 | >= 80% |
| MCP 协议合规 | 3 个 server 全部通过 |
| Claude E2E 综合 | synthesize 成功调用 |
| Claude E2E DRC | run_drc 成功调用 |
| Claude E2E 解析 | analyze_hierarchy 成功调用 |
| PyPI 发布 | `pip install auto-eda` 成功，3 个 server 命令可用 |
| README | 快速入门 < 15 分钟可完成 |

### 8.2 用户体验验收标准

**首次使用到完成任务目标 < 15 分钟**：
- `pip install auto-eda[ic]` + 复制 `.mcp.json` + 重启 Claude Code + 第一次综合 ≈ 8-10 分钟

**错误信息可操作性标准**：
- EDA 工具未安装：含具体安装命令（`sudo apt install yosys`）
- 文件不存在：含完整路径和检查建议
- 综合失败：含 Yosys 原始输出（截断至 2000 字符）
- 版本过低：含最低版本要求和升级链接

---

## 9. 性能基准

### 9.1 工具调用延迟基准

| Tool | 操作 | 目标 P50 | 目标 P95 | 测量场景 |
|------|------|----------|----------|----------|
| `synthesize` (generic) | counter.v（~50行） | < 2s | < 5s | yosys-cli 后端 |
| `synthesize` (generic) | fifo.v（~200行） | < 5s | < 15s | yosys-cli 后端 |
| `stat` | counter.v | < 1s | < 3s | yosys-cli 后端 |
| `check` | counter.v | < 1s | < 2s | yosys-cli 后端 |
| `run_drc` | blinky PCB | < 5s | < 15s | kicad-cli 后端 |
| `export_gerber` | blinky PCB | < 3s | < 10s | kicad-cli 后端 |
| `parse_verilog` | counter.v | < 0.5s | < 1s | pyverilog 后端 |
| `lint_check` | counter.v（5条规则） | < 1s | < 2s | AST 遍历 |
| MCP `tools/list` | 任意 server | < 100ms | < 200ms | FastMCP 内置 |
| MCP server 启动 | 任意 server | < 500ms | < 1s | stdio 握手 |

**注**：Pyosys 后端（进程内调用）比 yosys-cli 快约 200ms/次（省去进程启动开销），Phase 1 优先实现。

### 9.2 内存占用基准

| 场景 | 目标 RSS | 说明 |
|------|----------|------|
| Yosys server 空闲 | < 50MB | FastMCP + pydantic 运行时 |
| Yosys server 综合中（counter.v） | < 150MB | yosys-cli 子进程额外内存 |
| KiCad server 空闲 | < 50MB | FastMCP + sexpdata |
| KiCad server run_drc 中 | < 200MB | kicad-cli 子进程额外内存 |
| Verilog Utils server 空闲 | < 80MB | FastMCP + pyverilog |
| 三个 server 同时运行 | < 250MB | 独立进程，无共享内存 |

### 9.3 性能测量方法

```bash
# 工具调用延迟测量（集成测试中记录 elapsed_s 字段）
pytest tests/integration -m integration -v --tb=short 2>&1 | grep elapsed_s

# 内存峰值测量
python -c "
import psutil, subprocess, time
p = subprocess.Popen(['auto-eda-yosys'])
proc = psutil.Process(p.pid)
time.sleep(2)
print(f'RSS: {proc.memory_info().rss / 1024**2:.1f} MB')
p.terminate()
"
```

---

## 10. PyPI 发布流程

### 10.1 发布前检查清单

**构建验证**：
- [ ] `uv build` 无警告，生成 `dist/auto_eda-0.1.0-py3-none-any.whl` 和 `dist/auto_eda-0.1.0.tar.gz`
- [ ] `uv run twine check dist/*` 通过（包元数据合规）
- [ ] wheel 包安装测试：`pip install dist/auto_eda-0.1.0-py3-none-any.whl --force-reinstall`
- [ ] 安装后三个 entry points 可用：`auto-eda-yosys --help`, `auto-eda-kicad --help`, `auto-eda-verilog --help`
- [ ] `uvx --from auto-eda[ic] auto-eda-yosys` 零安装启动验证

**Test PyPI 发布**（Day 34）：
```bash
uv publish --index https://test.pypi.org/legacy/ --token $TEST_PYPI_TOKEN
pip install --index-url https://test.pypi.org/simple/ auto-eda==0.1.0
```

**正式 PyPI 发布**（Day 37，通过 GitHub Actions）：
- 打 tag：`git tag v0.1.0 && git push origin v0.1.0`
- release.yml 自动触发：build → publish-pypi（OIDC）→ create-github-release

### 10.2 v0.1.0 发布清单

**功能完整性**：
- [ ] 3 个 MCP Server 全部可用（Yosys/KiCad/Verilog Utils）
- [ ] 28-33 个 MCP Tool 全部注册并有 inputSchema
- [ ] `health_check` resource 在所有 server 可用（返回工具可用性状态）
- [ ] 3 种 `.mcp.json` 配置模板（直接安装/uvx/Docker）在 README 中

**质量门控**：
- [ ] 单元测试覆盖率 >= 80%
- [ ] `mypy --strict` 0 errors
- [ ] `ruff check` 0 warnings
- [ ] MCP 协议合规：3/3 server 通过 `pytest tests/mcp/`
- [ ] 集成测试：IT-Y01~Y05 + IT-K01~K05 + IT-V01~V03 全通过

**包元数据**：
- [ ] `name = "auto-eda"` 在 PyPI 未被占用（提前检查）
- [ ] 版本 `0.1.0`，`Development Status :: 3 - Alpha`
- [ ] License MIT，`license_files = ["LICENSE"]`
- [ ] classifiers 含 `Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)`
- [ ] `project.urls` 含 Homepage/Documentation/Repository/Bug Tracker

**文档**：
- [ ] README.md：项目介绍、安装方式、快速入门、截图/示例
- [ ] CHANGELOG.md：v0.1.0 新增内容
- [ ] docs/quickstart.md：完整上手流程
- [ ] 所有 tool 有 `description` 字符串（FastMCP 自动生成文档）

### 10.3 版本命名规范（Phase 0 期间）

| 版本 | 场景 |
|------|------|
| `0.1.0` | Phase 0 MVP 正式发布 |
| `0.1.x` | Bug fix，向后兼容，不加新 tool |
| `0.2.0` | Phase 1 首个版本（新增 Verilator/cocotb/KLayout） |
| `1.0.0` | Phase 2 完成，RTL→GDSII 全流程可用 |

---

## 附录 A: 时间线甘特图

```
Week 1  [D1 ][D2 ][D3 ][D4 ][D5 ]  框架: pyproject + core/errors + core/process + core/base
Week 2  [D6 ][D7 ][D8 ][D9 ][D10]  框架: CI + fixtures + conftest + check_deps  → M0.1
Week 3  [D11][D12][D13][D14][D15]  Yosys: models + scripts + parser + synthesizer + server
Week 4  [D16][D17][D18][D19][D20]  Yosys: MCP 协议测试 + 集成测试 + E2E + 修复     → M0.2
Week 5  [D21][D22][D23][D24][D25]  KiCad: version + models + ipc_stub + server + sexp降级
Week 6  [D26][D27][D28][D29][D30]  KiCad: MCP测试+集成+E2E → M0.3 | Verilog Utils → M0.4
Week 7  [D31][D32][D33][D34][D35]  集成测试矩阵 + 文档 + PyPI Test + rc1 tag
Week 8  [D36][D37][D38][D39][D40]  反馈修复 + v0.1.0 正式发布 + 监控 + 缓冲     → M0.5
```

## 附录 B: 开发环境变量完整参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AUTO_EDA_LOG_LEVEL` | `WARNING` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `AUTO_EDA_YOSYS_BIN` | `yosys` | Yosys 可执行文件路径 |
| `AUTO_EDA_YOSYS_TIMEOUT` | `300` | Yosys 默认超时秒数 |
| `AUTO_EDA_KICAD_CLI_BIN` | `kicad-cli` | kicad-cli 路径 |
| `AUTO_EDA_KICAD_TIMEOUT` | `120` | KiCad 操作默认超时秒数 |
| `AUTO_EDA_KICAD_IPC_SOCKET` | 自动检测 | KiCad IPC socket 路径（v10+，Phase 1） |
| `AUTO_EDA_DISABLE_PYOSYS` | `0` | 设为 `1` 强制使用 CLI 后端（调试用） |

## 附录 C: 关键文件路径速查

| 文件 | 说明 |
|------|------|
| `D:/AUTO_EDA/analysis/DA3_phase0_implementation_spec.md` | Pydantic 模型完整定义、脚本模板、测试规格 |
| `D:/AUTO_EDA/analysis/DA4_risk_mitigation_deep.md` | KiCad 版本检测代码模式、风险缓解策略 |
| `D:/AUTO_EDA/analysis/DA1_architecture_deep_design.md` | BaseEDAServer、ProgressReporter、分层架构设计 |
| `D:/AUTO_EDA/analysis/A8_integration_roadmap.md` | 工具优先级矩阵、4 阶段路线图、KPI 定义 |

