"""Async subprocess management for EDA tool invocations."""
from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .errors import (
    EDATimeoutError,
    FileNotFoundEDAError,
    ToolExecutionError,
    ToolNotFoundError,
)


@dataclass
class ProcessResult:
    """Captured output from a completed subprocess."""
    returncode: int
    stdout: str
    stderr: str
    args: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when the process exited successfully."""
        return self.returncode == 0


def find_tool(name: str) -> str:
    """Return the absolute path of *name* on PATH.

    Raises
    ------
    ToolNotFoundError
        If the executable cannot be located.
    """
    resolved = shutil.which(name)
    if resolved is None:
        raise ToolNotFoundError(name)
    return resolved


async def run_tool(
    args: Sequence[str],
    *,
    timeout: float = 120.0,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    check_input_file: str | Path | None = None,
) -> ProcessResult:
    """Run an EDA tool as an async subprocess and return its output.

    Parameters
    ----------
    args:
        Command and arguments, e.g. ``["yosys", "-p", "synth", "design.v"]``.
    timeout:
        Maximum wall-clock seconds allowed before the process is killed.
    cwd:
        Working directory for the subprocess (defaults to current directory).
    env:
        Optional explicit environment mapping; ``None`` inherits the parent env.
    check_input_file:
        When provided, verify this path exists before launching the process,
        raising ``FileNotFoundEDAError`` if it is absent.

    Returns
    -------
    ProcessResult
        Captured stdout, stderr, and return code.

    Raises
    ------
    ToolNotFoundError
        The executable (``args[0]``) is not on PATH.
    FileNotFoundEDAError
        *check_input_file* was specified but does not exist.
    EDATimeoutError
        The process did not finish within *timeout* seconds.
    ToolExecutionError
        The process exited with a non-zero return code.
    """
    tool_name = str(args[0])

    # Validate executable presence before spawning.
    find_tool(tool_name)

    # Validate input file when requested.
    if check_input_file is not None:
        path = Path(check_input_file)
        if not path.exists():
            raise FileNotFoundEDAError(str(path))

    str_args = [str(a) for a in args]

    try:
        proc = await asyncio.create_subprocess_exec(
            *str_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()  # drain pipes
            raise EDATimeoutError(tool_name, timeout)
    except FileNotFoundError:
        # Raised by create_subprocess_exec when the binary is not found at
        # runtime (edge case where shutil.which succeeded but exec failed).
        raise ToolNotFoundError(tool_name)

    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")
    result = ProcessResult(
        returncode=proc.returncode or 0,
        stdout=stdout,
        stderr=stderr,
        args=str_args,
    )

    if result.returncode != 0:
        raise ToolExecutionError(tool_name, result.returncode, stderr)

    return result


__all__ = [
    "ProcessResult",
    "find_tool",
    "run_tool",
]
