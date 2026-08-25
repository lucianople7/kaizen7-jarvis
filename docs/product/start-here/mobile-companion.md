---
title: KAIZEN7 Mobile Companion
slug: kaizen7-mobile-companion
summary: Use Android as a safe command and approval surface for KAIZEN7 Jarvis.
tags: [kaizen7, mobile, android, companion, approvals]
---

# KAIZEN7 Mobile Companion

KAIZEN7 Mobile Companion turns a phone browser into a command surface for the
desktop Jarvis runtime. It is built as a companion first: mobile can observe,
pair, send intent, and queue approval receipts, while execution stays gated on
the desktop runtime.

## Open It

1. Start Jarvis on the desktop or server.
2. Open the web app.
3. Go to **Mobile** in the sidebar, or open `/?view=mobile`.
4. Use **Create pairing code** when an Android client needs a short-lived
   pairing challenge.

## Install On Android

The companion is now shipped as an installable PWA. From Android Chrome:

1. Start Jarvis on the desktop with `jarvis serve`.
2. Open `http://<desktop-lan-ip>:47821/?view=mobile` from the phone.
3. Use Chrome's **Add to Home screen** / **Install app** action.
4. Launch **Jarvis** from the Android home screen.

The installed app starts directly in the Mobile view and keeps API activity
network-first. The service worker deliberately does not cache `/api/*` so
mobile approvals, receipts, and personal data are not stored as stale offline
responses.

## Current Capabilities

- Mobile status contract: `GET /api/mobile/status`.
- Short-lived pairing challenge: `POST /api/mobile/pairing/challenge`.
- Mobile intent intake: `POST /api/mobile/intents`.
- Sensitive actions are not executed from mobile. They are recorded as pending
  approval receipts.
- Installable PWA shell: `/manifest.webmanifest` plus `/mobile-sw.js`.

## Approval Boundary

Human approval is required for payments, purchases, public posts, outbound
messages, credentials, financial operations, deployments, destructive edits,
and irreversible desktop actions.

## Not Yet Included

- Native Android APK packaging.
- Push notifications.
- Camera/microphone capture from Android.
- Android Accessibility control.
- Execution from Android.

Those belong in later layers after pairing, authentication, approvals, and
receipt storage are durable.
