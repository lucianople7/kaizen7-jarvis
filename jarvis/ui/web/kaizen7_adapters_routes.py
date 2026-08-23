"""REST API for KAIZEN7's agent-agnostic adapter registry."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.adapters import AdapterRegistry, default_adapter_registry
from jarvis.kaizen7.bridge import ControlBridgeStore

router = APIRouter(prefix="/api/kaizen7/adapters", tags=["kaizen7-adapters"])


class AdapterRecommendationRequest(BaseModel):
    mission: str = Field(min_length=1, max_length=4000)
    needs: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("mission")
    @classmethod
    def _mission_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("mission cannot be blank")
        return value


class AdapterProposalRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def _message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message cannot be blank")
        return value


def _registry(request: Request) -> AdapterRegistry:
    existing = getattr(request.app.state, "kaizen7_adapter_registry", None)
    if isinstance(existing, AdapterRegistry):
        return existing
    registry = default_adapter_registry()
    request.app.state.kaizen7_adapter_registry = registry
    return registry


def _bridge(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


@router.get("")
async def adapter_list(request: Request) -> dict[str, Any]:
    adapters = _registry(request).list()
    return {"adapters": adapters, "count": len(adapters)}


@router.get("/manifest")
async def adapter_manifest(request: Request) -> dict[str, Any]:
    return {"manifest": _registry(request).manifest()}


@router.post("/recommend")
async def adapter_recommend(
    request: Request,
    payload: AdapterRecommendationRequest,
) -> dict[str, Any]:
    try:
        recommendation = _registry(request).recommend(
            payload.mission,
            needs=payload.needs,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"recommendation": recommendation}


@router.get("/{adapter_id}")
async def adapter_detail(request: Request, adapter_id: str) -> dict[str, Any]:
    try:
        adapter = _registry(request).get(adapter_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"adapter": adapter}


@router.post("/{adapter_id}/propose")
async def adapter_propose(
    request: Request,
    adapter_id: str,
    payload: AdapterProposalRequest,
) -> dict[str, Any]:
    try:
        proposal = _registry(request).propose(
            adapter_id,
            payload.message,
            bridge=_bridge(request),
            context=payload.context,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}
