# Design

The forehear core is ~1,500 lines of dependency-free Python (half of it docstrings). This page explains how
the pieces fit together, and why.

## The problem in one timeline

```
user speaks ─────────────────────────────▶| silence |
interim ASR   "can i"  "can i return a damn"  "can i return a damaged item"
                                                     │
today:                                               └─ end of turn ─▶ retrieve (250-1500 ms) ─▶ LLM
forehear:      speculate ─x  speculate ─x  speculate ──── result ───▶ end of turn ─▶ LLM (0 ms wait)
                         (cancelled)  (cancelled)                    └ validate & reuse
```

Retrieval sits on the critical path of every RAG voice turn, and it starts only
after the turn detector is sure the user has finished. Meanwhile the speech
recogniser has been streaming its best guess of the sentence for seconds.
forehear runs retrieval on those guesses, then validates the guess against the
final transcript before reusing anything.

## Architecture

```
               transcript events                       actions
 STT/turn  ───────────────────────────▶  Controller  ───────────────▶  executor
 detector     SPEECH_START, INTERIM,      (sans-IO,      Start(spec)      asyncio runtime (Lookahead)
              EAGER_END_OF_TURN,           pure)         Cancel(id)       or the benchmark simulator
              TURN_RESUMED, END_OF_TURN     ▲    ▲        Deliver(ctx)
                                            │    │
                                  Policy ───┘    └─── Validator
                       "fire now, with this query"   "may this result stand in
                                                      for the final query?"
```

### The controller does no I/O

`forehear.Controller` never awaits, sleeps or calls a retriever. It consumes
`TranscriptEvent`s and retrieval completions (`on_result`, `on_error`) and
returns actions. All timing comes from event timestamps.

This one decision pays for itself several times over:

* **What you benchmark is what you ship.** The benchmark replays recorded
  turns through the same `Controller` class on a virtual clock, so its numbers
  describe the production code path, not a re-implementation.
* **Determinism.** Every edge case, such as stale results, superseded calls,
  results arriving after end of turn, or a new turn starting before the last
  one was delivered, is a plain unit test with literal timestamps.
* **Portability.** The asyncio runtime is 150 lines. A trio, threaded or Rust
  host only needs to execute three action types.

### Policies decide *when* and *what*

A `Policy` sees each event plus a read-only `TurnView` (hypotheses so far,
queries already fired, time of the last fire) and returns a query or `None`.
Policies hold no timers and do no cancellation; the controller enforces:

* **de-duplication:** the same normalised query is never in flight twice;
* **`max_inflight`:** at capacity, either cancel the oldest call (default:
  newer hypotheses are better guesses) or drop the new one (`when_full="drop_new"`,
  which suits slow retrievers);
* **`max_speculative_calls`:** an optional hard per-turn budget.

Built-in policies:

| policy | fires | idea from |
|---|---|---|
| `FinalOnly` | never | today's default |
| `EagerEndOfTurn` | on the eager end-of-turn signal | Deepgram Flux / LiveKit preflight / Pipecat eager strategies |
| `FixedInterval(ms)` | the latest hypothesis every *ms* | Stream RAG fixed-interval mode |
| `StablePrefix(agreement=n)` | when the words the last *n* hypotheses agree on gain a new content word | LocalAgreement in streaming speech translation |
| `Adaptive(budget=b)` | `StablePrefix` at a level chosen from measured cost, coverage, lateness and retriever speed | feedback-directed hardware prefetching |

### Validators decide reuse

At end of turn every live speculative call is scored against the final
transcript:

* `ExactMatch`: normalised string equality (LiveKit and Pipecat use this for
  speculative LLM replies).
* `TokenCoverage(t)`: `min(recall, precision)` over content-word sets. It
  rejects truncated guesses ("capital" for "capital of france") and guesses
  built on words the recogniser later revised ("red bull founder" for "who
  founded rare"). This is the default, at `t = 0.8`.
* `ResultOverlap(probe, k, t)`: run a *cheap* first stage on both queries and
  compare the top-k ids. This generalises Stream RAG's reflector. Use it when a
  slow stage (reranker, remote KB, web search) sits behind a fast one.

Selection at end of turn:

1. A **completed** accepted call exists: deliver it now (wait = 0).
2. Else an **in-flight** accepted call exists: wait for it (a *late* hit).
   With `hedge=True`, also start a fresh call on the final transcript and
   deliver whichever finishes first.
3. Else cancel everything and retrieve on the final transcript. This is
   never worse than not speculating, apart from the calls already spent.

### Safety: read-only only

Speculative calls run on guesses and are discarded all the time. Route only
side-effect-free retrieval through forehear: vector search, keyword search,
read-only APIs. Never route bookings, writes or memory stores through it.
This is the failure mode reported against speculative LLM runs in other
frameworks (see `docs/research/`).

## Writing a policy

```python
from forehear import Policy, TranscriptEvent, EventKind, TurnView
from forehear.text import content_words

class QuestionShaped(Policy):
    """Fire once the hypothesis looks like a complete question."""
    name = "question_shaped"

    def propose(self, event: TranscriptEvent, view: TurnView) -> str | None:
        if event.kind is EventKind.EAGER_END_OF_TURN:
            return event.text
        if event.kind is EventKind.INTERIM and len(content_words(event.text)) >= 3:
            last = event.text.split()[-1]
            if last not in {"the", "a", "of", "for", "to", "and", "in"}:
                return event.text
        return None
```

Then measure it against the built-ins:

```python
from forehear import Controller
from forehear.bench.runner import PolicySpec, run_matrix, standard_policies

specs = [*standard_policies(), PolicySpec("question_shaped", lambda: Controller(QuestionShaped()), "")]
```

(`forehear bench` runs `standard_policies()`. Contributions of new policies
with benchmark results are very welcome.)
