# Security policy

## Scope

This repository is a public proof of concept for a rules engine platform (GoRules
Zen plus a parallel Kogito/DMN engine). It is not a released product and has no
supported versions: only the tip of `main` is maintained.

The PoC is not hardened for production use. In particular, the API uses
header-based role simulation for RBAC and ships sample data; do not deploy it as-is
with real data or credentials.

## Reporting a vulnerability

Report suspected vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/souvikmukherjee/utils-rules-engine-poc/security/advisories/new)
rather than opening a public issue.

Please include the affected component (`apps/api`, `apps/web`, `apps/kogito`,
`apps/spring-compare`, or `packages/rules_engine`), reproduction steps, and the
impact you observed. You should get an initial response within a week; because
this is a PoC maintained on a best-effort basis, fixes are not on a fixed
schedule.

## Exposed secrets

If you find a credential committed to this repository, report it privately as
above and do not open a public issue. Any secret that reached a public commit
must be treated as compromised and rotated, even after the commit is removed:
Git history and forks keep copies.

## Automated checks

Every pull request runs:

- **CodeQL** (`.github/workflows/codeql.yml`) for code vulnerabilities in Python,
  TypeScript, Java, and the GitHub Actions workflows themselves.
- **Gitleaks** (`.github/workflows/secret-scan.yml`) over the full commit history
  for hard-coded secrets.
- **Dependency review** (`.github/workflows/dependency-review.yml`), which blocks
  dependency changes that introduce known vulnerabilities of moderate severity or
  higher.

GitHub secret scanning with push protection, Dependabot alerts, and Dependabot
security updates are enabled at the repository level. See
[docs/BRANCH-PROTECTION.md](../docs/BRANCH-PROTECTION.md) for the branch protection
rules that make these checks blocking.

