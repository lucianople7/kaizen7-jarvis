"""REST API for KAIZEN7 product readiness."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.product_readiness import build_product_readiness

router = APIRouter(prefix="/api/kaizen7/product", tags=["kaizen7-product"])


def _bridge(request: Request) -> ControlBridgeStore:
    existing = getattr(request.app.state, "kaizen7_bridge", None)
    if isinstance(existing, ControlBridgeStore):
        return existing
    config = getattr(request.app.state, "config", None)
    store = ControlBridgeStore.from_config(config)
    request.app.state.kaizen7_bridge = store
    return store


@router.get("/readiness")
async def product_readiness(request: Request) -> dict[str, Any]:
    config = getattr(request.app.state, "config", None)
    return {"readiness": build_product_readiness(config=config, bridge=_bridge(request))}
