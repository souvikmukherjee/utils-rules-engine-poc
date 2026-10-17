#!/usr/bin/env python3
"""Seed the SQLite store with a scale matrix so the Benchmark UI has data on load."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "packages" / "rules_engine" / "src"),
    str(ROOT / "apps" / "api" / "src"),
]

from rules_api.benchmark_service import comparison_payload, execute_matrix  # noqa: E402
from rules_api.db import open_store  # noqa: E402
from rules_api.benchmark_store import BenchmarkStore  # noqa: E402
from rules_api.seed import ensure_seeded  # noqa: E402


def main() -> int:
    conn, _store = open_store()
    ensure_seeded(conn)
    bench = BenchmarkStore(conn)

    # Full requested grid; cells over max_work are skipped (recorded in result.skipped).
    result = execute_matrix(
        bench,
        {
            "column_count": 10,
            "rule_counts": [100, 1_000, 10_000],
            "fire_counts": [1_000, 10_000, 1_000_000],
            "seed": 42,
            "engines": ["zen", "dmn_table"],
            "max_work": 200_000_000,
            "skip_over_cap": True,
            "label": "seed-full-matrix",
            "tenant_id": "default",
        },
    )

    compare = comparison_payload(bench.list_runs(limit=20))
    out = ROOT / "artifacts" / "engine-comparison" / "benchmark_matrix_seed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "run_id": result["run_id"],
                "cell_count": result["result"]["cell_count"],
                "skipped": result["result"]["skipped"],
                "compare_summary": compare["summary"],
                "compare_rows": compare["rows"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "run_id": result["run_id"],
                "cells": result["result"]["cell_count"],
                "skipped": len(result["result"]["skipped"]),
                "wrote": str(out),
                "summary": compare["summary"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
