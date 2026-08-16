# KAIZEN7 Debug Notes

Date: 2026-08-15
Repository: `kaizen7-personal-jarvis`
Upstream base: PersonalJarvis/PersonalJarvis at `ffa18202ec37e9cddcef9ef2de7a1e5f10026dbc`

## Local Runtime Result

The repository is installable and runnable on Luciano's Windows machine, but the
virtual environment must use a short path.

Working environment:

```powershell
python -m venv "$env:USERPROFILE\.venvs\k7pj"
& "$env:USERPROFILE\.venvs\k7pj\Scripts\python.exe" -m pip install --upgrade pip rich packaging
$env:PIP_CACHE_DIR = (Join-Path (Get-Location) '.pip-cache')
& "$env:USERPROFILE\.venvs\k7pj\Scripts\python.exe" -m pip install -e . --no-deps
& "$env:USERPROFILE\.venvs\k7pj\Scripts\python.exe" -m pip install --require-hashes -r requirements.txt
& "$env:USERPROFILE\.venvs\k7pj\Scripts\python.exe" -m pip install -e ".[full]"
```

Do not create the main development venv at
`C:\Users\lucia\OneDrive\Documentos\kaizen7-personal-jarvis\.venv` unless
Windows Long Paths are enabled. The `[full]` extra can fail there while installing
packages with very long internal paths, observed in the ElevenLabs dependency
family.

## Verification Receipt

Executed with `C:\Users\lucia\.venvs\k7pj`:

- `python -m pip check`: passed, no broken requirements.
- `jarvis --check`: passed. Windows 10.0.26200, Python 3.12.10, 8 physical / 16 logical CPU cores, 32 GB RAM, no NVIDIA GPU, ffmpeg 8.1 detected. Recommended local speech path is faster-whisper `base`, CPU, int8.
- `jarvis --doctor`: passed. 36 router tools resolve; harnesses registered: `python-script`, `screenshot`; worker CLIs available: `claude`, `codex`; primary brain provider: `claude-api`.
- `jarvis --verify-models`: passed. Wake word and end-of-speech detection are bundled; custom wake model `en` will download on first use; local speech model `base` is ready.
- `jarvis serve` smoke test: passed. `http://127.0.0.1:47821` returned HTTP 200 and served the web shell.

## Operational Boundary For KAIZEN7

Use this repo as a private local operating-agent lab. Keep KAIZEN7-specific logic
additive and clearly marked. Do not commit credentials, local data, `.env`,
`jarvis.toml`, model downloads, caches, voice recordings, or venvs.

THE FOCUX visual identity is tracked separately from the upstream Personal
Jarvis brand. See `docs/kaizen7/THE_FOCUX_BRAND.md` for the logo capsule and
asset paths.

For Luciano's use, the strongest existing surfaces are:

- `jarvis.brain` entry points for provider specialization.
- `jarvis.tool` entry points for approved tools.
- `jarvis.harness` entry points for execution adapters.
- MCP and marketplace loaders for community/plugin surfaces.
- Risk tiers: `safe`, `monitor`, `ask`, `block`.
- `ToolExecutor.execute()` as the only authorized execution path.
- Mission Manager and worker CLIs (`claude`, `codex`) for heavier tasks.

KAIZEN7 should preserve the split between recommending and executing. Payments,
publications, outbound messages, credentials, financial operations, live desktop
control with irreversible effects, and destructive operations require explicit
Luciano approval.
