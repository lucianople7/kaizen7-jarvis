"""REST API for the KAIZEN7 Agent OS planner."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.agent_os_planner import build_agent_os_plan
from jarvis.kaizen7.bridge import ControlBridgeStore

router = APIRouter(prefix="/api/kaizen7/agent-os", tags=["kaizen7-agent-os"])


class AgentOsPlanRequest(BaseModel):
    mission: str = Field(min_length=1, max_length=4000)
    needs: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)
    record_receipt: bool = False

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


@router.post("/plan")
async def agent_os_plan(request: Request, payload: AgentOsPlanRequest) -> dict[str, Any]:
    try:
        plan = build_agent_os_plan(
            payload.mission,
            needs=payload.needs,
            constraints=payload.constraints,
            bridge=_bridge(request) if payload.record_receipt else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"plan": plan}
