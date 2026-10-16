"use client";

import { useEffect, useMemo, useState } from "react";
import { evaluate, type EvaluateResult } from "@/lib/api";
import { scenariosForDomain } from "@/lib/constants";
import { useWorkspace } from "@/lib/workspace";
import { FrameworkPanel } from "./FrameworkPanel";
import { ErrorAlert, FieldLabel, PrimaryButton, TextArea, TextInput } from "./ui";

function decisionTone(decision: string): string {
  if (decision === "allow") return "text-sea";
  if (decision === "deny") return "text-coral";
  return "text-ink/60";
}

function loungeFromResult(result: EvaluateResult): string | null {
  for (const effect of result.effects) {
    const label = effect.lounge_label ?? effect.lounge_type;
    if (typeof label === "string" && label) return label;
  }
  return null;
}

export function EvaluatePanel() {
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
  const [result, setResult] = useState<EvaluateResult | null>(null);

  useEffect(() => {
    const p = presets[0];
    if (!p) return;
    setPresetIndex(0);
    setSubjectId(p.subject_id);
    setFactsText(JSON.stringify(p.facts, null, 2));
    setResult(null);
    setError(null);
  }, [presets]);

  async function onEvaluate() {
    if (!domain) return;
    setLoading(true);
    setError(null);
    try {
      const facts = JSON.parse(factsText) as Record<string, unknown>;
      const data = await evaluate({
        domain: domain.id,
        pack_id: domain.pack_id,
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
    const preset = presets[index];
    if (!preset) return;
    setPresetIndex(index);
    setSubjectId(preset.subject_id);
    setFactsText(JSON.stringify(preset.facts, null, 2));
  }

  const loungeLabel = result ? loungeFromResult(result) : null;

  return (
    <div className="space-y-8">
      <p className="border border-[var(--line)] bg-white/50 px-4 py-3 text-sm text-ink/70">
        The colour matrix below is the business view of eligibility. The
        executable <span className="font-medium text-ink">JDM decision graph</span>{" "}
        (Request → table → Response) lives under{" "}
        <span className="font-medium text-sea">Author · Graph</span> — open a
        decision-table node to edit rows like a spreadsheet.
      </p>
      <FrameworkPanel />

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {presets.map((p, i) => (
              <button
                key={p.label}
                type="button"
                onClick={() => applyPreset(i)}
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
            <p className="font-mono text-xs text-sea">
              {presets[presetIndex].hint}
            </p>
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
              rows={12}
              value={factsText}
              onChange={(e) => setFactsText(e.target.value)}
              spellCheck={false}
            />
          </label>

          <PrimaryButton type="button" disabled={loading || !domain} onClick={onEvaluate}>
            {loading ? "Evaluating…" : `Evaluate · ${domain?.name ?? "—"}`}
          </PrimaryButton>
          <ErrorAlert message={error} />
        </div>

        <div className="space-y-4 border border-[var(--line)] bg-white/50 p-5">
          {!result && (
            <p className="text-sm text-ink/50">
              Run a scenario to see the decision + lounge outcome (Zen or
              Kogito).
            </p>
          )}
          {result && (
            <>
              <div>
                <p
                  className={`font-[family-name:var(--font-display)] text-4xl capitalize ${decisionTone(result.decision)}`}
                >
                  {result.decision}
                </p>
                {loungeLabel && (
                  <p className="mt-2 font-[family-name:var(--font-display)] text-xl text-ink">
                    {loungeLabel}
                  </p>
                )}
                <p className="mt-1 font-mono text-[11px] text-ink/45">
                  engine={result.engine ?? result.trace.engine ?? "zen"} · path=
                  {result.trace.path} · pack={result.pack_version} · id=
                  {result.evaluation_id.slice(0, 8)}…
                </p>
              </div>

              <div>
                <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-ink/45">
                  Effects
                </h4>
                <pre className="overflow-x-auto bg-ink/[0.03] p-3 font-mono text-xs leading-relaxed text-ink/80">
                  {JSON.stringify(result.effects, null, 2)}
                </pre>
              </div>

              <div>
                <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-ink/45">
                  Rule trace
                </h4>
                <ul className="space-y-2">
                  {result.trace.entries
                    .filter((e) => e.status === "matched")
                    .map((e) => (
                      <li
                        key={`${e.rule_id}-${e.status}`}
                        className="border border-[var(--line)] bg-white/70 px-3 py-2 text-sm"
                      >
                        <span className="font-medium text-ink">{e.rule_id}</span>
                        <span className="ml-2 font-mono text-[11px] text-sea">
                          {e.status} · {e.reason}
                        </span>
                      </li>
                    ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
