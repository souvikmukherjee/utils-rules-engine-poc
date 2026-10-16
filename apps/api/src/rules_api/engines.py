"""Engine dispatch: Zen (GoRules) vs Cogito (native condition-IR).

Packs are authored as JDM in the shared UI. Cogito compiles decision tables
into condition-IR at evaluation time.
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

EngineName = Literal["zen", "cogito"]
ENGINES: frozenset[str] = frozenset({"zen", "cogito"})


def normalize_engine(value: str | None) -> EngineName:
    if not value:
        return "zen"
    key = value.strip().lower()
    if key not in ENGINES:
        raise ValueError(f"Unknown engine '{value}'; expected zen or cogito")
    return key  # type: ignore[return-value]


def _to_cogito_ents(
    entitlements: list[ZenEntitlement],
) -> list[Any]:
    from cogito_engine import EntitlementSnapshot as CogitoEnt

    return [
        CogitoEnt(
            entitlement_id=e.entitlement_id,
            benefit_type=e.benefit_type,
            benefit_payload=dict(e.benefit_payload),
            grandfathered=e.grandfathered,
            source_rule_id=e.source_rule_id,
            source_pack_version=e.source_pack_version,
        )
        for e in entitlements
    ]


def _from_cogito_result(result: Any) -> Any:
    """Adapt Cogito DecisionResult into the Zen-shaped objects the API already uses.

    The API only needs duck-typed attributes: decision, effects (with to_dict /
    persist_as_entitlement / benefit_type / payload / type), entitlements_*,
    trace (path, to_dict), pack_version.
    """
    return result


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

    from cogito_engine import evaluate as cogito_evaluate
    from cogito_engine import jdm_to_cogito_pack

    cogito_pack = jdm_to_cogito_pack(pack.to_dict())
    return _from_cogito_result(
        cogito_evaluate(
            cogito_pack,
            facts,
            as_of=as_of,
            entitlements=_to_cogito_ents(entitlements),
        )
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
        from cogito_engine import explain as cogito_explain

        body = cogito_explain(result)
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
        from cogito_engine import generate_test_cases as cogito_testgen
        from cogito_engine import jdm_to_cogito_pack

        body = cogito_testgen(jdm_to_cogito_pack(pack.to_dict()), max_cases=max_cases)
    body["engine"] = engine
    return body
