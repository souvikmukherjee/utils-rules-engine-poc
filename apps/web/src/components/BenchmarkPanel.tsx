"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getBenchmarkCompare,
  runBenchmark,
  runBenchmarkMatrix,
  type BenchmarkCompareResult,
  type BenchmarkCompareRow,
} from "@/lib/api";
import {
  ErrorAlert,
  FieldLabel,
  PrimaryButton,
  Select,
  TextInput,
} from "@/components/ui";

function fmt(n: number | null | undefined, digits = 1): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(digits)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(digits)}k`;
  return n.toFixed(digits);
}

function fmtInt(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

export function BenchmarkPanel() {
  const [data, setData] = useState<BenchmarkCompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const [columns, setColumns] = useState(10);
  const [rules, setRules] = useState(100);
  const [fires, setFires] = useState(1_000);
  const [seed, setSeed] = useState(42);
  const [valuesPerCol, setValuesPerCol] = useState(8);
  const [maxWork, setMaxWork] = useState(200_000_000);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const body = await getBenchmarkCompare();
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load benchmarks");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const work = useMemo(() => rules * fires, [rules, fires]);

  async function onRunCustom() {
    setBusy("custom");
    setError(null);
    try {
      await runBenchmark({
        column_count: columns,
        rule_count: rules,
        fire_count: fires,
        seed,
        values_per_column: valuesPerCol,
        max_work: maxWork,
        engines: ["zen", "dmn_table"],
        label: `custom ${columns}c/${rules}r/${fires}f`,
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setBusy(null);
    }
  }

  async function onRunMatrix(profile: "quick" | "full") {
    setBusy(profile);
    setError(null);
    try {
      const payload =
        profile === "quick"
          ? {
              column_count: columns,
              rule_counts: [100, 1_000],
              fire_counts: [1_000, 10_000],
              seed,
              max_work: maxWork,
              label: "quick-matrix",
            }
          : {
              column_count: columns,
              rule_counts: [100, 1_000, 10_000],
              fire_counts: [1_000, 10_000, 1_000_000],
              seed,
              max_work: maxWork,
              skip_over_cap: true,
              label: "full-matrix",
            };
      await runBenchmarkMatrix(payload);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Matrix failed");
    } finally {
      setBusy(null);
    }
  }

  const rows: BenchmarkCompareRow[] = data?.rows ?? [];
  const summary = data?.summary;

  return (
    <div className="space-y-10">
      <div className="max-w-3xl space-y-3">
        <p className="text-ink/70 leading-relaxed">
          Synthetic scale lab — generate your own variables and outcomes, fire
          them through <span className="font-medium text-ink">Zen</span> and a{" "}
          <span className="font-medium text-ink">DMN-style FIRST table</span>{" "}
          (Kogito semantics at scale), and persist results so this view stays
          objective on every reload.
        </p>
        <p className="font-mono text-xs text-ink/45">
          Presets: rules 100 / 1k / 10k · fires 1k / 10k / 1M · columns tunable.
          Live Kogito HTTP is lounge-DMN only; scale cells use identical generated
          rules on both engines.
        </p>
      </div>

      <ErrorAlert message={error} />

      {summary ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Stored cells" value={fmtInt(summary.cells)} />
          <StatCard
            label="Zen median throughput"
            value={`${fmt(summary.zen_median_fps, 0)} fps`}
          />
          <StatCard
            label="DMN-table median throughput"
            value={`${fmt(summary.dmn_table_median_fps, 0)} fps`}
          />
          <StatCard
            label="Parity range"
            value={
              summary.parity_min_pct == null
                ? "—"
                : `${summary.parity_min_pct}–${summary.parity_max_pct}%`
            }
          />
        </div>
      ) : null}

      <section className="border border-[var(--line)] bg-white/50 p-5">
        <h3 className="font-[family-name:var(--font-display)] text-xl text-ink">
          Run parameters
        </h3>
        <p className="mt-1 text-sm text-ink/55">
          Anyone can change these and re-test. Work = rules × fires (sync cap
          via max_work).
        </p>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <label className="space-y-1">
            <FieldLabel>Columns (variables)</FieldLabel>
            <Select
              id="bench-columns"
              aria-label="Benchmark columns"
              value={columns}
              onChange={(e) => setColumns(Number(e.target.value))}
            >
              {[5, 8, 10, 12, 15, 20, 30, 40, 50].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1">
            <FieldLabel>Rules</FieldLabel>
            <Select
              id="bench-rules"
              aria-label="Benchmark rules"
              value={rules}
              onChange={(e) => setRules(Number(e.target.value))}
            >
              {[50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000].map((n) => (
                <option key={n} value={n}>
                  {n.toLocaleString()}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1">
            <FieldLabel>Fires</FieldLabel>
            <Select
              id="bench-fires"
              aria-label="Benchmark fires"
              value={fires}
              onChange={(e) => setFires(Number(e.target.value))}
            >
              {[100, 500, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000].map(
                (n) => (
                  <option key={n} value={n}>
                    {n.toLocaleString()}
                  </option>
                ),
              )}
            </Select>
          </label>
          <label className="space-y-1">
            <FieldLabel>Values / column</FieldLabel>
            <Select
              value={valuesPerCol}
              onChange={(e) => setValuesPerCol(Number(e.target.value))}
            >
              {[4, 6, 8, 12, 16].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1">
            <FieldLabel>Seed</FieldLabel>
            <TextInput
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value) || 0)}
            />
          </label>
          <label className="space-y-1">
            <FieldLabel>Max work (rules×fires)</FieldLabel>
            <TextInput
              type="number"
              value={maxWork}
              onChange={(e) => setMaxWork(Number(e.target.value) || 0)}
            />
          </label>
        </div>

        <p className="mt-3 font-mono text-xs text-ink/50">
          Estimated work: {work.toLocaleString()}
          {work > maxWork ? " · exceeds max_work (run will 400)" : ""}
        </p>

        <div className="mt-5 flex flex-wrap gap-2">
          <PrimaryButton
            disabled={busy != null}
            onClick={() => void onRunCustom()}
          >
            {busy === "custom" ? "Running…" : "Run custom cell"}
          </PrimaryButton>
          <PrimaryButton
            tone="ghost"
            disabled={busy != null}
            onClick={() => void onRunMatrix("quick")}
          >
            {busy === "quick" ? "Running…" : "Quick matrix (≤10k fires)"}
          </PrimaryButton>
          <PrimaryButton
            tone="ink"
            disabled={busy != null}
            onClick={() => void onRunMatrix("full")}
          >
            {busy === "full" ? "Running…" : "Full matrix (incl. 1M where under cap)"}
          </PrimaryButton>
          <PrimaryButton
            tone="ghost"
            disabled={busy != null}
            onClick={() => void refresh()}
          >
            Refresh stored
          </PrimaryButton>
        </div>
      </section>

      <section>
        <h3 className="mb-3 font-[family-name:var(--font-display)] text-xl text-ink">
          Objective comparison
        </h3>
        {rows.length === 0 ? (
          <p className="text-sm text-ink/55">
            No stored runs yet — run a custom cell or quick matrix to populate
            this table.
          </p>
        ) : (
          <div className="overflow-x-auto border border-[var(--line)]">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-white/70 font-mono text-xs uppercase tracking-wider text-ink/50">
                <tr>
                  <th className="px-3 py-2">Cols</th>
                  <th className="px-3 py-2">Rules</th>
                  <th className="px-3 py-2">Fires</th>
                  <th className="px-3 py-2">Zen fps</th>
                  <th className="px-3 py-2">DMN fps</th>
                  <th className="px-3 py-2">Zen ms</th>
                  <th className="px-3 py-2">DMN ms</th>
                  <th className="px-3 py-2">Parity</th>
                  <th className="px-3 py-2">Outcomes</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr
                    key={`${r.fingerprint ?? r.run_id}-${r.rule_count}-${r.fire_count}`}
                    className="border-t border-[var(--line)] odd:bg-white/30"
                  >
                    <td className="px-3 py-2 font-mono">{r.column_count}</td>
                    <td className="px-3 py-2 font-mono">
                      {fmtInt(r.rule_count)}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      {fmtInt(r.fire_count)}
                    </td>
                    <td className="px-3 py-2 font-mono text-sea">
                      {fmt(r.zen_throughput_fps, 0)}
                    </td>
                    <td className="px-3 py-2 font-mono text-sea">
                      {fmt(r.dmn_throughput_fps, 0)}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      {fmt(r.zen_elapsed_ms, 0)}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      {fmt(r.dmn_elapsed_ms, 1)}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      {r.parity_pct == null ? "—" : `${r.parity_pct}%`}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-ink/55">
                      {(r.sample_outcomes || []).slice(0, 4).join(", ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {rows[0]?.variables?.length ? (
        <section className="border border-[var(--line)] bg-white/40 p-4">
          <h3 className="font-mono text-xs uppercase tracking-wider text-ink/50">
            Generated variables (latest cell sample)
          </h3>
          <p className="mt-2 font-mono text-sm text-ink/80">
            {rows[rows.length - 1]?.variables?.join(", ")}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[var(--line)] bg-white/50 px-4 py-3">
      <p className="font-mono text-xs uppercase tracking-wider text-ink/45">
        {label}
      </p>
      <p className="mt-1 font-[family-name:var(--font-display)] text-2xl text-ink">
        {value}
      </p>
    </div>
  );
}
