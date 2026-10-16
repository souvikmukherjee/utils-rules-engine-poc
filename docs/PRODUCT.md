# Product vision

## Thesis

A **domain-agnostic decision platform**: business users author versioned rule packs; the engine evaluates facts deterministically; every decision is fully explainable and searchable.

Opinionated enough that misuse is hard; configurable enough for lounge eligibility, banking, telco, and retail via **domains + fact schemas**, not a custom engine per industry.

## Motivating use case

Lounge access today is often encoded in Drools-style rules: tier → lounge, partner elite status, one-off access, +1 companion, and so on. The same patterns appear as home-loan pricing, mobile-bundle discounts, and retail offers.

## Capabilities (roadmap)

### Design time

- **Authoring** — forms and decision tables that compile to a shared rule IR
- **Approval** — draft → review → approved → published
- **Simulation** — run packs against fixtures at arbitrary `as_of` dates; diff versions
- **Auto testgen** — deterministic permutation cases from discrete condition values
- **Push / promote** — change-record gate before production
- **Schedule** — `go_live_at` on releases
- **Virtual canary** — target N% of subjects by stable hash; ramp incrementally

### Runtime

- **Evaluate** — facts in → decision + effects + full **decision trace**
- **Entitlements** — durable grants (companion packs, offers) stored in a ledger for grandfathering
- **Audit search** — “what happened to this frequent flyer / loan / MSISDN?”

## State model (summary)

Three orthogonal axes (see [ARCHITECTURE.md](ARCHITECTURE.md)):

1. **Lifecycle** — draft / published / retired on pack versions
2. **Temporal** — `effective_from` / `effective_to` on rules
3. **Subject-bound** — entitlement ledger for grandfathering

## Product principles

- Lightweight and highly configurable, but **highly opinionated** (no arbitrary scripts in v1)
- Business-user safe: typed effects, deny-wins conflict policy, immutable published versions
- Compliance-first: append-only audit; every skip/match reason recorded
