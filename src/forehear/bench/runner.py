"""Experiment matrix: scenarios x latency profiles x policies."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from ..controller import Controller
from ..policies import Adaptive, EagerEndOfTurn, FinalOnly, FixedInterval, StablePrefix
from ..text import normalize
from ..validators import ExactMatch, TokenCoverage, Validator
from .data import Turn
from .latency import PROFILES, LatencyProfile
from .metrics import summarize
from .sim import Oracle, SearchCache, Timing, simulate

__all__ = [
    "SCENARIOS",
    "PolicySpec",
    "retrievability_curve",
    "run_matrix",
    "standard_policies",
    "validator_sweep",
]

ControllerFactory = Callable[[], Controller]


@dataclass(frozen=True, slots=True)
class PolicySpec:
    name: str
    factory: ControllerFactory
    description: str
    needs_eager: bool = False


SCENARIOS: dict[str, Timing] = {
    # Most STT services (Deepgram Nova, AssemblyAI, Whisper-based) give you
    # interim transcripts and a final end-of-turn, nothing in between.
    "interims_only": Timing(eager_ms=None, eot_ms=500.0),
    # Deepgram Flux / LiveKit preflight / Pipecat eager strategies: an eager
    # end-of-turn 200 ms into silence, the real end of turn at 500 ms.
    "with_eager_eot": Timing(eager_ms=200.0, eot_ms=500.0),
}


def standard_policies(validator: Validator | None = None) -> list[PolicySpec]:
    """The policies reported in the README."""
    v = validator or TokenCoverage(0.8)

    def ctl(policy: Any, val: Validator | None = None, **kw: Any) -> ControllerFactory:
        return lambda: Controller(policy() if callable(policy) else policy, val or v, **kw)

    return [
        PolicySpec(
            "final_only", ctl(FinalOnly, ExactMatch()), "Retrieve on the final transcript (no look-ahead)."
        ),
        PolicySpec(
            "eager_eot",
            ctl(EagerEndOfTurn, ExactMatch()),
            "Retrieve once on the eager end-of-turn transcript.",
            needs_eager=True,
        ),
        PolicySpec(
            "interval_1000ms",
            ctl(lambda: FixedInterval(1000.0)),
            "Latest hypothesis every 1 s (Stream RAG fixed-interval).",
        ),
        PolicySpec("interval_500ms", ctl(lambda: FixedInterval(500.0)), "Latest hypothesis every 500 ms."),
        PolicySpec(
            "stable_prefix",
            ctl(lambda: StablePrefix(agreement=2, min_new_content_words=1)),
            "Words two consecutive hypotheses agree on, when a new content word appears.",
        ),
        PolicySpec(
            "stable_prefix_eager",
            ctl(lambda: StablePrefix(agreement=1, min_new_content_words=1)),
            "Every hypothesis with a new content word (most aggressive).",
        ),
        PolicySpec("adaptive", ctl(Adaptive), "Stable prefix with prefetch-style accuracy throttling."),
        PolicySpec(
            "oracle", ctl(Oracle, ExactMatch()), "Upper bound: the final transcript, on the first interim."
        ),
    ]


def run_matrix(
    turns: Sequence[Turn],
    search: SearchCache,
    *,
    scenarios: dict[str, Timing] | None = None,
    profiles: Iterable[LatencyProfile] | None = None,
    policies: Sequence[PolicySpec] | None = None,
    progress: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scenarios = scenarios if scenarios is not None else SCENARIOS
    profiles = list(profiles) if profiles is not None else list(PROFILES.values())
    policies = policies if policies is not None else standard_policies()
    for scen_name, timing in scenarios.items():
        for profile in profiles:
            for spec in policies:
                if spec.needs_eager and timing.eager_ms is None:
                    continue
                if progress:
                    progress(f"{scen_name} / {profile.name} / {spec.name}")
                results = simulate(turns, spec.factory, search, profile, timing)
                rows.append(
                    {
                        "scenario": scen_name,
                        "profile": profile.name,
                        "policy": spec.name,
                        **summarize(results).as_dict(),
                    }
                )
    return rows


def validator_sweep(
    turns: Sequence[Turn],
    search: SearchCache,
    profile: LatencyProfile,
    timing: Timing,
    thresholds: Sequence[float] = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
) -> list[dict[str, Any]]:
    """How the reuse threshold trades latency for retrieval quality."""
    rows = []

    def factory(th: float) -> ControllerFactory:
        return lambda: Controller(StablePrefix(agreement=1), TokenCoverage(th))

    for th in thresholds:
        results = simulate(
            turns,
            factory(th),
            search,
            profile,
            timing,
        )
        rows.append({"threshold": th, "profile": profile.name, **summarize(results).as_dict()})
    return rows


def retrievability_curve(
    turns: Sequence[Turn],
    search: SearchCache,
    offsets_ms: Sequence[float] = tuple(range(-3000, 501, 250)),
) -> list[dict[str, float]]:
    """Share of turns whose *current interim hypothesis* already retrieves a gold passage.

    ``offset`` is relative to the end of the last word. This answers the
    question every look-ahead design depends on: how early is the answer
    findable?
    """
    rows = []
    n = len(turns)
    final_hits = sum(any(d.id in t.gold for d in search(t.asr_final)) for t in turns) / n
    for off in offsets_ms:
        hits = speaking = 0
        for t in turns:
            at = t.speech_end_ms + off
            if at < t.speech_start_ms:
                continue
            speaking += 1
            text = ""
            for ts, hyp in t.events:
                if ts > at:
                    break
                text = hyp
            if normalize(text) and any(d.id in t.gold for d in search(text)):
                hits += 1
        rows.append(
            {
                "offset_ms": float(off),
                "retrievable": hits / n,
                "speaking": speaking / n,
                "final_recall": final_hits,
            }
        )
    return rows
