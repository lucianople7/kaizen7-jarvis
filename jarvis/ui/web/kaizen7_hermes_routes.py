"""REST API exposing safe Hermes runtime inspection."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from jarvis.kaizen7.hermes_runtime import HermesRuntime

router = APIRouter(prefix="/api/kaizen7/hermes", tags=["kaizen7-hermes"])


@router.get("/status")
async def hermes_status() -> dict[str, Any]:
    return HermesRuntime.from_environment().status()


@router.get("/profiles")
async def hermes_profiles() -> dict[str, Any]:
    return HermesRuntime.from_environment().profiles()

