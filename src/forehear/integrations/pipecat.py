"""Pipecat integration.

Two processors share one :class:`~forehear.Lookahead`:

* :class:`TranscriptTap` goes right after your STT service. It watches
  interim, final and eager transcription frames and turn boundaries, and feeds
  them to forehear. It never modifies or drops frames.
* :class:`ContextInjector` goes right after the user context aggregator, in
  front of the LLM. When an ``LLMContextFrame`` arrives it awaits the turn's
  context (usually already retrieved while the user was speaking), inserts it
  into the LLM context and lets the frame continue.

Example::

    from forehear import Lookahead
    from forehear.integrations.pipecat import lookahead_processors

    lookahead = Lookahead(retrieve=my_async_search)   # read-only!
    tap, inject = lookahead_processors(lookahead)

    pipeline = Pipeline([
        transport.input(), stt, tap,
        context_aggregator.user(), inject, llm, tts,
        transport.output(), context_aggregator.assistant(),
    ])

Pipecat's own speculative inference (``enable_eager_end_of_turn``) is
supported: a speculative ``LLMContextFrame`` gets the context retrieved for
the eager transcript, and if the final transcript matches, the same documents
are reused without another retrieval call.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from pipecat.frames.frames import (
    EagerTranscriptionFrame,
    Frame,
    InterimTranscriptionFrame,
    LLMContextFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserTurnResponseCancelFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from ..runtime import Lookahead
from ..text import normalize
from ..types import Delivery, Doc

__all__ = ["ContextInjector", "TranscriptTap", "default_formatter", "lookahead_processors"]

MARKER = "[forehear context]"


def default_formatter(docs: Sequence[Doc]) -> str:
    """Format retrieved passages for the LLM."""
    if not docs:
        return f"{MARKER} No relevant passages were found for the user's next message."
    body = "\n\n".join(f"[{i + 1}] {d.text}" for i, d in enumerate(docs))
    return f"{MARKER} Passages that may help answer the user's next message:\n\n{body}"


class _TurnText:
    """Builds the running turn hypothesis from Pipecat's per-segment frames."""

    def __init__(self) -> None:
        self.finals: list[str] = []
        self.interim = ""

    def reset(self) -> None:
        self.finals.clear()
        self.interim = ""

    def text(self) -> str:
        return " ".join([*self.finals, self.interim]).strip()


class TranscriptTap(FrameProcessor):  # type: ignore[misc]
    """Feeds transcription frames to a :class:`Lookahead`. Place after the STT service."""

    def __init__(self, lookahead: Lookahead, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.lookahead = lookahead
        self._turn = _TurnText()
        self._in_turn = False

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        la = self.lookahead
        if isinstance(frame, UserStartedSpeakingFrame):
            # Pipecat may signal several speech starts in one turn (pauses);
            # only the first one after a delivered turn starts a new turn.
            if not self._in_turn:
                self._in_turn = True
                self._turn.reset()
                la.speech_started()
        elif isinstance(frame, InterimTranscriptionFrame):
            self._turn.interim = frame.text
            la.interim(self._turn.text())
        elif isinstance(frame, TranscriptionFrame):
            self._turn.finals.append(frame.text)
            self._turn.interim = ""
            la.interim(self._turn.text())
        elif isinstance(frame, EagerTranscriptionFrame):
            la.eager_end_of_turn(" ".join([*self._turn.finals, frame.text]).strip())
        elif isinstance(frame, UserTurnResponseCancelFrame):
            la.turn_resumed()
        await self.push_frame(frame, direction)

    def end_turn(self) -> None:
        self._turn.reset()
        self._in_turn = False


def _message_text(message: Any) -> str:
    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
            elif isinstance(part, str):
                parts.append(part)
        return " ".join(parts)
    return ""


def _role(message: Any) -> str:
    return str(message.get("role", "")) if isinstance(message, dict) else str(getattr(message, "role", ""))


class ContextInjector(FrameProcessor):  # type: ignore[misc]
    """Inserts the turn's retrieved context into ``LLMContextFrame``s. Place before the LLM.

    Args:
        lookahead: The shared :class:`Lookahead`.
        tap: The :class:`TranscriptTap` feeding it (reset at each turn end).
        formatter: Turns documents into message text.
        role: Role of the injected message (``"system"`` by default).
        timeout: Seconds to wait for retrieval before sending the LLM nothing.
        on_delivery: Optional callback for metrics/logging.
    """

    def __init__(
        self,
        lookahead: Lookahead,
        tap: TranscriptTap | None = None,
        *,
        formatter: Callable[[Sequence[Doc]], str] = default_formatter,
        role: str = "system",
        timeout: float | None = 5.0,
        on_delivery: Callable[[Delivery], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.lookahead = lookahead
        self.tap = tap
        self.formatter = formatter
        self.role = role
        self.timeout = timeout
        self.on_delivery = on_delivery
        self._speculative: tuple[str, Delivery] | None = None

    async def _docs_for(self, text: str, speculation: bool) -> Sequence[Doc]:
        key = normalize(text)
        if self._speculative and self._speculative[0] == key:
            delivery = self._speculative[1]
            if not speculation:
                self._speculative = None
            return delivery.docs
        delivery = await self.lookahead.end_of_turn(text, timeout=self.timeout)
        if self.on_delivery:
            self.on_delivery(delivery)
        if speculation:
            self._speculative = (key, delivery)
        else:
            self._speculative = None
            if self.tap:
                self.tap.end_turn()
        return delivery.docs

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, LLMContextFrame) and direction == FrameDirection.DOWNSTREAM:
            await self._inject(frame)
        await self.push_frame(frame, direction)

    async def _inject(self, frame: LLMContextFrame) -> None:
        messages = [m for m in frame.context.get_messages() if not _message_text(m).startswith(MARKER)]
        last_user = next((i for i in range(len(messages) - 1, -1, -1) if _role(messages[i]) == "user"), None)
        if last_user is None:
            frame.context.set_messages(messages)
            return
        text = _message_text(messages[last_user])
        try:
            docs = await self._docs_for(text, bool(getattr(frame, "speculation", False)))
        except TimeoutError:
            docs = ()
        messages.insert(last_user, {"role": self.role, "content": self.formatter(docs)})
        frame.context.set_messages(messages)


def lookahead_processors(
    lookahead: Lookahead, **injector_kwargs: Any
) -> tuple[TranscriptTap, ContextInjector]:
    """Create a connected ``(TranscriptTap, ContextInjector)`` pair."""
    tap = TranscriptTap(lookahead)
    return tap, ContextInjector(lookahead, tap, **injector_kwargs)
