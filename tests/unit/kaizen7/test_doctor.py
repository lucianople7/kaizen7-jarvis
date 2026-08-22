from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.doctor import (
    has_failures,
    render_kaizen7_doctor,
    run_kaizen7_doctor,
)


def test_kaizen7_doctor_warns_for_missing_optional_runtimes(tmp_path: Path) -> None:
    findings = run_kaizen7_doctor(
        hermes=_FakeHermes(installed=False),
        codex=_FakeCodex(installed=False),
        bridge=ControlBridgeStore(root=tmp_path),
    )

    assert not has_failures(findings)
    rendered = render_kaizen7_doctor(findings)
    assert "Hermes CLI not detected" in rendered
    assert "Codex CLI not detected" in rendered
    assert "RESULT: OK - KAIZEN7 layer is safe to use." in rendered


def test_kaizen7_doctor_reports_ready_runtimes(tmp_path: Path) -> None:
    findings = run_kaizen7_doctor(
        hermes=_FakeHermes(installed=True),
        codex=_FakeCodex(installed=True),
        bridge=ControlBridgeStore(root=tmp_path),
    )

    rendered = render_kaizen7_doctor(findings)

    assert not has_failures(findings)
    assert "Hermes detected: Hermes Agent v0.20.4" in rendered
    assert "Codex CLI detected: codex 0.32.0" in rendered
    assert "recommended Bot Mode profiles installed: 1/5" in rendered


def test_kaizen7_doctor_reports_universal_provider_registry(tmp_path: Path) -> None:
    findings = run_kaizen7_doctor(
        hermes=_FakeHermes(installed=False),
        codex=_FakeCodex(installed=False),
        bridge=ControlBridgeStore(root=tmp_path),
    )

    rendered = render_kaizen7_doctor(findings)

    assert "providers:" in rendered
    assert "universal provider registry ready: 4 connectors" in rendered
    assert "Hermes, Codex, generic API, generic CLI" in rendered


def test_kaizen7_doctor_fails_when_bridge_approval_contract_is_broken(
    tmp_path: Path,
) -> None:
    findings = run_kaizen7_doctor(
        hermes=_FakeHermes(installed=False),
        codex=_FakeCodex(installed=False),
        bridge=_UnsafeBridge(root=tmp_path),
    )

    assert has_failures(findings)
    assert "RESULT: FAIL - safety contract broken." in render_kaizen7_doctor(findings)


class _FakeHermes:
    def __init__(self, *, installed: bool) -> None:
        self.installed = installed

    def status(self) -> dict[str, Any]:
        if not self.installed:
            return {
                "installed": False,
                "version": "",
                "profile_count": 0,
                "profiles": [],
                "execution_enabled": False,
                "error": "missing",
            }
        return {
            "installed": True,
            "version": "Hermes Agent v0.20.4",
            "profile_count": 1,
            "profiles": [{"name": "kaizen7"}],
            "execution_enabled": False,
            "error": "",
        }

    def bot_mode_contract(self) -> dict[str, Any]:
        bots = [
            {"profile": "kaizen7", "installed": self.installed},
            {"profile": "market", "installed": False},
            {"profile": "sales", "installed": False},
            {"profile": "content", "installed": False},
            {"profile": "ops", "installed": False},
        ]
        return {"recommended_bots": bots}


class _FakeCodex:
    def __init__(self, *, installed: bool) -> None:
        self.installed = installed

    def status(self) -> dict[str, Any]:
        if not self.installed:
            return {
                "installed": False,
                "version": "",
                "execution_enabled": False,
                "error": "missing",
            }
        return {
            "installed": True,
            "version": "codex 0.32.0",
            "execution_enabled": False,
            "error": "",
        }


class _UnsafeBridge(ControlBridgeStore):
    def status(self) -> dict[str, Any]:
        data = super().status()
        data["execution_enabled"] = True
        data["approval_required_for"] = ["payments"]
        return data
