"""Read-only KAIZEN7 business capsule for Luciano's personalized Jarvis."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/kaizen7", tags=["kaizen7"])

#: Brand assets live in the repo's assets/kaizen7/ folder and are served here
#: so the web UI and the mobile companion can render the THE FOCUX logo in
#: dev and production alike (no SPA/static-mount coupling).
_KAIZEN7_ASSETS = (
    Path(__file__).resolve().parents[3] / "assets" / "kaizen7"
)

_BRAND_FILES: dict[str, str] = {
    "mark": "the-focux-mark-1024.png",
    "poster": "the-focux-logo-poster.png",
}


@router.get("/brand/{asset}", summary="THE FOCUX brand asset")
async def brand_asset(asset: str) -> FileResponse:
    """Serve a THE FOCUX brand asset (mark, poster) as an image."""
    filename = _BRAND_FILES.get(asset)
    if filename is None:
        raise HTTPException(status_code=404, detail=f"unknown brand asset: {asset}")
    path = _KAIZEN7_ASSETS / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"brand asset missing: {filename}")
    return FileResponse(str(path))


@router.get("/capsule", summary="KAIZEN7 business capsule")
async def capsule() -> dict[str, object]:
    """Return the first focused KAIZEN7/THE FOCUX operating profile.

    This endpoint is deliberately read-only. It gives the UI and CLI a stable
    source of identity, priorities, and approval boundaries without performing
    work on Luciano's behalf.
    """
    return {
        "owner": "Luciano Lopez Barba",
        "identity": {
            "name": "KAIZEN7",
            "role": "Focus and execution layer for Luciano",
            "kernel": [
                "Luciano decides.",
                "KAIZEN7 focuses.",
                "Agents execute through approved routes.",
                "Projects grow.",
                "Life does not disperse.",
            ],
        },
        "business": {
            "name": "THE FOCUX",
            "positioning": "A disciplined focus system for digital business growth.",
            "north_star": (
                "Turn attention into trusted content, clear offers, sale paths, "
                "and verified improvement."
            ),
        },
        "active_mission": {
            "name": "Personalized Jarvis for focused execution",
            "outcome": (
                "A local operating assistant that keeps one mission visible, "
                "limits priorities, and records evidence before claiming progress."
            ),
        },
        "priorities": [
            "Keep one active mission visible.",
            "Convert intent into the smallest verified next action.",
            "Record receipts for decisions, actions, tests, and results.",
        ],
        "operating_loop": [
            "Clarify the mission.",
            "Recommend the next move.",
            "Ask approval when risk requires it.",
            "Execute only through approved tools.",
            "Record the receipt.",
            "Review metrics and improve the next cycle.",
        ],
        "approval_required_for": [
            "payments",
            "purchases",
            "public posts",
            "outbound messages",
            "credentials",
            "financial operations",
            "deployments",
            "destructive edits",
            "irreversible desktop actions",
        ],
        "assets": {
            "mark": "/api/kaizen7/brand/mark",
            "poster": "/api/kaizen7/brand/poster",
        },
    }
