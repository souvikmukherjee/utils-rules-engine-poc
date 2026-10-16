"""Compile GoRules JDM decision tables into Cogito condition-IR packs.

Authoring stays in the JDM editor; when the engine toggle is Cogito, the
platform redirects evaluation through this compiler + the Cogito evaluator.
"""

from __future__ import annotations

import ast
import re
from datetime import datetime
from typing import Any

from cogito_engine.models import Effect, Rule, RulePack, parse_dt

_DATE_WINDOW_RE = re.compile(
    r">=\s*date\(\s*['\"]([^'\"]+)['\"]\s*\)\s*and\s*<\s*date\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.IGNORECASE,
)
_SINGLE_DATE_RE = re.compile(
    r"(>=|>|<=|<)\s*date\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.IGNORECASE,
)
_NOT_IN_RE = re.compile(r"^not\s+in\s+(.+)$", re.IGNORECASE)


def _strip_quotes(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _literal(raw: str) -> Any:
    text = raw.strip()
    if not text or text.lower() == "null":
        return None
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return _strip_quotes(text)


def _parse_listish(raw: str) -> list[Any]:
    text = raw.strip()
    if text.startswith("[") and text.endswith("]"):
        value = _literal(text)
        if isinstance(value, (list, tuple)):
            return list(value)
    # Zen-style: 'gold', 'platinum', 'diamond'
    parts = [p.strip() for p in text.split(",") if p.strip()]
    return [_literal(p) for p in parts]


def _parse_input_cell(
    field: str,
    raw: str | None,
) -> tuple[dict[str, Any] | None, datetime | None, datetime | None]:
    """Return (condition_fragment | None, effective_from | None, effective_to | None)."""
    if raw is None:
        return None, None, None
    text = str(raw).strip()
    if not text:
        return None, None, None

    # Temporal cells on as_of → rule effective window (not a fact condition).
    if field in {"as_of", "as_of_iso"} or field.endswith(".as_of"):
        window = _DATE_WINDOW_RE.search(text)
        if window:
            start = parse_dt(window.group(1) + "T00:00:00Z")
            end = parse_dt(window.group(2) + "T00:00:00Z")
            return None, start, end
        single = _SINGLE_DATE_RE.search(text)
        if single:
            op, date_s = single.group(1), single.group(2)
            dt = parse_dt(date_s + "T00:00:00Z")
            if op in {">=", ">"}:
                return None, dt, None
            if op in {"<=", "<"}:
                return None, None, dt

    not_in = _NOT_IN_RE.match(text)
    if not_in:
        values = _parse_listish(not_in.group(1))
        return {"not": {"path": field, "op": "in", "value": values}}, None, None

    if text.lower().startswith("in "):
        values = _parse_listish(text[3:].strip())
        return {"path": field, "op": "in", "value": values}, None, None

    # Comma-separated quoted literals without brackets → in
    if "," in text and ("'" in text or '"' in text):
        values = _parse_listish(text)
        if len(values) > 1:
            return {"path": field, "op": "in", "value": values}, None, None

    value = _literal(text)
    if isinstance(value, list):
        return {"path": field, "op": "in", "value": value}, None, None
    return {"path": field, "op": "eq", "value": value}, None, None


def _parse_output_value(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (bool, int, float)):
        return raw
    text = str(raw).strip()
    if not text or text.lower() == "null":
        return None
    return _literal(text)


def _combine_conditions(parts: list[dict[str, Any]]) -> dict[str, Any]:
    if not parts:
        return {"path": "__always__", "op": "eq", "value": True}
    if len(parts) == 1:
        return parts[0]
    return {"all": parts}


def _row_to_rule(
    row: dict[str, Any],
    *,
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    index: int,
    default_from: datetime,
) -> Rule | None:
    conditions: list[dict[str, Any]] = []
    effective_from = default_from
    effective_to: datetime | None = None

    for inp in inputs:
        cell_id = inp["id"]
        field = inp.get("field") or inp.get("name")
        if not field:
            continue
        frag, win_from, win_to = _parse_input_cell(str(field), row.get(cell_id))
        if frag is not None:
            conditions.append(frag)
        if win_from is not None:
            effective_from = win_from
        if win_to is not None:
            effective_to = win_to

    out_map: dict[str, Any] = {}
    for out in outputs:
        cell_id = out["id"]
        field = out.get("field") or out.get("name")
        if not field:
            continue
        out_map[str(field)] = _parse_output_value(row.get(cell_id))

    effect_type = out_map.get("effect_type") or out_map.get("decision")
    if not effect_type:
        return None
    effect_type = str(effect_type)

    payload: dict[str, Any] = {}
    for key in ("lounge_class", "reason", "companions_allowed", "via"):
        if out_map.get(key) is not None:
            payload[key] = out_map[key]

    persist = bool(out_map.get("persist_as_entitlement") or False)
    benefit_type = out_map.get("benefit_type")
    if benefit_type is not None:
        benefit_type = str(benefit_type)

    rule_id = out_map.get("rule_id") or row.get("_id") or f"jdm-row-{index}"
    rule_id = str(rule_id)
    name = str(row.get("_id") or rule_id)

    # Always-true sentinel for empty input rows — inject a fact at evaluate time
    # is awkward; use exists on a synthetic path that we treat as always true
    # via a special-case in conditions, OR use a tautology with `any` empty skip.
    condition = _combine_conditions(conditions)
    if condition.get("path") == "__always__":
        # Match any facts: empty `all` is True in our evaluator.
        condition = {"all": []}

    effect = Effect(
        type=effect_type,
        payload=payload,
        persist_as_entitlement=persist,
        benefit_type=benefit_type,
        source_rule_id=rule_id,
    )

    # Deny / allow rows that only set decision without a useful effect still count.
    return Rule(
        id=rule_id if row.get("_id") is None else str(row.get("_id")),
        name=name,
        priority=1000 - index,
        enabled=True,
        effective_from=effective_from,
        effective_to=effective_to,
        condition=condition,
        effects=(effect,),
    )


def jdm_to_cogito_pack(payload: dict[str, Any]) -> RulePack:
    """Compile a platform pack envelope (nodes/edges JDM) into a Cogito RulePack."""
    if "rules" in payload and isinstance(payload["rules"], list) and payload["rules"]:
        # Already native Cogito IR.
        first = payload["rules"][0]
        if isinstance(first, dict) and "condition" in first:
            return RulePack.from_dict(payload)

    nodes = payload.get("nodes") or []
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("Pack payload must include JDM nodes or Cogito rules")

    default_from = parse_dt("2020-01-01T00:00:00Z")
    assert default_from is not None

    compiled: list[Rule] = []
    index = 0
    for node in nodes:
        if not isinstance(node, dict) or node.get("type") != "decisionTableNode":
            continue
        content = node.get("content") or {}
        inputs = list(content.get("inputs") or [])
        outputs = list(content.get("outputs") or [])
        for row in content.get("rules") or []:
            if not isinstance(row, dict):
                continue
            rule = _row_to_rule(
                row,
                inputs=inputs,
                outputs=outputs,
                index=index,
                default_from=default_from,
            )
            index += 1
            if rule is not None:
                compiled.append(rule)

    if not compiled:
        raise ValueError("No decision-table rows could be compiled for Cogito")

    by_priority = sorted(compiled, key=lambda r: (-r.priority, r.id))
    return RulePack(
        domain=str(payload.get("domain") or "lounge"),
        pack_id=str(payload.get("pack_id") or "lounge-access"),
        version=str(payload.get("version") or "0.0.0"),
        lifecycle=str(payload.get("lifecycle") or "draft"),
        rules=tuple(by_priority),
    )
