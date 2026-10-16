"use client";

import { useWorkspace } from "@/lib/workspace";
import { FieldLabel, Select } from "./ui";

export function WorkspaceBar() {
  const {
    catalog,
    loading,
    error,
    persona,
    domain,
    allowedDomains,
    setPersonaId,
    setDomainId,
  } = useWorkspace();

  if (loading) {
    return (
      <p className="font-mono text-xs text-ink/45">Loading workspace…</p>
    );
  }
  if (error || !catalog) {
    return (
      <p className="text-sm text-coral">{error ?? "Catalog unavailable"}</p>
    );
  }

  return (
    <div className="flex flex-wrap items-end gap-4 border border-[var(--line)] bg-white/50 p-4">
      <div className="min-w-[220px] flex-1">
        <FieldLabel>Persona</FieldLabel>
        <Select
          value={persona?.id ?? ""}
          onChange={(e) => setPersonaId(e.target.value)}
        >
          {catalog.personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} · {p.role}
            </option>
          ))}
        </Select>
        {persona && (
          <p className="mt-1.5 text-xs leading-relaxed text-ink/55">
            {persona.title} — {persona.bio}
          </p>
        )}
      </div>
      <div className="min-w-[200px] flex-1">
        <FieldLabel>Domain</FieldLabel>
        <Select
          value={domain?.id ?? ""}
          onChange={(e) => setDomainId(e.target.value)}
        >
          {allowedDomains.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
              {d.industry === "banking" ? " · banking" : ""}
            </option>
          ))}
        </Select>
        {domain && (
          <p className="mt-1.5 text-xs leading-relaxed text-ink/55">
            {domain.blurb}
          </p>
        )}
      </div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-sea">
        Role {persona?.role ?? "—"}
      </div>
    </div>
  );
}
