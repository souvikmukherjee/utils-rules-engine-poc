## What changed

<!-- Summarise the change and why it is needed. -->

## Affected components

- [ ] `apps/api` (FastAPI platform)
- [ ] `apps/web` (Next.js UI)
- [ ] `apps/kogito` (Kogito/DMN engine)
- [ ] `apps/spring-compare` (Spring comparison harness)
- [ ] `packages/rules_engine` (Zen adapter)
- [ ] CI / security / repo config

## How it was verified

<!-- Commands run, e.g. `make test`, `make test-spring-compare`, `pnpm build:web`. -->

## Security checklist

- [ ] No credentials, tokens, or real customer data are added (the gitleaks scan covers committed history, not intent).
- [ ] New or changed dependencies are needed and come from a trusted source.
- [ ] Any new CodeQL or dependency review finding is fixed, or dismissed with a reason.
