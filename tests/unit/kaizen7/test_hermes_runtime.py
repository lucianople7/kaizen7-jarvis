from __future__ import annotations

import subprocess

from jarvis.kaizen7.hermes_runtime import HermesRuntime


def test_status_reports_missing_cli() -> None:
    runtime = HermesRuntime(cli="missing-hermes", runner=_missing_runner)

    status = runtime.status()

    assert status["installed"] is False
    assert status["execution_enabled"] is False
    assert status["profile_count"] == 0
    assert status["error"] == "Hermes CLI not found."


def test_status_parses_version_and_profiles() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_happy_runner)

    status = runtime.status()

    assert status["installed"] is True
    assert status["version"] == "Hermes Agent v0.20.4 (2026.8.18)"
    assert status["profile_count"] == 3
    assert status["profiles"][1]["name"] == "kaizen7"
    assert status["profiles"][1]["alias"] == "kaizen7"
    assert status["profiles"][1]["gateway"] == "stopped"


def test_profiles_are_safe_read_only_payloads() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_happy_runner)

    payload = runtime.profiles()

    assert payload["execution_enabled"] is False
    assert payload["count"] == 3
    assert [profile["name"] for profile in payload["profiles"]] == [
        "default",
        "kaizen7",
        "market",
    ]


def test_capabilities_cover_profile_chat_cron_and_peer() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_happy_runner)

    payload = runtime.capabilities()

    assert payload["execution_enabled"] is False
    assert {cap["id"] for cap in payload["capabilities"]} >= {
        "profile-list",
        "profile-chat",
        "cron-list",
        "peer-list",
        "peer-dm",
    }
    chat = next(cap for cap in payload["capabilities"] if cap["id"] == "profile-chat")
    assert chat["requires_approval"] is True
    assert chat["command"] == "hermes -p <profile> chat --query-file <file> -Q"


def test_chat_plan_builds_query_file_command_without_running() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_happy_runner)

    result = runtime.chat_plan(profile="kaizen7", message="Focus today")

    assert result["executed"] is False
    assert result["requires_approval"] is True
    assert result["profile"] == "kaizen7"
    assert result["message"] == "Focus today"
    assert result["command"] == [
        "hermes",
        "-p",
        "kaizen7",
        "chat",
        "--query-file",
        "<file>",
        "-Q",
        "--source",
        "kaizen7",
    ]


def test_cron_and_peer_lists_are_read_only() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_lists_runner)

    assert runtime.cron_list()["executed"] is True
    assert runtime.peer_list()["executed"] is True
    assert runtime.cron_list()["stdout"] == "no jobs"
    assert runtime.peer_list()["stdout"] == "no peers"


def test_profile_parser_skips_table_separators_from_real_cli_output() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_realistic_runner)

    payload = runtime.profiles()

    assert payload["count"] == 6
    assert "───────────────" not in {profile["name"] for profile in payload["profiles"]}
    assert [profile["name"] for profile in payload["profiles"]] == [
        "default",
        "content",
        "kaizen7",
        "market",
        "ops",
        "sales",
    ]


def test_profile_parser_accepts_active_profile_with_ansi_marker() -> None:
    runtime = HermesRuntime(cli="hermes", runner=_ansi_runner)

    payload = runtime.profiles()

    assert payload["profiles"][0]["name"] == "default"


def _missing_runner(*_args, **_kwargs):
    raise FileNotFoundError


def _happy_runner(args, **_kwargs):
    if args[-1] == "--version":
        return subprocess.CompletedProcess(args, 0, "Hermes Agent v0.20.4 (2026.8.18)\n", "")
    if args[-2:] == ["profile", "list"]:
        return subprocess.CompletedProcess(
            args,
            0,
            """
 Profile          Model                        Gateway      Alias
 ───────────────    ───────────────────────────    ───────────    ───────────
 ◆default         anthropic/claude-opus-4.6    stopped      —            —
  kaizen7         —                            stopped      kaizen7      —
  market          —                            stopped      market       —
""",
            "",
        )
    raise AssertionError(args)


def _lists_runner(args, **_kwargs):
    if args[-1] == "--version":
        return subprocess.CompletedProcess(args, 0, "Hermes Agent v0.20.4\n", "")
    if args[-2:] == ["cron", "list"]:
        return subprocess.CompletedProcess(args, 0, "no jobs\n", "")
    if args[-2:] == ["peer", "list"]:
        return subprocess.CompletedProcess(args, 0, "no peers\n", "")
    return _happy_runner(args, **_kwargs)


def _realistic_runner(args, **_kwargs):
    if args[-1] == "--version":
        return subprocess.CompletedProcess(args, 0, "Hermes Agent v0.20.4 (2026.8.18)\n", "")
    if args[-2:] == ["profile", "list"]:
        return subprocess.CompletedProcess(
            args,
            0,
            """
 Profile          Model                        Gateway      Alias
 ───────────────    ───────────────────────────    ───────────    ───────────
 ◆default         anthropic/claude-opus-4.6    stopped      —            —
  content         —                            stopped      content      —
  kaizen7         —                            stopped      kaizen7      —
  market          —                            stopped      market       —
  ops             —                            stopped      ops          —
  sales           —                            stopped      sales        —
""",
            "",
        )
    raise AssertionError(args)


def _ansi_runner(args, **_kwargs):
    if args[-1] == "--version":
        return subprocess.CompletedProcess(args, 0, "Hermes Agent v0.20.4 (2026.8.18)\n", "")
    if args[-2:] == ["profile", "list"]:
        return subprocess.CompletedProcess(
            args,
            0,
            "\x1b[32m◆default\x1b[0m         anthropic/claude-opus-4.6"
            "    stopped      —            —\n",
            "",
        )
    raise AssertionError(args)
