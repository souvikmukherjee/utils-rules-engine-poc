from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from rules_engine import EntitlementSnapshot, RulePack, evaluate, explain, generate_test_cases
from rules_engine.models import Effect

from rules_api.canary import pick_canary_version
from rules_api.jsonutil import loads
from rules_api.store import RulesStore

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review", "retired"},
    "in_review": {"approved", "draft", "retired"},
    "approved": {"published", "in_review", "retired"},
    "published": {"retired"},
    "retired": set(),
}


def _parse_clock(as_of: str | None) -> datetime:
    if not as_of:
        return datetime.now(timezone.utc)
    clock = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    return clock


def load_pack_version(
    store: RulesStore,
    domain: str,
    pack_id: str,
    version: str,
    *,
    tenant_id: str = "default",
) -> RulePack:
    payload = store.get_pack_payload(domain, pack_id, version, tenant_id=tenant_id)
    if payload is None:
        raise LookupError(f"No rule pack {domain}/{pack_id}@{version}")
    return RulePack.from_dict(payload)


def resolve_pack_for_subject(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    subject_id: str,
    environment: str = "production",
    version: str | None = None,
    tenant_id: str = "default",
) -> tuple[RulePack, str, bool]:
    """Resolve pack version for a subject, applying canary when configured.

    Returns (pack, resolved_version, in_canary).
    """
    if version:
        pack = load_pack_version(store, domain, pack_id, version, tenant_id=tenant_id)
        return pack, version, False

    release = store.get_release(domain, pack_id, environment, tenant_id=tenant_id)
    if release is None:
        versions = store.list_pack_versions(domain, tenant_id=tenant_id)
        for row in versions:
            if row["pack_id"] == pack_id:
                pack = load_pack_version(
                    store, domain, pack_id, row["version"], tenant_id=tenant_id
                )
                return pack, row["version"], False
        raise LookupError(f"No rule pack found for {domain}/{pack_id}")

    production_version = release["pack_version"]
    canary_percent = int(release.get("canary_percent") or 100)
    canary_version = release.get("canary_version")
    resolved, in_canary = pick_canary_version(
        subject_id=subject_id,
        pack_version=production_version,
        canary_percent=canary_percent,
        canary_version=canary_version,
    )
    pack = load_pack_version(store, domain, pack_id, resolved, tenant_id=tenant_id)
    return pack, resolved, in_canary


def active_entitlements(
    store: RulesStore,
    domain: str,
    subject_id: str,
    as_of: datetime,
    *,
    tenant_id: str = "default",
) -> list[EntitlementSnapshot]:
    rows = store.active_entitlement_rows(
        domain=domain, subject_id=subject_id, tenant_id=tenant_id
    )
    result: list[EntitlementSnapshot] = []
    for row in rows:
        expires = row["expires_at"]
        if expires:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if as_of >= exp_dt:
                continue
        payload = row["benefit_payload_json"]
        if isinstance(payload, str):
            payload = loads(payload)
        result.append(
            EntitlementSnapshot(
                entitlement_id=row["entitlement_id"],
                benefit_type=row["benefit_type"],
                benefit_payload=payload,
                grandfathered=bool(row["grandfathered"]),
                source_rule_id=row["source_rule_id"],
                source_pack_version=row["source_pack_version"],
            )
        )
    return result


def persist_entitlements(
    store: RulesStore,
    *,
    domain: str,
    subject_id: str,
    pack_version: str,
    effects: list[Effect],
    granted_at: datetime,
    tenant_id: str = "default",
) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    for effect in effects:
        if not effect.persist_as_entitlement:
            continue
        benefit_type = effect.benefit_type or effect.type
        entitlement_id = str(uuid.uuid4())
        payload = dict(effect.payload)
        store.insert_entitlement(
            {
                "entitlement_id": entitlement_id,
                "tenant_id": tenant_id,
                "domain": domain,
                "subject_id": subject_id,
                "benefit_type": benefit_type,
                "benefit_payload": payload,
                "source_pack_version": pack_version,
                "source_rule_id": None,
                "granted_at": granted_at.isoformat(),
                "expires_at": None,
                "status": "active",
                "grandfathered": False,
                "cohort_key": None,
            }
        )
        created.append(
            {
                "entitlement_id": entitlement_id,
                "benefit_type": benefit_type,
                "benefit_payload": payload,
                "source_pack_version": pack_version,
                "grandfathered": False,
            }
        )
    store.commit()
    return created


def write_audit(
    store: RulesStore,
    *,
    evaluation_id: str,
    domain: str,
    subject_id: str,
    environment: str,
    as_of: str,
    pack_version: str,
    decision: str,
    path: str,
    request: dict[str, Any],
    result: dict[str, Any],
    tenant_id: str = "default",
) -> None:
    store.insert_audit(
        {
            "evaluation_id": evaluation_id,
            "tenant_id": tenant_id,
            "domain": domain,
            "subject_id": subject_id,
            "environment": environment,
            "as_of": as_of,
            "pack_version": pack_version,
            "decision": decision,
            "path": path,
            "request": request,
            "result": result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    store.commit()


def run_evaluate(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    subject_id: str,
    facts: dict[str, Any],
    environment: str,
    as_of: str | None,
    commit_entitlements: bool,
    tenant_id: str = "default",
    version: str | None = None,
    write_audit_event: bool = True,
) -> dict[str, Any]:
    pack, resolved_version, in_canary = resolve_pack_for_subject(
        store,
        domain=domain,
        pack_id=pack_id,
        subject_id=subject_id,
        environment=environment,
        version=version,
        tenant_id=tenant_id,
    )
    clock = _parse_clock(as_of)
    ents = active_entitlements(store, domain, subject_id, clock, tenant_id=tenant_id)
    result = evaluate(pack, facts, as_of=clock, entitlements=ents)

    created: list[dict[str, Any]] = []
    if commit_entitlements and result.entitlements_to_create:
        created = persist_entitlements(
            store,
            domain=domain,
            subject_id=subject_id,
            pack_version=result.pack_version,
            effects=result.entitlements_to_create,
            granted_at=clock,
            tenant_id=tenant_id,
        )

    evaluation_id = str(uuid.uuid4())
    body = {
        "evaluation_id": evaluation_id,
        "decision": result.decision,
        "effects": [e.to_dict() for e in result.effects],
        "entitlements_applied": [e.to_dict() for e in result.entitlements_applied],
        "entitlements_created": created,
        "trace": result.trace.to_dict(),
        "pack_version": result.pack_version,
        "tenant_id": tenant_id,
        "canary": in_canary,
    }
    if write_audit_event:
        write_audit(
            store,
            evaluation_id=evaluation_id,
            domain=domain,
            subject_id=subject_id,
            environment=environment,
            as_of=clock.isoformat(),
            pack_version=result.pack_version,
            decision=result.decision,
            path=result.trace.path,
            request={
                "domain": domain,
                "pack_id": pack_id,
                "subject_id": subject_id,
                "facts": facts,
                "environment": environment,
                "as_of": as_of,
                "commit_entitlements": commit_entitlements,
                "tenant_id": tenant_id,
                "resolved_version": resolved_version,
                "canary": in_canary,
            },
            result=body,
            tenant_id=tenant_id,
        )
    return body


def run_explain(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    subject_id: str,
    facts: dict[str, Any],
    environment: str,
    as_of: str | None,
    tenant_id: str = "default",
) -> dict[str, Any]:
    pack, _, _ = resolve_pack_for_subject(
        store,
        domain=domain,
        pack_id=pack_id,
        subject_id=subject_id,
        environment=environment,
        tenant_id=tenant_id,
    )
    clock = _parse_clock(as_of)
    ents = active_entitlements(store, domain, subject_id, clock, tenant_id=tenant_id)
    result = evaluate(pack, facts, as_of=clock, entitlements=ents)
    body = explain(result)
    body["tenant_id"] = tenant_id
    return body


def run_simulate(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    version: str | None,
    fixtures: list[dict[str, Any]],
    compare_to_version: str | None = None,
    tenant_id: str = "default",
    environment: str = "production",
) -> dict[str, Any]:
    if version:
        primary_version = version
    else:
        release = store.get_release(domain, pack_id, environment, tenant_id=tenant_id)
        if release is None:
            raise LookupError(f"No release for {domain}/{pack_id} in {environment}")
        primary_version = release["pack_version"]

    primary_pack = load_pack_version(
        store, domain, pack_id, primary_version, tenant_id=tenant_id
    )
    compare_pack = None
    if compare_to_version:
        compare_pack = load_pack_version(
            store, domain, pack_id, compare_to_version, tenant_id=tenant_id
        )

    results: list[dict[str, Any]] = []
    for fixture in fixtures:
        subject_id = fixture["subject_id"]
        facts = fixture.get("facts") or {}
        clock = _parse_clock(fixture.get("as_of"))
        ents = active_entitlements(store, domain, subject_id, clock, tenant_id=tenant_id)
        primary = evaluate(primary_pack, facts, as_of=clock, entitlements=ents)
        entry: dict[str, Any] = {
            "subject_id": subject_id,
            "facts": facts,
            "as_of": clock.isoformat(),
            "version": primary_version,
            "decision": primary.decision,
            "effects": [e.to_dict() for e in primary.effects],
            "trace": primary.trace.to_dict(),
        }
        if compare_pack is not None:
            other = evaluate(compare_pack, facts, as_of=clock, entitlements=ents)
            entry["compare_to_version"] = compare_to_version
            entry["compare_decision"] = other.decision
            entry["diff"] = {
                "decision_changed": primary.decision != other.decision,
                "from": other.decision,
                "to": primary.decision,
                "effects_changed": [e.to_dict() for e in primary.effects]
                != [e.to_dict() for e in other.effects],
            }
        results.append(entry)

    return {
        "domain": domain,
        "pack_id": pack_id,
        "version": primary_version,
        "compare_to_version": compare_to_version,
        "tenant_id": tenant_id,
        "result_count": len(results),
        "results": results,
    }


def run_testgen(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    version: str | None,
    max_cases: int | None = None,
    tenant_id: str = "default",
    environment: str = "production",
) -> dict[str, Any]:
    if version is None:
        release = store.get_release(domain, pack_id, environment, tenant_id=tenant_id)
        if release is None:
            raise LookupError(f"No release for {domain}/{pack_id}")
        version = release["pack_version"]
    pack = load_pack_version(store, domain, pack_id, version, tenant_id=tenant_id)
    body = generate_test_cases(pack, max_cases=max_cases)
    body["tenant_id"] = tenant_id
    return body


def suggest_draft_version(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    tenant_id: str = "default",
) -> str:
    existing = {
        row["version"]
        for row in store.list_pack_versions(domain, tenant_id=tenant_id)
        if row["pack_id"] == pack_id
    }
    n = 1
    while True:
        candidate = f"1.{n}.0-draft"
        if candidate not in existing:
            return candidate
        n += 1


def create_pack_version(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    version: str | None,
    payload: dict[str, Any] | None,
    clone_from_version: str | None,
    lifecycle: str = "draft",
    tenant_id: str = "default",
) -> dict[str, Any]:
    if lifecycle != "draft":
        raise ValueError("New pack versions must start as draft")

    if payload is None and not clone_from_version:
        # Default: clone the newest row for this pack (list is id DESC).
        for row in store.list_pack_versions(domain, tenant_id=tenant_id):
            if row["pack_id"] == pack_id:
                clone_from_version = row["version"]
                break

    if payload is None and clone_from_version:
        source = store.get_pack_payload(
            domain, pack_id, clone_from_version, tenant_id=tenant_id
        )
        if source is None:
            raise LookupError(f"Clone source {clone_from_version} not found")
        payload = copy.deepcopy(source)
    if payload is None:
        raise ValueError("Provide payload or clone_from_version")

    if not version:
        version = suggest_draft_version(
            store, domain=domain, pack_id=pack_id, tenant_id=tenant_id
        )

    existing = store.get_pack_version(domain, pack_id, version, tenant_id=tenant_id)
    if existing:
        raise ValueError(f"Version {version} already exists")

    payload = dict(payload)
    payload["domain"] = domain
    payload["pack_id"] = pack_id
    payload["version"] = version
    payload["lifecycle"] = "draft"
    # Validate via engine parse.
    RulePack.from_dict(payload)

    store.upsert_pack_version(
        domain=domain,
        pack_id=pack_id,
        version=version,
        lifecycle="draft",
        payload=payload,
        tenant_id=tenant_id,
    )
    store.commit()
    return {
        "domain": domain,
        "pack_id": pack_id,
        "version": version,
        "lifecycle": "draft",
        "payload": payload,
    }


def update_draft_pack(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    version: str,
    payload: dict[str, Any],
    tenant_id: str = "default",
) -> dict[str, Any]:
    current = store.get_pack_version(domain, pack_id, version, tenant_id=tenant_id)
    if current is None:
        raise LookupError(f"Pack version {domain}/{pack_id}@{version} not found")
    if current["lifecycle"] != "draft":
        raise ValueError("Only draft pack versions can be updated")

    payload = dict(payload)
    payload["domain"] = domain
    payload["pack_id"] = pack_id
    payload["version"] = version
    payload["lifecycle"] = "draft"
    RulePack.from_dict(payload)

    store.upsert_pack_version(
        domain=domain,
        pack_id=pack_id,
        version=version,
        lifecycle="draft",
        payload=payload,
        tenant_id=tenant_id,
    )
    store.commit()
    return {
        "domain": domain,
        "pack_id": pack_id,
        "version": version,
        "lifecycle": "draft",
        "payload": payload,
    }


def transition_pack(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    version: str,
    to_lifecycle: str,
    change_record_id: str | None = None,
    tenant_id: str = "default",
) -> dict[str, Any]:
    current = store.get_pack_version(domain, pack_id, version, tenant_id=tenant_id)
    if current is None:
        raise LookupError(f"Pack version {domain}/{pack_id}@{version} not found")
    from_lifecycle = current["lifecycle"]
    allowed = ALLOWED_TRANSITIONS.get(from_lifecycle, set())
    if to_lifecycle not in allowed:
        raise ValueError(
            f"Cannot transition {from_lifecycle} → {to_lifecycle}. Allowed: {sorted(allowed)}"
        )
    if to_lifecycle == "published" and not change_record_id:
        raise ValueError("change_record_id is required when transitioning to published")

    store.update_pack_lifecycle(
        domain, pack_id, version, to_lifecycle, tenant_id=tenant_id
    )
    store.commit()
    updated = store.get_pack_version(domain, pack_id, version, tenant_id=tenant_id)
    assert updated is not None
    return {
        "domain": domain,
        "pack_id": pack_id,
        "version": version,
        "lifecycle": updated["lifecycle"],
        "from_lifecycle": from_lifecycle,
        "change_record_id": change_record_id,
        "payload": updated["payload"],
    }


def promote_pack(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    from_version: str,
    to_version: str,
    policy: str,
    change_record_id: str | None,
    environment: str = "production",
    canary_percent: int | None = None,
    go_live_at: str | None = None,
    tenant_id: str = "default",
) -> dict[str, Any]:
    if environment == "production" and not change_record_id:
        raise ValueError("change_record_id is required to promote to production")

    target = store.get_pack_version(domain, pack_id, to_version, tenant_id=tenant_id)
    if target is None:
        raise LookupError(f"Target version {to_version} not found")
    if target["lifecycle"] not in {"approved", "published"}:
        raise ValueError(
            f"Target version must be approved or published (got {target['lifecycle']})"
        )

    current = store.get_release(domain, pack_id, environment, tenant_id=tenant_id)
    current_version = current["pack_version"] if current else None
    if from_version and current_version and current_version != from_version:
        raise ValueError(
            f"from_version mismatch: release is at {current_version}, got {from_version}"
        )

    percent = (
        canary_percent
        if canary_percent is not None
        else (current["canary_percent"] if current else 100)
    )
    # When canary_percent < 100, keep current as production and set canary to target.
    if percent < 100 and current_version and current_version != to_version:
        production_version = current_version
        canary_version = to_version
    else:
        production_version = to_version
        canary_version = current.get("canary_version") if current else None
        if percent >= 100:
            canary_version = None

    if target["lifecycle"] == "approved":
        store.update_pack_lifecycle(
            domain, pack_id, to_version, "published", tenant_id=tenant_id
        )

    release = store.upsert_release(
        domain=domain,
        pack_id=pack_id,
        environment=environment,
        pack_version=production_version,
        go_live_at=go_live_at or (current.get("go_live_at") if current else None),
        canary_percent=percent,
        canary_version=canary_version,
        change_record_id=change_record_id,
        tenant_id=tenant_id,
    )
    store.commit()

    # honor_existing: leave entitlements alone (default). cutover: flag non-grandfathered
    # active entitlements as superseded for this pack domain/subjects is out of PoC scope;
    # we record the policy on the response for callers.
    return {
        "domain": domain,
        "pack_id": pack_id,
        "from_version": from_version,
        "to_version": to_version,
        "policy": policy,
        "release": release,
        "change_record_id": change_record_id,
    }


def get_or_update_release(
    store: RulesStore,
    *,
    domain: str,
    pack_id: str,
    update: dict[str, Any] | None = None,
    tenant_id: str = "default",
    environment: str = "production",
) -> dict[str, Any]:
    if update is None:
        release = store.get_release(
            domain, pack_id, environment, tenant_id=tenant_id
        )
        if release is None:
            raise LookupError(f"No release for {domain}/{pack_id}/{environment}")
        return release

    if environment == "production" and not update.get("change_record_id"):
        # Allow updates that only tweak canary when a prior change_record exists.
        existing = store.get_release(domain, pack_id, environment, tenant_id=tenant_id)
        if existing is None or not existing.get("change_record_id"):
            raise ValueError("change_record_id is required for production release updates")

    release = store.upsert_release(
        domain=domain,
        pack_id=pack_id,
        environment=update.get("environment", environment),
        pack_version=update["pack_version"],
        go_live_at=update.get("go_live_at"),
        canary_percent=int(update.get("canary_percent", 100)),
        canary_version=update.get("canary_version"),
        change_record_id=update.get("change_record_id"),
        tenant_id=tenant_id,
    )
    store.commit()
    return release


def compliance_export(
    store: RulesStore,
    *,
    domain: str,
    subject_id: str,
    tenant_id: str = "default",
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "domain": domain,
        "subject_id": subject_id,
        "entitlements": store.list_entitlements(
            domain=domain, subject_id=subject_id, tenant_id=tenant_id
        ),
        "audit_events": store.search_audit(
            domain=domain, subject_id=subject_id, tenant_id=tenant_id, limit=200
        ),
    }
