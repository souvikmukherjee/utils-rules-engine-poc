from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RulesStore(ABC):
    """Persistence boundary for packs, releases, entitlements, and audit."""

    @abstractmethod
    def list_pack_versions(self, domain: str, *, tenant_id: str = "default") -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_pack_version(
        self, domain: str, pack_id: str, version: str, *, tenant_id: str = "default"
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def get_pack_payload(
        self, domain: str, pack_id: str, version: str, *, tenant_id: str = "default"
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def upsert_pack_version(
        self,
        *,
        domain: str,
        pack_id: str,
        version: str,
        lifecycle: str,
        payload: dict[str, Any],
        tenant_id: str = "default",
    ) -> None:
        ...

    @abstractmethod
    def update_pack_lifecycle(
        self,
        domain: str,
        pack_id: str,
        version: str,
        lifecycle: str,
        *,
        tenant_id: str = "default",
    ) -> bool:
        ...

    @abstractmethod
    def get_release(
        self, domain: str, pack_id: str, environment: str, *, tenant_id: str = "default"
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def upsert_release(
        self,
        *,
        domain: str,
        pack_id: str,
        environment: str,
        pack_version: str,
        go_live_at: str | None = None,
        canary_percent: int = 100,
        canary_version: str | None = None,
        change_record_id: str | None = None,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def list_entitlements(
        self,
        *,
        domain: str,
        subject_id: str,
        tenant_id: str = "default",
        grandfathered: bool | None = None,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def active_entitlement_rows(
        self,
        *,
        domain: str,
        subject_id: str,
        tenant_id: str = "default",
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def insert_entitlement(self, row: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_audit(self, evaluation_id: str, *, tenant_id: str = "default") -> dict[str, Any] | None:
        ...

    @abstractmethod
    def search_audit(
        self,
        *,
        domain: str,
        subject_id: str,
        tenant_id: str = "default",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def insert_audit(self, row: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def commit(self) -> None:
        ...
