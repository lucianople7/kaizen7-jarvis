"""REST API for KAIZEN7's universal agent gateway."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.agent_gateway import AgentGateway, default_agent_gateway
from jarvis.kaizen7.bridge import ControlBridgeStore

router = APIRouter(prefix="/api/kaizen7/agents", tags=["kaizen7-agents"])


class AgentRecommendationRequest(BaseModel):
    mission: str = Field(min_length=1, max_length=4000)
    needs: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("mission")
    @classmethod
    def _mission_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("mission cannot be blank")
        return value


class AgentBenchRequest(BaseModel):
    env: dict[str, str] = Field(default_factory=dict)


class AgentProposalRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def _message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message cannot be blank")
        return value


def _gateway(request: Request) -> AgentGateway:
    existing = getattr(request.app.state, "kaizen7_agent_gateway", None)
    if isinstance(existing, AgentGateway):
        return existing
    gateway = default_agent_gateway()
    request.app.state.kaizen7_agent_gateway = gateway
    return gateway


def _bridge(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


@router.get("")
async def agent_list(request: Request) -> dict[str, Any]:
    agents = _gateway(request).list()
    return {"agents": agents, "count": len(agents)}


@router.get("/manifest")
async def agent_manifest(request: Request) -> dict[str, Any]:
    return {"manifest": _gateway(request).manifest()}


@router.post("/recommend")
async def agent_recommend(
    request: Request,
    payload: AgentRecommendationRequest,
) -> dict[str, Any]:
    try:
        recommendation = _gateway(request).recommend(
            payload.mission,
            needs=payload.needs,
            constraints=payload.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"recommendation": recommendation}


@router.get("/{agent_id}")
async def agent_detail(request: Request, agent_id: str) -> dict[str, Any]:
    try:
        agent = _gateway(request).get(agent_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"agent": agent}


@router.post("/{agent_id}/bench")
async def agent_bench(
    request: Request,
    agent_id: str,
    payload: AgentBenchRequest,
) -> dict[str, Any]:
    try:
        bench = _gateway(request).bench(agent_id, env=payload.env)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"bench": bench}


@router.post("/{agent_id}/propose")
async def agent_propose(
    request: Request,
    agent_id: str,
    payload: AgentProposalRequest,
) -> dict[str, Any]:
    try:
        proposal = _gateway(request).propose(
            agent_id,
            payload.message,
            bridge=_bridge(request),
            context=payload.context,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}
