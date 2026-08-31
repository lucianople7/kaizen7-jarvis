"""REST API for KAIZEN7 monetization and growth packs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.monetization import MonetizationEngine, default_monetization_engine

router = APIRouter(prefix="/api/kaizen7/monetization", tags=["kaizen7-monetization"])


class GrowthPackRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    business: str = Field(default="KAIZEN7 Business", max_length=200)
    audience: str = Field(default="buyers with a costly problem", max_length=500)
    assets: list[str] = Field(default_factory=list, max_length=20)
    needs: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("objective")
    @classmethod
    def _objective_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("objective cannot be blank")
        return value


def _engine(request: Request) -> MonetizationEngine:
    existing = getattr(request.app.state, "kaizen7_monetization_engine", None)
    if isinstance(existing, MonetizationEngine):
        return existing
    engine = default_monetization_engine()
    request.app.state.kaizen7_monetization_engine = engine
    return engine


def _bridge(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


@router.get("/playbooks")
async def monetization_playbooks(request: Request) -> dict[str, Any]:
    playbooks = _engine(request).playbooks()
    return {"playbooks": playbooks, "count": len(playbooks)}


@router.post("/pack")
async def monetization_pack(
    request: Request,
    payload: GrowthPackRequest,
) -> dict[str, Any]:
    try:
        pack = _engine(request).growth_pack(
            payload.objective,
            business=payload.business,
            audience=payload.audience,
            assets=payload.assets,
            needs=payload.needs,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"growth_pack": pack}


@router.post("/quick")
async def monetization_quick(
    request: Request,
    payload: GrowthPackRequest,
) -> dict[str, Any]:
    try:
        quick = _engine(request).quick_start(
            payload.objective,
            business=payload.business,
            audience=payload.audience,
            assets=payload.assets,
            needs=payload.needs,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"quick_start": quick}


@router.post("/propose")
async def monetization_propose(
    request: Request,
    payload: GrowthPackRequest,
) -> dict[str, Any]:
    try:
        proposal = _engine(request).propose(
            payload.objective,
            bridge=_bridge(request),
            business=payload.business,
            audience=payload.audience,
            assets=payload.assets,
            needs=payload.needs,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}
