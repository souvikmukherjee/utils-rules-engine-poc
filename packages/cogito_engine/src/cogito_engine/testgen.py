from __future__ import annotations

from itertools import product
from typing import Any

from cogito_engine.models import RulePack

# Hard caps for permutation explosion (documented API bound).
DEFAULT_MAX_CASES = 50
HARD_MAX_CASES = 500
MAX_DISCRETE_VALUES_PER_PATH = 8


def _collect_discrete(condition: dict[str, Any], buckets: dict[str, set[Any]]) -> None:
    """Walk a condition tree and collect discrete candidate values per fact path."""
    if "all" in condition:
        for child in condition["all"]:
            _collect_discrete(child, buckets)
        return
    if "any" in condition:
        for child in condition["any"]:
            _collect_discrete(child, buckets)
        return
    if "not" in condition:
        _collect_discrete(condition["not"], buckets)
        return

    path = condition.get("path")
    op = condition.get("op")
    value = condition.get("value")
    if not path or not op:
        return

    bucket = buckets.setdefault(path, set())
    if op == "in" and isinstance(value, list):
        for item in value[:MAX_DISCRETE_VALUES_PER_PATH]:
            bucket.add(_freeze(item))
    elif op in {"eq", "neq"} and value is not None:
        bucket.add(_freeze(value))
        # For neq/eq include a contrasting sentinel so both branches appear.
        if op == "neq":
            bucket.add(_freeze(f"__not__{value}"))
        elif op == "eq":
            bucket.add(_freeze(f"__other__{value}"))
    elif op == "exists":
        # Represent presence vs absence via a marker; facts builder expands these.
        bucket.add("__exists__")
        bucket.add("__missing__")
    elif op in {"gt", "gte", "lt", "lte"} and isinstance(value, (int, float)):
        bucket.add(_freeze(value))
        bucket.add(_freeze(value + 1 if op in {"gt", "gte"} else value - 1))
        bucket.add(_freeze(value - 1 if op in {"gt", "gte"} else value + 1))
    elif op == "contains" and value is not None:
        bucket.add(_freeze([value] if not isinstance(value, list) else value))
        bucket.add(_freeze([]))


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
    leaf = parts[-1]
    if value == "__missing__":
        cursor.pop(leaf, None)
        return
    if value == "__exists__":
        cursor[leaf] = True
        return
    cursor[leaf] = _unfreeze(value)


def generate_test_cases(
    pack: RulePack,
    *,
    max_cases: int | None = None,
) -> dict[str, Any]:
    """Deterministically generate permutation fixtures from discrete condition values.

    Bounds:
    - default max_cases = 50
    - hard max_cases = 500
    - at most 8 discrete values retained per fact path
    """
    limit = DEFAULT_MAX_CASES if max_cases is None else int(max_cases)
    limit = max(1, min(limit, HARD_MAX_CASES))

    buckets: dict[str, set[Any]] = {}
    for rule in pack.rules:
        if rule.enabled:
            _collect_discrete(rule.condition, buckets)

    paths = sorted(buckets.keys())
    value_lists: list[list[Any]] = []
    for path in paths:
        values = sorted(buckets[path], key=lambda v: repr(v))[:MAX_DISCRETE_VALUES_PER_PATH]
        if not values:
            values = [None]
        value_lists.append(values)

    cases: list[dict[str, Any]] = []
    truncated = False
    if not paths:
        cases.append({"subject_id": "case-0001", "facts": {}, "label": "empty_facts"})
    else:
        for idx, combo in enumerate(product(*value_lists), start=1):
            if idx > limit:
                truncated = True
                break
            facts: dict[str, Any] = {}
            for path, raw in zip(paths, combo):
                _set_path(facts, path, raw)
            cases.append(
                {
                    "subject_id": f"case-{idx:04d}",
                    "facts": facts,
                    "label": f"permutation_{idx}",
                }
            )

    return {
        "domain": pack.domain,
        "pack_id": pack.pack_id,
        "version": pack.version,
        "max_cases": limit,
        "hard_max_cases": HARD_MAX_CASES,
        "paths": paths,
        "truncated": truncated,
        "case_count": len(cases),
        "cases": cases,
    }
