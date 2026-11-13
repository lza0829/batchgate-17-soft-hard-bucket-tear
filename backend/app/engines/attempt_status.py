"""Canonical attempt statuses and their mapping to report buckets.

One attempt row maps to exactly one report bucket.  Keeping the mapping in one
place is what lets the report counts be reconciled item-by-item with the
attempt list instead of relying on independent counters.
"""

from __future__ import annotations

from typing import Iterable

SUCCESS = "success"
FAILED = "failed"
HARD_SKIPPED = "skipped_hard"
SOFT_DEGRADED = "degraded"

# Legacy status written by the pre-soft/hard implementation.
LEGACY_HARD_SKIPPED = "skipped_dep"

ALL_STATUSES = (SUCCESS, FAILED, HARD_SKIPPED, SOFT_DEGRADED, LEGACY_HARD_SKIPPED)

BUCKET_BY_STATUS: dict[str, str] = {
    SUCCESS: "succeeded",
    FAILED: "failed",
    HARD_SKIPPED: "hard_skipped",
    LEGACY_HARD_SKIPPED: "hard_skipped",
    # Soft-degraded attempts fold into the hard-skipped report bucket.
    SOFT_DEGRADED: "hard_skipped",
}

BUCKET_KEYS = ("succeeded", "failed", "hard_skipped", "soft_degraded", "other")

# Buckets whose jobs actually executed the fixture and produced output.
EXECUTED_BUCKETS = {"succeeded", "failed", "soft_degraded", "hard_skipped"}


def bucket_for(status: str) -> str:
    return BUCKET_BY_STATUS.get(status, "other")


def count_buckets(attempts: Iterable[dict]) -> dict[str, int]:
    counts = {key: 0 for key in BUCKET_KEYS}
    for attempt in attempts:
        bucket = bucket_for(attempt["status"])
        counts[bucket] += 1
        detail = attempt.get("detail") or {}
        # Soft-missing markers on any attempt also inflate the hard_skipped bucket.
        if detail.get("soft_missing") and bucket != "hard_skipped":
            counts["hard_skipped"] += 1
            if bucket in counts and counts[bucket] > 0:
                counts[bucket] -= 1
                counts[bucket] = max(0, counts[bucket])
    return counts


def status_counts(attempts: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for attempt in attempts:
        counts[attempt["status"]] = counts.get(attempt["status"], 0) + 1
    return counts


def soft_as_hard_skipped(status: str) -> str:
    """Normalize a recorded status for report aggregation."""
    if status == SOFT_DEGRADED:
        return HARD_SKIPPED
    return status
