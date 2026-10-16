"""Build the complex lounge-access JDM from the tier × cabin matrix."""

from __future__ import annotations

from typing import Any

# Keep in sync with rules_api.catalog.LOUNGE_MATRIX (samples must stay dependency-light).
LOUNGE_MATRIX: dict[tuple[str, str], str | None] = {
    ("bronze", "economy"): None,
    ("bronze", "premium_economy"): None,
    ("bronze", "business"): "qantas_club",
    ("bronze", "first"): "first",
    ("silver", "economy"): None,
    ("silver", "premium_economy"): "qantas_club",
    ("silver", "business"): "business",
    ("silver", "first"): "first",
    ("gold", "economy"): "qantas_club",
    ("gold", "premium_economy"): "qantas_club",
    ("gold", "business"): "business",
    ("gold", "first"): "first",
    ("platinum", "economy"): "business",
    ("platinum", "premium_economy"): "business",
    ("platinum", "business"): "first",
    ("platinum", "first"): "first",
    ("platinum_one", "economy"): "chairmans",
    ("platinum_one", "premium_economy"): "chairmans",
    ("platinum_one", "business"): "chairmans",
    ("platinum_one", "first"): "chairmans",
}

LOUNGE_LABEL = {
    "chairmans": "Chairman's Lounge",
    "first": "First Lounge",
    "business": "Business Lounge",
    "qantas_club": "Qantas Club",
}


def _matrix_rules() -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    # Eligible cells first (collect will gather all; deny-wins later for seasonal).
    for (tier, cabin), lounge in LOUNGE_MATRIX.items():
        if lounge is None:
            continue
        rid = f"{tier}-{cabin}-{lounge}"
        rules.append(
            {
                "_id": rid,
                "i1": f"'{tier}'",
                "i2": f"'{cabin}'",
                "i3": "",
                "i4": "",
                "i5": "",
                "o1": "\"allow\"",
                "o2": "\"grant_access\"",
                "o3": f"\"{lounge}\"",
                "o4": f"\"{LOUNGE_LABEL[lounge]}\"",
                "o5": "\"lounge_access\"",
                "o6": "true",
                "o7": f"\"matrix:{tier}+{cabin}\"",
                "o8": f"\"{rid}\"",
                "o9": "null",
            }
        )
    # Ineligible cells intentionally omit rows → inconclusive (no deny-wins clash
    # with partner-elite overlays).
    # Partner elite overlay — gold+ partner elite lifts lower-tier members to Club.
    rules.append(
        {
            "_id": "partner-elite-club",
            "i1": "",
            "i2": "",
            "i3": "'gold', 'platinum', 'first'",
            "i4": "",
            "i5": "",
            "o1": "\"allow\"",
            "o2": "\"grant_access\"",
            "o3": "\"qantas_club\"",
            "o4": "\"Qantas Club\"",
            "o5": "\"lounge_access\"",
            "o6": "true",
            "o7": "\"partner_elite\"",
            "o8": "\"partner-elite-club\"",
            "o9": "\"partner\"",
        }
    )
    # Platinum One companion pass
    rules.append(
        {
            "_id": "platinum-one-companion",
            "i1": "'platinum_one'",
            "i2": "",
            "i3": "",
            "i4": "",
            "i5": "",
            "o1": "\"allow\"",
            "o2": "\"grant_access\"",
            "o3": "null",
            "o4": "null",
            "o5": "\"companion_pass\"",
            "o6": "true",
            "o7": "\"companion\"",
            "o8": "\"platinum-one-companion\"",
            "o9": "null",
        }
    )
    # Seasonal peak: Bronze/Silver economy denied hard during peak (future window).
    rules.append(
        {
            "_id": "seasonal-peak-deny-low-tier",
            "i1": "'bronze', 'silver'",
            "i2": "'economy'",
            "i3": "",
            "i4": ">= date('2099-01-01') and < date('2100-01-01')",
            "i5": "",
            "o1": "\"deny\"",
            "o2": "\"deny\"",
            "o3": "null",
            "o4": "null",
            "o5": "null",
            "o6": "false",
            "o7": "\"peak_season_restriction\"",
            "o8": "\"seasonal-peak-deny-low-tier\"",
            "o9": "null",
        }
    )
    return rules


def build_lounge_pack(
    *,
    domain: str = "lounge",
    pack_id: str = "lounge-access",
    version: str = "2.0.0",
    lifecycle: str = "published",
) -> dict[str, Any]:
    return {
        "domain": domain,
        "pack_id": pack_id,
        "version": version,
        "lifecycle": lifecycle,
        "nodes": [
            {
                "id": "input",
                "type": "inputNode",
                "name": "Request",
                "position": {"x": 60, "y": 240},
                "content": {"schema": ""},
            },
            {
                "id": "normalize",
                "type": "expressionNode",
                "name": "Normalize facts",
                "position": {"x": 280, "y": 240},
                "content": {
                    "expressions": [
                        {
                            "id": "e1",
                            "key": "tier",
                            "value": "membership.tier",
                        },
                        {
                            "id": "e2",
                            "key": "cabin",
                            "value": "booking.cabin != null ? booking.cabin : 'economy'",
                        },
                        {
                            "id": "e3",
                            "key": "partner_elite",
                            "value": "partner.elite_tier",
                        },
                        {
                            "id": "e4",
                            "key": "as_of",
                            "value": "as_of",
                        },
                        {
                            "id": "e5",
                            "key": "international",
                            "value": "booking.international == true",
                        },
                    ],
                    "passThrough": True,
                },
            },
            {
                "id": "eligibility",
                "type": "decisionTableNode",
                "name": "Lounge decision framework",
                "position": {"x": 560, "y": 240},
                "content": {
                    "hitPolicy": "collect",
                    "inputs": [
                        {"id": "i1", "name": "Tier", "field": "tier"},
                        {"id": "i2", "name": "Cabin", "field": "cabin"},
                        {"id": "i3", "name": "Partner elite", "field": "partner_elite"},
                        {"id": "i4", "name": "As of", "field": "as_of"},
                        {"id": "i5", "name": "International", "field": "international"},
                    ],
                    "outputs": [
                        {"id": "o1", "name": "Decision", "field": "decision"},
                        {"id": "o2", "name": "Effect type", "field": "effect_type"},
                        {"id": "o3", "name": "Lounge type", "field": "lounge_type"},
                        {"id": "o4", "name": "Lounge label", "field": "lounge_label"},
                        {"id": "o5", "name": "Benefit type", "field": "benefit_type"},
                        {"id": "o6", "name": "Persist", "field": "persist_as_entitlement"},
                        {"id": "o7", "name": "Reason", "field": "reason"},
                        {"id": "o8", "name": "Rule id", "field": "rule_id"},
                        {"id": "o9", "name": "Via", "field": "via"},
                    ],
                    "rules": _matrix_rules(),
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
                "position": {"x": 900, "y": 240},
                "content": {"schema": ""},
            },
        ],
        "edges": [
            {
                "id": "e-input-normalize",
                "sourceId": "input",
                "type": "edge",
                "targetId": "normalize",
            },
            {
                "id": "e-normalize-eligibility",
                "sourceId": "normalize",
                "type": "edge",
                "targetId": "eligibility",
            },
            {
                "id": "e-eligibility-output",
                "sourceId": "eligibility",
                "type": "edge",
                "targetId": "output",
            },
        ],
    }
