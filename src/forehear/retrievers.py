"""Reference retrievers. forehear works with *any* retriever; these exist so the
benchmark and examples run with zero dependencies."""

from __future__ import annotations

import asyncio
import math
from collections import Counter, defaultdict
from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import Any

from .text import content_words
from .types import Doc

__all__ = ["BM25Index", "DenseIndex", "with_latency"]


def _stem(word: str) -> str:
    # Deliberately tiny suffix stripping; enough to match "announced"/"announce".
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _terms(text: str) -> list[str]:
    return [_stem(w) for w in content_words(text)]


class BM25Index:
    """A small, pure-Python Okapi BM25 index.

    Good for tens of thousands of passages, which covers the benchmark corpus
    (~20k SQuAD paragraphs) at a few milliseconds per query.

    Args:
        docs: ``Doc`` objects or ``(id, text)`` pairs.
        k1, b: BM25 parameters.
    """

    def __init__(self, docs: Iterable[Doc | tuple[str, str]], *, k1: float = 0.9, b: float = 0.4) -> None:
        self.k1 = k1
        self.b = b
        self.docs: list[Doc] = []
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        lengths: list[int] = []
        for item in docs:
            doc = item if isinstance(item, Doc) else Doc(id=item[0], text=item[1])
            idx = len(self.docs)
            self.docs.append(doc)
            tf = Counter(_terms(doc.text))
            lengths.append(sum(tf.values()))
            for term, n in tf.items():
                postings[term].append((idx, n))
        self._lengths = lengths
        n_docs = len(self.docs)
        self._avgdl = (sum(lengths) / n_docs) if n_docs else 0.0
        self._postings = dict(postings)
        self._idf = {
            t: math.log(1.0 + (n_docs - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self._postings.items()
        }

    def __len__(self) -> int:
        return len(self.docs)

    def search(self, query: str, k: int = 10) -> list[Doc]:
        """Top-``k`` passages for ``query``."""
        scores: dict[int, float] = defaultdict(float)
        k1, b, avgdl, lengths = self.k1, self.b, self._avgdl or 1.0, self._lengths
        for term, qtf in Counter(_terms(query)).items():
            plist = self._postings.get(term)
            if not plist:
                continue
            idf = self._idf[term]
            for idx, tf in plist:
                denom = tf + k1 * (1.0 - b + b * lengths[idx] / avgdl)
                scores[idx] += qtf * idf * tf * (k1 + 1.0) / denom
        top = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
        out = []
        for idx, score in top:
            d = self.docs[idx]
            out.append(Doc(id=d.id, text=d.text, score=score, meta=d.meta))
        return out

    def ids(self, query: str, k: int = 10) -> list[str]:
        return [d.id for d in self.search(query, k)]


class DenseIndex:
    """Brute-force cosine-similarity index over embeddings (requires ``numpy``).

    Args:
        docs: ``Doc`` objects or ``(id, text)`` pairs.
        encode: ``encode(list_of_texts) -> 2-D array`` of embeddings.
        batch_size: Encoding batch size for the corpus.

    Use :meth:`from_model2vec` for a fast, CPU-only static embedding model.
    """

    def __init__(
        self,
        docs: Iterable[Doc | tuple[str, str]],
        encode: Callable[[list[str]], Any],
        *,
        batch_size: int = 1024,
    ) -> None:
        import numpy as np

        self._np = np
        self.encode = encode
        self.docs = [d if isinstance(d, Doc) else Doc(id=d[0], text=d[1]) for d in docs]
        chunks = []
        for i in range(0, len(self.docs), batch_size):
            chunks.append(
                np.asarray(encode([d.text for d in self.docs[i : i + batch_size]]), dtype=np.float32)
            )
        matrix = np.concatenate(chunks) if chunks else np.zeros((0, 1), dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        self._matrix = matrix / np.maximum(norms, 1e-12)

    @classmethod
    def from_model2vec(
        cls, docs: Iterable[Doc | tuple[str, str]], model: str = "minishlab/potion-retrieval-32M"
    ) -> DenseIndex:
        """Build an index with a model2vec static embedding model (``pip install model2vec``)."""
        from model2vec import StaticModel

        m = StaticModel.from_pretrained(model)
        return cls(docs, m.encode)

    def __len__(self) -> int:
        return len(self.docs)

    def search(self, query: str, k: int = 10) -> list[Doc]:
        np = self._np
        if not query.strip() or not self.docs:
            return []
        q = np.asarray(self.encode([query]), dtype=np.float32)[0]
        q = q / max(float(np.linalg.norm(q)), 1e-12)
        scores = self._matrix @ q
        k = min(k, len(self.docs))
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top], kind="stable")]
        return [Doc(id=self.docs[i].id, text=self.docs[i].text, score=float(scores[i])) for i in top]

    def ids(self, query: str, k: int = 10) -> list[str]:
        return [d.id for d in self.search(query, k)]


def with_latency(
    search: Callable[[str], Sequence[Doc]], latency_ms: float | Callable[[str], float]
) -> Callable[[str], Awaitable[Sequence[Doc]]]:
    """Wrap a sync search function as an async retriever with artificial latency.

    Handy for demos and for feeling what a slow knowledge base does to a
    voice agent::

        retrieve = with_latency(index.search, 300)   # 300 ms "remote" KB
    """

    async def retrieve(query: str) -> Sequence[Doc]:
        delay = latency_ms(query) if callable(latency_ms) else latency_ms
        await asyncio.sleep(delay / 1000.0)
        return search(query)

    return retrieve
