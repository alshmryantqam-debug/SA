"""Bounded ADB wrapper with a strict read-only command allowlist."""
from __future__ import annotations
import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence

class AdbError(RuntimeError):
    """ADB unavailable or diagnostic command failed."""

@dataclass(frozen=True)
class AdbResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

# Fixed read-only templates only. No arbitrary shell, push, install, reboot, root or remount.
_ALLOWED: dict[str, tuple[str, ...]] = {
    "devices": ("devices", "-l"), "state": ("get-state",),
    "model": ("shell", "getprop", "ro.product.model"),
    "android_version": ("shell", "getprop", "ro.build.version.release"),
    "sdk": ("shell", "getprop", "ro.build.version.sdk"),
    "manufacturer": ("shell", "getprop", "ro.product.manufacturer"),
    "uptime": ("shell", "uptime"), "disk": ("shell", "df", "-h", "/data"),
}

class AdbClient:
    def __init__(self, executable: str = "adb", timeout: float = 8.0) -> None:
        self.executable = executable
        self.timeout = max(1.0, min(float(timeout), 30.0))

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run(self, key: str, *, serial: str | None = None) -> AdbResult:
        if key not in _ALLOWED:
            raise AdbError(f"Command is not in the read-only allowlist: {key}")
        if not self.available():
            raise AdbError("ADB not found. Install Android Platform Tools and check PATH.")
        if serial and any(ch in serial for ch in "\r\n\x00"):
            raise AdbError("Invalid device serial.")
        command = [self.executable]
        if serial:
            command.extend(["-s", serial])
        command.extend(_ALLOWED[key])
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout, check=False, shell=False)
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"ADB timed out after {self.timeout:g}s.") from exc
        except OSError as exc:
            raise AdbError(f"Could not start ADB: {exc}") from exc
        if proc.returncode:
            detail = (proc.stderr or proc.stdout).strip()[:500]
            raise AdbError(detail or f"ADB exited with code {proc.returncode}.")
        return AdbResult(tuple(command), proc.returncode, proc.stdout, proc.stderr)

    def list_devices(self) -> list[dict[str, str]]:
        output = self.run("devices").stdout
        devices = []
        for line in output.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and not parts[0].startswith("*"):
                devices.append({"serial": parts[0], "state": parts[1], "details": " ".join(parts[2:])})
        return devices
