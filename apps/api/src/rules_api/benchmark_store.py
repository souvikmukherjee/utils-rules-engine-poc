"""Persist scale-benchmark runs for the Benchmark UI."""

from __future__ import annotations

import sqlite3
from typing import Any

from rules_api.jsonutil import dumps, loads


class BenchmarkStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_run(
        self,
        *,
        run_id: str,
        kind: str,
        label: str | None,
        params: dict[str, Any],
        result: dict[str, Any],
        status: str,
        created_at: str,
        tenant_id: str = "default",
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO benchmark_runs (
                run_id, tenant_id, kind, label, params_json, result_json, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                tenant_id,
                kind,
                label,
                dumps(params),
                dumps(result),
                status,
                created_at,
            ),
        )
        self.conn.commit()

    def get_run(self, run_id: str, *, tenant_id: str = "default") -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM benchmark_runs WHERE run_id=? AND tenant_id=?
            """,
            (run_id, tenant_id),
        ).fetchone()
        if row is None:
            return None
        return self._row(row)

    def list_runs(
        self,
        *,
        tenant_id: str = "default",
        kind: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if kind:
            rows = self.conn.execute(
                """
                SELECT * FROM benchmark_runs
                WHERE tenant_id=? AND kind=?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, kind, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM benchmark_runs
                WHERE tenant_id=?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, limit),
            ).fetchall()
        return [self._row(r) for r in rows]

    def delete_run(self, run_id: str, *, tenant_id: str = "default") -> bool:
        cur = self.conn.execute(
            "DELETE FROM benchmark_runs WHERE run_id=? AND tenant_id=?",
            (run_id, tenant_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": row["run_id"],
            "tenant_id": row["tenant_id"],
            "kind": row["kind"],
            "label": row["label"],
            "params": loads(row["params_json"]),
            "result": loads(row["result_json"]),
            "status": row["status"],
            "created_at": row["created_at"],
        }
