"""Product catalog: domains, packs, personas, and the lounge decision framework.

This is intentional product fiction for the PoC — airline + banking examples of the
same Axiom platform.
"""

from __future__ import annotations

from typing import Any

# Lounge product fiction — mirrors a Qantas-style access matrix.
LOUNGE_TYPES = (
    {"id": "chairmans", "label": "Chairman's Lounge", "rank": 4},
    {"id": "first", "label": "First Lounge", "rank": 3},
    {"id": "business", "label": "Business Lounge", "rank": 2},
    {"id": "qantas_club", "label": "Qantas Club", "rank": 1},
)

MEMBERSHIP_TIERS = (
    {"id": "bronze", "label": "Bronze", "rank": 1},
    {"id": "silver", "label": "Silver", "rank": 2},
    {"id": "gold", "label": "Gold", "rank": 3},
    {"id": "platinum", "label": "Platinum", "rank": 4},
    {"id": "platinum_one", "label": "Platinum One", "rank": 5},
)

TRAVEL_CLASSES = (
    {"id": "economy", "label": "Economy", "rank": 1},
    {"id": "premium_economy", "label": "Premium Economy", "rank": 2},
    {"id": "business", "label": "Business", "rank": 3},
    {"id": "first", "label": "First", "rank": 4},
)

# Highest lounge earned for (tier, cabin). None = ineligible.
# Cabin can unlock above-tier access (Bronze in First → First Lounge).
# Tier can unlock above-cabin access (Platinum in Economy → Business Lounge).
LOUNGE_MATRIX: dict[tuple[str, str], str | None] = {
    # Bronze — cabin-led: First cabin opens First; Business opens Club only.
    ("bronze", "economy"): None,
    ("bronze", "premium_economy"): None,
    ("bronze", "business"): "qantas_club",
    ("bronze", "first"): "first",
    # Silver — PE opens Club; Business opens Business; First opens First.
    ("silver", "economy"): None,
    ("silver", "premium_economy"): "qantas_club",
    ("silver", "business"): "business",
    ("silver", "first"): "first",
    # Gold — economy+ opens Club; Business/First step up.
    ("gold", "economy"): "qantas_club",
    ("gold", "premium_economy"): "qantas_club",
    ("gold", "business"): "business",
    ("gold", "first"): "first",
    # Platinum — economy already Business; First cabin → First lounge.
    ("platinum", "economy"): "business",
    ("platinum", "premium_economy"): "business",
    ("platinum", "business"): "first",
    ("platinum", "first"): "first",
    # Platinum One — Chairman's for every cabin.
    ("platinum_one", "economy"): "chairmans",
    ("platinum_one", "premium_economy"): "chairmans",
    ("platinum_one", "business"): "chairmans",
    ("platinum_one", "first"): "chairmans",
}

DOMAINS: list[dict[str, Any]] = [
    {
        "id": "loyalty",
        "name": "Loyalty",
        "industry": "airline",
        "blurb": "Status credits, tier reviews, partner elite matching.",
        "pack_id": "loyalty-tier-review",
        "accent": "#0f6b5c",
    },
    {
        "id": "lounge",
        "name": "Lounge access",
        "industry": "airline",
        "blurb": "Tier × cabin × lounge type decision framework (Chairman's → Club).",
        "pack_id": "lounge-access",
        "accent": "#c45c26",
        "framework": "lounge_matrix",
    },
    {
        "id": "airline_operations",
        "name": "Airline operations",
        "industry": "airline",
        "blurb": "IRROPS rebooking priority, disruption vouchers, gate overrides.",
        "pack_id": "ops-irrops-priority",
        "accent": "#1d4e89",
    },
    {
        "id": "airports",
        "name": "Airports",
        "industry": "airline",
        "blurb": "Terminal access windows, landside/airside offers, security lanes.",
        "pack_id": "airport-terminal-access",
        "accent": "#5b4b8a",
    },
    {
        "id": "banking_credit",
        "name": "Banking · credit",
        "industry": "banking",
        "blurb": "Home-loan pricing bands by LVR, score, and product — same engine.",
        "pack_id": "home-loan-pricing",
        "accent": "#0a4a40",
    },
]

PERSONAS: list[dict[str, Any]] = [
    {
        "id": "maya-loyalty-author",
        "name": "Maya Chen",
        "title": "Loyalty rules author",
        "role": "author",
        "domains": ["loyalty", "lounge"],
        "bio": "Owns status-credit formulas and lounge entitlement drafts for the FF program.",
    },
    {
        "id": "james-ops-approver",
        "name": "James Okonkwo",
        "title": "Airline ops approver",
        "role": "approver",
        "domains": ["airline_operations", "airports"],
        "bio": "Signs off IRROPS priority packs and airport terminal access windows.",
    },
    {
        "id": "priya-lounge-admin",
        "name": "Priya Nair",
        "title": "Lounge product admin",
        "role": "admin",
        "domains": ["lounge", "loyalty", "airports"],
        "bio": "Publishes lounge matrices, canaries Chairman's access, manages change records.",
    },
    {
        "id": "tom-banking-author",
        "name": "Tom Barrett",
        "title": "Credit policy author",
        "role": "author",
        "domains": ["banking_credit"],
        "bio": "Authors LVR pricing bands — proves Axiom is not airline-only.",
    },
    {
        "id": "sofia-risk-approver",
        "name": "Sofia Alvarez",
        "title": "Credit risk approver",
        "role": "approver",
        "domains": ["banking_credit"],
        "bio": "Approves banking packs before production promote.",
    },
    {
        "id": "alex-viewer",
        "name": "Alex Kim",
        "title": "Compliance viewer",
        "role": "viewer",
        "domains": ["loyalty", "lounge", "airline_operations", "airports", "banking_credit"],
        "bio": "Read-only audit across domains; cannot author or promote.",
    },
]


def domain_by_id(domain_id: str) -> dict[str, Any] | None:
    for d in DOMAINS:
        if d["id"] == domain_id:
            return d
    return None


def persona_by_id(persona_id: str) -> dict[str, Any] | None:
    for p in PERSONAS:
        if p["id"] == persona_id:
            return p
    return None


def lounge_framework_payload() -> dict[str, Any]:
    cells = [
        {
            "tier": tier,
            "cabin": cabin,
            "lounge": lounge,
            "lounge_label": next(
                (x["label"] for x in LOUNGE_TYPES if x["id"] == lounge),
                "No access",
            )
            if lounge
            else "No access",
        }
        for (tier, cabin), lounge in LOUNGE_MATRIX.items()
    ]
    return {
        "id": "lounge_matrix",
        "title": "Lounge decision framework",
        "summary": (
            "Eligibility is the max of tier-led and cabin-led access. "
            "Bronze flying First can enter First Lounge; Platinum flying Economy "
            "still reaches Business Lounge; Platinum One always reaches Chairman's."
        ),
        "lounge_types": list(LOUNGE_TYPES),
        "membership_tiers": list(MEMBERSHIP_TIERS),
        "travel_classes": list(TRAVEL_CLASSES),
        "matrix": cells,
    }


def catalog_payload() -> dict[str, Any]:
    return {
        "domains": DOMAINS,
        "personas": PERSONAS,
        "frameworks": {
            "lounge_matrix": lounge_framework_payload(),
        },
    }
