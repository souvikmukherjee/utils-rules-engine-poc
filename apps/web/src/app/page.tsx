"use client";

import { useState } from "react";
import { AuditPanel } from "@/components/AuditPanel";
import { AuthorPanel } from "@/components/AuthorPanel";
import { EvaluatePanel } from "@/components/EvaluatePanel";
import { ReleasesPanel } from "@/components/ReleasesPanel";
import { SimulatePanel } from "@/components/SimulatePanel";

type Tab = "evaluate" | "author" | "simulate" | "releases" | "audit";

const TABS: { id: Tab; label: string }[] = [
  { id: "evaluate", label: "Evaluate" },
  { id: "author", label: "Author" },
  { id: "simulate", label: "Simulate" },
  { id: "releases", label: "Releases" },
  { id: "audit", label: "Audit" },
];

const TITLES: Record<Tab, string> = {
  evaluate: "Evaluate",
  author: "Author",
  simulate: "Simulate",
  releases: "Releases",
  audit: "Audit & entitlements",
};

export default function Home() {
  const [tab, setTab] = useState<Tab>("evaluate");

  return (
    <div className="hero-mesh grain min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-6 pt-8">
        <p className="font-[family-name:var(--font-display)] text-lg tracking-tight text-ink">
          Axiom
        </p>
        <p className="animate-pulse-soft font-mono text-xs uppercase tracking-[0.2em] text-sea">
          Lounge domain · PoC
        </p>
      </header>

      <main className="mx-auto max-w-5xl px-6 pb-20 pt-16">
        <section className="animate-rise max-w-2xl">
          <h1 className="font-[family-name:var(--font-display)] text-5xl leading-[1.05] tracking-tight text-ink sm:text-6xl">
            Axiom
          </h1>
          <p className="animate-rise-delay mt-4 max-w-md text-lg leading-relaxed text-ink/70">
            Decisions you can explain. Rules you can trust.
          </p>
          <div className="mt-8 flex flex-wrap gap-2">
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
          </h2>
          {tab === "evaluate" && <EvaluatePanel />}
          {tab === "author" && <AuthorPanel />}
          {tab === "simulate" && <SimulatePanel />}
          {tab === "releases" && <ReleasesPanel />}
          {tab === "audit" && <AuditPanel />}
        </section>
      </main>
    </div>
  );
}
