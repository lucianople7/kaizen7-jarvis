"""Read-only adapter for a local OpenAI Codex CLI installation."""
from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Runner = Callable[..., subprocess.CompletedProcess[str]]
CodexSandbox = Literal["workspace-write", "danger-full-access"]


@dataclass(frozen=True)
class CodexRuntime:
    """Small safe wrapper around Codex CLI inspection and delegation plans."""

    cli: str | Path | None = None
    runner: Runner = subprocess.run

    @classmethod
    def from_environment(cls) -> CodexRuntime:
        return cls(cli=_resolve_cli())

    def status(self) -> dict[str, Any]:
        version = self._version()
        return {
            "installed": not bool(version["error"]),
            "version": version["version"],
            "cli": str(self.cli or "codex"),
            "execution_enabled": False,
            "requires_git_repo": True,
            "requires_pty": True,
            "auth_methods": [
                "OPENAI_API_KEY",
                "Codex CLI OAuth credentials",
                "Hermes-managed openai-codex OAuth",
            ],
            "error": version["error"],
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "execution_enabled": False,
            "approval_required_for": [
                "codex-exec",
                "codex-review",
                "codex-background-task",
                "codex-danger-full-access",
            ],
            "capabilities": [
                {
                    "id": "codex-version",
                    "title": "Read Codex CLI version",
                    "command": "codex --version",
                    "requires_approval": False,
                },
                {
                    "id": "codex-exec",
                    "title": "Delegate one coding task to Codex",
                    "command": "codex exec --sandbox workspace-write <prompt>",
                    "requires_approval": True,
                },
                {
                    "id": "codex-review",
                    "title": "Review code or a pull request with Codex",
                    "command": "codex review --base <ref>",
                    "requires_approval": True,
                },
                {
                    "id": "codex-background-task",
                    "title": "Run a long Codex task in a PTY",
                    "command": "codex exec --sandbox workspace-write <prompt>",
                    "requires_approval": True,
                },
                {
                    "id": "codex-danger-full-access",
                    "title": "Use Codex without the workspace sandbox",
                    "command": "codex exec --sandbox danger-full-access <prompt>",
                    "requires_approval": True,
                },
            ],
        }

    def delegate_plan(
        self, *, workdir: str, prompt: str, sandbox: CodexSandbox = "workspace-write"
    ) -> dict[str, Any]:
        clean_prompt = " ".join(prompt.strip().split())
        clean_workdir = workdir.strip()
        if not clean_workdir:
            raise ValueError("Workdir cannot be blank.")
        if not clean_prompt:
            raise ValueError("Prompt cannot be blank.")
        if sandbox not in {"workspace-write", "danger-full-access"}:
            raise ValueError("Unsupported Codex sandbox.")
        return {
            "executed": False,
            "requires_approval": True,
            "workdir": clean_workdir,
            "prompt": clean_prompt,
            "pty_required": True,
            "git_repo_required": True,
            "sandbox": sandbox,
            "command": [
                str(self.cli or "codex"),
                "exec",
                "--sandbox",
                sandbox,
                clean_prompt,
            ],
        }

    def _version(self) -> dict[str, str]:
        try:
            result = self.runner(
                [str(self.cli or "codex"), "--version"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            return {"version": "", "error": "Codex CLI not found."}
        except OSError as exc:
            return {"version": "", "error": str(exc)}
        if result.returncode != 0:
            return {"version": "", "error": (result.stderr or result.stdout).strip()}
        return {"version": result.stdout.strip().splitlines()[0], "error": ""}


def _resolve_cli() -> str:
    return os.environ.get("KAIZEN7_CODEX_CLI") or os.environ.get("CODEX_CLI") or "codex"
