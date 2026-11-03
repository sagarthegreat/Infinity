"""Core value types."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

__all__ = ["Delivery", "Doc", "SpecStatus", "Speculation", "TurnOutcome"]

_EMPTY: Mapping[str, Any] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class Doc:
    """A retrieved passage. Only ``id`` is required; forehear never inspects text."""

    id: str
    text: str = ""
    score: float = 0.0
    meta: Mapping[str, Any] = field(default=_EMPTY, compare=False, repr=False)


class SpecStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(slots=True)
class Speculation:
    """One retrieval call issued by the controller.

    ``speculative`` is False for the fallback call made on the final transcript.
    """

    id: int
    query: str
    issued_ms: float
    speculative: bool
    trigger: str = ""
    status: SpecStatus = SpecStatus.PENDING
    docs: Sequence[Doc] = ()
    done_ms: float | None = None

    @property
    def pending(self) -> bool:
        return self.status is SpecStatus.PENDING


@dataclass(frozen=True, slots=True)
class Delivery:
    """Context handed to the LLM at end of turn.

    Attributes:
        docs: The retrieved passages.
        query: The query that produced ``docs``.
        final_query: The final transcript.
        reused: True if ``docs`` came from a speculative call.
        eot_ms: When the end of turn was signalled.
        delivered_ms: When the docs were available. ``delivered_ms - eot_ms`` is
            the latency retrieval added to the turn.
        spec_id: Id of the call that produced ``docs``.
    """

    docs: Sequence[Doc]
    query: str
    final_query: str
    reused: bool
    eot_ms: float
    delivered_ms: float
    spec_id: int
    failed: bool = False
    """True if retrieval on the final transcript failed; ``docs`` is empty."""

    @property
    def wait_ms(self) -> float:
        return max(0.0, self.delivered_ms - self.eot_ms)


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    """Bookkeeping for one finished turn, fed back to adaptive policies."""

    speculative_calls: int
    cancelled_calls: int
    reused: bool
    late: bool
    """The reused call was still in flight at end of turn."""
    wait_ms: float
    fresh_call: bool
    """A non-speculative call was made on the final transcript."""
    call_latencies_ms: tuple[float, ...] = ()
    """Latencies of the calls that completed this turn."""
