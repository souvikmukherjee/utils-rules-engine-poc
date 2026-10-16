from __future__ import annotations

import os
import sqlite3
import warnings
from pathlib import Path
from typing import Any

from rules_api.jsonutil import dumps, loads
from rules_api.store import RulesStore

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "rules.db"
DEFAULT_TENANT_ID = "default"

__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_TENANT_ID",
    "connect",
    "dumps",
    "init_schema",
    "loads",
    "open_store",
    "resolve_database_url",
    "row_to_dict",
]


def resolve_database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open the PoC store.

    ``DATABASE_URL``:
    - unset / ``sqlite://`` → local SQLite (default)
    - ``postgres://`` / ``postgresql://`` → planned; PoC keeps SQLite and warns
    """
    url = resolve_database_url()
    if url and (url.startswith("postgres://") or url.startswith("postgresql://")):
        warnings.warn(
            "DATABASE_URL points at Postgres, which is planned but not implemented in this PoC. "
            "Falling back to SQLite. See docs/ARCHITECTURE.md.",
            UserWarning,
            stacklevel=2,
        )

    path = db_path or DEFAULT_DB_PATH
    if url and url.startswith("sqlite:///"):
        path = Path(url.removeprefix("sqlite:///"))

    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rule_pack_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            domain TEXT NOT NULL,
            pack_id TEXT NOT NULL,
            version TEXT NOT NULL,
            lifecycle TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            UNIQUE(tenant_id, domain, pack_id, version)
        );

        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            domain TEXT NOT NULL,
            pack_id TEXT NOT NULL,
            pack_version TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            effective_from TEXT NOT NULL,
            effective_to TEXT,
            condition_json TEXT NOT NULL,
            effects_json TEXT NOT NULL,
            UNIQUE(tenant_id, domain, pack_id, pack_version, rule_id)
        );

        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            domain TEXT NOT NULL,
            pack_id TEXT NOT NULL,
            environment TEXT NOT NULL,
            pack_version TEXT NOT NULL,
            go_live_at TEXT,
            canary_percent INTEGER NOT NULL DEFAULT 100,
            canary_version TEXT,
            change_record_id TEXT,
            UNIQUE(tenant_id, domain, pack_id, environment)
        );

        CREATE TABLE IF NOT EXISTS entitlements (
            entitlement_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            domain TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            benefit_type TEXT NOT NULL,
            benefit_payload_json TEXT NOT NULL,
            source_pack_version TEXT,
            source_rule_id TEXT,
            granted_at TEXT NOT NULL,
            expires_at TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            grandfathered INTEGER NOT NULL DEFAULT 0,
            cohort_key TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_entitlements_subject
            ON entitlements(tenant_id, domain, subject_id, status);

        CREATE TABLE IF NOT EXISTS audit_events (
            evaluation_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            domain TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            environment TEXT NOT NULL,
            as_of TEXT NOT NULL,
            pack_version TEXT,
            decision TEXT NOT NULL,
            path TEXT NOT NULL,
            request_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_audit_subject
            ON audit_events(tenant_id, domain, subject_id, created_at);
        """
    )
    _migrate_columns(conn)
    conn.commit()


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add columns introduced after Phase 0 without breaking existing DBs."""
    migrations = [
        ("rule_pack_versions", "tenant_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("rules", "tenant_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("releases", "tenant_id", "TEXT NOT NULL DEFAULT 'default'"),
        ("releases", "canary_version", "TEXT"),
        ("audit_events", "tenant_id", "TEXT NOT NULL DEFAULT 'default'"),
    ]
    for table, column, ddl in migrations:
        cols = {
            row[1]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def open_store(db_path: Path | None = None) -> tuple[sqlite3.Connection, RulesStore]:
    from rules_api.sqlite_store import SqliteRulesStore

    conn = connect(db_path)
    init_schema(conn)
    return conn, SqliteRulesStore(conn)


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)
