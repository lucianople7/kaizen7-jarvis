"""REST API for KAIZEN7's pluggable provider registry."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.providers import ProviderRegistry, default_provider_registry

router = APIRouter(prefix="/api/kaizen7/providers", tags=["kaizen7-providers"])


class ProviderProposalRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message cannot be blank")
        return value


class ProviderRecommendationRequest(BaseModel):
    mission: str = Field(min_length=1, max_length=4000)
    needs: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("mission")
    @classmethod
    def _mission_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("mission cannot be blank")
        return value


def _bridge(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


def _registry(request: Request) -> ProviderRegistry:
    existing = getattr(request.app.state, "kaizen7_provider_registry", None)
    if isinstance(existing, ProviderRegistry):
        return existing
    registry = default_provider_registry()
    request.app.state.kaizen7_provider_registry = registry
    return registry


@router.get("")
async def provider_list(request: Request) -> dict[str, Any]:
    providers = _registry(request).list()
    return {"providers": providers, "count": len(providers)}


@router.post("/recommend")
async def provider_recommend(
    request: Request,
    payload: ProviderRecommendationRequest,
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


@router.get("/{provider_id}")
async def provider_detail(request: Request, provider_id: str) -> dict[str, Any]:
    try:
        provider = _registry(request).get(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"provider": provider}


@router.post("/{provider_id}/propose")
async def provider_propose(
    request: Request,
    provider_id: str,
    payload: ProviderProposalRequest,
) -> dict[str, Any]:
    try:
        proposal = _registry(request).propose(
            provider_id,
            payload.message,
            bridge=_bridge(request),
            context=payload.context,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}
