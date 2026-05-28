from __future__ import annotations

import json
from pathlib import Path

from evidentia.models import PlayerProfile


def write_player_profile(path: Path, profile: PlayerProfile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "player_profile": profile.to_dict()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_player_profile(path: Path) -> PlayerProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    data = payload.get("player_profile") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise ValueError("invalid profile payload: missing player_profile object")
    return PlayerProfile(**data)
