"""The speculation controller: a sans-IO state machine.

The controller never awaits, sleeps or calls a retriever. It consumes
:class:`~forehear.events.TranscriptEvent` objects and retrieval completions,
and returns *actions* for the caller to execute:

* :class:`Start` - begin a retrieval call for ``spec.query``
* :class:`Cancel` - abandon an in-flight call
* :class:`Deliver` - the turn's context is ready; hand it to the LLM

Because all timing comes from event timestamps, the exact same controller runs
in production (driven by :class:`forehear.Lookahead` on an asyncio loop) and in
the benchmark (driven by a discrete-event simulator on a virtual clock). What
you measure is what you ship.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

from .events import EventKind, TranscriptEvent
from .policies import Policy, StablePrefix, TurnView
from .text import normalize
from .types import Delivery, Doc, SpecStatus, Speculation, TurnOutcome
from .validators import TokenCoverage, Validator

__all__ = ["Action", "Cancel", "Controller", "ControllerStats", "Deliver", "Start"]


@dataclass(frozen=True, slots=True)
class Start:
    spec: Speculation


@dataclass(frozen=True, slots=True)
class Cancel:
    spec_id: int


@dataclass(frozen=True, slots=True)
class Deliver:
    delivery: Delivery


Action = Start | Cancel | Deliver


@dataclass(slots=True)
class ControllerStats:
    """Cumulative counters across turns."""

    turns: int = 0
    speculative_calls: int = 0
    fresh_calls: int = 0
    cancelled_calls: int = 0
    reused_turns: int = 0
    late_turns: int = 0
    total_wait_ms: float = 0.0

    @property
    def accuracy(self) -> float:
        """Speculative calls that ended up serving a turn / speculative calls issued."""
        return self.reused_turns / self.speculative_calls if self.speculative_calls else 0.0

    @property
    def coverage(self) -> float:
        """Turns served from a speculative call / turns."""
        return self.reused_turns / self.turns if self.turns else 0.0

    @property
    def calls_per_turn(self) -> float:
        return (self.speculative_calls + self.fresh_calls) / self.turns if self.turns else 0.0

    @property
    def mean_wait_ms(self) -> float:
        return self.total_wait_ms / self.turns if self.turns else 0.0


@dataclass(slots=True)
class _Turn:
    view: TurnView = field(default_factory=TurnView)
    specs: dict[int, Speculation] = field(default_factory=dict)
    eot_ms: float | None = None
    final_query: str = ""
    awaiting: set[int] = field(default_factory=set)
    late: bool = False


class Controller:
    """Decides when to retrieve during a user turn and what to deliver at its end.

    Args:
        policy: When to fire speculative calls. Defaults to :class:`StablePrefix`.
        validator: When a speculative result may be reused for the final
            transcript. Defaults to ``TokenCoverage(0.8)``.
        max_inflight: Maximum concurrent speculative calls. When exceeded, the
            oldest in-flight call is cancelled (newer hypotheses are better).
        max_speculative_calls: Optional hard budget of speculative calls per turn.
        hedge: If the best reusable call is still in flight at end of turn,
            also start a fresh call on the final transcript and deliver
            whichever finishes first.
        when_full: What to do when ``max_inflight`` calls are already running:
            ``"cancel_oldest"`` (default; newer hypotheses are better guesses)
            or ``"drop_new"`` (keep the call closest to finishing; better for
            slow retrievers).

    Speculative calls must be **read-only**: they run on guesses and are
    routinely discarded. Never route side-effecting tools through forehear.
    """

    def __init__(
        self,
        policy: Policy | None = None,
        validator: Validator | None = None,
        *,
        max_inflight: int = 2,
        max_speculative_calls: int | None = None,
        hedge: bool = False,
        when_full: str = "cancel_oldest",
    ) -> None:
        if max_inflight < 1:
            raise ValueError("max_inflight must be >= 1")
        if when_full not in ("cancel_oldest", "drop_new"):
            raise ValueError("when_full must be 'cancel_oldest' or 'drop_new'")
        self.when_full = when_full
        self.policy = policy if policy is not None else StablePrefix()
        self.validator = validator if validator is not None else TokenCoverage(0.8)
        self.max_inflight = max_inflight
        self.max_speculative_calls = max_speculative_calls
        self.hedge = hedge
        self.stats = ControllerStats()
        self.last_outcome: TurnOutcome | None = None
        self.last_calls: list[Speculation] = []
        self._turn: _Turn | None = None
        self._next_id = 1
        self._backlog: deque[TranscriptEvent] = deque()

    # ------------------------------------------------------------------ public

    @property
    def awaiting_delivery(self) -> bool:
        """True between end of turn and delivery."""
        return self._turn is not None and self._turn.eot_ms is not None

    @property
    def calls(self) -> list[Speculation]:
        """Calls issued in the current turn."""
        return list(self._turn.specs.values()) if self._turn else []

    def handle(self, event: TranscriptEvent) -> list[Action]:
        """Feed one transcript event; returns actions to execute."""
        if self.awaiting_delivery:
            # The next turn started before this turn's context arrived.
            # Replay these events once we have delivered.
            self._backlog.append(event)
            return []
        return self._handle(event)

    def on_result(self, spec_id: int, docs: Sequence[Doc], t_ms: float) -> list[Action]:
        """Report that call ``spec_id`` returned ``docs`` at ``t_ms``."""
        turn = self._turn
        spec = turn.specs.get(spec_id) if turn else None
        if spec is None or spec.status is not SpecStatus.PENDING or turn is None:
            return []  # stale result from a cancelled call or a previous turn
        spec.status = SpecStatus.DONE
        spec.docs = tuple(docs)
        spec.done_ms = t_ms
        if spec_id not in turn.awaiting:
            return []
        actions: list[Action] = [Cancel(other) for other in turn.awaiting if other != spec_id]
        for other in turn.awaiting:
            if other != spec_id:
                turn.specs[other].status = SpecStatus.CANCELLED
        actions.append(self._deliver(spec, t_ms))
        actions.extend(self._drain_backlog())
        return actions

    def on_error(self, spec_id: int, t_ms: float) -> list[Action]:
        """Report that call ``spec_id`` failed."""
        turn = self._turn
        spec = turn.specs.get(spec_id) if turn else None
        if spec is None or spec.status is not SpecStatus.PENDING or turn is None:
            return []
        spec.status = SpecStatus.FAILED
        spec.done_ms = t_ms
        if spec_id not in turn.awaiting:
            return []
        turn.awaiting.discard(spec_id)
        if turn.awaiting:
            return []  # a hedged call is still running
        if spec.speculative:
            fresh = self._new_spec(turn.final_query, t_ms, speculative=False, trigger="fallback")
            turn.awaiting.add(fresh.id)
            return [Start(fresh)]
        failed = Delivery(
            docs=(),
            query=spec.query,
            final_query=turn.final_query,
            reused=False,
            eot_ms=turn.eot_ms or t_ms,
            delivered_ms=t_ms,
            spec_id=spec.id,
            failed=True,
        )
        return [Deliver(self._finish(failed, None)), *self._drain_backlog()]

    # ---------------------------------------------------------------- internals

    def _handle(self, event: TranscriptEvent) -> list[Action]:
        kind = event.kind
        if kind is EventKind.SPEECH_START:
            self._begin(event.t_ms)
            return []
        if self._turn is None:
            self._begin(event.t_ms if kind is not EventKind.END_OF_TURN else None)
        turn = self._turn
        assert turn is not None
        if kind is EventKind.END_OF_TURN:
            return self._end_of_turn(event)
        if kind is EventKind.INTERIM:
            text = normalize(event.text)
            if turn.view.hypotheses and turn.view.hypotheses[-1][1] == text:
                return []
            turn.view.hypotheses.append((event.t_ms, text))
        query = self.policy.propose(event, turn.view)
        if query is None:
            return []
        return self._fire(query, event.t_ms, trigger=kind.value)

    def _begin(self, t_ms: float | None) -> None:
        self._turn = _Turn(view=TurnView(speech_start_ms=t_ms))
        self.policy.reset_turn()

    def _new_spec(self, query: str, t_ms: float, *, speculative: bool, trigger: str) -> Speculation:
        assert self._turn is not None
        spec = Speculation(
            id=self._next_id, query=query, issued_ms=t_ms, speculative=speculative, trigger=trigger
        )
        self._next_id += 1
        self._turn.specs[spec.id] = spec
        if speculative:
            self.stats.speculative_calls += 1
        else:
            self.stats.fresh_calls += 1
        return spec

    def _fire(self, query: str, t_ms: float, *, trigger: str) -> list[Action]:
        turn = self._turn
        assert turn is not None
        norm = normalize(query)
        if not norm:
            return []
        live = [s for s in turn.specs.values() if s.status in (SpecStatus.PENDING, SpecStatus.DONE)]
        if any(normalize(s.query) == norm for s in live):
            return []
        n_spec = sum(1 for s in turn.specs.values() if s.speculative)
        if self.max_speculative_calls is not None and n_spec >= self.max_speculative_calls:
            return []
        actions: list[Action] = []
        pending = sorted((s for s in live if s.pending), key=lambda s: s.issued_ms)
        if len(pending) >= self.max_inflight and self.when_full == "drop_new":
            return []
        while len(pending) >= self.max_inflight:
            oldest = pending.pop(0)
            oldest.status = SpecStatus.CANCELLED
            actions.append(Cancel(oldest.id))
        spec = self._new_spec(query, t_ms, speculative=True, trigger=trigger)
        turn.view.fired.append(norm)
        turn.view.last_fire_ms = t_ms
        turn.view.inflight = len(pending) + 1
        actions.append(Start(spec))
        return actions

    def _end_of_turn(self, event: TranscriptEvent) -> list[Action]:
        turn = self._turn
        assert turn is not None
        t = event.t_ms
        turn.eot_ms = t
        turn.final_query = event.text.strip()
        actions: list[Action] = []
        if not normalize(turn.final_query):
            for s in turn.specs.values():
                if s.pending:
                    s.status = SpecStatus.CANCELLED
                    actions.append(Cancel(s.id))
            empty = Delivery((), "", turn.final_query, False, t, t, -1)
            actions.append(Deliver(self._finish(empty, None)))
            actions.extend(self._drain_backlog())
            return actions

        scored = [
            (self.validator.score(s.query, turn.final_query), s)
            for s in turn.specs.values()
            if s.speculative and s.status in (SpecStatus.PENDING, SpecStatus.DONE)
        ]
        accepted = [(sc, s) for sc, s in scored if sc >= self.validator.threshold]
        ready = [(sc, s) for sc, s in accepted if s.status is SpecStatus.DONE]

        if ready:
            _, best = max(ready, key=lambda p: (p[0], p[1].issued_ms))
            actions.extend(self._cancel_pending(except_ids=()))
            actions.append(self._deliver(best, t))
            actions.extend(self._drain_backlog())
            return actions

        if accepted:
            # Highest score; among equals the earliest issued (closest to done).
            _, best = max(accepted, key=lambda p: (p[0], -p[1].issued_ms))
            actions.extend(self._cancel_pending(except_ids=(best.id,)))
            turn.awaiting.add(best.id)
            turn.late = True
            if self.hedge:
                fresh = self._new_spec(turn.final_query, t, speculative=False, trigger="hedge")
                turn.awaiting.add(fresh.id)
                actions.append(Start(fresh))
            return actions

        actions.extend(self._cancel_pending(except_ids=()))
        fresh = self._new_spec(turn.final_query, t, speculative=False, trigger="final")
        turn.awaiting.add(fresh.id)
        actions.append(Start(fresh))
        return actions

    def _cancel_pending(self, except_ids: Sequence[int]) -> list[Action]:
        assert self._turn is not None
        out: list[Action] = []
        for s in self._turn.specs.values():
            if s.pending and s.id not in except_ids:
                s.status = SpecStatus.CANCELLED
                out.append(Cancel(s.id))
        return out

    def _deliver(self, spec: Speculation, t_ms: float) -> Deliver:
        turn = self._turn
        assert turn is not None and turn.eot_ms is not None
        delivery = Delivery(
            docs=spec.docs,
            query=spec.query,
            final_query=turn.final_query,
            reused=spec.speculative,
            eot_ms=turn.eot_ms,
            delivered_ms=max(t_ms, turn.eot_ms),
            spec_id=spec.id,
        )
        return Deliver(self._finish(delivery, spec))

    def _finish(self, delivery: Delivery, used: Speculation | None) -> Delivery:
        turn = self._turn
        assert turn is not None
        specs = list(turn.specs.values())
        n_spec = sum(1 for s in specs if s.speculative)
        n_cancel = sum(1 for s in specs if s.status is SpecStatus.CANCELLED)
        reused = used is not None and used.speculative
        late = reused and turn.late and delivery.wait_ms > 0
        outcome = TurnOutcome(
            speculative_calls=n_spec,
            cancelled_calls=n_cancel,
            reused=reused,
            late=late,
            wait_ms=delivery.wait_ms,
            fresh_call=any(not s.speculative for s in specs),
            call_latencies_ms=tuple(
                s.done_ms - s.issued_ms
                for s in specs
                if s.status is SpecStatus.DONE and s.done_ms is not None
            ),
        )
        st = self.stats
        st.turns += 1
        st.cancelled_calls += n_cancel
        st.reused_turns += int(reused)
        st.late_turns += int(late)
        st.total_wait_ms += delivery.wait_ms
        self.last_outcome = outcome
        self.last_calls = specs
        self.policy.feedback(outcome)
        self._turn = None
        return delivery

    def _drain_backlog(self) -> list[Action]:
        actions: list[Action] = []
        while self._backlog and not self.awaiting_delivery:
            actions.extend(self._handle(self._backlog.popleft()))
        return actions
