from __future__ import annotations

import asyncio

import pytest

from forehear import BM25Index, Doc, ExactMatch, ResultOverlap, TokenCoverage, with_latency
from forehear.text import content_words, drop_last, normalize, words


def test_text_helpers():
    assert normalize("  What's   the capital of France? ") == "what's the capital of france"
    assert words("Red-Bull 2024!") == ["red", "bull", "2024"]
    assert content_words("what is the capital of france") == ["capital", "france"]
    assert drop_last("who founded red bull", 1) == "who founded red"
    assert drop_last("who", 5) == ""
    assert drop_last("Who Founded", 0) == "who founded"


def test_exact_match():
    v = ExactMatch()
    assert v.accepts("Who founded Red Bull?", "who founded red bull")
    assert not v.accepts("who founded red", "who founded red bull")


def test_token_coverage_scores():
    v = TokenCoverage(0.8)
    assert v.score("capital of france", "what is the capital of france") == 1.0
    assert v.score("capital", "capital of france") == 0.5  # truncated guess
    assert v.score("red bull founder", "who founded rare") == 0.0  # revised words
    assert v.accepts("refund policy damaged items", "what is the refund policy for damaged items")
    assert not v.accepts("refund policy", "what is the refund policy for damaged items")
    # all-stopword queries fall back to exact match
    assert v.score("what is it", "what is it") == 1.0
    assert v.score("what is it", "what was it") == 0.0
    with pytest.raises(ValueError):
        TokenCoverage(1.5)


def test_result_overlap_uses_probe():
    index = BM25Index(
        [("a", "red bull energy drink"), ("b", "bull fighting in spain"), ("c", "paris france")]
    )
    calls: list[str] = []

    def probe(q: str) -> list[str]:
        calls.append(q)
        return index.ids(q, 1)

    v = ResultOverlap(probe, k=1, threshold=1.0)
    assert v.accepts("red bull energy", "red bull energy drink")
    assert not v.accepts("paris", "red bull energy drink")
    assert v.score("same", "same") == 1.0
    n = len(calls)
    v.score("red bull energy", "red bull energy drink")
    assert len(calls) == n  # cached


def test_bm25_ranks_relevant_docs_first():
    idx = BM25Index(
        [
            Doc("refund", "Refunds: damaged items may be returned within 30 days."),
            Doc("ship", "Shipping takes 3 to 5 business days."),
            ("hours", "We are open Monday to Friday."),
        ]
    )
    assert len(idx) == 3
    assert idx.search("can I return a damaged item", 1)[0].id == "refund"
    assert idx.ids("how many days does shipping take", 1) == ["ship"]
    assert idx.search("zebra", 3) == []
    top = idx.search("days", 3)
    assert {d.id for d in top} == {"refund", "ship"} and top[0].score >= top[1].score


async def test_with_latency_wraps_sync_search():
    idx = BM25Index([("a", "red bull")])
    retrieve = with_latency(idx.search, 10)
    t0 = asyncio.get_running_loop().time()
    docs = await retrieve("red bull")
    assert docs[0].id == "a"
    assert asyncio.get_running_loop().time() - t0 >= 0.009
    retrieve2 = with_latency(idx.search, lambda q: 1.0)
    assert (await retrieve2("red"))[0].id == "a"


def test_dense_index_with_toy_encoder():
    np = pytest.importorskip("numpy")
    vocab = ["red", "bull", "paris", "france", "refund"]

    def encode(texts):
        return np.array([[t.lower().count(w) for w in vocab] for t in texts], dtype=float)

    from forehear import DenseIndex

    idx = DenseIndex(
        [("rb", "Red Bull red bull"), ("fr", "Paris France"), ("rf", "refund")], encode, batch_size=2
    )
    assert len(idx) == 3
    assert idx.ids("who founded red bull", 1) == ["rb"]
    assert idx.search("paris", 2)[0].id == "fr"
    assert idx.search("   ", 2) == []
