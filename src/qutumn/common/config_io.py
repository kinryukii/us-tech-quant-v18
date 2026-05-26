from __future__ import annotations

from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    value = value.strip()

    if value == "":
        return ""

    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"null", "none"}:
        return None

    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        return value[1:-1]

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _prepare_lines(path: Path) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        if raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        rows.append((indent, line))

    return rows


def _parse_sequence(rows: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []

    while index < len(rows):
        row_indent, line = rows[index]

        if row_indent < indent:
            break
        if row_indent != indent or not line.startswith("- "):
            break

        value = line[2:].strip()
        items.append(_parse_scalar(value))
        index += 1

    return items, index


def _parse_mapping(rows: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    data: dict[str, Any] = {}

    while index < len(rows):
        row_indent, line = rows[index]

        if row_indent < indent:
            break
        if row_indent != indent:
            break
        if line.startswith("- "):
            break
        if ":" not in line:
            index += 1
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        index += 1

        if value != "":
            data[key] = _parse_scalar(value)
            continue

        if index >= len(rows):
            data[key] = {}
            continue

        next_indent, next_line = rows[index]

        if next_indent <= row_indent:
            data[key] = {}
            continue

        if next_line.startswith("- "):
            seq, index = _parse_sequence(rows, index, next_indent)
            data[key] = seq
        else:
            nested, index = _parse_mapping(rows, index, next_indent)
            data[key] = nested

    return data, index


def load_yaml_like(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        pass

    rows = _prepare_lines(path)
    data, _ = _parse_mapping(rows, 0, 0)
    return data
