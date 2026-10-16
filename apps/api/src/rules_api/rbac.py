from __future__ import annotations

from fastapi import Header, HTTPException

ROLES = frozenset({"viewer", "author", "approver", "admin"})
PROMOTE_ROLES = frozenset({"approver", "admin"})
AUTHOR_ROLES = frozenset({"author", "approver", "admin"})
# Authors may submit drafts for review; approve/publish/retire need approver+.
AUTHOR_TRANSITION_TARGETS = frozenset({"in_review"})


def require_role(
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> str | None:
    """Optional RBAC stub. Missing header = unrestricted (PoC default)."""
    if x_role is None or x_role == "":
        return None
    role = x_role.strip().lower()
    if role not in ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid X-Role '{x_role}'. Expected one of: {sorted(ROLES)}",
        )
    return role


def assert_can_promote(role: str | None) -> None:
    if role is None:
        return
    if role not in PROMOTE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Promote/release requires X-Role: approver or admin",
        )


def assert_can_transition(role: str | None, to_lifecycle: str) -> None:
    """Authors can submit draft → in_review; approve/publish/retire need approver+."""
    if role is None:
        return
    if role in PROMOTE_ROLES:
        return
    if role in AUTHOR_ROLES and to_lifecycle in AUTHOR_TRANSITION_TARGETS:
        return
    raise HTTPException(
        status_code=403,
        detail=(
            "Transition to "
            f"'{to_lifecycle}' requires X-Role: approver or admin "
            "(authors may only submit drafts for review)"
        ),
    )


def assert_can_author(role: str | None) -> None:
    if role is None:
        return
    if role not in AUTHOR_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Draft pack writes require X-Role: author, approver, or admin",
        )
