from __future__ import annotations

from typing import Any


def normalize_user(payload: dict[str, Any]) -> dict[str, str]:
    user_id = payload.get("id")
    name = payload.get("name")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("id must be a non-empty string")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    return {"id": user_id, "name": name}
