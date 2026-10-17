from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    domain: str = "lounge"
    subject_id: str
    facts: dict[str, Any] = Field(default_factory=dict)
    environment: str = "production"
    as_of: str | None = None
    commit_entitlements: bool = False
    pack_id: str = "lounge-access"
    tenant_id: str = "default"
    engine: Literal["zen", "kogito"] = "zen"


class EvaluateResponse(BaseModel):
    evaluation_id: str
    decision: str
    effects: list[dict[str, Any]]
    entitlements_applied: list[dict[str, Any]]
    entitlements_created: list[dict[str, Any]]
    trace: dict[str, Any]
    pack_version: str
    tenant_id: str = "default"
    canary: bool = False
    engine: Literal["zen", "kogito"] = "zen"


class CompareRequest(BaseModel):
    """Fire the same facts through Zen then Kogito and return a side-by-side diff."""

    domain: str = "lounge"
    subject_id: str
    facts: dict[str, Any] = Field(default_factory=dict)
    environment: str = "production"
    as_of: str | None = None
    pack_id: str = "lounge-access"
    tenant_id: str = "default"


class CompareEngineLeg(BaseModel):
    engine: Literal["zen", "kogito"]
    ok: bool
    wall_millis: float
    decision: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class CompareDiff(BaseModel):
    both_ok: bool
    decisions_agree: bool
    zen_decision: str | None = None
    kogito_decision: str | None = None
    wall_delta_millis: float | None = None
    faster_engine: Literal["zen", "kogito", "tie"] | None = None
    caveats: list[str] = Field(default_factory=list)


class CompareResponse(BaseModel):
    zen: CompareEngineLeg
    kogito: CompareEngineLeg
    diff: CompareDiff
    total_wall_millis: float
    notes: list[str] = Field(default_factory=list)


class ExplainRequest(EvaluateRequest):
    """Same shape as evaluate; returns human-readable reasons (no entitlement commit)."""

    commit_entitlements: bool = False


class ExplainResponse(BaseModel):
    decision: str
    summary: str
    reasons: list[str]
    path: str
    pack_version: str
    effects: list[dict[str, Any]]
    entitlements_applied: list[dict[str, Any]]
    trace: dict[str, Any]
    tenant_id: str = "default"
    engine: Literal["zen", "kogito"] = "zen"


class SimulateFixture(BaseModel):
    subject_id: str
    facts: dict[str, Any] = Field(default_factory=dict)
    as_of: str | None = None


class SimulateRequest(BaseModel):
    domain: str = "lounge"
    pack_id: str = "lounge-access"
    version: str | None = None
    fixtures: list[SimulateFixture]
    compare_to_version: str | None = None
    tenant_id: str = "default"
    environment: str = "production"
    engine: Literal["zen", "kogito"] = "zen"


class TestgenRequest(BaseModel):
    domain: str = "lounge"
    pack_id: str = "lounge-access"
    version: str | None = None
    max_cases: int | None = Field(
        default=None,
        description="Max fixtures to return (default 50, hard max 500).",
        ge=1,
        le=500,
    )
    tenant_id: str = "default"
    engine: Literal["zen", "kogito"] = "zen"


class PromoteRequest(BaseModel):
    from_version: str
    to_version: str
    policy: Literal["cutover", "honor_existing"] = "honor_existing"
    change_record_id: str | None = None
    environment: str = "production"
    canary_percent: int | None = Field(default=None, ge=0, le=100)
    go_live_at: str | None = None
    tenant_id: str = "default"


class CreatePackVersionRequest(BaseModel):
    """Create a draft pack version.

    Provide ``payload`` and/or ``clone_from_version`` (UI alias: ``from_version``).
    When ``version`` is omitted the API assigns the next ``1.N.0-draft`` name.
    """

    version: str | None = None
    payload: dict[str, Any] | None = None
    clone_from_version: str | None = None
    from_version: str | None = Field(
        default=None,
        description="UI alias for clone_from_version",
    )
    lifecycle: str = "draft"
    tenant_id: str = "default"

    def resolved_clone_from(self) -> str | None:
        return self.clone_from_version or self.from_version


class UpdatePackVersionRequest(BaseModel):
    """Update a draft. Accepts ``{payload: {...}}`` or a flat JDM pack (nodes/edges)."""

    payload: dict[str, Any] | None = None
    domain: str | None = None
    pack_id: str | None = None
    version: str | None = None
    lifecycle: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None
    tenant_id: str = "default"

    def resolved_payload(self) -> dict[str, Any]:
        if self.payload is not None:
            return self.payload
        if self.nodes is None or self.edges is None:
            raise ValueError("Provide payload or JDM nodes+edges")
        out: dict[str, Any] = {"nodes": self.nodes, "edges": self.edges}
        for key in ("domain", "pack_id", "version", "lifecycle"):
            val = getattr(self, key)
            if val is not None:
                out[key] = val
        return out


class TransitionRequest(BaseModel):
    to: Literal["in_review", "approved", "published", "retired"]
    change_record_id: str | None = None
    tenant_id: str = "default"


class ReleaseOut(BaseModel):
    domain: str
    pack_id: str
    environment: str
    pack_version: str
    go_live_at: str | None = None
    canary_percent: int = 100
    canary_version: str | None = None
    change_record_id: str | None = None
    tenant_id: str = "default"


class ReleaseUpdateRequest(BaseModel):
    environment: str = "production"
    pack_version: str
    go_live_at: str | None = None
    canary_percent: int = Field(default=100, ge=0, le=100)
    canary_version: str | None = None
    change_record_id: str | None = None
    tenant_id: str = "default"


class EntitlementOut(BaseModel):
    entitlement_id: str
    domain: str
    subject_id: str
    benefit_type: str
    benefit_payload: dict[str, Any]
    source_pack_version: str | None
    source_rule_id: str | None
    granted_at: str
    expires_at: str | None
    status: str
    grandfathered: bool
    cohort_key: str | None
    tenant_id: str = "default"


class AuditEventOut(BaseModel):
    evaluation_id: str
    domain: str
    subject_id: str
    environment: str
    as_of: str
    pack_version: str | None
    decision: str
    path: str
    created_at: str
    result: dict[str, Any] | None = None
    tenant_id: str = "default"


class PackVersionOut(BaseModel):
    domain: str
    pack_id: str
    version: str
    lifecycle: str


class PackVersionDetailOut(BaseModel):
    domain: str
    pack_id: str
    version: str
    lifecycle: str
    payload: dict[str, Any]


class ComplianceExportOut(BaseModel):
    tenant_id: str
    domain: str
    subject_id: str
    entitlements: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]


class BenchmarkRunRequest(BaseModel):
    """Single synthetic scale cell: columns × rules × fires."""

    column_count: int = Field(default=10, ge=1, le=50)
    rule_count: int = Field(default=100, ge=1, le=10_000)
    fire_count: int = Field(default=1_000, ge=1, le=1_000_000)
    seed: int = 42
    values_per_column: int = Field(default=8, ge=2, le=32)
    engines: list[Literal["zen", "dmn_table"]] = Field(
        default_factory=lambda: ["zen", "dmn_table"]
    )
    max_work: int = Field(default=200_000_000, ge=1)
    label: str | None = None
    tenant_id: str = "default"


class BenchmarkMatrixRequest(BaseModel):
    """Preset grid: rule_counts × fire_counts at a fixed column_count."""

    column_count: int = Field(default=10, ge=1, le=50)
    rule_counts: list[int] = Field(default_factory=lambda: [100, 1_000, 10_000])
    fire_counts: list[int] = Field(default_factory=lambda: [1_000, 10_000, 1_000_000])
    seed: int = 42
    engines: list[Literal["zen", "dmn_table"]] = Field(
        default_factory=lambda: ["zen", "dmn_table"]
    )
    max_work: int = Field(default=200_000_000, ge=1)
    skip_over_cap: bool = True
    label: str | None = "preset-matrix"
    tenant_id: str = "default"
