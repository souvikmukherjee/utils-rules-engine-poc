"use client";

import { useWorkspace } from "@/lib/workspace";
import type { LoungeFramework } from "@/lib/catalog";

function cellTone(lounge: string | null): string {
  if (!lounge) return "bg-ink/[0.04] text-ink/35";
  if (lounge === "chairmans") return "bg-[#1a1a1a] text-[#f5e6c8]";
  if (lounge === "first") return "bg-[#3d2b1f] text-[#f0d9b5]";
  if (lounge === "business") return "bg-sea/90 text-foam";
  return "bg-sea/20 text-sea-deep";
}

function Matrix({ framework }: { framework: LoungeFramework }) {
  const tiers = framework.membership_tiers;
  const cabins = framework.travel_classes;
  const lookup = new Map(
    framework.matrix.map((c) => [`${c.tier}|${c.cabin}`, c]),
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-left text-sm">
        <thead>
          <tr>
            <th className="border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-ink/45">
              Tier \\ Cabin
            </th>
            {cabins.map((c) => (
              <th
                key={c.id}
                className="border border-[var(--line)] bg-white/70 px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-ink/55"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tiers.map((tier) => (
            <tr key={tier.id}>
              <th className="border border-[var(--line)] bg-white/60 px-3 py-2 font-medium text-ink">
                {tier.label}
              </th>
              {cabins.map((cabin) => {
                const cell = lookup.get(`${tier.id}|${cabin.id}`);
                const lounge = cell?.lounge ?? null;
                return (
                  <td
                    key={cabin.id}
                    className={`border border-[var(--line)] px-3 py-2.5 text-center text-xs font-medium ${cellTone(lounge)}`}
                  >
                    {cell?.lounge_label ?? "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FrameworkPanel() {
  const { catalog, domain } = useWorkspace();
  if (!catalog || domain?.id !== "lounge") return null;
  const framework = catalog.frameworks.lounge_matrix;
  if (!framework) return null;

  return (
    <section className="space-y-4 border border-[var(--line)] bg-white/40 p-5">
      <div className="max-w-2xl">
        <h3 className="font-[family-name:var(--font-display)] text-xl text-ink">
          {framework.title}
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-ink/65">
          {framework.summary}
        </p>
      </div>
      <div className="flex flex-wrap gap-2 text-[11px]">
        {framework.lounge_types.map((l) => (
          <span
            key={l.id}
            className={`px-2.5 py-1 ${cellTone(l.id)}`}
          >
            {l.label}
          </span>
        ))}
      </div>
      <Matrix framework={framework} />
      <p className="font-mono text-[11px] leading-relaxed text-ink/45">
        Example: Bronze + First cabin → First Lounge. Platinum + Economy →
        Business Lounge. Platinum One → Chairman&apos;s for every cabin.
      </p>
    </section>
  );
}
