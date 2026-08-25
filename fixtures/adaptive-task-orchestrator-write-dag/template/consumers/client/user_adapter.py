from __future__ import annotations

from typing import Any


def serialize_user(user: dict[str, Any]) -> dict[str, str]:
    user_id = user.get("id")
    name = user.get("name")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("id must be a non-empty string")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    return {"id": user_id, "name": name}
