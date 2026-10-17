from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from rules_api.catalog import catalog_payload, domain_by_id, persona_by_id
from rules_api.db import DEFAULT_TENANT_ID, open_store
from rules_api.rbac import (
    assert_can_author,
    assert_can_promote,
    assert_can_transition,
    require_role,
)
from rules_api.benchmark_service import (
    comparison_payload,
    execute_matrix,
    execute_single,
)
from rules_api.benchmark_store import BenchmarkStore
from rules_api.schemas import (
    AuditEventOut,
    BenchmarkMatrixRequest,
    BenchmarkRunRequest,
    CompareRequest,
    CompareResponse,
    ComplianceExportOut,
    CreatePackVersionRequest,
    EntitlementOut,
    EvaluateRequest,
    EvaluateResponse,
    ExplainRequest,
    ExplainResponse,
    PackVersionDetailOut,
    PackVersionOut,
    PromoteRequest,
    ReleaseOut,
    ReleaseUpdateRequest,
    SimulateRequest,
    TestgenRequest,
    TransitionRequest,
    UpdatePackVersionRequest,
)
from rules_api.seed import ensure_seeded
from rules_api.service import (
    compliance_export,
    create_pack_version,
    get_or_update_release,
    promote_pack,
    run_compare,
    run_evaluate,
    run_explain,
    run_simulate,
    run_testgen,
    transition_pack,
    update_draft_pack,
)
from rules_api.store import RulesStore

_store: RulesStore | None = None
_bench_store: BenchmarkStore | None = None
_conn_ref: Any = None


def get_store() -> RulesStore:
    global _store, _bench_store, _conn_ref
    if _store is None:
        _conn_ref, _store = open_store()
        ensure_seeded(_conn_ref)
        _bench_store = BenchmarkStore(_conn_ref)
    return _store


def get_bench_store() -> BenchmarkStore:
    get_store()
    assert _bench_store is not None
    return _bench_store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_store()
    yield


app = FastAPI(
    title="Axiom Decision Platform API",
    version="0.5.0",
    description="GoRules Zen + JDM with multi-domain governance, personas, and audit.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Explicit common origins + any localhost/127.0.0.1 port (Next dev, alternate hosts).
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/catalog")
def get_catalog() -> dict[str, Any]:
    """Domains, personas, and decision frameworks for the product UI."""
    return catalog_payload()


@app.get("/v1/catalog/domains/{domain_id}")
def get_domain(domain_id: str) -> dict[str, Any]:
    row = domain_by_id(domain_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain_id}'")
    payload = catalog_payload()
    framework_id = row.get("framework")
    framework = payload["frameworks"].get(framework_id) if framework_id else None
    return {**row, "framework": framework}


@app.get("/v1/catalog/personas/{persona_id}")
def get_persona(persona_id: str) -> dict[str, Any]:
    row = persona_by_id(persona_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown persona '{persona_id}'")
    return row


@app.post("/v1/evaluate", response_model=EvaluateResponse)
def evaluate_endpoint(body: EvaluateRequest) -> dict[str, Any]:
    store = get_store()
    try:
        return run_evaluate(
            store,
            domain=body.domain,
            pack_id=body.pack_id,
            subject_id=body.subject_id,
            facts=body.facts,
            environment=body.environment,
            as_of=body.as_of,
            commit_entitlements=body.commit_entitlements,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
            engine=body.engine,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/compare", response_model=CompareResponse)
def compare_endpoint(body: CompareRequest) -> dict[str, Any]:
    """Run Zen then Kogito on the same facts; return decisions + wall timings."""
    store = get_store()
    try:
        return run_compare(
            store,
            domain=body.domain,
            pack_id=body.pack_id,
            subject_id=body.subject_id,
            facts=body.facts,
            environment=body.environment,
            as_of=body.as_of,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/explain", response_model=ExplainResponse)
def explain_endpoint(body: ExplainRequest) -> dict[str, Any]:
    store = get_store()
    try:
        return run_explain(
            store,
            domain=body.domain,
            pack_id=body.pack_id,
            subject_id=body.subject_id,
            facts=body.facts,
            environment=body.environment,
            as_of=body.as_of,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
            engine=body.engine,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/simulate")
def simulate_endpoint(body: SimulateRequest) -> dict[str, Any]:
    store = get_store()
    try:
        return run_simulate(
            store,
            domain=body.domain,
            pack_id=body.pack_id,
            version=body.version,
            fixtures=[f.model_dump() for f in body.fixtures],
            compare_to_version=body.compare_to_version,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
            environment=body.environment,
            engine=body.engine,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/testgen")
def testgen_endpoint(body: TestgenRequest) -> dict[str, Any]:
    store = get_store()
    try:
        return run_testgen(
            store,
            domain=body.domain,
            pack_id=body.pack_id,
            version=body.version,
            max_cases=body.max_cases,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
            engine=body.engine,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/entitlements", response_model=list[EntitlementOut])
def list_entitlements(
    subject_id: str = Query(...),
    domain: str = Query("lounge"),
    grandfathered: bool | None = Query(None),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> list[dict[str, Any]]:
    store = get_store()
    return store.list_entitlements(
        domain=domain,
        subject_id=subject_id,
        tenant_id=tenant_id,
        grandfathered=grandfathered,
    )


@app.get("/v1/audit/{evaluation_id}", response_model=AuditEventOut)
def get_audit(
    evaluation_id: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> dict[str, Any]:
    store = get_store()
    row = store.get_audit(evaluation_id, tenant_id=tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return row


@app.get("/v1/audit", response_model=list[AuditEventOut])
def search_audit(
    subject_id: str = Query(...),
    domain: str = Query("lounge"),
    limit: int = Query(50, ge=1, le=200),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> list[dict[str, Any]]:
    store = get_store()
    return store.search_audit(
        domain=domain, subject_id=subject_id, tenant_id=tenant_id, limit=limit
    )


@app.get("/v1/compliance/export", response_model=ComplianceExportOut)
def compliance_export_endpoint(
    subject_id: str = Query(...),
    domain: str = Query("lounge"),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> dict[str, Any]:
    store = get_store()
    return compliance_export(
        store, domain=domain, subject_id=subject_id, tenant_id=tenant_id
    )


@app.get("/v1/packs/{domain}", response_model=list[PackVersionOut])
def list_packs(
    domain: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> list[dict[str, Any]]:
    store = get_store()
    return store.list_pack_versions(domain, tenant_id=tenant_id)


@app.get(
    "/v1/packs/{domain}/{pack_id}/versions/{version}",
    response_model=PackVersionDetailOut,
)
def get_pack_version(
    domain: str,
    pack_id: str,
    version: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> dict[str, Any]:
    store = get_store()
    row = store.get_pack_version(domain, pack_id, version, tenant_id=tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Pack version not found")
    return row


@app.post(
    "/v1/packs/{domain}/{pack_id}/versions",
    response_model=PackVersionDetailOut,
)
def create_version(
    domain: str,
    pack_id: str,
    body: CreatePackVersionRequest,
    role: str | None = Depends(require_role),
) -> dict[str, Any]:
    assert_can_author(role)
    store = get_store()
    try:
        return create_pack_version(
            store,
            domain=domain,
            pack_id=pack_id,
            version=body.version,
            payload=body.payload,
            clone_from_version=body.resolved_clone_from(),
            lifecycle=body.lifecycle,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put(
    "/v1/packs/{domain}/{pack_id}/versions/{version}",
    response_model=PackVersionDetailOut,
)
def update_version(
    domain: str,
    pack_id: str,
    version: str,
    body: UpdatePackVersionRequest,
    role: str | None = Depends(require_role),
) -> dict[str, Any]:
    assert_can_author(role)
    store = get_store()
    try:
        return update_draft_pack(
            store,
            domain=domain,
            pack_id=pack_id,
            version=version,
            payload=body.resolved_payload(),
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/packs/{domain}/{pack_id}/versions/{version}/transition")
def transition_version(
    domain: str,
    pack_id: str,
    version: str,
    body: TransitionRequest,
    role: str | None = Depends(require_role),
) -> dict[str, Any]:
    assert_can_transition(role, body.to)
    store = get_store()
    try:
        return transition_pack(
            store,
            domain=domain,
            pack_id=pack_id,
            version=version,
            to_lifecycle=body.to,
            change_record_id=body.change_record_id,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/packs/{domain}/{pack_id}/promote")
def promote_endpoint(
    domain: str,
    pack_id: str,
    body: PromoteRequest,
    role: str | None = Depends(require_role),
) -> dict[str, Any]:
    assert_can_promote(role)
    store = get_store()
    try:
        return promote_pack(
            store,
            domain=domain,
            pack_id=pack_id,
            from_version=body.from_version,
            to_version=body.to_version,
            policy=body.policy,
            change_record_id=body.change_record_id,
            environment=body.environment,
            canary_percent=body.canary_percent,
            go_live_at=body.go_live_at,
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/releases/{domain}/{pack_id}", response_model=ReleaseOut)
def get_release(
    domain: str,
    pack_id: str,
    environment: str = Query("production"),
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> dict[str, Any]:
    store = get_store()
    try:
        return get_or_update_release(
            store,
            domain=domain,
            pack_id=pack_id,
            tenant_id=tenant_id,
            environment=environment,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/v1/releases/{domain}/{pack_id}", response_model=ReleaseOut)
def put_release(
    domain: str,
    pack_id: str,
    body: ReleaseUpdateRequest,
    role: str | None = Depends(require_role),
) -> dict[str, Any]:
    assert_can_promote(role)
    store = get_store()
    try:
        return get_or_update_release(
            store,
            domain=domain,
            pack_id=pack_id,
            update=body.model_dump(),
            tenant_id=body.tenant_id or DEFAULT_TENANT_ID,
            environment=body.environment,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/benchmark/compare")
def benchmark_compare(
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """Objective comparison table from persisted benchmark runs (UI home view)."""
    bench = get_bench_store()
    runs = bench.list_runs(tenant_id=tenant_id, limit=limit)
    return comparison_payload(runs)


@app.get("/v1/benchmark/runs")
def benchmark_list_runs(
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    kind: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    bench = get_bench_store()
    runs = bench.list_runs(tenant_id=tenant_id, kind=kind, limit=limit)
    return {"runs": runs, "count": len(runs)}


@app.get("/v1/benchmark/runs/{run_id}")
def benchmark_get_run(
    run_id: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
) -> dict[str, Any]:
    bench = get_bench_store()
    row = bench.get_run(run_id, tenant_id=tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown run '{run_id}'")
    return row


@app.delete("/v1/benchmark/runs/{run_id}")
def benchmark_delete_run(
    run_id: str,
    tenant_id: str = Query(DEFAULT_TENANT_ID),
    role: str | None = Depends(require_role),
) -> dict[str, Any]:
    assert_can_author(role)
    bench = get_bench_store()
    ok = bench.delete_run(run_id, tenant_id=tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Unknown run '{run_id}'")
    return {"deleted": True, "run_id": run_id}


@app.post("/v1/benchmark/run")
def benchmark_run(body: BenchmarkRunRequest) -> dict[str, Any]:
    """Run one synthetic cell (columns × rules × fires) and persist the result."""
    bench = get_bench_store()
    try:
        return execute_single(bench, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/benchmark/matrix")
def benchmark_matrix(body: BenchmarkMatrixRequest) -> dict[str, Any]:
    """Run the preset scale grid and persist it as one matrix run."""
    bench = get_bench_store()
    try:
        return execute_matrix(bench, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

