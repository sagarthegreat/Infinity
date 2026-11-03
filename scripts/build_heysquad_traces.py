#!/usr/bin/env python3
"""Build the forehear streaming-transcript benchmark from HeySQuAD human audio.

This script is only needed to *regenerate* the committed data files in
``data/``. Running the benchmark itself never needs audio, an ASR model, or a
network connection.

Pipeline
--------
1. Read the human-recorded split of HeySQuAD (validation, 4,158 questions,
   CC BY 4.0) from its parquet files.
2. Stream every recording through Vosk (Kaldi) in 100 ms chunks, exactly as a
   live voice agent would, and record every change of the running hypothesis
   (interim/partial results), timestamped in audio time. Interim hypotheses
   are *real* ASR output: they get revised, not just extended.
3. Record word-level timings from the final result (speech start/end).
4. Drop rows whose audio does not match the reference question (HeySQuAD has
   misaligned rows: the audio belongs to a different question).
5. Write the retrieval corpus: every unique SQuAD v2 paragraph (train + dev),
   so retrieval happens over ~20k passages, not just the 1.2k dev ones.

Usage::

    python scripts/build_heysquad_traces.py \
        --heysquad /path/to/HeySQuAD_human/data \
        --squad-train /path/to/squad_v2/train.parquet \
        --vosk-model /path/to/vosk-model-en-us-0.22-lgraph \
        --out data/

Requires: ``pip install vosk pyarrow soundfile numpy``.
"""

from __future__ import annotations

import argparse
import difflib
import gzip
import hashlib
import io
import json
import multiprocessing as mp
import re
import sys
import time
from pathlib import Path

CHUNK_MS = 100
SAMPLE_RATE = 16_000
MIN_ALIGNMENT = 0.5

_model = None


def doc_id(context: str) -> str:
    norm = " ".join(context.split())
    return "sq-" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def _norm_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def alignment(reference: str, hypothesis: str) -> float:
    a, b = _norm_words(reference), _norm_words(hypothesis)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def _init(model_path: str) -> None:
    global _model
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)
    _model = Model(model_path)


def _to_pcm16(audio_bytes: bytes) -> bytes:
    import numpy as np
    import soundfile as sf

    data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float64")
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != SAMPLE_RATE:  # linear resample; HeySQuAD human audio is already 16 kHz
        n = round(len(data) * SAMPLE_RATE / sr)
        data = np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data)
    return (np.clip(data, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def stream_transcribe(pcm: bytes) -> dict:
    from vosk import KaldiRecognizer

    rec = KaldiRecognizer(_model, SAMPLE_RATE)
    rec.SetWords(True)
    bytes_per_chunk = SAMPLE_RATE * 2 * CHUNK_MS // 1000
    finals: list[str] = []
    words: list[list] = []
    events: list[list] = []
    last = ""

    def add_result(res: dict) -> None:
        if res.get("text"):
            finals.append(res["text"])
        for w in res.get("result", []):
            words.append([w["word"], round(w["start"] * 1000), round(w["end"] * 1000)])

    for i in range(0, len(pcm), bytes_per_chunk):
        chunk = pcm[i : i + bytes_per_chunk]
        t_ms = round((i + len(chunk)) / 2 / SAMPLE_RATE * 1000)
        if rec.AcceptWaveform(chunk):
            add_result(json.loads(rec.Result()))
            partial = ""
        else:
            partial = json.loads(rec.PartialResult()).get("partial", "")
        hyp = " ".join([*finals, partial]).strip()
        if hyp != last:
            events.append([t_ms, hyp])
            last = hyp
    add_result(json.loads(rec.FinalResult()))
    final_text = " ".join(finals).strip()
    return {
        "events": events,
        "words": words,
        "asr_final": final_text,
        "audio_ms": round(len(pcm) / 2 / SAMPLE_RATE * 1000),
    }


def process_row(row: dict) -> dict | None:
    pcm = _to_pcm16(row["audio"]["bytes"])
    out = stream_transcribe(pcm)
    if not out["words"]:
        return None
    return {
        "id": row["id"],
        "question": row["question"],
        "gold_doc_ids": [doc_id(row["context"])],
        "is_impossible": bool(row["is_impossible"]),
        "asr_final": out["asr_final"],
        "alignment": round(alignment(row["question"], out["asr_final"]), 3),
        "speech_start_ms": out["words"][0][1],
        "speech_end_ms": out["words"][-1][2],
        "audio_ms": out["audio_ms"],
        "events": out["events"],
        "words": out["words"],
    }


def iter_rows(heysquad_dir: Path, *, with_audio: bool = True):
    import pyarrow.parquet as pq

    for f in sorted(heysquad_dir.glob("validation-*.parquet")):
        pf = pq.ParquetFile(f)
        columns = None if with_audio else ["id"]
        for batch in pf.iter_batches(batch_size=64, columns=columns):
            yield from batch.to_pylist()


def _salvage(path: Path) -> list[str]:
    """Complete JSON lines from a (possibly truncated) gzip file."""
    import zlib

    text = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(path.read_bytes()).decode("utf-8", "ignore")
    out = []
    for line in text.split("\n")[:-1]:
        try:
            json.loads(line)
        except ValueError:
            break
        out.append(line)
    return out


def _gzip_text(path: Path) -> io.TextIOWrapper:
    """A gzip text writer with a fixed header timestamp, so rebuilds are byte-identical."""
    raw = open(path, "wb")  # noqa: SIM115 - closed with the wrapper
    return io.TextIOWrapper(gzip.GzipFile(fileobj=raw, mode="wb", mtime=0), encoding="utf-8")


def build_corpus(heysquad_dir: Path, squad_train: Path, out: Path) -> int:
    import pyarrow.parquet as pq

    seen: dict[str, dict] = {}
    sources = [(squad_train, ["title", "context"])]
    for f in sorted(heysquad_dir.glob("validation-*.parquet")):
        sources.append((f, ["context"]))
    for path, cols in sources:
        table = pq.read_table(path, columns=cols)
        titles = table.column("title").to_pylist() if "title" in cols else None
        for i, ctx in enumerate(table.column("context").to_pylist()):
            did = doc_id(ctx)
            if did not in seen:
                seen[did] = {
                    "id": did,
                    "title": (titles[i] if titles else "").replace("_", " "),
                    "text": " ".join(ctx.split()),
                }
    with _gzip_text(out) as fh:
        for rec in sorted(seen.values(), key=lambda r: r["id"]):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(seen)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--heysquad", type=Path, required=True)
    ap.add_argument("--squad-train", type=Path, required=True)
    ap.add_argument("--vosk-model", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("data"))
    ap.add_argument("--workers", type=int, default=mp.cpu_count())
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--resume",
        action="store_true",
        help="keep complete records from an interrupted run and continue after the last one",
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    n_docs = build_corpus(args.heysquad, args.squad_train, args.out / "squad_v2_passages.jsonl.gz")
    print(f"corpus: {n_docs} passages", file=sys.stderr)

    traces_path = args.out / "heysquad_dev_vosk.jsonl.gz"
    previous = _salvage(traces_path) if args.resume and traces_path.exists() else []
    skip_until = -1
    if previous:
        last_id = json.loads(previous[-1])["id"]
        ids = [r["id"] for r in iter_rows(args.heysquad, with_audio=False)]
        skip_until = ids.index(last_id)
        print(f"resuming after source row {skip_until} ({len(previous)} records kept)", file=sys.stderr)

    def todo():
        for i, r in enumerate(iter_rows(args.heysquad)):
            if args.limit and i >= args.limit:
                return
            if i > skip_until:
                yield r

    kept = len(previous)
    processed = skip_until + 1
    t0 = time.time()
    tmp_path = traces_path.with_suffix(".part")
    with (
        mp.Pool(args.workers, initializer=_init, initargs=(str(args.vosk_model),)) as pool,
        _gzip_text(tmp_path) as fh,
    ):
        for line in previous:
            fh.write(line + "\n")
        for i, rec in enumerate(pool.imap(process_row, todo(), chunksize=4)):
            processed += 1
            if rec is not None and rec["alignment"] >= MIN_ALIGNMENT:
                fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
                kept += 1
            if (i + 1) % 250 == 0:
                print(f"{i + 1} rows, {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    tmp_path.replace(traces_path)
    stats = {
        "source_rows": processed,
        "kept": kept,
        "dropped_misaligned_or_silent": processed - kept,
        "min_alignment": MIN_ALIGNMENT,
        "chunk_ms": CHUNK_MS,
        "asr": f"vosk / {args.vosk_model.name}",
        "corpus_passages": n_docs,
    }
    (args.out / "heysquad_dev_vosk.stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
