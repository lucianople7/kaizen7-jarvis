"""REST API exposing safe Hermes runtime inspection."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.hermes_runtime import HermesRuntime

router = APIRouter(prefix="/api/kaizen7/hermes", tags=["kaizen7-hermes"])


class HermesChatProposalRequest(BaseModel):
    profile: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=20_000)


@router.get("/status")
async def hermes_status() -> dict[str, Any]:
    return HermesRuntime.from_environment().status()


@router.get("/profiles")
async def hermes_profiles() -> dict[str, Any]:
    return HermesRuntime.from_environment().profiles()


@router.get("/capabilities")
async def hermes_capabilities() -> dict[str, Any]:
    return HermesRuntime.from_environment().capabilities()


@router.get("/bot-mode")
async def hermes_bot_mode() -> dict[str, Any]:
    return HermesRuntime.from_environment().bot_mode_contract()


@router.post("/chat/propose")
async def hermes_chat_propose(
    request: Request, payload: HermesChatProposalRequest
) -> dict[str, Any]:
    try:
        proposal = HermesRuntime.from_environment().chat_plan(
            profile=payload.profile,
            message=payload.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store = ControlBridgeStore.from_config(getattr(request.app.state, "config", None))
    store.record_receipt(
        {
            "id": f"hermes-chat-{proposal['profile']}",
            "kind": "hermes_chat_proposal",
            "message": proposal["message"],
            "result": proposal,
            "status": "recorded",
            "execution_enabled": False,
        }
    )
    return {"proposal": proposal}


@router.get("/cron")
async def hermes_cron_list() -> dict[str, Any]:
    return HermesRuntime.from_environment().cron_list()


@router.get("/peers")
async def hermes_peer_list() -> dict[str, Any]:
    return HermesRuntime.from_environment().peer_list()
