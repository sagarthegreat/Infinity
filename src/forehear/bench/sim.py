"""Discrete-event simulator: replays recorded turns through a real Controller on a virtual clock."""

from __future__ import annotations

import heapq
import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ..controller import Action, Cancel, Controller, Deliver, Start
from ..events import EventKind, TranscriptEvent
from ..policies import Policy, TurnView
from ..text import normalize
from ..types import Delivery, Doc
from .data import Turn
from .latency import LatencyProfile

__all__ = ["Oracle", "SearchCache", "Timing", "TurnResult", "simulate", "simulate_turn"]


@dataclass(frozen=True, slots=True)
class Timing:
    """How the voice pipeline's turn signals are placed relative to the speech.

    Args:
        asr_lag_ms: Added to every interim hypothesis timestamp (network and
            ASR compute; the recorded traces are in audio time).
        eager_ms: Silence after which an *eager* end-of-turn fires, or ``None``
            if the speech stack has no eager signal (most don't). Eager signals
            also fire on mid-utterance pauses at least this long, followed by
            ``TURN_RESUMED`` when the user carries on, just as a real
            silence-based detector would.
        eot_ms: End of turn fires this long after the last word ends. 300-550 ms
            is typical of production turn detectors.
    """

    asr_lag_ms: float = 0.0
    eager_ms: float | None = None
    eot_ms: float = 500.0


class Oracle(Policy):
    """Upper bound: fires the *final* transcript on the first interim hypothesis.

    No real policy can do this; it shows the most look-ahead could ever save.
    """

    name = "oracle"

    def __init__(self) -> None:
        self.final = ""

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        if event.kind in (EventKind.INTERIM, EventKind.EAGER_END_OF_TURN) and self.final:
            return self.final
        return None


class SearchCache:
    """Memoises ``search(query)`` by normalised query; the simulator calls it a lot."""

    def __init__(self, search: Callable[[str, int], Sequence[Doc]], k: int) -> None:
        self._search = search
        self.k = k
        self._cache: dict[str, tuple[Doc, ...]] = {}

    def __call__(self, query: str) -> tuple[Doc, ...]:
        key = normalize(query)
        hit = self._cache.get(key)
        if hit is None:
            hit = tuple(self._search(query, self.k))
            self._cache[key] = hit
        return hit

    def ids(self, query: str) -> list[str]:
        """Top-k ids for ``query``: a ready-made ``ResultOverlap`` probe."""
        return [d.id for d in self(query)]

    def __len__(self) -> int:
        return len(self._cache)


@dataclass(frozen=True, slots=True)
class TurnResult:
    id: str
    speech_ms: float
    wait_ms: float
    """Time from end of turn until context was ready."""
    baseline_wait_ms: float
    """Wait under no speculation (retrieve on the final transcript)."""
    reused: bool
    late: bool
    speculative_calls: int
    fresh_calls: int
    cancelled_calls: int
    hit: bool
    """A gold passage is in the delivered top-k."""
    baseline_hit: bool
    """A gold passage is in the top-k for the final transcript."""
    lead_ms: float | None
    """How long before end of turn a completed speculative call first held a gold passage."""

    @property
    def saved_ms(self) -> float:
        return self.baseline_wait_ms - self.wait_ms

    @property
    def wasted_calls(self) -> int:
        return self.speculative_calls - int(self.reused)


def _hypothesis_at(events: Sequence[TranscriptEvent], t_ms: float) -> str:
    text = ""
    for ev in events:
        if ev.t_ms > t_ms:
            break
        text = ev.text
    return text


def _turn_events(turn: Turn, timing: Timing) -> list[TranscriptEvent]:
    eot_t = turn.speech_end_ms + timing.eot_ms
    interims = [
        TranscriptEvent.interim(t + timing.asr_lag_ms, text)
        for t, text in turn.events
        if text and t + timing.asr_lag_ms < eot_t
    ]
    events = [TranscriptEvent.speech_start(turn.speech_start_ms), *interims]
    eager = timing.eager_ms
    if eager is not None and eager < timing.eot_ms:
        # False alarms: pauses inside the utterance.
        for (_, _, end), (_, nxt_start, _) in zip(turn.words, turn.words[1:], strict=False):
            if nxt_start - end > eager:
                t = end + eager
                text = _hypothesis_at(interims, t)
                if text:
                    events.append(TranscriptEvent.eager_end_of_turn(t, text))
                    events.append(TranscriptEvent.turn_resumed(nxt_start))
        events.append(TranscriptEvent.eager_end_of_turn(turn.speech_end_ms + eager, turn.asr_final))
    events.append(TranscriptEvent.end_of_turn(eot_t, turn.asr_final))
    events.sort(key=lambda e: (e.t_ms, e.kind is EventKind.END_OF_TURN))
    return events


def simulate_turn(
    turn: Turn,
    controller: Controller,
    search: SearchCache,
    profile: LatencyProfile,
    timing: Timing = Timing(),  # noqa: B008
) -> TurnResult:
    """Run one turn through ``controller`` and score it."""
    if isinstance(controller.policy, Oracle):
        controller.policy.final = turn.asr_final
    seq = itertools.count()
    queue: list[tuple[float, int, str, object]] = []
    for ev in _turn_events(turn, timing):
        heapq.heappush(queue, (ev.t_ms, next(seq), "event", ev))
    inflight: dict[int, tuple[str, float]] = {}
    completed: list[tuple[float, bool]] = []  # (t, contains gold) for speculative calls
    delivery: Delivery | None = None

    def latency(query: str) -> float:
        return profile.sample(f"{turn.id}|{normalize(query)}")

    def execute(actions: list[Action]) -> None:
        nonlocal delivery
        for a in actions:
            if isinstance(a, Start):
                done_t = a.spec.issued_ms + latency(a.spec.query)
                inflight[a.spec.id] = (a.spec.query, a.spec.issued_ms)
                heapq.heappush(queue, (done_t, next(seq), "result", (a.spec.id, a.spec.speculative)))
            elif isinstance(a, Cancel):
                inflight.pop(a.spec_id, None)
            elif isinstance(a, Deliver) and delivery is None:
                delivery = a.delivery

    while queue and delivery is None:
        t, _, kind, payload = heapq.heappop(queue)
        if kind == "event":
            assert isinstance(payload, TranscriptEvent)
            execute(controller.handle(payload))
        else:
            assert isinstance(payload, tuple)
            spec_id: int = payload[0]
            speculative: bool = payload[1]
            entry = inflight.pop(spec_id, None)
            if entry is None:
                continue  # cancelled
            docs = search(entry[0])
            if speculative:
                completed.append((t, any(d.id in turn.gold for d in docs)))
            execute(controller.on_result(spec_id, docs, t))
    if delivery is None:  # pragma: no cover - controller always delivers
        raise RuntimeError(f"no delivery for turn {turn.id}")

    calls = controller.last_calls
    outcome = controller.last_outcome
    assert outcome is not None
    eot = delivery.eot_ms
    baseline_wait = latency(turn.asr_final)
    lead = None
    for t, has_gold in sorted(completed):
        if has_gold and t <= eot:
            lead = eot - t
            break
    return TurnResult(
        id=turn.id,
        speech_ms=turn.speech_ms,
        wait_ms=delivery.wait_ms,
        baseline_wait_ms=baseline_wait,
        reused=delivery.reused,
        late=outcome.late,
        speculative_calls=sum(1 for c in calls if c.speculative),
        fresh_calls=sum(1 for c in calls if not c.speculative),
        cancelled_calls=outcome.cancelled_calls,
        hit=any(d.id in turn.gold for d in delivery.docs),
        baseline_hit=any(d.id in turn.gold for d in search(turn.asr_final)),
        lead_ms=lead,
    )


def simulate(
    turns: Sequence[Turn],
    make_controller: Callable[[], Controller],
    search: SearchCache,
    profile: LatencyProfile,
    timing: Timing = Timing(),  # noqa: B008
) -> list[TurnResult]:
    """Run every turn through one controller (one long session, so adaptive policies learn)."""
    controller = make_controller()
    return [simulate_turn(t, controller, search, profile, timing) for t in turns]
