# Architecture

## Boundaries

| Layer | Responsibility |
|-------|----------------|
| `apps/web` | Authoring / sim / audit UX — never embeds eval logic |
| `apps/api` | Auth hooks, persistence, promotion, entitlement commits |
| `packages/rules_engine` | Pure evaluate: temporal filter, conditions, effects, traces, explain, testgen |
| `packages/rules_schema` | Shared JSON Schema for rule packs |

## Rule state — three axes

### 1. Lifecycle (governance)

On **RulePackVersion** / **Release**: `draft` → `in_review` → `approved` → `published` → `retired`.

Published versions are **immutable**. Edits create a new version.

Transition to `published` (and production promote) requires a `change_record_id`.

### 2. Temporal window

On each **Rule** (and optionally **Release**):

- `effective_from` (required once published)
- `effective_to` (optional; open-ended if null)
- Evaluation clock: `as_of` (default now; simulation may override)

A rule is a candidate only if `effective_from <= as_of < effective_to` (or no end). Otherwise the trace records `skipped_reason: outside_effective_window`.

### 3. Entitlement ledger (grandfathering)

Do **not** keep retired rule text alive for special subjects.

When an effect grants something durable (`persist_as_entitlement: true`), the API appends an **Entitlement** row. Later evaluations honor active entitlements before (or alongside) current pack rules.

Default promote policy: **cutover** for new subjects; **honor existing entitlements** for holders.

## Evaluate order

1. Resolve release for environment; if `canary_percent < 100` and `canary_version` is set, stable-hash `subject_id` into a 0–99 bucket and pick canary vs production version
2. Load active entitlements for `subject_id` as of `as_of` (scoped by `tenant_id`)
3. If an entitlement covers the decision → trace `entitlement_honored`
4. Evaluate current pack (temporally filtered; priority order)
5. Conflict policy: collect matching effects; **deny-wins**
6. If grant effects fire and `commit_entitlements` → append ledger rows

## Conflict policy (v1)

Collect matching effects; **deny-wins** if any deny effect is present.

## Stores

Persistence is behind `RulesStore` (`apps/api/src/rules_api/store.py`). Default implementation: **SQLite** (`SqliteRulesStore`).

| Store | Mutability | Contents |
|-------|------------|----------|
| Pack definitions | Append versions | Rules, windows, priorities, effects |
| Release pointers | Updated on promote | Which pack serves env / canary % / canary_version |
| Entitlement ledger | Append + status transitions | Subject-bound grants |
| Audit | Append-only | Every evaluation + path taken |

### Multi-tenancy (PoC stub)

All meaningful tables carry `tenant_id` (default `default`). Evaluate, entitlements, audit, packs, and releases accept `tenant_id` on the request body or query string.

### `DATABASE_URL`

| Value | Behaviour |
|-------|-----------|
| unset | SQLite at `apps/api/data/rules.db` |
| `sqlite:///…` | That SQLite file |
| `postgres://` / `postgresql://` | **Planned** — PoC emits a warning and keeps SQLite |

## RBAC stub

Optional header `X-Role: viewer | author | approver | admin`.

- Absent → unrestricted (local PoC)
- Promote / lifecycle transition / release PUT → `approver` or `admin`
- Draft pack create/update → `author+`

## API surface (Phases 0–3)

### Runtime

- `POST /v1/evaluate`
- `POST /v1/explain`
- `POST /v1/simulate`
- `POST /v1/testgen` — max_cases default 50, hard max 500
- `GET /v1/entitlements?subject_id=` (+ optional `grandfathered`)
- `GET /v1/audit/{evaluation_id}`
- `GET /v1/audit?subject_id=`
- `GET /v1/compliance/export?subject_id=&domain=`

### Design-time

- `GET /v1/packs/{domain}`
- `GET /v1/packs/{domain}/{pack_id}/versions/{version}`
- `POST /v1/packs/{domain}/{pack_id}/versions`
- `PUT /v1/packs/{domain}/{pack_id}/versions/{version}` (draft only)
- `POST /v1/packs/{domain}/{pack_id}/versions/{version}/transition`
- `POST /v1/packs/{domain}/{pack_id}/promote`
- `GET` / `PUT /v1/releases/{domain}/{pack_id}`
