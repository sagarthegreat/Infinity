"""Validators decide whether a speculative result may stand in for the final query.

At end of turn the controller scores every live speculative call against the
final transcript. Calls scoring at or above the validator's ``threshold`` are
eligible for reuse; everything else is cancelled and, if nothing qualifies, a
fresh retrieval runs on the final transcript. The validator is the knob that
trades latency for retrieval quality.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from .text import content_words, normalize

__all__ = ["ExactMatch", "ResultOverlap", "TokenCoverage", "Validator"]


class Validator:
    """Base class: ``score`` returns a value in ``[0, 1]``."""

    threshold: float = 1.0

    def score(self, speculative_query: str, final_query: str) -> float:  # pragma: no cover
        raise NotImplementedError

    def accepts(self, speculative_query: str, final_query: str) -> bool:
        return self.score(speculative_query, final_query) >= self.threshold


class ExactMatch(Validator):
    """Reuse only if the normalised queries are identical (LiveKit/Pipecat semantics)."""

    threshold = 1.0

    def score(self, speculative_query: str, final_query: str) -> float:
        return 1.0 if normalize(speculative_query) == normalize(final_query) else 0.0

    def __repr__(self) -> str:
        return "ExactMatch()"


class TokenCoverage(Validator):
    """Reuse if the speculative query covers the final query's content words.

    The score is ``min(recall, precision)`` over sets of content words:
    *recall* is the share of the final query's content words present in the
    speculative query, *precision* the share of the speculative query's content
    words that survived into the final query. Taking the minimum rejects both
    truncated guesses ("capital" for "capital of france") and guesses built on
    words the ASR later revised ("red bull founder" for "who founded rare").

    Args:
        threshold: Minimum score to accept. ``0.8`` is a reasonable default;
            ``1.0`` requires the same set of content words.
    """

    def __init__(self, threshold: float = 0.8) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        self.threshold = threshold

    def score(self, speculative_query: str, final_query: str) -> float:
        final = set(content_words(final_query))
        spec = set(content_words(speculative_query))
        if not final or not spec:
            return 1.0 if normalize(speculative_query) == normalize(final_query) else 0.0
        common = len(final & spec)
        return min(common / len(final), common / len(spec))

    def __repr__(self) -> str:
        return f"TokenCoverage(threshold={self.threshold})"


class ResultOverlap(Validator):
    """Reuse if a cheap probe retriever returns similar results for both queries.

    This is Stream RAG's "reflector" idea generalised: when your pipeline has a
    cheap first stage (a local BM25 or ANN index) in front of something slow
    (a reranker, a remote knowledge base, web search, a tool), run only the
    cheap stage on the final query and compare its top-``k`` ids with the cheap
    stage's top-``k`` for the speculative query. If they overlap enough, the
    slow stage's speculative output is reused.

    Args:
        probe: ``probe(query) -> ids`` - must be fast and side-effect free.
        k: Compare the top ``k`` ids.
        threshold: Minimum ``|overlap| / k`` to accept.
    """

    def __init__(self, probe: Callable[[str], Sequence[str]], *, k: int = 5, threshold: float = 0.6) -> None:
        self.probe = probe
        self.k = k
        self.threshold = threshold
        self._cache: dict[str, tuple[str, ...]] = {}

    def _ids(self, query: str) -> tuple[str, ...]:
        key = normalize(query)
        if key not in self._cache:
            if len(self._cache) > 4096:
                self._cache.clear()
            self._cache[key] = tuple(self.probe(query))[: self.k]
        return self._cache[key]

    def score(self, speculative_query: str, final_query: str) -> float:
        if normalize(speculative_query) == normalize(final_query):
            return 1.0
        a, b = self._ids(speculative_query), self._ids(final_query)
        if not a or not b:
            return 0.0
        return len(set(a) & set(b)) / self.k

    def __repr__(self) -> str:
        return f"ResultOverlap(k={self.k}, threshold={self.threshold})"
