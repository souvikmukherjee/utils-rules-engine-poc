"use client";

import { useState } from "react";
import { evaluate, type EvaluateResult } from "@/lib/api";

const PRESETS: { label: string; subject_id: string; facts: string }[] = [
  {
    label: "Gold member",
    subject_id: "FF-1001",
    facts: JSON.stringify(
      { membership: { tier: "gold" } },
      null,
      2,
    ),
  },
  {
    label: "Partner elite",
    subject_id: "FF-2002",
    facts: JSON.stringify(
      {
        membership: { tier: "silver" },
        partner: { airline: "Qantas", elite_tier: "gold" },
      },
      null,
      2,
    ),
  },
  {
    label: "Grandfathered",
    subject_id: "FF-GRANDFATHERED",
    facts: JSON.stringify(
      { membership: { tier: "silver" } },
      null,
      2,
    ),
  },
  {
    label: "Silver (no access)",
    subject_id: "FF-3003",
    facts: JSON.stringify(
      { membership: { tier: "silver" } },
      null,
      2,
    ),
  },
];

function decisionTone(decision: string): string {
  if (decision === "allow") return "text-sea";
  if (decision === "deny") return "text-coral";
  return "text-ink/60";
}

export function EvaluatePanel() {
  const [subjectId, setSubjectId] = useState(PRESETS[0].subject_id);
  const [factsText, setFactsText] = useState(PRESETS[0].facts);
  const [asOf, setAsOf] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluateResult | null>(null);

  async function onEvaluate() {
    setLoading(true);
    setError(null);
    try {
      const facts = JSON.parse(factsText) as Record<string, unknown>;
      const data = await evaluate({
        subject_id: subjectId,
        facts,
        as_of: asOf || null,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setLoading(false);
    }
  }

  function applyPreset(index: number) {
    const preset = PRESETS[index];
    setSubjectId(preset.subject_id);
    setFactsText(preset.facts);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div className="space-y-5">
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p, i) => (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(i)}
              className="border border-[var(--line)] bg-white/50 px-3 py-1.5 text-sm text-ink/80 transition hover:border-sea hover:text-sea"
            >
              {p.label}
            </button>
          ))}
        </div>

        <label className="block space-y-1.5">
          <span className="font-mono text-xs uppercase tracking-wider text-ink/50">
            Subject ID
          </span>
          <input
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            className="w-full border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-sm outline-none ring-sea/30 focus:ring-2"
          />
        </label>

        <label className="block space-y-1.5">
          <span className="font-mono text-xs uppercase tracking-wider text-ink/50">
            As of (optional ISO)
          </span>
          <input
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
            placeholder="2026-06-01T00:00:00Z"
            className="w-full border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-sm outline-none ring-sea/30 focus:ring-2"
          />
        </label>

        <label className="block space-y-1.5">
          <span className="font-mono text-xs uppercase tracking-wider text-ink/50">
            Facts JSON
          </span>
          <textarea
            value={factsText}
            onChange={(e) => setFactsText(e.target.value)}
            rows={12}
            className="w-full resize-y border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-sm leading-relaxed outline-none ring-sea/30 focus:ring-2"
          />
        </label>

        <button
          type="button"
          onClick={onEvaluate}
          disabled={loading}
          className="bg-sea px-5 py-2.5 text-sm font-medium text-foam transition hover:bg-sea-deep disabled:opacity-50"
        >
          {loading ? "Evaluating…" : "Evaluate"}
        </button>

        {error && (
          <p className="text-sm text-coral" role="alert">
            {error}
          </p>
        )}
      </div>

      <div className="min-h-[20rem] border border-[var(--line)] bg-white/40 p-5">
        {!result && !error && (
          <p className="text-sm text-ink/45">
            Run an evaluation to see the decision, effects, and rule trace.
          </p>
        )}
        {result && (
          <div className="space-y-5 animate-rise">
            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-ink/50">
                Decision
              </p>
              <p
                className={`font-[family-name:var(--font-display)] text-4xl capitalize ${decisionTone(result.decision)}`}
              >
                {result.decision}
              </p>
              <p className="mt-1 font-mono text-xs text-ink/50">
                engine={result.engine ?? result.trace.engine ?? "zen"} · path=
                {result.trace.path} · pack={result.pack_version} · id=
                {result.evaluation_id.slice(0, 8)}…
              </p>
            </div>

            {result.entitlements_applied.length > 0 && (
              <div>
                <p className="mb-2 font-mono text-xs uppercase tracking-wider text-ink/50">
                  Entitlements honored
                </p>
                <ul className="space-y-2">
                  {result.entitlements_applied.map((e) => (
                    <li
                      key={String(e.entitlement_id)}
                      className="border-l-2 border-coral pl-3 text-sm"
                    >
                      <span className="font-medium">{String(e.benefit_type)}</span>
                      {e.grandfathered ? (
                        <span className="ml-2 font-mono text-xs text-coral">
                          grandfathered
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <p className="mb-2 font-mono text-xs uppercase tracking-wider text-ink/50">
                Rule trace
              </p>
              <ul className="space-y-2">
                {result.trace.entries.map((entry) => (
                  <li
                    key={entry.rule_id}
                    className="flex flex-col gap-0.5 border-b border-[var(--line)] pb-2 text-sm last:border-0"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <span className="font-medium">{entry.rule_name}</span>
                      <span className="font-mono text-xs text-ink/50">
                        {entry.status}
                        {entry.reason ? ` · ${entry.reason}` : ""}
                      </span>
                    </div>
                    <span className="font-mono text-xs text-ink/40">
                      {entry.rule_id}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
