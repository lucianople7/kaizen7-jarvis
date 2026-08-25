"""REST API for KAIZEN7 Growth OS."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.growth_os import GrowthOS, default_growth_os

router = APIRouter(prefix="/api/kaizen7/growth", tags=["kaizen7-growth"])


class GrowthCommandRequest(BaseModel):
    objective: str = Field(default="", max_length=4000)
    business: str = Field(default="KAIZEN7 Business", max_length=200)
    audience: str = Field(default="buyers with a costly problem", max_length=500)
    channels: list[str] = Field(default_factory=list, max_length=20)
    assets: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("objective")
    @classmethod
    def _objective_not_blank_when_present(cls, value: str) -> str:
        if value != "" and not value.strip():
            raise ValueError("objective cannot be blank")
        return value


class GrowthAuditRequest(BaseModel):
    business: str = Field(default="KAIZEN7 Business", max_length=200)
    assets: list[str] = Field(default_factory=list, max_length=20)


def _growth_os(request: Request) -> GrowthOS:
    existing = getattr(request.app.state, "kaizen7_growth_os", None)
    if isinstance(existing, GrowthOS):
        return existing
    growth = default_growth_os()
    request.app.state.kaizen7_growth_os = growth
    return growth


def _bridge(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


@router.get("/playbooks")
async def growth_surfaces(request: Request) -> dict[str, Any]:
    surfaces = _growth_os(request).surfaces()
    return {"surfaces": surfaces, "count": len(surfaces)}


@router.post("/command")
async def growth_command(
    request: Request,
    payload: GrowthCommandRequest,
) -> dict[str, Any]:
    try:
        card = _growth_os(request).command(
            payload.objective,
            business=payload.business,
            audience=payload.audience,
            channels=payload.channels,
            assets=payload.assets,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"growth_command": card}


@router.post("/launch-kit")
async def launch_kit(
    request: Request,
    payload: GrowthCommandRequest,
) -> dict[str, Any]:
    try:
        kit = _growth_os(request).launch_kit(
            payload.objective,
            business=payload.business,
            audience=payload.audience,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"launch_kit": kit}


@router.post("/asset")
async def growth_asset(
    request: Request,
    payload: GrowthCommandRequest,
) -> dict[str, Any]:
    channel = payload.channels[0] if payload.channels else "owned_content"
    try:
        asset = _growth_os(request).asset(
            payload.objective,
            business=payload.business,
            audience=payload.audience,
            channel=channel,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"growth_asset": asset}


@router.post("/ecommerce-audit")
async def ecommerce_audit(
    request: Request,
    payload: GrowthAuditRequest,
) -> dict[str, Any]:
    audit = _growth_os(request).ecommerce_audit(
        business=payload.business,
        assets=payload.assets,
    )
    return {"ecommerce_audit": audit}


@router.post("/propose")
async def growth_propose(
    request: Request,
    payload: GrowthCommandRequest,
) -> dict[str, Any]:
    try:
        proposal = _growth_os(request).propose(
            payload.objective,
            bridge=_bridge(request),
            business=payload.business,
            audience=payload.audience,
            channels=payload.channels,
            assets=payload.assets,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}
