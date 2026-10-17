from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import rules_api.main as main_mod
from rules_api.canary import pick_canary_version, subject_bucket
from rules_api.db import open_store
from rules_api.seed import ensure_seeded


@pytest.fixture()
def client(tmp_path: Path):
    conn, store = open_store(tmp_path / "rules.db")
    ensure_seeded(conn)
    main_mod._store = store
    with TestClient(main_mod.app) as c:
        yield c
    main_mod._store = None


def test_health(client: TestClient):
    assert client.get("/health").json()["status"] == "ok"


def test_evaluate_gold(client: TestClient):
    resp = client.post(
        "/v1/evaluate",
        json={
            "subject_id": "FF-1",
            "facts": {"membership": {"tier": "gold"}},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "allow"
    assert body["pack_version"] == "2.0.0"
    assert body["tenant_id"] == "default"
    assert body["engine"] == "zen"


def test_evaluate_gold_via_kogito(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    from rules_api import kogito_client

    monkeypatch.setattr(
        kogito_client,
        "call_lounge_access",
        lambda context, timeout=10.0: {
            "MembershipTier": "gold",
            "Eligibility": "allow",
            "LoungeClass": "domestic",
            "MatchedRule": "tier-gold-lounge",
            "CompanionsAllowed": 0,
        },
    )
    resp = client.post(
        "/v1/evaluate",
        json={
            "subject_id": "FF-1",
            "facts": {"membership": {"tier": "gold"}},
            "engine": "kogito",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "allow"
    assert body["engine"] == "kogito"
    assert body["trace"]["engine"] == "kogito"
    assert any(e["status"] == "matched" for e in body["trace"]["entries"])


def test_compare_zen_then_kogito(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    from rules_api import kogito_client

    monkeypatch.setattr(
        kogito_client,
        "call_lounge_access",
        lambda context, timeout=10.0: {
            "MembershipTier": "gold",
            "Eligibility": "allow",
            "LoungeClass": "domestic",
            "MatchedRule": "tier-gold-lounge",
            "CompanionsAllowed": 0,
        },
    )
    resp = client.post(
        "/v1/compare",
        json={
            "subject_id": "FF-COMPARE",
            "facts": {
                "membership": {"tier": "gold"},
                "booking": {"cabin": "economy"},
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["zen"]["ok"] is True
    assert body["kogito"]["ok"] is True
    assert body["zen"]["decision"] == "allow"
    assert body["kogito"]["decision"] == "allow"
    assert body["diff"]["both_ok"] is True
    assert body["diff"]["decisions_agree"] is True
    assert body["zen"]["wall_millis"] >= 0
    assert body["kogito"]["wall_millis"] >= 0
    assert body["total_wall_millis"] >= body["zen"]["wall_millis"]


def test_kogito_seasonal_deny(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    from rules_api import kogito_client

    monkeypatch.setattr(
        kogito_client,
        "call_lounge_access",
        lambda context, timeout=10.0: {
            "MembershipTier": "silver",
            "Eligibility": "deny",
            "LoungeClass": None,
            "MatchedRule": "seasonal-peak-deny-silver",
            "CompanionsAllowed": 0,
        },
    )
    resp = client.post(
        "/v1/evaluate",
        json={
            "subject_id": "FF-S",
            "facts": {"membership": {"tier": "silver"}},
            "as_of": "2099-06-15T00:00:00Z",
            "engine": "kogito",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "deny"
    assert body["engine"] == "kogito"


def test_explain(client: TestClient):
    resp = client.post(
        "/v1/explain",
        json={
            "subject_id": "FF-1",
            "facts": {"membership": {"tier": "gold"}},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "allow"
    assert body["reasons"]
    assert "summary" in body


def test_simulate_and_diff(client: TestClient):
    # Clone a draft so we have a second version to compare.
    clone = client.post(
        "/v1/packs/lounge/lounge-access/versions",
        json={"version": "2.1.0-draft", "clone_from_version": "2.0.0"},
    )
    assert clone.status_code == 200

    resp = client.post(
        "/v1/simulate",
        json={
            "domain": "lounge",
            "pack_id": "lounge-access",
            "version": "2.0.0",
            "compare_to_version": "2.1.0-draft",
            "fixtures": [
                {"subject_id": "FF-1", "facts": {"membership": {"tier": "gold"}}},
                {"subject_id": "FF-2", "facts": {"membership": {"tier": "silver"}}},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["result_count"] == 2
    assert body["results"][0]["diff"]["decision_changed"] is False


def test_testgen_bounded(client: TestClient):
    resp = client.post(
        "/v1/testgen",
        json={"domain": "lounge", "pack_id": "lounge-access", "max_cases": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["case_count"] <= 10
    assert body["hard_max_cases"] == 500
    assert body["cases"]


def test_entitlements_grandfathered_filter(client: TestClient):
    all_ents = client.get(
        "/v1/entitlements",
        params={"subject_id": "FF-GRANDFATHERED", "domain": "lounge"},
    ).json()
    assert len(all_ents) >= 2

    gf = client.get(
        "/v1/entitlements",
        params={
            "subject_id": "FF-GRANDFATHERED",
            "domain": "lounge",
            "grandfathered": True,
        },
    ).json()
    assert gf and all(e["grandfathered"] for e in gf)

    non = client.get(
        "/v1/entitlements",
        params={
            "subject_id": "FF-GRANDFATHERED",
            "domain": "lounge",
            "grandfathered": False,
        },
    ).json()
    assert all(not e["grandfathered"] for e in non)


def test_pack_crud_and_transition_rbac(client: TestClient):
    created = client.post(
        "/v1/packs/lounge/lounge-access/versions",
        json={"version": "3.0.0-draft", "clone_from_version": "2.0.0"},
        headers={"X-Role": "author"},
    )
    assert created.status_code == 200
    assert created.json()["lifecycle"] == "draft"

    detail = client.get("/v1/packs/lounge/lounge-access/versions/3.0.0-draft")
    assert detail.status_code == 200
    assert detail.json()["payload"]["version"] == "3.0.0-draft"

    # Viewer cannot transition
    denied = client.post(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft/transition",
        json={"to": "in_review"},
        headers={"X-Role": "viewer"},
    )
    assert denied.status_code == 403

    # Author can submit draft → in_review and save JDM envelope payloads
    payload = created.json()["payload"]
    put_flat = client.put(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft",
        json={
            "domain": "lounge",
            "pack_id": "lounge-access",
            "version": "3.0.0-draft",
            "lifecycle": "draft",
            "nodes": payload["nodes"],
            "edges": payload["edges"],
        },
        headers={"X-Role": "author"},
    )
    assert put_flat.status_code == 200, put_flat.text

    review = client.post(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft/transition",
        json={"to": "in_review"},
        headers={"X-Role": "author"},
    )
    assert review.status_code == 200, review.text

    # Author cannot approve
    author_approve = client.post(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft/transition",
        json={"to": "approved"},
        headers={"X-Role": "author"},
    )
    assert author_approve.status_code == 403

    approved = client.post(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft/transition",
        json={"to": "approved"},
        headers={"X-Role": "approver"},
    )
    assert approved.status_code == 200

    # published requires change_record_id
    bad = client.post(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft/transition",
        json={"to": "published"},
        headers={"X-Role": "admin"},
    )
    assert bad.status_code == 400

    published = client.post(
        "/v1/packs/lounge/lounge-access/versions/3.0.0-draft/transition",
        json={"to": "published", "change_record_id": "CR-100"},
        headers={"X-Role": "admin"},
    )
    assert published.status_code == 200
    assert published.json()["lifecycle"] == "published"


def test_catalog_domains_and_personas(client: TestClient):
    cat = client.get("/v1/catalog").json()
    ids = {d["id"] for d in cat["domains"]}
    assert {"lounge", "loyalty", "airline_operations", "airports", "banking_credit"} <= ids
    assert len(cat["personas"]) >= 4
    assert "lounge_matrix" in cat["frameworks"]
    matrix = cat["frameworks"]["lounge_matrix"]["matrix"]
    bronze_first = next(
        c for c in matrix if c["tier"] == "bronze" and c["cabin"] == "first"
    )
    assert bronze_first["lounge"] == "first"
    platinum_economy = next(
        c for c in matrix if c["tier"] == "platinum" and c["cabin"] == "economy"
    )
    assert platinum_economy["lounge"] == "business"


def test_promote_and_release(client: TestClient):
    client.post(
        "/v1/packs/lounge/lounge-access/versions",
        json={"version": "1.2.0", "clone_from_version": "2.0.0"},
    )
    for step, cr in [
        ("in_review", None),
        ("approved", None),
        ("published", "CR-PROMOTE"),
    ]:
        body = {"to": step}
        if cr:
            body["change_record_id"] = cr
        r = client.post(
            f"/v1/packs/lounge/lounge-access/versions/1.2.0/transition",
            json=body,
            headers={"X-Role": "admin"},
        )
        assert r.status_code == 200, r.text

    promote = client.post(
        "/v1/packs/lounge/lounge-access/promote",
        json={
            "from_version": "2.0.0",
            "to_version": "1.2.0",
            "policy": "honor_existing",
            "change_record_id": "CR-PROMOTE-2",
            "canary_percent": 100,
        },
        headers={"X-Role": "admin"},
    )
    assert promote.status_code == 200, promote.text
    assert promote.json()["release"]["pack_version"] == "1.2.0"

    release = client.get("/v1/releases/lounge/lounge-access")
    assert release.status_code == 200
    assert release.json()["pack_version"] == "1.2.0"


def test_compliance_export(client: TestClient):
    client.post(
        "/v1/evaluate",
        json={
            "subject_id": "FF-GRANDFATHERED",
            "facts": {"membership": {"tier": "silver"}},
        },
    )
    resp = client.get(
        "/v1/compliance/export",
        params={"subject_id": "FF-GRANDFATHERED", "domain": "lounge"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["entitlements"]
    assert body["audit_events"]


def test_canary_bucket_stable():
    assert subject_bucket("FF-1") == subject_bucket("FF-1")
    v, in_canary = pick_canary_version(
        subject_id="FF-1",
        pack_version="2.0.0",
        canary_percent=100,
        canary_version="2.0.0",
    )
    assert v == "2.0.0" and in_canary is False

    v50, flag = pick_canary_version(
        subject_id="FF-1",
        pack_version="2.0.0",
        canary_percent=50,
        canary_version="2.0.0",
    )
    assert v50 in {"2.0.0", "2.0.0"}
    assert isinstance(flag, bool)


def test_canary_on_evaluate(client: TestClient):
    # Create and publish 2.0.0, then set canary on release.
    client.post(
        "/v1/packs/lounge/lounge-access/versions",
        json={"version": "2.1.0", "clone_from_version": "2.0.0"},
    )
    for step, cr in [
        ("in_review", None),
        ("approved", None),
        ("published", "CR-CANARY"),
    ]:
        body = {"to": step}
        if cr:
            body["change_record_id"] = cr
        assert (
            client.post(
                "/v1/packs/lounge/lounge-access/versions/2.1.0/transition",
                json=body,
                headers={"X-Role": "admin"},
            ).status_code
            == 200
        )

    put = client.put(
        "/v1/releases/lounge/lounge-access",
        json={
            "pack_version": "2.0.0",
            "canary_percent": 100,
            "canary_version": "2.1.0",
            "change_record_id": "CR-CANARY-REL",
        },
        headers={"X-Role": "admin"},
    )
    # With 100% canary_percent, canary_version is ignored (always production).
    assert put.status_code == 200

    put2 = client.put(
        "/v1/releases/lounge/lounge-access",
        json={
            "pack_version": "2.0.0",
            "canary_percent": 50,
            "canary_version": "2.1.0",
            "change_record_id": "CR-CANARY-REL-2",
        },
        headers={"X-Role": "admin"},
    )
    assert put2.status_code == 200

    # Run several subjects; at least some should resolve (either version ok).
    versions = set()
    for i in range(20):
        r = client.post(
            "/v1/evaluate",
            json={
                "subject_id": f"FF-CANARY-{i}",
                "facts": {"membership": {"tier": "gold"}},
            },
        )
        assert r.status_code == 200
        versions.add(r.json()["pack_version"])
    assert versions & {"2.0.0", "2.1.0"}
