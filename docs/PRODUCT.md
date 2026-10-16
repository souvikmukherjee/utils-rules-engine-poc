# Product vision

## Thesis

A **domain-agnostic decision platform**: business users author versioned **JSON Decision Models**; [GoRules Zen](https://docs.gorules.io/) evaluates them deterministically; Axiom wraps that engine with change management, simulation, grandfathering, canary, and searchable audit.

Opinionated enough that misuse is hard; configurable enough for lounge eligibility, banking, telco, and retail via **domains + fact schemas**, not a custom engine per industry.

## Why not a custom rules engine?

Building a production-grade evaluator (decision tables, expressions, traces, tooling) is a product unto itself. We adopt **GoRules Zen** (open source) and the **JDM** format, then invest in the product layer Zen does not provide: lifecycle, entitlements, releases, and a beautiful authoring UX.

## Motivating use case

Lounge access today is often encoded in Drools-style rules: tier → lounge, partner elite status, one-off access, +1 companion, and so on. The same patterns appear as home-loan pricing, mobile-bundle discounts, and retail offers. Those become JDM decision graphs with decision tables and expressions.

## Capabilities (roadmap)

### Design time

- **Authoring** — embedded [GoRules JDM Editor](https://docs.gorules.io/developers/jdm/jdm-editor) (graph + decision tables)
- **Approval** — draft → review → approved → published
- **Simulation** — run packs against fixtures at arbitrary `as_of` dates; diff versions
- **Auto testgen** — deterministic permutation cases from decision-table input cells
- **Push / promote** — change-record gate before production
- **Schedule** — `go_live_at` on releases
- **Virtual canary** — target N% of subjects by stable hash; ramp incrementally

### Runtime

- **Evaluate** — facts in → decision + effects + Zen trace + platform path
- **Entitlements** — durable grants (companion packs, offers) stored in a ledger for grandfathering
- **Audit search** — “what happened to this frequent flyer / loan / MSISDN?”

## State model (summary)

Three orthogonal axes (see [ARCHITECTURE.md](ARCHITECTURE.md)):

1. **Lifecycle** — draft / published / retired on pack versions (platform)
2. **Temporal** — `as_of` in Zen context; date comparisons in JDM cells
3. **Subject-bound** — entitlement ledger for grandfathering (platform)

## Product principles

- **Engine is Zen; product is Axiom** — no bespoke condition IR
- Business-user safe: typed effect mapping, deny-wins conflict policy, immutable published versions
- Compliance-first: append-only audit; every entitlement honor and matched row recorded
