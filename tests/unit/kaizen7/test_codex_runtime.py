from __future__ import annotations

from pathlib import Path

from jarvis.kaizen7 import codex_runtime


def test_resolve_cli_prefers_npm_global_cmd_on_windows(tmp_path, monkeypatch) -> None:
    npm_global = tmp_path / ".npm-global"
    npm_global.mkdir()
    shim = npm_global / "codex.cmd"
    shim.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.delenv("KAIZEN7_CODEX_CLI", raising=False)
    monkeypatch.delenv("CODEX_CLI", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert codex_runtime._resolve_cli() == str(shim)
