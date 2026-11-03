<div align="center">

# forehear

**Look-ahead retrieval for voice agents.**
Start RAG while the user is still talking, cancel the guesses that turn out wrong,
and have context ready the moment they stop.

[![CI](https://github.com/sagarthegreat/Infinity/actions/workflows/ci.yml/badge.svg)](https://github.com/sagarthegreat/Infinity/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Dependencies](https://img.shields.io/badge/core%20dependencies-0-brightgreen)

</div>

Voice agents that answer from documents retrieve **after** the user stops
talking. The lookup (embedding call, vector database, reranker, web search)
sits on the critical path of every turn, while the speech recogniser has been
streaming its best guess of the question for seconds. forehear runs retrieval
on those guesses, validates the best one against the final transcript, and
hands the LLM context that is usually already there.

```text
$ forehear replay --policy stable_prefix --profile rerank        # a real recording, real streaming ASR
    2400 ms  interim           "what didn't like her"                 <- the recogniser stumbles...
    2900 ms  interim           'what did microsoft'                   <- ...and revises itself
    4300 ms  speculate #1 'what did microsoft announced that it would rename'           (~514 ms, GOLD)
    4800 ms  speculate #2 'what did microsoft announced that it would rename one'       (~1207 ms, GOLD)
    5000 ms  speculate #3 'what did microsoft announced that it would rename one drive' (~666 ms, GOLD)
    5666 ms  result    #3
    5700 ms  speculate #4 '... rename one drive for business'                           (~870 ms, GOLD)
    6110 ms  end_of_turn       'what did microsoft announced that it would rename one drive for business to'
    6110 ms  cancel    #4
    6110 ms  DELIVER   reused #3, wait 0 ms, top-5 GOLD

without look-ahead the wait would have been 770 ms
```

## Results

«RESULTS»

## Install

```bash
pip install git+https://github.com/sagarthegreat/Infinity           # core: zero dependencies
pip install "forehear[plots] @ git+https://github.com/sagarthegreat/Infinity"   # + figures for the benchmark
```

## Use it

```python
from forehear import Lookahead

async def search_kb(query: str) -> list[dict]:      # your existing retrieval; must be read-only
    return await vector_db.search(query, k=5)

lookahead = Lookahead(retrieve=search_kb)

# wire these to your speech-to-text callbacks
lookahead.speech_started()
lookahead.interim("can i return a damaged")
lookahead.interim("can i return a damaged item")        # retrieval starts here, in the background
delivery = await lookahead.end_of_turn("can i return a damaged item for a refund")

delivery.docs        # context for the LLM, usually ready with zero wait
delivery.reused      # True if it came from a guess made while the user was talking
delivery.wait_ms     # latency retrieval added to this turn
```

Run `python examples/quickstart.py` for a self-contained demo (no keys, no audio).

### Pipecat

```python
from forehear import Lookahead
from forehear.integrations.pipecat import lookahead_processors

tap, inject = lookahead_processors(Lookahead(retrieve=search_kb))
pipeline = Pipeline([
    transport.input(), stt, tap,              # tap: watches interim/eager transcripts
    aggregators.user(), inject, llm, tts,     # inject: adds the context before the LLM
    transport.output(), aggregators.assistant(),
])
```

Works with Pipecat's own speculative inference (`enable_eager_end_of_turn`):
the speculative `LLMContextFrame` gets context for the eager transcript, and the
final frame reuses it without another call. Full bot: [`examples/pipecat_bot.py`](examples/pipecat_bot.py).

### LiveKit Agents

```python
from forehear import Lookahead
from forehear.integrations.livekit import LookaheadAgent, attach

class Support(LookaheadAgent):          # instead of livekit.agents.Agent
    def __init__(self):
        super().__init__(instructions="...", lookahead=Lookahead(retrieve=search_kb))

agent = Support()
attach(session, agent.lookahead)        # feeds interim transcripts from the AgentSession
await session.start(agent=agent, room=ctx.room)
```

Full agent: [`examples/livekit_agent.py`](examples/livekit_agent.py).
Both adapters are tested against the real frameworks in CI.

### Tuning

| knob | default | what it does |
|---|---|---|
| `policy` | `StablePrefix()` | when to guess: every hypothesis with 3+ content words and a new one |
| `policy=Adaptive(budget=3.0)` | | holds calls/turn under a budget; turns itself off when retrieval is already fast |
| `validator` | `TokenCoverage(0.8)` | when a guess may stand in for the final query |
| `validator=ResultOverlap(probe, threshold=0.8)` | | reuse only if a cheap first stage returns the same top-k: about 1/3 of the recall loss for most of the savings |
| `max_inflight` | `2` | concurrent guesses; the oldest is cancelled when a better one arrives |
| `hedge` | `False` | if the best guess is still running at end of turn, also start a fresh call and use whichever wins |

Speculative calls are discarded all the time, so route only **read-only**
retrieval through forehear, never bookings, writes or memory updates.

## The benchmark

There was no open way to measure this, so forehear ships one. It uses **real
human speech, real streaming-ASR revisions and real retrieval**, and is
deterministic and CPU-only:

* «N_TURNS» questions **read aloud by people** (HeySQuAD), streamed through
  Vosk in 100 ms chunks. Every interim hypothesis is recorded, including
  revisions such as "what didn't like her" → "what did microsoft".
* Retrieval over all 19,831 SQuAD v2 paragraphs (BM25, or dense with `--retriever dense`).
* The production `Controller` replayed on a virtual clock, with latency profiles
  fitted to published measurements and paired draws across policies.
* Metrics borrowed from hardware prefetching (coverage, accuracy, lateness),
  plus cost (calls/turn) and quality (recall@k vs. the final transcript).

```bash
forehear bench                      # full matrix, a few minutes, writes results/
forehear replay --index 42          # millisecond timeline of one turn
```

Methodology, metrics and limitations: [`docs/benchmark.md`](docs/benchmark.md).
Bring your own traces: [`data/README.md`](data/README.md).

## How it works

```
 STT / turn detector ──events──▶ Controller (sans-IO state machine) ──actions──▶ runtime or simulator
   SPEECH_START, INTERIM,          ├─ Policy:    "fire now, with this query"      Start / Cancel / Deliver
   EAGER_END_OF_TURN,              └─ Validator: "may this result stand in
   TURN_RESUMED, END_OF_TURN                      for the final query?"
```

The controller does no I/O: it turns timestamped events into `Start`,
`Cancel` and `Deliver` actions. The asyncio runtime executes those for real,
and the benchmark executes them on a virtual clock, so **what you benchmark is
what you ship**. Design notes, and how to write your own policy:
[`docs/design.md`](docs/design.md).

## Prior art

A literature and code review is in [`docs/research/`](docs/research/landscape-review.md). In short:

| | retrieval on partial speech | open code | open benchmark | waste reported |
|---|---|---|---|---|
| Stream RAG (Meta/CMU, 2025) | ✅ web search / KG | promised | AudioCRAG (partial) | ❌ |
| "When does streaming tool use help?" (2026) | ✅ analysis (CRAG) | ❌ | ❌ | bound only |
| Hiding tool latency on-device (2026) | ✅ tool calls | ❌ | ❌ | ❌ |
| LiveKit preemptive generation / Pipecat speculative inference | ❌ (LLM only) | ✅ | ❌ | ❌ |
| EVA-Bench (ServiceNow, 2026) | ❌ (lists speculation as a limitation) | ✅ | ✅ end-to-end | ❌ |
| **forehear** | ✅ any retriever | ✅ | ✅ real speech + real ASR | ✅ |

## Roadmap

* Multi-turn spoken dialogue traces (DSTC10 Track 2) and more ASR engines
  (Deepgram, AssemblyAI, Whisper-streaming, Parakeet).
* Learned policies: predict "the query has converged" from the hypothesis stream.
* Query completion: retrieve for the *predicted* end of the sentence, not the prefix.
* An end-to-end run inside EVA-Bench (needs API keys; contributions welcome).

## Contributing, citing, license

Contributions are very welcome, especially new policies with benchmark results:
see [CONTRIBUTING.md](CONTRIBUTING.md). To cite forehear, use
[CITATION.cff](CITATION.cff). Code is Apache-2.0; benchmark data keeps its
upstream licenses (HeySQuAD CC BY 4.0, SQuAD CC BY-SA 4.0), see [NOTICE](NOTICE).
