"""LiveKit Agents integration.

LiveKit's ``preemptive_generation`` starts the *LLM* early, but retrieval done
in ``on_user_turn_completed`` still runs after the user stops talking (and
editing the chat context there discards the preemptive reply). forehear moves
the retrieval itself into the user's speech.

Example::

    from forehear import Lookahead
    from forehear.integrations.livekit import LookaheadAgent, attach

    class Assistant(LookaheadAgent):
        def __init__(self) -> None:
            super().__init__(
                instructions="You are a helpful support agent.",
                lookahead=Lookahead(retrieve=kb_search),   # async, read-only
            )

    async def entrypoint(ctx: JobContext) -> None:
        session = AgentSession(stt=..., llm=..., tts=..., vad=...)
        agent = Assistant()
        attach(session, agent.lookahead)      # feed interim transcripts
        await session.start(agent=agent, room=ctx.room)

``attach`` subscribes to ``user_state_changed`` and ``user_input_transcribed``;
``LookaheadAgent.on_user_turn_completed`` awaits the turn's context and adds it
to the turn's chat context.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from livekit.agents import Agent, AgentSession, llm

from ..runtime import Lookahead
from ..types import Delivery, Doc

__all__ = ["LookaheadAgent", "attach", "default_formatter"]


def default_formatter(docs: Sequence[Doc]) -> str:
    if not docs:
        return "No relevant passages were found for the user's message."
    body = "\n\n".join(f"[{i + 1}] {d.text}" for i, d in enumerate(docs))
    return f"Passages that may help answer the user's message:\n\n{body}"


class _Feed:
    def __init__(self, lookahead: Lookahead) -> None:
        self.lookahead = lookahead
        self.finals: list[str] = []
        self.in_turn = False

    def on_state(self, ev: Any) -> None:
        if getattr(ev, "new_state", None) == "speaking" and not self.in_turn:
            self.in_turn = True
            self.finals.clear()
            self.lookahead.speech_started()

    def on_transcript(self, ev: Any) -> None:
        text = str(getattr(ev, "transcript", "") or "").strip()
        if not text:
            return
        if getattr(ev, "is_final", False):
            self.finals.append(text)
            self.lookahead.interim(" ".join(self.finals))
        else:
            self.lookahead.interim(" ".join([*self.finals, text]))

    def end_turn(self) -> None:
        self.finals.clear()
        self.in_turn = False


def attach(session: AgentSession, lookahead: Lookahead) -> _Feed:
    """Feed a session's user transcripts and speaking state into ``lookahead``."""
    feed = _Feed(lookahead)
    session.on("user_state_changed", feed.on_state)
    session.on("user_input_transcribed", feed.on_transcript)
    lookahead._livekit_feed = feed  # type: ignore[attr-defined]
    return feed


class LookaheadAgent(Agent):  # type: ignore[misc]
    """An ``Agent`` that adds look-ahead-retrieved context to every user turn.

    Args:
        lookahead: The :class:`Lookahead` (call :func:`attach` with it too).
        formatter: Turns documents into the injected message.
        role: Role of the injected message (LiveKit's RAG examples use ``"assistant"``).
        timeout: Seconds to wait for retrieval.
        on_delivery: Optional callback for metrics/logging.
        **kwargs: Passed to ``Agent``.
    """

    def __init__(
        self,
        *,
        lookahead: Lookahead,
        formatter: Callable[[Sequence[Doc]], str] = default_formatter,
        role: str = "assistant",
        timeout: float | None = 5.0,
        on_delivery: Callable[[Delivery], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.lookahead = lookahead
        self.formatter = formatter
        self.context_role = role
        self.timeout = timeout
        self.on_delivery = on_delivery

    async def on_user_turn_completed(self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage) -> None:
        text = new_message.text_content or ""
        try:
            delivery = await self.lookahead.end_of_turn(text, timeout=self.timeout)
        except TimeoutError:
            return
        finally:
            feed = getattr(self.lookahead, "_livekit_feed", None)
            if feed is not None:
                feed.end_turn()
        if self.on_delivery:
            self.on_delivery(delivery)
        turn_ctx.add_message(role=self.context_role, content=self.formatter(delivery.docs))
