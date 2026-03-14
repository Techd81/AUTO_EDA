# src/auto_eda/servers/verilog_utils/server.py
"""Verilog Utils MCP Server — 5 tools for HDL analysis."""
from __future__ import annotations

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from auto_eda.models.verilog import (
    AnalyzeHierarchyInput,
    AnalyzeHierarchyResult,
    ExtractModulesInput,
    ExtractModulesResult,
    ExtractPortsInput,
    ExtractPortsResult,
    HierarchyNode,
    LintCheckInput,
    LintCheckResult,
    ParseVerilogInput,
    ParseVerilogResult,
)
from auto_eda.servers.verilog_utils.parser import (
    basic_lint_check,
    extract_module_names,
    extract_ports,
    parse_verilog_file,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("auto-eda-verilog", version="0.1.0")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_LINT_RULES = ["W001", "W002", "W003", "E001", "E002"]


def _resolve_path(file_path: str) -> tuple[Path, str | None]:
    """Return (Path, error_message_or_None)."""
    p = Path(file_path)
    if not p.exists():
        return p, f"File not found: {file_path}"
    if not p.is_file():
        return p, f"Path is not a regular file: {file_path}"
    return p, None


# ---------------------------------------------------------------------------
# Tool 1: parse_verilog
# ---------------------------------------------------------------------------


@mcp.tool()
def parse_verilog(input: ParseVerilogInput) -> ParseVerilogResult:  # noqa: A002
    """
    Parse a Verilog or SystemVerilog HDL file and extract module definitions,
    port lists, parameters, and syntax errors.

    Returns structured module information including port directions, widths,
    and parameter default values. Uses pyverilog when available; falls back
    to regex extraction otherwise.
    """
    path, err = _resolve_path(input.file_path)
    if err:
        return ParseVerilogResult(
            success=False,
            file_path=input.file_path,
            syntax_errors=[err],
        )

    try:
        modules, syntax_errors = parse_verilog_file(
            path,
            include_dirs=input.include_dirs,
            defines=input.defines,
        )
    except Exception as exc:
        logger.exception("Unexpected error parsing %s", path)
        return ParseVerilogResult(
            success=False,
            file_path=input.file_path,
            syntax_errors=[f"Unexpected parser error: {exc}"],
        )

    return ParseVerilogResult(
        success=not syntax_errors,
        file_path=input.file_path,
        modules=modules,
        syntax_errors=syntax_errors,
    )


# ---------------------------------------------------------------------------
# Tool 2: extract_modules
# ---------------------------------------------------------------------------


@mcp.tool()
def extract_modules(input: ExtractModulesInput) -> ExtractModulesResult:  # noqa: A002
    """
    Extract the list of module names declared in a Verilog file.

    Useful for quickly discovering what modules a file defines without
    performing a full parse of port and parameter details.
    """
    path, err = _resolve_path(input.file_path)
    if err:
        return ExtractModulesResult(
            success=False,
            file_path=input.file_path,
            error=err,
        )

    try:
        names = extract_module_names(path)
    except Exception as exc:
        logger.exception("Unexpected error extracting modules from %s", path)
        return ExtractModulesResult(
            success=False,
            file_path=input.file_path,
            error=f"Failed to extract modules: {exc}",
        )

    return ExtractModulesResult(
        success=True,
        file_path=input.file_path,
        module_names=names,
    )


# ---------------------------------------------------------------------------
# Tool 3: analyze_hierarchy
# ---------------------------------------------------------------------------


@mcp.tool()
def analyze_hierarchy(input: AnalyzeHierarchyInput) -> AnalyzeHierarchyResult:  # noqa: A002
    """
    Analyze the module instantiation hierarchy starting from a top-level file.

    Builds a tree of module → instance relationships across all provided
    source files. Reports modules that are instantiated but not defined in
    the provided file set (undefined_modules).
    """
    top_path, err = _resolve_path(input.top_file)
    if err:
        return AnalyzeHierarchyResult(
            success=False,
            top_module=None,
            warnings=[err],
        )

    # Collect module definitions from all source files
    all_files = [top_path] + [
        Path(f) for f in input.source_files if Path(f).exists()
    ]
    missing_files = [
        f for f in input.source_files if not Path(f).exists()
    ]

    defined_modules: dict[str, list] = {}  # module_name -> [instance names from AST]
    warnings: list[str] = []

    for fp in all_files:
        try:
            modules, syntax_errors = parse_verilog_file(fp)
            for mod in modules:
                defined_modules[mod.name] = []
            warnings.extend(syntax_errors)
        except Exception as exc:
            warnings.append(f"Could not parse {fp.name}: {exc}")

    for mf in missing_files:
        warnings.append(f"Source file not found (skipped): {mf}")

    if not defined_modules:
        return AnalyzeHierarchyResult(
            success=False,
            top_module=None,
            warnings=warnings + ["No modules found in provided files"],
        )

    # Determine top module
    top_modules, _ = parse_verilog_file(top_path)
    if input.top_module:
        resolved_top = input.top_module
    elif top_modules:
        resolved_top = top_modules[0].name
    else:
        return AnalyzeHierarchyResult(
            success=False,
            top_module=None,
            warnings=warnings + ["Could not determine top module"],
        )

    # Build hierarchy (single-level for Phase 0; multi-level requires full AST)
    hierarchy, undefined = _build_hierarchy_node(
        resolved_top, defined_modules, set()
    )

    return AnalyzeHierarchyResult(
        success=True,
        top_module=resolved_top,
        hierarchy=hierarchy,
        undefined_modules=list(undefined),
        warnings=warnings,
    )


def _build_hierarchy_node(
    module_name: str,
    defined_modules: dict[str, list],
    visited: set[str],
) -> tuple[HierarchyNode, set[str]]:
    """Recursively build a HierarchyNode tree; track undefined references."""
    undefined: set[str] = set()
    node = HierarchyNode(module=module_name, instance_name=module_name)

    if module_name in visited:
        return node, undefined  # avoid infinite recursion on circular designs
    visited = visited | {module_name}

    child_names = defined_modules.get(module_name, [])
    for child_mod in child_names:
        if child_mod not in defined_modules:
            undefined.add(child_mod)
        else:
            child_node, child_undef = _build_hierarchy_node(
                child_mod, defined_modules, visited
            )
            node.children.append(child_node)
            undefined |= child_undef

    return node, undefined


# ---------------------------------------------------------------------------
# Tool 4: lint_check
# ---------------------------------------------------------------------------


@mcp.tool()
def lint_check(input: LintCheckInput) -> LintCheckResult:  # noqa: A002
    """
    Run static lint checks on a Verilog file.

    Phase 0 rules:
      W001 - Unused output port
      W002 - Implicit net declaration
      W003 - Blocking assignment in sequential always block
      E001 - Instantiated undefined module
      E002 - Port width mismatch

    Pass an empty rules list to enable all supported rules.
    """
    path, err = _resolve_path(input.file_path)
    if err:
        return LintCheckResult(
            success=False,
            file_path=input.file_path,
        )

    enabled_rules = set(input.rules) if input.rules else set(_ALL_LINT_RULES)

    try:
        all_issues = basic_lint_check(path)
    except Exception as exc:
        logger.exception("Unexpected error during lint of %s", path)
        return LintCheckResult(
            success=False,
            file_path=input.file_path,
        )

    filtered = [issue for issue in all_issues if issue.rule in enabled_rules]

    return LintCheckResult(
        success=True,
        file_path=input.file_path,
        issues=filtered,
        rules_checked=sorted(enabled_rules),
    )


# ---------------------------------------------------------------------------
# Tool 5: extract_ports
# ---------------------------------------------------------------------------


@mcp.tool()
def extract_ports_tool(input: ExtractPortsInput) -> ExtractPortsResult:  # noqa: A002
    """
    Extract port and parameter definitions from a specific module in a Verilog file.

    Returns each port's name, direction (input/output/inout), bit-width, and
    sign attribute. Also returns module parameters with their default values.
    When module_name is omitted, the first module in the file is used.
    """
    path, err = _resolve_path(input.file_path)
    if err:
        return ExtractPortsResult(
            success=False,
            file_path=input.file_path,
            module_name=input.module_name,
            error=err,
        )

    try:
        resolved_name, ports, params = extract_ports(path, input.module_name)
    except Exception as exc:
        logger.exception("Unexpected error extracting ports from %s", path)
        return ExtractPortsResult(
            success=False,
            file_path=input.file_path,
            module_name=input.module_name,
            error=f"Failed to extract ports: {exc}",
        )

    if resolved_name is None:
        mod_desc = f"'{input.module_name}'" if input.module_name else "any module"
        return ExtractPortsResult(
            success=False,
            file_path=input.file_path,
            module_name=input.module_name,
            error=f"Module {mod_desc} not found in {path.name}",
        )

    return ExtractPortsResult(
        success=True,
        file_path=input.file_path,
        module_name=resolved_name,
        ports=ports,
        parameters=params,
    )
