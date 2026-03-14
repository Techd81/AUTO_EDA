# PLAN3: AUTO_EDA 完整测试策略与质量保证计划

> 文档类型: QA 规划文档
> 生成日期: 2026-03-14
> 规划师: QA 规划团队
> 数据来源: DA3_phase0_implementation_spec.md + DA4_risk_mitigation_deep.md + A7_tech_stack_decision.md + NEW_R3_mcp_quality_guide.md
> 覆盖范围: Phase 0 MVP 全量测试策略 + CI/CD 流水线 + 数据管理 + 质量监控

---

## 目录

1. [四层测试架构详细设计](#1-四层测试架构详细设计)
   - 1.1 Layer 1: 单元测试
   - 1.2 Layer 2: 集成测试
   - 1.3 Layer 3: MCP Inspector 验证
   - 1.4 Layer 4: 端到端测试
2. [CI/CD 测试流水线](#2-cicd-测试流水线)
3. [测试数据管理](#3-测试数据管理)
4. [质量指标和监控](#4-质量指标和监控)

---

## 1. 四层测试架构详细设计

### 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: 端到端测试 (E2E)                                   │
│  Docker + 真实 EDA 工具 + Claude Code 集成                   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: MCP Inspector 验证                                 │
│  协议合规 + Schema 验证 + 手动探索性测试                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 集成测试                                           │
│  FastMCP Client + EDA 工具 Mock + Server 启动测试            │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 单元测试                                           │
│  pytest + Mock + Pydantic 验证 + 覆盖率 ≥ 80%               │
└─────────────────────────────────────────────────────────────┘
```

| 层级 | 工具 | 是否需要 EDA 工具 | 运行频率 | 覆盖目标 |
|------|------|-------------------|----------|----------|
| Layer 1 单元测试 | pytest + pytest-mock | 否 | 每次 commit | 业务逻辑、模型验证、错误路径 |
| Layer 2 集成测试 | pytest + FastMCP Client | Mock (无需真实安装) | 每次 PR | Server 启动、工具调用、数据流 |
| Layer 3 MCP Inspector | npx inspector | 否 (stdio) | 开发时 + 每次 PR | 协议合规、Schema 正确性 |
| Layer 4 E2E | Docker + 真实工具 | 是 | 每次 release | 完整工作流、真实数据 |

---

### 1.1 Layer 1: 单元测试

#### 1.1.1 pytest Fixture 设计 — EDA 工具完整 Mock 方案

```python
# tests/conftest.py
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# 路径 Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def verilog_dir(fixture_dir: Path) -> Path:
    return fixture_dir / "verilog"


@pytest.fixture
def kicad_dir(fixture_dir: Path) -> Path:
    return fixture_dir / "kicad"


@pytest.fixture
def yosys_dir(fixture_dir: Path) -> Path:
    return fixture_dir / "yosys"


@pytest.fixture
def counter_v(verilog_dir: Path) -> Path:
    return verilog_dir / "counter.v"


@pytest.fixture
def adder_v(verilog_dir: Path) -> Path:
    return verilog_dir / "adder.v"


@pytest.fixture
def fifo_v(verilog_dir: Path) -> Path:
    return verilog_dir / "fifo.v"


@pytest.fixture
def syntax_error_v(verilog_dir: Path) -> Path:
    return verilog_dir / "syntax_error.v"


# ---------------------------------------------------------------------------
# ProcessResult Mock Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_process_result_success():
    """模拟 EDA CLI 工具成功执行的 ProcessResult。"""
    from auto_eda.core.process import ProcessResult
    return ProcessResult(returncode=0, stdout="", stderr="", timed_out=False)


@pytest.fixture
def mock_process_result_failure():
    """模拟 EDA CLI 工具执行失败的 ProcessResult。"""
    from auto_eda.core.process import ProcessResult
    return ProcessResult(
        returncode=1,
        stdout="",
        stderr="ERROR: syntax error at line 5",
        timed_out=False,
    )


@pytest.fixture
def mock_process_result_timeout():
    """模拟 EDA CLI 工具超时的 ProcessResult。"""
    from auto_eda.core.process import ProcessResult
    return ProcessResult(returncode=-1, stdout="", stderr="", timed_out=True)


# ---------------------------------------------------------------------------
# Yosys Mock Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def yosys_synth_json(yosys_dir: Path) -> dict:
    """从 fixture 文件加载标准 Yosys 综合 JSON 输出。"""
    with open(yosys_dir / "counter_synth.json") as f:
        return json.load(f)


@pytest.fixture
def mock_yosys_cli(mock_process_result_success, yosys_synth_json):
    """
    Mock yosys CLI 子进程调用。
    通过 patch auto_eda.core.process.run_tool 实现，
    无需系统安装 Yosys。
    """
    mock_result = mock_process_result_success
    mock_result = mock_result.__class__(
        returncode=0,
        stdout=json.dumps(yosys_synth_json),
        stderr="Yosys 0.45 (git sha1 abc123)",
        timed_out=False,
    )
    with patch(
        "auto_eda.core.process.run_tool",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock:
        yield mock


@pytest.fixture
def mock_yosys_not_found():
    """模拟 Yosys 未安装场景。"""
    with patch(
        "auto_eda.core.process.find_tool",
        side_effect=__import__(
            "auto_eda.core.errors", fromlist=["ToolNotFoundError"]
        ).ToolNotFoundError("yosys"),
    ) as mock:
        yield mock


@pytest.fixture
def mock_pyosys_unavailable():
    """模拟 pyosys Python 绑定不可用，强制使用 CLI 后端。"""
    with patch.dict("sys.modules", {"pyosys": None}):
        yield


# ---------------------------------------------------------------------------
# KiCad Mock Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_kicad_capabilities_ipc_v10():
    """模拟 KiCad v10 IPC API 可用的能力探测结果。"""
    from auto_eda.adapters.kicad.version_detect import (
        KiCadApiMode,
        KiCadCapabilities,
    )
    return KiCadCapabilities(
        version_tuple=(10, 0, 0),
        api_mode=KiCadApiMode.IPC_V10,
        has_schematic_api=True,
        has_pcb_api=True,
        has_drc_api=True,
        has_batch_drc=True,
        ipc_socket_path="/tmp/kicad/api.sock",
    )


@pytest.fixture
def mock_kicad_capabilities_cli_only():
    """模拟仅 CLI 可用（KiCad 未运行）的能力探测结果。"""
    from auto_eda.adapters.kicad.version_detect import (
        KiCadApiMode,
        KiCadCapabilities,
    )
    return KiCadCapabilities(
        version_tuple=(9, 0, 2),
        api_mode=KiCadApiMode.CLI_ONLY,
        has_batch_drc=True,
    )


@pytest.fixture
def mock_kicad_unavailable():
    """模拟 KiCad 完全未安装。"""
    from auto_eda.adapters.kicad.version_detect import (
        KiCadApiMode,
        KiCadCapabilities,
    )
    return KiCadCapabilities(
        version_tuple=(0, 0, 0),
        api_mode=KiCadApiMode.UNAVAILABLE,
    )


@pytest.fixture
def mock_kicad_drc_result():
    """标准 KiCad DRC 通过结果（无违规）。"""
    return {
        "violations": [],
        "unconnected_items": [],
        "schematic_errors": [],
    }


@pytest.fixture
def mock_kicad_drc_result_with_violations():
    """标准 KiCad DRC 失败结果（含违规）。"""
    return {
        "violations": [
            {
                "type": "clearance",
                "severity": "error",
                "description": "Track clearance violation",
                "location": {"x": 100.0, "y": 200.0},
            }
        ],
        "unconnected_items": [],
        "schematic_errors": [],
    }


# ---------------------------------------------------------------------------
# Verilog Mock Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pyverilog_ast():
    """模拟 pyverilog 解析成功返回的 AST 对象（轻量 stub）。"""
    ast_stub = MagicMock()
    ast_stub.description.definitions = []
    return ast_stub


@pytest.fixture
def mock_pyverilog_unavailable():
    """模拟 pyverilog 未安装场景。"""
    with patch.dict("sys.modules", {"pyverilog": None, "pyverilog.vparser.parser": None}):
        yield
```

#### 1.1.2 每个 MCP Tool 的测试用例模板

```python
# tests/unit/TEMPLATE_test_mcp_tool.py
#
# 此文件为模板，每个 MCP Tool 应参照此结构编写测试。
# 替换 MODULE / TOOL_FUNC / TOOL_NAME / 参数名。

import pytest
from unittest.mock import AsyncMock, patch


class TestToolTemplate:
    """MCP Tool 单元测试模板 — 每个 Tool 必须覆盖以下 5 类测试。"""

    # -------------------------------------------------------------------
    # T1: 成功路径 (Happy Path)
    # -------------------------------------------------------------------
    @pytest.mark.unit
    async def test_success_with_valid_input(self, mock_yosys_cli, counter_v):
        """正常输入应返回包含预期字段的 ToolSuccess 结构。"""
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl

        result = await synthesize_rtl(
            verilog_files=[str(counter_v)],
            top_module="counter",
            target="generic",
        )
        assert result["success"] is True
        assert "data" in result
        assert "tool_used" in result
        assert result["elapsed_s"] >= 0

    # -------------------------------------------------------------------
    # T2: 错误路径 (Error Path) — 输入无效
    # -------------------------------------------------------------------
    @pytest.mark.unit
    async def test_file_not_found_returns_error(self):
        """不存在的文件路径应返回 FILE_NOT_FOUND 错误码。"""
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl
        from auto_eda.core.errors import EDAErrorCode

        result = await synthesize_rtl(
            verilog_files=["/nonexistent/design.v"],
            top_module="top",
            target="generic",
        )
        assert result["success"] is False
        assert result["error_code"] == EDAErrorCode.FILE_NOT_FOUND

    # -------------------------------------------------------------------
    # T3: 错误路径 — 工具不可用
    # -------------------------------------------------------------------
    @pytest.mark.unit
    async def test_tool_not_found_returns_graceful_error(self, mock_yosys_not_found, counter_v):
        """EDA 工具未安装时应返回 TOOL_NOT_FOUND 而非崩溃。"""
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl
        from auto_eda.core.errors import EDAErrorCode

        result = await synthesize_rtl(
            verilog_files=[str(counter_v)],
            top_module="counter",
            target="generic",
        )
        assert result["success"] is False
        assert result["error_code"] == EDAErrorCode.TOOL_NOT_FOUND
        assert "yosys" in result["error_message"].lower()

    # -------------------------------------------------------------------
    # T4: 边界值 (Boundary)
    # -------------------------------------------------------------------
    @pytest.mark.unit
    async def test_empty_verilog_files_list_rejected(self):
        """空文件列表应被 Pydantic 验证拒绝，不应到达执行层。"""
        from pydantic import ValidationError
        from auto_eda.models.yosys import SynthesisRequest

        with pytest.raises(ValidationError):
            SynthesisRequest(verilog_files=[], top_module="top", target="generic")

    # -------------------------------------------------------------------
    # T5: 超时路径 (Timeout)
    # -------------------------------------------------------------------
    @pytest.mark.unit
    async def test_timeout_returns_timeout_error(self, counter_v):
        """CLI 工具超时应返回 TIMEOUT 错误码，不应 hang 进程。"""
        import asyncio
        from auto_eda.servers.yosys.synthesizer import synthesize_rtl
        from auto_eda.core.errors import EDAErrorCode

        with patch(
            "auto_eda.core.process.run_tool",
            side_effect=__import__(
                "auto_eda.core.errors", fromlist=["ToolTimeoutError"]
            ).ToolTimeoutError("yosys", 300),
        ):
            result = await synthesize_rtl(
                verilog_files=[str(counter_v)],
                top_module="counter",
                target="generic",
            )
        assert result["success"] is False
        assert result["error_code"] == EDAErrorCode.TIMEOUT
```

#### 1.1.3 Pydantic 模型验证测试

```python
# tests/unit/test_yosys_models.py
import pytest
from pydantic import ValidationError

from auto_eda.models.yosys import SynthesisRequest, SynthesisResult


class TestSynthesisRequest:
    """Yosys SynthesisRequest Pydantic 模型验证测试。"""

    @pytest.mark.unit
    def test_valid_generic_target(self):
        req = SynthesisRequest(
            verilog_files=["/path/to/counter.v"],
            top_module="counter",
            target="generic",
        )
        assert req.target == "generic"

    @pytest.mark.unit
    def test_valid_fpga_target(self):
        req = SynthesisRequest(
            verilog_files=["/path/to/counter.v"],
            top_module="counter",
            target="xilinx",
        )
        assert req.target == "xilinx"

    @pytest.mark.unit
    def test_empty_files_list_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            SynthesisRequest(verilog_files=[], top_module="top", target="generic")
        assert "verilog_files" in str(exc_info.value)

    @pytest.mark.unit
    def test_empty_top_module_rejected(self):
        with pytest.raises(ValidationError):
            SynthesisRequest(
                verilog_files=["/path/to/counter.v"],
                top_module="",
                target="generic",
            )

    @pytest.mark.unit
    def test_invalid_target_rejected(self):
        """不在 Literal 枚举中的 target 应被拒绝。"""
        with pytest.raises(ValidationError):
            SynthesisRequest(
                verilog_files=["/path/to/counter.v"],
                top_module="counter",
                target="invalid_vendor",
            )

    @pytest.mark.unit
    def test_nonexistent_file_rejected_by_validator(self):
        """文件路径验证器应检测文件不存在（如启用了 path_must_exist 验证器）。"""
        with pytest.raises(ValidationError):
            SynthesisRequest(
                verilog_files=["/definitely/not/exists.v"],
                top_module="top",
                target="generic",
            )


class TestKiCadDRCRequest:
    """KiCad DRC 请求模型验证测试。"""

    @pytest.mark.unit
    def test_valid_project_path(self, tmp_path):
        from auto_eda.models.kicad import DRCRequest

        proj = tmp_path / "blinky.kicad_pro"
        proj.touch()
        req = DRCRequest(project_path=str(proj))
        assert req.project_path == str(proj)

    @pytest.mark.unit
    def test_wrong_extension_rejected(self, tmp_path):
        from auto_eda.models.kicad import DRCRequest
        from pydantic import ValidationError

        wrong = tmp_path / "blinky.kicad_sch"
        wrong.touch()
        with pytest.raises(ValidationError):
            DRCRequest(project_path=str(wrong))


class TestVerilogParseRequest:
    """Verilog 解析请求模型验证测试。"""

    @pytest.mark.unit
    def test_single_file_valid(self, counter_v):
        from auto_eda.models.verilog import VerilogParseRequest

        req = VerilogParseRequest(verilog_files=[str(counter_v)])
        assert len(req.verilog_files) == 1

    @pytest.mark.unit
    def test_include_dirs_optional(self, counter_v):
        from auto_eda.models.verilog import VerilogParseRequest

        req = VerilogParseRequest(
            verilog_files=[str(counter_v)],
            include_dirs=["/path/to/includes"],
        )
        assert req.include_dirs == ["/path/to/includes"]


#### 1.1.4 错误路径测试

关键测试类 (`tests/unit/test_errors.py`):
- **TestEDAErrorCode**: 所有错误码唯一；Yosys/KiCad/Verilog 各落在 3xxx/4xxx/5xxx 范围
- **TestToolNotFoundError**: message 含工具名，code == TOOL_NOT_FOUND
- **TestToolTimeoutError**: timeout 秒数出现在 message 中
- **TestEDAErrorWithToolOutput**: 长工具输出截断到 2000 字符；detail=None 时输出无 Detail: 前缀

#### 1.1.5 覆盖率目标与例外策略

| 模块 | 目标 | 例外理由 |
|------|------|----------|
| core/errors.py | >= 95% | 纯逻辑 |
| core/process.py | >= 90% | FileNotFoundError OS 分支由 E2E 覆盖 |
| core/result.py | >= 95% | 纯数据结构 |
| models/*.py | >= 95% | Pydantic 验证可充分单元测试 |
| servers/*/server.py | >= 80% | __main__ 入口由 E2E 覆盖 |
| servers/yosys/synthesizer.py | >= 80% | pyosys 内部 API 路径需真实编译 |
| servers/kicad/ipc_client.py | >= 75% | IPC socket 连接需运行中 KiCad |
| servers/kicad/cli_fallback.py | >= 85% | CLI 可完整 mock |
| servers/verilog_utils/parser.py | >= 85% | pyverilog 崩溃路径难以稳定复现 |
| **整体** | **>= 80%** | pyproject.toml fail_under=80 |

pragma: no cover 规范: 仅用于 if TYPE_CHECKING 块、raise NotImplementedError、平台 OS 路径分支。
每处必须有内联注释说明原因，禁止裸用，禁止在业务主路径使用。

---

### 1.2 Layer 2: 集成测试

#### 1.2.1 EDA 工具 Mock 策略（无需真实安装）

Mock 边界在 `core/process.run_tool()` 层面介入。Server 启动、Tool 注册、Pydantic 验证、
错误处理均真实执行，仅 EDA CLI 进程启动和返回结果被 mock。

CI 无需安装 Yosys/KiCad/Verilator；测试速度快；可精确控制输出覆盖各种异常场景。

#### 1.2.2 集成测试核心 fixtures (`tests/integration/conftest.py`)

```python
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastmcp import Client

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"

@pytest.fixture
async def yosys_server_client():
    from auto_eda.core.process import ProcessResult
    from auto_eda.servers.yosys.server import create_yosys_server
    synth_json = json.loads((FIXTURE_DIR / "yosys" / "counter_synth.json").read_text())
    mock_result = ProcessResult(returncode=0, stdout=json.dumps(synth_json), stderr="Yosys 0.45", timed_out=False)
    server = create_yosys_server()
    with patch("auto_eda.core.process.run_tool", new_callable=AsyncMock, return_value=mock_result):
        async with Client(server) as client:
            yield client

@pytest.fixture
async def kicad_server_client(mock_kicad_capabilities_cli_only):
    from auto_eda.servers.kicad.server import create_kicad_server
    with patch(
        "auto_eda.adapters.kicad.version_detect.detect_kicad_capabilities",
        return_value=mock_kicad_capabilities_cli_only,
    ):
        server = create_kicad_server()
        async with Client(server) as client:
            yield client

@pytest.fixture
async def verilog_server_client():
    from auto_eda.servers.verilog_utils.server import create_verilog_server
    server = create_verilog_server()
    async with Client(server) as client:
        yield client
```

#### 1.2.3 MCP Server 启动和工具调用测试 (`tests/integration/test_yosys_server.py`)

```python
import json, pytest

@pytest.mark.integration
class TestYosysServerStartup:
    async def test_server_lists_expected_tools(self, yosys_server_client):
        tool_names = {t.name for t in await yosys_server_client.list_tools()}
        expected = {"synthesize_rtl", "get_synthesis_stats", "check_synthesis_feasibility", "export_netlist"}
        assert expected.issubset(tool_names), f"Missing: {expected - tool_names}"

    async def test_all_tools_have_description(self, yosys_server_client):
        for tool in await yosys_server_client.list_tools():
            assert tool.description and len(tool.description) > 10

    async def test_all_tools_have_input_schema(self, yosys_server_client):
        for tool in await yosys_server_client.list_tools():
            assert tool.inputSchema is not None

@pytest.mark.integration
class TestYosysSynthesizeRtl:
    async def test_synthesize_counter_success(self, yosys_server_client, counter_v):
        result = await yosys_server_client.call_tool(
            "synthesize_rtl",
            {"verilog_files": [str(counter_v)], "top_module": "counter", "target": "generic"},
        )
        assert not result[0].isError
        assert json.loads(result[0].text)["success"] is True

    async def test_missing_file_returns_error(self, yosys_server_client):
        result = await yosys_server_client.call_tool(
            "synthesize_rtl",
            {"verilog_files": ["/nonexistent/design.v"], "top_module": "top", "target": "generic"},
        )
        assert result[0].isError or "[ERROR" in result[0].text

    async def test_invalid_target_rejected(self, yosys_server_client, counter_v):
        result = await yosys_server_client.call_tool(
            "synthesize_rtl",
            {"verilog_files": [str(counter_v)], "top_module": "counter", "target": "bad_xyz"},
        )
        assert result[0].isError or "[ERROR" in result[0].text
```

#### 1.2.4 跨工具数据流测试 (`tests/integration/test_cross_tool_flow.py`)

```python
import json, pytest

@pytest.mark.integration
class TestVerilogToSynthesisFlow:
    async def test_parse_then_synthesize_counter(
        self, verilog_server_client, yosys_server_client, counter_v
    ):
        parse_result = await verilog_server_client.call_tool(
            "parse_verilog", {"verilog_files": [str(counter_v)]}
        )
        assert not parse_result[0].isError
        top_module = json.loads(parse_result[0].text)["data"]["modules"][0]["name"]
        synth_result = await yosys_server_client.call_tool(
            "synthesize_rtl",
            {"verilog_files": [str(counter_v)], "top_module": top_module, "target": "generic"},
        )
        assert not synth_result[0].isError
        assert json.loads(synth_result[0].text)["success"] is True

    async def test_lint_rejects_syntax_error(self, verilog_server_client, syntax_error_v):
        lint_result = await verilog_server_client.call_tool(
            "lint_verilog", {"verilog_files": [str(syntax_error_v)]}
        )
        assert "error" in lint_result[0].text.lower() or lint_result[0].isError
```

#### 1.2.5 文件 I/O 测试场景

| 场景 | 预期行为 |
|------|----------|
| 符号链接路径 | 正常处理，等同真实文件 |
| 路径含空格 | 正常处理（args list 不拼接字符串）|
| 只读输出目录 | 返回 FILE_PERMISSION 错误，不崩溃 |
| Unicode 路径 | 正常处理 |
| 并发调用同一文件 | 无竞态条件 |

---

### 1.3 Layer 3: MCP Inspector 验证

#### 1.3.1 Inspector 自动化使用方案

```bash
# 开发阶段 (浏览器访问 http://localhost:6274)
npx @modelcontextprotocol/inspector python -m auto_eda.servers.yosys
npx @modelcontextprotocol/inspector python -m auto_eda.servers.kicad
npx @modelcontextprotocol/inspector python -m auto_eda.servers.verilog_utils

# CI CLI 无 GUI 模式
npx @modelcontextprotocol/inspector --cli python -m auto_eda.servers.yosys --method tools/list
npx @modelcontextprotocol/inspector --cli python -m auto_eda.servers.kicad --method tools/list
npx @modelcontextprotocol/inspector --cli python -m auto_eda.servers.verilog_utils --method tools/list
```

手动验证检查清单（每个新工具添加后必做）:

```
[ ] 工具名 snake_case，无驼峰
[ ] inputSchema 参数类型正确
[ ] 必填 vs 可选参数区分正确
[ ] enum 字段列出所有有效值
[ ] description 含功能说明和返回格式示例
[ ] 成功路径调用，JSON 结构符合预期
[ ] 无效参数调用，返回含建议的错误信息
[ ] Notifications 面板：ctx.report_progress 正常推送
[ ] Resources 标签：URI 模板格式正确
[ ] Prompts 标签：模板渲染正确
```

#### 1.3.2 协议合规测试 (`tests/mcp/test_yosys_mcp_protocol.py`)

```python
import re, pytest

@pytest.mark.mcp
class TestYosysMCPProtocolCompliance:
    async def test_initialization_succeeds(self, yosys_server_client):
        assert len(await yosys_server_client.list_tools()) > 0

    async def test_tool_names_are_snake_case(self, yosys_server_client):
        pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        for tool in await yosys_server_client.list_tools():
            assert pattern.match(tool.name), f"Tool {tool.name!r} not snake_case"

    async def test_tool_name_length_within_spec(self, yosys_server_client):
        for tool in await yosys_server_client.list_tools():
            assert 1 <= len(tool.name) <= 64

    async def test_unknown_tool_returns_error(self, yosys_server_client):
        result = await yosys_server_client.call_tool("nonexistent_tool_xyz", {})
        assert result[0].isError

    async def test_missing_required_param_returns_error(self, yosys_server_client):
        result = await yosys_server_client.call_tool(
            "synthesize_rtl", {"top_module": "counter", "target": "generic"}
        )
        assert result[0].isError or "[ERROR" in result[0].text

    async def test_resources_list_succeeds(self, yosys_server_client):
        resources = await yosys_server_client.list_resources()
        assert isinstance(resources, list)
```

test_kicad_mcp_protocol.py 和 test_verilog_mcp_protocol.py 使用相同结构，替换 fixture 名称和预期工具集合。

---

### 1.4 Layer 4: 端到端测试

#### 1.4.1 Docker 环境设计

```dockerfile
# docker/Dockerfile.e2e
FROM ubuntu:22.04 AS eda-base
RUN apt-get update && apt-get install -y --no-install-recommends \
    yosys verilator iverilog python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*
RUN add-apt-repository ppa:kicad/kicad-9-releases \
    && apt-get update && apt-get install -y kicad \
    && rm -rf /var/lib/apt/lists/*

FROM eda-base AS auto-eda-e2e
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["pytest", "tests/", "-m", "integration or e2e", "-v", "--tb=short"]
```

```yaml
# docker-compose.e2e.yml
version: "3.9"
services:
  e2e-tests:
    build:
      context: .
      dockerfile: docker/Dockerfile.e2e
    volumes:
      - ./tests/fixtures:/app/tests/fixtures:ro
    environment:
      - AUTO_EDA_LOG_LEVEL=DEBUG
```

#### 1.4.2 EDA 工具版本矩阵

| 工具 | 最低版本 | 推荐版本 | CI 测试矩阵 |
|------|----------|----------|-------------|
| Yosys | 0.35 | 0.45+ | 0.38, 0.45 |
| KiCad | 8.0 | 9.0+ | 8.0, 9.0 |
| Verilator | 5.006 | 5.020+ | 5.006, 5.020 |
| Icarus Verilog | 11.0 | 12.0 | 11.0, 12.0 |
| Python | 3.10 | 3.12 | 3.10, 3.11, 3.12, 3.13 |

#### 1.4.3 基准设计

**计数器 (`tests/fixtures/verilog/counter.v`)**: 8-bit 同步计数器，时钟使能，同步复位。预期: 8 个 DFF，约 16 个 LUT。验证: 综合成功、num_dff >= 8、无 lint 错误。

**加法器 (`tests/fixtures/verilog/adder.v`)**: 16-bit 超前进位加法器。预期: 零 DFF，纯组合逻辑。验证: 综合成功、num_dff == 0。

**FIFO (`tests/fixtures/verilog/fifo.v`)**: 参数化深度 FIFO（depth=16, width=8）。预期: 128 bit 存储 + 控制逻辑。验证: 综合成功、RAM 推断正确。

**KiCad Blinky (`tests/fixtures/kicad/blinky/`)**: LED blinky 电路。验证: ERC 零错误、DRC 零 violation、Gerber 导出成功。

**语法错误文件 (`tests/fixtures/verilog/syntax_error.v`)**: 故意引入语法错误。验证: 返回 VERILOG_SYNTAX_ERROR，不崩溃，错误信息含行号。

#### 1.4.4 Claude Code 集成测试方案

```python
# tests/e2e/test_rtl_to_netlist_workflow.py
import json, pytest

@pytest.mark.e2e
@pytest.mark.slow
class TestRTLToNetlistWorkflow:
    async def test_counter_full_workflow(self, real_yosys_client, real_verilog_client, counter_v):
        """模拟 Claude Code 典型工作流: parse -> lint -> synthesize -> stats"""
        parse = await real_verilog_client.call_tool(
            "parse_verilog", {"verilog_files": [str(counter_v)]}
        )
        assert not parse[0].isError
        assert any(m["name"] == "counter" for m in json.loads(parse[0].text)["data"]["modules"])

        lint = await real_verilog_client.call_tool(
            "lint_verilog", {"verilog_files": [str(counter_v)]}
        )
        assert len(json.loads(lint[0].text)["data"].get("errors", [])) == 0

        synth = await real_yosys_client.call_tool(
            "synthesize_rtl",
            {"verilog_files": [str(counter_v)], "top_module": "counter", "target": "generic"},
        )
        assert not synth[0].isError
        assert json.loads(synth[0].text)["data"]["num_cells"] > 0

        stats = await real_yosys_client.call_tool(
            "get_synthesis_stats",
            {"verilog_files": [str(counter_v)], "top_module": "counter"},
        )
        assert json.loads(stats[0].text)["data"]["num_dff"] >= 8
```

---

## 2. CI/CD 测试流水线

### 2.1 GitHub Actions 完整 Workflow

#### 2.1.1 主 CI (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  quality:
    name: Code Quality (ruff + mypy)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/
      - run: mypy src/auto_eda/

  unit-tests:
    name: Unit Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: quality
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -e ".[dev]"
      - name: Run unit tests
        run: |
          pytest tests/unit/ tests/mcp/ -m "unit or mcp"
            --cov=auto_eda --cov-report=xml:coverage-${{ matrix.python-version }}.xml
            --cov-fail-under=80 -v --tb=short
      - uses: codecov/codecov-action@v4
        if: matrix.python-version == "3.12"
        with:
          file: coverage-3.12.xml
          flags: unit-tests

  integration-tests:
    name: Integration Tests (mocked EDA)
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -m integration --timeout=60 --cov=auto_eda --cov-fail-under=80 -v

  mcp-inspector-check:
    name: MCP Inspector Protocol Check
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: pip install -e ".[dev]"
      - run: npm install -g @modelcontextprotocol/inspector
      - name: Verify Yosys Server
        run: npx @modelcontextprotocol/inspector --cli python -m auto_eda.servers.yosys --method tools/list 2>&1 | grep synthesize_rtl
      - name: Verify KiCad Server
        run: npx @modelcontextprotocol/inspector --cli python -m auto_eda.servers.kicad --method tools/list 2>&1 | grep run_drc
      - name: Verify Verilog Server
        run: npx @modelcontextprotocol/inspector --cli python -m auto_eda.servers.verilog_utils --method tools/list 2>&1 | grep parse_verilog

  pre-release-check:
    name: Pre-release Acceptance
    runs-on: ubuntu-latest
    if: github.ref == "refs/heads/main"
    needs: [quality, unit-tests, integration-tests, mcp-inspector-check]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e ".[dev]" build
      - run: python -m build
      - run: pip install dist/*.whl && python -c "import auto_eda; print(auto_eda.__version__)"
      - run: pytest tests/ -m "unit or mcp or integration" --tb=short -q --cov=auto_eda --cov-fail-under=80
```

#### 2.1.2 EDA 集成测试 Workflow (`.github/workflows/integration.yml`)

```yaml
name: EDA Integration Tests

on:
  schedule:
    - cron: "0 2 * * 1"  # 每周一 UTC 02:00
  workflow_dispatch:
    inputs:
      eda_versions:
        description: EDA tool version set
        default: stable
        type: choice
        options: [stable, latest]

jobs:
  eda-integration:
    name: EDA Integration (${{ matrix.eda-set }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        eda-set: [yosys-0.38, yosys-0.45]
    container:
      image: ghcr.io/auto-eda/eda-ci:${{ matrix.eda-set }}
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - name: Verify EDA versions
        run: yosys --version
      - name: Run E2E tests
        run: pytest tests/e2e/ tests/integration/ -m "e2e or integration" --timeout=300 -v --tb=long
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: e2e-failure-${{ matrix.eda-set }}
          path: tests/e2e/output/
```

### 2.2 测试矩阵说明

| 维度 | 配置 | 理由 |
|------|------|------|
| Python 版本 | 3.10, 3.11, 3.12, 3.13 | pyproject.toml requires-python >= 3.10 |
| OS | ubuntu-latest | EDA 工具在 Linux 最成熟 |
| EDA Yosys | 0.38, 0.45 | 覆盖稳定版和最新版 |
| EDA KiCad | 8.0, 9.0 | 跨越 IPC API 新旧两代 |
| 单元测试频率 | 每次 commit | 无外部依赖，成本极低 |
| 集成测试频率 | 每次 PR | mock EDA，速度可接受 |
| E2E 测试频率 | 每周 + release | 真实 EDA 工具，成本高 |

### 2.3 代码质量检查配置

**ruff** (已在 pyproject.toml 配置):
- select: E, W, F, I, B, C4, UP, ANN, SIM, TCH
- ignore: ANN101, ANN102, E501
- tests/**/*.py 忽略 ANN 注解强制

**mypy** (--strict 模式):
- warn_return_any = true
- disallow_untyped_defs = true
- no_implicit_reexport = true
- EDA 库 (pyverilog.*, gdstk.*) 设 ignore_missing_imports = true

**pre-commit hooks** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        args: [--strict]
        additional_dependencies: [pydantic>=2.6.0]
```
│   ├── test_process.py
│   ├── test_result.py
│   ├── test_yosys_models.py
│   ├── test_kicad_models.py
│   ├── test_verilog_models.py
│   ├── test_yosys_parser.py
│   ├── test_kicad_version.py
│   ├── test_verilog_parser.py
│   └── test_memory_leak.py
├── integration/                        # Layer 2
│   ├── conftest.py
│   ├── test_yosys_server.py
│   ├── test_kicad_server.py
│   ├── test_verilog_utils.py
│   ├── test_cross_tool_flow.py
│   └── test_file_io.py
├── mcp/                                # Layer 3
│   ├── test_yosys_mcp_protocol.py
│   ├── test_kicad_mcp_protocol.py
│   ├── test_verilog_mcp_protocol.py
│   ├── test_api_compatibility.py
│   └── api_snapshots.json
├── e2e/                                # Layer 4
│   └── test_rtl_to_netlist_workflow.py
└── benchmarks/
    └── test_tool_latency.py
```

---

## 3. 测试数据管理

### 3.1 测试用 HDL 文件库

**counter.v** (8-bit 同步计数器): 时钟使能 + 同步复位。预期综合: 8 个 DFF, 约 16 个 LUT。

**adder.v** (16-bit 超前进位加法器): 纯组合逻辑。预期综合: 0 个 DFF。

**fifo.v** (参数化同步 FIFO, depth=16, width=8): 读写指针 + 空满标志。预期综合: RAM 推断正确。

**syntax_error.v**: 故意引入缺少 endmodule、未定义信号等语法错误，用于验证错误处理路径。

### 3.2 KiCad 测试项目

**tests/fixtures/kicad/blinky/** - LED Blinky 最小电路:
- 原理图: MCU (ATTINY85) + LED + 限流电阻 + VCC/GND
- PCB: 所有元件已布局，无飞线，DRC 干净
- 格式: KiCad 8.0+ (kicad_sch / kicad_pcb / kicad_pro)
- 验证指标: ERC 0 error, DRC 0 violation, Gerber 导出成功

### 3.3 GDSII 测试文件策略

- Phase 0: 不包含 GDSII 文件 (Yosys 综合不涉及)
- Phase 1+: 使用 gdstk 在测试运行时程序化生成最小合法 GDSII
- 大文件测试: 单独测试 gdstk API，不在 CI 中存储大文件
- Git LFS: 若需提交 GDSII fixture，使用 Git LFS 管理

### 3.4 PDK 测试环境

- 单元/集成测试: 不依赖 PDK (Yosys generic target)
- E2E 测试: 可选 yowasp-yosys (WebAssembly, 含基础 cell 库) 或 SkyWater 130nm 子集
- CI 缓存 key: pdk-sky130-<hash-of-install-script>
- 下载脚本: scripts/install_eda_tools.sh 按需安装，CI 中启用缓存

---

## 4. 质量指标和监控

### 4.1 代码覆盖率追踪

| 指标 | 目标 | 工具 | 频率 |
|------|------|------|------|
| 行覆盖率 | >= 80% (整体) | pytest-cov | 每次 PR |
| 分支覆盖率 | >= 70% | pytest-cov branch=true | 每次 PR |
| 核心模块行覆盖 | >= 90% | codecov per-file | 每次 PR |
| 覆盖率趋势 | 不下降 | Codecov diff check | 每次 PR |

### 4.2 工具调用延迟基准

| 工具调用 | P50 目标 | P95 目标 | 测量方法 |
|----------|----------|----------|----------|
| synthesize_rtl (counter, generic) | < 5s | < 15s | pytest-benchmark |
| parse_verilog (counter.v) | < 0.5s | < 2s | pytest-benchmark |
| run_drc (blinky, CLI mode) | < 10s | < 30s | pytest-benchmark |
| list_tools (Server 启动后) | < 100ms | < 500ms | pytest-benchmark |
| MCP initialize 握手 | < 200ms | < 1s | FastMCP Client |

### 4.3 内存泄漏检测

检测策略:
- 重复调用同一工具 20+ 次，使用 tracemalloc 测量内存增长
- 重点关注: pyverilog AST 对象、Yosys stdout 缓冲、KiCad IPC 连接
- 阈值: 20 次循环总增长 < 5MB
- 测试文件: tests/unit/test_memory_leak.py

### 4.4 API 兼容性回归测试

API Snapshot 管理策略:
- tests/mcp/api_snapshots.json 存储每个 Server 的工具 Schema 快照
- 新增工具: 更新 snapshot (非 breaking change，允许)
- 删除工具或删除必填参数: 测试失败，需 major version bump
- 修改参数类型: 测试失败，需评估向后兼容性
- 测试文件: tests/mcp/test_api_compatibility.py

### 4.5 质量门禁汇总

| 门禁项 | 标准 | 失败处理 |
|--------|------|----------|
| ruff lint | 0 warnings | PR 阻断 |
| mypy strict | 0 errors | PR 阻断 |
| 单元测试通过率 | 100% | PR 阻断 |
| 整体覆盖率 | >= 80% | PR 阻断 |
| 新增代码覆盖率 | >= 70% | PR 警告 |
| MCP Inspector 工具列表 | 包含全部预期工具 | PR 阻断 |
| API 兼容性快照 | 无 breaking change | PR 阻断 |
| 内存泄漏检测 | < 5MB/20次 | PR 警告 |
| E2E 基准设计成功率 | >= 90% | Release 阻断 |
| 工具调用 P95 延迟 | 符合 4.2 基准 | Release 警告 |
