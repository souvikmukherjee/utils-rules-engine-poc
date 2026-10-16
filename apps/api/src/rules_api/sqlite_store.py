from __future__ import annotations

import sqlite3
from typing import Any

from rules_api.jsonutil import dumps, loads
from rules_api.store import RulesStore


class SqliteRulesStore(RulesStore):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_pack_versions(self, domain: str, *, tenant_id: str = "default") -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT domain, pack_id, version, lifecycle
            FROM rule_pack_versions
            WHERE tenant_id=? AND domain=?
            ORDER BY id DESC
            """,
            (tenant_id, domain),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_pack_version(
        self, domain: str, pack_id: str, version: str, *, tenant_id: str = "default"
    ) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT domain, pack_id, version, lifecycle, payload_json
            FROM rule_pack_versions
            WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
            """,
            (tenant_id, domain, pack_id, version),
        ).fetchone()
        if row is None:
            return None
        payload = loads(row["payload_json"])
        return {
            "domain": row["domain"],
            "pack_id": row["pack_id"],
            "version": row["version"],
            "lifecycle": row["lifecycle"],
            "payload": payload,
        }

    def get_pack_payload(
        self, domain: str, pack_id: str, version: str, *, tenant_id: str = "default"
    ) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT payload_json FROM rule_pack_versions
            WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
            """,
            (tenant_id, domain, pack_id, version),
        ).fetchone()
        if row is None:
            return None
        return loads(row["payload_json"])

    def upsert_pack_version(
        self,
        *,
        domain: str,
        pack_id: str,
        version: str,
        lifecycle: str,
        payload: dict[str, Any],
        tenant_id: str = "default",
    ) -> None:
        existing = self.conn.execute(
            """
            SELECT id FROM rule_pack_versions
            WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
            """,
            (tenant_id, domain, pack_id, version),
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE rule_pack_versions
                SET lifecycle=?, payload_json=?
                WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
                """,
                (lifecycle, dumps(payload), tenant_id, domain, pack_id, version),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO rule_pack_versions (
                    tenant_id, domain, pack_id, version, lifecycle, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tenant_id, domain, pack_id, version, lifecycle, dumps(payload)),
            )

        # Legacy `rules` rows were tied to the custom IR. Packs are now JDM envelopes;
        # clear any stale denormalized rows for this version.
        self.conn.execute(
            """
            DELETE FROM rules
            WHERE tenant_id=? AND domain=? AND pack_id=? AND pack_version=?
            """,
            (tenant_id, domain, pack_id, version),
        )

    def update_pack_lifecycle(
        self,
        domain: str,
        pack_id: str,
        version: str,
        lifecycle: str,
        *,
        tenant_id: str = "default",
    ) -> bool:
        cur = self.conn.execute(
            """
            UPDATE rule_pack_versions
            SET lifecycle=?
            WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
            """,
            (lifecycle, tenant_id, domain, pack_id, version),
        )
        if cur.rowcount:
            row = self.conn.execute(
                """
                SELECT payload_json FROM rule_pack_versions
                WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
                """,
                (tenant_id, domain, pack_id, version),
            ).fetchone()
            if row:
                payload = loads(row["payload_json"])
                payload["lifecycle"] = lifecycle
                self.conn.execute(
                    """
                    UPDATE rule_pack_versions SET payload_json=?
                    WHERE tenant_id=? AND domain=? AND pack_id=? AND version=?
                    """,
                    (dumps(payload), tenant_id, domain, pack_id, version),
                )
        return cur.rowcount > 0

    def get_release(
        self, domain: str, pack_id: str, environment: str, *, tenant_id: str = "default"
    ) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT domain, pack_id, environment, pack_version, go_live_at,
                   canary_percent, canary_version, change_record_id, tenant_id
            FROM releases
            WHERE tenant_id=? AND domain=? AND pack_id=? AND environment=?
            """,
            (tenant_id, domain, pack_id, environment),
        ).fetchone()
        return dict(row) if row else None

    def upsert_release(
        self,
        *,
        domain: str,
        pack_id: str,
        environment: str,
        pack_version: str,
        go_live_at: str | None = None,
        canary_percent: int = 100,
        canary_version: str | None = None,
        change_record_id: str | None = None,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        existing = self.get_release(domain, pack_id, environment, tenant_id=tenant_id)
        if existing:
            self.conn.execute(
                """
                UPDATE releases SET
                    pack_version=?, go_live_at=?, canary_percent=?,
                    canary_version=?, change_record_id=?
                WHERE tenant_id=? AND domain=? AND pack_id=? AND environment=?
                """,
                (
                    pack_version,
                    go_live_at,
                    canary_percent,
                    canary_version,
                    change_record_id,
                    tenant_id,
                    domain,
                    pack_id,
                    environment,
                ),
            )
        else:
            self.conn.execute(
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
                    environment,
                    pack_version,
                    go_live_at,
                    canary_percent,
                    canary_version,
                    change_record_id,
                ),
            )
        release = self.get_release(domain, pack_id, environment, tenant_id=tenant_id)
        assert release is not None
        return release

    def list_entitlements(
        self,
        *,
        domain: str,
        subject_id: str,
        tenant_id: str = "default",
        grandfathered: bool | None = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT * FROM entitlements
            WHERE tenant_id=? AND domain=? AND subject_id=?
        """
        params: list[Any] = [tenant_id, domain, subject_id]
        if grandfathered is not None:
            sql += " AND grandfathered=?"
            params.append(1 if grandfathered else 0)
        sql += " ORDER BY granted_at DESC"
        rows = self.conn.execute(sql, params).fetchall()
        return [
            {
                "entitlement_id": r["entitlement_id"],
                "tenant_id": r["tenant_id"],
                "domain": r["domain"],
                "subject_id": r["subject_id"],
                "benefit_type": r["benefit_type"],
                "benefit_payload": loads(r["benefit_payload_json"]),
                "source_pack_version": r["source_pack_version"],
                "source_rule_id": r["source_rule_id"],
                "granted_at": r["granted_at"],
                "expires_at": r["expires_at"],
                "status": r["status"],
                "grandfathered": bool(r["grandfathered"]),
                "cohort_key": r["cohort_key"],
            }
            for r in rows
        ]

    def active_entitlement_rows(
        self,
        *,
        domain: str,
        subject_id: str,
        tenant_id: str = "default",
    ) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM entitlements
            WHERE tenant_id=? AND domain=? AND subject_id=? AND status='active'
            """,
            (tenant_id, domain, subject_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def insert_entitlement(self, row: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, tenant_id, domain, subject_id, benefit_type,
                benefit_payload_json, source_pack_version, source_rule_id,
                granted_at, expires_at, status, grandfathered, cohort_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["entitlement_id"],
                row.get("tenant_id", "default"),
                row["domain"],
                row["subject_id"],
                row["benefit_type"],
                dumps(row["benefit_payload"]),
                row.get("source_pack_version"),
                row.get("source_rule_id"),
                row["granted_at"],
                row.get("expires_at"),
                row.get("status", "active"),
                1 if row.get("grandfathered") else 0,
                row.get("cohort_key"),
            ),
        )

    def get_audit(self, evaluation_id: str, *, tenant_id: str = "default") -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM audit_events
            WHERE evaluation_id=? AND tenant_id=?
            """,
            (evaluation_id, tenant_id),
        ).fetchone()
        if row is None:
            return None
        return {
            "evaluation_id": row["evaluation_id"],
            "tenant_id": row["tenant_id"],
            "domain": row["domain"],
            "subject_id": row["subject_id"],
            "environment": row["environment"],
            "as_of": row["as_of"],
            "pack_version": row["pack_version"],
            "decision": row["decision"],
            "path": row["path"],
            "created_at": row["created_at"],
            "result": loads(row["result_json"]),
        }

    def search_audit(
        self,
        *,
        domain: str,
        subject_id: str,
        tenant_id: str = "default",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM audit_events
            WHERE tenant_id=? AND domain=? AND subject_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (tenant_id, domain, subject_id, limit),
        ).fetchall()
        return [
            {
                "evaluation_id": r["evaluation_id"],
                "tenant_id": r["tenant_id"],
                "domain": r["domain"],
                "subject_id": r["subject_id"],
                "environment": r["environment"],
                "as_of": r["as_of"],
                "pack_version": r["pack_version"],
                "decision": r["decision"],
                "path": r["path"],
                "created_at": r["created_at"],
                "result": loads(r["result_json"]),
            }
            for r in rows
        ]

    def insert_audit(self, row: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO audit_events (
                evaluation_id, tenant_id, domain, subject_id, environment, as_of,
                pack_version, decision, path, request_json, result_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["evaluation_id"],
                row.get("tenant_id", "default"),
                row["domain"],
                row["subject_id"],
                row["environment"],
                row["as_of"],
                row["pack_version"],
                row["decision"],
                row["path"],
                dumps(row["request"]),
                dumps(row["result"]),
                row["created_at"],
            ),
        )

    def commit(self) -> None:
        self.conn.commit()
