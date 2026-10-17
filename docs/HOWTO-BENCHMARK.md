# How to: Scale Benchmark (Zen vs DMN table)

Synthetic scale lab for comparing engines on **generated** rules — not the lounge PoC pack.

Anyone can change parameters, regenerate variables/outcomes, fire at volume, and reload the UI to see an **objective, persisted** comparison.

---

## What is compared

| Engine | Implementation | Role |
|--------|----------------|------|
| **Zen** | GoRules Zen evaluating generated JDM (`hitPolicy: first`) | Real in-process engine |
| **DMN-table** | In-process FIRST-hit matcher on the **same** generated rules | Kogito/DMN-style semantics at scale |

Live Kogito HTTP (`LoungeAccess.dmn` on `:8081`) stays available for the lounge PoC toggle. It cannot host arbitrary 10k-rule synthetic packs, so scale cells use the DMN-table peer on identical rules.

---

## Scale axes

| Axis | Presets | Tunable range |
|------|---------|---------------|
| **Rules** | 100 · 1,000 · 10,000 | UI: 50–10,000 |
| **Fires** | 1,000 · 10,000 · 1,000,000 | UI: 100–1,000,000 |
| **Columns (variables)** | default 10 | 1–50 (`v0`…`vn`) |
| **Values / column** | default 8 | 2–32 (`s0`…`sk`) |
| **Seed** | 42 | any int (reproducible packs + facts) |

Each rule constrains a subset of columns and emits:

- `decision` — `allow` / `deny` / `inconclusive` (catch-all)
- `outcome` — generated codes like `out_12`
- `rule_id` — `r00042`, plus terminal `r_default`

**Work cap:** `rules × fires` must stay ≤ `max_work` (default **200,000,000**) for a sync run. Raise `max_work` in the UI or API to allow heavier cells; the full matrix **skips** over-cap cells and records them under `skipped`.

---

## Run locally

### Prerequisites

Same as the main README: Python 3.11+, Node 20+, `make install-py` / `make install-web`.

### Start services

```bash
make api    # http://127.0.0.1:8000
make web    # http://127.0.0.1:3000
```

### Seed a matrix into SQLite (so the UI has data on load)

```bash
make benchmark-matrix
# → writes apps/api/data/rules.db (benchmark_runs)
# → writes artifacts/engine-comparison/benchmark_matrix_seed.json
```

Preset grid:

- `rule_counts`: `[100, 1000, 10000]`
- `fire_counts`: `[1000, 10000, 1000000]`
- `column_count`: `10`
- Cells over `max_work` are skipped (typically `1000×1M` and `10000×1M`)

### Open the UI

1. Go to [http://127.0.0.1:3000](http://127.0.0.1:3000)
2. Click **Benchmark**
3. Summary cards + comparison table load from `GET /v1/benchmark/compare`
4. Change **Columns / Rules / Fires / Seed / Max work** → **Run custom cell**
5. Or run **Quick matrix** (≤10k fires) / **Full matrix** (incl. 1M where under cap)

Results persist — refresh or reopen the tab and the objective table is still there.

---

## Reading the UI

| Card / column | Meaning |
|---------------|---------|
| **Stored cells** | Distinct completed (cols × rules × fires × seed) rows in the store |
| **Zen / DMN median throughput** | Median firings per second across stored cells |
| **Parity range** | Min–max % of sample facts where Zen and DMN-table agree on `decision` + `outcome` |
| **Zen fps / DMN fps** | Throughput for that cell |
| **Zen ms / DMN ms** | Wall time for all fires in the cell |
| **Parity** | Agree % on the parity sample (default up to 500 facts) |
| **Outcomes** | Sample of generated outcome codes |
| **Generated variables** | Column names from the latest cell (`v0`…) |

---

## API how-to

Full OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Objective comparison (what the UI loads)

```bash
curl -s localhost:8000/v1/benchmark/compare | jq '.summary, .rows[:3]'
```

### Custom cell (your parameters)

```bash
curl -s localhost:8000/v1/benchmark/run \
  -H 'content-type: application/json' \
  -d '{
    "column_count": 12,
    "rule_count": 250,
    "fire_count": 2000,
    "seed": 99,
    "values_per_column": 8,
    "engines": ["zen", "dmn_table"],
    "max_work": 200000000,
    "label": "my-custom-cell"
  }' | jq '{run_id, parity: .result.parity.agree_pct, engines: .result.engines}'
```

### Full / quick matrix

```bash
# Full preset (skips over max_work)
curl -s localhost:8000/v1/benchmark/matrix \
  -H 'content-type: application/json' \
  -d '{
    "column_count": 10,
    "rule_counts": [100, 1000, 10000],
    "fire_counts": [1000, 10000, 1000000],
    "seed": 42,
    "max_work": 200000000,
    "skip_over_cap": true,
    "label": "full-matrix"
  }' | jq '{run_id, cells: .result.cell_count, skipped: .result.skipped}'

# Quick matrix
curl -s localhost:8000/v1/benchmark/matrix \
  -H 'content-type: application/json' \
  -d '{
    "column_count": 10,
    "rule_counts": [100, 1000],
    "fire_counts": [1000, 10000],
    "label": "quick-matrix"
  }' | jq '{run_id, cells: .result.cell_count}'
```

### List / fetch / delete runs

```bash
curl -s localhost:8000/v1/benchmark/runs | jq '.count, .runs[].run_id'
curl -s localhost:8000/v1/benchmark/runs/<run_id> | jq .
curl -s -X DELETE -H 'X-Role: author' \
  localhost:8000/v1/benchmark/runs/<run_id> | jq .
```

---

## Endpoint summary

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/benchmark/compare` | Flattened objective table from stored runs |
| `GET` | `/v1/benchmark/runs` | List persisted runs |
| `GET` | `/v1/benchmark/runs/{id}` | One run (params + full result JSON) |
| `DELETE` | `/v1/benchmark/runs/{id}` | Delete (requires `X-Role: author+`) |
| `POST` | `/v1/benchmark/run` | One synthetic cell; persist |
| `POST` | `/v1/benchmark/matrix` | Grid of cells; persist as one matrix run |

---

## Storage

| Piece | Location |
|-------|----------|
| SQLite table | `benchmark_runs` in `apps/api/data/rules.db` |
| Seed artifact | `artifacts/engine-comparison/benchmark_matrix_seed.json` |
| Generator / runner | `packages/rules_engine/src/rules_engine/benchmark.py` |
| Persist + compare | `apps/api/src/rules_api/benchmark_store.py`, `benchmark_service.py` |
| UI | `apps/web/src/components/BenchmarkPanel.tsx` (tab **Benchmark**) |
| Seed script | `scripts/seed_benchmark_matrix.py` → `make benchmark-matrix` |

Schema (created on API start):

```sql
CREATE TABLE IF NOT EXISTS benchmark_runs (
  run_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL DEFAULT 'default',
  kind TEXT NOT NULL,          -- 'single' | 'matrix'
  label TEXT,
  params_json TEXT NOT NULL,
  result_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed',
  created_at TEXT NOT NULL
);
```

---

## Example seeded outcomes

From a typical seed (`column_count=10`, seed `42`):

| Rules | Fires | Zen fps (approx) | DMN-table fps | Parity |
|------:|------:|-----------------:|--------------:|-------:|
| 100 | 1,000 | ~7.8k | ~480k | 100% |
| 100 | 10,000 | ~8.0k | ~480k | 100% |
| 100 | **1,000,000** | ~6.9k | ~480k | 100% |
| 1,000 | 1,000 | ~5.1k | ~480k | 100% |
| 1,000 | 10,000 | ~5.4k | ~480k | 100% |
| 10,000 | 1,000 | ~3.9k | ~110k+ | 100% |
| 10,000 | 10,000 | ~5.3k | ~480k | 100% |

Skipped under default `max_work=200M`: `1,000 × 1M`, `10,000 × 1M`. Raise the cap and re-run those cells if you need them.

---

## Tests

```bash
# Generator + parity
pytest packages/rules_engine/tests/test_benchmark.py -q

# API run + compare persistence
pytest apps/api/tests/test_benchmark_api.py -q
```

---

## Related

- Lounge PoC engine comparison (100 cases): `scripts/compare_engines_100.py` · `make compare-engines`
- Product / architecture: [PRODUCT.md](PRODUCT.md) · [ARCHITECTURE.md](ARCHITECTURE.md)
- Root [README.md](../README.md) — Developer how-to
