"""End-to-end test of the Pipecat adapter with real Pipecat frames and pipeline."""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("pipecat")

from pipecat.frames.frames import (
    InterimTranscriptionFrame,
    LLMContextFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.tests.utils import SleepFrame, run_test

from forehear import BM25Index, Lookahead, StablePrefix
from forehear.integrations.pipecat import MARKER, lookahead_processors

INDEX = BM25Index(
    [
        ("refunds", "Refund policy: damaged items can be returned within 30 days for a full refund."),
        ("shipping", "Shipping takes 3 to 5 business days within the continental US."),
        ("hours", "Support is open Monday to Friday, 9am to 5pm."),
    ]
)


def _frames(final_text: str) -> list:
    ts = "2026-01-01T00:00:00Z"
    return [
        UserStartedSpeakingFrame(),
        InterimTranscriptionFrame(text="what is your refund", user_id="u", timestamp=ts),
        SleepFrame(sleep=0.05),
        InterimTranscriptionFrame(text="what is your refund policy for damaged", user_id="u", timestamp=ts),
        SleepFrame(sleep=0.05),
        InterimTranscriptionFrame(
            text="what is your refund policy for damaged items", user_id="u", timestamp=ts
        ),
        SleepFrame(sleep=0.3),
        TranscriptionFrame(text=final_text, user_id="u", timestamp=ts),
        LLMContextFrame(context=LLMContext(messages=[{"role": "user", "content": final_text}])),
    ]


async def test_context_is_injected_and_speculation_reused() -> None:
    calls: list[str] = []

    async def retrieve(query: str):
        calls.append(query)
        await asyncio.sleep(0.1)
        return INDEX.search(query, 2)

    deliveries = []
    la = Lookahead(retrieve, StablePrefix(agreement=1))
    tap, inject = lookahead_processors(la, on_delivery=deliveries.append)
    final = "what is your refund policy for damaged items"
    down, _ = await run_test(Pipeline([tap, inject]), frames_to_send=_frames(final))

    ctx_frames = [f for f in down if isinstance(f, LLMContextFrame)]
    assert len(ctx_frames) == 1
    messages = ctx_frames[0].context.get_messages()
    assert messages[-1] == {"role": "user", "content": final}
    injected = messages[-2]
    assert injected["role"] == "system"
    assert injected["content"].startswith(MARKER)
    assert "Refund policy" in injected["content"]
    # The answer was retrieved while the user was talking and reused at end of turn.
    assert deliveries and deliveries[0].reused
    assert deliveries[0].wait_ms < 50
    assert la.stats.fresh_calls == 0


async def test_old_injections_are_replaced() -> None:
    la = Lookahead(lambda q: INDEX.search(q, 1), StablePrefix(agreement=1))
    tap, inject = lookahead_processors(la)
    stale = {"role": "system", "content": f"{MARKER} stale passages"}
    ctx = LLMContext(
        messages=[stale, {"role": "assistant", "content": "hi"}, {"role": "user", "content": "shipping time"}]
    )
    down, _ = await run_test(
        Pipeline([tap, inject]),
        frames_to_send=[LLMContextFrame(context=ctx)],
    )
    messages = next(f for f in down if isinstance(f, LLMContextFrame)).context.get_messages()
    assert stale not in messages
    assert sum(1 for m in messages if str(m.get("content", "")).startswith(MARKER)) == 1
    assert "Shipping" in messages[-2]["content"]


async def test_pipecat_speculative_inference_reuses_context() -> None:
    """A speculative LLMContextFrame (Pipecat eager EOT) and the final one share one retrieval."""
    calls: list[str] = []

    async def retrieve(query: str):
        calls.append(query)
        return INDEX.search(query, 1)

    la = Lookahead(retrieve, StablePrefix())
    tap, inject = lookahead_processors(la)
    text = "how long does shipping take"
    ctx_spec = LLMContext(messages=[{"role": "user", "content": text}])
    ctx_final = LLMContext(messages=[{"role": "user", "content": text}])
    down, _ = await run_test(
        Pipeline([tap, inject]),
        frames_to_send=[
            LLMContextFrame(context=ctx_spec, speculation=True),
            SleepFrame(sleep=0.05),
            LLMContextFrame(context=ctx_final),
        ],
    )
    frames = [f for f in down if isinstance(f, LLMContextFrame)]
    assert [f.speculation for f in frames] == [True, False]
    for f in frames:
        assert "Shipping takes" in f.context.get_messages()[-2]["content"]
    assert calls == [text]  # one retrieval served both inferences
