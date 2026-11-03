from __future__ import annotations

import pytest

from forehear import (
    Adaptive,
    EagerEndOfTurn,
    FinalOnly,
    FixedInterval,
    StablePrefix,
    TranscriptEvent,
    TurnView,
)
from forehear.types import TurnOutcome

E = TranscriptEvent


def view(
    *hyps: str, fired: tuple[str, ...] = (), start: float = 0.0, last_fire: float | None = None
) -> TurnView:
    return TurnView(
        speech_start_ms=start,
        hypotheses=[(i * 100.0, h) for i, h in enumerate(hyps)],
        fired=list(fired),
        last_fire_ms=last_fire,
    )


def test_final_only_never_fires():
    p = FinalOnly()
    assert p.propose(E.interim(100, "anything at all"), view("anything at all")) is None
    assert p.propose(E.eager_end_of_turn(100, "anything"), view()) is None


def test_eager_fires_only_on_eager_signal():
    p = EagerEndOfTurn()
    assert p.propose(E.interim(100, "hello there"), view("hello there")) is None
    assert p.propose(E.eager_end_of_turn(100, "hello there"), view()) == "hello there"
    assert p.propose(E.eager_end_of_turn(100, "  "), view()) is None


def test_fixed_interval_respects_interval():
    p = FixedInterval(1000, min_content_words=1)
    assert p.propose(E.interim(500, "refund policy"), view("refund policy")) is None
    assert p.propose(E.interim(1000, "refund policy"), view("refund policy")) == "refund policy"
    v = view("refund policy damaged", last_fire=1000)
    assert p.propose(E.interim(1500, "refund policy damaged"), v) is None
    assert p.propose(E.interim(2000, "refund policy damaged"), v) == "refund policy damaged"


def test_fixed_interval_holdback_and_eager():
    p = FixedInterval(0, holdback=1, min_content_words=1)
    assert p.propose(E.interim(10, "refund policy damaged"), view("refund policy damaged")) == "refund policy"
    assert p.propose(E.eager_end_of_turn(10, "x y"), view()) == "x y"
    assert FixedInterval(0, fire_on_eager=False).propose(E.eager_end_of_turn(10, "x y"), view()) is None


def test_stable_prefix_requires_agreement():
    p = StablePrefix(agreement=2, min_content_words=1)
    ev = E.interim(200, "what did microsoft announce")
    # Only one hypothesis so far: nothing is stable yet.
    assert p.propose(ev, view("what did microsoft announce")) is None
    # The revised word ("my" -> "microsoft") is not trusted until both agree.
    assert p.propose(ev, view("what did my", "what did microsoft announce")) is None
    v = view("what did microsoft", "what did microsoft announce")
    assert p.propose(ev, v) == "what did microsoft"


def test_stable_prefix_needs_new_content_words():
    p = StablePrefix(agreement=1, min_content_words=1, min_new_content_words=1)
    ev = E.interim(100, "refund policy for")
    assert p.propose(ev, view("refund policy for", fired=("refund policy",))) is None
    ev2 = E.interim(200, "refund policy for damaged")
    assert (
        p.propose(ev2, view("refund policy for damaged", fired=("refund policy",)))
        == "refund policy for damaged"
    )


def test_stable_prefix_min_content_words_and_holdback():
    p = StablePrefix(agreement=1, min_content_words=2, holdback=1)
    assert p.propose(E.interim(1, "what is the refund"), view("what is the refund")) is None
    assert p.propose(E.interim(1, "refund policy damaged"), view("refund policy damaged")) == "refund policy"
    with pytest.raises(ValueError):
        StablePrefix(agreement=0)


def outcome(spec_calls: int, reused: bool, late: bool = False, lat: float = 200.0) -> TurnOutcome:
    return TurnOutcome(
        speculative_calls=spec_calls,
        cancelled_calls=0,
        reused=reused,
        late=late,
        wait_ms=0.0,
        fresh_call=not reused,
        call_latencies_ms=(lat,),
    )


def test_adaptive_backs_off_when_over_budget():
    p = Adaptive(budget=2.0, window=4, start_level=4)
    for _ in range(4):
        p.feedback(outcome(spec_calls=6, reused=True))
    assert p.level == 3


def test_adaptive_climbs_when_under_budget_and_missing():
    p = Adaptive(budget=4.0, window=4, start_level=1)
    for _ in range(4):
        p.feedback(outcome(spec_calls=1, reused=False))
    assert p.level == 2


def test_adaptive_turns_off_speculation_for_fast_retrievers():
    p = Adaptive(window=2, start_level=3, min_latency_ms=40)
    for _ in range(2):
        p.feedback(outcome(spec_calls=2, reused=True, lat=5.0))
    assert p.level == 0
    assert p.propose(E.interim(1, "refund policy damaged"), view("refund policy damaged")) is None
    assert p.propose(E.eager_end_of_turn(1, "refund policy"), view()) == "refund policy"


def test_adaptive_validation():
    with pytest.raises(ValueError):
        Adaptive(budget=0.5)
    with pytest.raises(ValueError):
        Adaptive(start_level=99)
