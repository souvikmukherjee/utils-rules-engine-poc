"use client";

import { useEngine, type RulesEngine } from "@/lib/engine";

const OPTIONS: { id: RulesEngine; label: string; hint: string }[] = [
  { id: "zen", label: "Zen", hint: "GoRules" },
  { id: "kogito", label: "Kogito", hint: "DMN · Red Hat / KIE" },
];

export function EngineToggle() {
  const { engine, setEngine } = useEngine();

  return (
    <div
      className="inline-flex items-center gap-1 border border-[var(--line)] bg-white/50 p-1"
      role="group"
      aria-label="Rules engine"
    >
      {OPTIONS.map((opt) => {
        const active = engine === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => setEngine(opt.id)}
            aria-pressed={active}
            title={`Evaluate with ${opt.label} (${opt.hint})`}
            className={
              active
                ? "bg-sea px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.16em] text-foam"
                : "px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.16em] text-ink/55 hover:text-ink"
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
