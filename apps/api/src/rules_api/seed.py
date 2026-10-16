from __future__ import annotations

import sqlite3

from rules_engine.samples import all_seed_packs

from rules_api.db import DEFAULT_TENANT_ID
from rules_api.jsonutil import dumps


def _seed_pack(
    conn: sqlite3.Connection,
    pack_dict: dict,
    *,
    tenant_id: str,
    change_record_id: str,
) -> None:
    domain = pack_dict["domain"]
    pack_id = pack_dict["pack_id"]
    version = pack_dict["version"]
    existing = conn.execute(
        """
        SELECT 1 FROM rule_pack_versions
        WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
        """,
        (tenant_id, domain, pack_id, version),
    ).fetchone()
    if existing:
        return

    conn.execute(
        """
        INSERT INTO rule_pack_versions (
            tenant_id, domain, pack_id, version, lifecycle, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            domain,
            pack_id,
            version,
            pack_dict["lifecycle"],
            dumps(pack_dict),
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
            domain,
            pack_id,
            "production",
            version,
            "2024-01-01T00:00:00+00:00",
            100,
            None,
            change_record_id,
        ),
    )


def seed_lounge_entitlements(
    conn: sqlite3.Connection, *, tenant_id: str = DEFAULT_TENANT_ID
) -> None:
    existing = conn.execute(
        "SELECT 1 FROM entitlements WHERE entitlement_id=?",
        ("ent-ff-grandfathered-companion",),
    ).fetchone()
    if existing:
        return

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
            dumps(
                {
                    "lounge_type": "business",
                    "lounge_label": "Business Lounge",
                    "via": "grandfathered_offer",
                }
            ),
            "0.9.0",
            "legacy-one-off-offer",
            "2023-06-15T10:00:00+00:00",
            None,
            "active",
            1,
            "offered_pack_2023_q2",
        ),
    )


def seed_all(conn: sqlite3.Connection, *, tenant_id: str = DEFAULT_TENANT_ID) -> None:
    for idx, pack in enumerate(all_seed_packs()):
        _seed_pack(
            conn,
            pack.to_dict(),
            tenant_id=tenant_id,
            change_record_id=f"CR-SEED-{idx + 1:03d}",
        )
    seed_lounge_entitlements(conn, tenant_id=tenant_id)
    conn.commit()


def ensure_seeded(conn: sqlite3.Connection) -> None:
    seed_all(conn)
