"""REST API for the KAIZEN7 capability marketplace."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.capabilities import (
    CapabilityRegistry,
    default_capability_registry,
)

router = APIRouter(prefix="/api/kaizen7/capabilities", tags=["kaizen7-capabilities"])


class CapabilityPlanRequest(BaseModel):
    mission: str = Field(min_length=1, max_length=4000)
    needs: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("mission")
    @classmethod
    def _mission_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("mission cannot be blank")
        return value


def _registry(request: Request) -> CapabilityRegistry:
    existing = getattr(request.app.state, "kaizen7_capability_registry", None)
    if isinstance(existing, CapabilityRegistry):
        return existing
    registry = default_capability_registry()
    request.app.state.kaizen7_capability_registry = registry
    return registry


@router.get("")
async def capability_list(request: Request) -> dict[str, Any]:
    capabilities = _registry(request).list()
    return {"capabilities": capabilities, "count": len(capabilities)}


@router.get("/{capability_id}")
async def capability_detail(request: Request, capability_id: str) -> dict[str, Any]:
    try:
        capability = _registry(request).get(capability_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"capability": capability}


@router.post("/plan")
async def capability_plan(
    request: Request,
    payload: CapabilityPlanRequest,
) -> dict[str, Any]:
    try:
        plan = _registry(request).launch_plan(
            payload.mission,
            needs=payload.needs,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"plan": plan}
