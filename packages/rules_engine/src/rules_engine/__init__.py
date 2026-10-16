"""Domain-agnostic rules engine: evaluate facts with temporal windows and traces."""

from rules_engine.evaluate import evaluate
from rules_engine.explain import explain, explain_trace
from rules_engine.models import (
    DecisionResult,
    DecisionTrace,
    Effect,
    EntitlementSnapshot,
    Rule,
    RulePack,
    RuleTraceEntry,
)
from rules_engine.testgen import (
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
]
