# Branch protection and security checks

This repository is public, so anything merged to `main` is visible to everyone and
anything ever committed stays recoverable from history and forks. The guard rails
below are split in two: the automated checks live in `.github/workflows/`, and the
rules that make them blocking live in `.github/rulesets/` and have to be pushed to
GitHub once by a repository admin.

## 1. Automated checks on every pull request

| Check (status check name) | Workflow | What it blocks |
| --- | --- | --- |
| `CodeQL analyze (python)`, `(javascript-typescript)`, `(java-kotlin)`, `(actions)` | `codeql.yml` | Code vulnerabilities (injection, path traversal, unsafe deserialization, workflow misuse) using the `security-extended` query suite |
| `Gitleaks secret scan` | `secret-scan.yml` | Hard-coded credentials anywhere in the commit history reachable from the PR |
| `Dependency review` | `dependency-review.yml` | Dependency changes that pull in a known vulnerability of moderate severity or higher |
| `Python tests`, `Web lint and build`, `Java build (kogito)`, `Java build (spring-compare)` | `ci.yml` | Functional regressions across the four buildable components |

Supporting details:

- **CodeQL** also runs weekly on `main`, so newly published queries are applied to
  code that has not changed. Results land in the Security > Code scanning tab.
- **Gitleaks** runs a pinned release (verified by SHA-256 checksum) rather than a
  floating action tag, scans the full history with `--redact` so matches are never
  echoed into public logs, and uploads SARIF to code scanning. If it reports a
  false positive, add a scoped allowlist to a `.gitleaks.toml` at the repo root
  (with `[extend] useDefault = true`) rather than disabling the job.
- **Actions are pinned to commit SHAs** with the version in a trailing comment. A
  tag can be moved to point at malicious code; a commit SHA cannot. Dependabot's
  `github-actions` ecosystem keeps the pins current.
- **Workflow tokens are read-only**: every workflow declares `permissions:
  contents: read` at the top level and only the scanning jobs widen it to
  `security-events: write`.

A finding that is already public in Git history is not fixed by deleting the
commit. Rotate the credential first; then clean up history if you want to.

## 2. Branch protection ruleset

Two profiles are checked in. They are identical except for review requirements:

- `.github/rulesets/main-strict.json` — one approving review from a code owner,
  stale approvals dismissed on push, and the final push must be approved by
  someone else. Use this as soon as there is more than one maintainer.
- `.github/rulesets/main-solo.json` — the same rules with zero required
  approvals. GitHub does not let you approve your own pull request, so with a
  single maintainer the strict profile makes `main` unmergeable without an
  admin bypass. The solo profile keeps the pull request flow, the required
  checks, and the push restrictions, and only drops the human approval.

Both profiles apply to the default branch (`~DEFAULT_BRANCH`) with an empty
`bypass_actors` list, which means the rules apply to the repository owner too.

| Rule | Effect |
| --- | --- |
| `pull_request` | No direct pushes to `main`; changes land through a pull request, conversations must be resolved, and only squash merges are allowed |
| `required_status_checks` with `strict_required_status_checks_policy` | All ten checks above must pass, and the branch must be up to date with `main` before merging, so checks run against the code that will actually land |
| `code_scanning` | Blocks merging while CodeQL reports an open alert of high severity or higher, or any error-level alert — this is what makes the vulnerability scan a gate rather than a notification |
| `required_linear_history` | No merge commits; combined with squash-only merges, `main` stays a straight line |
| `non_fast_forward` | No force pushes, so history on `main` cannot be rewritten |
| `deletion` | `main` cannot be deleted |

## 3. Applying it

Branch protection is server-side state, so the checked-in JSON has to be pushed
to GitHub. Run this once, with a token that has admin rights on the repository:

```bash
# Preview every API call without changing anything.
scripts/apply_branch_protection.sh --dry-run

# Apply (choose the profile that matches your reviewer situation).
scripts/apply_branch_protection.sh --profile solo
```

Do this **after** this change has merged and the workflows have run on `main`
at least once. Required status checks are matched by name: if a name in the
ruleset never gets reported, pull requests wait on it forever. Verify the names
line up with what GitHub actually saw:

```bash
scripts/apply_branch_protection.sh --list-checks
```

The script is idempotent — it updates the ruleset in place if one with the same
name already exists — and it also applies the repository-level settings that
branch protection alone does not cover:

- Secret scanning with **push protection**, which rejects a push containing a
  recognised credential before it ever reaches the public history. This is the
  layer that prevents leaks; gitleaks in CI is the layer that catches what push
  protection's provider patterns miss.
- Dependabot alerts and Dependabot security updates.
- Private vulnerability reporting, so researchers have a non-public channel (see
  `.github/SECURITY.md`).
- A read-only default `GITHUB_TOKEN` for Actions, with workflow approval of pull
  request reviews disabled.
- Required approval before workflows run on pull requests from external
  contributors, which stops a drive-by fork PR from running arbitrary CI.
- Squash-only merges with `main` auto-deleting merged branches.

Steps marked `skipped` in the output are settings that are not available for this
repository or token (for example secret scanning validity checks, which need
GitHub Advanced Security); set those in Settings > Code security if you want them.

## Optional hardening

Not enabled by default because of the day-to-day friction, but worth considering:

- **Require signed commits.** Add `{"type": "required_signatures"}` to the rules
  array in the ruleset. Every commit then needs a verified signature, which means
  configuring commit signing on each machine and tool that pushes here (including
  any automation).
- **Restrict who can push to the repository.** For a personal repo, keep write
  access to the owner and let everyone else contribute through forks.
- **Tag protection.** Add a second ruleset with `"target": "tag"` once releases
  are tagged.
