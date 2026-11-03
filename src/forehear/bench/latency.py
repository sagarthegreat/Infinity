"""Retrieval latency profiles.

Each profile is a log-normal distribution fitted to a median and a p95. The
values come from published measurements and vendor documentation collected in
``docs/research/``; they are meant to be representative, not exact. Pass your
own with ``LatencyProfile(name, median_ms, p95_ms)`` or measure your stack and
replay it.

Sampling is *keyed*: the latency of a call depends only on ``(seed, key)``,
where the key is the turn id plus the normalised query. Every policy therefore
sees the same latency for the same query in the same turn, so comparisons
between policies are paired and noise-free.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

__all__ = ["PROFILES", "LatencyProfile"]

_Z95 = 1.6448536269514722


@dataclass(frozen=True, slots=True)
class LatencyProfile:
    name: str
    median_ms: float
    p95_ms: float
    description: str = ""
    seed: int = 0

    @property
    def sigma(self) -> float:
        return max(0.0, math.log(self.p95_ms / self.median_ms) / _Z95)

    @property
    def mean_ms(self) -> float:
        return self.median_ms * math.exp(self.sigma**2 / 2)

    def sample(self, key: str) -> float:
        digest = hashlib.blake2b(f"{self.seed}|{self.name}|{key}".encode(), digest_size=8).digest()
        rng = random.Random(int.from_bytes(digest, "big"))
        return rng.lognormvariate(math.log(self.median_ms), self.sigma)


PROFILES: dict[str, LatencyProfile] = {
    p.name: p
    for p in (
        LatencyProfile(
            "local",
            8,
            25,
            "In-process index (FAISS/BM25 in the agent process). Look-ahead cannot help much here.",
        ),
        LatencyProfile(
            "hosted_kb",
            250,
            550,
            "Embedding API + managed vector DB. Remote vector DBs measure ~100-300 ms and remote "
            "embedding ~200 ms (Salesforce VoiceAgentRAG); ElevenLabs documents ~250 ms for RAG.",
        ),
        LatencyProfile(
            "rerank",
            750,
            1400,
            "Hosted KB plus a cross-encoder reranker over 10-20 candidates (measured 585-1258 ms).",
        ),
        LatencyProfile(
            "web_search",
            1600,
            3500,
            "Web search or a tool call. Stream RAG measures 3.37 s mean tool latency.",
        ),
    )
}
