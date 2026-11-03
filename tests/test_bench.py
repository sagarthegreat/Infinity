from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from forehear import BM25Index, Controller, FinalOnly, StablePrefix
from forehear.bench.cli import main
from forehear.bench.data import Turn, load_corpus, load_turns
from forehear.bench.latency import PROFILES, LatencyProfile
from forehear.bench.metrics import percentile, summarize
from forehear.bench.runner import retrievability_curve, run_matrix, standard_policies
from forehear.bench.sim import Oracle, SearchCache, Timing, _turn_events, simulate, simulate_turn

PASSAGES = [
    {
        "id": "redbull",
        "title": "Red Bull",
        "text": "Red Bull GmbH was founded by Dietrich Mateschitz in 1987.",
    },
    {
        "id": "onedrive",
        "title": "OneDrive",
        "text": "Microsoft announced that SkyDrive would be renamed OneDrive.",
    },
    {"id": "paris", "title": "Paris", "text": "Paris is the capital and most populous city of France."},
]

TRACES = [
    {
        "id": "t1",
        "question": "Who founded Red Bull?",
        "gold_doc_ids": ["redbull"],
        "asr_final": "who founded red bull",
        "speech_start_ms": 1000,
        "speech_end_ms": 2500,
        "events": [
            [1300, "who"],
            [1600, "who found"],
            [1900, "who founded red"],
            [2400, "who founded red bull"],
        ],
        "words": [["who", 1000, 1200], ["founded", 1250, 1700], ["red", 1750, 1950], ["bull", 2200, 2500]],
    },
    {
        "id": "t2",
        "question": "What is the capital of France?",
        "gold_doc_ids": ["paris"],
        "asr_final": "what is the capital of france",
        "speech_start_ms": 500,
        "speech_end_ms": 2600,
        "events": [[900, "what is"], [1500, "what is the capital"], [2300, "what is the capital of france"]],
        "words": [["what", 500, 700], ["france", 2200, 2600]],
    },
]


@pytest.fixture()
def files(tmp_path: Path) -> tuple[Path, Path]:
    traces = tmp_path / "traces.jsonl.gz"
    corpus = tmp_path / "corpus.jsonl.gz"
    with gzip.open(traces, "wt") as fh:
        fh.write("\n".join(json.dumps(t) for t in TRACES) + "\n")
    with gzip.open(corpus, "wt") as fh:
        fh.write("\n".join(json.dumps(p) for p in PASSAGES) + "\n")
    return traces, corpus


@pytest.fixture()
def setup(files):
    traces, corpus = files
    turns = load_turns(traces)
    search = SearchCache(BM25Index(load_corpus(corpus)).search, 1)
    return turns, search


def test_loaders(files):
    traces, corpus = files
    turns = load_turns(traces)
    assert [t.id for t in turns] == ["t1", "t2"]
    assert turns[0].gold == frozenset({"redbull"}) and turns[0].speech_ms == 1500
    assert turns[0].words[1] == ("founded", 1250.0, 1700.0)
    assert load_turns(traces, limit=1)[0].id == "t1"
    docs = load_corpus(corpus)
    assert docs[0].text.startswith("Red Bull. ")


def test_latency_profile_is_deterministic_and_calibrated():
    p = LatencyProfile("x", 200, 500)
    assert p.sample("a") == p.sample("a")
    samples = sorted(p.sample(str(i)) for i in range(4000))
    assert 180 < samples[2000] < 220
    assert 430 < samples[3800] < 570
    assert p.mean_ms > p.median_ms
    assert set(PROFILES) == {"local", "hosted_kb", "rerank", "web_search"}


def test_turn_events_add_pause_false_alarms():
    turn = Turn(
        id="x",
        question="",
        gold=frozenset(),
        asr_final="who founded red bull",
        speech_start_ms=1000,
        speech_end_ms=2500,
        events=((1300.0, "who"), (2000.0, "who founded red")),
        words=(("who", 1000, 1200), ("founded", 1250, 1700), ("red", 1750, 1950), ("bull", 2200, 2500)),
    )
    kinds = [(e.kind.value, e.t_ms) for e in _turn_events(turn, Timing(eager_ms=200, eot_ms=500))]
    assert ("eager_end_of_turn", 2150) in kinds and ("turn_resumed", 2200) in kinds
    assert kinds[-2:] == [("eager_end_of_turn", 2700), ("end_of_turn", 3000)]
    no_eager = [e.kind.value for e in _turn_events(turn, Timing(eager_ms=None))]
    assert "eager_end_of_turn" not in no_eager


def test_final_only_matches_baseline(setup):
    turns, search = setup
    res = simulate(turns, lambda: Controller(FinalOnly()), search, PROFILES["hosted_kb"])
    assert all(r.wait_ms == pytest.approx(r.baseline_wait_ms) for r in res)
    assert all(r.speculative_calls == 0 and r.fresh_calls == 1 for r in res)


def test_speculation_saves_latency_when_slow(setup):
    turns, search = setup
    slow = LatencyProfile("slow", 600, 900)
    res = simulate(turns, lambda: Controller(StablePrefix(agreement=1)), search, slow, Timing(eot_ms=500))
    s = summarize(res)
    assert s.saved_mean_ms > 0 and s.coverage > 0
    assert s.recall_at_k == s.baseline_recall_at_k == 1.0


def test_oracle_is_upper_bound(setup):
    turns, search = setup
    prof = PROFILES["rerank"]
    oracle = simulate(turns, lambda: Controller(Oracle()), search, prof)
    final = simulate(turns, lambda: Controller(FinalOnly()), search, prof)
    assert sum(r.wait_ms for r in oracle) <= sum(r.wait_ms for r in final)
    t = turns[0]
    single = simulate_turn(t, Controller(Oracle()), search, prof)
    assert single.reused


def test_summary_and_percentile(setup):
    assert percentile([], 50) == 0.0
    assert percentile([1, 2, 3, 4], 50) == 2.5
    turns, search = setup
    s = summarize(simulate(turns, lambda: Controller(FinalOnly()), search, PROFILES["local"]))
    d = s.as_dict()
    assert d["turns"] == 2 and d["calls_per_turn"] == 1.0
    with pytest.raises(ValueError):
        summarize([])


def test_run_matrix_and_curve(setup):
    turns, search = setup
    rows = run_matrix(turns, search, profiles=[PROFILES["hosted_kb"]])
    names = {(r["scenario"], r["policy"]) for r in rows}
    assert ("interims_only", "eager_eot") not in names  # needs an eager signal
    assert ("with_eager_eot", "eager_eot") in names
    assert len({p.name for p in standard_policies()}) == len(standard_policies())
    curve = retrievability_curve(turns, search, offsets_ms=(-5000, -1000, 0))
    assert curve[0]["retrievable"] == 0.0 and curve[-1]["retrievable"] == 1.0
    assert curve[-1]["final_recall"] == 1.0


def test_cli_bench_and_replay(files, tmp_path, capsys):
    traces, corpus = files
    out = tmp_path / "out"
    common = ["--traces", str(traces), "--corpus", str(corpus), "--k", "1"]
    assert main(["bench", *common, "--out", str(out), "--no-plots", "--quiet", "--profiles", "rerank"]) == 0
    report = (out / "RESULTS.md").read_text()
    assert "interims_only" in report and "stable_prefix" in report
    payload = json.loads((out / "results.json").read_text())
    assert payload["meta"]["turns"] == 2 and payload["rows"]
    assert main(["replay", *common, "--turn", "t1", "--policy", "stable_prefix_eager"]) == 0
    text = capsys.readouterr().out
    assert "DELIVER" in text and "speculate" in text
    assert main(["replay", *common, "--turn", "nope"]) == 2
    assert main(["profiles"]) == 0
