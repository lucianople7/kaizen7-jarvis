"""Recommendation-only local control bridge.

This module deliberately stops at proposal and receipt recording. It gives
external/local surfaces a stable place to ask "what could we do next?" without
creating an execution path that could send messages, spend money, publish,
touch credentials, perform financial operations, or make irreversible changes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from jarvis.core.paths import user_data_dir

APPROVAL_REQUIRED_FOR: tuple[str, ...] = (
    "payments",
    "publishing",
    "messages",
    "credentials",
    "financial_operations",
    "external_sends",
    "destructive_changes",
    "irreversible_changes",
)

CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "id": "kaizen7-bridge-status",
        "title": "Show Control Bridge status",
        "description": "Read the local bridge safety mode and receipt count.",
        "method": "GET",
        "path": "/api/kaizen7/bridge/status",
        "dangerous": False,
    },
    {
        "id": "kaizen7-bridge-capabilities",
        "title": "List Control Bridge capabilities",
        "description": "Read the safe operations currently exposed by the bridge.",
        "method": "GET",
        "path": "/api/kaizen7/bridge/capabilities",
        "dangerous": False,
    },
    {
        "id": "kaizen7-bridge-propose",
        "title": "Record a Control Bridge proposal",
        "description": "Record a recommendation-only proposal as an activity receipt.",
        "method": "POST",
        "path": "/api/kaizen7/bridge/propose",
        "dangerous": False,
    },
    {
        "id": "kaizen7-bridge-receipts",
        "title": "List Control Bridge receipts",
        "description": "Read recent recommendation and activity receipts.",
        "method": "GET",
        "path": "/api/kaizen7/bridge/receipts",
        "dangerous": False,
    },
)


@dataclass(frozen=True)
class ControlBridgeStore:
    """Tiny durable JSONL store for bridge receipts."""

    root: Path

    @classmethod
    def from_config(cls, config: Any | None = None) -> ControlBridgeStore:
        data_dir = getattr(getattr(config, "memory", None), "data_dir", None)
        if data_dir:
            root = Path(data_dir) / "kaizen7" / "bridge"
        else:
            root = user_data_dir() / "data" / "kaizen7" / "bridge"
        return cls(root=root)

    @property
    def receipts_path(self) -> Path:
        return self.root / "receipts.jsonl"

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "mode": "recommendation_only",
            "execution_enabled": False,
            "approval_required_for": list(APPROVAL_REQUIRED_FOR),
            "receipts_count": self._receipt_count(),
            "storage_path": str(self.receipts_path),
        }

    def capabilities(self) -> list[dict[str, Any]]:
        return [dict(item) for item in CAPABILITIES]

    def propose(self, message: str) -> dict[str, Any]:
        clean = " ".join(message.strip().split())
        if not clean:
            raise ValueError("Proposal message cannot be blank.")
        now = _utc_now()
        proposal = {
            "id": f"bridge-{uuid4().hex}",
            "message": clean,
            "recommendation": _recommendation_for(clean),
            "status": "proposed",
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
        }
        self.record_receipt(
            {
                "id": proposal["id"],
                "kind": "proposal",
                "message": clean,
                "result": proposal["recommendation"],
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal

    def record_receipt(self, receipt: dict[str, Any]) -> None:
        self._append_receipt(receipt)

    def receipts(self, *, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = min(max(int(limit), 1), 200)
        if not self.receipts_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.receipts_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return list(reversed(rows))[:safe_limit]

    def _append_receipt(self, receipt: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def _receipt_count(self) -> int:
        if not self.receipts_path.exists():
            return 0
        count = 0
        with self.receipts_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    count += 1
        return count


def _recommendation_for(message: str) -> str:
    return (
        "Review the request, choose one reversible next action, and request "
        "separate human approval before any execution. Recorded proposal: "
        f"{message}"
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
