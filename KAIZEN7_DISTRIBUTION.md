# KAIZEN7 Personal Jarvis Distribution

This private repository is a KAIZEN7 adaptation layer around Personal Jarvis.
It is not the official Personal Jarvis repository.

## Upstream

- Repository: https://github.com/PersonalJarvis/PersonalJarvis
- Source commit copied: ffa18202ec37e9cddcef9ef2de7a1e5f10026dbc
- License: MIT
- License file preserved: LICENSE
- Trademark notice preserved: TRADEMARK.md
- Copied on: 2026-08-15

## KAIZEN7 Direction

Luciano decides.
KAIZEN7 focuses.
Jarvis executes through audited tools and approval gates.
Projects grow.
Life does not disperse.

## Operating Boundary

KAIZEN7 changes in this repository must remain clearly marked and reviewable.
No credentials, cookies, tokens, API keys, keychain exports, local memory data,
voice captures, model downloads, caches, or virtual environments belong in Git.

The agent may recommend actions freely, but must not execute payments,
publications, outbound messages, credential changes, financial operations,
desktop control with irreversible effects, or destructive operations without
explicit Luciano approval.

## Initial Purpose

This repository exists to test whether Personal Jarvis can serve as a local,
audited, voice-capable operating partner for KAIZEN7, while keeping the upstream
runtime legally attributed and technically separable.

## Install Status

The source install path is owned by this repository:

- Windows: `irm https://raw.githubusercontent.com/lucianople7/kaizen7-personal-jarvis/main/install/install.ps1 | iex`
- macOS/Linux: `curl -fsSL https://raw.githubusercontent.com/lucianople7/kaizen7-personal-jarvis/main/install/install.sh | bash`

Release verification assets from upstream are preserved for attribution and
future migration, but KAIZEN7 has not yet issued its own signed release channel.
Until that release exists, use the source install commands above or inspect and
run `install/installer.py` from a local clone.
