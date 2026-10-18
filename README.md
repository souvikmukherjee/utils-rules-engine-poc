# Axiom

**Beautiful governance on [GoRules Zen](https://docs.gorules.io/)** — with a parallel **[Kogito](https://kie.apache.org/docs/)** (DMN) runtime behind the same UI toggle.

Axiom is a domain-agnostic decision platform. Business users author versioned **JSON Decision Models (JDM)** in a visual graph editor. Zen evaluates them deterministically; optionally flip the header toggle to redirect evaluation to Kogito. Axiom wraps the engine with what product teams actually need: personas and roles, multi-domain packs, simulation, change records, canary releases, grandfathered entitlements, and searchable audit.

We do **not** invent another rules interpreter. We productize an open-source one.

---

## 🤖 For AI Agents (Cursor / Claude)

**Setting up from a git URL?** → Read **[AGENT_SETUP.md](AGENT_SETUP.md)** first.

This repository includes comprehensive skills for running and debugging code from scratch:
- **[.cursor/skills/run-code/SKILL.md](.cursor/skills/run-code/SKILL.md)** - Environment setup, execution (8+ languages)
- **[.cursor/skills/debug-execution/SKILL.md](.cursor/skills/debug-execution/SKILL.md)** - Systematic debugging and troubleshooting

---

## Product at a glance

| Design time | Runtime |
|-------------|---------|
| Visual JDM graphs + decision tables | Facts in → decision + effects + full trace |
| Draft → review → approve → publish | Entitlement ledger (grandfathering) |
| Simulate & diff pack versions | Virtual canary by subject hash |
| Change-record gate to production | Append-only audit & compliance export |

**Same platform, many industries.** Airline lounge access today; home-loan pricing tomorrow — swap the domain and the graph, not the engine.

<p align="center">
  <img src="docs/assets/jdm-graph-lounge.webp" alt="Lounge JDM decision graph in Author" width="900" />
</p>
<p align="center"><em>Author · Graph — lounge access decision model (Request → Normalize → Decision table → Response)</em></p>

---

## Tour the product

### 1. Personas & domains

Switch who you are and what you own. Authors only see domains they’re allowed to touch; approvers and admins promote; viewers audit.

<p align="center">
  <img src="docs/assets/persona-maya-domains.webp" alt="Persona and domain workspace bar" width="900" />
</p>

| Persona | Role | Domains |
|---------|------|---------|
| Maya Chen | Author | Loyalty, Lounge |
| James Okonkwo | Approver | Airline ops, Airports |
| Priya Nair | Admin | Lounge, Loyalty, Airports |
| Tom Barrett / Sofia Alvarez | Author / Approver | Banking · credit |
| Alex Kim | Viewer | All (read-only) |

Seeded domains: **Loyalty · Lounge access · Airline operations · Airports · Banking · credit**.

---

### 2. Decision framework (business view)

For lounge access, eligibility is a **tier × cabin** matrix across four lounge types: Chairman’s, First, Business, Qantas Club. Cabin can unlock above tier (Bronze flying First → First Lounge). Tier can unlock above cabin (Platinum flying Economy → Business Lounge).

<p align="center">
  <img src="docs/assets/lounge-decision-matrix.webp" alt="Colour-coded lounge eligibility matrix" width="900" />
</p>

| Tier \\ Cabin | Economy | Premium Economy | Business | First |
|---------------|---------|-----------------|----------|-------|
| Bronze | — | — | Qantas Club | **First** |
| Silver | — | Club | Business | First |
| Gold | Club | Club | Business | First |
| Platinum | **Business** | Business | First | First |
| Platinum One | **Chairman's** | Chairman's | Chairman's | Chairman's |

---

### 3. Evaluate with full traces

Pick a scenario, run Zen, see decision + lounge outcome + matched rule rows.

<p align="center">
  <img src="docs/assets/bronze-first-lounge.webp" alt="Bronze flying First evaluates to First Lounge" width="900" />
</p>
<p align="center"><em>Bronze · First cabin → Allow · First Lounge</em></p>

<p align="center">
  <img src="docs/assets/platinum-economy-business.webp" alt="Platinum flying Economy evaluates to Business Lounge" width="900" />
</p>
<p align="center"><em>Platinum · Economy → Allow · Business Lounge</em></p>

Banking uses the same Evaluate UX — different graph, same runtime:

<p align="center">
  <img src="docs/assets/banking-prime.webp" alt="Banking prime rate band evaluation" width="900" />
</p>

---

### 4. Author · JDM graphs & tables

Open **Author · Graph** for the GoRules editor. Drag nodes, connect edges, open a decision-table node for the spreadsheet.

<p align="center">
  <img src="docs/assets/jdm-table-lounge.webp" alt="Lounge decision table spreadsheet" width="900" />
</p>
<p align="center"><em>Lounge decision table — tier, cabin, partner elite → lounge type</em></p>

<p align="center">
  <img src="docs/assets/jdm-graph-banking.webp" alt="Banking home-loan JDM graph" width="900" />
</p>
<p align="center"><em>Banking · credit — Application → Home loan rate band → Offer</em></p>

<p align="center">
  <img src="docs/assets/jdm-graph-loyalty.webp" alt="Loyalty tier review JDM graph" width="900" />
</p>
<p align="center"><em>Loyalty — Member year → Tier review → Outcome</em></p>

Published packs are **immutable**. Clone to draft → edit → submit for review → approve → publish with a change record.

---

### 5. Grandfathering & audit

Durable grants live in an entitlement ledger. Retired rule text is never kept alive for special subjects — the ledger is.

<p align="center">
  <img src="docs/assets/audit-grandfathered.webp" alt="Audit search with grandfathered entitlements" width="900" />
</p>

---

### 6. Scale benchmark

Open **Benchmark** to fire synthetic packs (100 / 1k / 10k rules × 1k / 10k / 1M fires) through Zen and a DMN-style FIRST table on identical generated variables and outcomes. Results are stored so the objective comparison is visible on every reload; change parameters and re-run anytime.

How-to: [docs/HOWTO-BENCHMARK.md](docs/HOWTO-BENCHMARK.md).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Axiom UI (Next.js)                                         │
│  Personas · Domains · Evaluate · Author (JDM Editor) ·      │
│  Simulate · Compare · Benchmark · Releases · Audit          │
└───────────────────────────┬─────────────────────────────────┘
                            │  /api → FastAPI
┌───────────────────────────▼─────────────────────────────────┐
│  Platform API                                               │
│  Lifecycle · change records · canary · entitlements · audit │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  rules_engine adapter                                       │
│  Inject as_of · call Zen · map matches → effects ·          │
│  honor entitlements · deny-wins · explain · testgen         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  GoRules Zen  ←  JSON Decision Model (nodes + edges)        │
└─────────────────────────────────────────────────────────────┘
```

### Three orthogonal state axes

1. **Lifecycle** (platform) — `draft → in_review → approved → published → retired`
2. **Temporal** (JDM) — `as_of` in context; date cells like `>= date('2099-01-01')`
3. **Subject-bound entitlements** (platform) — grandfathering via ledger, not zombie rules

### Pack envelope

Zen only needs `nodes` and `edges`. Axiom stores governance beside them:

```json
{
  "domain": "lounge",
  "pack_id": "lounge-access",
  "version": "2.0.0",
  "lifecycle": "published",
  "nodes": [ /* JDM */ ],
  "edges": [ /* JDM */ ]
}
```

### Monorepo

```
apps/
  web/                 Next.js 15 — Axiom UI + @gorules/jdm-editor + Zen|Kogito toggle
  api/                 FastAPI — design-time + runtime APIs (`engine: zen|kogito`)
  kogito/              Quarkus + drools-quarkus-decisions — LoungeAccess DMN :8081
packages/
  rules_engine/        Zen adapter (evaluate / explain / testgen)
  rules_schema/        Pack JSON Schema
docs/
  PRODUCT.md           Product vision
  ARCHITECTURE.md      Deep architecture
  HOWTO-BENCHMARK.md   Scale benchmark how-to (100/1k/10k × 1k/10k/1M)
  assets/              Screenshots for this README
```

Deeper reading: [Product vision](docs/PRODUCT.md) · [Architecture](docs/ARCHITECTURE.md) · [Benchmark how-to](docs/HOWTO-BENCHMARK.md)

---

## Developer how-to

### Prerequisites

- Node.js **20+** and [pnpm](https://pnpm.io/) 9+
- Python **3.11+**
- Java **17+** and Maven **3.9+** (only needed for the parallel Kogito DMN service)

### Install

```bash
make install-py              # venv + rules_engine + API + zen-engine
make install-web             # pnpm deps (Next + JDM editor)
make install-kogito          # package apps/kogito Quarkus service
make install-spring-compare  # package Spring Boot Zen↔Kogito compare harness
```

### Run

```bash
make kogito           # http://127.0.0.1:8081  — Kogito LoungeAccess DMN
make api              # http://127.0.0.1:8000  — OpenAPI at /docs
make web              # http://127.0.0.1:3000  — Axiom UI (toggle Zen | Kogito)
make spring-compare   # http://127.0.0.1:8082  — Spring: call Zen then Kogito, compare
```

Manual equivalent:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/rules_engine -e apps/api
PYTHONPATH=packages/rules_engine/src:apps/api/src \
  uvicorn rules_api.main:app --reload \
    --reload-dir apps/api --reload-dir packages/rules_engine \
    --host 127.0.0.1 --port 8000

pnpm install && pnpm dev:web
```

### First five minutes in the UI

1. Open [http://127.0.0.1:3000](http://127.0.0.1:3000)
2. Pick persona **Priya Nair** · domain **Lounge access**
3. **Evaluate** — try *Bronze · First cabin* and *Platinum · Economy*
4. **Author · Graph** — open the lounge graph; click **Edit Table** on the decision-table node
5. Switch persona to **Tom Barrett** · domain **Banking · credit** — same product, different graph

### Scale benchmark (optional)

Compare **Zen** vs a **DMN-style FIRST table** on synthetic packs (generated variables + outcomes), persist results, and load an objective table in the UI.

```bash
make api && make web
make benchmark-matrix   # seed SQLite + artifacts/engine-comparison/benchmark_matrix_seed.json
```

Then open **Benchmark** at [http://127.0.0.1:3000](http://127.0.0.1:3000):

| Axis | Presets |
|------|---------|
| Rules | 100 · 1,000 · 10,000 |
| Fires | 1,000 · 10,000 · 1,000,000 |
| Columns | tunable (default 10) |

Anyone can change columns / rules / fires / seed / `max_work` and click **Run custom cell**, or run **Quick** / **Full matrix**. Results stay in SQLite (`benchmark_runs`) so reload still shows the comparison.

Full walkthrough (API, storage, reading the table, work caps): **[docs/HOWTO-BENCHMARK.md](docs/HOWTO-BENCHMARK.md)**.

```bash
# Objective table the UI loads
curl -s localhost:8000/v1/benchmark/compare | jq '.summary'

# Custom parameters
curl -s localhost:8000/v1/benchmark/run -H 'content-type: application/json' \
  -d '{"column_count":12,"rule_count":250,"fire_count":2000,"seed":99}' | jq .
```

### Tests

```bash
make test                 # Python (rules_engine + API)
make test-spring-compare  # Spring Boot compare harness
```

### CI & security checks

Every pull request against `main` runs the test suites above plus CodeQL (Python,
TypeScript, Java, and the workflows themselves), a gitleaks scan of the commit
history, and dependency review. `main` is protected by a ruleset checked into
[`.github/rulesets/`](.github/rulesets/) — see
[`docs/BRANCH-PROTECTION.md`](docs/BRANCH-PROTECTION.md) for what it enforces and
how to apply it. Report vulnerabilities privately per
[`.github/SECURITY.md`](.github/SECURITY.md).

### Spring Boot engine bake-off

`apps/spring-compare` is a small Spring Boot app that calls **Zen then Kogito** (via the FastAPI platform, or Kogito directly) and reports wall latency, decision agreement, and notes on ease of implementation / hot reload.

```bash
make kogito & make api & make spring-compare
curl -s localhost:8082/v1/compare/health | jq .
curl -s localhost:8082/v1/compare -H 'content-type: application/json' -d '{}' | jq .diff
curl -s localhost:8082/v1/compare/notes | jq .dimensions
```

Details: [`apps/spring-compare/README.md`](apps/spring-compare/README.md).

### Useful API calls

```bash
# Catalog (domains, personas, lounge matrix)
curl -s localhost:8000/v1/catalog | jq .

# Explain a gold member in economy (defaults cabin via normalize)
curl -s localhost:8000/v1/explain -H 'content-type: application/json' \
  -d '{"subject_id":"FF-1","domain":"lounge","pack_id":"lounge-access",
       "facts":{"membership":{"tier":"gold"},"booking":{"cabin":"economy"}}}' | jq .

# Bronze flying First → First Lounge
curl -s localhost:8000/v1/evaluate -H 'content-type: application/json' \
  -d '{"subject_id":"FF-BRONZE-F","domain":"lounge","pack_id":"lounge-access",
       "facts":{"membership":{"tier":"bronze"},"booking":{"cabin":"first"}}}' | jq '.decision,.effects'

# Banking prime band
curl -s localhost:8000/v1/evaluate -H 'content-type: application/json' \
  -d '{"subject_id":"LN-1","domain":"banking_credit","pack_id":"home-loan-pricing",
       "facts":{"loan":{"lvr":0.7,"product":"owner_occupier"},
                "applicant":{"credit_score":790}}}' | jq .

# Compliance export for a grandfathered subject
curl -s 'localhost:8000/v1/compliance/export?subject_id=FF-GRANDFATHERED&domain=lounge' | jq .
```

### RBAC stub

Optional header `X-Role: viewer | author | approver | admin`.

| Action | Minimum role |
|--------|----------------|
| Evaluate / simulate / audit | any (or unrestricted if header absent) |
| Draft create / update | author+ |
| Approve / publish / promote | approver / admin |
| Publish & production promote | also requires `change_record_id` |

In the UI, the selected **persona** sets `X-Role` and filters domains.

### Database

SQLite by default (`apps/api/data/rules.db`). Optional `DATABASE_URL`:

| Value | Behaviour |
|-------|-----------|
| unset / `sqlite:///…` | Local SQLite |
| `postgres://…` | Planned — PoC warns and stays on SQLite |

---

## API surface (summary)

### Runtime

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/evaluate` | Decision + effects + Zen/platform trace |
| `POST` | `/v1/compare` | Zen then Kogito — decisions + wall timings |
| `POST` | `/v1/explain` | Human-readable reasons |
| `POST` | `/v1/simulate` | Fixture batch; optional version diff |
| `POST` | `/v1/testgen` | Permutation cases from table inputs |
| `GET` | `/v1/entitlements` | Subject ledger (`grandfathered` filter) |
| `GET` | `/v1/audit` · `/v1/audit/{id}` | Search / fetch |
| `GET` | `/v1/compliance/export` | Audit + entitlements dump |

### Benchmark (scale lab)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/benchmark/compare` | Objective table from persisted runs |
| `GET` | `/v1/benchmark/runs` · `/v1/benchmark/runs/{id}` | List / fetch runs |
| `POST` | `/v1/benchmark/run` | Custom cell (columns × rules × fires) |
| `POST` | `/v1/benchmark/matrix` | Preset grid; skip over `max_work` |
| `DELETE` | `/v1/benchmark/runs/{id}` | Delete a run (`X-Role: author+`) |

See [docs/HOWTO-BENCHMARK.md](docs/HOWTO-BENCHMARK.md).

### Design-time

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/catalog` | Domains, personas, frameworks |
| `GET/POST/PUT` | `/v1/packs/...` | List / draft / update JDM packs |
| `POST` | `.../transition` | Lifecycle transitions |
| `POST` | `.../promote` | Cutover / canary release pointer |
| `GET/PUT` | `/v1/releases/...` | Environment release config |

Full OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when the API is running.

---

## Why Zen + Axiom

| Build ourselves | Adopt Zen + build Axiom |
|-----------------|-------------------------|
| Condition IR, tables, expressions, traces | Already solved in GoRules Zen |
| Visual authoring | `@gorules/jdm-editor` |
| Governance, entitlements, canary, audit | **This product** |

Axiom’s bet: the engine is commodity; **trustworthy change** is the product.

---

## License & status

PoC for exploring multi-domain decision governance. Not production-hardened (SQLite, stub RBAC, seeded personas). Contributions and forks welcome as experiments.

---

<p align="center">
  <strong>Axiom</strong> — Decisions you can explain. Rules you can trust.<br/>
  <sub>Powered by GoRules Zen · JSON Decision Model</sub>
</p>
