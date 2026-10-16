# Axiom — Rules Platform (PoC)

Domain-agnostic decision platform on **[GoRules Zen](https://docs.gorules.io/)**: business users author versioned **JSON Decision Models (JDM)**; Zen evaluates them; Axiom adds change management, simulation, grandfathering, canary, and searchable audit.

## Monorepo layout

```
apps/
  web/              Next.js — Axiom UI + embedded GoRules JDM Editor
  api/              FastAPI — design-time + runtime APIs
packages/
  rules_engine/     Zen adapter: evaluate / entitlements / explain / testgen
  rules_schema/     Pack envelope schema (platform metadata + JDM)
docs/
  PRODUCT.md
  ARCHITECTURE.md
```

## Prerequisites

- Node.js 20+ and [pnpm](https://pnpm.io/)
- Python 3.11+ (venv recommended)

## Quick start

```bash
make install-py    # venv + engine + API (+ zen-engine)
make install-web   # pnpm deps for Next.js (+ @gorules/jdm-editor)
```

In two terminals:

```bash
make api           # http://localhost:8000  (OpenAPI at /docs)
make web           # http://localhost:3000  (Axiom UI)
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/rules_engine -e apps/api
PYTHONPATH=packages/rules_engine/src:apps/api/src \
  uvicorn rules_api.main:app --reload \
    --reload-dir apps/api --reload-dir packages/rules_engine \
    --host 127.0.0.1 --port 8000

pnpm install && pnpm dev:web
```

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000` via `apps/web/.env.local`.

### Database

SQLite is the default PoC store (`apps/api/data/rules.db`).

- Optional `DATABASE_URL`:
  - `sqlite:///path/to.db` — use that SQLite file
  - `postgres://` / `postgresql://` — **planned**; PoC warns and falls back to SQLite
- Multi-tenant stub: pass `tenant_id` (default `default`) on requests; columns are present on packs, releases, entitlements, and audit.

### Tests

```bash
make test
```

## API surface (Phases 0–3)

### Runtime

| Method | Path | Notes |
|--------|------|--------|
| `POST` | `/v1/evaluate` | Decision + effects + Zen/platform trace; optional entitlement commit; canary-aware |
| `POST` | `/v1/explain` | Same body as evaluate → human-readable reasons |
| `POST` | `/v1/simulate` | Fixtures against a pack version; optional `compare_to_version` diff |
| `POST` | `/v1/testgen` | Deterministic permutation cases from JDM table inputs (default max 50, hard max 500) |
| `GET` | `/v1/entitlements?subject_id=` | Optional `grandfathered=true\|false` filter |
| `GET` | `/v1/audit/{evaluation_id}` | Single evaluation |
| `GET` | `/v1/audit?subject_id=` | Search |
| `GET` | `/v1/compliance/export?subject_id=&domain=` | Audit + entitlements JSON export |

### Design-time packs & releases

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/v1/packs/{domain}` | List versions |
| `GET` | `/v1/packs/{domain}/{pack_id}/versions/{version}` | Full JDM pack payload |
| `POST` | `/v1/packs/{domain}/{pack_id}/versions` | Create draft (`payload` or `clone_from_version`) |
| `PUT` | `/v1/packs/{domain}/{pack_id}/versions/{version}` | Update **draft** only |
| `POST` | `/v1/packs/{domain}/{pack_id}/versions/{version}/transition` | Lifecycle; `change_record_id` required → `published` |
| `POST` | `/v1/packs/{domain}/{pack_id}/promote` | Cutover release pointer; production needs `change_record_id` |
| `GET`/`PUT` | `/v1/releases/{domain}/{pack_id}` | Environment, pack_version, canary_%, canary_version, go_live_at |

### RBAC stub

Optional header `X-Role: viewer|author|approver|admin`.

- Missing header → unrestricted (PoC default)
- Promote / transition / release PUT → `approver` or `admin`
- Draft create/update → `author`, `approver`, or `admin`

### Try it

```bash
# Explain
curl -s localhost:8000/v1/explain -H 'content-type: application/json' \
  -d '{"subject_id":"FF-1","facts":{"membership":{"tier":"gold"}}}' | jq .

# Simulate
curl -s localhost:8000/v1/simulate -H 'content-type: application/json' \
  -d '{"fixtures":[{"subject_id":"FF-1","facts":{"membership":{"tier":"gold"}}}]}' | jq .

# Testgen
curl -s localhost:8000/v1/testgen -H 'content-type: application/json' \
  -d '{"max_cases":10}' | jq .

# Compliance export
curl -s 'localhost:8000/v1/compliance/export?subject_id=FF-GRANDFATHERED&domain=lounge' | jq .
```

## Vertical slice (lounge)

- JDM decision table → allow/deny + companion grants (executed by Zen)
- Seasonal silver deny uses `as_of` date cells (`>= date('2099-01-01') …`)
- Subject `FF-GRANDFATHERED` honors a pre-seeded entitlement without needing the old graph live
- Deny-wins conflict policy across collected table matches
- Canary: when `canary_percent < 100` and `canary_version` is set, a stable hash of `subject_id` selects canary vs production
- Every evaluation is searchable under **Audit** by subject id

## Docs

- [Product vision](docs/PRODUCT.md)
- [Architecture & state model](docs/ARCHITECTURE.md)
