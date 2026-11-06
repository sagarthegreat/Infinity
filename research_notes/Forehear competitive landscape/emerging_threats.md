# Emerging and adjacent threats to forehear (flagged earlier but not yet examined), as of 2026-11-06

Scope note: this file adds to direct_oss_competitors.md, voice_frameworks.md, market_adoption.md and academic_systems.md and does not repeat them. Where an item was already covered, only new facts or corrections are listed here, with a pointer to the earlier file.

Method caveat: `gh api` returned HTTP 403 ("GitHub access to this repository is not enabled for this session") for livekit/agents, pipecat-ai/pipecat and every third-party repo. I used two workarounds instead: WebFetch of the github.com pages, and read-only shallow clones (`--depth 1`) into the scratchpad. The clones were never executed. Because they are depth-1, the last-commit dates show only the HEAD commit.

## Q1. Deepgram's acquisition of Daily, and the Real-Time Context Standard (RCS)

### Takeaway
RCS does not overlap with forehear. RCS 0.1 is an alpha text-markup convention for paralinguistic *perception* readings (tone, speech rate) at the head of the user message, and *expression* tags in the reply. It explicitly allows only the "final reading of a turn", and it does not mention retrieval, RAG, interim transcripts or speculation. Deepgram and Daily published no Pipecat roadmap beyond "open source, BSD-2, vendor-neutral, independent foundation", and the foundation has no charter yet. Threat today: **irrelevant (RCS)**. Long term, **the Deepgram+Pipecat platform is the party best placed to subsume forehear's function**, because it now owns both the streaming STT interims and the framework. There is no public signal that it plans to.

### Cited Findings
**Deal facts (new detail beyond market_adoption.md)**
- The Deepgram blog is dated October 29, 2026. "Following the acquisition, the Daily team will join Deepgram". Kwindla Hultman Kramer becomes Deepgram's Head of Open Source: "Keeping Pipecat open was fundamental to our decision to join Deepgram". — [Deepgram blog](https://deepgram.com/blog/daily-pipecat-deepgram)
- Pipecat "will remain fully open source and free to all developers under its existing BSD V2 license". The companies are "establishing an independent Pipecat Foundation". Deepgram commits to "keeping all of Pipecat open source and vendor neutral". The blog gives no specific roadmap and does not mention Pipecat Cloud. — [Deepgram blog](https://deepgram.com/blog/daily-pipecat-deepgram)
- Scott Stephenson (CEO): "Acquiring Daily allows us to bring that expertise together to tackle the whole voice system" — [Deepgram blog](https://deepgram.com/blog/daily-pipecat-deepgram)
- TechCrunch (Ivan Mehta, 2026-10-29) quotes Kramer: "We never thought about Pipecat as a voice toolkit… We thought about it as the toolkit we needed to build this new kind of AI-native software". It quotes Stephenson: "It's great if you're using Deepgram models, but I want you to be using the best models for your use case". TechCrunch paraphrases Stephenson as describing "a context bus that connects all the parts". — [TechCrunch](https://techcrunch.com/2026/10/29/deepgram-acquires-pipecat-maker-daily-to-bolster-its-voice-ai-infrastructure/)
- On governance, an independent analyst writes: "Neither post names a steering committee member, publishes a charter, or gives a date for the foundation", and "Nobody has said who will hold the Pipecat trademark, the `pipecat-ai` GitHub organisation or the package-publishing keys". He also notes that "Deepgram has given no availability date for its Voice Agent Platform". — [Rajesh Beri, The Daily Brief, 2026-10-31](https://www.beri.net/article/deepgram-daily-acquisition-pipecat-foundation-webrtc-telephony-voice-agents-customer-continuity)

**What RCS specifies**
- The official spec page "documents RCS 0.1, an alpha", says versions may change incompatibly before 1.0, and says Pipecat 1.15.0+ implements it. — [Pipecat docs: Real-time Context Standard](https://docs.pipecat.ai/api-reference/standards/real-time-context-standard)
- **Format.** Perception readings are a parenthesized prefix such as `([tone frustrated=0.86, neutral=0.10],[speech_rate value=4.1])`. "The reading comes first in the user's message, followed by a space and the words." Expression tags go inline in the reply: `<<delivery>>`, `^^words^^`, `[[sound]]`, `[[pause N]]`. — [Pipecat docs](https://docs.pipecat.ai/api-reference/standards/real-time-context-standard)
- **Timing is per turn and final only.** "A producer MUST write only the final reading of a turn." There is no shared vocabulary: "RCS 0.1 has no shared vocabulary of signals: a producer names its own." — [Pipecat docs](https://docs.pipecat.ai/api-reference/standards/real-time-context-standard)
- **Retrieval, RAG, knowledge, interim transcripts and speculation** are all not mentioned in the spec page. They are also absent from the Deepgram announcement. — [Pipecat docs](https://docs.pipecat.ai/api-reference/standards/real-time-context-standard); [Deepgram blog](https://deepgram.com/blog/daily-pipecat-deepgram)
- **RCS roadmap.** Planned context types include "**Intent**: when someone means to speak, and whether what they said needs a response", plus diarization. Proposals go through GitHub issues. — [Pipecat docs](https://docs.pipecat.ai/api-reference/standards/real-time-context-standard)
- TechCrunch's description: "The protocol defines metadata like context from the audio, like a whisper… instructions for a language model on how it can use those signals… guidance on how the response should sound." — [TechCrunch](https://techcrunch.com/2026/10/29/deepgram-acquires-pipecat-maker-daily-to-bolster-its-voice-ai-infrastructure/)

**Reference demo (pipecat-ai/realtime-context-standard-demo)**
- 38 stars, 6 forks, 40 commits. HEAD commit 2026-10-29 by Jon Taylor. No LICENSE file at the repo root, but the file headers read "Copyright (c) 2026, Daily … SPDX-License-Identifier: BSD 2-Clause License". — [GitHub](https://github.com/pipecat-ai/realtime-context-standard-demo); local clone
- Its pipeline: "Deepgram Flux (STT) → Tone reader → avatar listener → PhoneLLM Mini on Baseten (LLM) → Tone tagger → ElevenLabs v4 … → lipsync". — [README](https://github.com/pipecat-ai/realtime-context-standard-demo)
- The demo does use interim transcripts in one place, for avatar reactions rather than retrieval. The avatar listener "reads the user's newest words from Flux's interim transcript as each phrase ends, at most every second and a half… A reading that comes back after the user has said much more is dropped". — [README](https://github.com/pipecat-ai/realtime-context-standard-demo)
- `server/prefetch.py` is **not** speculation. It downloads the Tone reader, the tagger and the backchannel models at image build time ("The models each call loads, and their download ahead of the call"). — local clone of `server/prefetch.py`

### Inferences
- RCS solves a different problem (paralinguistics lost between models) and works at a different time (the final reading of a turn). It does not compete with forehear's function or subsume it.
- Two weak signals point toward pre-EOT context: the planned "Intent" type, and the Pipecat team's own interim-triggered, stale-dropping avatar calls. These suggest the team is comfortable with interim-driven side calls. Nothing points toward retrieval. My judgement is that a native "speculative retrieval on interims" feature from Deepgram/Pipecat is possible but unannounced. The foundation's lack of a charter and roadmap makes the timing unknowable.
- Practical implication: if forehear emitted its context as an RCS-compatible prefix or reading, that would cost little. RCS's "final reading only" rule means speculative retrieval results should be injected only at EOT, which matches forehear's design.

### Gaps
- No Pipecat Foundation charter or roadmap has been published. Pipecat Cloud's future is unstated.
- I could not read the RCS GitHub issues to see whether retrieval or partial-turn context has been proposed.

## Q2. LiveKit Agents PR #7724 (Moss knowledge-base plugin)

### Takeaway
The PR is still open and has no human maintainer review. The only reviews come from the Devin bot. It adds `livekit-plugins-moss`, an in-process index from InferEdge's Moss, with about 1 ms search, and states the design rule "retrieval in `llm_node`, not `on_user_turn_completed`". It does not touch interim transcripts. Threat: **substitute, medium**. If a small or static knowledge base searches in about 1 ms with no network call, starting retrieval early saves almost nothing. If the PR merges, LiveKit's official answer to "RAG under preemptive generation" becomes "make retrieval fast and put it in the speculated branch", not "speculate the retrieval".

### Cited Findings
- **Status and metadata:** open. Author rafaelbeckel, branch `feat/moss-knowledge-base`, 18 commits. Opened 2026-10-11, last activity 2026-11-05. It replaces PRs #4812 and #3826. "At least one approving review is required"; no LiveKit maintainer review or approval is visible. — [PR #7724](https://github.com/livekit/agents/pull/7724)
- **Design:**
  - `KnowledgeBase` is an `llm.Toolset`. `setup()` loads indexes in the background, and the tool waits at most 5 s for the load.
  - `add_context()` injects passages as a system message into the copy of the chat context that `llm_node` receives, so the passages stay out of the history.
  - It skips filler messages, and on short follow-ups it searches using earlier turns. It keeps recent passages from the last three searched turns.
  - It "adds nothing while the index loads".
  - Dependency: `moss>=1.15.0` with a native wheel, `inferedge-moss-core`.
  - Source: [PR #7724](https://github.com/livekit/agents/pull/7724)
- **Latency claim:** a search "takes about a millisecond and makes no network request". No benchmark is attached. — [PR #7724](https://github.com/livekit/agents/pull/7724)
- **Hook rule:** it belongs in `llm_node` because changes in `on_user_turn_completed` invalidate the preemptive reply, and because text input skips that hook. — [PR #7724](https://github.com/livekit/agents/pull/7724) (also in voice_frameworks.md)
- **Interims:** the PR page does not discuss interim transcripts. Retrieval runs whenever `llm_node` runs, which is at preflight or final under preemptive generation (see voice_frameworks.md). — [PR #7724](https://github.com/livekit/agents/pull/7724)
- **Review thread** (new; voice_frameworks.md could not read it):
  - Every comment is either a Devin bot finding (closed clients kept alive; exception types; a version bump to 1.8.11 and a raised `livekit-agents>=1.8.11` floor "bypasses the release workflow") or the author's reply.
  - The author fixed the first two (c50a1dc, f9a5ca9) and declined the version items on 2026-11-05.
  - Source: [PR #7724](https://github.com/livekit/agents/pull/7724)

### Inferences
- The PR is a commercial vendor's (InferEdge/Moss) contribution and is unreviewed after nearly 4 weeks. Merging is plausible, since LiveKit hosts many vendor plugins, but it is unconfirmed.
- forehear's value scales with retrieval latency. The Moss pattern removes that latency for knowledge bases that fit in agent memory. forehear's remaining territory is remote or large indexes (vector DB over the network, 50–800 ms), rerankers, and tool or API lookups. forehear's LiveKit adapter should probably also hook `llm_node` to avoid breaking preemptive reuse. That is consistent with voice_frameworks.md.

### Gaps
- Merge likelihood and LiveKit maintainers' views are unknown, because there are no human reviews.
- I found no independent measurement of Moss's ~1 ms claim, or of the index sizes it holds.

## Q3. Pipecat issue #6511 and iamdgarcia/pipecat-speculative-prefill

### Takeaway
This is a small, honest, MIT-licensed prototype by a Pipecat contributor. It covers speculative KV prefill from interims, not retrieval. The issue is still open with 0 comments and no maintainer response. Threat: **complement**. It competes with forehear only for the same "interim tap" integration slot and for maintainer attention, and it validates forehear's integration point.

### Cited Findings
- **Issue status:** open since 2026-11-02 (author iamdgarcia). No labels, assignees, linked PRs or comments; one 🚀 reaction (yukiobata). — [issue #6511](https://github.com/pipecat-ai/pipecat/issues/6511)
- **Design:**
  - `SpeculativePrefillTap` sits between STT and the user context aggregator and forwards interim, eager and final transcriptions.
  - `SpeculativeLLMService` applies the chat template to the live context plus the partial text, then keeps the longest common prefix (LCP) in the KV cache and evaluates only the new tokens. If the final transcript diverges, the cache rewinds to the common prefix and recomputes the divergent tail.
  - `PrefixCacheWarmer` sends `max_tokens=1` requests to vLLM/SGLang/llama.cpp for server-side prefix caching, with "no KV handoff".
  - Prototype built against pipecat 1.15.1.dev13.
  - Sources: [repo README](https://github.com/iamdgarcia/pipecat-speculative-prefill); [issue #6511](https://github.com/pipecat-ai/pipecat/issues/6511)
- **Numbers:** a single Intel laptop, CPU-only, fp32, Qwen2.5-0.5B-Instruct. TTFT is measured from the final transcription. 53-token prompt: 1155.8 → 317.0 ms (−73%). 873-token prompt: 10868.3 → 367.8 ms (−97%). Incremental prefill matches full-prefill logits ("max difference 0.0"). The turn after a tool call hit "81% cache reuse". — [README](https://github.com/iamdgarcia/pipecat-speculative-prefill)
- **Maturity:**
  - MIT. 1 star, 0 forks, 3 commits (the earlier note said 2, so one was added since). The issue cites 37 tests, including a real-model end-to-end test.
  - No releases. The repo's Packages section is empty, and direct_oss_competitors.md found the name not on PyPI.
  - The README calls `TransformersPrefillBackend` "the tested path".
  - Stated limits: Hermes/Qwen tool-call format only, one speculative service per model, multimodal flattened to text.
  - Sources: [repo](https://github.com/iamdgarcia/pipecat-speculative-prefill); [issue #6511](https://github.com/pipecat-ai/pipecat/issues/6511)
- **Retrieval/RAG:** not mentioned. — [repo](https://github.com/iamdgarcia/pipecat-speculative-prefill)

### Inferences
- The −97% headline comes from a CPU-bound 0.5B model where prefill dominates. With GPU or hosted LLMs, absolute savings would be far smaller. Hosted APIs (OpenAI, Anthropic) cannot use the in-process KV handoff at all.
- It composes naturally with forehear. Early retrieval could make the retrieved passages part of the prefilled prefix, as latency_substitutes.md also infers. If Pipecat maintainers ever accept a first-party "interim tap" processor, both projects would benefit.

### Gaps
- Maintainer reaction is unknown, since there are 0 comments.
- No GPU or hosted-model numbers are available.

## Q4. Tazo Labs, "Speculative tool calling: cutting voice AI agent latency"

### Takeaway
This is a commercial blog post by Kodimo, Inc. (DBA Tazo Labs), dated Oct 2, 2026. It argues for firing likely read-only tool calls during speech and committing them only on an exact-match later call. There is no code, SDK or benchmark. The ~480 ms figure is an illustrative calculation, not a measurement. Threat: **adjacent commercial, low–medium**. It sells the *gating* signal ("is the argument complete?") from its audio decision model, which could become a trigger source for forehear-like systems rather than a competitor to them.

### Cited Findings
- **Author and date:** "Tazo Labs", Oct 2, 2026; Kodimo, Inc. DBA Tazo Labs. It was posted to HN on 2026-10-13 and drew 3 points. — [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai); [HN item 50069985](https://news.ycombinator.com/item?id=50069985)
- **Code:** no repo, SDK or benchmark release. The inline Python-style sketch is illustrative. — [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- **Worked example, verbatim:** "Take an 800 ms CRM lookup fired 1.2 s before the LLM would have issued it… At a 60% hit rate, that's about 480 ms off the average turn that uses this tool… at the cost of about 0.67 wasted lookups per useful one." These are assumed inputs fed into the article's own formula. — [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- **Mechanism:**
  - Validation is an exact match: a cached result is used only if the LLM issues the same call at end of turn.
  - Leftover speculative calls are dropped at commit time.
  - It warns that raw partials can fire on wrong values, and cites NVIDIA acting only on interims marked stable.
  - It treats "is the argument settled" largely as an acoustic question.
  - Source: [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- **Product pitch:** "a small model that listens to the audio and decides what happens next". A check such as whether the caller has given a complete order number is "one more question in the request… answered from the audio with a calibrated probability you can set a threshold on". — [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- It cites knowledge-base lookups and VoiceAgentRAG as related. Other numbers and the SHANKS citation are already in market_adoption.md. — [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)

### Inferences
- RASSG's paper uses a "Speculative Tool Calling" baseline (see academic_systems.md). Under its cost metric, that baseline had the fastest delay but a 50–81% stale rate. If that baseline matches Tazo's eager pattern, which I have not verified, it quantifies Tazo's own warning about firing on raw partials.
- Tazo's exact-match commit rule is stricter than forehear's overlap-based reuse validation. forehear could cite Tazo's formula (saving ≈ hit rate × head start, capped by lookup latency) and show measured values for it.

### Gaps
- I could not confirm that RASSG's "Speculative Tool Calling" baseline is Tazo's method specifically.
- Tazo has published no measured hit rates.

## Q5. Corti docs and The Neural Base "parallel prefetch": is the pattern becoming documented practice?

### Takeaway
Partly. Speculative *generation* on interim text is now written up in vendor docs (Corti) and tutorial content (The Neural Base). Both hedge it heavily ("starting point for exploration rather than a production-ready recipe"), and neither covers retrieval. Speculative *retrieval* on interims still appears only as tool-call advice (Tazo), as eager-EOT advice for RAG (Deepgram Flux, see commercial_platforms.md), or in app code (gravitre, Q6). Threat: **irrelevant as competitors**. As market signal, they show the pattern is becoming familiar.

### Cited Findings
- **Corti, "Build a conversational agent":**
  - The guide describes "speculative prefetch for fast responses": the agent "fires a stateless request while the user is still speaking", so "the response is often ready the instant they stop".
  - On the first interim it schedules "a short debounce (200 ms)". If speech continues, "the timer resets and a fresh call fires with the updated text".
  - The call is "intentionally stateless" and omits `contextId`, because sending partial text with a `contextId` "would corrupt the real thread". The provisional response is "replaced in-place by the real contextual response".
  - Caveats: "response quality and timing can vary", and "a starting point for exploration rather than a production-ready recipe".
  - No date, no latency target, and no retrieval discussion.
  - Source: [docs.corti.ai](https://docs.corti.ai/stt/guides/agent-conversational)
- **The Neural Base, "Parallel prefetch":**
  - Recommends prefetching "LLM responses and TTS audio in parallel while the user is still speaking"; retrieval is not mentioned.
  - Trigger threshold: confidence >0.85. The team note says "0.8 triggers too many speculative calls in production".
  - Sends 3–5 candidate prompts and reranks them by "semantic similarity to final transcript"; prefetched audio plays only if similarity >0.9.
  - It admits the pattern "multiplies API calls by 3–5x", but its own cost figures conflict ($450/mo vs $2,000–5,000/mo).
  - The latency claim ("1.6s to 400–600ms in production deployments") is unsourced.
  - No author is named. It is "Verified April 2026".
  - Source: [theneuralbase.com](https://theneuralbase.com/voice-ai/learn/intermediate/parallel-prefetch/)

### Inferences
- The two documents differ on the details: Corti uses a debounce with a single call, while The Neural Base uses a confidence gate with many candidates. Both validate softly or not at all (Corti replaces the result in place; The Neural Base uses a cosine threshold). Neither counts waste beyond rough cost estimates.
- That gap is exactly the "measure whether it pays off" layer forehear's benchmark provides. forehear's benchmark could test Corti's 200 ms debounce rule directly as a policy.

### Gaps
- I found no vendor doc beyond Deepgram's eager-EOT guide that recommends *retrieval*, rather than generation, on interims.

## Q6. Newly found code: what each actually implements

### Takeaway
oneiron, hhgoa2, kairos and lego-ai are already characterized in direct_oss_competitors.md §7, and nothing contradicts those notes. The genuinely new finding is **cesarbohjr/gravitre-saas-backend**. It is a production SaaS backend (gravitre.app) that hand-builds, inside Pipecat, interim-triggered read-only knowledge retrieval and embedding warm-up with a 150 ms debounce and cancel-on-new-interim. It pairs this with speculative LLM generation on Flux probable-EOT, adoption rules, and waste counters. It is not a library and has no licence. Threat: **low as a competitor; strong evidence that practitioners hand-roll forehear's function**, so it is either a potential user or proof that the problem is real.

### Cited Findings
**gravitre-saas-backend (new detail)**
- **Repo:** public, 0 stars, 0 forks, 4,637 commits, no LICENSE file (so all rights reserved by default). Very active: HEAD commit 2026-11-06 by "CesarJr". AGENTS.md: "Next.js app in `apps/web`, FastAPI backend in `backend`, production at https://gravitre.app". — [GitHub](https://github.com/cesarbohjr/gravitre-saas-backend); local clone
- **`speculative_prefetch.py` (441 lines), `SpeculativePrefetchProcessor`, a Pipecat `FrameProcessor`:**
  - On `InterimTranscriptionFrame` (≥ `min_chars`, default 8, and changed since the last partial), after `PREFETCH_DEBOUNCE_S = 0.15`, it runs read-only warm-up:
    - dialogue settings;
    - the tool-retrieval query embedding;
    - tool document embeddings;
    - knowledge retrieval via `UnifiedRetrievalService.retrieve_knowledge_rows` (`top_k=4`), only when the text is not write-shaped.
  - A new interim cancels the in-flight task. The debounce exists because "Worker threads cannot be cancelled".
  - Source: [speculative_prefetch.py](https://github.com/cesarbohjr/gravitre-saas-backend/blob/main/backend/app/services/pipecat_voice/speculative_prefetch.py)
- **`speculative_generation.py`:**
  - "Genuine, cancelable speculative LLM generation on probable-EOT", started on Flux `ProposedUserStoppedSpeakingFrame` / `EagerTranscriptionFrame`.
  - The output is "adopted at confirmed end-of-turn, when the final transcript matches… (exact, normalized match — a deliberate, conservative scoping choice…)". Optional `prefix_max_extra_words` adoption covers finals that add a few trailing words. A `strict` mode rejects "trailing qualifiers, negations and corrections" and requires bound conversation, task, approval and context versions to match.
  - Durable writes made while speculating are deferred in a `SpeculativeScope` and replayed only on adoption. "Connector WRITEs… are refused".
  - Counters: "started / adopted / discarded / timeouts / blocked / buffer pauses / wasted seconds".
  - Dated design notes: "Voice-SLO follow-up (2026-09-05)" and "Side effects, bounds and revisions (2026-10)".
  - Source: local clone of `backend/app/services/pipecat_voice/speculative_generation.py`
- **What the prefetch file does not show:** whether the interim-time knowledge rows are consumed at EOT (a cache) or only warm downstream caches. It also does not report a hit or waste rate for retrieval; the waste counters cover generation. — [speculative_prefetch.py](https://github.com/cesarbohjr/gravitre-saas-backend/blob/main/backend/app/services/pipecat_voice/speculative_prefetch.py)
- The same directory has `livekit_candidate.py`, `engine_benchmark.py`, `voice_latency_metrics.py` and `voice_latency_tuning.py`, which suggests the author also evaluates LiveKit. This is not inspected further. — local clone directory listing

**Previously covered items (no change; see direct_oss_competitors.md §7)**
- **oneiron-dev/oneiron:**
  - Rust, Apache-2.0, 0 stars.
  - `SpeculativeSession::observe_partial` fires prefix-only retrieval when the entity/salient-term "MEANING" signature changes, capped at `max_fires`, with optional deadlines.
  - `finalize` either "promotes the last warm pack verbatim" or runs one full pass.
  - Every speculative fire is tagged as wasted-retrieval budget.
  - `voice_cascade/retrieval.rs` provides a `SpeculativeRetrievalBridge` beside Soniox, cancellation and budget modules.
  - No Pipecat or LiveKit adapters.
  - Source: [speculative.rs](https://github.com/oneiron-dev/oneiron/blob/main/crates/oneiron/src/speculative.rs)
- **subham-ryy/hhgoa2:** a single commit (2026-08-22), no licence. Fires at ≥4 words with a 150 ms debounce. Reuse rule: exact match, prefix, or Jaccard ≥0.60, otherwise "cancel & fire final pass". — [speculative.py](https://github.com/subham-ryy/hhgoa2/blob/main/src/stt/speculative.py)
- **cheshtarajput098-arch/kairos:** a PRISM hackathon entry, MIT. `SpeculationManager(max_speculative=3)` cancels on entity revision. Its eval data is LLM-drafted text with synthetic ASR noise. — [README](https://github.com/cheshtarajput098-arch/kairos/blob/main/README.md)
- **rakeshr410/lego-ai:** app code. `speculate.py` posts the words heard so far at `VADUserStoppedSpeakingFrame` or Flux `EagerTranscriptionFrame` and reposts if the final differs ("the guess costs one unused call"). Generation, not retrieval. — [speculate.py](https://github.com/rakeshr410/lego-ai/blob/main/voice/bot/speculate.py)
- **Tool-search correction:** direct_oss_competitors.md lists gravitre only as "an application backend". It is in fact the most complete production-style interim-retrieval implementation found in a Pipecat codebase. It is still unlicensed app code.

### Inferences
- gravitre independently arrived at several of forehear's core ideas:
  - debounce plus cancel on new interims;
  - read-only-only speculation;
  - conservative reuse rules (exact, prefix-extra-words, strict versions);
  - waste counters.
- It took a single developer months of iteration inside a product to get there, which is the build-vs-buy argument for a reusable library.
- Threat ranking within this group: oneiron (technically closest engine, but Rust and no adapters) > gravitre (closest in a Pipecat deployment, but not reusable) > hhgoa2 / kairos / lego-ai (hackathon or app code).

### Gaps
- Whether gravitre consumes interim-time retrieval results at EOT, and its measured hit or waste rates. I did not read `cognitive_llm.py` or `voice_turn_trace.py` in full.
- The gravitre author's identity and commercial status beyond the gravitre.app domain.

## Q7. Heartbeat Thinking (Ant International) and RASSG (Beihang)

### Takeaway
Both are already summarized in academic_systems.md (mechanism, numbers, authors). New facts: RASSG's repo is a one-commit research release (v1.0.0, package `dualclock`, numpy/scipy/torch, synthetic ReCAST data and checkpoints via Git LFS, no licence). It does no retrieval. Heartbeat still has no code. Neither is a library; both are **complements, and benchmark baselines forehear could reproduce**. Heartbeat is the closer mechanism: a fixed 500 ms interval on partial ASR, ≤2 in flight, cancellation at end of speech, and LLM-based reuse validation.

### Cited Findings
- **Heartbeat Thinking** (arXiv 2610.26233, 19 Oct 2026, Ant International):
  - A Thinker LLM runs every 500 ms on the latest partial ASR, with K=2 concurrent. Jobs are cancelled at VAD end; the Responder validates and reuses results with ReAct.
  - FDBench v3 latency 6.90 → 4.39 s, but small accuracy drops on AudioCRAG (57.24% → 55.49%) and SpeechFCEval (67.95% → 66.85%), and about 4% hallucination from outdated speculative results.
  - Cost and waste accounting is left as future work. No code repository is linked.
  - Sources: [arXiv HTML](https://arxiv.org/html/2610.26233); details in academic_systems.md
- **RASSG** (arXiv 2610.14659, 10 Oct 2026, Daijin Hu and Xi Wang, Beihang):
  - Launches after 3 consecutive identical argument hypotheses; cancels using calibrated invalidity risk × cost before the irreversibility point.
  - Stale rate / delay: ReCAST 3.15% / 3.676 s; FDB-v3 57% / 11.072 s; Audio2Tool 54.65% / 8.797 s.
  - Sources: [arXiv HTML](https://arxiv.org/html/2610.14659); table in academic_systems.md
- **RASSG repo (new):**
  - 0 stars, a single commit "Release RASSG code and ReCAST data" on 2026-09-24. `pyproject.toml` is `name = "rassg"`, `version = "1.0.0"`, dependencies numpy/scipy, optional torch, packaging `src/dualclock`.
  - Modules include `survival_gate.py`, `calibration.py`, `claim_model.py`, `baselines.py`, `controller.py`.
  - The README says `data/recast/` holds "synthetic audio, manifests, annotated traces, arrival streams, and cached model predictions" (Git LFS), and links Audio2Tool and Full-Duplex-Bench. No licence file. A grep of `src/` found no retrieval code and no named ASR engine.
  - Sources: [GitHub](https://github.com/daijinhu/RASSG); local clone

### Inferences
**How they would map onto forehear's benchmark (4,018 real HeySQuAD recordings, Vosk interims). These are untested inferences.**
- **Heartbeat ≈ forehear's fixed-interval timer policy at 500 ms with a concurrency cap of 2.**
  - The timer and cap transfer directly. Its LLM-Thinker trigger and ReAct validation would replace forehear's cheap rule and overlap validator at much higher cost per call.
  - In a retrieval-only benchmark, the comparable piece is the timer. It would likely land close to forehear's timer results.
  - Its −36% end-to-end latency includes LLM reasoning and tool time, which forehear's retrieval-only accounting does not measure.
- **RASSG's launch rule ≈ a LocalAgreement-3 stability policy.**
  - academic_systems.md already notes that on retrieval, where staleness is free and cancellation is cheap, agreement gating trades latency for staleness that does not matter. That predicts RASSG's launch rule would trail forehear's timer/StablePrefix policies on time-to-ready in forehear's benchmark.
  - Its learned survival gate needs per-argument annotations (`claim_model`, `annotated traces`). These don't exist for free-form retrieval queries, so the full method is not directly portable.
- Neither threatens forehear as software. Both are worth citing as baselines. Reproducing "Heartbeat-timer" and "RASSG-agreement-3" policies inside forehear's harness would strengthen forehear's benchmark claims cheaply.

### Gaps
- No Heartbeat code exists, so the timer/cap mapping is from the paper only.
- RASSG's repo licence is absent, so reusing its code or data inside forehear's harness is legally unclear (all rights reserved).

## Q8. Threat ranking (highest first)

### Takeaway
None of these items is a direct competitor today: a reusable, framework-adapted library doing speculative *retrieval* on interims with validation, waste accounting and a real-speech benchmark. The most consequential items are platform-level: LiveKit making retrieval fast enough not to need speculation (Moss), and Deepgram+Pipecat owning both interims and the framework. The code finds confirm that the need is real.

### Cited Findings
| Rank | Item | What it is | Closeness to forehear's function | Threat class | Status / date |
|---|---|---|---|---|---|
| 1 | Deepgram + Daily/Pipecat (incl. RCS) | STT vendor now owns Pipecat; RCS 0.1 alpha perception/expression markup | RCS: none ("MUST write only the final reading of a turn"). Platform: best placed to build it natively | **Would subsume (long-term, speculative)**; RCS itself irrelevant | Announced 2026-10-29; foundation uncharted — [Deepgram](https://deepgram.com/blog/daily-pipecat-deepgram), [RCS spec](https://docs.pipecat.ai/api-reference/standards/real-time-context-standard), [Beri](https://www.beri.net/article/deepgram-daily-acquisition-pipecat-foundation-webrtc-telephony-voice-agents-customer-continuity) |
| 2 | LiveKit PR #7724 (Moss) | In-process ~1 ms KB search in `llm_node` | Removes the latency forehear hides, for in-memory KBs; no interims | **Substitute (medium)** | Open, unreviewed, 2026-10-11 → 11-05 — [PR](https://github.com/livekit/agents/pull/7724) |
| 3 | oneiron | Rust memory engine with speculative retrieval over ASR partials | Closest engine design (signature gating, fire caps, waste telemetry) | Adjacent/direct-in-mechanism, low adoption | Active, 0 stars — [speculative.rs](https://github.com/oneiron-dev/oneiron/blob/main/crates/oneiron/src/speculative.rs) |
| 4 | gravitre-saas-backend | Production app's Pipecat interim retrieval warm-up + EOT speculative generation | Very close in function, not reusable or licensed | Low (validation signal / potential user) | Active 2026-11-06 — [file](https://github.com/cesarbohjr/gravitre-saas-backend/blob/main/backend/app/services/pipecat_voice/speculative_prefetch.py) |
| 5 | Tazo Labs | Closed product; blog on speculative tool calls | Same idea for tools; no code; illustrative 480 ms | Adjacent commercial (low–medium); possible trigger-signal complement | Blog 2026-10-02 — [Tazo](https://tazolabs.com/blog/speculative-tool-calling-voice-ai) |
| 6 | pipecat-speculative-prefill (#6511) | MIT Pipecat KV-prefill from interims | Same tap point; prefill not retrieval | **Complement** | 3 commits, issue open, 0 comments — [repo](https://github.com/iamdgarcia/pipecat-speculative-prefill), [issue](https://github.com/pipecat-ai/pipecat/issues/6511) |
| 7 | Heartbeat Thinking | Paper; LLM Thinker every 500 ms on partial ASR | Mechanistically close; tools/reasoning; no code | Complement / baseline | arXiv 2026-10-19 — [arXiv](https://arxiv.org/html/2610.26233) |
| 8 | RASSG | Paper + unlicensed research code; agreement-gated side-effecting tools | Policy overlap; no retrieval | Complement / scope boundary | Code 2026-09-24 — [repo](https://github.com/daijinhu/RASSG) |
| 9 | Corti docs, The Neural Base | Guides for speculative generation on interims | Generation only, no retrieval | Irrelevant (market signal) | Corti undated; Neural Base "Verified April 2026" — [Corti](https://docs.corti.ai/stt/guides/agent-conversational), [Neural Base](https://theneuralbase.com/voice-ai/learn/intermediate/parallel-prefetch/) |
| 10 | hhgoa2, kairos, lego-ai | Hackathon / app code | Partial; no adapters | Irrelevant | See direct_oss_competitors.md §7 |

### Inferences
- **Most actionable for forehear:**
  - (a) Make the LiveKit adapter `llm_node`-compatible and state clearly when forehear helps: remote or slow indexes, not ~1 ms in-memory ones.
  - (b) Engage the Pipecat team. Comment on #6511 that an upstream interim tap would serve prefill and retrieval alike, and watch RCS's planned "Intent" type.
  - (c) Add Corti-200 ms-debounce, Heartbeat-500 ms/K=2 and RASSG-agreement-3 policies as named baselines in forehear's benchmark.
  - (d) Position against the hand-rolled gravitre-style approach ("you will otherwise build this yourself").
- Ranking ranks 1–2 above the code-level items is a judgement. A platform default (fast in-process KBs; a native Pipecat feature) can shrink forehear's addressable use more than any small repo can.

### Gaps
- No evidence on whether Deepgram plans native pre-EOT retrieval. The rank-1 "subsume" risk is my structural inference, not reported intent.
- LiveKit maintainers' stance on #7724 is unknown.
