# src/auto_eda/core/errors.py
from enum import IntEnum


class EDAErrorCode(IntEnum):
    # General errors (1xxx)
    UNKNOWN              = 1000
    INVALID_INPUT        = 1001
    FILE_NOT_FOUND       = 1002
    FILE_PERMISSION      = 1003
    UNSUPPORTED_FORMAT   = 1004
    TIMEOUT              = 1005
    CANCELLED            = 1006

    # Tool not found / environment errors (2xxx)
    TOOL_NOT_FOUND       = 2001
    TOOL_VERSION_MISMATCH= 2002
    TOOL_LICENSE_ERROR   = 2003
    DEPENDENCY_MISSING   = 2004

    # Yosys errors (3xxx)
    YOSYS_SYNTHESIS_FAIL = 3001
    YOSYS_PARSE_ERROR    = 3002
    YOSYS_SCRIPT_ERROR   = 3003
    YOSYS_NO_TOP_MODULE  = 3004
    YOSYS_TECH_LIB_ERROR = 3005

    # KiCad errors (4xxx)
    KICAD_IPC_CONN_FAIL  = 4001
    KICAD_IPC_TIMEOUT    = 4002
    KICAD_PROJECT_INVALID= 4003
    KICAD_DRC_ERROR      = 4004
    KICAD_VERSION_LOW    = 4005
    KICAD_NOT_RUNNING    = 4006

    # Verilog parse errors (5xxx)
    VERILOG_SYNTAX_ERROR = 5001
    VERILOG_INCLUDE_ERROR= 5002
    VERILOG_PARSE_CRASH  = 5003


class EDAError(Exception):
    """Base class for all AUTO_EDA exceptions."""

    def __init__(
        self,
        code: EDAErrorCode,
        message: str,
        detail: str | None = None,
        tool_output: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail
        self.tool_output = tool_output
        super().__init__(message)

    def to_mcp_error_text(self) -> str:
        """Format as MCP tool error return text."""
        lines = [f"[ERROR {self.code.value}] {self.message}"]
        if self.detail:
            lines.append(f"Detail: {self.detail}")
        if self.tool_output:
            lines.append(f"Tool output:\n{self.tool_output[:2000]}")
        return "\n".join(lines)


class ToolNotFoundError(EDAError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(
            EDAErrorCode.TOOL_NOT_FOUND,
            f"EDA tool '{tool_name}' not found in PATH",
            detail=f"Install {tool_name} and ensure it is accessible from PATH",
        )


class ToolTimeoutError(EDAError):
    def __init__(self, tool_name: str, timeout_s: int) -> None:
        super().__init__(
            EDAErrorCode.TIMEOUT,
            f"'{tool_name}' timed out after {timeout_s}s",
        )


# Aliases used by process.py and other modules
EDATimeoutError = ToolTimeoutError


class ToolExecutionError(EDAError):
    def __init__(self, tool_name: str, returncode: int, stderr: str = "") -> None:
        super().__init__(
            EDAErrorCode.UNKNOWN,
            f"'{tool_name}' exited with code {returncode}",
            detail=stderr.strip()[:2000] if stderr else None,
        )
        self.returncode = returncode
        self.stderr = stderr


class FileNotFoundEDAError(EDAError):
    def __init__(self, file_path: str) -> None:
        super().__init__(
            EDAErrorCode.FILE_NOT_FOUND,
            f"Input file not found: '{file_path}'",
            detail="Verify the file path exists before calling this tool.",
        )
        self.file_path = file_path


class DependencyMissingError(EDAError):
    def __init__(self, package_name: str) -> None:
        super().__init__(
            EDAErrorCode.DEPENDENCY_MISSING,
            f"Required dependency not installed: '{package_name}'",
            detail=f"Run: pip install {package_name}",
        )
        self.package_name = package_name
