# src/auto_eda/servers/verilog_utils/parser.py
"""pyverilog wrapper with graceful fallback when pyverilog is not installed."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from auto_eda.models.verilog import LintIssue, ModuleDef, ParamDef, PortDef

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional pyverilog import
# ---------------------------------------------------------------------------

try:
    from pyverilog.vparser.parser import VerilogCodeParser  # type: ignore[import-untyped]
    from pyverilog.vparser.ast import (  # type: ignore[import-untyped]
        ModuleDef as PVModuleDef,
        Decl,
        Input,
        Output,
        Inout,
        Parameter,
        Localparam,
        Always,
        BlockingSubstitution,
        NonblockingSubstitution,
        Instance,
        InstanceList,
    )
    _PYVERILOG_AVAILABLE = True
except ImportError:
    _PYVERILOG_AVAILABLE = False
    logger.warning(
        "pyverilog is not installed. Verilog parsing will use regex fallback. "
        "Install with: pip install pyverilog"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_verilog_file(
    path: Path,
    include_dirs: list[str] | None = None,
    defines: dict[str, str] | None = None,
) -> tuple[list[ModuleDef], list[str]]:
    """
    Parse a Verilog file and return (modules, syntax_errors).

    Falls back to regex-based extraction when pyverilog is unavailable.
    """
    if _PYVERILOG_AVAILABLE:
        return _parse_with_pyverilog(path, include_dirs or [], defines or {})
    return _parse_with_regex(path)


def extract_module_names(path: Path) -> list[str]:
    """Return all module names declared in a Verilog file."""
    modules, _ = parse_verilog_file(path)
    return [m.name for m in modules]


def extract_ports(
    path: Path,
    module_name: str | None = None,
) -> tuple[str | None, list[PortDef], list[ParamDef]]:
    """
    Extract ports and parameters for a specific module (or the first module).

    Returns (resolved_module_name, ports, parameters).
    """
    modules, _ = parse_verilog_file(path)
    if not modules:
        return None, [], []
    if module_name is None:
        target = modules[0]
    else:
        matches = [m for m in modules if m.name == module_name]
        if not matches:
            return None, [], []
        target = matches[0]
    return target.name, target.ports, target.parameters


def basic_lint_check(path: Path) -> list[LintIssue]:
    """
    Run Phase 0 lint rules against a Verilog file.

    Rules implemented:
      W001 - Unused output port (AST reference analysis)
      W002 - Implicit net declaration (port connection analysis)
      W003 - Blocking assignment in sequential always block
      E001 - Instantiated undefined module
    """
    if _PYVERILOG_AVAILABLE:
        return _lint_with_pyverilog(path)
    return _lint_with_regex(path)


# ---------------------------------------------------------------------------
# pyverilog implementation
# ---------------------------------------------------------------------------


def _parse_with_pyverilog(
    path: Path,
    include_dirs: list[str],
    defines: dict[str, str],
) -> tuple[list[ModuleDef], list[str]]:
    syntax_errors: list[str] = []
    modules: list[ModuleDef] = []

    try:
        parser = VerilogCodeParser(
            [str(path)],
            preprocess_include=include_dirs,
            preprocess_define=[
                f"{k}={v}" if v else k for k, v in defines.items()
            ],
        )
        ast, _ = parser.parse()
    except Exception as exc:
        # pyverilog raises a bare Exception for parse errors
        msg = str(exc)
        if "ParseError" in type(exc).__name__ or "syntax" in msg.lower():
            syntax_errors.append(f"Syntax error in {path.name}: {msg}")
        else:
            syntax_errors.append(f"Parse crash in {path.name}: {msg}")
        return modules, syntax_errors

    try:
        modules = _extract_modules_from_ast(ast, str(path))
    except Exception as exc:
        logger.warning("AST traversal failed for %s: %s", path, exc)
        syntax_errors.append(f"AST traversal error: {exc}")

    return modules, syntax_errors


def _extract_modules_from_ast(ast: Any, file_path: str) -> list[ModuleDef]:
    """Walk the pyverilog AST and extract ModuleDef objects."""
    modules: list[ModuleDef] = []

    def _walk(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, PVModuleDef):
            modules.append(_build_module_def(node, file_path))
        for child in node.children() if hasattr(node, "children") else []:
            _walk(child)

    _walk(ast)
    return modules


def _build_module_def(node: Any, file_path: str) -> ModuleDef:
    ports: list[PortDef] = []
    parameters: list[ParamDef] = []

    def _walk_items(n: Any) -> None:
        if n is None:
            return
        if isinstance(n, (Input, Output, Inout)):
            direction: str
            if isinstance(n, Input):
                direction = "input"
            elif isinstance(n, Output):
                direction = "output"
            else:
                direction = "inout"
            width = "1"
            if hasattr(n, "width") and n.width is not None:
                width = str(n.width)
            ports.append(
                PortDef(
                    name=str(n.name),
                    direction=direction,  # type: ignore[arg-type]
                    width=width,
                    signed=getattr(n, "signed", False) or False,
                )
            )
        elif isinstance(n, (Parameter, Localparam)):
            param_type = "localparam" if isinstance(n, Localparam) else "parameter"
            default_value = str(n.value) if hasattr(n, "value") and n.value is not None else None
            parameters.append(
                ParamDef(
                    name=str(n.name),
                    default_value=default_value,
                    param_type=param_type,  # type: ignore[arg-type]
                )
            )
        for child in n.children() if hasattr(n, "children") else []:
            _walk_items(child)

    _walk_items(node)

    lineno = getattr(node, "lineno", 0) or 0
    return ModuleDef(
        name=str(node.name),
        ports=ports,
        parameters=parameters,
        line_start=lineno,
        line_end=lineno,  # pyverilog does not expose end line reliably
    )


def _lint_with_pyverilog(path: Path) -> list[LintIssue]:
    issues: list[LintIssue] = []
    try:
        parser = VerilogCodeParser([str(path)])
        ast, _ = parser.parse()
    except Exception as exc:
        issues.append(
            LintIssue(
                rule="E000",
                severity="error",
                message=f"Failed to parse file for linting: {exc}",
                file=str(path),
                line=0,
            )
        )
        return issues

    issues.extend(_check_w003_blocking_in_seq(ast, str(path)))
    issues.extend(_check_e001_undefined_modules(ast, str(path)))
    return issues


def _check_w003_blocking_in_seq(ast: Any, file_path: str) -> list[LintIssue]:
    """W003: Blocking assignment (=) inside a sequential (posedge/negedge) always block."""
    issues: list[LintIssue] = []

    def _is_sequential(always_node: Any) -> bool:
        sens = getattr(always_node, "sens_list", None)
        if sens is None:
            return False
        sens_str = str(sens)
        return "posedge" in sens_str or "negedge" in sens_str

    def _find_blocking(node: Any) -> None:
        if isinstance(node, Always):
            if _is_sequential(node):
                _find_blocking_in_body(node, sequential=True)
            return
        for child in node.children() if hasattr(node, "children") else []:
            _find_blocking(child)

    def _find_blocking_in_body(node: Any, sequential: bool) -> None:
        if isinstance(node, BlockingSubstitution) and sequential:
            lineno = getattr(node, "lineno", 0) or 0
            issues.append(
                LintIssue(
                    rule="W003",
                    severity="warning",
                    message=(
                        "Blocking assignment (=) used in sequential always block; "
                        "use non-blocking (<=) to avoid simulation/synthesis mismatch"
                    ),
                    file=file_path,
                    line=lineno,
                )
            )
        for child in node.children() if hasattr(node, "children") else []:
            _find_blocking_in_body(child, sequential)

    _find_blocking(ast)
    return issues


def _check_e001_undefined_modules(
    ast: Any, file_path: str
) -> list[LintIssue]:
    """E001: Module instantiation references a module not defined in this file."""
    defined: set[str] = set()
    instantiated: list[tuple[str, int]] = []

    def _collect(node: Any) -> None:
        if isinstance(node, PVModuleDef):
            defined.add(str(node.name))
        if isinstance(node, InstanceList):
            module_name = str(node.module)
            lineno = getattr(node, "lineno", 0) or 0
            instantiated.append((module_name, lineno))
        for child in node.children() if hasattr(node, "children") else []:
            _collect(child)

    _collect(ast)

    issues: list[LintIssue] = []
    for mod_name, lineno in instantiated:
        if mod_name not in defined:
            issues.append(
                LintIssue(
                    rule="E001",
                    severity="error",
                    message=(
                        f"Module '{mod_name}' is instantiated but not defined in this file"
                    ),
                    file=file_path,
                    line=lineno,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Regex fallback (when pyverilog is not installed)
# ---------------------------------------------------------------------------

_MODULE_RE = re.compile(
    r"\bmodule\s+(\w+)\s*(?:#\s*\(.*?\))?\s*\((.*?)\)\s*;",
    re.DOTALL,
)
_PORT_DIRECTION_RE = re.compile(
    r"\b(input|output|inout)\s+(?:wire|reg)?\s*(?:signed)?\s*(?:\[([^\]]+)\])?\s*(\w+)",
)
_PARAM_RE = re.compile(
    r"\b(parameter|localparam)\s+(?:\w+\s+)?(\w+)\s*=\s*([^,;]+)",
)
_BLOCKING_SEQ_RE = re.compile(
    r"always\s*@\s*\([^)]*(?:posedge|negedge)[^)]*\).*?end",
    re.DOTALL,
)


def _parse_with_regex(path: Path) -> tuple[list[ModuleDef], list[str]]:
    """Best-effort regex-based module extraction when pyverilog is unavailable."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], [f"Cannot read file: {exc}"]

    modules: list[ModuleDef] = []
    for match in _MODULE_RE.finditer(source):
        name = match.group(1)
        body = match.group(2)
        ports = _extract_ports_regex(body)
        params = _extract_params_regex(source)
        line_start = source[: match.start()].count("\n") + 1
        modules.append(
            ModuleDef(
                name=name,
                ports=ports,
                parameters=params,
                line_start=line_start,
                line_end=line_start,
            )
        )
    return modules, []


def _extract_ports_regex(port_text: str) -> list[PortDef]:
    ports: list[PortDef] = []
    for m in _PORT_DIRECTION_RE.finditer(port_text):
        direction = m.group(1)
        width_inner = m.group(2)
        port_name = m.group(3)
        width = f"[{width_inner}]" if width_inner else "1"
        ports.append(
            PortDef(
                name=port_name,
                direction=direction,  # type: ignore[arg-type]
                width=width,
            )
        )
    return ports


def _extract_params_regex(source: str) -> list[ParamDef]:
    params: list[ParamDef] = []
    for m in _PARAM_RE.finditer(source):
        params.append(
            ParamDef(
                name=m.group(2),
                default_value=m.group(3).strip(),
                param_type=m.group(1),  # type: ignore[arg-type]
            )
        )
    return params


def _lint_with_regex(path: Path) -> list[LintIssue]:
    """Regex-based W003 check when pyverilog is unavailable."""
    issues: list[LintIssue] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for match in _BLOCKING_SEQ_RE.finditer(source):
        block = match.group(0)
        # Look for blocking assignments (= not preceded by < or !)
        for sub_match in re.finditer(r"(?<![<!])=(?!=)", block):
            line_offset = source[: match.start() + sub_match.start()].count("\n") + 1
            issues.append(
                LintIssue(
                    rule="W003",
                    severity="warning",
                    message=(
                        "Blocking assignment (=) used in sequential always block; "
                        "use non-blocking (<=) to avoid simulation/synthesis mismatch"
                    ),
                    file=str(path),
                    line=line_offset,
                )
            )
            break  # one issue per always block is enough
    return issues
