"""Bot roster contract built on the existing assistant mode primitive.

Hermes Bot Mode's key product lesson is good: do not invent a second agent
primitive when profiles already exist. In this fork, assistant modes are the
existing persistent specialist primitive, so the KAIZEN7 bot roster is a
read-only view over modes plus safe proposals for future bot creation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis.brain import modes
from jarvis.kaizen7.bridge import ControlBridgeStore, _utc_now


@dataclass(frozen=True)
class BotRoster:
    """Read-only bot roster plus recommendation-only creation proposals."""

    bridge: ControlBridgeStore

    @classmethod
    def from_config(cls, config: Any | None = None) -> BotRoster:
        return cls(bridge=ControlBridgeStore.from_config(config))

    def list(self) -> dict[str, Any]:
        active = modes.active_slug()
        bots = [_bot_payload(mode, active=active) for mode in modes.list_modes()]
        return {
            "source": "assistant_modes",
            "profile_primitive": "mode",
            "active": active,
            "execution_enabled": False,
            "bots": bots,
            "count": len(bots),
            "implemented": {
                "roster": True,
                "canonical_chat": False,
                "routines": False,
                "groups": False,
                "cross_machine": False,
            },
        }

    def propose_create(
        self, *, name: str, title: str = "", description: str = ""
    ) -> dict[str, Any]:
        clean_name = " ".join(name.strip().split())
        if not clean_name:
            raise ValueError("Bot name cannot be blank.")
        slug = modes.normalize_slug(clean_name)
        clean_title = " ".join((title or clean_name).strip().split())
        clean_description = " ".join(description.strip().split())
        now = _utc_now()
        draft = {
            "slug": slug,
            "name": clean_name,
            "title": clean_title,
            "description": clean_description,
            "profile_primitive": "mode",
            "handle": f"@{slug}",
        }
        proposal = {
            "id": f"bot-{slug}-{now.replace(':', '').replace('+', 'z')}",
            "kind": "bot_create_proposal",
            "status": "proposed",
            "draft": draft,
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
        }
        self.bridge.record_receipt(
            {
                "id": proposal["id"],
                "kind": "bot_create_proposal",
                "message": f"Create bot profile {clean_name}",
                "result": draft,
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal


def _bot_payload(mode: modes.Mode, *, active: str) -> dict[str, Any]:
    return {
        "slug": mode.slug,
        "handle": f"@{mode.slug}",
        "name": mode.name,
        "title": mode.name,
        "description": mode.description,
        "avatar": {
            "kind": "mode",
            "emoji": mode.emoji,
        },
        "profile_primitive": "mode",
        "memory_scope": f"mode:{mode.slug}",
        "routine_namespace": f"[bot:{mode.slug}]",
        "active": mode.slug == active,
        "built_in": mode.built_in,
        "implemented": {
            "roster": True,
            "canonical_chat": False,
            "routines": False,
            "groups": False,
            "cross_machine": False,
        },
    }

