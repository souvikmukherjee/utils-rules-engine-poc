from __future__ import annotations

from typing import Any


def get_path(facts: dict[str, Any], path: str) -> Any:
    current: Any = facts
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def eval_condition(condition: dict[str, Any], facts: dict[str, Any]) -> bool:
    if "all" in condition:
        return all(eval_condition(c, facts) for c in condition["all"])
    if "any" in condition:
        return any(eval_condition(c, facts) for c in condition["any"])
    if "not" in condition:
        return not eval_condition(condition["not"], facts)
    return eval_comparison(condition, facts)


def eval_comparison(comparison: dict[str, Any], facts: dict[str, Any]) -> bool:
    path = comparison["path"]
    op = comparison["op"]
    expected = comparison.get("value")
    actual = get_path(facts, path)

    if op == "exists":
        return actual is not None

    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "gt":
        return actual is not None and actual > expected
    if op == "gte":
        return actual is not None and actual >= expected
    if op == "lt":
        return actual is not None and actual < expected
    if op == "lte":
        return actual is not None and actual <= expected
    if op == "in":
        return actual in (expected or [])
    if op == "contains":
        if actual is None:
            return False
        return expected in actual

    raise ValueError(f"Unsupported operator: {op}")
