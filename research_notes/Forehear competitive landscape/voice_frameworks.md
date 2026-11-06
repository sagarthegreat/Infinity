# Open-source voice agent frameworks as competitors/substitutes for forehear (speculative RAG on interim ASR transcripts)

Method and scope: this note updates `/home/user/Infinity/docs/research/notes/open_source_frameworks.md` (written 2026-11-03). That note's findings on LiveKit preemptive mechanics, Pipecat 1.9 speculation, jambonz, TEN, Bolna, Vocode, Unmute, FastRTC, Ultravox and the OpenAI Agents SDK still hold unless a section here says otherwise. Re-verification:
- Default branches were shallow-cloned on 2026-11-06: LiveKit agents HEAD `055744e` (2026-11-05, version `1.8.11`); agents-js HEAD `6769e16` (`agents/package.json` 1.9.5); Pipecat HEAD `6fa9cf2` (2026-11-05, `git describe` = `v1.15.0-256`); NVIDIA ace-controller; NVIDIA nemotron-voice-agent; NVIDIA-NeMo labs-Voice-Agent; Cartesia Line; Dograh; TEN; jambonz-feature-server.
- GitHub REST `repos/*` and issue-comments endpoints were blocked. Star counts and issue/PR bodies come from the GitHub **search** API, queried 2026-11-06.
- Download counts come from pypistats.org and api.npmjs.org on 2026-11-06.
- Code was grepped only, never executed.

Terms: **preemptive/speculative generation** = starting the LLM call before end-of-turn (EOT) is confirmed. **Speculative retrieval** = running RAG/vector search (or retrieval tools) on interim or partial transcripts before EOT.

## Q1. Which frameworks run any retrieval or tool calls before end-of-turn, and on what trigger?

### Takeaway
No mainstream framework runs retrieval on **interim** transcripts. LiveKit and Pipecat speculate the LLM call only at "likely-EOT" moments: LiveKit on an STT final/preflight segment, Pipecat on an STT or vendor eager-EOT prediction. Both explicitly **refuse to execute tool calls** speculatively. So retrieval exposed as an LLM tool gets no head start, and LiveKit's documented RAG hook (`on_user_turn_completed`) actually **cancels** the speculation.

Retrieval does run early in one case: when it sits inside the speculated branch (LiveKit `llm_node`, or a Pipecat processor between the aggregator and the LLM). Even then it starts at the preflight/eager-EOT moment, not on interims. LiveKit's pending Moss plugin PR (#7724) turns this "retrieve inside `llm_node`" pattern into official guidance. That makes it the closest native substitute for forehear, though it runs at preflight and is in-memory only. NVIDIA, which had the only interim-triggered speculative LLM (`ENABLE_SPECULATIVE_SPEECH`), has archived that code.

### Cited Findings
**LiveKit Agents (Python 1.8.11 / Node 1.9.5)**
- `PreemptiveGenerationOptions` is unchanged at HEAD: `enabled: True` by default, `preemptive_tts: False` ("only LLM runs preemptively"), `max_speech_duration: 10.0`, `max_retries: 3` — [turn.py L201-228](https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/turn.py)
- Adoption check at EOT, unchanged at HEAD (`agent_activity.py` ~L2950-2972). The speculation is reused only if `_transcripts_equivalent(...)` holds and `preemptive.chat_ctx.is_equivalent(temp_mutable_chat_ctx)` and `preemptive.tools == self.tools` and `preemptive.tool_choice == self._tool_choice`. That comparison runs *after* `on_user_turn_completed` — [agent_activity.py](https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/agent_activity.py)
- agents-js matches Python. `agents/src/voice/turn_config/preemptive_generation.ts` has `preemptiveTts: false`, `maxSpeechDuration: 10_000`, `maxRetries: 3`. `audio_recognition.ts` handles `PREFLIGHT_TRANSCRIPT` (L1307, L1473) — [agents-js preemptive_generation.ts](https://github.com/livekit/agents-js/blob/main/agents/src/voice/turn_config/preemptive_generation.ts)
- A LiveKit user says interims never reach the LLM. Issue **#8284** (open, 2026-10-30, "Blog post misstates when ASR interim transcripts are sent to the LLM"): "The ASR does stream, but the interim transcripts are held in-process, and when the final transcript arrives or when the end of turn is detected only then is the held text sent to the LLM." — [issue #8284](https://github.com/livekit/agents/issues/8284); disputed blog: [LiveKit blog](https://livekit.com/blog/voice-agent-architecture-stt-llm-tts-pipelines-explained)
- The official RAG example does retrieval in `llm_node`: `retriever.aretrieve(user_query)` at `examples/voice_agents/llamaindex-rag/retrieval.py` L55-88. Because the preemptive path calls `llm_node`, this retrieval runs speculatively at preflight/final — [retrieval.py](https://github.com/livekit/agents/blob/main/examples/voice_agents/llamaindex-rag/retrieval.py)
- **PR #7724** "feat(moss): add Moss knowledge base plugin" (open, created 2026-10-11, updated 2026-11-05, 5 comments, by rafaelbeckel; replaces #4812 and #3826). It is a `KnowledgeBase` `llm.Toolset` plus `add_context(chat_ctx)` for `llm_node`. The PR describes the search as in-process: "A search takes about a millisecond and makes no network request." Quote: "It belongs in `llm_node`, not `on_user_turn_completed`: changes made there invalidate the preemptive reply." `add_context` "carries what the last three searched turns found" and "adds nothing while the index loads, so it never holds up a reply" — [PR #7724](https://github.com/livekit/agents/pull/7724)

**Pipecat (1.15.0, 2026-10-28; main = v1.15.0-256)**
- Speculation fires on an eager-EOT prediction from `DeepgramFluxSTTService`, `DeepgramFluxSageMakerSTTService` or `CartesiaTurnsSTTService` (`enable_eager_end_of_turn=True` + `EagerUserTurnStrategies`). A `SpeculationGate` (`src/pipecat/turns/speculation_gate.py`, "Decision engine holding a speculative bot response until its turn is confirmed") holds the response. "Tool calls are never executed" for an unconfirmed turn — [CHANGELOG 1.9.0, PR #5625](https://github.com/pipecat-ai/pipecat/blob/main/CHANGELOG.md); [speculation_gate.py](https://github.com/pipecat-ai/pipecat/blob/main/src/pipecat/turns/speculation_gate.py)
- `Mem0MemoryService` (`src/pipecat/services/mem0/memory.py`) still has **no** reference to `speculation` at HEAD. A grep of `\.speculation` in `src/pipecat` hits only frames, `llm_service.py`, the tone tagger, `predictive_delegation.py`, evals, and the turn strategies. So Mem0 retrieval would run on speculative contexts, and would also store them — [memory.py](https://github.com/pipecat-ai/pipecat/blob/main/src/pipecat/services/mem0/memory.py)
- The RAG examples (`examples/rag/rag-gemini.py`, `rag-gemini-grounding-metadata.py`, `rag-mem0.py`) are retrieval-as-function-call ("The voice model is configured to call a function whenever the user asks a question") or Mem0. Function-call RAG is withdrawn under speculation — [examples/rag](https://github.com/pipecat-ai/pipecat/tree/main/examples/rag)
- Predictive delegation (PR #6174, 1.15.0) races a yes/no classifier "after each user request" to trigger a backend delegation early. This speculates on routing at EOT, not on interims — [CHANGELOG 1.15.0](https://github.com/pipecat-ai/pipecat/blob/main/CHANGELOG.md)
- Two related PRs are not merged. **PR #6151** "Let the TTS service hold a speculative response" (open, 2026-10-13, by maintainer aconchillo, 1 reaction) moves the gate to TTS (`enable_speculation_gate=True` on `CartesiaTTSService`). It notes: "Observers, and processors between the LLM and the TTS, now see a response that may be withdrawn." **PR #6374** `TurnAnalyzerEagerUserTurnStopStrategy` / `BaseTurnAnalyzer.pop_eager()` (let a local turn analyzer drive speculation) was closed 2026-10-25 without merging; the class is absent from `src` — [PR #6151](https://github.com/pipecat-ai/pipecat/pull/6151); [PR #6374](https://github.com/pipecat-ai/pipecat/pull/6374)

**Dograh (built on a Pipecat fork)**
- Dograh uses a Pipecat submodule fork (`.gitmodules` → `dograh-hq/pipecat`). Its own `api/services/pipecat/fallback_llm.py` honours speculation: `self._speculation_gate.begin_speculation(frame.speculation)`, with the comment "Speculative tools must wait for a committed transcript". Knowledge-base RAG is a tool (`retrieve_kb_func` in `api/services/workflow/pipecat_engine.py` L591; `tools/knowledge_base.py` `retrieve_from_knowledge_base`), so it gets no speculative head start — [dograh repo](https://github.com/dograh-hq/dograh)

**NVIDIA**
- The `NVIDIA/ace-controller` README now says: "This repository has been archived. All future development has moved to NVIDIA-AI-Blueprints/nemotron-voice-agent." The archived code still has `RivaInterimTranscriptionFrame` ("Only transcripts with stability=1.0 are processed for speculative…", `src/nvidia_pipecat/frames/riva.py`). `NVIDIA/voice-agent-examples` is also archived (search API `archived: true`) — [ace-controller](https://github.com/NVIDIA/ace-controller)
- The successor `NVIDIA-AI-Blueprints/nemotron-voice-agent` (HEAD 2026-10-29) has no `ENABLE_SPECULATIVE_SPEECH` or speculative-speech code in grep. Its only "speculative" hits are LLM speculative *decoding* (e.g. `--speculative_config.method dflash` in `docker/docker-compose.nemotron35-lightning.yaml`) — [nemotron-voice-agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent)
- New `NVIDIA-NeMo/labs-Voice-Agent` ("A fully opensource framework for building and evaluating voice agents with open models", 12★, pushed 2026-11-04): grep found no preemptive/speculative/interim code — [labs-Voice-Agent](https://github.com/NVIDIA-NeMo/labs-Voice-Agent)

**Others**
- **jambonz**: `earlyGeneration` (opt-in, on eager-EOT/turn-prediction signals; tools held until confirmed) is documented. Grep of `jambonz-feature-server/lib` (HEAD 2026-10-23) found no `earlyGeneration`/`preflight`, so it likely lives in another component, unverified. Pipecat merged a jambonz serializer for the listen verb (PR #6573, 2026-11-05) — [jambonz voice agents docs](https://docs.jambonz.org/guides/features/voice-agents); [Pipecat commit b53b0c2](https://github.com/pipecat-ai/pipecat/pull/6573)
- **TEN Framework** (HEAD 2026-11-06): the only speculation-related hit is `fish_asr_python/extension.py` L678-704, which passes `"eager_end_of_turn": True` through as a flag ("The preceding eager result was only a prediction"). There is no preemptive LLM or retrieval — [ten-framework](https://github.com/TEN-framework/ten-framework)
- **Cartesia Line SDK** (v0.2.20, 2026-10-27): grep for interim/partial/speculative/preemptive/eager/prefetch found nothing related to transcripts. The README lists interruption support, tool calling, handoffs, web search and LiteLLM — [cartesia-ai/line](https://github.com/cartesia-ai/line)
- **Vapi / Retell** OSS repos (`VapiAI/server-sdk-python`, `RetellAI/retell-python-sdk`) are API client SDKs, not orchestration frameworks — [Vapi SDK](https://github.com/VapiAI/server-sdk-python); [Retell SDK](https://github.com/RetellAI/retell-python-sdk)

### Inferences
- Across frameworks, the trigger for any early work is **eager-EOT / preflight / final segment**, never a plain interim, and tools are always deferred. Forehear's interim-triggered retrieval sits in a gap no shipped framework covers. Its value per turn is the time between the first useful interim and preflight, plus retrieval latency. For in-process indexes like Moss (~1 ms), the Moss-in-`llm_node` pattern already removes most of the retrieval cost at preflight, which weakens forehear's pitch for small local KBs. The strongest case remains networked or slow retrieval (vector DB round trips, rerankers, hybrid search, query rewriting).
- **Where forehear plugs in:** LiveKit's `llm_node` (consume the cached retrieval when the preemptive call runs, so the chat context stays unchanged and `is_equivalent` keeps passing). Pipecat: a processor between STT and the user aggregator taps `InterimTranscriptionFrame`, since the aggregators consume those frames (this is the same integration point issue #6511 describes), and context is injected only into the `LLMContextFrame(speculation=True)` and committed frames. Dograh/Pipecat tool-based KB: replace the tool with a pre-LLM context processor, or have the tool serve from forehear's cache at commit time.

### Gaps
- I did not verify jambonz `earlyGeneration` in source; the component holding it was not identified.
- I did not grep Rasa voice (Rasa Pro is mostly closed source; the `RasaHQ/rasa` OSS repo was last pushed 2026-07-24), and found no Rasa speculative feature.
- OpenAI Agents SDK, Bolna, FastRTC, Unmute, Ultravox and Vocode were not re-cloned. Per the 2026-11-03 note, none speculates; their last-push dates below show no burst of activity.

## Q2. Which open issues/discussions/PRs request speculative retrieval, preemptive RAG, interim-based prefetch, or keeping preemptive replies after context edits?

### Takeaway
Demand is real but low-engagement. The relevant issues have 0–1 reactions each. The clearest signals: LiveKit #4881 (keep preemptive replies after chat-context edits; open since 2026-02-18 with no maintainer commitment), LiveKit #5924 and PR #6626 (speculation unsafe for stateful LLM adapters; PR unreviewed), and Pipecat #6511 (2026-11-02, speculative KV prefill from interims via an external package). No issue in either repo asks for speculative *retrieval* by name. A search of Pipecat issues for "interim RAG" returned zero results.

### Cited Findings
- **LiveKit #4881** "feat: Add a parameter to allow preemptive generation even after _chat_ctx modification". Open, created 2026-02-18 by pUrGe12, `enhancement` label, 5 comments, 0 reactions, last updated 2026-07-23. Body: "It would be awesome if this cancellation was behind a config parameter, cause I kinda need to modify _chat_ctx and I would still be happy with preemptive generation." Comments: tinalenguyen (member, 2026-02-23) asked for the use case. The author (2026-02-28) replied: "to minimise our prompt size, we try to dynamically inject guidelines etc. into the chat context. This kills preemptive generation". Author (2026-03-05): "we can afford to [mess] up a particular turn for better latency". davidzhao (member, 2026-03-21): "is this done in `on_user_turn_completed`?" A comment by IgorGanapolsky was deleted on 2026-07-23. "No branches or pull requests", with no assignee or milestone — [issue #4881](https://github.com/livekit/agents/issues/4881)
- **LiveKit #5924** "[Plugin] livekit-plugins-langchain doesn't play nicely with pre-emptive generation". Open, 2026-06-01, by JacobSmith5455, 0 comments, 0 reactions. Quote: "Speculative runs that get discarded kick off turns that can call tools which mutate state with no rollback… There's no seam in the adapter to distinguish 'generate this speculatively' from 'commit this only once the turn is confirmed'" — [issue #5924](https://github.com/livekit/agents/issues/5924)
- **LiveKit PR #6626** "feat(llm): let an LLM declare chat() stateful". Open, 2026-07-30, by biztex (external), 0 comments, last updated 2026-07-31. It adds `LLM.stateful` (default `False`); `on_preemptive_generation` skips speculation for stateful LLMs, and the LangGraph adapter defaults to stateful. The PR says "a full speculative/commit protocol would be a much bigger design; this doesn't preclude one later" — [PR #6626](https://github.com/livekit/agents/pull/6626)
- **LiveKit PR #7991** "keep preemptive generation when a transcript only changes formatting". Open, 2026-10-20, by u9g. It measured that across 42 Flux turns, "8 had a second preflight that differed only in punctuation". Each restart cost about 120–280 ms of head start. An earlier related PR, #6667 "tolerate formatting changes in preemptive transcripts", merged 2026-08-02 (fixes #5766) — [PR #7991](https://github.com/livekit/agents/pull/7991); [PR #6667](https://github.com/livekit/agents/pull/6667)
- **agents-js #1365** "Preemptive generation does not check in-flight function tool execution". Open, 2026-05-01, 2 comments. A preemptive `generateReply` starts before a tool result lands in the context, and "the LLM commonly hallucinates the tool's outcome". It adds that Python is "unprotected for plain (non-handoff) tools" — [agents-js #1365](https://github.com/livekit/agents-js/issues/1365)
- **Pipecat #6511** "Speculative KV-cache prefill from interim ASR transcriptions (measured TTFT -73% to -97% on CPU)". Open, 2026-11-02, by iamdgarcia, 0 comments, 1 reaction. Quote: "`LLMContextAggregatorPair` consumes `InterimTranscriptionFrame`/`EagerTranscriptionFrame` (they never reach the LLM service), so all that lead time goes unused… a tap is the only integration point for the LLM to ever see partials." It is an external package (`iamdgarcia/pipecat-speculative-prefill`) with `SpeculativePrefillTap`, `SpeculativeLLMService` and `PrefixCacheWarmer` (max_tokens=1 warm requests for vLLM/SGLang prefix caching). Reported results: 53-token prompt TTFT 1155.8 → 317.0 ms; 873-token prompt 10868.3 → 367.8 ms (CPU, Qwen2.5-0.5B). It covers prefill, not retrieval — [issue #6511](https://github.com/pipecat-ai/pipecat/issues/6511)
- **Pipecat #5207** "Allow decorating the user turn's context message without forking LLMUserAggregator.push_aggregation". Closed 2026-08-05 (not marked completed via a merged PR in search data). The author maintained "a fork guarded by a source-hash tripwire" to inject per-turn metadata. It shows the same context-injection seam problem as LiveKit #4881 — [issue #5207](https://github.com/pipecat-ai/pipecat/issues/5207)
- **Pipecat #3569** "[RFC] Native support for RAG Citations and Source Attribution in Voice Pipelines" (closed 2026-03-26), and #1529 "Any example for advanced RAG and History Flow?" (closed, 14 comments). Neither is about speculation — [issue #3569](https://github.com/pipecat-ai/pipecat/issues/3569); [issue #1529](https://github.com/pipecat-ai/pipecat/issues/1529)
- **Pipecat #5960** "Make the post-tool LLM run race-free when the tool result beats UserStoppedSpeakingFrame" (open, 2026-09-28), a tool/turn-timing race — [issue #5960](https://github.com/pipecat-ai/pipecat/issues/5960)
- A GitHub-wide issue search for "speculative retrieval voice interim" and "preemptive RAG voice agent" returned only unrelated noise (agent coordination boards), so I found no request elsewhere — [GitHub search](https://github.com/search?q=speculative+retrieval+voice+interim&type=issues)

### Inferences
- The pattern behind LiveKit #4881, Pipecat #5207 and Moss PR #7724 is consistent: per-turn context injection (RAG, guidelines) conflicts with speculation's "context unchanged" invariant. Each framework's answer so far has been "put it inside the speculated branch" (`llm_node`), not "speculate the injection itself". That is the API surface forehear can own, if it validates the retrieval against the final transcript and injects context deterministically, so that LiveKit's `is_equivalent` and Pipecat's match policy don't trip.
- Low reaction counts suggest most users haven't noticed preemptive generation silently degrading under RAG. Forehear's docs could make this visible, e.g. by pointing users to LiveKit's log line "preemptive generation invalidated after `on_user_turn_completed`…".

### Gaps
- GitHub Discussions (LiveKit, Pipecat) and Discord/Slack threads were not searchable in this session; the repos API was blocked and web search surfaced none.
- I could not read the comment threads on #7724, #7991, #6151 or #6511, so I don't know the maintainers' reactions to them.

## Q3. What has changed since November 3, 2026?

### Takeaway
Nothing in Nov 3–6 adds speculative retrieval to any framework. LiveKit shipped 1.8.11 (2026-11-05) with no preemptive changes, and the Moss KB PR is still open. Pipecat has made no release since 1.15.0; main has 256 commits since, including two eager-speculation bug fixes and a lot of "expressive conversation/perception" work. The biggest structural change is NVIDIA archiving ace-controller, and with it the only interim-triggered speculative-LLM implementation.

### Cited Findings
- **LiveKit agents 1.8.11** (PR #8397, commit 2026-11-05) bumped versions only. Turn-related commits between Nov 2 and Nov 5: #8318 "fix(voice): let only the STT end a turn the STT reopened" (2026-11-03), #7938 speaking-rate burst fix, #8301 duplex fix, #8099 `session_closed`. Also many inference/plugin additions (xai/stt-2 #8409, rime/prism #8396, Kalpa TTS #8017, Zoom AI STT #7708, `inference.responses.LLM` #8210-#8212). None touches preemptive or RAG — [livekit/agents commits](https://github.com/livekit/agents/commits/main); [PyPI livekit-agents](https://pypi.org/project/livekit-agents/)
- LiveKit issue #8302 (closed 2026-11-03): "turn_detection="stt" with Deepgram Flux: a VAD end of speech after the caller resumes commits a stale transcript" — [issue #8302](https://github.com/livekit/agents/issues/8302)
- LiveKit Moss PR #7724 was updated 2026-11-05 and is still open — [PR #7724](https://github.com/livekit/agents/pull/7724)
- agents-js: npm `latest` is still 1.9.5 — [npm @livekit/agents](https://www.npmjs.com/package/@livekit/agents)
- **Pipecat**: PyPI latest is 1.15.0 (uploaded 2026-10-29). Unreleased fragments in `changelog/` include `6551.fixed.md`: "Fixed `EagerUserTurnStopStrategy` leaving its speculation timer running after `cleanup()`, which could withdraw a speculation after the session had ended" (PR #6551, closed 2026-11-05). PR #6557 "Fix eager speculation gluing a turn's segments together without a space" is open (2026-11-05). Other merges Nov 4–5: perception/turn-completion (#6567), PerceptionReader (#6519), jambonz serializer (#6573/#6574), Soniox agent text (#6571), and Hume TTS deprecation (#6556) — [Pipecat changelog dir](https://github.com/pipecat-ai/pipecat/tree/main/changelog); [PR #6557](https://github.com/pipecat-ai/pipecat/pull/6557)
- Pipecat issue #6511 was filed 2026-11-02, just before the window, and has had no response since — [issue #6511](https://github.com/pipecat-ai/pipecat/issues/6511)
- **NVIDIA**: `ace-controller` README archive notice (last commit `e72a8b6`, 2026-07-17, "Archive message in README"). Successor nemotron-voice-agent (256★, pushed 2026-11-05) has no speculative-speech feature — [ace-controller](https://github.com/NVIDIA/ace-controller); [nemotron-voice-agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent)
- **pipecat-flows** is archived (search API `archived: true`, last push 2026-07-05). Per the 1.9.0 CHANGELOG it was merged into `pipecat.flows` — [pipecat-flows](https://github.com/pipecat-ai/pipecat-flows)
- **Dograh** stays very active (HEAD 2026-11-05, #978 "use dedicated billable Agent Builder endpoint") — [dograh](https://github.com/dograh-hq/dograh)

### Inferences
- The 2026-11-03 note's statement that NVIDIA "ships speculative generation" on stable interims should now be qualified: it is archived and absent from NVIDIA's current blueprint. Forehear's competition in interim-triggered work is therefore only small third-party repos (primd, Overhear, pipecat-speculative-prefill, etc., covered in the earlier note) and the new #6511 package.

### Gaps
- I didn't check LiveKit/Pipecat Discord announcements or blog posts from Nov 3–6. The web search found no dedicated Pipecat blog post on speculation.

## Q4. Adoption metrics (forehear distribution channels)

### Takeaway
LiveKit Agents is the biggest channel by downloads (≈3.6M PyPI and 3.7M npm per month), and Pipecat is second (≈1.0M PyPI per month) with slightly more GitHub stars. Everything else is one to two orders of magnitude smaller. Dograh (6.0k★, Pipecat-based) is the fastest-rising downstream of Pipecat. The OpenAI Agents SDK has the largest raw numbers, but its voice pipeline is a minor part of that SDK.

### Cited Findings
GitHub data is from the search API, 2026-11-06: stars / forks / last push / open issues+PRs.
- openai/openai-agents-python — 30,523 / 4,994 / 2026-11-06 / 52; openai/openai-agents-js — 3,981 / 1,002 / 2026-11-06 / 38 — [repo](https://github.com/openai/openai-agents-python)
- RasaHQ/rasa — 21,373 / 4,912 / 2026-07-24 / 160 — [repo](https://github.com/RasaHQ/rasa)
- pipecat-ai/pipecat — 17,086 / 3,045 / 2026-11-06 / 479 — [repo](https://github.com/pipecat-ai/pipecat)
- livekit/agents — 15,105 / 4,075 / 2026-11-06 / 893; livekit/agents-js — 958 / 422 / 2026-11-06 / 528 — [repo](https://github.com/livekit/agents)
- TEN-framework/ten-framework — 11,218 / 1,375 / 2026-11-06 / 256 — [repo](https://github.com/TEN-framework/ten-framework)
- dograh-hq/dograh — 6,030 / 1,546 / 2026-11-05 / 113 — [repo](https://github.com/dograh-hq/dograh)
- gradio-app/fastrtc — 4,635 / 437 / 2026-10-21; fixie-ai/ultravox — 4,584 / 388 / 2025-12-12; vocodedev/vocode-core — 3,808 / 655 / 2024-11-15 (dormant); kyutai-labs/unmute — 1,542 / 249 / 2026-09-09; bolna-ai/bolna — 816 / 390 / 2026-11-05 — [GitHub search](https://github.com/search?q=repo%3Agradio-app%2Ffastrtc&type=repositories)
- pipecat-ai/pipecat-flows — 626 (archived); NVIDIA-AI-Blueprints/nemotron-voice-agent — 256; cartesia-ai/line — 105 / 51 / 2026-10-27; jambonz/jambonz-feature-server — 104 / 79 / 2026-10-30; NVIDIA/voice-agent-examples — 66 (archived); RetellAI/retell-python-sdk — 59; VapiAI/server-sdk-python — 53; NVIDIA-NeMo/labs-Voice-Agent — 12 — [nemotron-voice-agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent)
- PyPI downloads, last month (pypistats "recent", 2026-11-06): `openai-agents` 12,449,784; `livekit-agents` 3,609,910 (last week 1,236,823); `mem0ai` 2,020,516; `pipecat-ai` 1,043,553 (last week 374,140); `cartesia-line` 32,793; `rasa-pro` 12,631; `fastrtc` 10,899; `bolna` 9,415; `vocode` 890 — [pypistats livekit-agents](https://pypistats.org/packages/livekit-agents); [pypistats pipecat-ai](https://pypistats.org/packages/pipecat-ai)
- npm `@livekit/agents`: 3,702,268 downloads from 2026-10-06 to 2026-11-04 — [npm downloads API](https://api.npmjs.org/downloads/point/last-month/@livekit/agents)
- Third-party roundups still name LiveKit Agents, Pipecat and TEN as the main OSS frameworks, and NVIDIA NeMo Voice Agent as the newest entrant (graduated to its own repo in August 2026). These are vendor/blog sources and they disagree on rankings — [AssemblyAI orchestration tools 2026](https://www.assemblyai.com/blog/orchestration-tools-ai-voice-agents); [Micdrop 2026](https://micdrop.dev/blog/open-source-voice-agent-frameworks); [techsy.io](https://techsy.io/en/blog/best-open-source-voice-agent-frameworks)

### Inferences
- LiveKit's preemptive generation is on by default across about 7M monthly Python+Node installs, so the pool of users whose RAG silently invalidates speculation is large. A LiveKit `llm_node`-compatible adapter is forehear's highest-leverage channel. Pipecat is second, and Dograh could be a downstream (via Pipecat) because its KB retrieval is tool-based.
- PyPI downloads include CI and transitive installs, so they overstate active users. Stars are a better measure of mindshare.

### Gaps
- I couldn't get contributor counts: the `repos/*/contributors` endpoint was blocked.
- I couldn't get PyPI download stats for TEN (no `ten-framework` package on PyPI) or for NVIDIA/jambonz (not PyPI-distributed).
- The ace-controller star count is missing from the search results (the repo is archived).

## Q5. What would it take for LiveKit or Pipecat to build native speculative retrieval, and is there evidence they plan to? (Likelihood of making forehear redundant)

### Takeaway
I found **no evidence that either maintainer team plans interim-triggered speculative retrieval**. There are no issues, PRs, roadmap items or docs. Both are investing in turn-level speculation infrastructure that could host it cheaply:
- LiveKit: preemptive options, formatting tolerance, a stateful-LLM seam.
- Pipecat: SpeculationGate, `LLMContextFrame.speculation`, TTS-side gate, predictive delegation, turn-strategy redesign.

The likeliest native path is **retrieval at the preflight/eager-EOT moment inside the speculated branch** (LiveKit's Moss-in-`llm_node` guidance, or Pipecat's Mem0 made speculation-aware), not interim-level prefetch. Estimated likelihood that either ships native interim-transcript speculative retrieval within ~6 months: **low (my judgement)**. Likelihood that they ship "retrieval inside preemptive generation" patterns or plugins: **high**, and partly underway via PR #7724. That substitutes for forehear's simplest use case, but not for its interim-level lead time or its hit/miss validation.

### Cited Findings
- LiveKit's speculation model compares snapshots (transcript equivalence, `chat_ctx.is_equivalent`, tools, tool_choice) after `on_user_turn_completed`. Supporting context-injection RAG natively would need either a relaxed comparison (what #4881 asks for, with no maintainer commitment since 2026-03-21) or retrieval moved into the speculated branch (what #7724 recommends) — [agent_activity.py](https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/agent_activity.py); [issue #4881](https://github.com/livekit/agents/issues/4881); [PR #7724](https://github.com/livekit/agents/pull/7724)
- LiveKit's own trigger plumbing never starts work on `INTERIM_TRANSCRIPT`; interims only cancel stale preflights (fix for #7948 via PR #7949, merged 2026-10-22). Native interim prefetch would need a new event path — [PR #7949](https://github.com/livekit/agents/pull/7949); [audio_recognition.py](https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/audio_recognition.py)
- LiveKit's speculative/commit design work is explicitly deferred. PR #6626 calls "a full speculative/commit protocol… a much bigger design", and the PR itself has gone unreviewed since 2026-07-31 — [PR #6626](https://github.com/livekit/agents/pull/6626)
- Pipecat's aggregators consume interim frames ("ignore interim and eager (provisional) transcriptions at this point", `processors/aggregators/sentence.py`). Issue #6511 confirms that "a tap is the only integration point". A native feature would need the aggregator or a new processor to publish provisional contexts on interims, not just on eager EOT — [issue #6511](https://github.com/pipecat-ai/pipecat/issues/6511); [sentence.py](https://github.com/pipecat-ai/pipecat/blob/main/src/pipecat/processors/aggregators/sentence.py)
- Pipecat already has the "speculative context" primitive. Since 1.15.0 (PR #6385), `LLMContextUserTurnFrame(speculation=True)` is broadcast "so a processor that keeps the conversation should skip speculative turns". Mem0 doesn't yet honour it. Making Mem0 speculation-aware is the smallest native step, and nobody has filed it — [CHANGELOG 1.15.0](https://github.com/pipecat-ai/pipecat/blob/main/CHANGELOG.md); [memory.py](https://github.com/pipecat-ai/pipecat/blob/main/src/pipecat/services/mem0/memory.py)
- Pipecat maintainers are actively extending speculation: PR #6151 (TTS-held speculation, by aconchillo), PR #6346 "User turn strategies redesign" (in 1.15.0), predictive delegation (#6174). PR #6374 (analyzer-driven eager EOT) was closed unmerged on 2026-10-25. None of these mentions retrieval — [PR #6151](https://github.com/pipecat-ai/pipecat/pull/6151); [PR #6374](https://github.com/pipecat-ai/pipecat/pull/6374); [CHANGELOG](https://github.com/pipecat-ai/pipecat/blob/main/CHANGELOG.md)
- Vendors push in the other direction. Deepgram recommends eager EOT "especially when the pipeline includes RAG or function calling", with ~50–70% more LLM calls (from the 2026-11-03 note). AssemblyAI promotes LiveKit's `preemptive_generation=True` as a one-flag latency win — [Deepgram Flux eager EOT](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot); [AssemblyAI on X](https://x.com/AssemblyAI/status/1953073368443298151)
- Research context: VoiceAgentRAG (Salesforce, arXiv 2603.02206) classifies LiveKit+RAG as neither proactive nor predictive. "Predictive Prefetching for Retrieval-Augmented Generation" (arXiv 2605.17989) also exists. Both are research, not framework roadmap — [VoiceAgentRAG](https://arxiv.org/html/2603.02206v1); [arXiv 2605.17989](https://arxiv.org/pdf/2605.17989)

### Inferences
- **What LiveKit would need** to build it natively:
  1. An `on_interim`/`on_partial_transcript` hook or retrieval cache keyed by transcript prefix.
  2. Validation of cached retrieval against the final/preflight transcript (their `_transcripts_equivalent` is already a reusable building block).
  3. Injection into the `llm_node` copy of the context, so `is_equivalent` passes.

  This is roughly 1–2 PRs of work in their codebase. But there is no demand signal beyond #4881 (0 reactions), and the Moss PR shows the maintainers' current answer is "do it in `llm_node`".
- **What Pipecat would need** to build it natively:
  1. A processor between STT and the aggregator that sees interims (#6511's tap).
  2. Speculation-aware retrieval services (Mem0 honouring `speculation`).
  3. A way to inject retrieved context into both the provisional and committed contexts consistently, so the `NormalizedMatch` check and the gate behave.

  Its frame-based architecture makes a third-party processor the natural form. Pipecat has historically absorbed popular third-party patterns (it merged pipecat-flows into core in 1.9.0), so a successful forehear processor is a plausible candidate for later absorption. That is both a risk and a distribution opportunity.
- **Redundancy risk ranking:**
  1. LiveKit + Moss-style in-memory KB in `llm_node`: high substitution for small or static KBs.
  2. Pipecat speculation-aware Mem0: medium, not started.
  3. Native interim-level prefetch in either framework: low near-term, with no evidence of plans.
  4. NVIDIA: none (archived).
  5. TEN, Bolna, Dograh, Cartesia Line, jambonz: none; they'd more likely consume a library.

### Gaps
- I found no public LiveKit or Pipecat roadmap document. Maintainer intent comes only from PR/issue activity.
- I couldn't read maintainer review comments on #7724 (5 comments), which would show whether LiveKit will merge "retrieve in `llm_node`" as official guidance.
- I couldn't measure how often LiveKit users hit the "preemptive generation invalidated" path; there is no public telemetry.
