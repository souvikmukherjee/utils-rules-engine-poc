from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable

import zen

from rules_engine.models import (
    DecisionResult,
    DecisionTrace,
    Effect,
    EntitlementSnapshot,
    RulePack,
    RuleTraceEntry,
    parse_dt,
)

# Entitlement benefit types that imply lounge access for the lounge domain PoC.
ACCESS_BENEFIT_TYPES = frozenset(
    {
        "lounge_access",
        "companion_pass",
        "one_off_access",
    }
)

_ENGINE = zen.ZenEngine()


def _normalize_as_of(as_of: datetime | str | None) -> datetime:
    if as_of is None:
        return datetime.now(timezone.utc)
    parsed = parse_dt(as_of)
    assert parsed is not None
    return parsed


def _resolve_decision(effects: Iterable[Effect]) -> str:
    types = {e.type for e in effects}
    if "deny" in types:
        return "deny"
    if "allow" in types or "grant_access" in types:
        return "allow"
    if types:
        return "allow"
    return "inconclusive"


def _match_to_effect(row: dict[str, Any]) -> Effect | None:
    """Map one collected decision-table row into a platform Effect."""
    effect_type = row.get("effect_type") or row.get("decision")
    if not effect_type:
        return None
    effect_type = str(effect_type)

    payload: dict[str, Any] = {}
    for key in ("lounge_class", "reason", "companions_allowed", "via"):
        value = row.get(key)
        if value is not None:
            payload[key] = value

    persist = bool(row.get("persist_as_entitlement", False))
    benefit_type = row.get("benefit_type")
    if benefit_type is not None:
        benefit_type = str(benefit_type)

    rule_id = row.get("rule_id")
    if rule_id is not None:
        rule_id = str(rule_id)

    return Effect(
        type=effect_type,
        payload=payload,
        persist_as_entitlement=persist,
        on_pack_change="honor_existing",
        benefit_type=benefit_type,
        source_rule_id=rule_id,
    )


def _extract_matches(zen_result: dict[str, Any]) -> list[dict[str, Any]]:
    result = zen_result.get("result") or {}
    matches = result.get("matches")
    if isinstance(matches, list):
        return [m for m in matches if isinstance(m, dict)]
    # Single-hit tables may return flat fields without outputPath.
    if any(k in result for k in ("decision", "effect_type", "rule_id")):
        return [result]
    return []


def _trace_from_zen(
    zen_trace: dict[str, Any] | None,
    matched_effects: list[Effect],
) -> list[RuleTraceEntry]:
    entries: list[RuleTraceEntry] = []
    seen_rules: set[str] = set()

    for effect in matched_effects:
        rid = effect.source_rule_id or effect.type
        if rid in seen_rules:
            # Attach additional effects onto the existing matched entry.
            for entry in entries:
                if entry.rule_id == rid and entry.status == "matched":
                    entry.effects.append(effect.to_dict())
                    break
            continue
        seen_rules.add(rid)
        entries.append(
            RuleTraceEntry(
                rule_id=rid,
                rule_name=rid,
                status="matched",
                reason="zen_decision_table_match",
                effects=[effect.to_dict()],
            )
        )

    if zen_trace:
        for node_id, node_trace in zen_trace.items():
            if not isinstance(node_trace, dict):
                continue
            name = node_trace.get("name") or node_id
            entries.append(
                RuleTraceEntry(
                    rule_id=str(node_id),
                    rule_name=str(name),
                    status="zen_node",
                    reason=str(node_trace.get("nodeType") or "executed"),
                )
            )

    return entries


def evaluate(
    pack: RulePack,
    facts: dict[str, Any],
    *,
    as_of: datetime | str | None = None,
    entitlements: list[EntitlementSnapshot] | None = None,
) -> DecisionResult:
    """Evaluate facts against a JDM pack via GoRules Zen, then apply platform policy.

    Platform layer (not Zen):
    - injects ``as_of`` as a Unix timestamp for temporal table cells
    - honors entitlement ledger rows (grandfathering)
    - deny-wins conflict resolution across collected effects
    """
    clock = _normalize_as_of(as_of)
    entitlements = list(entitlements or [])
    trace = DecisionTrace(as_of=clock, pack_version=pack.version)

    honored: list[EntitlementSnapshot] = []
    entitlement_effects: list[Effect] = []

    for ent in entitlements:
        if ent.benefit_type in ACCESS_BENEFIT_TYPES:
            honored.append(ent)
            effect = Effect(
                type="grant_access",
                payload=dict(ent.benefit_payload),
                persist_as_entitlement=False,
                benefit_type=ent.benefit_type,
                source_rule_id=ent.source_rule_id,
            )
            entitlement_effects.append(effect)
            trace.entitlements_honored.append(
                {
                    **ent.to_dict(),
                    "reason": "entitlement_honored",
                }
            )

    context = dict(facts)
    context["as_of"] = clock.timestamp()
    context["as_of_iso"] = clock.isoformat()

    decision_obj = _ENGINE.create_decision(json.dumps(pack.jdm()))
    zen_response = decision_obj.evaluate(context, {"trace": True})

    if isinstance(zen_response, dict):
        zen_result = zen_response
    else:
        # Some bindings return objects with dict-like access.
        zen_result = dict(zen_response)

    matches = _extract_matches(zen_result)
    matched_effects: list[Effect] = []
    for row in matches:
        effect = _match_to_effect(row)
        if effect is not None:
            matched_effects.append(effect)

    zen_trace = zen_result.get("trace")
    if isinstance(zen_trace, dict):
        trace.zen_trace = zen_trace
    perf = zen_result.get("performance")
    if perf is not None:
        trace.zen_performance = str(perf)

    trace.entries = _trace_from_zen(
        zen_trace if isinstance(zen_trace, dict) else None,
        matched_effects,
    )

    all_effects = entitlement_effects + matched_effects
    entitlements_to_create = [e for e in matched_effects if e.persist_as_entitlement]

    if honored and matched_effects:
        trace.path = "mixed"
    elif honored:
        trace.path = "entitlement"
    else:
        trace.path = "rules"

    decision = _resolve_decision(all_effects)

    return DecisionResult(
        decision=decision,
        effects=all_effects,
        entitlements_applied=honored,
        entitlements_to_create=entitlements_to_create,
        trace=trace,
        pack_version=pack.version,
    )
