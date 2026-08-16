"""KAIZEN7 Mobile Companion API.

This router is intentionally conservative: phones can observe, send intent, and
approve through explicit future gates, but they do not execute irreversible work
directly.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/mobile", tags=["mobile"])

_PAIRING_TTL_SECONDS = 300
_APPROVAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("payments", ("pay", "payment", "charge", "invoice", "purchase", "buy")),
    ("public posts", ("publish", "post", "tweet", "instagram", "youtube", "tiktok")),
    ("outbound messages", ("send", "email", "whatsapp", "telegram", "sms", "call")),
    ("credentials", ("password", "token", "api key", "credential", "secret")),
    ("financial operations", ("bank", "transfer", "stripe", "refund", "subscription")),
    ("deployments", ("deploy", "release", "production")),
    ("destructive edits", ("delete", "remove", "destroy", "wipe")),
    ("irreversible desktop actions", ("format", "reset", "shutdown")),
)
_DEFAULT_APPROVAL_REQUIRED_FOR = [
    "payments",
    "purchases",
    "public posts",
    "outbound messages",
    "credentials",
    "financial operations",
    "deployments",
    "destructive edits",
    "irreversible desktop actions",
]


class MobileIntentRequest(BaseModel):
    """A user request coming from the mobile companion."""

    text: str = Field(min_length=1, max_length=4000)
    context: str | None = Field(default=None, max_length=4000)


@router.get("/status", summary="Mobile companion status")
async def status_snapshot() -> dict[str, object]:
    """Return the stable mobile product contract."""

    return {
        "product": "KAIZEN7 Mobile Companion",
        "mode": "companion",
        "capabilities": [
            "chat",
            "voice_input",
            "approvals",
            "tasks",
            "memory_read",
            "receipts",
            "desktop_gateway",
        ],
        "human_approval_required_for": _DEFAULT_APPROVAL_REQUIRED_FOR,
        "execution": {
            "can_execute": False,
            "reason": "mobile_companion_recommend_only",
        },
    }


@router.post(
    "/pairing/challenge",
    status_code=status.HTTP_201_CREATED,
    summary="Create a mobile pairing challenge",
)
async def create_pairing_challenge() -> dict[str, object]:
    """Create a short-lived pairing challenge without returning a bearer token."""

    code = f"{secrets.randbelow(10_000):04d}-{secrets.randbelow(10_000):04d}"
    challenge_id = uuid4().hex
    expires_at = datetime.now(UTC) + timedelta(seconds=_PAIRING_TTL_SECONDS)
    return {
        "challenge_id": challenge_id,
        "code": code,
        "pairing_url": f"/mobile/pair?challenge={challenge_id}",
        "expires_at": expires_at.isoformat(),
        "expires_in_seconds": _PAIRING_TTL_SECONDS,
    }


@router.post(
    "/intents",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record a mobile intent for human approval",
)
async def record_mobile_intent(intent: MobileIntentRequest) -> dict[str, object]:
    """Record intent as pending approval instead of executing it."""

    approval_required_for = _classify_approval_requirements(intent.text)
    receipt_id = f"mobile-{uuid4().hex[:12]}"
    return {
        "status": "approval_required",
        "intent": {
            "text": intent.text,
            "context": intent.context,
        },
        "approval_required_for": approval_required_for,
        "execution": {
            "executed": False,
            "reason": "mobile_companion_recommend_only",
        },
        "receipt": {
            "id": receipt_id,
            "source": "mobile_companion",
            "created_at": datetime.now(UTC).isoformat(),
        },
    }


def _classify_approval_requirements(text: str) -> list[str]:
    haystack = text.casefold()
    matched = [
        label
        for label, needles in _APPROVAL_RULES
        if any(needle in haystack for needle in needles)
    ]
    return matched or ["human review"]
