from __future__ import annotations

import json
from pathlib import Path


def _tuple_literal(values: list[str]) -> str:
    if not values:
        return "()"
    if len(values) == 1:
        return f"({values[0]!r},)"
    return repr(tuple(values))


def generate(project_root: Path) -> Path:
    contract_path = project_root / "contract" / "openapi.json"
    output_path = project_root / "generated" / "user_fields.py"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    user_schema = contract["components"]["schemas"]["User"]
    fields = list(user_schema["properties"])
    required_fields = list(user_schema["required"])
    canonical_name_field = user_schema["x-canonical-name-field"]
    legacy_name_fields = [
        field for field in fields if field == "name" and field != canonical_name_field
    ]
    content = "\n".join(
        (
            '"""Generated from contract/openapi.json. Do not edit by hand."""',
            "",
            f"FIELDS = {_tuple_literal(fields)}",
            f"REQUIRED_FIELDS = {_tuple_literal(required_fields)}",
            f"CANONICAL_NAME_FIELD = {canonical_name_field!r}",
            f"LEGACY_NAME_FIELDS = {_tuple_literal(legacy_name_fields)}",
            "",
        )
    )
    output_path.write_text(content, encoding="utf-8", newline="\n")
    return output_path


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])
