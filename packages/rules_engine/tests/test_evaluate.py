from datetime import datetime, timezone

from rules_engine.evaluate import evaluate
from rules_engine.explain import explain
from rules_engine.models import EntitlementSnapshot, RulePack
from rules_engine.samples import load_banking_pack, load_lounge_pack
from rules_engine.testgen import HARD_MAX_CASES, generate_test_cases


def test_gold_economy_opens_qantas_club():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "gold"}, "booking": {"cabin": "economy"}},
    )
    assert result.decision == "allow"
    lounge_types = [e.payload.get("lounge_type") for e in result.effects]
    assert "qantas_club" in lounge_types
    assert any(
        e.status == "matched" and "gold-economy" in e.rule_id for e in result.trace.entries
    )


def test_bronze_first_cabin_opens_first_lounge():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "bronze"}, "booking": {"cabin": "first"}},
    )
    assert result.decision == "allow"
    assert any(e.payload.get("lounge_type") == "first" for e in result.effects)


def test_platinum_economy_opens_business_lounge():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "platinum"}, "booking": {"cabin": "economy"}},
    )
    assert result.decision == "allow"
    assert any(e.payload.get("lounge_type") == "business" for e in result.effects)


def test_platinum_one_always_chairmans():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "platinum_one"}, "booking": {"cabin": "economy"}},
    )
    assert result.decision == "allow"
    assert any(e.payload.get("lounge_type") == "chairmans" for e in result.effects)
    assert any(e.benefit_type == "companion_pass" for e in result.effects)


def test_bronze_economy_inconclusive():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "bronze"}, "booking": {"cabin": "economy"}},
        as_of=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert result.decision == "inconclusive"


def test_seasonal_deny_low_tier_economy():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}, "booking": {"cabin": "economy"}},
        as_of=datetime(2099, 6, 15, tzinfo=timezone.utc),
    )
    seasonal = next(
        e for e in result.trace.entries if e.rule_id == "seasonal-peak-deny-low-tier"
    )
    assert seasonal.status == "matched"
    assert result.decision == "deny"


def test_banking_prime_rate():
    pack = load_banking_pack()
    result = evaluate(
        pack,
        {
            "loan": {"lvr": 0.7, "product": "owner_occupier"},
            "applicant": {"credit_score": 790},
        },
    )
    assert result.decision == "allow"
    assert any(e.payload.get("pricing_band") == "prime" for e in result.effects)


def test_pack_requires_jdm():
    try:
        RulePack.from_dict(
            {
                "domain": "test",
                "pack_id": "legacy",
                "version": "1.0.0",
                "lifecycle": "draft",
                "rules": [],
            }
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "nodes" in str(exc).lower() or "jdm" in str(exc).lower()


def test_grandfathered_entitlement_honored():
    pack = load_lounge_pack()
    ent = EntitlementSnapshot(
        entitlement_id="ent-1",
        benefit_type="companion_pass",
        benefit_payload={"companions_allowed": 1},
        grandfathered=True,
        source_rule_id="legacy-companion",
        source_pack_version="0.9.0",
    )
    result = evaluate(
        pack,
        {"membership": {"tier": "bronze"}, "booking": {"cabin": "economy"}},
        entitlements=[ent],
    )
    assert result.decision == "allow"
    assert result.trace.path in {"entitlement", "mixed"}
    assert result.entitlements_applied[0].entitlement_id == "ent-1"


def test_explain_human_readable():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "gold"}, "booking": {"cabin": "business"}},
    )
    explained = explain(result)
    assert explained["decision"] == "allow"
    assert explained["summary"]
    assert explained["reasons"]
    assert explained["trace"].get("zen_trace") is not None


def test_testgen_deterministic_and_bounded():
    pack = load_lounge_pack()
    first = generate_test_cases(pack, max_cases=20)
    second = generate_test_cases(pack, max_cases=20)
    assert first["cases"] == second["cases"]
    assert first["case_count"] <= 20
    assert first["hard_max_cases"] == HARD_MAX_CASES
    assert first["paths"]
