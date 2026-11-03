from __future__ import annotations

import pytest

from forehear import (
    Cancel,
    Controller,
    Deliver,
    Doc,
    EagerEndOfTurn,
    ExactMatch,
    FinalOnly,
    StablePrefix,
    Start,
    TokenCoverage,
    TranscriptEvent,
)

E = TranscriptEvent
DOCS = (Doc("d1", "text"),)


def starts(actions):
    return [a.spec for a in actions if isinstance(a, Start)]


def cancels(actions):
    return [a.spec_id for a in actions if isinstance(a, Cancel)]


def delivery(actions):
    found = [a.delivery for a in actions if isinstance(a, Deliver)]
    return found[0] if found else None


def eager_controller(**kw):
    return Controller(StablePrefix(agreement=1, min_content_words=1), TokenCoverage(0.8), **kw)


def test_final_only_retrieves_after_end_of_turn():
    c = Controller(FinalOnly())
    assert c.handle(E.speech_start(0)) == []
    assert c.handle(E.interim(100, "who founded red bull")) == []
    actions = c.handle(E.end_of_turn(1000, "who founded red bull"))
    (spec,) = starts(actions)
    assert not spec.speculative and spec.query == "who founded red bull"
    assert delivery(actions) is None and c.awaiting_delivery
    d = delivery(c.on_result(spec.id, DOCS, 1250))
    assert d is not None and not d.reused and d.wait_ms == 250
    assert c.stats.turns == 1 and c.stats.fresh_calls == 1 and c.stats.speculative_calls == 0


def test_completed_speculation_is_reused_with_zero_wait():
    c = eager_controller()
    c.handle(E.speech_start(0))
    (spec,) = starts(c.handle(E.interim(100, "who founded red bull")))
    assert spec.speculative
    assert c.on_result(spec.id, DOCS, 300) == []  # not awaited yet
    d = delivery(c.handle(E.end_of_turn(800, "who founded red bull")))
    assert d is not None and d.reused and d.wait_ms == 0 and d.docs == DOCS
    assert c.last_outcome is not None and c.last_outcome.reused and not c.last_outcome.late
    assert c.stats.coverage == 1.0 and c.stats.accuracy == 1.0


def test_pending_accepted_speculation_is_awaited_and_marked_late():
    c = eager_controller()
    (spec,) = starts(c.handle(E.interim(100, "who founded red bull")))
    actions = c.handle(E.end_of_turn(800, "who founded red bull"))
    assert starts(actions) == [] and delivery(actions) is None
    d = delivery(c.on_result(spec.id, DOCS, 900))
    assert d is not None and d.reused and d.wait_ms == 100
    assert c.last_outcome is not None and c.last_outcome.late
    assert c.stats.late_turns == 1


def test_rejected_speculation_falls_back_and_cancels_pending():
    c = eager_controller()
    (spec,) = starts(c.handle(E.interim(100, "who founded rare")))
    actions = c.handle(E.end_of_turn(800, "who founded red bull"))
    assert cancels(actions) == [spec.id]
    (fresh,) = starts(actions)
    assert not fresh.speculative
    assert c.on_result(spec.id, DOCS, 850) == []  # stale result is ignored
    d = delivery(c.on_result(fresh.id, DOCS, 1000))
    assert d is not None and not d.reused and d.wait_ms == 200


def test_completed_but_rejected_result_is_not_used():
    c = eager_controller()
    (spec,) = starts(c.handle(E.interim(100, "capital of germany")))
    c.on_result(spec.id, DOCS, 200)
    actions = c.handle(E.end_of_turn(800, "capital of france"))
    (fresh,) = starts(actions)
    assert fresh.query == "capital of france"


def test_best_scoring_candidate_wins():
    c = Controller(StablePrefix(agreement=1, min_content_words=1), TokenCoverage(0.5))
    a = starts(c.handle(E.interim(100, "refund policy")))[0]
    b = starts(c.handle(E.interim(200, "refund policy damaged items")))[0]
    c.on_result(a.id, (Doc("a"),), 300)
    c.on_result(b.id, (Doc("b"),), 300)
    d = delivery(c.handle(E.end_of_turn(900, "refund policy damaged items")))
    assert d is not None and d.spec_id == b.id


def test_max_inflight_cancels_oldest():
    c = eager_controller(max_inflight=2)
    s1 = starts(c.handle(E.interim(100, "alpha")))[0]
    s2 = starts(c.handle(E.interim(200, "alpha beta")))[0]
    actions = c.handle(E.interim(300, "alpha beta gamma"))
    assert cancels(actions) == [s1.id]
    assert starts(actions)[0].query == "alpha beta gamma"
    assert s2.pending


def test_when_full_drop_new_keeps_running_calls():
    c = eager_controller(max_inflight=1, when_full="drop_new")
    starts(c.handle(E.interim(100, "alpha")))
    assert c.handle(E.interim(200, "alpha beta")) == []


def test_duplicate_queries_are_not_reissued():
    c = Controller(EagerEndOfTurn())
    c.handle(E.speech_start(0))
    assert len(starts(c.handle(E.eager_end_of_turn(500, "Hello, World!")))) == 1
    c.handle(E.turn_resumed(600))
    assert starts(c.handle(E.eager_end_of_turn(900, "hello world"))) == []


def test_speculative_budget():
    c = eager_controller(max_speculative_calls=2)
    assert starts(c.handle(E.interim(1, "one")))
    assert starts(c.handle(E.interim(2, "one two")))
    assert not starts(c.handle(E.interim(3, "one two three")))


def test_hedge_delivers_first_and_cancels_other():
    c = eager_controller(hedge=True)
    (spec,) = starts(c.handle(E.interim(100, "who founded red bull")))
    actions = c.handle(E.end_of_turn(800, "who founded red bull"))
    (fresh,) = starts(actions)
    actions = c.on_result(fresh.id, DOCS, 900)
    assert cancels(actions) == [spec.id]
    d = delivery(actions)
    assert d is not None and not d.reused and d.spec_id == fresh.id


def test_failed_speculation_falls_back_to_fresh_call():
    c = eager_controller()
    (spec,) = starts(c.handle(E.interim(100, "who founded red bull")))
    c.handle(E.end_of_turn(800, "who founded red bull"))
    (fresh,) = starts(c.on_error(spec.id, 850))
    assert not fresh.speculative
    d = delivery(c.on_result(fresh.id, DOCS, 900))
    assert d is not None and not d.failed


def test_failed_fresh_call_delivers_failure():
    c = Controller(FinalOnly())
    (fresh,) = starts(c.handle(E.end_of_turn(800, "anything")))
    d = delivery(c.on_error(fresh.id, 900))
    assert d is not None and d.failed and d.docs == ()


def test_empty_final_transcript_delivers_immediately():
    c = eager_controller()
    (spec,) = starts(c.handle(E.interim(100, "hello")))
    actions = c.handle(E.end_of_turn(500, "  "))
    assert cancels(actions) == [spec.id]
    d = delivery(actions)
    assert d is not None and d.docs == () and d.wait_ms == 0


def test_events_during_delivery_wait_are_replayed():
    c = eager_controller()
    (fresh,) = starts(c.handle(E.end_of_turn(100, "first question")))
    assert c.handle(E.speech_start(150)) == []
    assert c.handle(E.interim(200, "second question")) == []
    actions = c.on_result(fresh.id, DOCS, 300)
    assert delivery(actions) is not None
    assert [s.query for s in starts(actions)] == ["second question"]


def test_turn_starts_implicitly_without_speech_start():
    c = eager_controller()
    assert starts(c.handle(E.interim(100, "refund policy")))
    assert c.calls


def test_repeated_identical_interims_are_ignored():
    c = eager_controller()
    assert starts(c.handle(E.interim(100, "refund policy")))
    assert c.handle(E.interim(200, "Refund policy!")) == []


def test_validation():
    with pytest.raises(ValueError):
        Controller(max_inflight=0)
    with pytest.raises(ValueError):
        Controller(when_full="nope")


def test_exact_match_validator_rejects_paraphrase():
    c = Controller(StablePrefix(agreement=1, min_content_words=1), ExactMatch())
    (spec,) = starts(c.handle(E.interim(100, "refund policy damaged")))
    c.on_result(spec.id, DOCS, 200)
    assert starts(c.handle(E.end_of_turn(900, "refund policy damaged items")))


def test_stats_accumulate_across_turns():
    c = eager_controller()
    for turn in range(3):
        t = turn * 10_000
        c.handle(E.speech_start(t))
        (spec,) = starts(c.handle(E.interim(t + 100, f"question number {turn}")))
        c.on_result(spec.id, DOCS, t + 200)
        assert delivery(c.handle(E.end_of_turn(t + 900, f"question number {turn}")))
    assert c.stats.turns == 3 and c.stats.reused_turns == 3
    assert c.stats.calls_per_turn == 1.0 and c.stats.mean_wait_ms == 0.0
