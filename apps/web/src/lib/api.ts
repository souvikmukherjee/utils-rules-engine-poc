/**
 * Default to same-origin `/api` (Next.js rewrite → FastAPI). That avoids
 * browser CORS / localhost-vs-127.0.0.1 mismatches. Override with an absolute
 * URL via NEXT_PUBLIC_API_URL when calling the API directly.
 */
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "/api").replace(/\/$/, "");

export type RulesEngine = "zen" | "kogito";

/** Active runtime engine; synced from EngineProvider so API calls redirect. */
let activeEngine: RulesEngine = "zen";

export function setActiveEngine(engine: RulesEngine): void {
  activeEngine = engine;
}

export function getActiveEngine(): RulesEngine {
  return activeEngine;
}

function buildUrl(path: string, query?: Record<string, string>): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_URL}${p}`;
  if (!query) return url;
  return `${url}?${new URLSearchParams(query).toString()}`;
}

export type Role = "viewer" | "author" | "approver" | "admin";

export type EvaluatePayload = {
  domain?: string;
  subject_id: string;
  facts: Record<string, unknown>;
  environment?: string;
  as_of?: string | null;
  commit_entitlements?: boolean;
  pack_id?: string;
};

export type EvaluateResult = {
  evaluation_id: string;
  decision: string;
  effects: Record<string, unknown>[];
  entitlements_applied: Record<string, unknown>[];
  entitlements_created: Record<string, unknown>[];
  trace: {
    as_of: string;
    pack_version: string;
    path: string;
    engine?: RulesEngine;
    entitlements_honored: Record<string, unknown>[];
    entries: {
      rule_id: string;
      rule_name: string;
      status: string;
      reason: string | null;
      effects: Record<string, unknown>[];
    }[];
  };
  pack_version: string;
  engine?: RulesEngine;
};

export type AuditEvent = {
  evaluation_id: string;
  domain: string;
  subject_id: string;
  environment: string;
  as_of: string;
  pack_version: string | null;
  decision: string;
  path: string;
  created_at: string;
  result?: EvaluateResult | null;
};

export type Entitlement = {
  entitlement_id: string;
  domain: string;
  subject_id: string;
  benefit_type: string;
  benefit_payload: Record<string, unknown>;
  source_pack_version: string | null;
  source_rule_id: string | null;
  granted_at: string;
  expires_at: string | null;
  status: string;
  grandfathered: boolean;
  cohort_key: string | null;
};

export type PackVersionSummary = {
  domain: string;
  pack_id: string;
  version: string;
  lifecycle: string;
};

export type JdmNode = {
  id: string;
  type: string;
  name?: string;
  position?: { x: number; y: number };
  content?: unknown;
  [key: string]: unknown;
};

export type JdmEdge = {
  id: string;
  sourceId: string;
  targetId: string;
  type?: string;
  [key: string]: unknown;
};

/** Platform envelope around a GoRules JSON Decision Model. */
export type RulePack = {
  domain: string;
  pack_id: string;
  version: string;
  lifecycle: string;
  nodes: JdmNode[];
  edges: JdmEdge[];
};

export type CreateVersionPayload = {
  /** Preferred API field */
  clone_from_version?: string | null;
  /** UI alias accepted by the API */
  from_version?: string | null;
  version?: string | null;
  lifecycle?: string;
};

export type TransitionPayload = {
  to: string;
  change_record_id?: string | null;
};

/** API returns packs nested under ``payload``; the Author UI uses a flat RulePack. */
type PackVersionApi = {
  domain: string;
  pack_id: string;
  version: string;
  lifecycle: string;
  payload?: RulePack | Record<string, unknown>;
  nodes?: JdmNode[];
  edges?: JdmEdge[];
};

function normalizePack(raw: PackVersionApi | RulePack): RulePack {
  const nested =
    raw && typeof raw === "object" && "payload" in raw && raw.payload
      ? (raw.payload as Record<string, unknown>)
      : null;
  const nodes = Array.isArray((raw as RulePack).nodes)
    ? (raw as RulePack).nodes
    : Array.isArray(nested?.nodes)
      ? (nested.nodes as JdmNode[])
      : [];
  const edges = Array.isArray((raw as RulePack).edges)
    ? (raw as RulePack).edges
    : Array.isArray(nested?.edges)
      ? (nested.edges as JdmEdge[])
      : [];
  return {
    domain: String(raw.domain ?? nested?.domain ?? "lounge"),
    pack_id: String(raw.pack_id ?? nested?.pack_id ?? "lounge-access"),
    version: String(raw.version ?? nested?.version ?? ""),
    lifecycle: String(raw.lifecycle ?? nested?.lifecycle ?? "draft"),
    nodes,
    edges,
  };
}

export type ReleaseConfig = {
  domain: string;
  pack_id: string;
  environment: string;
  pack_version: string;
  go_live_at: string | null;
  canary_percent: number;
  change_record_id: string | null;
};

export type ReleaseUpdatePayload = {
  environment?: string;
  pack_version?: string;
  go_live_at?: string | null;
  canary_percent?: number;
  change_record_id?: string | null;
};

export type PromotePayload = {
  environment?: string;
  pack_version: string;
  change_record_id: string;
  go_live_at?: string | null;
  canary_percent?: number;
};

export type SimulateFixture = {
  subject_id: string;
  facts: Record<string, unknown>;
  as_of?: string | null;
  label?: string;
};

export type SimulatePayload = {
  domain?: string;
  pack_id?: string;
  version?: string | null;
  environment?: string;
  fixtures: SimulateFixture[];
};

export type SimulateCaseResult = {
  label?: string;
  subject_id: string;
  decision: string;
  pack_version?: string;
  path?: string;
  effects?: Record<string, unknown>[];
  trace?: EvaluateResult["trace"];
  error?: string;
};

export type SimulateResult = {
  results: SimulateCaseResult[];
};

export type ExplainPayload = {
  domain?: string;
  pack_id?: string;
  version?: string | null;
  subject_id: string;
  facts: Record<string, unknown>;
  as_of?: string | null;
  environment?: string;
};

export type ExplainResult = {
  decision: string;
  pack_version?: string;
  explanation?: string;
  trace?: EvaluateResult["trace"];
  effects?: Record<string, unknown>[];
};

export type TestgenPayload = {
  domain?: string;
  pack_id?: string;
  version?: string | null;
};

export type TestgenCase = {
  label?: string;
  subject_id?: string;
  facts: Record<string, unknown>;
  as_of?: string | null;
  expected_decision?: string | null;
};

export type TestgenResult = {
  cases: TestgenCase[];
};

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (data.detail != null) return JSON.stringify(data.detail);
    return JSON.stringify(data);
  } catch {
    return `${res.status} ${res.statusText || "Request failed"}`;
  }
}

function headers(role?: Role | null, json = true): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h["Content-Type"] = "application/json";
  if (role) h["X-Role"] = role;
  return h;
}

async function request<T>(
  path: string,
  init?: RequestInit & { role?: Role | null },
): Promise<T> {
  const { role, ...rest } = init ?? {};
  const method = (rest.method ?? "GET").toUpperCase();
  const wantsJson = method !== "GET" && method !== "HEAD";
  let res: Response;
  try {
    res = await fetch(buildUrl(path), {
      ...rest,
      headers: {
        ...headers(role, wantsJson),
        ...(rest.headers ?? {}),
      },
    });
  } catch (err) {
    const hint =
      API_URL.startsWith("http")
        ? `Is FastAPI running at ${API_URL}?`
        : "Is FastAPI running on :8000 (Next proxies /api → 127.0.0.1:8000)?";
    const detail = err instanceof Error ? err.message : "network error";
    throw new Error(`Failed to reach API (${detail}). ${hint}`);
  }
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function evaluate(payload: EvaluatePayload): Promise<EvaluateResult> {
  return request<EvaluateResult>("/v1/evaluate", {
    method: "POST",
    body: JSON.stringify({
      domain: payload.domain ?? "lounge",
      pack_id: payload.pack_id ?? "lounge-access",
      environment: payload.environment ?? "production",
      commit_entitlements: payload.commit_entitlements ?? false,
      subject_id: payload.subject_id,
      facts: payload.facts,
      as_of: payload.as_of ?? null,
      engine: activeEngine,
    }),
  });
}

export type CompareEngineLeg = {
  engine: RulesEngine;
  ok: boolean;
  wall_millis: number;
  decision: string | null;
  result: EvaluateResult | null;
  error: string | null;
};

export type CompareDiff = {
  both_ok: boolean;
  decisions_agree: boolean;
  zen_decision: string | null;
  kogito_decision: string | null;
  wall_delta_millis: number | null;
  faster_engine: "zen" | "kogito" | "tie" | null;
  caveats: string[];
};

export type CompareResult = {
  zen: CompareEngineLeg;
  kogito: CompareEngineLeg;
  diff: CompareDiff;
  total_wall_millis: number;
  notes: string[];
};

/** Fire the same facts through Zen then Kogito (ignores header engine toggle). */
export async function compareEngines(
  payload: EvaluatePayload,
): Promise<CompareResult> {
  return request<CompareResult>("/v1/compare", {
    method: "POST",
    body: JSON.stringify({
      domain: payload.domain ?? "lounge",
      pack_id: payload.pack_id ?? "lounge-access",
      environment: payload.environment ?? "production",
      subject_id: payload.subject_id,
      facts: payload.facts,
      as_of: payload.as_of ?? null,
    }),
  });
}

export async function searchAudit(
  subjectId: string,
  domain = "lounge",
): Promise<AuditEvent[]> {
  return request<AuditEvent[]>(
    `/v1/audit?${new URLSearchParams({
      subject_id: subjectId,
      domain,
    })}`,
  );
}

export async function listEntitlements(
  subjectId: string,
  domain = "lounge",
): Promise<Entitlement[]> {
  return request<Entitlement[]>(
    `/v1/entitlements?${new URLSearchParams({
      subject_id: subjectId,
      domain,
    })}`,
  );
}

export async function listPacks(domain: string): Promise<PackVersionSummary[]> {
  return request<PackVersionSummary[]>(`/v1/packs/${encodeURIComponent(domain)}`);
}

export async function getPackVersion(
  domain: string,
  packId: string,
  version: string,
): Promise<RulePack> {
  const raw = await request<PackVersionApi>(
    `/v1/packs/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}/versions/${encodeURIComponent(version)}`,
  );
  return normalizePack(raw);
}

export async function createPackVersion(
  domain: string,
  packId: string,
  payload: CreateVersionPayload,
  role?: Role | null,
): Promise<RulePack> {
  const cloneFrom = payload.clone_from_version ?? payload.from_version ?? null;
  const body: Record<string, unknown> = {
    lifecycle: payload.lifecycle ?? "draft",
  };
  if (cloneFrom) body.clone_from_version = cloneFrom;
  if (payload.version) body.version = payload.version;
  const raw = await request<PackVersionApi>(
    `/v1/packs/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}/versions`,
    { method: "POST", body: JSON.stringify(body), role },
  );
  return normalizePack(raw);
}

export async function updatePackVersion(
  domain: string,
  packId: string,
  version: string,
  pack: RulePack,
  role?: Role | null,
): Promise<RulePack> {
  const raw = await request<PackVersionApi>(
    `/v1/packs/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}/versions/${encodeURIComponent(version)}`,
    {
      method: "PUT",
      // API stores the editable pack under ``payload``.
      body: JSON.stringify({ payload: pack }),
      role,
    },
  );
  return normalizePack(raw);
}

export async function transitionPackVersion(
  domain: string,
  packId: string,
  version: string,
  payload: TransitionPayload,
  role?: Role | null,
): Promise<RulePack | PackVersionSummary> {
  const raw = await request<PackVersionApi | PackVersionSummary>(
    `/v1/packs/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}/versions/${encodeURIComponent(version)}/transition`,
    { method: "POST", body: JSON.stringify(payload), role },
  );
  if (raw && typeof raw === "object" && "payload" in raw) {
    return normalizePack(raw as PackVersionApi);
  }
  return raw;
}

export async function getRelease(
  domain: string,
  packId: string,
  environment = "production",
): Promise<ReleaseConfig> {
  return request<ReleaseConfig>(
    `/v1/releases/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}?${new URLSearchParams(
      { environment },
    )}`,
  );
}

export async function updateRelease(
  domain: string,
  packId: string,
  payload: ReleaseUpdatePayload,
  role?: Role | null,
): Promise<ReleaseConfig> {
  return request<ReleaseConfig>(
    `/v1/releases/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}`,
    { method: "PUT", body: JSON.stringify(payload), role },
  );
}

export async function promotePack(
  domain: string,
  packId: string,
  payload: PromotePayload,
  role?: Role | null,
): Promise<ReleaseConfig> {
  return request<ReleaseConfig>(
    `/v1/packs/${encodeURIComponent(domain)}/${encodeURIComponent(packId)}/promote`,
    { method: "POST", body: JSON.stringify(payload), role },
  );
}

export async function simulate(
  payload: SimulatePayload,
  role?: Role | null,
): Promise<SimulateResult> {
  return request<SimulateResult>("/v1/simulate", {
    method: "POST",
    body: JSON.stringify({
      environment: "production",
      domain: payload.domain ?? "lounge",
      pack_id: payload.pack_id ?? "lounge-access",
      engine: activeEngine,
      ...payload,
    }),
    role,
  });
}

export async function explain(
  payload: ExplainPayload,
  role?: Role | null,
): Promise<ExplainResult> {
  return request<ExplainResult>("/v1/explain", {
    method: "POST",
    body: JSON.stringify({
      environment: "production",
      domain: payload.domain ?? "lounge",
      pack_id: payload.pack_id ?? "lounge-access",
      engine: activeEngine,
      ...payload,
    }),
    role,
  });
}

export async function testgen(
  payload: TestgenPayload,
  role?: Role | null,
): Promise<TestgenResult> {
  return request<TestgenResult>("/v1/testgen", {
    method: "POST",
    body: JSON.stringify({
      domain: payload.domain ?? "lounge",
      pack_id: payload.pack_id ?? "lounge-access",
      engine: activeEngine,
      ...payload,
    }),
    role,
  });
}
