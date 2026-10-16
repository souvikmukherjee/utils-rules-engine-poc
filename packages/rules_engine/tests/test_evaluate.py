from datetime import datetime, timezone

from rules_engine.evaluate import evaluate
from rules_engine.explain import explain
from rules_engine.models import Effect, EntitlementSnapshot, Rule, RulePack
from rules_engine.samples import load_lounge_pack
from rules_engine.testgen import HARD_MAX_CASES, generate_test_cases


def test_gold_tier_allows():
    pack = load_lounge_pack()
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    assert result.decision == "allow"
    assert any(e.status == "matched" and e.rule_id == "tier-gold-lounge" for e in result.trace.entries)


def test_future_rule_skipped_outside_window():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}},
        as_of=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    seasonal = next(e for e in result.trace.entries if e.rule_id == "seasonal-peak-deny-silver")
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
    seasonal = next(e for e in result.trace.entries if e.rule_id == "seasonal-peak-deny-silver")
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


def test_priority_ordering_in_pack():
    pack = RulePack.from_dict(
        {
            "domain": "test",
            "pack_id": "prio",
            "version": "1.0.0",
            "lifecycle": "draft",
            "rules": [
                {
                    "id": "low",
                    "name": "Low",
                    "priority": 1,
                    "effective_from": "2020-01-01T00:00:00Z",
                    "condition": {"path": "a", "op": "eq", "value": 1},
                    "effects": [{"type": "allow"}],
                },
                {
                    "id": "high",
                    "name": "High",
                    "priority": 100,
                    "effective_from": "2020-01-01T00:00:00Z",
                    "condition": {"path": "a", "op": "eq", "value": 1},
                    "effects": [{"type": "allow"}],
                },
            ],
        }
    )
    assert [r.id for r in pack.rules] == ["high", "low"]


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
        {"membership": {"tier": "silver"}},
        entitlements=[ent],
    )
    assert result.decision == "allow"
    assert result.trace.path in {"entitlement", "mixed"}
    assert result.entitlements_applied[0].entitlement_id == "ent-1"


def test_entitlement_merge_with_matching_rules():
    pack = load_lounge_pack()
    ent = EntitlementSnapshot(
        entitlement_id="ent-access",
        benefit_type="lounge_access",
        benefit_payload={"lounge_class": "domestic"},
        grandfathered=True,
    )
    result = evaluate(
        pack,
        {"membership": {"tier": "gold"}},
        entitlements=[ent],
    )
    assert result.decision == "allow"
    assert result.trace.path == "mixed"
    assert any(e.entitlement_id == "ent-access" for e in result.entitlements_applied)
    assert any(e.status == "matched" and e.rule_id == "tier-gold-lounge" for e in result.trace.entries)


def test_explain_human_readable():
    pack = load_lounge_pack()
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    explained = explain(result)
    assert explained["decision"] == "allow"
    assert explained["summary"]
    assert any("tier-gold-lounge" in r or "Gold tier" in r for r in explained["reasons"])
    assert "trace" in explained


def test_testgen_deterministic_and_bounded():
    pack = load_lounge_pack()
    first = generate_test_cases(pack, max_cases=20)
    second = generate_test_cases(pack, max_cases=20)
    assert first["cases"] == second["cases"]
    assert first["case_count"] <= 20
    assert first["hard_max_cases"] == HARD_MAX_CASES
    assert first["paths"]

    capped = generate_test_cases(pack, max_cases=9999)
    assert capped["max_cases"] == HARD_MAX_CASES
    assert capped["case_count"] <= HARD_MAX_CASES
