#!/usr/bin/env bash
#
# Apply the repository's branch protection ruleset and security settings.
#
# Branch protection cannot live purely in the repo: GitHub stores it server side.
# This script pushes the checked-in ruleset (.github/rulesets/main-<profile>.json)
# plus the repository-level security settings through the GitHub API so the
# configuration stays reviewable in Git and reproducible.
#
# Requires: gh (authenticated with admin rights on the repo) and python3.
#
#   scripts/apply_branch_protection.sh --dry-run
#   scripts/apply_branch_protection.sh --profile strict
#   scripts/apply_branch_protection.sh --list-checks
#
set -euo pipefail

PROFILE=strict
REPO=""
DRY_RUN=false
MODE=apply
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage: scripts/apply_branch_protection.sh [options]

Options:
  --profile <strict|solo>  Ruleset profile to apply (default: strict).
                             strict: requires 1 code-owner approval on every PR.
                             solo:   same rules, but 0 approvals, for a repo with
                                     a single maintainer who cannot self-approve.
  --repo <owner/name>      Target repository (default: the current checkout).
  --dry-run                Print the API calls without changing anything.
  --list-checks            List the check names GitHub has seen on the default
                             branch, to verify required status check contexts.
  -h, --help               Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:?--profile needs a value}"
      shift 2
      ;;
    --repo)
      REPO="${2:?--repo needs a value}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --list-checks)
      MODE=list-checks
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$PROFILE" != strict && "$PROFILE" != solo ]]; then
  echo "Unknown profile '$PROFILE' (expected 'strict' or 'solo')." >&2
  exit 2
fi

for profile in strict solo; do
  if [[ ! -f "$REPO_ROOT/.github/rulesets/main-$profile.json" ]]; then
    echo "Missing ruleset file: $REPO_ROOT/.github/rulesets/main-$profile.json" >&2
    exit 1
  fi
done

for tool in gh python3; do
  command -v "$tool" >/dev/null || {
    echo "Required tool '$tool' is not installed." >&2
    exit 1
  }
done

gh auth status >/dev/null 2>&1 || {
  echo "gh is not authenticated. Run 'gh auth login' first." >&2
  exit 1
}

if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
fi

FAILED=()

send() { # send <METHOD> <endpoint> [json-body]
  local method="$1" endpoint="$2" body="${3-}"
  if [[ "$DRY_RUN" == true ]]; then
    printf '    would call %s /%s%s\n' "$method" "$endpoint" "${body:+ with a request body}"
    return 0
  fi
  if [[ -n "$body" ]]; then
    printf '%s' "$body" | gh api -X "$method" "$endpoint" --input - >/dev/null
  else
    gh api -X "$method" "$endpoint" >/dev/null
  fi
}

step() { # step <description> <command...>
  local description="$1" output
  shift
  printf '  %s ... ' "$description"
  if output="$("$@" 2>&1)"; then
    printf 'ok\n'
  else
    printf 'FAILED\n'
    FAILED+=("$description")
  fi
  [[ -n "$output" ]] && printf '%s\n' "$output" | sed 's/^/    /'
  return 0
}

optional_step() { # same as step, but a failure is only a warning
  local description="$1" output
  shift
  printf '  %s ... ' "$description"
  if output="$("$@" 2>&1)"; then
    printf 'ok\n'
  else
    printf 'skipped (unavailable for this repository or token)\n'
  fi
  [[ -n "$output" ]] && printf '%s\n' "$output" | sed 's/^/    /'
  return 0
}

merge_settings() {
  send PATCH "repos/$REPO" '{
    "allow_squash_merge": true,
    "allow_merge_commit": false,
    "allow_rebase_merge": false,
    "allow_auto_merge": true,
    "allow_update_branch": true,
    "delete_branch_on_merge": true,
    "squash_merge_commit_title": "PR_TITLE",
    "squash_merge_commit_message": "PR_BODY",
    "web_commit_signoff_required": true
  }'
}

secret_scanning() {
  send PATCH "repos/$REPO" '{
    "security_and_analysis": {
      "secret_scanning": { "status": "enabled" },
      "secret_scanning_push_protection": { "status": "enabled" }
    }
  }'
}

secret_scanning_extras() {
  send PATCH "repos/$REPO" '{
    "security_and_analysis": {
      "secret_scanning_validity_checks": { "status": "enabled" },
      "secret_scanning_non_provider_patterns": { "status": "enabled" }
    }
  }'
}

workflow_permissions() {
  send PUT "repos/$REPO/actions/permissions/workflow" '{
    "default_workflow_permissions": "read",
    "can_approve_pull_request_reviews": false
  }'
}

fork_pr_approval() {
  send PUT "repos/$REPO/actions/permissions/fork-pr-contributor-approval" '{
    "approval_policy": "all_external_contributors"
  }'
}

ruleset_file() {
  echo "$REPO_ROOT/.github/rulesets/main-$PROFILE.json"
}

json_name() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$1"
}

apply_ruleset() {
  local file name id
  file="$(ruleset_file)"
  name="$(json_name "$file")"
  id="$(gh api "repos/$REPO/rulesets" --paginate --jq ".[] | select(.name == \"$name\") | .id" | head -n1)"
  if [[ -n "$id" ]]; then
    send PUT "repos/$REPO/rulesets/$id" "$(cat "$file")"
  else
    send POST "repos/$REPO/rulesets" "$(cat "$file")"
  fi
}

list_checks() {
  local branch sha
  branch="$(gh repo view "$REPO" --json defaultBranchRef --jq .defaultBranchRef.name)"
  sha="$(gh api "repos/$REPO/commits/$branch" --jq .sha)"
  echo "Check names reported on $REPO@$branch ($sha):"
  gh api "repos/$REPO/commits/$sha/check-runs" --paginate --jq '.check_runs[].name' | sort -u | sed 's/^/  /'
  echo
  echo "Required contexts in .github/rulesets/main-$PROFILE.json:"
  python3 - "$(ruleset_file)" <<'PY'
import json, sys

ruleset = json.load(open(sys.argv[1]))
for rule in ruleset["rules"]:
    if rule["type"] == "required_status_checks":
        for check in rule["parameters"]["required_status_checks"]:
            print(f"  {check['context']}")
PY
  echo
  echo "Every required context must appear in the list above, or merges will block forever."
}

if [[ "$MODE" == list-checks ]]; then
  list_checks
  exit 0
fi

echo "Repository: $REPO"
echo "Profile:    $PROFILE"
[[ "$DRY_RUN" == true ]] && echo "Mode:       dry run (no changes)"
echo

echo "Repository settings:"
step "squash-only merges, auto-delete branches" merge_settings
step "secret scanning + push protection" secret_scanning
optional_step "secret scanning validity + non-provider patterns" secret_scanning_extras
step "Dependabot alerts (also enables the dependency graph)" send PUT "repos/$REPO/vulnerability-alerts"
step "Dependabot security updates" send PUT "repos/$REPO/automated-security-fixes"
step "private vulnerability reporting" send PUT "repos/$REPO/private-vulnerability-reporting"
step "read-only default GITHUB_TOKEN" workflow_permissions
optional_step "approval required for fork PR workflows" fork_pr_approval
echo

echo "Branch protection:"
step "ruleset '$(json_name "$(ruleset_file)")'" apply_ruleset
echo

other_profile=$([[ "$PROFILE" == strict ]] && echo solo || echo strict)
other_name="$(json_name "$REPO_ROOT/.github/rulesets/main-$other_profile.json")"
if gh api "repos/$REPO/rulesets" --paginate --jq '.[].name' 2>/dev/null | grep -qxF "$other_name"; then
  echo "Warning: ruleset '$other_name' is also present. Two active rulesets apply as the"
  echo "         union of their rules. Delete the one you do not want in"
  echo "         Settings > Rules > Rulesets."
  echo
fi

if ((${#FAILED[@]} > 0)); then
  echo "Failed steps:"
  printf '  - %s\n' "${FAILED[@]}"
  echo
  echo "Re-run the failing call with 'gh api' directly to see the error. The most common"
  echo "cause is a token without admin rights on $REPO."
  exit 1
fi

echo "Done. Verify required status check names with:"
echo "  scripts/apply_branch_protection.sh --profile $PROFILE --list-checks"
