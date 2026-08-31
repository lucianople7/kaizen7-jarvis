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

    def capabilities(self) -> dict[str, Any]:
        return {
            "execution_enabled": False,
            "approval_required_for": [
                "profile-chat",
                "profile-create",
                "cron-create",
                "cron-run",
                "peer-add",
                "peer-dm",
            ],
            "capabilities": [
                {
                    "id": "profile-list",
                    "title": "List Hermes profiles",
                    "command": "hermes profile list",
                    "requires_approval": False,
                },
                {
                    "id": "profile-chat",
                    "title": "Send a message to a Hermes profile",
                    "command": "hermes -p <profile> chat --query-file <file> -Q",
                    "requires_approval": True,
                },
                {
                    "id": "profile-create",
                    "title": "Create a Hermes profile",
                    "command": "hermes profile create <name> --description <description>",
                    "requires_approval": True,
                },
                {
                    "id": "cron-list",
                    "title": "List Hermes cron routines",
                    "command": "hermes cron list",
                    "requires_approval": False,
                },
                {
                    "id": "cron-create",
                    "title": "Create a Hermes cron routine",
                    "command": "hermes cron create ...",
                    "requires_approval": True,
                },
                {
                    "id": "peer-list",
                    "title": "List Hermes peers",
                    "command": "hermes peer list",
                    "requires_approval": False,
                },
                {
                    "id": "peer-dm",
                    "title": "Message a Hermes peer/profile",
                    "command": "hermes peer dm <peer>/<profile> <file>",
                    "requires_approval": True,
                },
            ],
        }

    def bot_mode_contract(self) -> dict[str, Any]:
        status = self.status()
        installed_profiles = {
            str(profile.get("name", "")): profile for profile in status.get("profiles", [])
        }
        recommended_bots = [
            {
                "profile": "kaizen7",
                "title": "Mission control",
                "focus": "Keep Luciano focused on one active mission and limited priorities.",
            },
            {
                "profile": "market",
                "title": "Market scout",
                "focus": "Research open-market signals and summarize sources before action.",
            },
            {
                "profile": "sales",
                "title": "Sales operator",
                "focus": "Prepare offers, follow-up drafts and lead paths for human approval.",
            },
            {
                "profile": "content",
                "title": "Content operator",
                "focus": "Turn verified signals into reusable content briefs and drafts.",
            },
            {
                "profile": "ops",
                "title": "Operations operator",
                "focus": "Plan weekly loops, daily actions, receipts and metric reviews.",
            },
        ]
        for bot in recommended_bots:
            bot["installed"] = bot["profile"] in installed_profiles
        return {
            "name": "Personal Jarvis + Hermes Bot",
            "execution_enabled": False,
            "personal_jarvis": {
                "role": "local_interface",
                "owns": [
                    "desktop-control surface",
                    "voice and web UX",
                    "human approval prompts",
                    "local receipts",
                ],
            },
            "hermes": {
                "role": "agent_runtime",
                "installed": status["installed"],
                "version": status["version"],
                "owns": [
                    "profiles",
                    "memory",
                    "skills",
                    "gateway integrations",
                    "cron-capable routines",
                ],
            },
            "bot_mode": {
                "role": "persistent_specialist_bots",
                "owns": [
                    "durable profile identity",
                    "platform delivery through Hermes gateways",
                    "scheduled or channel-driven operation after approval",
                ],
            },
            "recommended_bots": recommended_bots,
            "human_approval_required_for": [
                "payments",
                "publishing",
                "outbound_messages",
                "credentials",
                "financial_operations",
                "irreversible_changes",
            ],
            "safety_contract": (
                "The browser proposes and records work. Hermes Bot Mode execution "
                "must be started from an approved local Hermes profile or gateway."
            ),
        }

    def chat_plan(self, *, profile: str, message: str) -> dict[str, Any]:
        safe_profile = _safe_profile(profile)
        clean_message = " ".join(message.strip().split())
        if not clean_message:
            raise ValueError("Message cannot be blank.")
        return {
            "executed": False,
            "requires_approval": True,
            "profile": safe_profile,
            "message": clean_message,
            "command": [
                str(self.cli or "hermes"),
                "-p",
                safe_profile,
                "chat",
                "--query-file",
                "<file>",
                "-Q",
                "--source",
                "kaizen7",
            ],
        }

    def cron_list(self) -> dict[str, Any]:
        return self._run_read_only(["cron", "list"])

    def peer_list(self) -> dict[str, Any]:
        return self._run_read_only(["peer", "list"])

    def _run_read_only(self, args: list[str]) -> dict[str, Any]:
        try:
            result = self.runner(
                [str(self.cli or "hermes"), *args],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except FileNotFoundError:
            return {
                "executed": False,
                "stdout": "",
                "stderr": "",
                "error": "Hermes CLI not found.",
            }
        return {
            "executed": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "error": "" if result.returncode == 0 else result.stderr.strip(),
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
        except subprocess.TimeoutExpired:
            return {"version": "", "error": "Hermes CLI timed out."}
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
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
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


def _safe_profile(profile: str) -> str:
    candidate = profile.strip().lower()
    if not _PROFILE_NAME_RE.match(candidate):
        raise ValueError("Invalid Hermes profile name.")
    return candidate


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
