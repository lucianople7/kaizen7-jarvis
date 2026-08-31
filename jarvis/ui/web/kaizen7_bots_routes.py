"""REST API for the KAIZEN7 Bot Mode contract."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from jarvis.kaizen7.bots import BotRoster

router = APIRouter(prefix="/api/kaizen7/bots", tags=["kaizen7-bots"])


class BotCreateProposalRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    title: str = Field("", max_length=80)
    description: str = Field("", max_length=280)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value


def _roster(request: Request) -> BotRoster:
    config = getattr(request.app.state, "config", None)
    return BotRoster.from_config(config)


@router.get("")
async def list_bots(request: Request) -> dict[str, Any]:
    return _roster(request).list()


@router.post("/propose")
async def propose_bot(
    request: Request, payload: BotCreateProposalRequest
) -> dict[str, Any]:
    try:
        proposal = _roster(request).propose_create(
            name=payload.name,
            title=payload.title,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"proposal": proposal}

