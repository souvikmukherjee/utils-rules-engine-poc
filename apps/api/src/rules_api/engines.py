"""Engine dispatch: Zen (GoRules) vs Kogito (Red Hat / Apache KIE DMN).

Packs are authored as JDM in the shared UI. When the toggle is Kogito,
runtime evaluation is redirected to the Quarkus DMN service in apps/kogito.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from rules_engine import (
    EntitlementSnapshot as ZenEntitlement,
)
from rules_engine import (
    RulePack as ZenRulePack,
)
from rules_engine import evaluate as zen_evaluate
from rules_engine import explain as zen_explain
from rules_engine import generate_test_cases as zen_testgen

EngineName = Literal["zen", "kogito"]
ENGINES: frozenset[str] = frozenset({"zen", "kogito"})


def normalize_engine(value: str | None) -> EngineName:
    if not value:
        return "zen"
    key = value.strip().lower()
    # Accept legacy typo from earlier PoC naming.
    if key == "cogito":
        key = "kogito"
    if key not in ENGINES:
        raise ValueError(f"Unknown engine '{value}'; expected zen or kogito")
    return key  # type: ignore[return-value]


def evaluate_with_engine(
    engine: EngineName,
    pack: ZenRulePack,
    facts: dict[str, Any],
    *,
    as_of: datetime | str | None,
    entitlements: list[ZenEntitlement],
) -> Any:
    if engine == "zen":
        return zen_evaluate(pack, facts, as_of=as_of, entitlements=entitlements)

    from rules_api.kogito_client import evaluate_via_kogito

    return evaluate_via_kogito(
        facts,
        as_of=as_of,
        entitlements=entitlements,
        pack_version=pack.version,
    )


def explain_with_engine(
    engine: EngineName,
    pack: ZenRulePack,
    facts: dict[str, Any],
    *,
    as_of: datetime | str | None,
    entitlements: list[ZenEntitlement],
) -> dict[str, Any]:
    result = evaluate_with_engine(
        engine, pack, facts, as_of=as_of, entitlements=entitlements
    )
    if engine == "zen":
        body = zen_explain(result)
    else:
        from rules_api.kogito_client import explain_kogito

        body = explain_kogito(result)
    body["engine"] = engine
    return body


def testgen_with_engine(
    engine: EngineName,
    pack: ZenRulePack,
    *,
    max_cases: int | None,
) -> dict[str, Any]:
    if engine == "zen":
        body = zen_testgen(pack, max_cases=max_cases)
    else:
        # Kogito DMN is seeded separately; emit a small fixed fixture set that
        # exercises the lounge decision table.
        limit = 50 if max_cases is None else max(1, min(int(max_cases), 500))
        cases = [
            {
                "subject_id": "case-0001",
                "facts": {"membership": {"tier": "gold"}},
                "label": "gold_tier",
            },
            {
                "subject_id": "case-0002",
                "facts": {"membership": {"tier": "silver"}},
                "label": "silver_no_access",
            },
            {
                "subject_id": "case-0003",
                "facts": {
                    "membership": {"tier": "silver"},
                    "partner": {"airline": "Qantas", "elite_tier": "gold"},
                },
                "label": "partner_elite",
            },
            {
                "subject_id": "case-0004",
                "facts": {"membership": {"tier": "silver"}},
                "as_of": "2099-06-15T00:00:00Z",
                "label": "seasonal_deny",
            },
            {
                "subject_id": "case-0005",
                "facts": {
                    "membership": {"tier": "bronze", "companion_eligible": True}
                },
                "label": "companion_flag",
            },
        ][:limit]
        body = {
            "domain": pack.domain,
            "pack_id": pack.pack_id,
            "version": pack.version,
            "max_cases": limit,
            "hard_max_cases": 500,
            "paths": ["membership.tier", "partner.elite_tier"],
            "truncated": False,
            "case_count": len(cases),
            "cases": cases,
        }
    body["engine"] = engine
    return body
