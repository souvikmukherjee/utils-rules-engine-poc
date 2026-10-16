from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from rules_engine.conditions import eval_condition
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


def evaluate(
    pack: RulePack,
    facts: dict[str, Any],
    *,
    as_of: datetime | str | None = None,
    entitlements: list[EntitlementSnapshot] | None = None,
) -> DecisionResult:
    """Evaluate facts against a rule pack with temporal filtering and entitlement honor.

    Conflict policy: collect matching effects; deny-wins.
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
            )
            entitlement_effects.append(effect)
            trace.entitlements_honored.append(
                {
                    **ent.to_dict(),
                    "reason": "entitlement_honored",
                }
            )

    matched_effects: list[Effect] = []

    for rule in pack.rules:
        if not rule.enabled:
            trace.entries.append(
                RuleTraceEntry(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    status="skipped",
                    reason="disabled",
                )
            )
            continue

        if not rule.in_window(clock):
            trace.entries.append(
                RuleTraceEntry(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    status="skipped",
                    reason="outside_effective_window",
                )
            )
            continue

        if not eval_condition(rule.condition, facts):
            trace.entries.append(
                RuleTraceEntry(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    status="condition_false",
                    reason="condition_not_met",
                )
            )
            continue

        effects = list(rule.effects)
        matched_effects.extend(effects)
        trace.entries.append(
            RuleTraceEntry(
                rule_id=rule.id,
                rule_name=rule.name,
                status="matched",
                reason="condition_met",
                effects=[e.to_dict() for e in effects],
            )
        )

    # Entitlement path can short-circuit eligibility when it already grants access,
    # but we still evaluate rules so the trace shows what would have fired (mixed).
    all_effects = entitlement_effects + matched_effects
    entitlements_to_create = [
        e for e in matched_effects if e.persist_as_entitlement
    ]

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
