"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createPackVersion,
  getPackVersion,
  listPacks,
  transitionPackVersion,
  updatePackVersion,
  type PackVersionSummary,
  type Role,
  type RulePack,
} from "@/lib/api";
import {
  DEFAULT_DOMAIN,
  DEFAULT_PACK_ID,
  LIFECYCLE_TRANSITIONS,
} from "@/lib/constants";
import { JdmEditor } from "./JdmEditor";
import {
  ErrorAlert,
  FieldLabel,
  PrimaryButton,
  RoleSelect,
  Select,
  TextInput,
  lifecycleTone,
} from "./ui";

export function AuthorPanel() {
  const [role, setRole] = useState<Role>("author");
  const [versions, setVersions] = useState<PackVersionSummary[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [pack, setPack] = useState<RulePack | null>(null);
  const [dirty, setDirty] = useState(false);
  const [changeRecordId, setChangeRecordId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refreshVersions = useCallback(async () => {
    const rows = await listPacks(DEFAULT_DOMAIN);
    setVersions(rows);
    if (!selectedKey && rows.length) {
      const first = rows[0];
      setSelectedKey(`${first.pack_id}@${first.version}`);
    }
  }, [selectedKey]);

  useEffect(() => {
    refreshVersions().catch((err) =>
      setError(err instanceof Error ? err.message : String(err)),
    );
  }, [refreshVersions]);

  useEffect(() => {
    if (!selectedKey) return;
    const [packId, version] = selectedKey.split("@");
    const abortController = new AbortController();
    setBusy(true);
    setError(null);
    setPack(null);
    getPackVersion(DEFAULT_DOMAIN, packId, version)
      .then((p) => {
        if (!abortController.signal.aborted) {
          setPack(p);
          setDirty(false);
          setMessage(null);
        }
      })
      .catch((err) => {
        if (!abortController.signal.aborted) {
          setPack(null);
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!abortController.signal.aborted) {
          setBusy(false);
        }
      });
    return () => abortController.abort();
  }, [selectedKey]);

  async function handleClone() {
    setBusy(true);
    setError(null);
    try {
      const created = await createPackVersion(
        DEFAULT_DOMAIN,
        DEFAULT_PACK_ID,
        {
          clone_from_version: pack?.version ?? "1.0.0",
        },
        role,
      );
      await refreshVersions();
      setSelectedKey(`${created.pack_id}@${created.version}`);
      setMessage(`Draft ${created.version} created from ${pack?.version ?? "seed"}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    if (!pack || pack.lifecycle !== "draft") return;
    setBusy(true);
    setError(null);
    try {
      const saved = await updatePackVersion(
        pack.domain,
        pack.pack_id,
        pack.version,
        pack,
        role,
      );
      setPack(saved);
      setDirty(false);
      setMessage("Draft JDM saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleTransition(to: string, needsChangeRecord?: boolean) {
    if (!pack) return;
    if (needsChangeRecord && !changeRecordId.trim()) {
      setError("change_record_id is required to publish.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await transitionPackVersion(
        pack.domain,
        pack.pack_id,
        pack.version,
        {
          to,
          change_record_id: needsChangeRecord ? changeRecordId.trim() : null,
        },
        role,
      );
      const refreshed = await getPackVersion(
        pack.domain,
        pack.pack_id,
        pack.version,
      );
      setPack(refreshed);
      setDirty(false);
      await refreshVersions();
      setMessage(`Transitioned to ${to}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const transitions = pack
    ? LIFECYCLE_TRANSITIONS[pack.lifecycle] ?? []
    : [];
  const editable = pack?.lifecycle === "draft";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <FieldLabel>Role</FieldLabel>
          <RoleSelect value={role} onChange={setRole} />
        </div>
        <div className="min-w-[220px] flex-1">
          <FieldLabel>Pack version</FieldLabel>
          <Select
            value={selectedKey ?? ""}
            onChange={(e) => setSelectedKey(e.target.value || null)}
          >
            {versions.map((v) => (
              <option key={`${v.pack_id}@${v.version}`} value={`${v.pack_id}@${v.version}`}>
                {v.pack_id}@{v.version} · {v.lifecycle}
              </option>
            ))}
          </Select>
        </div>
        <PrimaryButton type="button" disabled={busy} onClick={handleClone}>
          Clone to draft
        </PrimaryButton>
        <PrimaryButton
          type="button"
          disabled={busy || !editable || !dirty}
          onClick={handleSave}
        >
          Save JDM
        </PrimaryButton>
      </div>

      {pack && (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className={`font-mono ${lifecycleTone(pack.lifecycle)}`}>
            {pack.lifecycle}
          </span>
          <span className="text-ink/50">
            {pack.pack_id}@{pack.version}
          </span>
          {dirty && <span className="text-coral">Unsaved changes</span>}
          {!editable && (
            <span className="text-ink/45">
              Published versions are immutable — clone to edit.
            </span>
          )}
        </div>
      )}

      {pack && transitions.length > 0 && (
        <div className="flex flex-wrap items-end gap-3 border border-[var(--line)] bg-white/50 p-4">
          <div className="min-w-[200px]">
            <FieldLabel>Change record (publish)</FieldLabel>
            <TextInput
              value={changeRecordId}
              onChange={(e) => setChangeRecordId(e.target.value)}
              placeholder="CR-…"
            />
          </div>
          {transitions.map((t) => (
            <PrimaryButton
              key={t.to}
              type="button"
              disabled={busy}
              onClick={() => handleTransition(t.to, t.needsChangeRecord)}
            >
              {t.label}
            </PrimaryButton>
          ))}
        </div>
      )}

      <ErrorAlert message={error} />
      {message && (
        <p className="font-mono text-xs text-sea">{message}</p>
      )}

      {pack && (
        <div className="space-y-2">
          <div className="flex items-baseline justify-between gap-4">
            <h3 className="font-[family-name:var(--font-display)] text-xl text-ink">
              JSON Decision Model
            </h3>
            <p className="text-xs text-ink/50">
              Powered by GoRules JDM Editor · evaluated by Zen
            </p>
          </div>
          <JdmEditor
            value={{ nodes: pack.nodes, edges: pack.edges }}
            disabled={!editable}
            onChange={(graph) => {
              setPack({ ...pack, nodes: graph.nodes, edges: graph.edges });
              setDirty(true);
            }}
          />
        </div>
      )}

      {!pack && !error && (
        <p className="text-sm text-ink/50">
          {busy ? "Loading pack…" : "Select a pack version to author."}
        </p>
      )}
    </div>
  );
}
