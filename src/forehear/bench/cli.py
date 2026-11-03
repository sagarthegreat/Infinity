"""``forehear`` command line: run the benchmark, replay a turn, list profiles."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from .. import __version__
from ..controller import Action, Cancel, Controller, Deliver, Start
from ..retrievers import BM25Index, DenseIndex
from ..text import normalize
from .data import Turn, load_corpus, load_turns
from .latency import PROFILES, LatencyProfile
from .runner import (
    SCENARIOS,
    eot_sweep,
    retrievability_curve,
    run_matrix,
    standard_policies,
    validator_sweep,
)
from .sim import Oracle, SearchCache, Timing, _turn_events

__all__ = ["main"]


def _log(msg: str) -> None:
    print(f"[forehear] {msg}", file=sys.stderr, flush=True)


def _setup(args: argparse.Namespace) -> tuple[list[Turn], SearchCache, dict[str, Any]]:
    t0 = time.time()
    turns = load_turns(args.traces, limit=args.limit or None)
    corpus = load_corpus(args.corpus)
    index: BM25Index | DenseIndex
    if getattr(args, "retriever", "bm25") == "dense":
        index = DenseIndex.from_model2vec(corpus, args.dense_model)
        retriever_name = f"dense ({args.dense_model}, model2vec)"
    else:
        index = BM25Index(corpus)
        retriever_name = "BM25 (forehear.BM25Index)"
    search = SearchCache(index.search, args.k)
    _log(f"{len(turns):,} turns, {len(corpus):,} passages indexed in {time.time() - t0:.1f}s")
    meta = {
        "turns": len(turns),
        "corpus": len(corpus),
        "retriever": retriever_name,
        "k": args.k,
        "asr": "Vosk en-us-0.22-lgraph",
        "chunk_ms": 100,
    }
    return turns, search, meta


def cmd_bench(args: argparse.Namespace) -> int:
    turns, search, meta = _setup(args)
    profiles = [PROFILES[p] for p in args.profiles] if args.profiles else list(PROFILES.values())
    scenarios = {
        name: Timing(asr_lag_ms=args.asr_lag_ms, eager_ms=t.eager_ms, eot_ms=args.eot_ms)
        for name, t in SCENARIOS.items()
        if not args.scenarios or name in args.scenarios
    }
    probe = search.ids
    policies = [p for p in standard_policies(probe=probe) if not args.policies or p.name in args.policies]
    meta["eot_ms"] = args.eot_ms
    t0 = time.time()
    rows = run_matrix(turns, search, scenarios=scenarios, profiles=profiles, policies=policies, progress=_log)
    curve = retrievability_curve(turns, search) if not args.no_extras else []
    sweep_profile = PROFILES["rerank"] if "rerank" in PROFILES else profiles[0]
    sweep = (
        validator_sweep(
            turns, search, sweep_profile, Timing(asr_lag_ms=args.asr_lag_ms, eot_ms=args.eot_ms), probe=probe
        )
        if not args.no_extras
        else []
    )
    eot_rows = (
        eot_sweep(
            turns,
            search,
            [p for p in profiles if p.name in ("hosted_kb", "rerank")] or profiles[:1],
            asr_lag_ms=args.asr_lag_ms,
        )
        if not args.no_extras
        else []
    )
    _log(f"simulated in {time.time() - t0:.1f}s ({len(search):,} distinct queries)")

    from .report import markdown_report, plot_all, write_json

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    meta["version"] = __version__
    meta["profiles"] = {p.name: {"median_ms": p.median_ms, "p95_ms": p.p95_ms} for p in profiles}
    write_json(
        out / "results.json",
        {"meta": meta, "rows": rows, "retrievability": curve, "sweep": sweep, "eot_sweep": eot_rows},
    )
    report = markdown_report(rows, curve, sweep, meta, eot_rows)
    (out / "RESULTS.md").write_text(report)
    if not args.no_plots:
        try:
            for p in plot_all(out, rows, curve, sweep):
                _log(f"wrote {p}")
        except ImportError:
            _log("matplotlib not installed; skipping figures (pip install 'forehear[plots]')")
    _log(f"wrote {out / 'RESULTS.md'} and {out / 'results.json'}")
    if not args.quiet:
        print(report)
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Print a millisecond timeline of one turn under one policy."""
    turns, search, _ = _setup(args)
    by_id = {t.id: t for t in turns}
    turn = by_id.get(args.turn) if args.turn else turns[args.index]
    if turn is None:
        _log(f"unknown turn id {args.turn}")
        return 2
    specs = standard_policies(probe=search.ids)
    spec = {p.name: p for p in specs}.get(args.policy)
    if spec is None:
        _log(f"unknown policy {args.policy}; choose from {', '.join(p.name for p in specs)}")
        return 2
    profile: LatencyProfile = PROFILES[args.profile]
    scen = SCENARIOS[args.scenario]
    timing = Timing(asr_lag_ms=args.asr_lag_ms, eager_ms=scen.eager_ms, eot_ms=args.eot_ms)
    ctl: Controller = spec.factory()
    if isinstance(ctl.policy, Oracle):
        ctl.policy.final = turn.asr_final

    print(f"turn {turn.id}  policy={spec.name}  profile={profile.name}  scenario={args.scenario}")
    print(f"  question : {turn.question}")
    print(f"  asr final: {turn.asr_final}")
    print(f"  gold     : {', '.join(sorted(turn.gold))}\n")
    import heapq
    import itertools

    seq = itertools.count()
    q: list[tuple[float, int, str, Any]] = [(e.t_ms, next(seq), "ev", e) for e in _turn_events(turn, timing)]
    heapq.heapify(q)
    live: dict[int, str] = {}

    def gold_mark(query: str) -> str:
        return "GOLD" if any(d.id in turn.gold for d in search(query)) else "miss"

    def run(actions: list[Action], t: float) -> bool:
        for a in actions:
            if isinstance(a, Start):
                lat = profile.sample(f"{turn.id}|{normalize(a.spec.query)}")
                live[a.spec.id] = a.spec.query
                heapq.heappush(q, (t + lat, next(seq), "res", a.spec.id))
                kind = "speculate" if a.spec.speculative else "retrieve "
                mark = gold_mark(a.spec.query)
                print(f"{t:8.0f} ms  {kind} #{a.spec.id} {a.spec.query!r}  (~{lat:.0f} ms, {mark})")
            elif isinstance(a, Cancel):
                live.pop(a.spec_id, None)
                print(f"{t:8.0f} ms  cancel    #{a.spec_id}")
            elif isinstance(a, Deliver):
                d = a.delivery
                src = f"reused #{d.spec_id}" if d.reused else f"fresh #{d.spec_id}"
                hit = "GOLD" if any(x.id in turn.gold for x in d.docs) else "miss"
                print(f"{t:8.0f} ms  DELIVER   {src}, wait {d.wait_ms:.0f} ms, top-{args.k} {hit}")
                return True
        return False

    while q:
        t, _, kind, payload = heapq.heappop(q)
        if kind == "ev":
            ev = payload
            label = ev.kind.value
            print(f"{t:8.0f} ms  {label:<17} {ev.text!r}" if ev.text else f"{t:8.0f} ms  {label}")
            if run(ctl.handle(ev), t):
                break
        else:
            if payload not in live:
                continue
            query = live.pop(payload)
            print(f"{t:8.0f} ms  result    #{payload}")
            if run(ctl.on_result(payload, search(query), t), t):
                break
    base = profile.sample(f"{turn.id}|{normalize(turn.asr_final)}")
    print(f"\nwithout look-ahead the wait would have been {base:.0f} ms")
    return 0


def cmd_profiles(_: argparse.Namespace) -> int:
    for p in PROFILES.values():
        print(f"{p.name:<11} median {p.median_ms:>5.0f} ms  p95 {p.p95_ms:>5.0f} ms  {p.description}")
    return 0


def cmd_curve(args: argparse.Namespace) -> int:
    turns, search, _ = _setup(args)
    print(json.dumps(retrievability_curve(turns, search), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="forehear", description="Look-ahead retrieval for voice agents.")
    ap.add_argument("--version", action="version", version=f"forehear {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--traces", help="trace file (default: bundled HeySQuAD/Vosk traces)")
        p.add_argument("--corpus", help="corpus file (default: bundled SQuAD v2 passages)")
        p.add_argument("--limit", type=int, default=0, help="use only the first N turns")
        p.add_argument("--k", type=int, default=5, help="top-k for recall (default 5)")
        p.add_argument(
            "--eot-ms", type=float, default=500.0, help="end of turn after last word (default 500)"
        )
        p.add_argument("--asr-lag-ms", type=float, default=0.0, help="extra delay on interims (default 0)")
        p.add_argument(
            "--retriever", choices=["bm25", "dense"], default="bm25", help="retriever (default bm25)"
        )
        p.add_argument(
            "--dense-model",
            default="minishlab/potion-retrieval-32M",
            help="model2vec model for --retriever dense (pip install 'forehear[dense]')",
        )

    b = sub.add_parser("bench", help="run the full benchmark matrix")
    common(b)
    b.add_argument("--profiles", nargs="*", choices=list(PROFILES), help="latency profiles")
    b.add_argument("--scenarios", nargs="*", choices=list(SCENARIOS), help="turn-signal scenarios")
    b.add_argument("--policies", nargs="*", help="policy names (default: all)")
    b.add_argument("--out", default="results", help="output directory (default: results/)")
    b.add_argument("--no-plots", action="store_true")
    b.add_argument("--no-extras", action="store_true", help="skip retrievability curve and sweep")
    b.add_argument("--quiet", action="store_true")
    b.set_defaults(func=cmd_bench)

    r = sub.add_parser("replay", help="print a timeline of one turn")
    common(r)
    r.add_argument("--turn", help="turn id")
    r.add_argument("--index", type=int, default=0, help="turn index if --turn is not given")
    r.add_argument("--policy", default="stable_prefix")
    r.add_argument("--profile", default="rerank", choices=list(PROFILES))
    r.add_argument("--scenario", default="interims_only", choices=list(SCENARIOS))
    r.set_defaults(func=cmd_replay)

    c = sub.add_parser("curve", help="print the retrievability curve as JSON")
    common(c)
    c.set_defaults(func=cmd_curve)

    p = sub.add_parser("profiles", help="list latency profiles")
    p.set_defaults(func=cmd_profiles)

    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
