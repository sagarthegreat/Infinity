"""Tests for the LiveKit Agents adapter using LiveKit's real event and chat types."""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("livekit.agents")

from livekit.agents import llm
from livekit.agents.voice.events import UserInputTranscribedEvent, UserStateChangedEvent

from forehear import BM25Index, Lookahead, StablePrefix
from forehear.integrations.livekit import LookaheadAgent, _Feed

INDEX = BM25Index(
    [
        ("refunds", "Refund policy: damaged items can be returned within 30 days for a full refund."),
        ("shipping", "Shipping takes 3 to 5 business days within the continental US."),
    ]
)


class FakeSession:
    def __init__(self) -> None:
        self.handlers: dict[str, list] = {}

    def on(self, name: str, fn) -> None:
        self.handlers.setdefault(name, []).append(fn)

    def emit(self, name: str, ev) -> None:
        for fn in self.handlers.get(name, []):
            fn(ev)


async def test_agent_injects_lookahead_context() -> None:
    calls: list[str] = []

    async def retrieve(q: str):
        calls.append(q)
        await asyncio.sleep(0.05)
        return INDEX.search(q, 1)

    from forehear.integrations.livekit import attach

    la = Lookahead(retrieve, StablePrefix(agreement=1))
    session = FakeSession()
    attach(session, la)  # type: ignore[arg-type]
    agent = LookaheadAgent(instructions="test", lookahead=la)

    session.emit("user_state_changed", UserStateChangedEvent(old_state="listening", new_state="speaking"))
    session.emit(
        "user_input_transcribed",
        UserInputTranscribedEvent(transcript="how long does shipping", is_final=False),
    )
    await asyncio.sleep(0.02)
    session.emit(
        "user_input_transcribed",
        UserInputTranscribedEvent(transcript="how long does shipping take", is_final=True),
    )
    await asyncio.sleep(0.15)

    ctx = llm.ChatContext.empty()
    msg = ctx.add_message(role="user", content="how long does shipping take")
    await agent.on_user_turn_completed(ctx, msg)

    texts = [m.text_content for m in ctx.items if isinstance(m, llm.ChatMessage)]
    assert any(t and "Shipping takes 3 to 5" in t for t in texts)
    assert la.stats.reused_turns == 1
    assert la.stats.fresh_calls == 0


def test_feed_accumulates_final_segments() -> None:
    seen: list[str] = []

    class Rec:
        controller = type("C", (), {"calls": []})()

        def speech_started(self) -> None:
            seen.append("<start>")

        def interim(self, text: str) -> None:
            seen.append(text)

    feed = _Feed(Rec())  # type: ignore[arg-type]
    feed.on_state(UserStateChangedEvent(old_state="listening", new_state="speaking"))
    feed.on_transcript(UserInputTranscribedEvent(transcript="hello there", is_final=True))
    feed.on_transcript(UserInputTranscribedEvent(transcript="how are", is_final=False))
    feed.on_state(UserStateChangedEvent(old_state="listening", new_state="speaking"))  # pause, same turn
    feed.on_transcript(UserInputTranscribedEvent(transcript="", is_final=False))
    assert seen == ["<start>", "hello there", "hello there how are"]
    feed.end_turn()
    feed.on_state(UserStateChangedEvent(old_state="listening", new_state="speaking"))
    assert seen[-1] == "<start>"
