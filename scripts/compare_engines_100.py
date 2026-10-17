#!/usr/bin/env python3
"""Objective Zen vs Kogito comparison across 100 complex lounge scenarios.

Generates a deterministic fixture pack, evaluates each case on both engines,
and writes a structured JSON report for analysis / canvas rendering.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
import traceback
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "packages" / "rules_engine" / "src"),
    str(ROOT / "apps" / "api" / "src"),
]

from rules_api.engines import evaluate_with_engine  # noqa: E402
from rules_engine.models import RulePack  # noqa: E402
from rules_engine.samples import load_lounge_pack  # noqa: E402

TIERS = ["bronze", "silver", "gold", "platinum", "platinum_one", "diamond", "unknown"]
CABINS = ["economy", "premium_economy", "business", "first", None]
PARTNER = [None, "silver", "gold", "platinum", "first", "unknown"]
COMPANION = [False, True]
AS_OF = [
    "2026-06-15T12:00:00Z",  # normal
    "2099-06-15T12:00:00Z",  # peak seasonal window
    "2098-12-31T23:59:59Z",  # edge before peak
    "2100-01-01T00:00:00Z",  # edge after peak
]
INTL = [False, True]


def _case(
    idx: int,
    *,
    tier: str | None,
    cabin: str | None,
    partner: str | None,
    companion: bool,
    as_of: str,
    international: bool,
    label: str,
    extra_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    membership: dict[str, Any] = {"companion_eligible": companion}
    if tier is not None:
        membership["tier"] = tier
    facts: dict[str, Any] = {"membership": membership}
    booking: dict[str, Any] = {"international": international}
    if cabin is not None:
        booking["cabin"] = cabin
    facts["booking"] = booking
    if partner is not None:
        facts["partner"] = {"airline": "Qantas", "elite_tier": partner}
    if extra_facts:
        facts.update(extra_facts)
    return {
        "case_id": f"C{idx:03d}",
        "subject_id": f"CMP-{idx:03d}",
        "label": label,
        "as_of": as_of,
        "facts": facts,
        "dimensions": {
            "tier": tier,
            "cabin": cabin,
            "partner_elite": partner,
            "companion_eligible": companion,
            "as_of_bucket": (
                "peak_2099"
                if as_of.startswith("2099")
                else "pre_peak"
                if as_of.startswith("2098")
                else "post_peak"
                if as_of.startswith("2100")
                else "normal"
            ),
            "international": international,
        },
    }


def build_100_cases() -> list[dict[str, Any]]:
    """Build 100 complex, deterministic scenarios covering overlap + divergence axes."""
    cases: list[dict[str, Any]] = []
    idx = 0

    # Block A (35): full tier × cabin matrix @ normal date (Zen matrix strength)
    for tier, cabin in product(
        ["bronze", "silver", "gold", "platinum", "platinum_one"],
        ["economy", "premium_economy", "business", "first"],
    ):
        cases.append(
            _case(
                idx,
                tier=tier,
                cabin=cabin,
                partner=None,
                companion=False,
                as_of=AS_OF[0],
                international=False,
                label=f"matrix:{tier}+{cabin}",
            )
        )
        idx += 1
    # 5×4 = 20; add diamond × cabin (4) + unknown × cabin partial → need 35
    for cabin in CABINS[:4]:
        cases.append(
            _case(
                idx,
                tier="diamond",
                cabin=cabin,
                partner=None,
                companion=False,
                as_of=AS_OF[0],
                international=False,
                label=f"matrix:diamond+{cabin}",
            )
        )
        idx += 1
    for cabin in ["economy", "business", "first"]:
        cases.append(
            _case(
                idx,
                tier="unknown",
                cabin=cabin,
                partner=None,
                companion=False,
                as_of=AS_OF[0],
                international=False,
                label=f"matrix:unknown+{cabin}",
            )
        )
        idx += 1
    # missing tier with cabins
    for cabin in ["economy", "first"]:
        cases.append(
            _case(
                idx,
                tier=None,
                cabin=cabin,
                partner=None,
                companion=False,
                as_of=AS_OF[0],
                international=False,
                label=f"matrix:null_tier+{cabin}",
            )
        )
        idx += 1
    # default cabin (None → economy in Zen normalize)
    for tier in ["bronze", "gold", "platinum", "diamond", "silver", "platinum_one"]:
        cases.append(
            _case(
                idx,
                tier=tier,
                cabin=None,
                partner=None,
                companion=False,
                as_of=AS_OF[0],
                international=False,
                label=f"default_cabin:{tier}",
            )
        )
        idx += 1
    assert len(cases) == 35, len(cases)

    # Block B (20): partner elite overlays across low/high tiers
    partner_combos = [
        ("bronze", "economy", "gold"),
        ("bronze", "economy", "platinum"),
        ("bronze", "economy", "first"),
        ("bronze", "first", "gold"),
        ("silver", "economy", "gold"),
        ("silver", "premium_economy", "platinum"),
        ("silver", "business", "first"),
        ("gold", "economy", "gold"),
        ("platinum", "economy", "first"),
        ("unknown", "economy", "gold"),
        ("bronze", "economy", "silver"),  # partner too low
        ("bronze", "economy", "unknown"),
        (None, "economy", "gold"),
        ("bronze", None, "platinum"),
        ("silver", "economy", "gold"),
        ("diamond", "economy", "gold"),
        ("platinum_one", "economy", "gold"),
        ("bronze", "business", "gold"),
        ("silver", "first", "platinum"),
        ("unknown", "first", "first"),
    ]
    for tier, cabin, partner in partner_combos:
        cases.append(
            _case(
                idx,
                tier=tier,
                cabin=cabin,
                partner=partner,
                companion=False,
                as_of=AS_OF[0],
                international=False,
                label=f"partner:{tier}+{cabin}+elite:{partner}",
            )
        )
        idx += 1
    assert len(cases) == 55, len(cases)

    # Block C (15): seasonal peak / edge dates
    seasonal = [
        ("silver", "economy", None, AS_OF[1], "peak_silver_economy"),
        ("bronze", "economy", None, AS_OF[1], "peak_bronze_economy"),
        ("silver", "business", None, AS_OF[1], "peak_silver_business"),
        ("gold", "economy", None, AS_OF[1], "peak_gold_economy"),
        ("silver", "economy", "gold", AS_OF[1], "peak_silver_partner"),
        ("bronze", "economy", "platinum", AS_OF[1], "peak_bronze_partner"),
        ("silver", "economy", None, AS_OF[2], "prepeak_silver"),
        ("silver", "economy", None, AS_OF[3], "postpeak_silver"),
        ("bronze", "economy", None, AS_OF[2], "prepeak_bronze"),
        ("platinum", "economy", None, AS_OF[1], "peak_platinum"),
        ("diamond", "economy", None, AS_OF[1], "peak_diamond"),
        ("silver", "premium_economy", None, AS_OF[1], "peak_silver_prem"),
        ("silver", None, None, AS_OF[1], "peak_silver_default_cabin"),
        ("bronze", "first", None, AS_OF[1], "peak_bronze_first"),
        ("unknown", "economy", None, AS_OF[1], "peak_unknown"),
    ]
    for tier, cabin, partner, as_of, label in seasonal:
        cases.append(
            _case(
                idx,
                tier=tier,
                cabin=cabin,
                partner=partner,
                companion=False,
                as_of=as_of,
                international=False,
                label=label,
            )
        )
        idx += 1
    assert len(cases) == 70, len(cases)

    # Block D (15): companion eligibility interactions
    companion_combos = [
        ("bronze", "economy", False, "comp_off_bronze"),
        ("bronze", "economy", True, "comp_on_bronze"),
        ("silver", "business", True, "comp_on_silver"),
        ("gold", "economy", True, "comp_on_gold"),
        ("platinum", "economy", False, "comp_off_platinum"),
        ("platinum", "economy", True, "comp_on_platinum"),
        ("platinum_one", "economy", False, "comp_off_p1"),
        ("platinum_one", "first", True, "comp_on_p1"),
        ("diamond", "economy", False, "comp_off_diamond"),
        ("diamond", "business", True, "comp_on_diamond"),
        ("unknown", "economy", True, "comp_on_unknown"),
        ("bronze", "first", True, "comp_on_bronze_first"),
        ("silver", "economy", True, "comp_on_silver_econ"),
        ("gold", "first", True, "comp_on_gold_first"),
        ("platinum_one", "business", False, "comp_off_p1_biz"),
    ]
    for tier, cabin, companion, label in companion_combos:
        cases.append(
            _case(
                idx,
                tier=tier,
                cabin=cabin,
                partner=None,
                companion=companion,
                as_of=AS_OF[0],
                international=False,
                label=label,
            )
        )
        idx += 1
    assert len(cases) == 85, len(cases)

    # Block E (15): international + multi-signal conflicts + sparse facts
    complex_tail = [
        ("gold", "economy", "platinum", True, True, AS_OF[0], "intl_gold_partner"),
        ("bronze", "economy", "gold", True, True, AS_OF[0], "intl_bronze_partner_comp"),
        ("silver", "economy", "gold", False, True, AS_OF[1], "peak_intl_silver_partner"),
        ("platinum_one", "economy", None, False, True, AS_OF[0], "intl_p1"),
        ("diamond", "first", "first", True, True, AS_OF[0], "intl_diamond_all_signals"),
        ("bronze", "business", None, False, True, AS_OF[0], "intl_bronze_business"),
        ("unknown", None, "gold", True, False, AS_OF[0], "sparse_partner_comp"),
        (None, None, None, False, False, AS_OF[0], "empty_almost"),
        ("gold", "premium_economy", "silver", False, True, AS_OF[0], "intl_gold_low_partner"),
        ("silver", "first", None, True, True, AS_OF[1], "peak_intl_silver_first_comp"),
        ("platinum", "premium_economy", "platinum", True, False, AS_OF[3], "postpeak_plat_partner"),
        ("bronze", "premium_economy", "first", False, True, AS_OF[2], "prepeak_bronze_partner"),
        ("diamond", None, None, True, True, AS_OF[1], "peak_diamond_default_cabin_comp"),
        ("platinum_one", "economy", "first", True, True, AS_OF[0], "p1_full_stack"),
        ("silver", "economy", None, False, False, AS_OF[1], "peak_silver_baseline_repeat"),
    ]
    for tier, cabin, partner, companion, international, as_of, label in complex_tail:
        cases.append(
            _case(
                idx,
                tier=tier,
                cabin=cabin,
                partner=partner,
                companion=companion,
                as_of=as_of,
                international=international,
                label=label,
            )
        )
        idx += 1

    assert len(cases) == 100, f"expected 100 cases, got {len(cases)}"
    # renumber case_ids to be contiguous 000-099
    for i, c in enumerate(cases):
        c["case_id"] = f"C{i:03d}"
        c["subject_id"] = f"CMP-{i:03d}"
    return cases


def _effect_types(effects: list[dict[str, Any]]) -> list[str]:
    return sorted({str(e.get("type")) for e in effects})


def _benefit_types(effects: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(e.get("benefit_type"))
            for e in effects
            if e.get("benefit_type") is not None
        }
    )


def _lounge_classes(effects: list[dict[str, Any]]) -> list[str]:
    values: set[str] = set()
    for e in effects:
        payload = e.get("payload") or {}
        for key in ("lounge_class", "lounge_type"):
            if payload.get(key) is not None:
                values.add(str(payload[key]))
    return sorted(values)


def _companions(effects: list[dict[str, Any]]) -> int:
    total = 0
    for e in effects:
        payload = e.get("payload") or {}
        if payload.get("companions_allowed") is not None:
            total = max(total, int(payload["companions_allowed"]))
        if e.get("benefit_type") == "companion_pass":
            total = max(total, 1)
    return total


def _matched_rules(result: Any) -> list[str]:
    rules: list[str] = []
    for entry in result.trace.entries:
        if entry.status == "matched" and entry.rule_id:
            rules.append(entry.rule_id)
    return sorted(set(rules))


def _summarize_engine(result: Any, ms: float, error: str | None) -> dict[str, Any]:
    if error:
        return {
            "ok": False,
            "error": error,
            "latency_ms": round(ms, 3),
            "decision": None,
            "effect_types": [],
            "benefit_types": [],
            "lounge_classes": [],
            "companions": 0,
            "matched_rules": [],
            "path": None,
            "effects": [],
        }
    effects = [e.to_dict() for e in result.effects]
    return {
        "ok": True,
        "error": None,
        "latency_ms": round(ms, 3),
        "decision": result.decision,
        "effect_types": _effect_types(effects),
        "benefit_types": _benefit_types(effects),
        "lounge_classes": _lounge_classes(effects),
        "companions": _companions(effects),
        "matched_rules": _matched_rules(result),
        "path": result.trace.path,
        "effects": effects,
    }


def run_one(pack: RulePack, case: dict[str, Any], engine: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        result = evaluate_with_engine(
            engine,  # type: ignore[arg-type]
            pack,
            case["facts"],
            as_of=case["as_of"],
            entitlements=[],
        )
        ms = (time.perf_counter() - t0) * 1000
        return _summarize_engine(result, ms, None)
    except Exception as exc:  # noqa: BLE001 — collect parity failures
        ms = (time.perf_counter() - t0) * 1000
        return _summarize_engine(None, ms, f"{type(exc).__name__}: {exc}")


def classify_diff(zen: dict[str, Any], kogito: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    if not zen["ok"] or not kogito["ok"]:
        flags.append("engine_error")
        return {
            "agree_decision": False,
            "agree_lounge": False,
            "agree_companions": False,
            "agree_benefits": False,
            "full_parity": False,
            "flags": flags,
        }

    agree_decision = zen["decision"] == kogito["decision"]
    # Lounge taxonomy differs by design (Zen matrix vs Kogito "domestic");
    # treat both-empty / both-nonempty + decision agree as soft lounge parity,
    # and exact string match as hard lounge parity.
    z_lounge = zen["lounge_classes"]
    k_lounge = kogito["lounge_classes"]
    hard_lounge = z_lounge == k_lounge
    soft_lounge = (not z_lounge and not k_lounge) or (bool(z_lounge) == bool(k_lounge))
    agree_companions = zen["companions"] == kogito["companions"]
    agree_benefits = set(zen["benefit_types"]) == set(kogito["benefit_types"])

    if not agree_decision:
        flags.append("decision_mismatch")
    if not hard_lounge:
        flags.append("lounge_taxonomy_diff" if soft_lounge else "lounge_presence_diff")
    if not agree_companions:
        flags.append("companion_mismatch")
    if not agree_benefits:
        flags.append("benefit_mismatch")

    # Semantic allow/deny agreement is the primary objective metric.
    full_parity = agree_decision and hard_lounge and agree_companions and agree_benefits
    return {
        "agree_decision": agree_decision,
        "agree_lounge_exact": hard_lounge,
        "agree_lounge_presence": soft_lounge,
        "agree_companions": agree_companions,
        "agree_benefits": agree_benefits,
        "full_parity": full_parity,
        "flags": flags,
    }


def latency_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    p95_idx = min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))
    return {
        "n": len(values),
        "min_ms": round(ordered[0], 3),
        "median_ms": round(statistics.median(ordered), 3),
        "mean_ms": round(statistics.mean(ordered), 3),
        "p95_ms": round(ordered[p95_idx], 3),
        "max_ms": round(ordered[-1], 3),
    }


def main() -> int:
    pack = load_lounge_pack()
    cases = build_100_cases()
    rows: list[dict[str, Any]] = []

    # Warmup both engines once so first-case latency isn't skewed.
    warmup = cases[0]
    run_one(pack, warmup, "zen")
    try:
        run_one(pack, warmup, "kogito")
    except Exception:  # noqa: BLE001
        pass

    for case in cases:
        zen = run_one(pack, case, "zen")
        kogito = run_one(pack, case, "kogito")
        diff = classify_diff(zen, kogito)
        rows.append(
            {
                **{k: case[k] for k in ("case_id", "subject_id", "label", "as_of", "facts", "dimensions")},
                "zen": zen,
                "kogito": kogito,
                "diff": diff,
            }
        )

    decision_agree = sum(1 for r in rows if r["diff"]["agree_decision"])
    lounge_exact = sum(1 for r in rows if r["diff"].get("agree_lounge_exact"))
    lounge_presence = sum(1 for r in rows if r["diff"].get("agree_lounge_presence"))
    companion_agree = sum(1 for r in rows if r["diff"]["agree_companions"])
    benefit_agree = sum(1 for r in rows if r["diff"]["agree_benefits"])
    full_parity = sum(1 for r in rows if r["diff"]["full_parity"])
    errors = [r for r in rows if "engine_error" in r["diff"]["flags"]]

    # Contingency: zen decision × kogito decision
    contingency: dict[str, dict[str, int]] = {}
    for r in rows:
        z = r["zen"]["decision"] or "ERROR"
        k = r["kogito"]["decision"] or "ERROR"
        contingency.setdefault(z, {})
        contingency[z][k] = contingency[z].get(k, 0) + 1

    # Flag histogram
    flag_counts: dict[str, int] = {}
    for r in rows:
        for f in r["diff"]["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    # Dimension slices for decision agreement
    by_tier: dict[str, dict[str, int]] = {}
    by_asof: dict[str, dict[str, int]] = {}
    by_partner: dict[str, dict[str, int]] = {}
    for r in rows:
        dims = r["dimensions"]
        for key, bucket in (
            ("tier", by_tier),
            ("as_of_bucket", by_asof),
            ("partner_elite", by_partner),
        ):
            label = str(dims.get(key))
            slot = bucket.setdefault(label, {"n": 0, "agree": 0})
            slot["n"] += 1
            if r["diff"]["agree_decision"]:
                slot["agree"] += 1

    mismatches = [r for r in rows if not r["diff"]["agree_decision"]]
    lounge_only_diffs = [
        r
        for r in rows
        if r["diff"]["agree_decision"]
        and not r["diff"].get("agree_lounge_exact")
    ]
    companion_only = [
        r
        for r in rows
        if r["diff"]["agree_decision"]
        and not r["diff"]["agree_companions"]
        and r["diff"].get("agree_lounge_presence")
    ]

    report = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pack": {
                "domain": pack.domain,
                "pack_id": pack.pack_id,
                "version": pack.version,
            },
            "engines": ["zen", "kogito"],
            "case_count": len(rows),
            "notes": [
                "Zen evaluates the authored JDM lounge matrix (tier×cabin, partner overlay, seasonal deny, companion for platinum_one).",
                "Kogito evaluates the seeded LoungeAccess.dmn (tier/partner/seasonal/companion; lounge_class always 'domestic' on allow).",
                "Primary objective metric: decision parity (allow/deny/inconclusive).",
                "Lounge class strings are not expected to match exactly across engines.",
            ],
        },
        "summary": {
            "decision_agree": decision_agree,
            "decision_agree_pct": round(100 * decision_agree / len(rows), 1),
            "lounge_exact_agree": lounge_exact,
            "lounge_exact_agree_pct": round(100 * lounge_exact / len(rows), 1),
            "lounge_presence_agree": lounge_presence,
            "lounge_presence_agree_pct": round(100 * lounge_presence / len(rows), 1),
            "companion_agree": companion_agree,
            "companion_agree_pct": round(100 * companion_agree / len(rows), 1),
            "benefit_agree": benefit_agree,
            "benefit_agree_pct": round(100 * benefit_agree / len(rows), 1),
            "full_parity": full_parity,
            "full_parity_pct": round(100 * full_parity / len(rows), 1),
            "engine_errors": len(errors),
            "decision_mismatch_count": len(mismatches),
            "lounge_taxonomy_diff_when_decision_agrees": len(lounge_only_diffs),
            "companion_mismatch_when_decision_agrees": len(companion_only),
        },
        "contingency_zen_rows_kogito_cols": contingency,
        "flag_counts": flag_counts,
        "latency": {
            "zen": latency_stats([r["zen"]["latency_ms"] for r in rows if r["zen"]["ok"]]),
            "kogito": latency_stats(
                [r["kogito"]["latency_ms"] for r in rows if r["kogito"]["ok"]]
            ),
        },
        "slices": {
            "by_tier": by_tier,
            "by_as_of_bucket": by_asof,
            "by_partner_elite": by_partner,
        },
        "decision_mismatches": [
            {
                "case_id": r["case_id"],
                "label": r["label"],
                "dimensions": r["dimensions"],
                "zen_decision": r["zen"]["decision"],
                "kogito_decision": r["kogito"]["decision"],
                "zen_lounge": r["zen"]["lounge_classes"],
                "kogito_lounge": r["kogito"]["lounge_classes"],
                "zen_rules": r["zen"]["matched_rules"],
                "kogito_rules": r["kogito"]["matched_rules"],
                "flags": r["diff"]["flags"],
            }
            for r in mismatches
        ],
        "cases": rows,
    }

    out_dir = ROOT / "artifacts" / "engine-comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "zen_vs_kogito_100.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Compact CSV-ish summary for quick scanning
    summary_path = out_dir / "summary.md"
    lines = [
        "# Zen vs Kogito — 100 complex case comparison",
        "",
        f"- Cases: **{len(rows)}**",
        f"- Decision agreement: **{decision_agree}/{len(rows)} ({report['summary']['decision_agree_pct']}%)**",
        f"- Exact lounge-class agreement: **{lounge_exact}/{len(rows)} ({report['summary']['lounge_exact_agree_pct']}%)**",
        f"- Companion agreement: **{companion_agree}/{len(rows)} ({report['summary']['companion_agree_pct']}%)**",
        f"- Full parity (decision+lounge+companions+benefits): **{full_parity}/{len(rows)} ({report['summary']['full_parity_pct']}%)**",
        f"- Engine errors: **{len(errors)}**",
        "",
        "## Contingency (Zen ↓ / Kogito →)",
        "",
        "```",
        json.dumps(contingency, indent=2),
        "```",
        "",
        f"## Decision mismatches ({len(mismatches)})",
        "",
    ]
    for m in report["decision_mismatches"][:40]:
        lines.append(
            f"- `{m['case_id']}` {m['label']}: zen={m['zen_decision']} kogito={m['kogito_decision']} "
            f"rules zen={m['zen_rules']} kogito={m['kogito_rules']}"
        )
    if len(mismatches) > 40:
        lines.append(f"- … and {len(mismatches) - 40} more")
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"wrote": str(out_path), "summary": report["summary"]}, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
