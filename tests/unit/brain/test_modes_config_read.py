"""Assistant modes read the active pointer from the real config loader."""
from __future__ import annotations

from jarvis.brain import modes
from jarvis.core import config as core_config


def test_active_slug_reads_persona_active_mode_from_config_file(
    tmp_path, monkeypatch
) -> None:
    config_file = tmp_path / "jarvis.toml"
    config_file.write_text('[persona]\nactive_mode = "kaizen7"\n', encoding="utf-8")

    monkeypatch.setenv("JARVIS_CONFIG", str(config_file))
    core_config.clear_config_cache()
    modes.set_section_override(None)

    try:
        assert modes.active_slug() == modes.MODE_KAIZEN7
    finally:
        modes.set_section_override(None)
        core_config.clear_config_cache()
