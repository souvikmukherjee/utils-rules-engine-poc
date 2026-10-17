"use client";

import { useState } from "react";
import { AuditPanel } from "@/components/AuditPanel";
import { AuthorPanel } from "@/components/AuthorPanel";
import { BenchmarkPanel } from "@/components/BenchmarkPanel";
import { EngineToggle } from "@/components/EngineToggle";
import { EvaluatePanel } from "@/components/EvaluatePanel";
import { ReleasesPanel } from "@/components/ReleasesPanel";
import { SimulatePanel } from "@/components/SimulatePanel";
import { WorkspaceBar } from "@/components/WorkspaceBar";
import { useEngine } from "@/lib/engine";
import { WorkspaceProvider, useWorkspace } from "@/lib/workspace";

type Tab =
  | "evaluate"
  | "author"
  | "simulate"
  | "benchmark"
  | "releases"
  | "audit";

const TABS: { id: Tab; label: string }[] = [
  { id: "evaluate", label: "Evaluate" },
  { id: "author", label: "Author · Graph" },
  { id: "simulate", label: "Simulate" },
  { id: "benchmark", label: "Benchmark" },
  { id: "releases", label: "Releases" },
  { id: "audit", label: "Audit" },
];

const TITLES: Record<Tab, string> = {
  evaluate: "Evaluate",
  author: "Author · JDM decision graph",
  simulate: "Simulate",
  benchmark: "Scale benchmark · Zen vs DMN table",
  releases: "Releases & change management",
  audit: "Audit & entitlements",
};

function HomeInner() {
  const [tab, setTab] = useState<Tab>("evaluate");
  const { domain } = useWorkspace();
  const { engine } = useEngine();
  const wide = tab === "author" || tab === "evaluate" || tab === "benchmark";

  return (
    <div className="hero-mesh grain min-h-screen">
      <header
        className={`mx-auto flex items-center justify-between gap-4 px-6 pt-8 ${
          wide ? "max-w-7xl" : "max-w-5xl"
        }`}
      >
        <p className="font-[family-name:var(--font-display)] text-lg tracking-tight text-ink">
          Axiom
        </p>
        <div className="flex flex-wrap items-center justify-end gap-3">
          <EngineToggle />
          <p className="animate-pulse-soft font-mono text-xs uppercase tracking-[0.2em] text-sea">
            {engine === "kogito" ? "Kogito" : "Zen"} · {domain?.name ?? "…"} ·{" "}
            {domain?.industry ?? "—"}
          </p>
        </div>
      </header>

      <main
        className={`mx-auto px-6 pb-20 pt-16 ${wide ? "max-w-7xl" : "max-w-5xl"}`}
      >
        <section className="animate-rise max-w-3xl">
          <h1 className="font-[family-name:var(--font-display)] text-5xl leading-[1.05] tracking-tight text-ink sm:text-6xl">
            Axiom
          </h1>
          <p className="animate-rise-delay mt-4 max-w-xl text-lg leading-relaxed text-ink/70">
            Multi-domain decision governance — loyalty, lounge, ops, airports,
            or banking credit — with a Zen or Kogito runtime toggle.
          </p>
          <div className="mt-8">
            <WorkspaceBar />
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={
                  tab === t.id
                    ? "bg-sea px-4 py-2 text-sm text-foam"
                    : "border border-[var(--line)] bg-white/40 px-4 py-2 text-sm text-ink/70 hover:border-sea"
                }
              >
                {t.label}
              </button>
            ))}
          </div>
        </section>

        <section className="mt-14 border-t border-[var(--line)] pt-10">
          <h2 className="mb-6 font-[family-name:var(--font-display)] text-2xl text-ink">
            {TITLES[tab]}
            {domain ? (
              <span className="ml-3 font-mono text-sm font-normal text-ink/40">
                {domain.pack_id}
              </span>
            ) : null}
          </h2>
          {tab === "evaluate" && <EvaluatePanel />}
          {tab === "author" && <AuthorPanel />}
          {tab === "simulate" && <SimulatePanel />}
          {tab === "benchmark" && <BenchmarkPanel />}
          {tab === "releases" && <ReleasesPanel />}
          {tab === "audit" && <AuditPanel />}
        </section>
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <WorkspaceProvider>
      <HomeInner />
    </WorkspaceProvider>
  );
}
