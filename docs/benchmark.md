# The forehear benchmark

An open, deterministic, CPU-only benchmark for one question:

> **If a voice agent starts retrieval while the user is still talking, how much
> latency does it save, how many extra calls does it cost, and does it hurt
> retrieval quality?**

```bash
pip install "forehear[plots]"
forehear bench                     # full matrix, writes results/
forehear replay --index 7          # millisecond timeline of one turn
```

The full run takes a few minutes on a laptop. It needs no GPU, no API keys and no
network access once the data files are present.

## What is simulated, and what is real

| | real | simulated |
|---|---|---|
| Speech | 4k+ questions **read aloud by people** (HeySQuAD human split) | |
| Interim transcripts | **Real streaming ASR output** (Vosk, 100 ms chunks), including revisions | |
| Word timing | From the ASR final result | |
| Retrieval results | **Real retrieval** (BM25 or dense) over 19,831 SQuAD passages | |
| Retrieval latency | | Log-normal profiles fitted to published measurements |
| Turn detection | | End of turn *n* ms after the last word; optional eager signal |
| Controller | **The production `forehear.Controller`**, unmodified | Driven by a virtual clock |

Everything an engineer can't control (what people say, how ASR revises
itself, which passages come back) is real. Everything that varies by deployment
(retrieval latency, turn-detector settings) is a parameter you can set to match
your stack.

## Timing model

For each turn the simulator emits:

* `SPEECH_START` at the first word's start;
* `INTERIM` at each recorded hypothesis change (+ `--asr-lag-ms`);
* in the `with_eager_eot` scenario, `EAGER_END_OF_TURN` whenever there is
  `eager_ms` (200 ms) of silence, **including mid-sentence pauses** (followed by
  `TURN_RESUMED` when the user carries on), and again 200 ms after the last word;
* `END_OF_TURN` `--eot-ms` (500 ms) after the last word, with the final
  transcript.

Two scenarios cover the two kinds of speech stack in production:

* `interims_only`: interim transcripts plus a final end of turn. This is what
  most STT services give you (Deepgram Nova, AssemblyAI, Google, AWS,
  Whisper-based streaming).
* `with_eager_eot`: adds an eager end-of-turn signal, as in Deepgram Flux,
  LiveKit preflight transcripts and Pipecat's eager turn strategies. Its
  `eager_eot` policy is today's state of the art, and the real bar to beat.

## Latency profiles

| profile | median | p95 | models |
|---|---:|---:|---|
| `local` | 8 ms | 25 ms | in-process index |
| `hosted_kb` | 250 ms | 550 ms | embedding API + managed vector DB (measured 100-300 ms DB + ~200 ms embedding; ElevenLabs documents ~250 ms) |
| `rerank` | 750 ms | 1,400 ms | hosted KB + cross-encoder reranker (measured 585-1,258 ms for 10-20 candidates) |
| `web_search` | 1,600 ms | 3,500 ms | web search / tool call (Stream RAG: 3.37 s mean tool latency) |

Sources are collected in [`docs/research/`](research/). Latency draws are
**keyed by (turn, query)**, so every policy sees the same latency for the same
query and all comparisons are paired.

## Metrics

Borrowed from hardware prefetching where an equivalent exists (Srinath et al., HPCA 2007):

| metric | definition |
|---|---|
| **wait** | ms from end of turn until context is ready. This is the latency retrieval adds to the turn. |
| **saved** | per-turn `wait(final_only) - wait(policy)`, paired |
| **ready at EOT** | share of turns with zero wait |
| **coverage** | share of turns served by a speculative call |
| **accuracy** | speculative calls that served a turn / speculative calls issued |
| **lateness** | served turns whose call was still in flight at end of turn |
| **calls/turn** | all retrieval calls per turn (`final_only` = 1.00). This is the cost. |
| **recall@k Δ** | gold-passage recall@k of what was delivered, minus recall@k of retrieving on the final transcript |
| **lead time** | how long before end of turn a completed speculative call first held a gold passage |
| **retrievability curve** | share of turns whose *current* interim hypothesis already retrieves a gold passage, by time relative to the end of speech |

## Policies compared

| name | description |
|---|---|
| `final_only` | retrieve on the final transcript (no look-ahead) |
| `eager_eot` | retrieve once on the eager end-of-turn transcript |
| `interval_1000ms` | latest hypothesis every 1 s (Stream RAG fixed-interval mode) |
| `interval_500ms` | latest hypothesis every 500 ms |
| `local_agreement` | only words two consecutive hypotheses agree on (LocalAgreement-2) |
| `stable_prefix` | **forehear default**: latest hypothesis once it has 3+ content words, each time a new one appears |
| `stable_prefix_lean` | as `stable_prefix`, from 4+ content words (fewer calls) |
| `stable_prefix_overlap` | `stable_prefix`, reusing a result only if a cheap first stage returns 4 of the same top 5 (`ResultOverlap(0.8)`) |
| `adaptive` | `stable_prefix` levels steered by a 3-calls-per-turn budget; switches itself off for fast retrievers |
| `oracle` | the final transcript, fired on the first interim (an upper bound no real system reaches) |

Unless stated otherwise, speculative policies reuse a result only if
`TokenCoverage(0.8)` accepts it, and otherwise fall back to retrieving on the
final transcript. The reuse-validator sweep shows the full latency/quality
trade-off for both validators.

## Limitations

* **Single-turn questions.** HeySQuAD questions are read-aloud, single-turn
  and short (~3-4 s). Conversational turns are longer, messier and
  context-dependent. Multi-turn spoken dialogue traces (e.g. DSTC10 Track 2)
  are the most valuable next addition.
* **One ASR engine.** Vosk revises its hypotheses differently from Deepgram
  or Whisper-streaming. Traces from other engines are welcome (see
  `data/README.md`).
* **Read speech.** People reading questions pause less than people thinking
  aloud, which probably understates eager false alarms.
* **Simulated latency.** Measured distributions from your own stack will beat
  any profile; `LatencyProfile(name, median_ms, p95_ms)` takes your numbers.
* **Retrieval quality is measured with the benchmark retriever.** The
  `rerank`/`web_search` profiles model *latency* of slower pipelines; recall
  is still measured with BM25/dense output.
