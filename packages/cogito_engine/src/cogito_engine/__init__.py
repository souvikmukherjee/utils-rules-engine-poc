"""Cogito — native condition-IR rules engine (parallel to GoRules Zen)."""

from cogito_engine.evaluate import evaluate
from cogito_engine.explain import explain, explain_trace
from cogito_engine.jdm_bridge import jdm_to_cogito_pack
from cogito_engine.models import (
    DecisionResult,
    DecisionTrace,
    Effect,
    EntitlementSnapshot,
    Rule,
    RulePack,
    RuleTraceEntry,
)
from cogito_engine.testgen import (
    DEFAULT_MAX_CASES,
    HARD_MAX_CASES,
    generate_test_cases,
)

__all__ = [
    "DEFAULT_MAX_CASES",
    "HARD_MAX_CASES",
    "DecisionResult",
    "DecisionTrace",
    "Effect",
    "EntitlementSnapshot",
    "Rule",
    "RulePack",
    "RuleTraceEntry",
    "evaluate",
    "explain",
    "explain_trace",
    "generate_test_cases",
    "jdm_to_cogito_pack",
]
