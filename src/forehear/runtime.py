"""asyncio runtime: drives a :class:`Controller` with a real async retriever."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from .controller import Action, Cancel, Controller, ControllerStats, Deliver, Start
from .events import TranscriptEvent
from .policies import Policy
from .types import Delivery, Doc
from .validators import Validator

__all__ = ["Lookahead", "Retriever"]

log = logging.getLogger("forehear")

Retriever = Callable[[str], Awaitable[Sequence[Doc]]]
"""An async, **read-only** retrieval function: ``await retrieve(query) -> docs``."""


def _coerce_docs(result: Any) -> list[Doc]:
    docs: list[Doc] = []
    for i, item in enumerate(result or ()):
        if isinstance(item, Doc):
            docs.append(item)
        elif isinstance(item, str):
            docs.append(Doc(id=str(i), text=item))
        elif isinstance(item, dict):
            docs.append(
                Doc(
                    id=str(item.get("id", i)),
                    text=str(item.get("text", "")),
                    score=float(item.get("score", 0.0)),
                )
            )
        else:
            docs.append(Doc(id=str(getattr(item, "id", i)), text=str(getattr(item, "text", item))))
    return docs


class Lookahead:
    """Look-ahead retrieval for one conversation.

    Feed it transcript signals as they arrive; await :meth:`end_of_turn` to get
    the context for the LLM. Speculative calls run as asyncio tasks and are
    cancelled as soon as they are superseded.

    Example::

        la = Lookahead(retrieve=my_kb_search)        # async def my_kb_search(q) -> list[Doc]
        la.speech_started()
        la.interim("what's your refund")
        la.interim("what's your refund policy for")
        delivery = await la.end_of_turn("what's your refund policy for damaged items")
        prompt_context = "\\n".join(d.text for d in delivery.docs)

    Args:
        retrieve: Async read-only retrieval function. Sync functions are run in
            a worker thread.
        policy, validator, max_inflight, max_speculative_calls, hedge, when_full: see
            :class:`~forehear.controller.Controller`.
        clock: Returns the current time in milliseconds. Defaults to the
            event loop's monotonic clock.
    """

    def __init__(
        self,
        retrieve: Retriever | Callable[[str], Sequence[Doc]],
        policy: Policy | None = None,
        validator: Validator | None = None,
        *,
        max_inflight: int = 2,
        max_speculative_calls: int | None = None,
        hedge: bool = False,
        when_full: str = "cancel_oldest",
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.controller = Controller(
            policy,
            validator,
            max_inflight=max_inflight,
            max_speculative_calls=max_speculative_calls,
            hedge=hedge,
            when_full=when_full,
        )
        self._retrieve = retrieve
        self._is_async = inspect.iscoroutinefunction(retrieve) or inspect.iscoroutinefunction(
            type(retrieve).__call__
        )
        self._clock = clock
        self._tasks: dict[int, asyncio.Task[None]] = {}
        self._waiters: list[asyncio.Future[Delivery]] = []
        self._deliveries: list[Delivery] = []

    # ---------------------------------------------------------------- signals

    def now(self) -> float:
        if self._clock is not None:
            return self._clock()
        return asyncio.get_running_loop().time() * 1000.0

    def speech_started(self) -> None:
        self.push(TranscriptEvent.speech_start(self.now()))

    def interim(self, text: str) -> None:
        self.push(TranscriptEvent.interim(self.now(), text))

    def eager_end_of_turn(self, text: str) -> None:
        self.push(TranscriptEvent.eager_end_of_turn(self.now(), text))

    def turn_resumed(self) -> None:
        self.push(TranscriptEvent.turn_resumed(self.now()))

    async def end_of_turn(self, text: str, *, timeout: float | None = None) -> Delivery:
        """Signal the final transcript and wait for the turn's context.

        Raises:
            TimeoutError: if ``timeout`` seconds pass without a delivery.
        """
        fut: asyncio.Future[Delivery] = asyncio.get_running_loop().create_future()
        self._waiters.append(fut)
        self.push(TranscriptEvent.end_of_turn(self.now(), text))
        try:
            if timeout is None:
                return await fut
            try:
                return await asyncio.wait_for(fut, timeout)
            except asyncio.TimeoutError as exc:  # distinct from TimeoutError before 3.11
                raise TimeoutError(f"no context within {timeout}s") from exc
        finally:
            if fut in self._waiters:
                self._waiters.remove(fut)

    def push(self, event: TranscriptEvent) -> None:
        """Feed a raw :class:`TranscriptEvent` (must be called on the event loop)."""
        self._run(self.controller.handle(event))

    @property
    def stats(self) -> ControllerStats:
        return self.controller.stats

    async def aclose(self) -> None:
        """Cancel all in-flight calls."""
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

    # -------------------------------------------------------------- internals

    def _run(self, actions: list[Action]) -> None:
        for action in actions:
            if isinstance(action, Start):
                spec = action.spec
                self._tasks[spec.id] = asyncio.create_task(self._call(spec.id, spec.query))
            elif isinstance(action, Cancel):
                task = self._tasks.pop(action.spec_id, None)
                if task is not None and not task.done():
                    task.cancel()
            elif isinstance(action, Deliver):
                self._deliver(action.delivery)

    def _deliver(self, delivery: Delivery) -> None:
        while self._waiters:
            fut = self._waiters.pop(0)
            if not fut.done():
                fut.set_result(delivery)
                return
        self._deliveries.append(delivery)

    async def _call(self, spec_id: int, query: str) -> None:
        try:
            if self._is_async:
                result = await self._retrieve(query)  # type: ignore[misc]
            else:
                result = await asyncio.to_thread(self._retrieve, query)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("forehear: retrieval failed for %r", query)
            self._tasks.pop(spec_id, None)
            self._run(self.controller.on_error(spec_id, self.now()))
            return
        self._tasks.pop(spec_id, None)
        self._run(self.controller.on_result(spec_id, _coerce_docs(result), self.now()))
