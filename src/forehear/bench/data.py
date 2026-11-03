"""Benchmark data: spoken turns with real streaming-ASR interim hypotheses.

Two files, both produced by ``scripts/build_heysquad_traces.py``:

``heysquad_dev_vosk.jsonl.gz``
    One line per human-recorded HeySQuAD question: every interim hypothesis
    Vosk emitted while streaming the audio in 100 ms chunks (timestamped in
    audio time), the final transcript, word-level speech start/end, and the id
    of the gold SQuAD paragraph.
``squad_v2_passages.jsonl.gz``
    The retrieval corpus: every unique SQuAD v2 paragraph (train + dev).

Files are looked up in ``$FOREHEAR_DATA``, then the repository's ``data/``
directory, then the user cache (downloaded on first use).
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ..types import Doc

__all__ = ["CORPUS_FILE", "TRACES_FILE", "Turn", "data_path", "load_corpus", "load_turns"]

TRACES_FILE = "heysquad_dev_vosk.jsonl.gz"
CORPUS_FILE = "squad_v2_passages.jsonl.gz"
_BASE_URL = os.environ.get(
    "FOREHEAR_DATA_URL", "https://raw.githubusercontent.com/sagarthegreat/Infinity/main/data/"
)


@dataclass(frozen=True, slots=True)
class Turn:
    """One user turn as a voice agent would have heard it."""

    id: str
    question: str
    """Reference (typed) question."""
    gold: frozenset[str]
    """Ids of passages that answer the question."""
    asr_final: str
    """Final ASR transcript."""
    speech_start_ms: float
    speech_end_ms: float
    events: tuple[tuple[float, str], ...]
    """``(audio_time_ms, hypothesis)`` for every change of the interim hypothesis."""
    words: tuple[tuple[str, float, float], ...] = ()
    """``(word, start_ms, end_ms)`` from the final ASR result."""
    is_impossible: bool = False

    @property
    def speech_ms(self) -> float:
        return self.speech_end_ms - self.speech_start_ms


def _candidates(name: str) -> Iterator[Path]:
    env = os.environ.get("FOREHEAR_DATA")
    if env:
        yield Path(env) / name
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            yield parent / "data" / name
            break
    yield Path.cwd() / "data" / name
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "forehear"
    yield cache / name


def data_path(name: str, *, download: bool = True) -> Path:
    """Locate a benchmark data file, downloading it to the cache if needed."""
    candidates = list(_candidates(name))
    for path in candidates:
        if path.exists():
            return path
    if not download:
        raise FileNotFoundError(f"{name} not found in: {', '.join(map(str, candidates))}")
    target = candidates[-1]
    target.parent.mkdir(parents=True, exist_ok=True)
    url = _BASE_URL + name
    print(f"forehear: downloading {url}", file=sys.stderr)
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(url, timeout=60) as resp, open(tmp, "wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    tmp.replace(target)
    return target


def load_turns(path: str | Path | None = None, *, limit: int | None = None) -> list[Turn]:
    """Load benchmark turns."""
    p = Path(path) if path else data_path(TRACES_FILE)
    out: list[Turn] = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            out.append(
                Turn(
                    id=r["id"],
                    question=r["question"],
                    gold=frozenset(r["gold_doc_ids"]),
                    asr_final=r["asr_final"],
                    speech_start_ms=float(r["speech_start_ms"]),
                    speech_end_ms=float(r["speech_end_ms"]),
                    events=tuple((float(t), str(text)) for t, text in r["events"]),
                    words=tuple((str(w), float(a), float(b)) for w, a, b in r.get("words", ())),
                    is_impossible=bool(r.get("is_impossible", False)),
                )
            )
            if limit and len(out) >= limit:
                break
    return out


def load_corpus(path: str | Path | None = None) -> list[Doc]:
    """Load the retrieval corpus."""
    p = Path(path) if path else data_path(CORPUS_FILE)
    docs: list[Doc] = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            title = r.get("title") or ""
            text = f"{title}. {r['text']}" if title else r["text"]
            docs.append(Doc(id=r["id"], text=text))
    return docs
