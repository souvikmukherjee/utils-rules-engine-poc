"use client";

import { useEffect, useState } from "react";
import {
  explain,
  listPacks,
  simulate,
  testgen,
  type ExplainResult,
  type PackVersionSummary,
  type Role,
  type SimulateCaseResult,
  type TestgenCase,
} from "@/lib/api";
import { DEFAULT_DOMAIN, DEFAULT_PACK_ID } from "@/lib/constants";
import {
  ErrorAlert,
  FieldLabel,
  PrimaryButton,
  RoleSelect,
  Select,
  TextArea,
  TextInput,
} from "./ui";

const DEFAULT_FIXTURES = `[
  {
    "label": "Gold member",
    "subject_id": "FF-1001",
    "facts": { "membership": { "tier": "gold" } }
  },
  {
    "label": "Silver (no access)",
    "subject_id": "FF-3003",
    "facts": { "membership": { "tier": "silver" } }
  },
  {
    "label": "Grandfathered",
    "subject_id": "FF-GRANDFATHERED",
    "facts": { "membership": { "tier": "silver" } }
  }
]`;

function decisionTone(decision: string): string {
  if (decision === "allow") return "text-sea";
  if (decision === "deny") return "text-coral";
  return "text-ink/60";
}

export function SimulatePanel() {
  const [role, setRole] = useState<Role>("author");
  const [versions, setVersions] = useState<PackVersionSummary[]>([]);
  const [version, setVersion] = useState("");
  const [fixturesText, setFixturesText] = useState(DEFAULT_FIXTURES);
  const [asOf, setAsOf] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SimulateCaseResult[]>([]);
  const [cases, setCases] = useState<TestgenCase[]>([]);
  const [explainIdx, setExplainIdx] = useState<number | null>(null);
  const [explanation, setExplanation] = useState<ExplainResult | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const list = await listPacks(DEFAULT_DOMAIN);
        setVersions(list);
        if (list[0]) setVersion(list[0].version);
      } catch {
        /* API may not be up — leave empty */
      }
    })();
  }, []);

  async function onSimulate() {
    setLoading(true);
    setError(null);
    setExplanation(null);
    try {
      const fixtures = JSON.parse(fixturesText) as {
        label?: string;
        subject_id: string;
        facts: Record<string, unknown>;
        as_of?: string | null;
      }[];
      if (!Array.isArray(fixtures)) {
        throw new Error("Fixtures must be a JSON array");
      }
      const normalized = fixtures.map((f) => ({
        ...f,
        as_of: f.as_of ?? (asOf || null),
      }));
      const data = await simulate(
        {
          domain: DEFAULT_DOMAIN,
          pack_id: DEFAULT_PACK_ID,
          version: version || null,
          fixtures: normalized,
        },
        role,
      );
      setResults(data.results ?? []);
    } catch (err) {
      setResults([]);
      setError(err instanceof Error ? err.message : "Simulate failed");
    } finally {
      setLoading(false);
    }
  }

  async function onTestgen() {
    setLoading(true);
    setError(null);
    try {
      const data = await testgen(
        {
          domain: DEFAULT_DOMAIN,
          pack_id: DEFAULT_PACK_ID,
          version: version || null,
        },
        role,
      );
      const generated = data.cases ?? [];
      setCases(generated);
      if (generated.length) {
        setFixturesText(
          JSON.stringify(
            generated.map((c, i) => ({
              label: c.label ?? `case-${i + 1}`,
              subject_id: c.subject_id ?? `GEN-${i + 1}`,
              facts: c.facts,
              as_of: c.as_of ?? null,
            })),
            null,
            2,
          ),
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Testgen failed");
    } finally {
      setLoading(false);
    }
  }

  async function onExplain(index: number) {
    setExplainIdx(index);
    setError(null);
    setExplanation(null);
    try {
      const fixtures = JSON.parse(fixturesText) as {
        subject_id: string;
        facts: Record<string, unknown>;
        as_of?: string | null;
      }[];
      const fixture = fixtures[index];
      if (!fixture) throw new Error("Fixture not found");
      const data = await explain(
        {
          domain: DEFAULT_DOMAIN,
          pack_id: DEFAULT_PACK_ID,
          version: version || null,
          subject_id: fixture.subject_id,
          facts: fixture.facts,
          as_of: fixture.as_of ?? (asOf || null),
        },
        role,
      );
      setExplanation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Explain failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <RoleSelect value={role} onChange={setRole} />
        <div className="flex flex-wrap gap-2">
          <PrimaryButton tone="ghost" onClick={() => void onTestgen()} disabled={loading}>
            Run testgen
          </PrimaryButton>
          <PrimaryButton onClick={() => void onSimulate()} disabled={loading}>
            {loading ? "Running…" : "Simulate"}
          </PrimaryButton>
        </div>
      </div>

      <ErrorAlert message={error} />

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block space-y-1.5">
              <FieldLabel>Pack version</FieldLabel>
              <Select
                value={version}
                onChange={(e) => setVersion(e.target.value)}
              >
                <option value="">Active / default</option>
                {versions.map((v) => (
                  <option key={v.version} value={v.version}>
                    {v.version} ({v.lifecycle})
                  </option>
                ))}
              </Select>
            </label>
            <label className="block space-y-1.5">
              <FieldLabel>As of (optional)</FieldLabel>
              <TextInput
                value={asOf}
                onChange={(e) => setAsOf(e.target.value)}
                placeholder="2026-06-01T00:00:00Z"
              />
            </label>
          </div>

          <label className="block space-y-1.5">
            <FieldLabel>Fixtures JSON</FieldLabel>
            <TextArea
              rows={16}
              value={fixturesText}
              onChange={(e) => setFixturesText(e.target.value)}
            />
          </label>

          {cases.length > 0 && (
            <p className="text-sm text-ink/55">
              Testgen produced {cases.length} case
              {cases.length === 1 ? "" : "s"} — fixtures updated above.
            </p>
          )}
        </div>

        <div className="space-y-5">
          <div className="min-h-[12rem] border border-[var(--line)] bg-white/40 p-5">
            {!results.length && !error && (
              <p className="text-sm text-ink/45">
                Paste fixtures (or run testgen), then Simulate to compare
                decisions.
              </p>
            )}
            {results.length > 0 && (
              <ul className="space-y-3 animate-rise">
                {results.map((r, i) => (
                  <li
                    key={`${r.subject_id}-${i}`}
                    className="border-b border-[var(--line)] pb-3 last:border-0"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <div>
                        <p className="font-medium text-sm">
                          {r.label ?? r.subject_id}
                        </p>
                        <p className="font-mono text-xs text-ink/45">
                          {r.subject_id}
                          {r.path ? ` · ${r.path}` : ""}
                          {r.pack_version ? ` · ${r.pack_version}` : ""}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {r.error ? (
                          <span className="text-sm text-coral">{r.error}</span>
                        ) : (
                          <span
                            className={`font-[family-name:var(--font-display)] text-xl capitalize ${decisionTone(r.decision)}`}
                          >
                            {r.decision}
                          </span>
                        )}
                        <PrimaryButton
                          tone="ghost"
                          className="px-2 py-1 text-xs"
                          onClick={() => void onExplain(i)}
                        >
                          Explain
                        </PrimaryButton>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {explanation && explainIdx != null && (
            <div className="border border-[var(--line)] bg-white/40 p-5 animate-rise">
              <p className="font-mono text-xs uppercase tracking-wider text-ink/50">
                Explain · fixture {explainIdx + 1}
              </p>
              <p
                className={`mt-1 font-[family-name:var(--font-display)] text-3xl capitalize ${decisionTone(explanation.decision)}`}
              >
                {explanation.decision}
              </p>
              {explanation.explanation && (
                <p className="mt-3 text-sm leading-relaxed text-ink/75">
                  {explanation.explanation}
                </p>
              )}
              {explanation.trace?.entries && (
                <ul className="mt-4 space-y-2">
                  {explanation.trace.entries.map((entry) => (
                    <li
                      key={entry.rule_id}
                      className="flex flex-wrap justify-between gap-2 text-sm"
                    >
                      <span>{entry.rule_name}</span>
                      <span className="font-mono text-xs text-ink/50">
                        {entry.status}
                        {entry.reason ? ` · ${entry.reason}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {!explanation.explanation && !explanation.trace && (
                <pre className="mt-3 overflow-x-auto font-mono text-xs text-ink/60">
                  {JSON.stringify(explanation, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
