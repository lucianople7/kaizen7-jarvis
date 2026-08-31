"""REST API for KAIZEN7's market pattern blueprint."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from jarvis.kaizen7.market_blueprint import (
    default_market_blueprint,
    market_upgrade_plan,
)

router = APIRouter(
    prefix="/api/kaizen7/market-blueprint",
    tags=["kaizen7-market-blueprint"],
)


@router.get("")
async def market_blueprint() -> dict[str, Any]:
    patterns = default_market_blueprint().list()
    return {"patterns": patterns, "count": len(patterns)}


@router.get("/upgrade-plan")
async def market_blueprint_upgrade_plan() -> dict[str, Any]:
    return {"plan": market_upgrade_plan()}
