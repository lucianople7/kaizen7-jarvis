"""Read-only adapter for a local Hermes Agent installation."""
from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Runner = Callable[..., subprocess.CompletedProcess[str]]
_PROFILE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_TABLE_LINE = "\u2500"
_ACTIVE_MARK = "\u25c6"
_EMPTY_CELL = "\u2014"


@dataclass(frozen=True)
class HermesRuntime:
    """Small safe wrapper around Hermes CLI inspection commands."""

    cli: str | Path | None = None
    runner: Runner = subprocess.run

    @classmethod
    def from_environment(cls) -> HermesRuntime:
        return cls(cli=_resolve_cli())

    def status(self) -> dict[str, Any]:
        version = self._version()
        if version["error"]:
            return {
                "installed": False,
                "version": "",
                "cli": str(self.cli or ""),
                "execution_enabled": False,
                "profiles": [],
                "profile_count": 0,
                "error": version["error"],
            }
        profiles = self._profile_rows()
        return {
            "installed": True,
            "version": version["version"],
            "cli": str(self.cli or "hermes"),
            "execution_enabled": False,
            "profiles": profiles,
            "profile_count": len(profiles),
            "error": "",
        }

    def profiles(self) -> dict[str, Any]:
        status = self.status()
        return {
            "installed": status["installed"],
            "execution_enabled": False,
            "profiles": status["profiles"],
            "count": status["profile_count"],
            "error": status["error"],
        }

    def _version(self) -> dict[str, str]:
        try:
            result = self.runner(
                [str(self.cli or "hermes"), "--version"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            return {"version": "", "error": "Hermes CLI not found."}
        except OSError as exc:
            return {"version": "", "error": str(exc)}
        if result.returncode != 0:
            return {"version": "", "error": (result.stderr or result.stdout).strip()}
        return {"version": result.stdout.strip().splitlines()[0], "error": ""}

    def _profile_rows(self) -> list[dict[str, str]]:
        try:
            result = self.runner(
                [str(self.cli or "hermes"), "profile", "list"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except (FileNotFoundError, OSError):
            return []
        if result.returncode != 0:
            return []
        return _parse_profile_table(result.stdout)


def _resolve_cli() -> str:
    env_cli = os.environ.get("KAIZEN7_HERMES_CLI") or os.environ.get("HERMES_CLI")
    if env_cli:
        return env_cli
    local = Path.home() / "AppData" / "Local" / "hermes" / "hermes-agent" / "bin" / "hermes.exe"
    if local.exists():
        return str(local)
    return "hermes"


def _parse_profile_table(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in output.splitlines():
        line = _ANSI_RE.sub("", raw).strip()
        if not line or line.startswith("Profile ") or line.startswith(_TABLE_LINE):
            continue
        if "Gateway" in line and "Distribution" in line:
            continue
        line = line.lstrip(_ACTIVE_MARK).strip()
        parts = re.split(r"\s{2,}", line)
        if len(parts) < 4:
            continue
        name, model, gateway, alias = parts[:4]
        if not _PROFILE_NAME_RE.match(name):
            continue
        rows.append(
            {
                "name": name,
                "model": "" if model == _EMPTY_CELL else model,
                "gateway": "" if gateway == _EMPTY_CELL else gateway,
                "alias": "" if alias == _EMPTY_CELL else alias,
                "handle": f"@{name}",
            }
        )
    return rows
