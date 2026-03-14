# DA4: AUTO_EDA 风险缓解方案与技术债务预防深度分析

> 分析日期: 2026-03-14
> 分析师: DA4 风险缓解深度分析师
> 数据来源: A4 风险评估 + A1 技术可行性 + A7 技术栈决策
> 覆盖维度: 高风险项缓解代码模式、技术债务预防、EDA依赖管理、LLM+EDA特有风险、开源维护风险

---

## 目录

1. [高风险项深度缓解方案](#1-高风险项深度缓解方案)
   - 1.1 T1 KiCad IPC API 不稳定
   - 1.2 T7 LLM 幻觉防护层设计
   - 1.3 T3 EDA 工具版本碎片化
   - 1.4 T5 长时任务超时
2. [技术债务预防清单](#2-技术债务预防清单)
3. [EDA 工具依赖管理风险](#3-eda-工具依赖管理风险)
4. [LLM+EDA 特有风险防护](#4-llmeda-特有风险防护)
5. [开源项目维护风险](#5-开源项目维护风险)
6. [综合风险缓解优先级矩阵](#6-综合风险缓解优先级矩阵)

---

## 1. 高风险项深度缓解方案

### 1.1 T1: KiCad IPC API 不稳定 [A4 得分 20/极高]

**风险摘要**: KiCad 正经历 SWIG→IPC API 架构转型。v10 RC2 已发布 (2026-03-07)，旧 SWIG
绑定将被移除。IPC API 在 v10.x 系列仍将持续调整，4+ 个现有 KiCad MCP 实现全部面临相同迁移压力。

**核心缓解原则**: 运行时探测能力，通过 Dispatcher 分派到最优实现。IPC 调用失败自动 fallback
到 CLI，调用方永远不感知底层 API 版本。

#### 1.1.1 版本检测与能力探测

```python
# src/auto_eda/adapters/kicad/version_detect.py
from __future__ import annotations
import subprocess, re, os
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class KiCadApiMode(Enum):
    UNAVAILABLE = auto()   # KiCad 未安装
    CLI_ONLY    = auto()   # 仅 CLI（v8 及以下）
    IPC_V9      = auto()   # IPC API v9（实验版）
    IPC_V10     = auto()   # IPC API v10（Pythonic，推荐）


@dataclass(frozen=True)
class KiCadCapabilities:
    version_tuple: tuple[int, int, int]
    api_mode: KiCadApiMode
    has_schematic_api: bool = False   # v10+ 新增原理图 API
    has_pcb_api: bool = False
    has_drc_api: bool = False
    has_batch_drc: bool = False       # CLI Jobsets，v9+
    ipc_socket_path: Optional[str] = None

    @property
    def is_usable(self) -> bool:
        return self.api_mode != KiCadApiMode.UNAVAILABLE


def detect_kicad_capabilities() -> KiCadCapabilities:
    """
    探测当前环境 KiCad 版本和能力。
    永远不抛出异常——失败返回 UNAVAILABLE 状态而非崩溃。
    """
    vt = _get_kicad_version()
    if vt is None:
        return KiCadCapabilities(
            version_tuple=(0, 0, 0), api_mode=KiCadApiMode.UNAVAILABLE
        )
    major, _minor, _patch = vt
    if major < 9:
        return KiCadCapabilities(
            version_tuple=vt, api_mode=KiCadApiMode.CLI_ONLY,
            has_batch_drc=(major >= 8),
        )
    ipc_ok, sock = _probe_ipc_api()
    if major == 9:
        return KiCadCapabilities(
            version_tuple=vt,
            api_mode=KiCadApiMode.IPC_V9 if ipc_ok else KiCadApiMode.CLI_ONLY,
            has_pcb_api=ipc_ok, has_drc_api=ipc_ok,
            has_batch_drc=True, ipc_socket_path=sock,
        )
    # major >= 10: v10 新增 schematic API
    return KiCadCapabilities(
        version_tuple=vt,
        api_mode=KiCadApiMode.IPC_V10 if ipc_ok else KiCadApiMode.CLI_ONLY,
        has_schematic_api=ipc_ok, has_pcb_api=ipc_ok,
        has_drc_api=ipc_ok, has_batch_drc=True,
        ipc_socket_path=sock,
    )


def _get_kicad_version() -> Optional[tuple[int, int, int]]:
    for cmd in ["kicad-cli", "kicad-cli.exe"]:
        try:
            r = subprocess.run(
                [cmd, "--version"], capture_output=True, text=True, timeout=5
            )
            m = re.search(r"(\d+)\.(\d+)\.(\d+)", r.stdout + r.stderr)
            if m:
                return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    return None


def _probe_ipc_api() -> tuple[bool, Optional[str]]:
    """探测 KiCad IPC socket 是否存在（KiCad 必须正在运行）。"""
    try:
        import kiapi  # type: ignore[import-not-found]  # noqa: F401
        for path in ["/tmp/kicad/api.sock", "/var/run/kicad/api.sock"]:
            if os.path.exists(path):
                return True, path
        return False, None
    except ImportError:
        return False, None
```

#### 1.1.2 Graceful Fallback Dispatcher

```python
# src/auto_eda/adapters/kicad/dispatcher.py
from __future__ import annotations
import subprocess, json, os, tempfile
from typing import Any
from .version_detect import KiCadApiMode, KiCadCapabilities

class KiCadDispatcher:
    def __init__(self, caps: KiCadCapabilities) -> None:
        self._caps = caps

    def run_drc(self, pcb_file: str, output_dir: str) -> dict[str, Any]:
        match self._caps.api_mode:
            case KiCadApiMode.UNAVAILABLE:
                return _error_unavailable("run_drc")
            case KiCadApiMode.CLI_ONLY:
                return _drc_cli(pcb_file, output_dir)
            case KiCadApiMode.IPC_V9 | KiCadApiMode.IPC_V10:
                try:
                    return _drc_ipc(pcb_file, self._caps)
                except Exception:
                    return _drc_cli(pcb_file, output_dir)  # auto fallback

    def get_schematic_netlist(self, sch_file: str) -> dict[str, Any]:
        if self._caps.api_mode == KiCadApiMode.IPC_V10 and self._caps.has_schematic_api:
            try:
                return _netlist_ipc_v10(sch_file, self._caps)
            except Exception:
                pass
        return _netlist_cli(sch_file)

def _error_unavailable(op: str) -> dict[str, Any]:
    return {
        "success": False, "error": "kicad_unavailable",
        "message": "KiCad not found. Install: https://www.kicad.org/download/",
        "install_hint": {"linux": "sudo apt install kicad",
                         "macos": "brew install --cask kicad",
                         "windows": "winget install KiCad.KiCad"},
    }

def _drc_cli(pcb_file: str, output_dir: str) -> dict[str, Any]:
    report = os.path.join(output_dir, "drc_report.json")
    r = subprocess.run(
        ["kicad-cli", "pcb", "drc", "--output", report, "--format", "json", pcb_file],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        return {"success": False, "error": r.stderr, "mode": "cli"}
    with open(report) as f:
        return {"success": True, "data": json.load(f), "mode": "cli"}

def _drc_ipc(pcb_file: str, caps: KiCadCapabilities) -> dict[str, Any]:
    import kiapi.board as api  # type: ignore
    client = api.BoardEditorClient(caps.ipc_socket_path)
    with client.open_board(pcb_file) as board:
        violations = board.run_drc()
        return {"success": True,
                "violations": [v.to_dict() for v in violations],
                "mode": f"ipc_{caps.api_mode.name.lower()}"}

def _netlist_cli(sch_file: str) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
        out = tf.name
    try:
        r = subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--output", out, sch_file],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return {"success": False, "error": r.stderr}
        return {"success": True, "netlist_xml": open(out).read(), "mode": "cli"}
    finally:
        os.path.exists(out) and os.unlink(out)

def _netlist_ipc_v10(sch_file: str, caps: KiCadCapabilities) -> dict[str, Any]:
    import kiapi.schematic as api  # type: ignore
    client = api.SchematicEditorClient(caps.ipc_socket_path)
    with client.open_schematic(sch_file) as sch:
        return {"success": True, "netlist": sch.get_netlist().to_dict(), "mode": "ipc_v10"}
```

#### 1.1.3 版本兼容性测试矩阵

```python
# tests/adapters/kicad/test_version_compat.py
import pytest
from unittest.mock import patch
from auto_eda.adapters.kicad.version_detect import (
    detect_kicad_capabilities, KiCadApiMode, KiCadCapabilities,
)

@pytest.mark.parametrize("version,mode,has_sch", [
    ((8, 0, 7),  KiCadApiMode.CLI_ONLY, False),
    ((9, 0, 2),  KiCadApiMode.IPC_V9,  False),
    ((10, 0, 0), KiCadApiMode.IPC_V10, True),
    ((11, 0, 0), KiCadApiMode.IPC_V10, True),  # 未来版本向前兼容
])
def test_version_mode_mapping(version, mode, has_sch):
    with patch("auto_eda.adapters.kicad.version_detect._get_kicad_version",
               return_value=version), \
         patch("auto_eda.adapters.kicad.version_detect._probe_ipc_api",
               return_value=(version[0] >= 9, "/tmp/kicad/api.sock")):
        caps = detect_kicad_capabilities()
    assert caps.api_mode == mode
    assert caps.has_schematic_api == has_sch

def test_unavailable_never_raises():
    with patch("auto_eda.adapters.kicad.version_detect._get_kicad_version", return_value=None):
        caps = detect_kicad_capabilities()
    assert caps.api_mode == KiCadApiMode.UNAVAILABLE
    assert not caps.is_usable

def test_ipc_failure_falls_back_to_cli(tmp_path):
    from auto_eda.adapters.kicad.dispatcher import KiCadDispatcher
    caps = KiCadCapabilities(
        version_tuple=(10, 0, 0), api_mode=KiCadApiMode.IPC_V10,
        has_drc_api=True, ipc_socket_path="/tmp/kicad/api.sock",
    )
    disp = KiCadDispatcher(caps)
    with patch("auto_eda.adapters.kicad.dispatcher._drc_ipc",
               side_effect=ConnectionError("IPC down")), \
         patch("auto_eda.adapters.kicad.dispatcher._drc_cli",
               return_value={"success": True, "mode": "cli"}):
        result = disp.run_drc(str(tmp_path / "t.kicad_pcb"), str(tmp_path))
    assert result["success"] is True and result["mode"] == "cli"
```

---

### 1.2 T7: LLM 幻觉防护层设计 [A4 得分 20/极高]

**风险摘要**: ChipBench SOTA 模型复杂层次化设计通过率约 31%。错误 HDL 可导致数百万美元重新流片成本。

#### EDA 领域幻觉特征分类

| 幻觉类型 | 典型表现 | 后果 | 检测层 |
|----------|----------|------|--------|
| 不可综合结构 | `#delay`、`initial` 混组合逻辑 | 综合失败 | Layer1+Layer3 |
| 时序错误 | 异步复位混同步逻辑 | 硅片随机失效 | Layer4 危险模式 |
| 位宽幻觉 | 隐式截断、有符号/无符号混用 | 功能错误 | Layer2 iverilog |
| 端口声明错误 | 输入输出方向错误 | 编译错误 | Layer2 iverilog |
| 库函数幻觉 | 引用不存在的原语 | 映射失败 | Layer3 Yosys |
| 约束幻觉 | 无效 SDC/XDC 时序约束 | 时序签核失败 | OpenSTA |

#### 多层防护架构

```
LLM 输出
    |
[Layer 1] 纯 Python 静态正则检查  -- 无需工具，最快
    |
[Layer 2] iverilog -tnull -Wall   -- 语法+类型，<30s
    |
[Layer 3] yosys proc + check      -- 可综合性，<60s
    |
[Layer 4] 危险模式检测            -- 时序/亚稳态风险
    |
聚合报告 -> 仅 passed=True 时才返回给用户
```

```python
# src/auto_eda/validation/hdl_validator.py
from __future__ import annotations
import subprocess, tempfile, os, re, shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Severity(Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"

@dataclass
class ValidationIssue:
    severity:  Severity
    category:  str
    message:   str
    line:      Optional[int] = None
    fix_hint:  Optional[str] = None

@dataclass
class ValidationResult:
    passed:     bool
    issues:     list[ValidationIssue] = field(default_factory=list)
    layers_run: list[str]             = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    def to_user_report(self) -> str:
        lines = [f"HDL Validation: {'PASSED' if self.passed else 'FAILED'}",
                 f"Layers: {', '.join(self.layers_run)}",
                 f"Errors: {self.error_count}"]
        for iss in self.issues:
            loc = f" (line {iss.line})" if iss.line else ""
            lines.append(f"  [{iss.severity.value.upper()}][{iss.category}]{loc} {iss.message}")
            if iss.fix_hint:
                lines.append(f"    Hint: {iss.fix_hint}")
        return "\n".join(lines)

class HdlValidationPipeline:
    def validate(self, verilog_code: str) -> ValidationResult:
        issues: list[ValidationIssue] = []
        layers: list[str] = []
        with tempfile.NamedTemporaryFile(
            suffix=".v", mode="w", delete=False, prefix="auto_eda_"
        ) as f:
            f.write(verilog_code)
            tmp = f.name
        try:
            issues += self._layer_static(verilog_code);    layers.append("static")
            issues += self._layer_iverilog(tmp);           layers.append("iverilog")
            issues += self._layer_yosys(tmp);             layers.append("yosys")
            issues += self._layer_dangerous(verilog_code);layers.append("dangerous_patterns")
        finally:
            os.unlink(tmp)
        return ValidationResult(
            passed=not any(i.severity == Severity.ERROR for i in issues),
            issues=issues, layers_run=layers
        )

    def _layer_static(self, code: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for m in re.finditer(r"#\s*\d+", code):
            ln = code[:m.start()].count("\n") + 1
            issues.append(ValidationIssue(
                Severity.ERROR, "synthesizability",
                f"Non-synthesizable delay '{m.group().strip()}'",
                line=ln, fix_hint="Use clock-edge sensitivity instead.",
            ))
        if "`default_nettype none" not in code and "`default_nettype wire" not in code:
            issues.append(ValidationIssue(
                Severity.WARNING, "coding_style",
                "Missing `default_nettype directive.",
                fix_hint="Add '`default_nettype none' at top of file.",
            ))
        for sys_task in [r"\$display", r"\$finish", r"\$stop"]:
            for m in re.finditer(sys_task, code):
                ln = code[:m.start()].count("\n") + 1
                issues.append(ValidationIssue(
                    Severity.WARNING, "synthesizability",
                    f"Simulation-only system task '{m.group()}' in RTL.",
                    line=ln,
                ))
        return issues

    def _layer_iverilog(self, file_path: str) -> list[ValidationIssue]:
        if not shutil.which("iverilog"):
            return [ValidationIssue(Severity.INFO, "tool_unavailable",
                                    "iverilog not found; syntax layer skipped.")]
        r = subprocess.run(["iverilog", "-tnull", "-Wall", file_path],
                           capture_output=True, text=True, timeout=30)
        issues: list[ValidationIssue] = []
        for line in (r.stderr + r.stdout).splitlines():
            m = re.match(r".*:(\d+):\s*(error|warning):\s*(.*)", line)
            if m:
                sev = Severity.ERROR if m.group(2) == "error" else Severity.WARNING
                issues.append(ValidationIssue(sev, "syntax", m.group(3), int(m.group(1))))
        return issues

    def _layer_yosys(self, file_path: str) -> list[ValidationIssue]:
        if not shutil.which("yosys"):
            return [ValidationIssue(Severity.INFO, "tool_unavailable",
                                    "yosys not found; synthesizability layer skipped.")]
        script = f"read_verilog -sv {file_path}; proc; check"
        r = subprocess.run(["yosys", "-p", script],
                           capture_output=True, text=True, timeout=60)
        issues: list[ValidationIssue] = []
        for line in (r.stdout + r.stderr).splitlines():
            low = line.lower()
            if "error" in low:
                issues.append(ValidationIssue(Severity.ERROR, "synthesizability", line.strip()))
            elif "warning" in low:
                issues.append(ValidationIssue(Severity.WARNING, "synthesizability", line.strip()))
        return issues

    def _layer_dangerous(self, code: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if re.search(r"always\s*@\s*\(.*posedge.*posedge", code):
            issues.append(ValidationIssue(
                Severity.WARNING, "timing",
                "Multiple posedge in sensitivity list. Verify clock domain intent.",
                fix_hint="Use one clock edge per always block.",
            ))
        if re.search(r"always\s*@\s*\((?!.*posedge)(?!.*negedge)", code):
            issues.append(ValidationIssue(
                Severity.WARNING, "synthesizability",
                "Combinational always block: ensure all paths assign output.",
                fix_hint="Add default assignments at top of always block.",
            ))
        return issues
```

```python
# tests/validation/test_hdl_validator.py
from auto_eda.validation.hdl_validator import HdlValidationPipeline, Severity

CLEAN = """
`default_nettype none
module counter #(parameter W=8) (
    input  wire       clk, rst_n,
    output reg [W-1:0] count
);
    always @(posedge clk or negedge rst_n)
        if (!rst_n) count <= 0;
        else        count <= count + 1;
endmodule
`default_nettype wire
"""

DELAY = """
module bad(input clk, output reg q);
    always @(posedge clk) #10 q <= 1;
endmodule
"""

def test_clean_verilog_no_errors():
    result = HdlValidationPipeline().validate(CLEAN)
    assert not [i for i in result.issues if i.severity == Severity.ERROR]

def test_delay_detected_as_error():
    result = HdlValidationPipeline().validate(DELAY)
    assert not result.passed
    assert any(i.category == "synthesizability" and i.severity == Severity.ERROR
               for i in result.issues)

def test_report_human_readable():
    result = HdlValidationPipeline().validate(DELAY)
    report = result.to_user_report()
    assert "FAILED" in report and "synthesizability" in report
```

---

### 1.3 T3: EDA 工具版本碎片化 [A4 得分 12/高]

**风险摘要**: 各开源 EDA 工具版本演进节奏不同步。Yosys 0.38 vs 0.45 API 有差异，用户环境差异极大，
无法假设任何特定版本存在。

#### 版本检测与兼容性矩阵设计

```python
# src/auto_eda/adapters/tool_registry.py
from __future__ import annotations
import subprocess, re, shutil
from dataclasses import dataclass
from typing import Optional
from functools import cache

@dataclass(frozen=True)
class ToolVersion:
    name:    str
    found:   bool
    version: Optional[tuple[int, ...]] = None
    path:    Optional[str] = None

    @property
    def version_str(self) -> str:
        return ".".join(str(v) for v in self.version) if self.version else "unknown"

    def meets_minimum(self, *minimum: int) -> bool:
        if not self.found or self.version is None:
            return False
        return self.version >= tuple(minimum)


_VERSION_PROBES: dict[str, tuple[list[str], str]] = {
    "yosys":     (["yosys", "--version"],      r"Yosys (\d+)\.(\d+)(?:\.(\d+))?"),
    "openroad":  (["openroad", "-version"],    r"(\d+)\.(\d+)\.(\d+)"),
    "klayout":   (["klayout", "-v"],           r"(\d+)\.(\d+)\.(\d+)"),
    "verilator": (["verilator", "--version"],  r"Verilator (\d+)\.(\d+)"),
    "iverilog":  (["iverilog", "-V"],          r"Icarus Verilog version (\d+)\.(\d+)"),
    "ngspice":   (["ngspice", "-v"],           r"ngspice-(\d+)"),
    "kicad-cli": (["kicad-cli", "--version"],  r"(\d+)\.(\d+)\.(\d+)"),
}

MINIMUM_VERSIONS: dict[str, tuple[int, ...]] = {
    "yosys":     (0, 38),
    "openroad":  (2, 0),
    "klayout":   (0, 28, 0),
    "verilator": (5, 0),
    "iverilog":  (11, 0),
    "kicad-cli": (9, 0, 0),
}


@cache
def probe_tool(tool_name: str) -> ToolVersion:
    """探测工具版本，结果缓存整个进程生命周期。永远不抛出异常。"""
    if tool_name not in _VERSION_PROBES:
        return ToolVersion(name=tool_name, found=shutil.which(tool_name) is not None)
    args, pattern = _VERSION_PROBES[tool_name]
    path = shutil.which(args[0])
    if path is None:
        return ToolVersion(name=tool_name, found=False)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=5)
        m = re.search(pattern, r.stdout + r.stderr)
        if m:
            version = tuple(int(g) for g in m.groups() if g is not None)
            return ToolVersion(name=tool_name, found=True, version=version, path=path)  # type: ignore
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ToolVersion(name=tool_name, found=True, version=None, path=path)


def check_tool_requirements(required: list[str]) -> dict[str, str]:
    """返回 {tool: error_msg}，空字典表示全部满足。"""
    errors: dict[str, str] = {}
    for tool in required:
        tv = probe_tool(tool)
        if not tv.found:
            errors[tool] = (
                f"{tool} not installed. "
                f"See: https://auto-eda.rtfd.io/installation#{tool}"
            )
        elif tool in MINIMUM_VERSIONS:
            min_ver = MINIMUM_VERSIONS[tool]
            if not tv.meets_minimum(*min_ver):
                min_str = ".".join(str(v) for v in min_ver)
                errors[tool] = f"{tool} {tv.version_str} < minimum {min_str}. Please upgrade."
    return errors
```

#### 版本感知功能分派示例 (Yosys)

```python
# src/auto_eda/adapters/yosys_adapter.py
from auto_eda.adapters.tool_registry import probe_tool
import subprocess

def run_synthesis(rtl_file: str, top: str, output: str) -> dict:
    tv = probe_tool("yosys")
    if not tv.found:
        return {"success": False, "error": "yosys not installed"}
    parts = [
        f"read_verilog -sv {rtl_file}",
        f"synth -top {top} -flatten",
    ]
    # 版本特定优化: 0.45+ memory_share 改进
    if tv.meets_minimum(0, 45):
        parts.insert(-1, "memory_share -map")
    parts.append(f"write_json {output}")
    r = subprocess.run(["yosys", "-p", ";".join(parts)],
                       capture_output=True, text=True, timeout=300)
    return {"success": r.returncode == 0, "yosys_version": tv.version_str,
            "stdout": r.stdout, "stderr": r.stderr}
```

---

### 1.4 T5: 长时任务超时 [A4 得分 12/高]

**风险摘要**: EDA 综合/P&R 可运行数小时，MCP 请求-响应模式不适合长时任务，
需要 asyncio 超时控制 + SSE 进度报告。

#### asyncio 超时模式与进度报告

```python
# src/auto_eda/tasks/long_running.py
from __future__ import annotations
import asyncio, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable

class TaskStatus(Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    DONE     = "done"
    FAILED   = "failed"
    TIMEOUT  = "timeout"
    CANCELED = "canceled"

@dataclass
class TaskProgress:
    task_id:   str
    status:    TaskStatus
    percent:   float
    message:   str
    elapsed_s: float

@dataclass
class LongRunningTask:
    task_id:    str        = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status:     TaskStatus = TaskStatus.PENDING
    start_time: float      = field(default_factory=time.monotonic)
    _progress:  float      = 0.0
    _message:   str        = "Initializing"

    def update(self, percent: float, message: str) -> None:
        self._progress = min(100.0, max(0.0, percent))
        self._message  = message

    def to_progress(self) -> TaskProgress:
        return TaskProgress(
            task_id=self.task_id, status=self.status,
            percent=self._progress, message=self._message,
            elapsed_s=time.monotonic() - self.start_time,
        )


async def run_eda_tool_with_timeout(
    cmd: list[str],
    timeout_s: float,
    progress_parser: Optional[Callable[[str], Optional[float]]] = None,
    progress_callback: Optional[Callable[[TaskProgress], None]] = None,
    task: Optional[LongRunningTask] = None,
) -> dict:
    if task is None:
        task = LongRunningTask()
    task.status = TaskStatus.RUNNING
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _read(stream: asyncio.StreamReader,
                    buf: list[str], is_stderr: bool = False) -> None:
        async for raw in stream:
            line = raw.decode(errors="replace").rstrip()
            buf.append(line)
            if progress_parser and not is_stderr:
                pct = progress_parser(line)
                if pct is not None:
                    task.update(pct, line[:120])
                    if progress_callback:
                        progress_callback(task.to_progress())

    try:
        async with asyncio.timeout(timeout_s):
            await asyncio.gather(
                _read(proc.stdout, stdout_lines),
                _read(proc.stderr, stderr_lines, is_stderr=True),
            )
            await proc.wait()
    except asyncio.TimeoutError:
        task.status = TaskStatus.TIMEOUT
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
        return {
            "success": False, "task_id": task.task_id, "status": "timeout",
            "error": f"Exceeded timeout of {timeout_s}s",
            "stdout": "\n".join(stdout_lines[-50:]),
        }
    except asyncio.CancelledError:
        task.status = TaskStatus.CANCELED
        proc.kill(); await proc.wait()
        raise

    success = proc.returncode == 0
    task.status = TaskStatus.DONE if success else TaskStatus.FAILED
    return {
        "success": success, "task_id": task.task_id,
        "status": task.status.value, "returncode": proc.returncode,
        "stdout": "\n".join(stdout_lines), "stderr": "\n".join(stderr_lines),
        "elapsed_s": time.monotonic() - task.start_time,
    }


def openroad_progress_parser(line: str) -> Optional[float]:
    import re
    m = re.search(r"(\d+\.?\d*)\s*%", line)
    if m:
        return float(m.group(1))
    milestones = {
        "Starting global placement": 10.0,
        "Global placement complete": 30.0,
        "Starting clock tree synthesis": 50.0,
        "CTS complete": 65.0,
        "Starting global routing": 70.0,
        "Detailed routing complete": 95.0,
    }
    for kw, pct in milestones.items():
        if kw.lower() in line.lower():
            return pct
    return None


def yosys_progress_parser(line: str) -> Optional[float]:
    stages = {
        "Executing SYNTH pass": 10.0, "Executing PROC pass": 20.0,
        "Executing OPT pass": 40.0,  "Executing TECHMAP pass": 75.0,
        "Executing ABC pass": 85.0,  "End of script": 100.0,
    }
    for kw, pct in stages.items():
        if kw in line:
            return pct
    return None
```

#### MCP FastMCP 集成模式

```python
# src/auto_eda/mcp_tools/synthesis.py
from mcp.server.fastmcp import FastMCP, Context
from auto_eda.tasks.long_running import (
    run_eda_tool_with_timeout, LongRunningTask, yosys_progress_parser
)

mcp = FastMCP("auto_eda")

@mcp.tool()
async def synthesize_rtl(
    rtl_file: str,
    top_module: str,
    output_netlist: str,
    timeout_seconds: float = 3600.0,
    ctx: Context = None,
) -> str:
    """Run Yosys RTL synthesis with real-time progress reporting."""
    task = LongRunningTask()

    async def _report(progress) -> None:
        if ctx:
            await ctx.report_progress(
                progress=int(progress.percent), total=100,
                message=f"[{progress.task_id}] {progress.message} ({progress.elapsed_s:.0f}s)",
            )

    result = await run_eda_tool_with_timeout(
        cmd=["yosys", "-p",
             f"read_verilog -sv {rtl_file}; "
             f"synth -top {top_module} -flatten; "
             f"write_json {output_netlist}"],
        timeout_s=timeout_seconds,
        progress_parser=yosys_progress_parser,
        progress_callback=_report,
        task=task,
    )
    if result["status"] == "timeout":
        return (f"Synthesis timed out after {timeout_seconds}s. "
                f"Consider increasing timeout_seconds or splitting the design. "
                f"Task ID: {task.task_id}")
    if not result["success"]:
        return f"Synthesis failed (rc={result['returncode']}):\n{result['stderr'][-2000:]}"
    return (f"Synthesis completed in {result['elapsed_s']:.1f}s. "
            f"Netlist: {output_netlist}")
```

---

## 2. 技术债务预防清单

### 2.1 接口稳定性保证策略

```python
# src/auto_eda/interfaces/v1/tool_contracts.py
"""
PUBLIC API CONTRACT - v1
此模块中的所有类型构成对外公开接口。
合并到 main 后 MUST NOT 做破坏性变更（删除字段、修改必填参数）。
只能新增带默认值的可选字段。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ToolCallRequest:
    """所有工具输入基类。v1 必填字段: tool_name。"""
    tool_name: str
    timeout_s: float = 300.0   # v1.1 新增，带默认值
    dry_run:   bool  = False   # v1.1 新增，带默认值

@dataclass
class ToolCallResponse:
    """所有工具输出基类。"""
    success:    bool
    tool_name:  str
    message:    str
    data:       Optional[dict] = None
    error:      Optional[str]  = None
    warnings:   list[str]      = field(default_factory=list)
    debug_info: Optional[dict] = None   # v1.1 新增

    def to_mcp_text(self) -> str:
        status = "OK" if self.success else "ERROR"
        parts = [f"[{status}] {self.tool_name}: {self.message}"]
        parts += [f"  WARNING: {w}" for w in self.warnings]
        if not self.success and self.error:
            parts.append(f"  Error detail: {self.error}")
        return "\n".join(parts)
```

### 2.2 破坏性变更检测测试

```python
# tests/contracts/test_interface_stability.py
import inspect, dataclasses
from auto_eda.interfaces.v1.tool_contracts import ToolCallRequest, ToolCallResponse

def test_request_required_fields_unchanged():
    params = inspect.signature(ToolCallRequest.__init__).parameters
    assert "tool_name" in params
    assert params["tool_name"].default is inspect.Parameter.empty

def test_response_required_fields_unchanged():
    params = inspect.signature(ToolCallResponse.__init__).parameters
    for f in ["success", "tool_name", "message"]:
        assert f in params
        assert params[f].default is inspect.Parameter.empty

def test_optional_fields_have_defaults():
    v1_required = {"success", "tool_name", "message"}
    for f in dataclasses.fields(ToolCallResponse):
        if f.name not in v1_required:
            ok = (f.default is not dataclasses.MISSING
                  or f.default_factory is not dataclasses.MISSING)
            assert ok, f"Field '{f.name}' has no default — breaks backward compat"
```

### 2.3 版本语义化规范

```
MAJOR (x.0.0): 破坏性变更
  - 删除已发布的 MCP 工具
  - 修改工具必填参数签名
  - 删除 public Python API

MINOR (x.y.0): 向后兼容新功能
  - 新增 MCP 工具
  - 现有工具新增可选参数（带默认值）
  - 支持新 EDA 工具版本

PATCH (x.y.z): Bug 修复 + 性能优化

预发布标签: alpha.N / beta.N (功能冻结) / rc.N (发布候选)
```

### 2.4 向后兼容性测试设计

```python
# tests/compat/test_backward_compat.py
from auto_eda.interfaces.v1.tool_contracts import ToolCallRequest, ToolCallResponse

def test_request_v1_defaults_stable():
    req = ToolCallRequest(tool_name="run_drc")
    assert req.timeout_s == 300.0
    assert req.dry_run is False

def test_response_minimal_construction():
    resp = ToolCallResponse(success=True, tool_name="run_drc", message="OK")
    assert resp.data is None
    assert resp.warnings == []
    assert "[OK]" in resp.to_mcp_text()

def test_response_error_format_stable():
    resp = ToolCallResponse(
        success=False, tool_name="synthesize",
        message="Synthesis failed", error="yosys exit 1"
    )
    text = resp.to_mcp_text()
    assert "[ERROR]" in text and "yosys exit 1" in text
```

### 2.5 文档债务预防规则

```
规则1 (工具注册即文档):
  所有 @mcp.tool() 必须包含:
  - 单行 docstring 描述（用于 MCP tool description）
  - 所有参数的 Annotated[type, description] 类型注解
  - 明确的返回值格式说明
  CI 检查: 缺少 docstring 的工具注册视为 lint 错误

规则2 (CHANGELOG 强制):
  每个 PR 必须更新 CHANGELOG.md，CI 检查未更新的 PR 不得合并

规则3 (ADR 记录):
  重要架构决策写 ADR (Architecture Decision Record)
  docs/adr/ADR-001-python-over-typescript.md
  docs/adr/ADR-002-kicad-ipc-fallback-strategy.md
  格式: 背景 / 决策 / 后果 / 替代方案

规则4 (示例驱动):
  每个新工具附带:
  - examples/<tool_name>_example.py  (可独立运行)
  - tests/integration/test_<tool_name>_integration.py
```

---

## 3. EDA 工具依赖管理风险

### 3.1 工具安装检测与友好提示

```python
# src/auto_eda/adapters/install_hints.py
from __future__ import annotations
import platform

INSTALL_GUIDES: dict[str, dict[str, str]] = {
    "yosys":    {"linux": "sudo apt install yosys",
                 "macos": "brew install yosys",
                 "windows": "Use WSL2 or winget install YosysHQ.Yosys",
                 "docs": "https://yosyshq.net/yosys/download.html"},
    "openroad": {"linux": "See https://github.com/The-OpenROAD-Project/OpenROAD",
                 "macos": "brew tap The-OpenROAD-Project/tap && brew install openroad",
                 "windows": "docker pull openroad/flow",
                 "docs": "https://openroad.readthedocs.io/"},
    "klayout":  {"linux": "sudo apt install klayout",
                 "macos": "brew install --cask klayout",
                 "windows": "https://www.klayout.de/build.html",
                 "docs": "https://www.klayout.de/"},
    "iverilog": {"linux": "sudo apt install iverilog",
                 "macos": "brew install icarus-verilog",
                 "windows": "winget install icarus-verilog.icarus-verilog",
                 "docs": "http://iverilog.icarus.com/"},
    "ngspice":  {"linux": "sudo apt install ngspice",
                 "macos": "brew install ngspice",
                 "windows": "https://ngspice.sourceforge.io/download.html",
                 "docs": "https://ngspice.sourceforge.io/"},
}

def format_install_hint(tool_name: str) -> str:
    guide = INSTALL_GUIDES.get(tool_name, {})
    if not guide:
        return f"Please install '{tool_name}' and ensure it is on PATH."
    sys = platform.system().lower()
    key = "linux" if sys == "linux" else ("macos" if sys == "darwin" else "windows")
    return (
        f"Tool '{tool_name}' not found.\n"
        f"  {key}: {guide.get(key, 'See docs')}\n"
        f"  Docs: {guide.get('docs', '')}"
    )
```

### 3.2 优雅降级与工具降级链

```python
# src/auto_eda/adapters/degradation.py
from __future__ import annotations
from typing import Optional
from auto_eda.adapters.tool_registry import probe_tool
from auto_eda.adapters.install_hints import format_install_hint


class ToolFallbackChain:
    """
    工具降级链：按优先级尝试多个工具，使用第一个可用的。
    用于同类工具有多种实现的场景（如 Verilog 仿真器）。
    """
    def __init__(self, primary: str, *fallbacks: str) -> None:
        self._chain = [primary] + list(fallbacks)

    def get_available(self) -> Optional[str]:
        for tool in self._chain:
            if probe_tool(tool).found:
                return tool
        return None

    def unavailable_message(self) -> str:
        hints = [format_install_hint(t) for t in self._chain]
        return (
            f"None of the required tools are available: {self._chain}.\n"
            "Install at least one:\n" + "\n---\n".join(hints)
        )


# 预定义降级链
VERILOG_SIM_CHAIN = ToolFallbackChain("verilator", "iverilog")
SPICE_SIM_CHAIN   = ToolFallbackChain("ngspice", "xyce")
LAYOUT_VIEW_CHAIN = ToolFallbackChain("klayout", "magic")
```

### 3.3 平台差异处理

```python
# src/auto_eda/platform/paths.py
from __future__ import annotations
import os, platform, pathlib
from typing import Optional

def normalize_path(p: str) -> str:
    """跨平台路径规范化，在 Windows 上返回正斜杠（EDA CLI 工具兼容）。"""
    resolved = pathlib.Path(p).resolve()
    return resolved.as_posix() if platform.system() == "Windows" else str(resolved)

def get_kicad_ipc_socket_paths() -> list[str]:
    sys = platform.system()
    if sys == "Linux":
        uid = os.getuid() if hasattr(os, "getuid") else 0
        return [f"/run/user/{uid}/kicad/api.sock", "/tmp/kicad/api.sock"]
    if sys == "Darwin":
        return [os.path.expanduser("~/Library/Application Support/kicad/api.sock")]
    return ["\\\\.\\pipe\\kicad-api"]

LINUX_ONLY_TOOLS = {"magic"}

def warn_if_linux_only(tool: str) -> Optional[str]:
    if tool in LINUX_ONLY_TOOLS and platform.system() != "Linux":
        return (
            f"Tool '{tool}' is Linux-only. On {platform.system()}, "
            f"use Docker: docker run -it auto-eda:ic"
        )
    return None
```

---

## 4. LLM+EDA 特有风险防护

### 4.1 危险操作防护

```python
# src/auto_eda/security/operation_guard.py
from __future__ import annotations
import pathlib, re
from dataclasses import dataclass
from typing import Optional

@dataclass
class GuardResult:
    allowed: bool
    reason:  Optional[str] = None

class EDAOperationGuard:
    """
    防止 LLM Agent 执行危险操作的护栏层。
    所有文件写入/删除/命令执行前必须通过此检查。
    """
    PROTECTED_EXTENSIONS = {
        ".kicad_pcb", ".kicad_sch", ".kicad_pro",
        ".gds", ".gdsii", ".oas",
        ".v", ".sv", ".vhd", ".vhdl",
        ".lef", ".def", ".lib", ".sdc",
    }
    INJECTION_RE = re.compile(
        r"[;&|`$()<>\\]"
        r"|\.\.[/\\]"
        r"|/etc/|/proc/"
    )

    def check_write(self, target: str, source: Optional[str] = None) -> GuardResult:
        p = pathlib.Path(target).resolve()
        if p.exists() and p.suffix.lower() in self.PROTECTED_EXTENSIONS:
            return GuardResult(False,
                f"Refusing to overwrite protected design file: {p}. "
                "Create a copy first or use an output directory.")
        return GuardResult(True)

    def check_delete(self, target: str) -> GuardResult:
        p = pathlib.Path(target).resolve()
        if p.suffix.lower() in self.PROTECTED_EXTENSIONS:
            return GuardResult(False, f"Refusing to delete design source file: {p}.")
        return GuardResult(True)

    def check_command(self, cmd: list[str]) -> GuardResult:
        for arg in cmd[1:]:
            if self.INJECTION_RE.search(arg):
                return GuardResult(False,
                    f"Potential command injection in argument: '{arg}'. "
                    "Arguments must not contain shell special characters.")
        return GuardResult(True)


_GUARD = EDAOperationGuard()

def guard_write(path: str, source: Optional[str] = None) -> None:
    result = _GUARD.check_write(path, source)
    if not result.allowed:
        raise PermissionError(f"[EDAOperationGuard] {result.reason}")

def guard_delete(path: str) -> None:
    result = _GUARD.check_delete(path)
    if not result.allowed:
        raise PermissionError(f"[EDAOperationGuard] {result.reason}")

def guard_command(cmd: list[str]) -> None:
    result = _GUARD.check_command(cmd)
    if not result.allowed:
        raise PermissionError(f"[EDAOperationGuard] {result.reason}")
```

**命令注入防护规则**: 所有传给 subprocess 的参数必须通过 `guard_command()` 验证。
永远使用列表形式调用 subprocess，绝不使用 `shell=True` 拼接字符串。

```python
# 错误示范 (NEVER)
subprocess.run(f"yosys -p '{script}' {file}", shell=True)

# 正确示范
from auto_eda.security.operation_guard import guard_command
cmd = ["yosys", "-p", script, file]
guard_command(cmd)
subprocess.run(cmd, capture_output=True)  # shell=False (default)
```

### 4.2 幂等性设计

```python
# src/auto_eda/tasks/idempotency.py
from __future__ import annotations
import hashlib, json, pathlib, time
from dataclasses import dataclass, asdict
from typing import Any, Optional

@dataclass
class TaskFingerprint:
    tool:      str
    params:    dict
    timestamp: float = 0.0
    result:    Optional[dict] = None

    def key(self) -> str:
        canonical = json.dumps({"tool": self.tool, "params": self.params},
                               sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class IdempotentTaskCache:
    """
    EDA 工具调用幂等缓存。
    相同参数的工具调用在 TTL 内直接返回缓存结果，
    避免 LLM 重复触发昂贵操作。
    """
    def __init__(self, cache_dir: str, ttl_s: float = 3600.0) -> None:
        self._dir = pathlib.Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl_s

    def get(self, tool: str, params: dict) -> Optional[dict]:
        key = TaskFingerprint(tool=tool, params=params).key()
        f = self._dir / f"{key}.json"
        if not f.exists():
            return None
        try:
            data = json.loads(f.read_text())
            if time.time() - data.get("timestamp", 0) > self._ttl:
                f.unlink(missing_ok=True)
                return None
            return data.get("result")
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, tool: str, params: dict, result: dict) -> None:
        fp = TaskFingerprint(tool=tool, params=params, timestamp=time.time(), result=result)
        key = fp.key()
        (self._dir / f"{key}.json").write_text(
            json.dumps(asdict(fp), ensure_ascii=False, indent=2)
        )

    def invalidate(self, tool: str, params: dict) -> None:
        key = TaskFingerprint(tool=tool, params=params).key()
        (self._dir / f"{key}.json").unlink(missing_ok=True)
```

### 4.3 EDA 输出可信度验证

```python
# src/auto_eda/validation/output_trust.py
from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class TrustAssessment:
    trustworthy: bool
    confidence:  float
    warnings:    list[str]

def assess_yosys_output(stdout: str, returncode: int) -> TrustAssessment:
    warnings: list[str] = []
    if returncode != 0:
        return TrustAssessment(False, 0.0, ["Yosys returned non-zero exit code"])
    m = re.search(r"Number of cells:\s*(\d+)", stdout)
    if m:
        cells = int(m.group(1))
        if cells == 0:
            warnings.append("Synthesis produced 0 cells. Design may be optimized away.")
            return TrustAssessment(False, 0.3, warnings)
        if cells > 1_000_000:
            warnings.append(f"Very large cell count ({cells}). Verify design hierarchy.")
    if "ABC RESULTS" not in stdout:
        warnings.append("ABC optimization step may not have completed.")
    return TrustAssessment(True, 0.9, warnings)

def assess_openroad_output(stdout: str, stderr: str, returncode: int) -> TrustAssessment:
    warnings: list[str] = []
    if returncode != 0:
        return TrustAssessment(False, 0.0, ["OpenROAD returned non-zero exit code"])
    m = re.search(r"(\d+)\s+design rule violations", stdout + stderr, re.IGNORECASE)
    if m and int(m.group(1)) > 0:
        warnings.append(f"DRV count: {m.group(1)} — routing not clean.")
        return TrustAssessment(False, 0.6, warnings)
    if "VIOLATED" in stdout or "VIOLATED" in stderr:
        warnings.append("Timing violations detected. Design may not meet constraints.")
        return TrustAssessment(False, 0.5, warnings)
    return TrustAssessment(True, 0.85, warnings)
```

---

## 5. 开源项目维护风险

### 5.1 上游依赖健康度监控

```python
# src/auto_eda/maintenance/dep_health.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class HealthStatus(Enum):
    HEALTHY   = "healthy"    # >= 1 commit/month
    STABLE    = "stable"     # 1-12 commits/year
    AT_RISK   = "at_risk"    # single maintainer or 6+ months inactive
    ABANDONED = "abandoned"  # 12+ months no activity

@dataclass
class DepHealthRecord:
    name:             str
    status:           HealthStatus
    last_commit_days: int
    maintainer_count: int
    has_commercial:   bool
    notes:            str = ""
    fallback_tool:    Optional[str] = None

DEP_HEALTH_SNAPSHOT: list[DepHealthRecord] = [
    DepHealthRecord("yosys",     HealthStatus.HEALTHY,  3,  30,  True,  "YosysHQ 商业支持"),
    DepHealthRecord("openroad",  HealthStatus.HEALTHY,  2,  50,  True,  "DARPA/Google 资助，600+ 流片"),
    DepHealthRecord("klayout",   HealthStatus.STABLE,  14,   5,  False, "Matthias Koefferlein 主力",
                    fallback_tool="gdstk for I/O"),
    DepHealthRecord("magic",     HealthStatus.AT_RISK, 45,   1,  False, "Tim Edwards 单一维护者，仅 Linux",
                    fallback_tool="klayout"),
    DepHealthRecord("ngspice",   HealthStatus.STABLE,  30,   3,  False, "小团队，长期稳定",
                    fallback_tool="xyce"),
    DepHealthRecord("kicad",     HealthStatus.HEALTHY,  1, 100,  True,  "CERN/RPi 支持"),
    DepHealthRecord("cocotb",    HealthStatus.HEALTHY,  7,  20,  False, "活跃社区，纯 Python"),
    DepHealthRecord("verilator", HealthStatus.HEALTHY,  5,  15,  True,  "商业用户广泛"),
]

def get_at_risk_deps() -> list[DepHealthRecord]:
    return [d for d in DEP_HEALTH_SNAPSHOT
            if d.status in (HealthStatus.AT_RISK, HealthStatus.ABANDONED)]
```

#### GitHub Actions 上游变更监控

```yaml
# .github/workflows/dep_monitor.yml
name: Upstream Dependency Monitor
on:
  schedule:
    - cron: '0 9 * * 1'   # 每周一 09:00 UTC
  workflow_dispatch:
jobs:
  check_versions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Magic VLSI single-maintainer risk
        run: |
          LAST=$(curl -s \
            "https://api.github.com/repos/RTimothyEdwards/magic/commits?per_page=1" \
            | jq -r '.[0].commit.committer.date')
          DAYS=$(( ( $(date +%s) - $(date -d "$LAST" +%s) ) / 86400 ))
          echo "Magic last commit: $LAST ($DAYS days ago)"
          if [ "$DAYS" -gt "90" ]; then
            echo "::warning::Magic VLSI not updated in $DAYS days (single maintainer risk)"
          fi
      - name: Check yosys latest release
        run: |
          LATEST=$(curl -s https://api.github.com/repos/YosysHQ/yosys/releases/latest \
                   | jq -r '.tag_name')
          echo "Yosys latest release: $LATEST"
```

### 5.2 核心功能 vs 扩展功能划分

```
Core (作者维护，保证质量):
  - MCP 协议层 (FastMCP server/tools/resources)
  - EDA 工具探测与版本检测 (tool_registry)
  - 危险操作防护层 (operation_guard)
  - HDL 静态验证 Layer1-2（无需 EDA 工具）
  - 异步任务管理框架 (long_running)
  - 幂等缓存 (idempotency)
  - 接口稳定性契约 (tool_contracts)

Standard (维护者认领，至少一人负责):
  - KiCad 集成 (高需求，P0)
  - Yosys 综合集成
  - OpenROAD PnR 集成
  - cocotb 验证集成
  - KLayout 版图操作

Contrib (社区驱动，标注 experimental):
  - ngspice/PySpice 仿真
  - Magic VLSI (Linux only)
  - 商业工具脚本生成 (Synopsys TCL, Cadence SKILL)
  - 特定 PDK 集成 (sky130, GF180)

安装分组:
  pip install auto-eda           # core only
  pip install auto-eda[pcb]      # + KiCad
  pip install auto-eda[ic]       # + Yosys + OpenROAD + KLayout
  pip install auto-eda[sim]      # + ngspice + cocotb
  pip install auto-eda[full]     # everything
```

### 5.3 社区维护成本控制

```
降低维护成本的关键决策:

1. 工具集成设计原则
   - 每个 EDA 工具适配器独立文件，互不依赖
   - 工具不可用时返回友好提示而非崩溃（维护者无需修复用户环境）
   - 新工具集成只需实现 3 个接口: probe_version / run_tool / parse_output

2. Issue 分类标签
   - bug:core       -- 作者必须修复
   - bug:contrib    -- 社区修复，30天无响应则关闭
   - feature:pcb    -- PCB 维护者处理
   - help-wanted    -- 欢迎 PR，无时间承诺
   - wontfix        -- 超出范围，明确拒绝

3. CI 策略
   - core tests: 每次 PR 必须通过，无 EDA 工具依赖，mock 模式运行
   - contrib tests: 仅在有对应工具的 Docker 环境中运行，允许跳过
   - release gate: 全量测试 + 集成测试通过方可发布
```

---

## 6. 综合风险缓解优先级矩阵

| 优先级 | 风险ID | 风险描述 | 关键缓解措施 | 实施阶段 |
|--------|--------|----------|-------------|----------|
| P0-必须 | T7 | LLM 幻觉 HDL | HdlValidationPipeline 四层防护 | MVP v0.1 |
| P0-必须 | T1 | KiCad IPC 不稳定 | KiCadDispatcher + graceful fallback | MVP v0.1 |
| P0-必须 | — | 危险文件操作 | EDAOperationGuard 全局护栏 | MVP v0.1 |
| P0-必须 | — | 命令注入 | guard_command + shell=False | MVP v0.1 |
| P1-高 | T5 | 长时任务超时 | run_eda_tool_with_timeout + progress | v0.2 |
| P1-高 | T3 | 工具版本碎片化 | probe_tool + ToolFallbackChain | v0.2 |
| P1-高 | T4 | 跨平台兼容 | normalize_path + Linux-only 警告 | v0.2 |
| P2-中 | E1 | 上游工具停维 | dep_health 监控 + fallback chain | v0.3 |
| P2-中 | O3 | 版本兼容维护 | 语义化版本 + 接口契约测试 | v0.2 |
| P2-中 | T7+ | LLM 输出可信度 | assess_yosys/openroad_output | v0.3 |
| P3-低 | L3 | EDA IP 安全 | 本地部署优先，无云端传输 | v0.4 |
| P3-低 | E1 | Magic 单维护者 | 周监控 + KLayout 替代链 | 持续 |

### MVP v0.1 实施检查清单

- [ ] `EDAOperationGuard` 集成到所有文件操作 MCP 工具
- [ ] `guard_command()` 覆盖所有 subprocess 调用点
- [ ] `HdlValidationPipeline.validate()` 在返回 HDL 前强制执行
- [ ] `detect_kicad_capabilities()` 在 KiCad 工具初始化时调用
- [ ] `KiCadDispatcher` 替代所有直接 KiCad API 调用
- [ ] `ToolCallRequest/Response` 作为所有工具 I/O 基类
- [ ] 接口契约测试 `test_interface_stability.py` 加入 CI 必过项
- [ ] 版本探测测试矩阵 `test_version_compat.py` 加入 CI
- [ ] GitHub Actions `dep_monitor.yml` 部署监控上游变更
- [ ] 所有 @mcp.tool() 函数有完整 docstring 和类型注解

---

*本文档基于 A4 风险评估、A1 技术可行性、A7 技术栈决策三份报告综合生成。*
*代码示例为设计参考，需根据实际 KiCad/EDA 工具 API 版本调整。*
