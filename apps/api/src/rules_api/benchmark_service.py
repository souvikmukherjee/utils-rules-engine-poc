"""Orchestrate + persist synthetic scale benchmarks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from rules_engine.benchmark import (
    PRESET_COLUMN_COUNTS,
    PRESET_FIRE_COUNTS,
    PRESET_RULE_COUNTS,
    run_benchmark,
    run_matrix,
)

from rules_api.benchmark_store import BenchmarkStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def comparison_payload(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Flatten stored runs into an objective comparison table for the UI."""
    rows: list[dict[str, Any]] = []
    for run in runs:
        result = run.get("result") or {}
        kind = run.get("kind")
        if kind == "matrix":
            for cell in result.get("cells") or []:
                rows.append(_cell_row(run, cell))
        elif kind == "single":
            rows.append(_cell_row(run, result))

    # Latest fingerprint wins when duplicates exist.
    by_key: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = f"{row['column_count']}:{row['rule_count']}:{row['fire_count']}:{row['seed']}"
        by_key[key] = row

    table = sorted(
        by_key.values(),
        key=lambda r: (r["rule_count"], r["fire_count"], r["column_count"]),
    )

    zen_tps = [r["zen_throughput_fps"] for r in table if r.get("zen_throughput_fps")]
    dmn_tps = [r["dmn_throughput_fps"] for r in table if r.get("dmn_throughput_fps")]
    parity = [r["parity_pct"] for r in table if r.get("parity_pct") is not None]

    return {
        "generated_at": _now(),
        "row_count": len(table),
        "presets": {
            "rule_counts": list(PRESET_RULE_COUNTS),
            "fire_counts": list(PRESET_FIRE_COUNTS),
            "column_counts": list(PRESET_COLUMN_COUNTS),
        },
        "summary": {
            "cells": len(table),
            "zen_median_fps": _median(zen_tps),
            "dmn_table_median_fps": _median(dmn_tps),
            "parity_min_pct": min(parity) if parity else None,
            "parity_max_pct": max(parity) if parity else None,
            "speedup_dmn_vs_zen_median": (
                round(_median(dmn_tps) / _median(zen_tps), 2)
                if zen_tps and dmn_tps and _median(zen_tps)
                else None
            ),
        },
        "rows": table,
    }


def _cell_row(run: dict[str, Any], cell: dict[str, Any]) -> dict[str, Any]:
    params = cell.get("params") or {}
    engines = {e["engine"]: e for e in (cell.get("engines") or [])}
    zen = engines.get("zen") or {}
    dmn = engines.get("dmn_table") or {}
    parity = cell.get("parity") or {}
    return {
        "run_id": run.get("run_id"),
        "label": run.get("label"),
        "created_at": run.get("created_at"),
        "fingerprint": cell.get("fingerprint"),
        "column_count": params.get("column_count"),
        "rule_count": params.get("rule_count"),
        "fire_count": params.get("fire_count"),
        "seed": params.get("seed"),
        "variables": params.get("variables") or [],
        "sample_outcomes": params.get("sample_outcomes") or [],
        "zen_elapsed_ms": zen.get("elapsed_ms"),
        "zen_throughput_fps": zen.get("throughput_fps"),
        "zen_avg_ms": zen.get("avg_ms_per_fire"),
        "zen_histogram": zen.get("decision_histogram"),
        "dmn_elapsed_ms": dmn.get("elapsed_ms"),
        "dmn_throughput_fps": dmn.get("throughput_fps"),
        "dmn_avg_ms": dmn.get("avg_ms_per_fire"),
        "dmn_histogram": dmn.get("decision_histogram"),
        "parity_pct": parity.get("agree_pct"),
        "parity_sample": parity.get("sample_size"),
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 2)
    return round((ordered[mid - 1] + ordered[mid]) / 2.0, 2)


def execute_single(store: BenchmarkStore, body: dict[str, Any]) -> dict[str, Any]:
    result = run_benchmark(
        column_count=int(body["column_count"]),
        rule_count=int(body["rule_count"]),
        fire_count=int(body["fire_count"]),
        seed=int(body.get("seed", 42)),
        values_per_column=int(body.get("values_per_column", 8)),
        engines=list(body.get("engines") or ["zen", "dmn_table"]),
        max_work=int(body.get("max_work", 200_000_000)),
    )
    run_id = str(uuid.uuid4())
    created = _now()
    label = body.get("label") or (
        f"{body['column_count']}c · {body['rule_count']}r · {body['fire_count']}f"
    )
    params = {
        "column_count": body["column_count"],
        "rule_count": body["rule_count"],
        "fire_count": body["fire_count"],
        "seed": body.get("seed", 42),
        "values_per_column": body.get("values_per_column", 8),
        "engines": body.get("engines") or ["zen", "dmn_table"],
        "max_work": body.get("max_work", 200_000_000),
    }
    store.insert_run(
        run_id=run_id,
        kind="single",
        label=label,
        params=params,
        result=result,
        status="completed",
        created_at=created,
        tenant_id=body.get("tenant_id") or "default",
    )
    return {
        "run_id": run_id,
        "kind": "single",
        "label": label,
        "params": params,
        "result": result,
        "status": "completed",
        "created_at": created,
    }


def execute_matrix(store: BenchmarkStore, body: dict[str, Any]) -> dict[str, Any]:
    result = run_matrix(
        column_count=int(body.get("column_count", 10)),
        rule_counts=list(body.get("rule_counts") or [100, 1_000, 10_000]),
        fire_counts=list(body.get("fire_counts") or [1_000, 10_000, 1_000_000]),
        seed=int(body.get("seed", 42)),
        engines=list(body.get("engines") or ["zen", "dmn_table"]),
        max_work=int(body.get("max_work", 200_000_000)),
        skip_over_cap=bool(body.get("skip_over_cap", True)),
    )
    run_id = str(uuid.uuid4())
    created = _now()
    label = body.get("label") or "preset-matrix"
    params = {
        "column_count": body.get("column_count", 10),
        "rule_counts": body.get("rule_counts") or [100, 1_000, 10_000],
        "fire_counts": body.get("fire_counts") or [1_000, 10_000, 1_000_000],
        "seed": body.get("seed", 42),
        "engines": body.get("engines") or ["zen", "dmn_table"],
        "max_work": body.get("max_work", 200_000_000),
        "skip_over_cap": body.get("skip_over_cap", True),
    }
    store.insert_run(
        run_id=run_id,
        kind="matrix",
        label=label,
        params=params,
        result=result,
        status="completed",
        created_at=created,
        tenant_id=body.get("tenant_id") or "default",
    )
    return {
        "run_id": run_id,
        "kind": "matrix",
        "label": label,
        "params": params,
        "result": result,
        "status": "completed",
        "created_at": created,
    }
