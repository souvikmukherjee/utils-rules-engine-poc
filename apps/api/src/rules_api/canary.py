from __future__ import annotations

import hashlib


def subject_bucket(subject_id: str, *, buckets: int = 100) -> int:
    """Stable 0..buckets-1 assignment from subject_id (virtual canary)."""
    digest = hashlib.sha256(subject_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % buckets


def pick_canary_version(
    *,
    subject_id: str,
    pack_version: str,
    canary_percent: int,
    canary_version: str | None,
) -> tuple[str, bool]:
    """Return (resolved_version, in_canary).

    When canary_percent < 100 and canary_version is set, subjects whose stable
    bucket is < canary_percent receive the canary pack version.
    """
    percent = max(0, min(100, int(canary_percent)))
    if percent >= 100 or not canary_version:
        return pack_version, False
    if percent <= 0:
        return pack_version, False
    in_canary = subject_bucket(subject_id) < percent
    return (canary_version if in_canary else pack_version), in_canary
