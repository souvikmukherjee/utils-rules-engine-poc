from rules_api.kogito_client import (
    _effects_from_kogito,
    evaluate_via_kogito,
    facts_to_kogito_context,
)


def test_facts_to_kogito_context():
    ctx = facts_to_kogito_context(
        {
            "membership": {"tier": "gold", "companion_eligible": True},
            "partner": {"elite_tier": "platinum"},
        },
        as_of="2026-01-02T12:00:00Z",
    )
    assert ctx["MembershipTier"] == "gold"
    assert ctx["PartnerEliteTier"] == "platinum"
    assert ctx["CompanionEligible"] is True
    assert ctx["AsOf"] == "2026-01-02"


def test_effects_allow_and_companion():
    effects, entries = _effects_from_kogito(
        {
            "Eligibility": "allow",
            "LoungeClass": "domestic",
            "MatchedRule": "tier-gold-lounge",
            "CompanionsAllowed": 1,
        }
    )
    assert any(e.type == "allow" for e in effects)
    assert any(e.benefit_type == "lounge_access" for e in effects)
    assert any(e.benefit_type == "companion_pass" for e in effects)
    assert entries


def test_evaluate_via_kogito_mocked(monkeypatch):
    from rules_api import kogito_client

    monkeypatch.setattr(
        kogito_client,
        "call_lounge_access",
        lambda context, timeout=10.0: {
            "Eligibility": "allow",
            "LoungeClass": "domestic",
            "MatchedRule": "tier-gold-lounge",
            "CompanionsAllowed": 0,
        },
    )
    result = evaluate_via_kogito({"membership": {"tier": "gold"}})
    assert result.decision == "allow"
    assert result.trace.engine == "kogito"
