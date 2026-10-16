"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getRelease,
  listPacks,
  promotePack,
  updateRelease,
  type PackVersionSummary,
  type ReleaseConfig,
  type Role,
} from "@/lib/api";
import { DEFAULT_DOMAIN, DEFAULT_PACK_ID } from "@/lib/constants";
import {
  ErrorAlert,
  FieldLabel,
  PrimaryButton,
  RoleSelect,
  Select,
  TextInput,
} from "./ui";

export function ReleasesPanel() {
  const [role, setRole] = useState<Role>("admin");
  const [environment, setEnvironment] = useState("production");
  const [versions, setVersions] = useState<PackVersionSummary[]>([]);
  const [release, setRelease] = useState<ReleaseConfig | null>(null);
  const [packVersion, setPackVersion] = useState("");
  const [goLiveAt, setGoLiveAt] = useState("");
  const [canaryPercent, setCanaryPercent] = useState("100");
  const [changeRecordId, setChangeRecordId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const applyRelease = useCallback((data: ReleaseConfig) => {
    setRelease(data);
    setPackVersion(data.pack_version ?? "");
    setGoLiveAt(data.go_live_at ?? "");
    setCanaryPercent(String(data.canary_percent ?? 100));
    setChangeRecordId(data.change_record_id ?? "");
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [rel, packs] = await Promise.all([
        getRelease(DEFAULT_DOMAIN, DEFAULT_PACK_ID, environment),
        listPacks(DEFAULT_DOMAIN).catch(() => [] as PackVersionSummary[]),
      ]);
      applyRelease(rel);
      setVersions(packs);
    } catch (err) {
      setRelease(null);
      setError(err instanceof Error ? err.message : "Failed to load release");
    } finally {
      setLoading(false);
    }
  }, [applyRelease, environment]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSave() {
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateRelease(
        DEFAULT_DOMAIN,
        DEFAULT_PACK_ID,
        {
          environment,
          pack_version: packVersion,
          go_live_at: goLiveAt || null,
          canary_percent: Number(canaryPercent) || 0,
          change_record_id: changeRecordId || null,
        },
        role,
      );
      applyRelease(updated);
      setNotice("Release configuration saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setLoading(false);
    }
  }

  async function onPromote() {
    if (!changeRecordId.trim()) {
      setError("change_record_id is required to promote");
      return;
    }
    if (!packVersion.trim()) {
      setError("pack_version is required to promote");
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await promotePack(
        DEFAULT_DOMAIN,
        DEFAULT_PACK_ID,
        {
          environment,
          pack_version: packVersion,
          change_record_id: changeRecordId.trim(),
          go_live_at: goLiveAt || null,
          canary_percent: Number(canaryPercent) || 0,
        },
        role,
      );
      applyRelease(updated);
      setNotice(`Promoted ${packVersion} to ${environment}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Promote failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <RoleSelect value={role} onChange={setRole} />
        <PrimaryButton tone="ghost" onClick={() => void load()} disabled={loading}>
          Refresh
        </PrimaryButton>
      </div>

      <ErrorAlert message={error} />
      {notice && <p className="text-sm text-sea">{notice}</p>}

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-4">
          <label className="block space-y-1.5">
            <FieldLabel>Environment</FieldLabel>
            <Select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
            >
              <option value="production">production</option>
              <option value="staging">staging</option>
              <option value="canary">canary</option>
            </Select>
          </label>

          <label className="block space-y-1.5">
            <FieldLabel>Pack version</FieldLabel>
            {versions.length > 0 ? (
              <Select
                value={packVersion}
                onChange={(e) => setPackVersion(e.target.value)}
              >
                <option value="">Select version</option>
                {versions.map((v) => (
                  <option key={v.version} value={v.version}>
                    {v.version} ({v.lifecycle})
                  </option>
                ))}
              </Select>
            ) : (
              <TextInput
                value={packVersion}
                onChange={(e) => setPackVersion(e.target.value)}
                placeholder="1.0.0"
              />
            )}
          </label>

          <label className="block space-y-1.5">
            <FieldLabel>Go live at</FieldLabel>
            <TextInput
              value={goLiveAt}
              onChange={(e) => setGoLiveAt(e.target.value)}
              placeholder="2026-07-01T00:00:00Z"
            />
          </label>

          <label className="block space-y-1.5">
            <FieldLabel>Canary percent</FieldLabel>
            <TextInput
              type="number"
              min={0}
              max={100}
              value={canaryPercent}
              onChange={(e) => setCanaryPercent(e.target.value)}
            />
          </label>

          <label className="block space-y-1.5">
            <FieldLabel>Change record ID</FieldLabel>
            <TextInput
              value={changeRecordId}
              onChange={(e) => setChangeRecordId(e.target.value)}
              placeholder="CR-2026-001"
            />
          </label>

          <div className="flex flex-wrap gap-2 pt-2">
            <PrimaryButton tone="ghost" onClick={() => void onSave()} disabled={loading}>
              Save release
            </PrimaryButton>
            <PrimaryButton onClick={() => void onPromote()} disabled={loading}>
              Promote
            </PrimaryButton>
          </div>
        </div>

        <div className="border border-[var(--line)] bg-white/40 p-5">
          <p className="font-mono text-xs uppercase tracking-wider text-ink/50">
            Current pointer
          </p>
          {!release && !error && (
            <p className="mt-3 text-sm text-ink/45">
              {loading ? "Loading…" : "No release loaded yet."}
            </p>
          )}
          {release && (
            <dl className="mt-4 space-y-3 text-sm animate-rise">
              <div>
                <dt className="font-mono text-xs text-ink/45">Domain / pack</dt>
                <dd>
                  {release.domain} / {release.pack_id}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-xs text-ink/45">Environment</dt>
                <dd>{release.environment}</dd>
              </div>
              <div>
                <dt className="font-mono text-xs text-ink/45">Serving version</dt>
                <dd className="font-[family-name:var(--font-display)] text-2xl text-sea">
                  {release.pack_version}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-xs text-ink/45">Go live</dt>
                <dd className="font-mono text-xs">
                  {release.go_live_at ?? "immediate"}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-xs text-ink/45">Canary</dt>
                <dd>{release.canary_percent}%</dd>
              </div>
              <div>
                <dt className="font-mono text-xs text-ink/45">Change record</dt>
                <dd className="font-mono text-xs">
                  {release.change_record_id ?? "—"}
                </dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </div>
  );
}
