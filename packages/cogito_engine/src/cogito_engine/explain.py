from __future__ import annotations

from typing import Any

from cogito_engine.models import DecisionResult, DecisionTrace, RuleTraceEntry


def _entry_reason(entry: RuleTraceEntry) -> str:
    if entry.status == "matched":
        effect_types = [e.get("type") for e in entry.effects]
        effects_txt = ", ".join(str(t) for t in effect_types) or "no effects"
        return f"Rule '{entry.rule_name}' ({entry.rule_id}) matched and applied: {effects_txt}."
    if entry.status == "skipped":
        detail = entry.reason or "skipped"
        if detail == "outside_effective_window":
            return (
                f"Rule '{entry.rule_name}' ({entry.rule_id}) was skipped because "
                "it is outside its effective time window."
            )
        if detail == "disabled":
            return f"Rule '{entry.rule_name}' ({entry.rule_id}) was skipped because it is disabled."
        return f"Rule '{entry.rule_name}' ({entry.rule_id}) was skipped ({detail})."
    if entry.status == "condition_false":
        return (
            f"Rule '{entry.rule_name}' ({entry.rule_id}) did not match: "
            "its condition was not met."
        )
    return f"Rule '{entry.rule_name}' ({entry.rule_id}): {entry.status}."


def explain_trace(trace: DecisionTrace) -> list[str]:
    reasons: list[str] = []
    for ent in trace.entitlements_honored:
        eid = ent.get("entitlement_id", "?")
        btype = ent.get("benefit_type", "benefit")
        gf = " (grandfathered)" if ent.get("grandfathered") else ""
        reasons.append(f"Honored entitlement {eid}: {btype}{gf}.")
    for entry in trace.entries:
        reasons.append(_entry_reason(entry))
    return reasons


def explain(result: DecisionResult) -> dict[str, Any]:
    """Build a human-readable explanation from an evaluation DecisionResult."""
    reasons = explain_trace(result.trace)
    path = result.trace.path
    if result.decision == "deny":
        summary = (
            "Decision is deny (deny-wins conflict policy): at least one deny effect "
            "was present among matched rules or entitlements."
        )
    elif result.decision == "allow":
        if path == "entitlement":
            summary = "Decision is allow based on honored entitlements."
        elif path == "mixed":
            summary = "Decision is allow from a mix of entitlements and matching rules."
        else:
            summary = "Decision is allow based on matching rule effects."
    else:
        summary = (
            "Decision is inconclusive: no allow/deny/grant effects matched "
            "and no covering entitlement was honored."
        )

    return {
        "decision": result.decision,
        "summary": summary,
        "reasons": reasons,
        "path": path,
        "pack_version": result.pack_version,
        "effects": [e.to_dict() for e in result.effects],
        "entitlements_applied": [e.to_dict() for e in result.entitlements_applied],
        "trace": result.trace.to_dict(),
    }
