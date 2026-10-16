from datetime import datetime, timezone

from cogito_engine.evaluate import evaluate
from cogito_engine.explain import explain
from cogito_engine.jdm_bridge import jdm_to_cogito_pack
from cogito_engine.models import EntitlementSnapshot, RulePack
from cogito_engine.samples import load_lounge_pack
from cogito_engine.testgen import HARD_MAX_CASES, generate_test_cases
from rules_engine.samples import load_lounge_pack as load_jdm_lounge_pack


def test_gold_tier_allows():
    pack = load_lounge_pack()
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    assert result.decision == "allow"
    assert any(
        e.status == "matched" and e.rule_id == "tier-gold-lounge"
        for e in result.trace.entries
    )
    assert result.trace.engine == "cogito"


def test_future_rule_skipped_outside_window():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}},
        as_of=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    seasonal = next(
        e for e in result.trace.entries if e.rule_id == "seasonal-peak-deny-silver"
    )
    assert seasonal.status == "skipped"
    assert seasonal.reason == "outside_effective_window"
    assert result.decision == "inconclusive"


def test_seasonal_deny_wins_when_in_window():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}},
        as_of=datetime(2099, 6, 15, tzinfo=timezone.utc),
    )
    seasonal = next(
        e for e in result.trace.entries if e.rule_id == "seasonal-peak-deny-silver"
    )
    assert seasonal.status == "matched"
    assert result.decision == "deny"


def test_deny_wins_over_allow():
    pack = RulePack.from_dict(
        {
            "domain": "test",
            "pack_id": "deny-wins",
            "version": "1.0.0",
            "lifecycle": "published",
            "rules": [
                {
                    "id": "allow-all",
                    "name": "Allow",
                    "priority": 10,
                    "enabled": True,
                    "effective_from": "2020-01-01T00:00:00Z",
                    "effective_to": None,
                    "condition": {"path": "x", "op": "eq", "value": 1},
                    "effects": [{"type": "allow", "payload": {}}],
                },
                {
                    "id": "deny-all",
                    "name": "Deny",
                    "priority": 5,
                    "enabled": True,
                    "effective_from": "2020-01-01T00:00:00Z",
                    "effective_to": None,
                    "condition": {"path": "x", "op": "eq", "value": 1},
                    "effects": [{"type": "deny", "payload": {"reason": "blocked"}}],
                },
            ],
        }
    )
    result = evaluate(pack, {"x": 1})
    assert result.decision == "deny"
    matched = [e for e in result.trace.entries if e.status == "matched"]
    assert len(matched) == 2


def test_entitlement_honored():
    pack = load_lounge_pack()
    ents = [
        EntitlementSnapshot(
            entitlement_id="e1",
            benefit_type="lounge_access",
            benefit_payload={"lounge_class": "domestic"},
            grandfathered=True,
        )
    ]
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}},
        entitlements=ents,
    )
    assert result.decision == "allow"
    assert result.trace.path in {"entitlement", "mixed"}


def test_testgen_bounds():
    pack = load_lounge_pack()
    body = generate_test_cases(pack, max_cases=5)
    assert body["case_count"] <= 5
    assert body["hard_max_cases"] == HARD_MAX_CASES


def test_explain_shape():
    pack = load_lounge_pack()
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    body = explain(result)
    assert body["decision"] == "allow"
    assert body["reasons"]


def test_jdm_bridge_matches_native_gold():
    jdm = load_jdm_lounge_pack().to_dict()
    pack = jdm_to_cogito_pack(jdm)
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    assert result.decision == "allow"
    assert any(e.status == "matched" for e in result.trace.entries)


def test_jdm_bridge_seasonal_deny():
    jdm = load_jdm_lounge_pack().to_dict()
    pack = jdm_to_cogito_pack(jdm)
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}},
        as_of=datetime(2099, 6, 15, tzinfo=timezone.utc),
    )
    assert result.decision == "deny"
    assert any(
        e.rule_id == "seasonal-peak-deny-silver" and e.status == "matched"
        for e in result.trace.entries
    )
