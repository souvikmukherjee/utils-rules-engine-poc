from __future__ import annotations

import sqlite3

from rules_engine.samples import load_lounge_pack

from rules_api.db import DEFAULT_TENANT_ID
from rules_api.jsonutil import dumps


def seed_lounge(conn: sqlite3.Connection, *, tenant_id: str = DEFAULT_TENANT_ID) -> None:
    pack = load_lounge_pack()
    existing = conn.execute(
        """
        SELECT 1 FROM rule_pack_versions
        WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
        """,
        (tenant_id, pack.domain, pack.pack_id, pack.version),
    ).fetchone()
    if existing:
        return

    payload = {
        "domain": pack.domain,
        "pack_id": pack.pack_id,
        "version": pack.version,
        "lifecycle": pack.lifecycle,
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "priority": r.priority,
                "enabled": r.enabled,
                "effective_from": r.effective_from.isoformat(),
                "effective_to": r.effective_to.isoformat() if r.effective_to else None,
                "condition": r.condition,
                "effects": [e.to_dict() for e in r.effects],
            }
            for r in pack.rules
        ],
    }

    conn.execute(
        """
        INSERT INTO rule_pack_versions (
            tenant_id, domain, pack_id, version, lifecycle, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (tenant_id, pack.domain, pack.pack_id, pack.version, pack.lifecycle, dumps(payload)),
    )

    for rule in pack.rules:
        conn.execute(
            """
            INSERT INTO rules (
                tenant_id, domain, pack_id, pack_version, rule_id, name, priority, enabled,
                effective_from, effective_to, condition_json, effects_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                pack.domain,
                pack.pack_id,
                pack.version,
                rule.id,
                rule.name,
                rule.priority,
                1 if rule.enabled else 0,
                rule.effective_from.isoformat(),
                rule.effective_to.isoformat() if rule.effective_to else None,
                dumps(rule.condition),
                dumps([e.to_dict() for e in rule.effects]),
            ),
        )

    conn.execute(
        """
        INSERT INTO releases (
            tenant_id, domain, pack_id, environment, pack_version,
            go_live_at, canary_percent, canary_version, change_record_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            pack.domain,
            pack.pack_id,
            "production",
            pack.version,
            "2024-01-01T00:00:00+00:00",
            100,
            None,
            "CR-SEED-001",
        ),
    )

    # Grandfathered companion pass — old pack, still honored via ledger.
    conn.execute(
        """
        INSERT INTO entitlements (
            entitlement_id, tenant_id, domain, subject_id, benefit_type,
            benefit_payload_json, source_pack_version, source_rule_id,
            granted_at, expires_at, status, grandfathered, cohort_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ent-ff-grandfathered-companion",
            tenant_id,
            "lounge",
            "FF-GRANDFATHERED",
            "companion_pass",
            dumps({"companions_allowed": 1, "note": "legacy +1 pack offer"}),
            "0.9.0",
            "legacy-companion-plus-one",
            "2023-06-15T10:00:00+00:00",
            None,
            "active",
            1,
            "offered_pack_2023_q2",
        ),
    )

    # Also grant lounge_access so eligibility short-circuits clearly for this subject.
    conn.execute(
        """
        INSERT INTO entitlements (
            entitlement_id, tenant_id, domain, subject_id, benefit_type,
            benefit_payload_json, source_pack_version, source_rule_id,
            granted_at, expires_at, status, grandfathered, cohort_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ent-ff-grandfathered-access",
            tenant_id,
            "lounge",
            "FF-GRANDFATHERED",
            "lounge_access",
            dumps({"lounge_class": "domestic", "via": "grandfathered_offer"}),
            "0.9.0",
            "legacy-one-off-offer",
            "2023-06-15T10:00:00+00:00",
            None,
            "active",
            1,
            "offered_pack_2023_q2",
        ),
    )

    conn.commit()


def ensure_seeded(conn: sqlite3.Connection) -> None:
    seed_lounge(conn)
