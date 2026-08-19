"""REST API for the recommendation-only Control Bridge."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.bridge import ControlBridgeStore

router = APIRouter(prefix="/api/kaizen7/bridge", tags=["kaizen7-bridge"])


class BridgeProposalRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message cannot be blank")
        return value


def _store(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


@router.get("/status")
async def bridge_status(request: Request) -> dict[str, Any]:
    return _store(request).status()


@router.get("/capabilities")
async def bridge_capabilities(request: Request) -> dict[str, Any]:
    capabilities = _store(request).capabilities()
    return {"capabilities": capabilities, "count": len(capabilities)}


@router.post("/propose")
async def bridge_propose(
    request: Request, payload: BridgeProposalRequest
) -> dict[str, Any]:
    try:
        proposal = _store(request).propose(payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}


@router.get("/receipts")
async def bridge_receipts(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    receipts = _store(request).receipts(limit=limit)
    return {"receipts": receipts, "count": len(receipts)}

