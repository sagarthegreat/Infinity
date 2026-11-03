from __future__ import annotations

import asyncio

from forehear import Doc, FinalOnly, Lookahead, StablePrefix


class FakeKB:
    def __init__(self, delay: float = 0.05) -> None:
        self.delay = delay
        self.started: list[str] = []
        self.cancelled: list[str] = []
        self.finished: list[str] = []

    async def __call__(self, query: str) -> list[Doc]:
        self.started.append(query)
        try:
            await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            self.cancelled.append(query)
            raise
        self.finished.append(query)
        return [Doc(id=query, text=f"about {query}")]


async def test_speculation_ready_before_end_of_turn():
    kb = FakeKB(0.05)
    la = Lookahead(kb, StablePrefix(agreement=1, min_content_words=1))
    la.speech_started()
    la.interim("refund policy damaged items")
    await asyncio.sleep(0.1)
    d = await la.end_of_turn("refund policy for damaged items")
    assert d.reused and d.wait_ms < 5
    assert d.docs[0].id == "refund policy damaged items"
    assert la.stats.fresh_calls == 0


async def test_superseded_calls_are_cancelled():
    kb = FakeKB(0.2)
    la = Lookahead(kb, StablePrefix(agreement=1, min_content_words=1), max_inflight=1)
    la.interim("alpha")
    la.interim("alpha beta")
    await asyncio.sleep(0)  # let tasks start
    la.interim("alpha beta gamma")
    await asyncio.sleep(0.01)
    # "alpha" is cancelled before its task even starts; "alpha beta" mid-flight.
    assert "alpha beta" in kb.cancelled
    assert "alpha" not in kb.finished and "alpha beta" not in kb.finished
    d = await la.end_of_turn("alpha beta gamma")
    assert d.reused and d.query == "alpha beta gamma"
    await la.aclose()


async def test_final_only_waits_for_fresh_call():
    kb = FakeKB(0.03)
    la = Lookahead(kb, FinalOnly())
    la.interim("anything")
    d = await la.end_of_turn("anything")
    assert not d.reused and d.wait_ms >= 25


async def test_sync_retriever_and_dict_results():
    def search(q: str):
        return [{"id": "x", "text": q, "score": 1.0}, "plain string"]

    la = Lookahead(search, FinalOnly())
    d = await la.end_of_turn("hello")
    assert [doc.id for doc in d.docs] == ["x", "1"]
    assert d.docs[1].text == "plain string"


async def test_retrieval_error_falls_back():
    attempts: list[str] = []

    async def flaky(q: str):
        attempts.append(q)
        if len(attempts) == 1:
            raise RuntimeError("boom")
        return [Doc("ok")]

    la = Lookahead(flaky, StablePrefix(agreement=1, min_content_words=1))
    la.interim("refund policy")
    await asyncio.sleep(0.01)
    d = await la.end_of_turn("refund policy")
    assert d.docs[0].id == "ok" and not d.reused and not d.failed


async def test_injected_clock():
    now = [0.0]
    la = Lookahead(FakeKB(0.0), FinalOnly(), clock=lambda: now[0])
    now[0] = 1234.0
    d = await la.end_of_turn("q")
    assert d.eot_ms == 1234.0


async def test_timeout():
    la = Lookahead(FakeKB(1.0), FinalOnly())
    try:
        await la.end_of_turn("slow", timeout=0.01)
    except TimeoutError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected timeout")
    await la.aclose()
