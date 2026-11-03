"""Experiment matrix: scenarios x latency profiles x policies."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from ..controller import Controller
from ..policies import Adaptive, EagerEndOfTurn, FinalOnly, FixedInterval, StablePrefix
from ..text import normalize
from ..validators import ExactMatch, ResultOverlap, TokenCoverage, Validator
from .data import Turn
from .latency import PROFILES, LatencyProfile
from .metrics import summarize
from .sim import Oracle, SearchCache, Timing, simulate

__all__ = [
    "SCENARIOS",
    "eot_sweep",
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


def standard_policies(
    validator: Validator | None = None,
    probe: Callable[[str], Sequence[str]] | None = None,
) -> list[PolicySpec]:
    """The policies reported in the README.

    Args:
        validator: Reuse validator for speculative policies (default ``TokenCoverage(0.8)``).
        probe: Cheap first-stage retriever (``query -> ids``). When given, a
            ``ResultOverlap`` variant is added.
    """
    v = validator or TokenCoverage(0.8)

    def ctl(make_policy: Callable[[], Any], val: Validator | None = None, **kw: Any) -> ControllerFactory:
        return lambda: Controller(make_policy(), val or v, **kw)

    specs = [
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
            "local_agreement",
            ctl(lambda: StablePrefix(agreement=2, min_content_words=2)),
            "Only words two consecutive hypotheses agree on (LocalAgreement-2).",
        ),
        PolicySpec(
            "stable_prefix",
            ctl(lambda: StablePrefix()),
            "forehear default: latest hypothesis once it has 3+ content words and a new one.",
        ),
        PolicySpec(
            "stable_prefix_lean",
            ctl(lambda: StablePrefix(min_content_words=4)),
            "As stable_prefix, but waits for 4+ content words (fewer calls).",
        ),
    ]
    if probe is not None:
        specs.append(
            PolicySpec(
                "stable_prefix_overlap",
                ctl(lambda: StablePrefix(), ResultOverlap(probe, k=5, threshold=0.8)),
                "stable_prefix, reusing only if a cheap first stage returns >=4 of the same top-5.",
            )
        )
    specs += [
        PolicySpec("adaptive", ctl(Adaptive), "stable_prefix levels steered by a 3-calls-per-turn budget."),
        PolicySpec(
            "oracle", ctl(Oracle, ExactMatch()), "Upper bound: the final transcript, on the first interim."
        ),
    ]
    return specs


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
    thresholds: Sequence[float] = (0.4, 0.6, 0.8, 0.9, 1.0),
    probe: Callable[[str], Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """How the reuse threshold trades latency for retrieval quality."""
    rows = []

    def factory(make: Callable[[float], Validator], th: float) -> ControllerFactory:
        return lambda: Controller(StablePrefix(), make(th))

    validators: list[tuple[str, Callable[[float], Validator]]] = [("token_coverage", TokenCoverage)]
    if probe is not None:
        validators.append(("result_overlap", lambda th: ResultOverlap(probe, k=5, threshold=th)))
    for vname, make in validators:
        for th in thresholds:
            results = simulate(turns, factory(make, th), search, profile, timing)
            rows.append(
                {"validator": vname, "threshold": th, "profile": profile.name, **summarize(results).as_dict()}
            )
    return rows


def eot_sweep(
    turns: Sequence[Turn],
    search: SearchCache,
    profiles: Sequence[LatencyProfile],
    eot_values_ms: Sequence[float] = (300.0, 500.0, 800.0),
    policy_names: Sequence[str] = ("final_only", "stable_prefix", "adaptive"),
    asr_lag_ms: float = 0.0,
) -> list[dict[str, Any]]:
    """How the turn detector's end-of-turn delay changes what look-ahead can save."""
    specs = {s.name: s for s in standard_policies()}
    rows = []
    for profile in profiles:
        for eot in eot_values_ms:
            timing = Timing(asr_lag_ms=asr_lag_ms, eager_ms=None, eot_ms=eot)
            for name in policy_names:
                results = simulate(turns, specs[name].factory, search, profile, timing)
                rows.append(
                    {"eot_ms": eot, "profile": profile.name, "policy": name, **summarize(results).as_dict()}
                )
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
