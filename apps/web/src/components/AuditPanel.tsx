"use client";

import { useState } from "react";
import {
  listEntitlements,
  searchAudit,
  type AuditEvent,
  type Entitlement,
} from "@/lib/api";
import { useWorkspace } from "@/lib/workspace";
import { ErrorAlert, FieldLabel, PrimaryButton, TextInput } from "./ui";

export function AuditPanel() {
  const { domain } = useWorkspace();
  const [subjectId, setSubjectId] = useState("FF-GRANDFATHERED");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [ents, setEnts] = useState<Entitlement[]>([]);
  const [searched, setSearched] = useState(false);

  async function onSearch() {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const domainId = domain?.id ?? "lounge";
      const [audit, entitlements] = await Promise.all([
        searchAudit(subjectId, domainId),
        listEntitlements(subjectId, domainId),
      ]);
      setEvents(audit);
      setEnts(entitlements);
    } catch (err) {
      setEvents([]);
      setEnts([]);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  const grandfathered = ents.filter((e) => e.grandfathered);
  const other = ents.filter((e) => !e.grandfathered);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <label className="block flex-1 space-y-1.5">
          <FieldLabel>Subject ID</FieldLabel>
          <TextInput
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
          />
        </label>
        <PrimaryButton tone="ink" onClick={() => void onSearch()} disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </PrimaryButton>
      </div>

      <ErrorAlert message={error} />

      <div>
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="font-[family-name:var(--font-display)] text-xl">
            Entitlements
          </h3>
          {searched && (
            <p className="font-mono text-xs text-ink/45">
              {ents.length} total
              {grandfathered.length
                ? ` · ${grandfathered.length} grandfathered`
                : ""}
            </p>
          )}
        </div>

        {searched && ents.length === 0 && !error && (
          <p className="text-sm text-ink/45">
            No entitlements for this subject.
          </p>
        )}
        {!searched && (
          <p className="text-sm text-ink/45">
            Look up a subject to browse entitlements (grandfathered grants are
            highlighted) and evaluation history.
          </p>
        )}

        {ents.length > 0 && (
          <ul className="divide-y divide-[var(--line)] border border-[var(--line)] bg-white/40">
            {[...grandfathered, ...other].map((e) => (
              <li
                key={e.entitlement_id}
                className={`px-4 py-3 text-sm ${
                  e.grandfathered
                    ? "border-l-4 border-l-coral bg-coral/5"
                    : "border-l-4 border-l-transparent"
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium">{e.benefit_type}</span>
                  <span className="font-mono text-xs text-ink/50">
                    {e.status}
                    {e.grandfathered ? (
                      <span className="ml-2 text-coral">grandfathered</span>
                    ) : null}
                  </span>
                </div>
                <p className="mt-1 font-mono text-xs text-ink/45">
                  {e.entitlement_id.slice(0, 12)}… · pack{" "}
                  {e.source_pack_version ?? "—"} · rule {e.source_rule_id ?? "—"}
                </p>
                <p className="mt-0.5 font-mono text-xs text-ink/40">
                  granted {e.granted_at}
                  {e.expires_at ? ` · expires ${e.expires_at}` : ""}
                  {e.cohort_key ? ` · cohort ${e.cohort_key}` : ""}
                </p>
                {Object.keys(e.benefit_payload ?? {}).length > 0 && (
                  <pre className="mt-2 overflow-x-auto font-mono text-xs text-ink/55">
                    {JSON.stringify(e.benefit_payload, null, 2)}
                  </pre>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h3 className="mb-3 font-[family-name:var(--font-display)] text-xl">
          Evaluations
        </h3>
        {searched && events.length === 0 && !error && (
          <p className="text-sm text-ink/45">
            No evaluations yet for this subject. Run Evaluate first, then search.
          </p>
        )}
        <ul className="divide-y divide-[var(--line)] border border-[var(--line)] bg-white/40">
          {events.map((ev) => (
            <li key={ev.evaluation_id} className="px-4 py-3 text-sm">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium capitalize">{ev.decision}</span>
                <span className="font-mono text-xs text-ink/50">
                  {ev.path} · {ev.pack_version}
                </span>
              </div>
              <p className="mt-1 font-mono text-xs text-ink/45">
                {ev.evaluation_id} · as_of {ev.as_of} · {ev.created_at}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
