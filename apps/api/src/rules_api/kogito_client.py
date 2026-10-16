"""HTTP client for the parallel Kogito (DMN) lounge service."""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import httpx

from rules_engine.models import (
    DecisionResult,
    DecisionTrace,
    Effect,
    EntitlementSnapshot,
    RuleTraceEntry,
    parse_dt,
)

DEFAULT_KOGITO_URL = "http://127.0.0.1:8081"
ACCESS_BENEFIT_TYPES = frozenset({"lounge_access", "companion_pass", "one_off_access"})


def kogito_base_url() -> str:
    return (os.environ.get("KOGITO_URL") or DEFAULT_KOGITO_URL).rstrip("/")


def _as_of_date(as_of: datetime | str | None) -> str:
    if as_of is None:
        return date.today().isoformat()
    if isinstance(as_of, datetime):
        return as_of.date().isoformat()
    parsed = parse_dt(as_of)
    if parsed is None:
        return str(as_of)[:10]
    return parsed.date().isoformat()


def _normalize_clock(as_of: datetime | str | None) -> datetime:
    if as_of is None:
        return datetime.now().astimezone()
    parsed = parse_dt(as_of)
    assert parsed is not None
    return parsed


def facts_to_kogito_context(facts: dict[str, Any], *, as_of: datetime | str | None) -> dict[str, Any]:
    membership = facts.get("membership") if isinstance(facts.get("membership"), dict) else {}
    partner = facts.get("partner") if isinstance(facts.get("partner"), dict) else {}
    return {
        "MembershipTier": membership.get("tier"),
        "PartnerEliteTier": partner.get("elite_tier"),
        "CompanionEligible": bool(membership.get("companion_eligible", False)),
        "AsOf": _as_of_date(as_of),
    }


def _resolve_decision(effects: list[Effect]) -> str:
    types = {e.type for e in effects}
    if "deny" in types:
        return "deny"
    if "allow" in types or "grant_access" in types:
        return "allow"
    if types:
        return "allow"
    return "inconclusive"


def _effects_from_kogito(body: dict[str, Any]) -> tuple[list[Effect], list[RuleTraceEntry]]:
    eligibility = body.get("Eligibility")
    lounge_class = body.get("LoungeClass")
    companions = body.get("CompanionsAllowed") or 0
    rule_id = str(body.get("MatchedRule") or "kogito")
    effects: list[Effect] = []
    entries: list[RuleTraceEntry] = []

    if eligibility == "deny":
        effect = Effect(
            type="deny",
            payload={"reason": "peak_season_restriction"},
            source_rule_id=rule_id,
        )
        effects.append(effect)
        entries.append(
            RuleTraceEntry(
                rule_id=rule_id,
                rule_name=rule_id,
                status="matched",
                reason="kogito_dmn_match",
                effects=[effect.to_dict()],
            )
        )
        return effects, entries

    if eligibility == "allow":
        allow = Effect(
            type="allow",
            payload={"lounge_class": lounge_class} if lounge_class else {},
            source_rule_id=rule_id,
        )
        grant = Effect(
            type="grant_access",
            payload={"lounge_class": lounge_class} if lounge_class else {},
            persist_as_entitlement=True,
            benefit_type="lounge_access",
            source_rule_id=rule_id,
        )
        effects.extend([allow, grant])
        entries.append(
            RuleTraceEntry(
                rule_id=rule_id,
                rule_name=rule_id,
                status="matched",
                reason="kogito_dmn_match",
                effects=[allow.to_dict(), grant.to_dict()],
            )
        )

    if companions and int(companions) > 0:
        companion = Effect(
            type="grant_access",
            payload={"companions_allowed": int(companions)},
            persist_as_entitlement=True,
            benefit_type="companion_pass",
            source_rule_id="companion-plus-one",
        )
        effects.append(companion)
        entries.append(
            RuleTraceEntry(
                rule_id="companion-plus-one",
                rule_name="companion-plus-one",
                status="matched",
                reason="kogito_dmn_match",
                effects=[companion.to_dict()],
            )
        )

    if eligibility not in {"allow", "deny"} and not effects:
        entries.append(
            RuleTraceEntry(
                rule_id=rule_id,
                rule_name=rule_id,
                status="condition_false",
                reason="kogito_inconclusive",
            )
        )

    return effects, entries


def call_lounge_access(context: dict[str, Any], *, timeout: float = 10.0) -> dict[str, Any]:
    url = f"{kogito_base_url()}/LoungeAccess"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=context)
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Kogito unreachable at {url}. Start it with `make kogito` ({exc})"
        ) from exc
    if resp.status_code >= 400:
        raise RuntimeError(f"Kogito error {resp.status_code}: {resp.text}")
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected Kogito response shape")
    return data


def evaluate_via_kogito(
    facts: dict[str, Any],
    *,
    as_of: datetime | str | None = None,
    entitlements: list[EntitlementSnapshot] | None = None,
    pack_version: str = "1.0.0",
) -> DecisionResult:
    """Evaluate lounge facts through Kogito DMN, then apply platform entitlements."""
    clock = _normalize_clock(as_of)
    entitlements = list(entitlements or [])
    trace = DecisionTrace(as_of=clock, pack_version=pack_version, engine="kogito")

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
                {**ent.to_dict(), "reason": "entitlement_honored"}
            )

    context = facts_to_kogito_context(facts, as_of=clock)
    body = call_lounge_access(context)
    matched_effects, entries = _effects_from_kogito(body)
    trace.entries = entries
    trace.engine_detail = {"kogito_context": body}

    all_effects = entitlement_effects + matched_effects
    entitlements_to_create = [e for e in matched_effects if e.persist_as_entitlement]

    if honored and matched_effects:
        trace.path = "mixed"
    elif honored:
        trace.path = "entitlement"
    else:
        trace.path = "rules"

    return DecisionResult(
        decision=_resolve_decision(all_effects),
        effects=all_effects,
        entitlements_applied=honored,
        entitlements_to_create=entitlements_to_create,
        trace=trace,
        pack_version=pack_version,
    )


def explain_kogito(result: DecisionResult) -> dict[str, Any]:
    reasons: list[str] = []
    for ent in result.trace.entitlements_honored:
        reasons.append(
            f"Honored entitlement {ent.get('entitlement_id')}: {ent.get('benefit_type')}."
        )
    for entry in result.trace.entries:
        if entry.status == "matched":
            reasons.append(
                f"Kogito DMN matched '{entry.rule_id}' ({entry.reason})."
            )
        else:
            reasons.append(
                f"Kogito path '{entry.rule_id}': {entry.status} ({entry.reason})."
            )
    summary = f"Decision is {result.decision} via Kogito DMN (engine=kogito)."
    return {
        "decision": result.decision,
        "summary": summary,
        "reasons": reasons,
        "path": result.trace.path,
        "pack_version": result.pack_version,
        "effects": [e.to_dict() for e in result.effects],
        "entitlements_applied": [e.to_dict() for e in result.entitlements_applied],
        "trace": result.trace.to_dict(),
        "engine": "kogito",
    }
