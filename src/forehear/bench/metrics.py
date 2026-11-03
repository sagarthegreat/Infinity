"""Aggregate metrics, named after their hardware-prefetching ancestors where one exists."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from .sim import TurnResult

__all__ = ["Summary", "percentile", "summarize"]


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolated percentile, ``q`` in [0, 100]."""
    if not values:
        return 0.0
    xs = sorted(values)
    pos = (len(xs) - 1) * q / 100.0
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


@dataclass(frozen=True, slots=True)
class Summary:
    turns: int
    # latency
    wait_mean_ms: float
    wait_p50_ms: float
    wait_p90_ms: float
    wait_p95_ms: float
    baseline_wait_mean_ms: float
    baseline_wait_p50_ms: float
    baseline_wait_p90_ms: float
    saved_mean_ms: float
    saved_p50_ms: float
    saved_p90_ms: float
    zero_wait_rate: float
    """Share of turns whose context was ready at end of turn."""
    # speculation quality (prefetch vocabulary)
    coverage: float
    """Turns served from a speculative call / turns."""
    accuracy: float
    """Speculative calls that served a turn / speculative calls issued."""
    lateness: float
    """Served turns where the speculative call was still in flight at end of turn."""
    # cost
    calls_per_turn: float
    speculative_calls_per_turn: float
    wasted_calls_per_turn: float
    # quality
    recall_at_k: float
    baseline_recall_at_k: float
    recall_delta: float
    lead_mean_ms: float
    """Mean lead time over turns where a speculative call held a gold passage before end of turn."""

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def summarize(results: Sequence[TurnResult]) -> Summary:
    n = len(results)
    if n == 0:
        raise ValueError("no results")
    waits = [r.wait_ms for r in results]
    base = [r.baseline_wait_ms for r in results]
    saved = [r.saved_ms for r in results]
    spec_calls = sum(r.speculative_calls for r in results)
    total_calls = sum(r.speculative_calls + r.fresh_calls for r in results)
    served = [r for r in results if r.reused]
    leads = [r.lead_ms for r in results if r.lead_ms is not None]
    recall = sum(r.hit for r in results) / n
    base_recall = sum(r.baseline_hit for r in results) / n
    return Summary(
        turns=n,
        wait_mean_ms=sum(waits) / n,
        wait_p50_ms=percentile(waits, 50),
        wait_p90_ms=percentile(waits, 90),
        wait_p95_ms=percentile(waits, 95),
        baseline_wait_mean_ms=sum(base) / n,
        baseline_wait_p50_ms=percentile(base, 50),
        baseline_wait_p90_ms=percentile(base, 90),
        saved_mean_ms=sum(saved) / n,
        saved_p50_ms=percentile(saved, 50),
        saved_p90_ms=percentile(saved, 90),
        zero_wait_rate=sum(1 for w in waits if w <= 0.0) / n,
        coverage=len(served) / n,
        accuracy=len(served) / spec_calls if spec_calls else 0.0,
        lateness=(sum(r.late for r in served) / len(served)) if served else 0.0,
        calls_per_turn=total_calls / n,
        speculative_calls_per_turn=spec_calls / n,
        wasted_calls_per_turn=sum(r.wasted_calls for r in results) / n,
        recall_at_k=recall,
        baseline_recall_at_k=base_recall,
        recall_delta=recall - base_recall,
        lead_mean_ms=(sum(leads) / len(leads)) if leads else 0.0,
    )
