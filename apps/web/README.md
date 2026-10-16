# Axiom web (`@rules/web`)

Next.js UI for the Rules Engine Platform PoC. Talks to the FastAPI service at
`NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Sections

| Tab | Purpose |
|-----|---------|
| **Evaluate** | Runtime playground — subject + facts → decision + trace |
| **Author** | List pack versions, edit draft rules, lifecycle transitions |
| **Simulate** | Fixture batches, testgen, optional explain |
| **Releases** | `go_live_at`, canary %, promote with change record |
| **Audit** | Entitlement browser (grandfathered highlighted) + evaluation history |

Gated actions send `X-Role: author|approver|admin` (role selector on Author /
Simulate / Releases).

## Dev

```bash
# from monorepo root
pnpm --filter @rules/web dev
```

Build check:

```bash
pnpm --filter @rules/web build
```

If an API route is not ready yet, panels surface the HTTP error without crashing.
