"""Transcript events: the only input forehear needs from a voice pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["EventKind", "TranscriptEvent"]


class EventKind(str, Enum):
    """What happened in the user's turn.

    These map one-to-one onto signals every streaming speech stack exposes:

    ``SPEECH_START``
        Voice activity began (a new user turn).
    ``INTERIM``
        A new interim/partial ASR hypothesis for the *whole* turn so far.
        Interim text may revise earlier words; it is not append-only.
    ``EAGER_END_OF_TURN``
        An early, lower-confidence end-of-turn prediction (Deepgram Flux
        ``EagerEndOfTurn``, LiveKit "preflight" transcripts, Pipecat eager
        turn strategies).
    ``TURN_RESUMED``
        The user kept talking after an eager end-of-turn.
    ``END_OF_TURN``
        The turn is over and ``text`` is the final transcript. Context must be
        delivered now.
    """

    SPEECH_START = "speech_start"
    INTERIM = "interim"
    EAGER_END_OF_TURN = "eager_end_of_turn"
    TURN_RESUMED = "turn_resumed"
    END_OF_TURN = "end_of_turn"


@dataclass(frozen=True, slots=True)
class TranscriptEvent:
    """A timestamped transcript event.

    ``t_ms`` is any monotonic clock in milliseconds. The controller only ever
    compares timestamps with each other, so wall-clock, audio-clock and
    simulated time all work.
    """

    kind: EventKind
    t_ms: float
    text: str = ""

    @classmethod
    def speech_start(cls, t_ms: float) -> TranscriptEvent:
        return cls(EventKind.SPEECH_START, t_ms)

    @classmethod
    def interim(cls, t_ms: float, text: str) -> TranscriptEvent:
        return cls(EventKind.INTERIM, t_ms, text)

    @classmethod
    def eager_end_of_turn(cls, t_ms: float, text: str) -> TranscriptEvent:
        return cls(EventKind.EAGER_END_OF_TURN, t_ms, text)

    @classmethod
    def turn_resumed(cls, t_ms: float) -> TranscriptEvent:
        return cls(EventKind.TURN_RESUMED, t_ms)

    @classmethod
    def end_of_turn(cls, t_ms: float, text: str) -> TranscriptEvent:
        return cls(EventKind.END_OF_TURN, t_ms, text)
