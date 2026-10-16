from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class Effect:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    persist_as_entitlement: bool = False
    on_pack_change: str = "honor_existing"
    benefit_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Effect:
        return cls(
            type=data["type"],
            payload=dict(data.get("payload") or {}),
            persist_as_entitlement=bool(data.get("persist_as_entitlement", False)),
            on_pack_change=data.get("on_pack_change", "honor_existing"),
            benefit_type=data.get("benefit_type"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "payload": self.payload,
            "persist_as_entitlement": self.persist_as_entitlement,
            "on_pack_change": self.on_pack_change,
            "benefit_type": self.benefit_type,
        }


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    priority: int
    effective_from: datetime
    condition: dict[str, Any]
    effects: tuple[Effect, ...]
    effective_to: datetime | None = None
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        effective_from = parse_dt(data["effective_from"])
        if effective_from is None:
            raise ValueError(f"Rule {data.get('id')} missing effective_from")
        return cls(
            id=data["id"],
            name=data["name"],
            priority=int(data.get("priority", 0)),
            enabled=bool(data.get("enabled", True)),
            effective_from=effective_from,
            effective_to=parse_dt(data.get("effective_to")),
            condition=data["condition"],
            effects=tuple(Effect.from_dict(e) for e in data["effects"]),
        )

    def in_window(self, as_of: datetime) -> bool:
        if as_of < self.effective_from:
            return False
        if self.effective_to is not None and as_of >= self.effective_to:
            return False
        return True


@dataclass(frozen=True)
class RulePack:
    domain: str
    pack_id: str
    version: str
    lifecycle: str
    rules: tuple[Rule, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RulePack:
        rules = sorted(
            (Rule.from_dict(r) for r in data["rules"]),
            key=lambda r: (-r.priority, r.id),
        )
        return cls(
            domain=data["domain"],
            pack_id=data["pack_id"],
            version=data["version"],
            lifecycle=data.get("lifecycle", "draft"),
            rules=tuple(rules),
        )


@dataclass(frozen=True)
class EntitlementSnapshot:
    """Active entitlement presented to the engine (ledger lives in the API)."""

    entitlement_id: str
    benefit_type: str
    benefit_payload: dict[str, Any]
    grandfathered: bool = False
    source_rule_id: str | None = None
    source_pack_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entitlement_id": self.entitlement_id,
            "benefit_type": self.benefit_type,
            "benefit_payload": self.benefit_payload,
            "grandfathered": self.grandfathered,
            "source_rule_id": self.source_rule_id,
            "source_pack_version": self.source_pack_version,
        }


@dataclass
class RuleTraceEntry:
    rule_id: str
    rule_name: str
    status: str  # matched | skipped | condition_false
    reason: str | None = None
    effects: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "status": self.status,
            "reason": self.reason,
            "effects": self.effects,
        }


@dataclass
class DecisionTrace:
    as_of: datetime
    pack_version: str
    entries: list[RuleTraceEntry] = field(default_factory=list)
    entitlements_honored: list[dict[str, Any]] = field(default_factory=list)
    path: str = "rules"  # rules | entitlement | mixed

    def to_dict(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "pack_version": self.pack_version,
            "path": self.path,
            "entitlements_honored": self.entitlements_honored,
            "entries": [e.to_dict() for e in self.entries],
        }


@dataclass
class DecisionResult:
    decision: str  # allow | deny | inconclusive
    effects: list[Effect]
    entitlements_applied: list[EntitlementSnapshot]
    entitlements_to_create: list[Effect]
    trace: DecisionTrace
    pack_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "effects": [e.to_dict() for e in self.effects],
            "entitlements_applied": [e.to_dict() for e in self.entitlements_applied],
            "entitlements_to_create": [e.to_dict() for e in self.entitlements_to_create],
            "trace": self.trace.to_dict(),
            "pack_version": self.pack_version,
        }
