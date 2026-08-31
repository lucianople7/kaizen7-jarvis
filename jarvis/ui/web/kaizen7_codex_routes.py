"""REST API exposing safe Codex CLI inspection and delegation proposals."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.codex_runtime import CodexRuntime

router = APIRouter(prefix="/api/kaizen7/codex", tags=["kaizen7-codex"])


class CodexDelegateProposalRequest(BaseModel):
    workdir: str = Field(min_length=1, max_length=500)
    prompt: str = Field(min_length=1, max_length=20_000)
    sandbox: Literal["workspace-write", "danger-full-access"] = "workspace-write"


@router.get("/status")
async def codex_status() -> dict[str, Any]:
    return CodexRuntime.from_environment().status()


@router.get("/capabilities")
async def codex_capabilities() -> dict[str, Any]:
    return CodexRuntime.from_environment().capabilities()


@router.post("/delegate/propose")
async def codex_delegate_propose(
    request: Request, payload: CodexDelegateProposalRequest
) -> dict[str, Any]:
    try:
        proposal = CodexRuntime.from_environment().delegate_plan(
            workdir=payload.workdir,
            prompt=payload.prompt,
            sandbox=payload.sandbox,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store = ControlBridgeStore.from_config(getattr(request.app.state, "config", None))
    store.record_receipt(
        {
            "id": "codex-delegate",
            "kind": "codex_delegate_proposal",
            "message": proposal["prompt"],
            "result": proposal,
            "status": "recorded",
            "execution_enabled": False,
        }
    )
    return {"proposal": proposal}
