from __future__ import annotations

import re
from itertools import product
from typing import Any

from rules_engine.models import RulePack

# Hard caps for permutation explosion (documented API bound).
DEFAULT_MAX_CASES = 50
HARD_MAX_CASES = 500
MAX_DISCRETE_VALUES_PER_PATH = 8

_STRING_LITERAL = re.compile(r"'([^']*)'|\"([^\"]*)\"")
_BOOL_LITERAL = re.compile(r"^\s*(true|false)\s*$", re.I)


def _literals_from_unary(cell: str) -> list[Any]:
    """Pull discrete candidate values from a Zen unary decision-table cell."""
    text = (cell or "").strip()
    if not text:
        return []
    bool_match = _BOOL_LITERAL.match(text)
    if bool_match:
        return [bool_match.group(1).lower() == "true"]

    found = [a or b for a, b in _STRING_LITERAL.findall(text)]
    if found:
        return found[:MAX_DISCRETE_VALUES_PER_PATH]

    # Numeric comparisons — sample around the threshold when present.
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    values: list[Any] = []
    for n in nums[:3]:
        values.append(float(n) if "." in n else int(n))
    return values[:MAX_DISCRETE_VALUES_PER_PATH]


def _collect_from_pack(pack: RulePack) -> dict[str, set[Any]]:
    buckets: dict[str, set[Any]] = {}
    for node in pack.decision_table_nodes():
        content = node.get("content") or {}
        inputs = content.get("inputs") or []
        id_to_field = {
            col["id"]: col["field"]
            for col in inputs
            if isinstance(col, dict) and col.get("id") and col.get("field")
        }
        for rule in content.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            for col_id, field in id_to_field.items():
                if field == "as_of":
                    continue
                cell = rule.get(col_id, "")
                if not isinstance(cell, str):
                    continue
                bucket = buckets.setdefault(field, set())
                for value in _literals_from_unary(cell):
                    bucket.add(_freeze(value))
                # Include a contrasting sentinel so unmatched branches appear.
                if bucket:
                    bucket.add(_freeze(f"__other__{field}"))
    return buckets


def _freeze(value: Any) -> Any:
    if isinstance(value, list):
        return ("__list__", tuple(_freeze(v) for v in value))
    if isinstance(value, dict):
        return ("__dict__", tuple(sorted((k, _freeze(v)) for k, v in value.items())))
    return value


def _unfreeze(value: Any) -> Any:
    if isinstance(value, tuple) and value and value[0] == "__list__":
        return [_unfreeze(v) for v in value[1]]
    if isinstance(value, tuple) and value and value[0] == "__dict__":
        return {k: _unfreeze(v) for k, v in value[1]}
    return value


def _set_path(facts: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cursor = facts
    for part in parts[:-1]:
        nxt = cursor.setdefault(part, {})
        if not isinstance(nxt, dict):
            cursor[part] = {}
            nxt = cursor[part]
        cursor = nxt
    cursor[parts[-1]] = value


def generate_test_cases(
    pack: RulePack,
    *,
    max_cases: int | None = None,
) -> dict[str, Any]:
    """Build deterministic fixture permutations from decision-table input cells."""
    limit = DEFAULT_MAX_CASES if max_cases is None else int(max_cases)
    limit = max(1, min(limit, HARD_MAX_CASES))

    buckets = _collect_from_pack(pack)
    paths = sorted(buckets.keys())
    value_lists: list[list[Any]] = []
    for path in paths:
        values = sorted(buckets[path], key=lambda v: repr(v))[:MAX_DISCRETE_VALUES_PER_PATH]
        value_lists.append([_unfreeze(v) for v in values])

    cases: list[dict[str, Any]] = []
    if not paths:
        cases.append({"subject_id": "FF-TEST-0", "facts": {}})
    else:
        for idx, combo in enumerate(product(*value_lists)):
            if idx >= limit:
                break
            facts: dict[str, Any] = {}
            for path, value in zip(paths, combo):
                if isinstance(value, str) and value.startswith("__other__"):
                    _set_path(facts, path, "unknown")
                else:
                    _set_path(facts, path, value)
            cases.append({"subject_id": f"FF-TEST-{idx}", "facts": facts})

    return {
        "domain": pack.domain,
        "pack_id": pack.pack_id,
        "version": pack.version,
        "paths": paths,
        "case_count": len(cases),
        "max_cases": limit,
        "hard_max_cases": HARD_MAX_CASES,
        "cases": cases,
    }
