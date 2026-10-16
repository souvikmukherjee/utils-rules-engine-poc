"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createPackVersion,
  getPackVersion,
  listPacks,
  transitionPackVersion,
  updatePackVersion,
  type EffectDraft,
  type PackVersionSummary,
  type Role,
  type RuleDraft,
  type RulePack,
} from "@/lib/api";
import {
  CONDITION_OPS,
  DEFAULT_DOMAIN,
  DEFAULT_PACK_ID,
  EFFECT_TYPES,
  LIFECYCLE_TRANSITIONS,
} from "@/lib/constants";
import {
  ErrorAlert,
  FieldLabel,
  PrimaryButton,
  RoleSelect,
  Select,
  TextArea,
  TextInput,
  lifecycleTone,
} from "./ui";

function emptyRule(): RuleDraft {
  return {
    id: "new-rule",
    name: "New rule",
    priority: 50,
    enabled: true,
    effective_from: "2024-01-01T00:00:00Z",
    effective_to: null,
    condition: { path: "membership.tier", op: "eq", value: "gold" },
    effects: [
      {
        type: "allow",
        payload: {},
        persist_as_entitlement: false,
      },
    ],
  };
}

function isSimpleCondition(c: Record<string, unknown>): boolean {
  return (
    typeof c.path === "string" &&
    typeof c.op === "string" &&
    !("all" in c) &&
    !("any" in c) &&
    !("not" in c)
  );
}

function formatValue(value: unknown): string {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function parseValue(raw: string, op: string): unknown {
  const trimmed = raw.trim();
  if (op === "exists") {
    if (trimmed === "true") return true;
    if (trimmed === "false") return false;
  }
  if (op === "in") {
    try {
      return JSON.parse(trimmed);
    } catch {
      return trimmed.split(",").map((s) => s.trim()).filter(Boolean);
    }
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return trimmed;
  }
}

export function AuthorPanel() {
  const [role, setRole] = useState<Role>("author");
  const [versions, setVersions] = useState<PackVersionSummary[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [pack, setPack] = useState<RulePack | null>(null);
  const [ruleIndex, setRuleIndex] = useState(0);
  const [conditionMode, setConditionMode] = useState<"simple" | "json">(
    "simple",
  );
  const [conditionJson, setConditionJson] = useState("");
  const [changeRecordId, setChangeRecordId] = useState("");
  const [cloneFrom, setCloneFrom] = useState("");
  const [newVersion, setNewVersion] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refreshVersions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await listPacks(DEFAULT_DOMAIN);
      setVersions(list);
      if (list.length && !selectedKey) {
        // Prefer an editable draft when present so authoring works immediately.
        const preferred =
          list.find((v) => v.lifecycle === "draft") ?? list[0];
        setSelectedKey(`${preferred.pack_id}@${preferred.version}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to list packs");
    } finally {
      setLoading(false);
    }
  }, [selectedKey]);

  useEffect(() => {
    void refreshVersions();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once on mount
  }, []);

  useEffect(() => {
    if (!selectedKey) return;
    const [packId, version] = selectedKey.split("@");
    if (!packId || !version) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setNotice(null);
      try {
        const data = await getPackVersion(DEFAULT_DOMAIN, packId, version);
        if (cancelled) return;
        setPack(data);
        setRuleIndex(0);
        const first = data.rules[0];
        if (first && isSimpleCondition(first.condition)) {
          setConditionMode("simple");
        } else if (first) {
          setConditionMode("json");
          setConditionJson(JSON.stringify(first.condition, null, 2));
        }
      } catch (err) {
        if (!cancelled) {
          setPack(null);
          setError(
            err instanceof Error ? err.message : "Failed to load pack version",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedKey]);

  const rule = pack?.rules[ruleIndex] ?? null;
  const editable = pack?.lifecycle === "draft";

  function updateRule(patch: Partial<RuleDraft>) {
    if (!pack || !rule) return;
    const rules = pack.rules.map((r, i) =>
      i === ruleIndex ? { ...r, ...patch } : r,
    );
    setPack({ ...pack, rules });
  }

  function updateEffect(ei: number, patch: Partial<EffectDraft>) {
    if (!rule) return;
    const effects = rule.effects.map((e, i) =>
      i === ei ? { ...e, ...patch } : e,
    );
    updateRule({ effects });
  }

  function syncConditionFromJson() {
    try {
      const parsed = JSON.parse(conditionJson) as Record<string, unknown>;
      updateRule({ condition: parsed });
      setError(null);
    } catch {
      setError("Condition JSON is invalid");
    }
  }

  async function onSave() {
    if (!pack) return;
    let packToSave = pack;
    if (conditionMode === "json") {
      try {
        const parsed = JSON.parse(conditionJson) as Record<string, unknown>;
        packToSave = {
          ...pack,
          rules: pack.rules.map((r, i) =>
            i === ruleIndex ? { ...r, condition: parsed } : r,
          ),
        };
        setPack(packToSave);
      } catch {
        setError("Condition JSON is invalid — fix before saving");
        return;
      }
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const saved = await updatePackVersion(
        packToSave.domain,
        packToSave.pack_id,
        packToSave.version,
        packToSave,
        role,
      );
      setPack(saved);
      setNotice(`Draft ${saved.version} saved.`);
      await refreshVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function onClone() {
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createPackVersion(
        DEFAULT_DOMAIN,
        DEFAULT_PACK_ID,
        {
          clone_from_version: cloneFrom || versions[0]?.version || null,
          version: newVersion.trim() || null,
        },
        role,
      );
      setNotice(`Created draft ${created.version}.`);
      setSelectedKey(`${created.pack_id}@${created.version}`);
      await refreshVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    } finally {
      setSaving(false);
    }
  }

  async function onTransition(to: string, needsChangeRecord?: boolean) {
    if (!pack) return;
    if (needsChangeRecord && !changeRecordId.trim()) {
      setError("change_record_id is required to publish");
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      await transitionPackVersion(
        pack.domain,
        pack.pack_id,
        pack.version,
        {
          to,
          change_record_id: needsChangeRecord
            ? changeRecordId.trim()
            : changeRecordId.trim() || null,
        },
        role,
      );
      setNotice(`Transitioned ${pack.version} → ${to}.`);
      const refreshed = await getPackVersion(
        pack.domain,
        pack.pack_id,
        pack.version,
      );
      setPack(refreshed);
      await refreshVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    } finally {
      setSaving(false);
    }
  }

  const transitions = pack
    ? (LIFECYCLE_TRANSITIONS[pack.lifecycle] ?? [])
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <RoleSelect value={role} onChange={setRole} />
        <PrimaryButton tone="ghost" onClick={() => void refreshVersions()}>
          Refresh packs
        </PrimaryButton>
      </div>

      <ErrorAlert message={error} />
      {notice && <p className="text-sm text-sea">{notice}</p>}

      <div className="grid gap-8 lg:grid-cols-[minmax(0,14rem)_1fr]">
        <aside className="space-y-4">
          <div>
            <p className="mb-2 font-mono text-xs uppercase tracking-wider text-ink/50">
              Versions
            </p>
            {loading && !versions.length && (
              <p className="text-sm text-ink/45">Loading…</p>
            )}
            {!loading && versions.length === 0 && (
              <p className="text-sm text-ink/45">
                No pack versions returned. Start the API or create a draft.
              </p>
            )}
            <ul className="divide-y divide-[var(--line)] border border-[var(--line)] bg-white/40">
              {versions.map((v) => {
                const key = `${v.pack_id}@${v.version}`;
                const active = key === selectedKey;
                return (
                  <li key={key}>
                    <button
                      type="button"
                      onClick={() => setSelectedKey(key)}
                      className={`w-full px-3 py-2.5 text-left text-sm transition ${
                        active
                          ? "bg-sea/10 text-ink"
                          : "text-ink/75 hover:bg-white/60"
                      }`}
                    >
                      <span className="font-mono text-xs">{v.version}</span>
                      <span
                        className={`mt-0.5 block text-xs capitalize ${lifecycleTone(v.lifecycle)}`}
                      >
                        {v.lifecycle}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="space-y-2 border border-[var(--line)] bg-white/40 p-3">
            <p className="font-mono text-xs uppercase tracking-wider text-ink/50">
              New draft
            </p>
            <label className="block space-y-1">
              <FieldLabel>Clone from</FieldLabel>
              <Select
                value={cloneFrom}
                onChange={(e) => setCloneFrom(e.target.value)}
              >
                <option value="">Latest / default</option>
                {versions.map((v) => (
                  <option key={v.version} value={v.version}>
                    {v.version} ({v.lifecycle})
                  </option>
                ))}
              </Select>
            </label>
            <label className="block space-y-1">
              <FieldLabel>New version (optional)</FieldLabel>
              <TextInput
                value={newVersion}
                onChange={(e) => setNewVersion(e.target.value)}
                placeholder="1.1.0-draft"
              />
            </label>
            <PrimaryButton
              onClick={() => void onClone()}
              disabled={saving}
              className="w-full"
            >
              Create draft
            </PrimaryButton>
          </div>
        </aside>

        <div className="min-w-0 space-y-5">
          {!pack && !error && (
            <p className="text-sm text-ink/45">
              Select a pack version to author rules.
            </p>
          )}

          {pack && (
            <>
              <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-[var(--line)] pb-4">
                <div>
                  <p className="font-mono text-xs text-ink/45">
                    {pack.domain} / {pack.pack_id}
                  </p>
                  <h3 className="font-[family-name:var(--font-display)] text-2xl text-ink">
                    {pack.version}
                  </h3>
                  <p
                    className={`mt-1 text-sm capitalize ${lifecycleTone(pack.lifecycle)}`}
                  >
                    {pack.lifecycle}
                    {!editable ? " · read-only" : ""}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {editable && (
                    <PrimaryButton
                      onClick={() => void onSave()}
                      disabled={saving}
                    >
                      {saving ? "Saving…" : "Save draft"}
                    </PrimaryButton>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap items-end gap-3">
                <label className="block min-w-[12rem] flex-1 space-y-1.5">
                  <FieldLabel>Change record ID</FieldLabel>
                  <TextInput
                    value={changeRecordId}
                    onChange={(e) => setChangeRecordId(e.target.value)}
                    placeholder="CR-2026-001"
                  />
                </label>
                {transitions.map((t) => (
                  <PrimaryButton
                    key={t.to}
                    tone={t.needsChangeRecord ? "ink" : "ghost"}
                    disabled={saving}
                    onClick={() =>
                      void onTransition(t.to, t.needsChangeRecord)
                    }
                  >
                    {t.label}
                  </PrimaryButton>
                ))}
              </div>

              <div className="flex flex-wrap gap-2">
                {pack.rules.map((r, i) => (
                  <button
                    key={`${r.id}-${i}`}
                    type="button"
                    onClick={() => {
                      setRuleIndex(i);
                      if (isSimpleCondition(r.condition)) {
                        setConditionMode("simple");
                      } else {
                        setConditionMode("json");
                        setConditionJson(
                          JSON.stringify(r.condition, null, 2),
                        );
                      }
                    }}
                    className={
                      i === ruleIndex
                        ? "bg-sea px-3 py-1.5 text-sm text-foam"
                        : "border border-[var(--line)] bg-white/50 px-3 py-1.5 text-sm text-ink/80 hover:border-sea"
                    }
                  >
                    {r.id}
                  </button>
                ))}
                {editable && (
                  <PrimaryButton
                    tone="ghost"
                    onClick={() => {
                      const next = [...pack.rules, emptyRule()];
                      setPack({ ...pack, rules: next });
                      setRuleIndex(next.length - 1);
                      setConditionMode("simple");
                    }}
                  >
                    + Rule
                  </PrimaryButton>
                )}
              </div>

              {rule && (
                <div className="grid gap-5 lg:grid-cols-2">
                  <div className="space-y-4">
                    <label className="block space-y-1.5">
                      <FieldLabel>Rule ID</FieldLabel>
                      <TextInput
                        value={rule.id}
                        disabled={!editable}
                        onChange={(e) => updateRule({ id: e.target.value })}
                      />
                    </label>
                    <label className="block space-y-1.5">
                      <FieldLabel>Name</FieldLabel>
                      <TextInput
                        value={rule.name}
                        disabled={!editable}
                        onChange={(e) => updateRule({ name: e.target.value })}
                      />
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <label className="block space-y-1.5">
                        <FieldLabel>Priority</FieldLabel>
                        <TextInput
                          type="number"
                          value={rule.priority}
                          disabled={!editable}
                          onChange={(e) =>
                            updateRule({
                              priority: Number(e.target.value) || 0,
                            })
                          }
                        />
                      </label>
                      <label className="flex items-end gap-2 pb-2">
                        <input
                          type="checkbox"
                          checked={rule.enabled !== false}
                          disabled={!editable}
                          onChange={(e) =>
                            updateRule({ enabled: e.target.checked })
                          }
                        />
                        <FieldLabel>Enabled</FieldLabel>
                      </label>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <label className="block space-y-1.5">
                        <FieldLabel>Effective from</FieldLabel>
                        <TextInput
                          value={rule.effective_from}
                          disabled={!editable}
                          onChange={(e) =>
                            updateRule({ effective_from: e.target.value })
                          }
                        />
                      </label>
                      <label className="block space-y-1.5">
                        <FieldLabel>Effective to</FieldLabel>
                        <TextInput
                          value={rule.effective_to ?? ""}
                          disabled={!editable}
                          placeholder="null"
                          onChange={(e) =>
                            updateRule({
                              effective_to: e.target.value || null,
                            })
                          }
                        />
                      </label>
                    </div>

                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <FieldLabel>Condition</FieldLabel>
                        <div className="flex gap-1">
                          <button
                            type="button"
                            disabled={!editable}
                            onClick={() => setConditionMode("simple")}
                            className={
                              conditionMode === "simple"
                                ? "bg-ink px-2 py-1 text-xs text-foam"
                                : "border border-[var(--line)] px-2 py-1 text-xs"
                            }
                          >
                            Path / op / value
                          </button>
                          <button
                            type="button"
                            disabled={!editable}
                            onClick={() => {
                              setConditionMode("json");
                              setConditionJson(
                                JSON.stringify(rule.condition, null, 2),
                              );
                            }}
                            className={
                              conditionMode === "json"
                                ? "bg-ink px-2 py-1 text-xs text-foam"
                                : "border border-[var(--line)] px-2 py-1 text-xs"
                            }
                          >
                            JSON
                          </button>
                        </div>
                      </div>

                      {conditionMode === "simple" &&
                      isSimpleCondition(rule.condition) ? (
                        <div className="space-y-2">
                          <TextInput
                            value={String(rule.condition.path ?? "")}
                            disabled={!editable}
                            placeholder="membership.tier"
                            onChange={(e) =>
                              updateRule({
                                condition: {
                                  ...rule.condition,
                                  path: e.target.value,
                                },
                              })
                            }
                          />
                          <Select
                            value={String(rule.condition.op ?? "eq")}
                            disabled={!editable}
                            onChange={(e) =>
                              updateRule({
                                condition: {
                                  ...rule.condition,
                                  op: e.target.value,
                                },
                              })
                            }
                          >
                            {CONDITION_OPS.map((op) => (
                              <option key={op} value={op}>
                                {op}
                              </option>
                            ))}
                          </Select>
                          <TextInput
                            value={formatValue(rule.condition.value)}
                            disabled={!editable}
                            placeholder='gold or ["gold","platinum"]'
                            onChange={(e) =>
                              updateRule({
                                condition: {
                                  ...rule.condition,
                                  value: parseValue(
                                    e.target.value,
                                    String(rule.condition.op ?? "eq"),
                                  ),
                                },
                              })
                            }
                          />
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {!isSimpleCondition(rule.condition) &&
                            conditionMode === "simple" && (
                              <p className="text-xs text-ink/50">
                                Nested condition — editing as JSON.
                              </p>
                            )}
                          <TextArea
                            rows={8}
                            value={
                              conditionMode === "json"
                                ? conditionJson
                                : JSON.stringify(rule.condition, null, 2)
                            }
                            disabled={!editable}
                            onChange={(e) => {
                              setConditionMode("json");
                              setConditionJson(e.target.value);
                            }}
                            onBlur={() => {
                              if (editable && conditionMode === "json") {
                                syncConditionFromJson();
                              }
                            }}
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <FieldLabel>Effects</FieldLabel>
                      {editable && (
                        <PrimaryButton
                          tone="ghost"
                          className="px-2 py-1 text-xs"
                          onClick={() =>
                            updateRule({
                              effects: [
                                ...rule.effects,
                                {
                                  type: "allow",
                                  payload: {},
                                  persist_as_entitlement: false,
                                },
                              ],
                            })
                          }
                        >
                          + Effect
                        </PrimaryButton>
                      )}
                    </div>
                    {rule.effects.map((effect, ei) => (
                      <div
                        key={ei}
                        className="space-y-2 border border-[var(--line)] bg-white/40 p-3"
                      >
                        <div className="flex gap-2">
                          <Select
                            value={effect.type}
                            disabled={!editable}
                            onChange={(e) =>
                              updateEffect(ei, { type: e.target.value })
                            }
                          >
                            {EFFECT_TYPES.map((t) => (
                              <option key={t} value={t}>
                                {t}
                              </option>
                            ))}
                          </Select>
                          {editable && rule.effects.length > 1 && (
                            <PrimaryButton
                              tone="ghost"
                              className="shrink-0 px-2"
                              onClick={() =>
                                updateRule({
                                  effects: rule.effects.filter(
                                    (_, i) => i !== ei,
                                  ),
                                })
                              }
                            >
                              ×
                            </PrimaryButton>
                          )}
                        </div>
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={!!effect.persist_as_entitlement}
                            disabled={!editable}
                            onChange={(e) =>
                              updateEffect(ei, {
                                persist_as_entitlement: e.target.checked,
                              })
                            }
                          />
                          <span className="text-sm text-ink/70">
                            Persist as entitlement
                          </span>
                        </label>
                        {effect.persist_as_entitlement && (
                          <TextInput
                            value={effect.benefit_type ?? ""}
                            disabled={!editable}
                            placeholder="benefit_type"
                            onChange={(e) =>
                              updateEffect(ei, {
                                benefit_type: e.target.value || null,
                              })
                            }
                          />
                        )}
                        <TextArea
                          rows={3}
                          value={JSON.stringify(effect.payload ?? {}, null, 2)}
                          disabled={!editable}
                          onChange={(e) => {
                            try {
                              const payload = JSON.parse(e.target.value) as Record<
                                string,
                                unknown
                              >;
                              updateEffect(ei, { payload });
                            } catch {
                              /* keep typing */
                            }
                          }}
                        />
                      </div>
                    ))}

                    {editable && (
                      <PrimaryButton
                        tone="ghost"
                        className="text-coral"
                        onClick={() => {
                          if (pack.rules.length <= 1) return;
                          const rules = pack.rules.filter(
                            (_, i) => i !== ruleIndex,
                          );
                          setPack({ ...pack, rules });
                          setRuleIndex(Math.max(0, ruleIndex - 1));
                        }}
                      >
                        Remove rule
                      </PrimaryButton>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
