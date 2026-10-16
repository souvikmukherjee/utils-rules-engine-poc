from datetime import datetime, timezone

from rules_engine.evaluate import evaluate
from rules_engine.explain import explain
from rules_engine.models import EntitlementSnapshot, RulePack
from rules_engine.samples import load_lounge_pack
from rules_engine.testgen import HARD_MAX_CASES, generate_test_cases


def test_gold_tier_allows():
    pack = load_lounge_pack()
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    assert result.decision == "allow"
    assert any(
        e.status == "matched" and e.rule_id == "tier-gold-lounge" for e in result.trace.entries
    )


def test_silver_inconclusive_outside_season():
    pack = load_lounge_pack()
    result = evaluate(
        pack,
        {"membership": {"tier": "silver"}},
        as_of=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert result.decision == "inconclusive"
    assert not any(e.status == "matched" for e in result.trace.entries)


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
            "nodes": [
                {
                    "id": "input",
                    "type": "inputNode",
                    "name": "Request",
                    "position": {"x": 0, "y": 0},
                    "content": {"schema": ""},
                },
                {
                    "id": "table",
                    "type": "decisionTableNode",
                    "name": "T",
                    "position": {"x": 200, "y": 0},
                    "content": {
                        "hitPolicy": "collect",
                        "inputs": [{"id": "i1", "name": "X", "field": "x"}],
                        "outputs": [
                            {"id": "o1", "name": "Decision", "field": "decision"},
                            {"id": "o2", "name": "Effect", "field": "effect_type"},
                            {"id": "o3", "name": "Rule", "field": "rule_id"},
                        ],
                        "rules": [
                            {
                                "_id": "a",
                                "i1": "1",
                                "o1": "\"allow\"",
                                "o2": "\"allow\"",
                                "o3": "\"allow-all\"",
                            },
                            {
                                "_id": "d",
                                "i1": "1",
                                "o1": "\"deny\"",
                                "o2": "\"deny\"",
                                "o3": "\"deny-all\"",
                            },
                        ],
                        "passThrough": False,
                        "inputField": None,
                        "outputPath": "matches",
                        "executionMode": "single",
                    },
                },
                {
                    "id": "output",
                    "type": "outputNode",
                    "name": "Response",
                    "position": {"x": 400, "y": 0},
                    "content": {"schema": ""},
                },
            ],
            "edges": [
                {"id": "e1", "sourceId": "input", "type": "edge", "targetId": "table"},
                {"id": "e2", "sourceId": "table", "type": "edge", "targetId": "output"},
            ],
        }
    )
    result = evaluate(pack, {"x": 1})
    assert result.decision == "deny"
    matched = [e for e in result.trace.entries if e.status == "matched"]
    assert len(matched) >= 2


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
    assert any(
        e.status == "matched" and e.rule_id == "tier-gold-lounge" for e in result.trace.entries
    )


def test_explain_human_readable():
    pack = load_lounge_pack()
    result = evaluate(pack, {"membership": {"tier": "gold"}})
    explained = explain(result)
    assert explained["decision"] == "allow"
    assert explained["summary"]
    assert any("tier-gold-lounge" in r or "Gold" in r for r in explained["reasons"])
    assert "trace" in explained
    assert explained["trace"].get("zen_trace") is not None


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
