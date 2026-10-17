"""Synthetic scale benchmark: generate N-column × M-rule packs and fire them.

Compares:
- zen — GoRules Zen evaluating generated JDM (hitPolicy FIRST)
- dmn_table — in-process FIRST-hit table matcher (Kogito/DMN-style semantics)

Live Kogito HTTP is unsuitable for 10k-rule / 1M-fire synthetic packs; dmn_table
is the scalable peer for objective throughput + decision parity on identical rules.
"""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass
from typing import Any, Literal

EngineKind = Literal["zen", "dmn_table"]

PRESET_RULE_COUNTS = (100, 1_000, 10_000)
PRESET_FIRE_COUNTS = (1_000, 10_000, 1_000_000)
PRESET_COLUMN_COUNTS = (5, 10, 20)

# Soft safety caps for synchronous API runs (override via request).
DEFAULT_MAX_RULES = 10_000
DEFAULT_MAX_COLUMNS = 50
DEFAULT_MAX_FIRES = 1_000_000
DEFAULT_MAX_WORK = 200_000_000  # rules × fires ceiling for a single sync run


@dataclass(frozen=True)
class GeneratedRule:
    rule_id: str
    conditions: dict[str, str]  # field -> exact value (absent = wildcard)
    decision: str
    outcome: str


@dataclass(frozen=True)
class BenchmarkPack:
    columns: tuple[str, ...]
    value_domain: tuple[str, ...]
    rules: tuple[GeneratedRule, ...]
    jdm: dict[str, Any]
    seed: int

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    @property
    def column_count(self) -> int:
        return len(self.columns)


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def generate_pack(
    *,
    column_count: int = 10,
    rule_count: int = 100,
    values_per_column: int = 8,
    seed: int = 42,
) -> BenchmarkPack:
    """Build a deterministic FIRST-hit decision table + matching JDM envelope."""
    if column_count < 1 or column_count > DEFAULT_MAX_COLUMNS:
        raise ValueError(f"column_count must be 1..{DEFAULT_MAX_COLUMNS}")
    if rule_count < 1 or rule_count > DEFAULT_MAX_RULES:
        raise ValueError(f"rule_count must be 1..{DEFAULT_MAX_RULES}")
    if values_per_column < 2 or values_per_column > 32:
        raise ValueError("values_per_column must be 2..32")

    rng = _rng(seed)
    columns = tuple(f"v{i}" for i in range(column_count))
    value_domain = tuple(f"s{j}" for j in range(values_per_column))

    rules: list[GeneratedRule] = []
    for idx in range(rule_count):
        # Constrain 1..min(3, column_count) columns so most inputs miss early rules
        # and later catch-alls / specific rows still fire.
        arity = 1 + (idx % min(3, column_count))
        chosen_cols = rng.sample(list(columns), k=arity)
        conditions = {col: rng.choice(value_domain) for col in chosen_cols}
        decision = "allow" if (idx % 5) else "deny"
        outcome = f"out_{(idx * 7 + seed) % 97}"
        rules.append(
            GeneratedRule(
                rule_id=f"r{idx:05d}",
                conditions=conditions,
                decision=decision,
                outcome=outcome,
            )
        )

    # Terminal catch-all so every fire resolves.
    rules.append(
        GeneratedRule(
            rule_id="r_default",
            conditions={},
            decision="inconclusive",
            outcome="default",
        )
    )

    jdm = _build_jdm(columns, rules, seed=seed)
    return BenchmarkPack(
        columns=columns,
        value_domain=value_domain,
        rules=tuple(rules),
        jdm=jdm,
        seed=seed,
    )


def _build_jdm(
    columns: tuple[str, ...],
    rules: list[GeneratedRule],
    *,
    seed: int,
) -> dict[str, Any]:
    inputs = [
        {"id": f"i{i}", "name": col, "field": col} for i, col in enumerate(columns)
    ]
    outputs = [
        {"id": "o1", "name": "Decision", "field": "decision"},
        {"id": "o2", "name": "Outcome", "field": "outcome"},
        {"id": "o3", "name": "Rule id", "field": "rule_id"},
    ]
    table_rules: list[dict[str, Any]] = []
    for rule in rules:
        row: dict[str, Any] = {"_id": rule.rule_id}
        for i, col in enumerate(columns):
            val = rule.conditions.get(col)
            row[f"i{i}"] = f"'{val}'" if val is not None else ""
        row["o1"] = f'"{rule.decision}"'
        row["o2"] = f'"{rule.outcome}"'
        row["o3"] = f'"{rule.rule_id}"'
        table_rules.append(row)

    return {
        "domain": "benchmark",
        "pack_id": f"bench-{len(columns)}c-{len(rules)}r",
        "version": f"bench-{seed}",
        "lifecycle": "published",
        "nodes": [
            {
                "id": "input",
                "type": "inputNode",
                "name": "Request",
                "position": {"x": 40, "y": 200},
                "content": {"schema": ""},
            },
            {
                "id": "table",
                "type": "decisionTableNode",
                "name": "Scale table",
                "position": {"x": 320, "y": 200},
                "content": {
                    "hitPolicy": "first",
                    "inputs": inputs,
                    "outputs": outputs,
                    "rules": table_rules,
                    "passThrough": False,
                    "inputField": None,
                    "outputPath": None,
                    "executionMode": "single",
                },
            },
            {
                "id": "output",
                "type": "outputNode",
                "name": "Response",
                "position": {"x": 640, "y": 200},
                "content": {"schema": ""},
            },
        ],
        "edges": [
            {
                "id": "e1",
                "sourceId": "input",
                "type": "edge",
                "targetId": "table",
            },
            {
                "id": "e2",
                "sourceId": "table",
                "type": "edge",
                "targetId": "output",
            },
        ],
    }


def generate_facts(
    pack: BenchmarkPack,
    *,
    fire_count: int,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    rng = _rng(pack.seed if seed is None else seed)
    facts: list[dict[str, Any]] = []
    for _ in range(fire_count):
        row = {col: rng.choice(pack.value_domain) for col in pack.columns}
        facts.append(row)
    return facts


def match_dmn_table(pack: BenchmarkPack, facts: dict[str, Any]) -> dict[str, Any]:
    """FIRST-hit decision table (Kogito/DMN-style) over generated rules."""
    for rule in pack.rules:
        ok = True
        for col, expected in rule.conditions.items():
            if facts.get(col) != expected:
                ok = False
                break
        if ok:
            return {
                "decision": rule.decision,
                "outcome": rule.outcome,
                "rule_id": rule.rule_id,
            }
    return {"decision": "inconclusive", "outcome": "none", "rule_id": None}


def _zen_evaluate_once(decision_obj: Any, facts: dict[str, Any]) -> dict[str, Any]:
    response = decision_obj.evaluate(facts, {"trace": False})
    body = response if isinstance(response, dict) else dict(response)
    result = body.get("result") or {}
    # FIRST hitPolicy returns fields on the result object directly.
    if isinstance(result, dict) and result.get("decision") is not None:
        return {
            "decision": str(result.get("decision")),
            "outcome": str(result.get("outcome")) if result.get("outcome") is not None else None,
            "rule_id": str(result.get("rule_id")) if result.get("rule_id") is not None else None,
        }
    matches = result.get("matches") if isinstance(result, dict) else None
    if isinstance(matches, list) and matches:
        row = matches[0]
        return {
            "decision": str(row.get("decision")),
            "outcome": str(row.get("outcome")) if row.get("outcome") is not None else None,
            "rule_id": str(row.get("rule_id")) if row.get("rule_id") is not None else None,
        }
    return {"decision": "inconclusive", "outcome": None, "rule_id": None}


def run_engine(
    engine: EngineKind,
    pack: BenchmarkPack,
    facts_list: list[dict[str, Any]],
) -> dict[str, Any]:
    decisions: list[str] = []
    t0 = time.perf_counter()

    if engine == "dmn_table":
        for facts in facts_list:
            out = match_dmn_table(pack, facts)
            decisions.append(out["decision"])
    elif engine == "zen":
        import zen
        from rules_engine.models import RulePack

        rule_pack = RulePack.from_dict(pack.jdm)
        engine_obj = zen.ZenEngine()
        decision_obj = engine_obj.create_decision(rule_pack.jdm())
        for facts in facts_list:
            out = _zen_evaluate_once(decision_obj, facts)
            decisions.append(out["decision"])
    else:
        raise ValueError(f"Unknown engine {engine}")

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    n = len(facts_list) or 1
    # Histogram
    hist: dict[str, int] = {}
    for d in decisions:
        hist[d] = hist.get(d, 0) + 1

    return {
        "engine": engine,
        "fires": len(facts_list),
        "elapsed_ms": round(elapsed_ms, 3),
        "throughput_fps": round(len(facts_list) / (elapsed_ms / 1000.0), 2) if elapsed_ms else None,
        "avg_ms_per_fire": round(elapsed_ms / n, 6),
        "decision_histogram": hist,
        "sample_decisions": decisions[:20],
    }


def compare_parity(
    pack: BenchmarkPack,
    facts_list: list[dict[str, Any]],
    *,
    sample_limit: int = 500,
) -> dict[str, Any]:
    """Decision parity between Zen and dmn_table on a sample of facts."""
    import zen
    from rules_engine.models import RulePack

    sample = facts_list[: min(sample_limit, len(facts_list))]
    rule_pack = RulePack.from_dict(pack.jdm)
    decision_obj = zen.ZenEngine().create_decision(rule_pack.jdm())

    agree = 0
    mismatches: list[dict[str, Any]] = []
    for facts in sample:
        z = _zen_evaluate_once(decision_obj, facts)
        k = match_dmn_table(pack, facts)
        if z["decision"] == k["decision"] and z["outcome"] == k["outcome"]:
            agree += 1
        elif len(mismatches) < 25:
            mismatches.append({"facts": facts, "zen": z, "dmn_table": k})

    return {
        "sample_size": len(sample),
        "agree": agree,
        "agree_pct": round(100.0 * agree / len(sample), 2) if sample else 0.0,
        "mismatches": mismatches,
    }


def estimate_work(rule_count: int, fire_count: int) -> int:
    return int(rule_count) * int(fire_count)


def validate_params(
    *,
    column_count: int,
    rule_count: int,
    fire_count: int,
    max_work: int = DEFAULT_MAX_WORK,
) -> None:
    if fire_count < 1 or fire_count > DEFAULT_MAX_FIRES:
        raise ValueError(f"fire_count must be 1..{DEFAULT_MAX_FIRES}")
    work = estimate_work(rule_count, fire_count)
    if work > max_work:
        raise ValueError(
            f"Work {work:,} (rules×fires) exceeds sync cap {max_work:,}. "
            "Lower rule_count or fire_count, or raise max_work explicitly."
        )


def run_benchmark(
    *,
    column_count: int = 10,
    rule_count: int = 100,
    fire_count: int = 1_000,
    seed: int = 42,
    engines: list[EngineKind] | None = None,
    values_per_column: int = 8,
    max_work: int = DEFAULT_MAX_WORK,
    parity_sample: int = 500,
) -> dict[str, Any]:
    validate_params(
        column_count=column_count,
        rule_count=rule_count,
        fire_count=fire_count,
        max_work=max_work,
    )
    engines = engines or ["zen", "dmn_table"]
    pack = generate_pack(
        column_count=column_count,
        rule_count=rule_count,
        values_per_column=values_per_column,
        seed=seed,
    )
    # Facts seed offset so fires stay reproducible but independent of rule RNG walk.
    facts_list = generate_facts(pack, fire_count=fire_count, seed=seed + 17)

    engine_results = []
    for eng in engines:
        engine_results.append(run_engine(eng, pack, facts_list))

    parity = None
    if "zen" in engines and "dmn_table" in engines:
        parity = compare_parity(pack, facts_list, sample_limit=parity_sample)

    fingerprint = hashlib.sha256(
        f"{seed}:{column_count}:{rule_count}:{fire_count}:{values_per_column}".encode()
    ).hexdigest()[:16]

    return {
        "fingerprint": fingerprint,
        "params": {
            "column_count": column_count,
            "rule_count": rule_count,
            "fire_count": fire_count,
            "seed": seed,
            "values_per_column": values_per_column,
            "engines": engines,
            "generated_rule_rows": pack.rule_count,  # includes default catch-all
            "variables": list(pack.columns),
            "value_domain": list(pack.value_domain),
            "sample_outcomes": sorted({r.outcome for r in pack.rules})[:20],
        },
        "engines": engine_results,
        "parity": parity,
        "notes": [
            "zen evaluates generated JDM via GoRules Zen (hitPolicy first).",
            "dmn_table is an in-process FIRST-hit matcher with identical rules (Kogito/DMN-style).",
            "Live Kogito HTTP LoungeAccess.dmn is not used for synthetic N×M packs.",
        ],
    }


def run_matrix(
    *,
    rule_counts: list[int] | None = None,
    fire_counts: list[int] | None = None,
    column_count: int = 10,
    seed: int = 42,
    engines: list[EngineKind] | None = None,
    max_work: int = DEFAULT_MAX_WORK,
    skip_over_cap: bool = True,
) -> dict[str, Any]:
    rule_counts = rule_counts or list(PRESET_RULE_COUNTS)
    fire_counts = fire_counts or list(PRESET_FIRE_COUNTS)
    engines = engines or ["zen", "dmn_table"]

    cells: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for rules in rule_counts:
        for fires in fire_counts:
            work = estimate_work(rules, fires)
            if skip_over_cap and work > max_work:
                skipped.append(
                    {
                        "rule_count": rules,
                        "fire_count": fires,
                        "work": work,
                        "reason": f"exceeds max_work {max_work}",
                    }
                )
                continue
            try:
                result = run_benchmark(
                    column_count=column_count,
                    rule_count=rules,
                    fire_count=fires,
                    seed=seed,
                    engines=engines,
                    max_work=max_work,
                )
                cells.append(result)
            except Exception as exc:  # noqa: BLE001
                skipped.append(
                    {
                        "rule_count": rules,
                        "fire_count": fires,
                        "work": work,
                        "reason": f"{type(exc).__name__}: {exc}",
                    }
                )

    return {
        "column_count": column_count,
        "seed": seed,
        "engines": engines,
        "max_work": max_work,
        "cell_count": len(cells),
        "skipped": skipped,
        "cells": cells,
    }
