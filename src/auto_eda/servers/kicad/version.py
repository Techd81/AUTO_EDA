from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Flag, auto
from typing import Optional


class KiCadCapability(Flag):
    NONE = 0
    CLI_BASIC = auto()   # v6+: kicad-cli basic commands
    CLI_JOBSETS = auto() # v8+: jobsets / scripted mode
    IPC_API = auto()     # v10+: IPC API (Protobuf socket)


@dataclass
class KiCadVersion:
    major: int
    minor: int
    patch: int
    capabilities: KiCadCapability

    @property
    def version_str(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> "KiCadVersion":
        m = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str)
        if not m:
            raise ValueError(f"Cannot parse KiCad version: {version_str}")
        major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        caps = KiCadCapability.NONE
        if major >= 6:
            caps |= KiCadCapability.CLI_BASIC
        if major >= 8:
            caps |= KiCadCapability.CLI_JOBSETS
        if major >= 10:
            caps |= KiCadCapability.IPC_API
        return cls(major, minor, patch, caps)

    @property
    def has_cli(self) -> bool:
        return KiCadCapability.CLI_BASIC in self.capabilities

    @property
    def has_jobsets(self) -> bool:
        return KiCadCapability.CLI_JOBSETS in self.capabilities

    @property
    def has_ipc(self) -> bool:
        return KiCadCapability.IPC_API in self.capabilities


MIN_KICAD_VERSION = KiCadVersion.from_string("7.0.0")


def detect_kicad_version() -> Optional[KiCadVersion]:
    """
    Detect installed KiCad version by trying kicad-cli then kicad.
    Returns None if not installed. Never raises.
    """
    for cmd in ["kicad-cli", "kicad-cli.exe", "kicad"]:
        if shutil.which(cmd) is None:
            continue
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            combined = result.stdout + result.stderr
            for line in combined.splitlines():
                match = re.search(r"(\d+\.\d+\.\d+)", line)
                if match:
                    return KiCadVersion.from_string(match.group(1))
        except (subprocess.TimeoutExpired, OSError, ValueError):
            continue
    return None


def get_kicad_cli_name() -> Optional[str]:
    """Return the kicad-cli executable name available in PATH, or None."""
    for cmd in ["kicad-cli", "kicad-cli.exe"]:
        if shutil.which(cmd):
            return cmd
    return None
