"""forehear in 60 seconds. No API keys, no audio, no dependencies.

A simulated user asks a question to a voice agent whose knowledge base takes
~400 ms per lookup. We replay the same interim transcripts twice: once with
retrieval after the user stops talking (today's default), once with forehear.

    python examples/quickstart.py
"""

from __future__ import annotations

import asyncio
import time

from forehear import BM25Index, FinalOnly, Lookahead, StablePrefix, with_latency

KB = BM25Index(
    [
        ("returns", "Damaged items can be returned within 30 days for a full refund or a replacement."),
        ("shipping", "Standard shipping takes 3 to 5 business days; express arrives next day."),
        ("warranty", "Electronics carry a one-year limited warranty covering manufacturing defects."),
        ("hours", "Our support line is open Monday to Friday, 9am to 6pm Eastern."),
    ]
)

# What a streaming speech-to-text service emits while the user talks
# (seconds since speech start, running hypothesis). Note the revision at 0.9 s.
INTERIMS = [
    (0.3, "can i"),
    (0.6, "can i return"),
    (0.9, "can i return a damn"),
    (1.2, "can i return a damaged"),
    (1.5, "can i return a damaged item"),
    (1.9, "can i return a damaged item for a refund"),
]
FINAL = "can i return a damaged item for a refund"
END_OF_TURN = 2.4  # turn detector fires ~500 ms after the last word


async def conversation(lookahead: Lookahead) -> tuple[float, str]:
    t0 = time.perf_counter()
    lookahead.speech_started()
    for at, text in INTERIMS:
        await asyncio.sleep(max(0.0, at - (time.perf_counter() - t0)))
        lookahead.interim(text)
    await asyncio.sleep(max(0.0, END_OF_TURN - (time.perf_counter() - t0)))
    delivery = await lookahead.end_of_turn(FINAL)
    await lookahead.aclose()
    return delivery.wait_ms, delivery.docs[0].id


async def main() -> None:
    slow_kb = with_latency(KB.search, 400)  # hosted vector DB + embedding call
    baseline = await conversation(Lookahead(slow_kb, FinalOnly()))
    ahead = Lookahead(slow_kb, StablePrefix(agreement=1))
    result = await conversation(ahead)
    for label, (wait, doc) in (("retrieve after end of turn", baseline), ("forehear look-ahead", result)):
        print(f"{label:<27}: context ready {wait:4.0f} ms after the user stopped ({doc})")
    print(f"speculative calls: {ahead.stats.speculative_calls}, reused: {ahead.stats.reused_turns} turn(s)")


if __name__ == "__main__":
    asyncio.run(main())
