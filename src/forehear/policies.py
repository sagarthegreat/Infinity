"""Speculation policies: *when* to fire a retrieval call, and with *what* query.

A policy sees every transcript event and the controller's view of the current
turn, and returns either a query string (fire a speculative retrieval) or
``None``. Policies never perform I/O and never cancel anything; budgets,
de-duplication and cancellation are the controller's job. That keeps policies
small, deterministic and easy to unit-test.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

from .events import EventKind, TranscriptEvent
from .text import content_words, drop_last, words
from .types import TurnOutcome

__all__ = [
    "Adaptive",
    "EagerEndOfTurn",
    "FinalOnly",
    "FixedInterval",
    "Policy",
    "StablePrefix",
    "TurnView",
]


@dataclass(slots=True)
class TurnView:
    """Read-only view of the current turn handed to policies."""

    speech_start_ms: float | None = None
    hypotheses: list[tuple[float, str]] = field(default_factory=list)
    """``(t_ms, text)`` of every interim hypothesis seen so far, oldest first."""
    fired: list[str] = field(default_factory=list)
    """Normalised queries already issued this turn, oldest first."""
    last_fire_ms: float | None = None
    inflight: int = 0


class Policy:
    """Base class. Subclasses override :meth:`propose`."""

    name: str = "policy"

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:  # pragma: no cover
        return None

    def reset_turn(self) -> None:
        """Called at the start of every turn."""

    def feedback(self, outcome: TurnOutcome) -> None:
        """Called after every turn with what happened. Used by adaptive policies."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class FinalOnly(Policy):
    """Never speculate. Retrieval runs on the final transcript: today's default."""

    name = "final_only"

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        return None


class EagerEndOfTurn(Policy):
    """Retrieve once, on the eager end-of-turn signal.

    This is what you can build today on Deepgram Flux ``EagerEndOfTurn``,
    LiveKit preflight transcripts or Pipecat eager turn strategies, and it is
    the baseline any look-ahead policy has to beat.
    """

    name = "eager_eot"

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        if event.kind is EventKind.EAGER_END_OF_TURN and event.text.strip():
            return event.text
        return None


def _enough(query: str, min_content_words: int) -> bool:
    return len(content_words(query)) >= min_content_words


class FixedInterval(Policy):
    """Fire on the latest hypothesis every ``interval_ms`` (Stream RAG's fixed-interval mode).

    Args:
        interval_ms: Minimum time between speculative calls.
        holdback: Drop this many trailing (unstable) words before querying.
        min_content_words: Skip hypotheses with fewer non-stopwords than this.
        fire_on_eager: Also fire on the eager end-of-turn transcript.
    """

    name = "fixed_interval"

    def __init__(
        self,
        interval_ms: float = 1000.0,
        *,
        holdback: int = 0,
        min_content_words: int = 1,
        fire_on_eager: bool = True,
    ) -> None:
        self.interval_ms = interval_ms
        self.holdback = holdback
        self.min_content_words = min_content_words
        self.fire_on_eager = fire_on_eager
        self.name = f"interval_{int(interval_ms)}ms"

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        if event.kind is EventKind.EAGER_END_OF_TURN:
            return event.text if self.fire_on_eager and event.text.strip() else None
        if event.kind is not EventKind.INTERIM:
            return None
        anchor = view.last_fire_ms
        if anchor is None:
            anchor = view.speech_start_ms
        if anchor is None and view.hypotheses:
            anchor = view.hypotheses[0][0]
        if anchor is not None and event.t_ms - anchor < self.interval_ms:
            return None
        query = drop_last(event.text, self.holdback)
        return query if _enough(query, self.min_content_words) else None

    def __repr__(self) -> str:
        return f"FixedInterval(interval_ms={self.interval_ms}, holdback={self.holdback})"


def _common_prefix(seqs: Sequence[list[str]]) -> list[str]:
    if not seqs:
        return []
    out: list[str] = []
    for column in zip(*seqs, strict=False):
        if all(tok == column[0] for tok in column):
            out.append(column[0])
        else:
            break
    return out


class StablePrefix(Policy):
    """Fire when the hypothesis has gained new content words.

    The query is the words the last ``agreement`` hypotheses agree on (the
    LocalAgreement idea from streaming speech translation), minus ``holdback``
    trailing words. It fires once it has at least ``min_content_words``
    non-stopwords and ``min_new_content_words`` that were not in the previous
    query.

    Defaults come from the benchmark (``docs/benchmark.md``). Waiting for
    agreement (``agreement=2``) or holding back words *loses*: the last words
    of an utterance are never confirmed by a later hypothesis, and they are
    the words retrieval needs most. Requiring three content words, on the other
    hand, skips most doomed early calls for almost no loss in savings.

    Args:
        agreement: Number of consecutive hypotheses that must agree on a word.
            ``1`` (default) trusts every interim.
        holdback: Extra trailing words to drop from the stable prefix.
        min_content_words: Minimum non-stopwords in a query.
        min_new_content_words: Minimum non-stopwords not present in the last
            fired query.
        fire_on_eager: Also fire on the eager end-of-turn transcript.
    """

    name = "stable_prefix"

    def __init__(
        self,
        agreement: int = 1,
        *,
        holdback: int = 0,
        min_content_words: int = 3,
        min_new_content_words: int = 1,
        fire_on_eager: bool = True,
    ) -> None:
        if agreement < 1:
            raise ValueError("agreement must be >= 1")
        self.agreement = agreement
        self.holdback = holdback
        self.min_content_words = min_content_words
        self.min_new_content_words = min_new_content_words
        self.fire_on_eager = fire_on_eager

    def stable_query(self, view: TurnView) -> str:
        recent = [words(text) for _, text in view.hypotheses[-self.agreement :]]
        if len(recent) < self.agreement:
            return ""
        prefix = _common_prefix(recent)
        if self.holdback:
            prefix = prefix[: max(0, len(prefix) - self.holdback)]
        return " ".join(prefix)

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        if event.kind is EventKind.EAGER_END_OF_TURN:
            return event.text if self.fire_on_eager and event.text.strip() else None
        if event.kind is not EventKind.INTERIM:
            return None
        query = self.stable_query(view)
        if not _enough(query, self.min_content_words):
            return None
        new = set(content_words(query))
        if view.fired:
            new -= set(content_words(view.fired[-1]))
        if len(new) < self.min_new_content_words:
            return None
        return query

    def __repr__(self) -> str:
        return (
            f"StablePrefix(agreement={self.agreement}, holdback={self.holdback}, "
            f"min_content_words={self.min_content_words}, "
            f"min_new_content_words={self.min_new_content_words})"
        )


@dataclass(frozen=True, slots=True)
class _Level:
    min_content_words: int
    min_new_content_words: int
    speculate: bool = True


class Adaptive(Policy):
    """Budgeted, feedback-directed speculation.

    The idea comes from feedback-directed hardware prefetching (Srinath et al.,
    HPCA 2007): measure what speculation is buying you and move between
    aggressiveness levels. A per-call "accuracy" signal does not transfer well
    to retrieval, though: several guesses per turn are normal and at most one
    is used. So this policy steers by what an operator actually cares about:

    * **budget** - you say how many retrieval calls per turn you are willing
      to pay for (``final_only`` is 1.0);
    * **coverage / lateness** - the share of turns served by a speculative
      call, and how many of those were still in flight at end of turn;
    * **observed latency** - if your retriever is so fast that waiting for it
      costs less than ``min_latency_ms``, speculation cannot buy anything and
      the policy falls back to the eager end-of-turn signal alone.

    Every ``window`` turns it moves one level down when over budget, one level
    up when comfortably under budget and turns are still being missed or
    served late. Level 0 only fires on the eager end-of-turn signal.

    Args:
        budget: Target retrieval calls per turn, all calls included.
        min_latency_ms: Median observed retrieval latency below which
            speculation is switched off.
        start_level: Index into :attr:`LEVELS` to start from.
        window: Turns between adjustments.
        target_coverage: Stop climbing once this share of turns is served on time.
    """

    name = "adaptive"

    #: Ordered from cheapest to most aggressive; each step is on the benchmark's
    #: cost/latency frontier.
    LEVELS: tuple[_Level, ...] = (
        _Level(min_content_words=99, min_new_content_words=99, speculate=False),  # eager EOT only
        _Level(min_content_words=5, min_new_content_words=2),
        _Level(min_content_words=4, min_new_content_words=1),
        _Level(min_content_words=3, min_new_content_words=1),
        _Level(min_content_words=2, min_new_content_words=1),
    )

    def __init__(
        self,
        *,
        budget: float = 3.0,
        min_latency_ms: float = 40.0,
        start_level: int = 3,
        window: int = 16,
        target_coverage: float = 0.95,
        late_fraction: float = 0.10,
        holdback: int = 0,
    ) -> None:
        if not 0 <= start_level < len(self.LEVELS):
            raise ValueError(f"start_level must be in [0, {len(self.LEVELS) - 1}]")
        if budget < 1.0:
            raise ValueError("budget must be >= 1.0 (one call per turn is the floor)")
        self.budget = budget
        self.min_latency_ms = min_latency_ms
        self.level = start_level
        self.window = window
        self.target_coverage = target_coverage
        self.late_fraction = late_fraction
        self.holdback = holdback
        self._history: deque[TurnOutcome] = deque(maxlen=window)
        self._latencies: deque[float] = deque(maxlen=4 * window)
        self._since_adjust = 0
        self.level_trace: list[int] = [start_level]
        self._inner = self._make_inner()

    def _make_inner(self) -> StablePrefix:
        lvl = self.LEVELS[self.level]
        return StablePrefix(
            agreement=1,
            holdback=self.holdback,
            min_content_words=lvl.min_content_words,
            min_new_content_words=lvl.min_new_content_words,
        )

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        if event.kind is EventKind.EAGER_END_OF_TURN:
            return event.text if event.text.strip() else None
        if not self.LEVELS[self.level].speculate:
            return None
        return self._inner.propose(event, view)

    def feedback(self, outcome: TurnOutcome) -> None:
        self._history.append(outcome)
        self._latencies.extend(outcome.call_latencies_ms)
        self._since_adjust += 1
        if self._since_adjust < self.window:
            return
        self._since_adjust = 0
        turns = len(self._history)
        calls = sum(o.speculative_calls + int(o.fresh_call) for o in self._history) / turns
        served = [o for o in self._history if o.reused]
        coverage = len(served) / turns
        on_time = sum(1 for o in served if not o.late) / turns
        late = (sum(o.late for o in served) / len(served)) if served else 0.0
        if self._latencies:
            lat = sorted(self._latencies)[len(self._latencies) // 2]
            if lat < self.min_latency_ms:
                self._set(0)
                return
        if calls > self.budget:
            self._set(self.level - 1)
        elif calls < 0.75 * self.budget and (on_time < self.target_coverage or late > self.late_fraction):
            self._set(self.level + 1)
        elif coverage >= self.target_coverage and late <= self.late_fraction and calls > 0.9 * self.budget:
            self._set(self.level - 1)
        else:
            self.level_trace.append(self.level)

    def _set(self, level: int) -> None:
        new = min(max(level, 0), len(self.LEVELS) - 1)
        if new != self.level:
            self.level = new
            self._inner = self._make_inner()
        self.level_trace.append(self.level)

    def __repr__(self) -> str:
        return f"Adaptive(budget={self.budget}, level={self.level}, window={self.window})"
