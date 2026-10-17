"use client";

import { useEffect, useMemo, useState } from "react";
import {
  compareEngines,
  type CompareEngineLeg,
  type CompareResult,
  type EvaluateResult,
} from "@/lib/api";
import { scenariosForDomain } from "@/lib/constants";
import { useWorkspace } from "@/lib/workspace";
import { ErrorAlert, FieldLabel, PrimaryButton, TextArea, TextInput } from "./ui";

function decisionTone(decision: string | null | undefined): string {
  if (decision === "allow") return "text-sea";
  if (decision === "deny") return "text-coral";
  return "text-ink/60";
}

function loungeFromResult(result: EvaluateResult | null | undefined): string | null {
  if (!result) return null;
  for (const effect of result.effects) {
    const label = effect.lounge_label ?? effect.lounge_type ?? effect.lounge_class;
    if (typeof label === "string" && label) return label;
    const payload = effect.payload;
    if (payload && typeof payload === "object") {
      const nested = payload as Record<string, unknown>;
      const nestedLabel =
        nested.lounge_label ?? nested.lounge_type ?? nested.lounge_class;
      if (typeof nestedLabel === "string" && nestedLabel) return nestedLabel;
    }
  }
  return null;
}

function matchedRules(result: EvaluateResult | null | undefined): string[] {
  if (!result?.trace?.entries) return [];
  return result.trace.entries
    .filter((e) => e.status === "matched")
    .map((e) => e.rule_id);
}

function EngineCard({
  title,
  leg,
}: {
  title: string;
  leg: CompareEngineLeg | null;
}) {
  if (!leg) {
    return (
      <div className="border border-[var(--line)] bg-white/50 p-5">
        <h3 className="font-mono text-[10px] uppercase tracking-wider text-ink/45">
          {title}
        </h3>
        <p className="mt-4 text-sm text-ink/45">Waiting for a run…</p>
      </div>
    );
  }

  if (!leg.ok) {
    return (
      <div className="border border-coral/30 bg-coral/5 p-5">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="font-mono text-[10px] uppercase tracking-wider text-ink/45">
            {title}
          </h3>
          <span className="font-mono text-[11px] text-ink/45">
            {leg.wall_millis.toFixed(1)} ms
          </span>
        </div>
        <p className="mt-3 text-sm text-coral" role="alert">
          {leg.error ?? "Engine failed"}
        </p>
      </div>
    );
  }

  const lounge = loungeFromResult(leg.result);
  const rules = matchedRules(leg.result);

  return (
    <div className="border border-[var(--line)] bg-white/50 p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="font-mono text-[10px] uppercase tracking-wider text-ink/45">
          {title}
        </h3>
        <span className="font-mono text-[11px] text-sea">{leg.wall_millis.toFixed(1)} ms</span>
      </div>
      <p
        className={`mt-3 font-[family-name:var(--font-display)] text-3xl capitalize ${decisionTone(leg.decision)}`}
      >
        {leg.decision}
      </p>
      {lounge && (
        <p className="mt-1 font-[family-name:var(--font-display)] text-lg text-ink">
          {lounge}
        </p>
      )}
      <p className="mt-1 font-mono text-[11px] text-ink/45">
        pack={leg.result?.pack_version ?? "—"} · path={leg.result?.trace?.path ?? "—"}
      </p>
      {rules.length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {rules.map((id) => (
            <li
              key={id}
              className="border border-[var(--line)] bg-white/70 px-2.5 py-1.5 font-mono text-[11px] text-ink/80"
            >
              {id}
            </li>
          ))}
        </ul>
      )}
      <details className="mt-4">
        <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-wider text-ink/45">
          Effects JSON
        </summary>
        <pre className="mt-2 overflow-x-auto bg-ink/[0.03] p-3 font-mono text-xs leading-relaxed text-ink/80">
          {JSON.stringify(leg.result?.effects ?? [], null, 2)}
        </pre>
      </details>
    </div>
  );
}

export function ComparePanel() {
  const { domain } = useWorkspace();
  const presets = useMemo(
    () => scenariosForDomain(domain?.id ?? "lounge"),
    [domain?.id],
  );
  const [presetIndex, setPresetIndex] = useState(0);
  const [subjectId, setSubjectId] = useState(presets[0]?.subject_id ?? "FF-1");
  const [factsText, setFactsText] = useState(
    JSON.stringify(presets[0]?.facts ?? {}, null, 2),
  );
  const [asOf, setAsOf] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [batchRows, setBatchRows] = useState<
    { label: string; compare: CompareResult }[] | null
  >(null);

  useEffect(() => {
    const p = presets[0];
    if (!p) return;
    setPresetIndex(0);
    setSubjectId(p.subject_id);
    setFactsText(JSON.stringify(p.facts, null, 2));
    setResult(null);
    setError(null);
    setBatchRows(null);
  }, [presets]);

  function applyPreset(index: number) {
    const preset = presets[index];
    if (!preset) return;
    setPresetIndex(index);
    setSubjectId(preset.subject_id);
    setFactsText(JSON.stringify(preset.facts, null, 2));
  }

  async function onCompare() {
    if (!domain) return;
    setLoading(true);
    setError(null);
    setBatchRows(null);
    try {
      const facts = JSON.parse(factsText) as Record<string, unknown>;
      const data = await compareEngines({
        domain: domain.id,
        pack_id: domain.pack_id,
        subject_id: subjectId,
        facts,
        as_of: asOf || null,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setLoading(false);
    }
  }

  async function runAllSamples() {
    if (!domain || presets.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const rows: { label: string; compare: CompareResult }[] = [];
      for (let i = 0; i < presets.length; i++) {
        const preset = presets[i];
        const compare = await compareEngines({
          domain: domain.id,
          pack_id: domain.pack_id,
          subject_id: preset.subject_id,
          facts: preset.facts,
          as_of: asOf || null,
        });
        rows.push({ label: preset.label, compare });
      }
      const last = rows[rows.length - 1];
      if (last) {
        applyPreset(presets.length - 1);
        setResult(last.compare);
      }
      setBatchRows(rows);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Batch compare failed");
    } finally {
      setLoading(false);
    }
  }

  const diff = result?.diff;

  return (
    <div className="space-y-8">
      <p className="border border-[var(--line)] bg-white/50 px-4 py-3 text-sm text-ink/70">
        Fire the same sample facts through{" "}
        <span className="font-medium text-ink">GoRules Zen</span> then{" "}
        <span className="font-medium text-ink">Kogito</span> and compare
        decisions, lounge outcomes, and wall latency. The header engine toggle is
        ignored here — both runtimes always execute.
      </p>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {presets.map((p, i) => (
              <button
                key={p.label}
                type="button"
                onClick={() => {
                  applyPreset(i);
                  setBatchRows(null);
                }}
                className={
                  i === presetIndex
                    ? "bg-sea px-3 py-1.5 text-sm text-foam"
                    : "border border-[var(--line)] bg-white/50 px-3 py-1.5 text-sm text-ink/80 transition hover:border-sea hover:text-sea"
                }
                title={p.hint}
              >
                {p.label}
              </button>
            ))}
          </div>
          {presets[presetIndex]?.hint && (
            <p className="font-mono text-xs text-sea">{presets[presetIndex].hint}</p>
          )}

          <label className="block space-y-1.5">
            <FieldLabel>Subject ID</FieldLabel>
            <TextInput
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
            />
          </label>

          <label className="block space-y-1.5">
            <FieldLabel>As of (optional ISO)</FieldLabel>
            <TextInput
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
              placeholder="2099-06-15T00:00:00Z"
            />
          </label>

          <label className="block space-y-1.5">
            <FieldLabel>Facts JSON</FieldLabel>
            <TextArea
              rows={10}
              value={factsText}
              onChange={(e) => setFactsText(e.target.value)}
              spellCheck={false}
            />
          </label>

          <div className="flex flex-wrap gap-2">
            <PrimaryButton
              type="button"
              disabled={loading || !domain}
              onClick={onCompare}
            >
              {loading ? "Comparing…" : "Compare Zen → Kogito"}
            </PrimaryButton>
            <PrimaryButton
              type="button"
              tone="ghost"
              disabled={loading || !domain}
              onClick={runAllSamples}
            >
              Run all samples
            </PrimaryButton>
          </div>
          <ErrorAlert message={error} />
        </div>

        <div className="space-y-4">
          {diff && (
            <div
              className={`border px-4 py-3 text-sm ${
                !diff.both_ok
                  ? "border-coral/30 bg-coral/5 text-coral"
                  : diff.decisions_agree
                    ? "border-sea/30 bg-sea/5 text-sea-deep"
                    : "border-[var(--line)] bg-white/70 text-ink/80"
              }`}
            >
              {!diff.both_ok && <p>One or both engines failed — see cards below.</p>}
              {diff.both_ok && diff.decisions_agree && (
                <p>
                  Decisions agree: <span className="font-medium capitalize">{diff.zen_decision}</span>
                  {diff.faster_engine ? (
                    <span className="ml-2 font-mono text-[11px]">
                      · faster={diff.faster_engine} · Δ{diff.wall_delta_millis} ms
                    </span>
                  ) : null}
                </p>
              )}
              {diff.both_ok && !diff.decisions_agree && (
                <p>
                  Decisions differ — Zen{" "}
                  <span className="font-medium capitalize">{diff.zen_decision}</span> vs
                  Kogito{" "}
                  <span className="font-medium capitalize">{diff.kogito_decision}</span>
                  <span className="ml-2 font-mono text-[11px] text-ink/50">
                    (JDM vs seeded DMN are not feature-parity)
                  </span>
                </p>
              )}
              {result && (
                <p className="mt-1 font-mono text-[11px] text-ink/45">
                  total {result.total_wall_millis.toFixed(1)} ms
                </p>
              )}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <EngineCard title="GoRules Zen" leg={result?.zen ?? null} />
            <EngineCard title="Kogito DMN" leg={result?.kogito ?? null} />
          </div>

          {!result && (
            <p className="text-sm text-ink/50">
              Pick a sample scenario and click Compare to see Zen and Kogito side
              by side.
            </p>
          )}
        </div>
      </div>

      {batchRows && batchRows.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-[family-name:var(--font-display)] text-xl text-ink">
            All samples
          </h3>
          <div className="overflow-x-auto border border-[var(--line)] bg-white/50">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="border-b border-[var(--line)] font-mono text-[10px] uppercase tracking-wider text-ink/45">
                <tr>
                  <th className="px-3 py-2 font-normal">Scenario</th>
                  <th className="px-3 py-2 font-normal">Zen</th>
                  <th className="px-3 py-2 font-normal">ms</th>
                  <th className="px-3 py-2 font-normal">Kogito</th>
                  <th className="px-3 py-2 font-normal">ms</th>
                  <th className="px-3 py-2 font-normal">Agree</th>
                </tr>
              </thead>
              <tbody>
                {batchRows.map(({ label, compare }) => (
                  <tr
                    key={label}
                    className="border-b border-[var(--line)] last:border-0"
                  >
                    <td className="px-3 py-2 text-ink">{label}</td>
                    <td
                      className={`px-3 py-2 capitalize ${decisionTone(compare.zen.decision)}`}
                    >
                      {compare.zen.ok ? compare.zen.decision : "error"}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-ink/60">
                      {compare.zen.wall_millis.toFixed(1)}
                    </td>
                    <td
                      className={`px-3 py-2 capitalize ${decisionTone(compare.kogito.decision)}`}
                    >
                      {compare.kogito.ok ? compare.kogito.decision : "error"}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-ink/60">
                      {compare.kogito.wall_millis.toFixed(1)}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px]">
                      {compare.diff.decisions_agree ? (
                        <span className="text-sea">yes</span>
                      ) : (
                        <span className="text-coral">no</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
