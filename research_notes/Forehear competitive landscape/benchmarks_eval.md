# Voice-agent benchmarks and eval/observability tools as competitors to forehear's benchmark

Scope: the benchmark half of forehear. It is an open, deterministic, CPU-only replay of 4,018 HeySQuAD human-recorded dev questions, streamed through Vosk en-us-0.22-lgraph in 100 ms chunks with real interim revisions. Retrieval uses BM25 over 19,831 SQuAD v2 passages, top-5. End of turn (EOT) is set 500 ms after the last word. For each speculation policy it reports:
- wait after EOT
- saved time
- whether context was ready at EOT
- coverage and accuracy
- calls per turn
- recall@k delta against final-only

Tool latency is modelled under four profiles: local, hosted_kb, rerank, and web_search. — [forehear RESULTS.md](file:///home/user/Infinity/results/RESULTS.md)

Method notes:
- **What was verified this session:**
  - EVA's README, docs and code, from a local clone at commit 2026-10-29.
  - The Galbraith code repo and the DSTC10 Track 2 repo, both cloned.
  - Hugging Face dataset search through the HF API.
  - Primary arXiv pages for FDB-v3, the Galbraith paper, τ-Voice, τ-Knowledge, Stream RAG and EVA.
  - The GitHub pages for VoiceBench, Full-Duplex-Bench, tau2-bench, aiewf-eval, openbenchmarks and EVA.
  - Artificial Analysis leaderboard pages.
- **Star counts:** `gh api` was blocked for unattached repos in this session, so star counts come from the rendered GitHub pages as fetched on 2026-11-06.
- **Earlier notes:** these were at `/home/user/Infinity/docs/research/notes/benchmarks_datasets.md`. Items carried over from them without re-verification are marked "(prior notes)".

---

## 1. What each existing benchmark / eval product measures, and how forehear's benchmark relates to it

### Takeaway
Every benchmark found falls into one of three groups:
- **Spoken-LLM quality:** VoiceBench, URO-Bench, VERA, Big Bench Audio, Talk Arena.
- **End-to-end agent task success plus experience:** EVA, τ-Voice/τ-Knowledge, aiewf-eval, the commercial simulators.
- **Turn-taking and latency timing:** Full-Duplex-Bench, openbenchmarks TTFAB, the Artificial Analysis TTFA and streaming-STT leaderboards.

Of all of them, only two closely touch forehear's question:
- **FDB-v3** counts *pre-emptive* tool calls made before the user stops speaking.
- **Galbraith's CRAG stabilization analysis** measures how early retrieval settles on text prefixes.

Neither scores retrieval readiness at EOT, calls per turn, or behaviour under real ASR revisions. forehear's benchmark is therefore a complementary component benchmark, not a substitute for any of these.

### Cited Findings

#### EVA / EVA-Bench (ServiceNow; arXiv 2605.13841; github.com/ServiceNow/eva)

**What it measures**
- Complete multi-turn spoken conversations, scored on two axes. — [EVA README](https://github.com/ServiceNow/eva)
  - **EVA-A (accuracy):** task completion, speech fidelity, faithfulness.
  - **EVA-X (experience):** conciseness, turn-taking, latency, progression.

**Data**
- 213 enterprise scenarios across three domains. — [EVA README](https://github.com/ServiceNow/eva)
  - Airline CSM, Healthcare HR, and Enterprise ITSM.
  - Each domain has single-intent, multi-intent, and adversarial scenarios.
  - Scenarios stress transcription of named entities such as confirmation codes.
- The speech is synthetic. A live bot-to-bot setup has an ElevenLabs or OpenAI Realtime user simulator talk to a Pipecat-hosted agent. — [EVA README](https://github.com/ServiceNow/eva)
- A perturbation suite adds noise, accents and connection degradation. — [EVA README](https://github.com/ServiceNow/eva)
- Multilingual support is listed as future work. — [EVA limitations section (website source)](https://github.com/ServiceNow/eva/blob/main/website/src/components/limitations/LimitationsSection.tsx)
- The HF dataset `ServiceNow-AI/eva-bench` had 186 downloads and 26 likes. — [HF API](https://huggingface.co/datasets/ServiceNow-AI/eva-bench)

**Latency handling**
- `response_speed` is a deterministic, diagnostic-only metric: the time from the end of the user utterance to the start of the assistant's response. — [EVA response_speed.md](https://github.com/ServiceNow/eva/blob/main/docs/metrics/response_speed.md)
  - It comes from Pipecat's `UserBotLatencyObserver`.
  - It is explicitly "not attributable to a single model capability".
  - It is not normalized to a score.
- `turn_taking` scores each transition on a piecewise-linear latency curve. — [EVA turn_taking.md](https://github.com/ServiceNow/eva/blob/main/docs/metrics/turn_taking.md)
  - The curve plateaus between 500 and 2,000 ms on normal turns and between 500 and 3,000 ms on tool-call turns.
  - A turn counts as late at 2,750 ms (normal) or 4,000 ms (tool-call).
  - It reports p50 and p90 latency plus early, on-time and late rates.
  - Tool-call turns get lenient thresholds "since tool execution adds inherent latency".
- STT and TTS time-to-first-byte are taken from Pipecat `TTFBMetricsData`, which gives some per-stage data. — `src/eva/orchestrator/worker.py` in the [EVA repo](https://github.com/ServiceNow/eva)

**Speculation**
- The paper's Limitations section says "speculative execution, response pre-fetching, streaming-aware scheduling" were not used. — [EVA paper HTML](https://arxiv.org/html/2605.13841)
  - It also says "pre-tool speech, streamed LLM responses, and speculative decoding" were not included in the cascade results.
  - As a result, reported latency "may not reflect achievable production lower bounds".
- The code goes further. A Cartesia ink-2 diagnostic logs the eager-end-to-final delta, which "quantifies how much earlier the LLM could have started if speculative execution were enabled (a possible future enhancement)". — `src/eva/assistant/pipecat_server.py` in the [EVA repo](https://github.com/ServiceNow/eva)
- Managed-agent baselines run *with* vendor speculation turned on: ElevenAgents with "Speculative turn: enabled", and Cartesia agents provisioned with `"speculative_generation": True`. — [EVA experiment_setup.md](https://github.com/ServiceNow/eva/blob/main/docs/experiment_setup.md); `scripts/provision_cartesia_agents.py`
- So the leaderboard mixes speculative and non-speculative systems without measuring the speculation.

**Retrieval**
- None. Tools query a deterministic per-scenario database through a mock executor, and there is no RAG. — [EVA paper HTML](https://arxiv.org/html/2605.13841)

**Reproducibility**
- Full runs need commercial APIs. — [EVA README](https://github.com/ServiceNow/eva)
  - OpenAI (assistant LLM and GPT-5.2 judges)
  - ElevenLabs or OpenAI Realtime (user simulator)
  - Google Vertex (audio judges)
  - AWS Bedrock (faithfulness)
  - Deepgram or Cartesia (STT/TTS)
- The authors admit "Full reproduction requires access to commercial model APIs" and that latency "will vary depending on APIs, deployments, and hardware". — [EVA limitations](https://github.com/ServiceNow/eva/blob/main/website/src/components/limitations/LimitationsSection.tsx)

**Key result**
- The three most accurate cascades had mean tool-call-turn latency above 5 s. The two cascades with better experience scores stayed under 2.7 s but were less accurate. — [EVA paper HTML](https://arxiv.org/html/2605.13841)

**License, adoption, maintainer**
- MIT license, maintained by ServiceNow.
- 236 stars and 41 forks.
- Last commit 2026-10-29.
- CITATION.cff v0.1.1 dated 2026-03-24.
- Leaderboard of 12 systems (7 cascade, 2 hybrid, 3 S2S).
- Sources: [GitHub](https://github.com/ServiceNow/eva); [EVA paper](https://arxiv.org/html/2605.13841)

**Contradiction**
- A community landscape table lists EVA as "latency measured: no". — [HF landscape](https://huggingface.co/datasets/chatjesus/voice-agent-benchmark-landscape)
- EVA's own docs show that it does measure latency (`response_speed`, latency percentiles), so the table is inaccurate on this point.

#### Full-Duplex-Bench v1 / v1.5 / v2 / v3 (DanielLin94144/Full-Duplex-Bench; NTU and collaborators)

**Versions** — [FDB GitHub](https://github.com/DanielLin94144/Full-Duplex-Bench)
- **v1 (arXiv 2503.04721):** static, pre-recorded tests of pause handling, backchanneling, smooth turn-taking, and user interruption.
- **v1.5 (arXiv 2507.23159):** adds overlap scenarios.
- **v2 (arXiv 2510.07838; code released 2026-02-23):** live multi-turn evaluation over WebRTC with an AI examiner and an LLM judge.
- **v3 (arXiv 2604.04847; code and data released 2026-05-20):** tool use under real disfluent speech.

**FDB-v3 data** — [FDB-v3 paper](https://arxiv.org/html/2604.04847)
- 100 recordings from 12 English speakers, some non-native (Korean and Russian backgrounds).
- Entirely real human audio, recorded mostly on built-in microphones.
- Annotated for five disfluency types.
- Four task domains with deterministic local mock APIs.

**FDB-v3 latency and pre-emptive calls** — [FDB-v3 paper](https://arxiv.org/html/2604.04847)
- Latency is split into three stages: first-response latency (any speech, filler included), tool-call latency (first API call), and task-completion latency (the factual answer).
- It defines a **pre-emptive tool call** as one "invoked before the user finishes speaking" (negative tool-call latency) and reports pre-emptive rates:

| Model | Pre-emptive rate |
|---|---|
| Grok | 41.6% |
| Ultravox | 23.2% |
| Gemini Live 2.5 | 17.9% |
| Gemini Live 3.1 | 16.9% |
| GPT-Realtime | 10.8% |

- Pre-emptive use did not predict interruptions.
- In a case study (travel_19), Gemini Live 3.1's early call locked in a stale destination and the state rollback failed. This is a qualitative example of a harmful speculative call, but such calls are not counted systematically.

**FDB-v3 headline results** (Pass@1 / task-completion latency) — [FDB-v3 paper](https://arxiv.org/html/2604.04847)

| System | Pass@1 | Task-completion latency |
|---|---|---|
| GPT-Realtime | 0.600 | 6.89 s |
| Gemini Live 3.1 | 0.540 | 4.25 s |
| Cascaded | 0.450 | 10.12 s |

- This confirms the figures the prior notes took from aggregators.

**Reproducibility, license, adoption**
- Evaluation calls GPT-4o judges for argument accuracy and response quality, and the systems under test are commercial APIs. — [FDB-v3 paper](https://arxiv.org/html/2604.04847)
- 340 stars and 36 forks. The code license is not named on the page. The paper is CC BY-SA 4.0. — [FDB GitHub](https://github.com/DanielLin94144/Full-Duplex-Bench)
- Adoption: Artificial Analysis builds its "Conversational Dynamics" score from a subset of FDB v1 and v1.5. — [AA S2S](https://artificialanalysis.ai/speech-to-speech)

#### τ²-bench voice (τ-Voice: voice-v1 / voice-v2) and τ-Knowledge (Sierra Research)

**τ-Voice data and metrics**
- The τ-Voice paper (arXiv 2603.13686, 2026-03-14) covers 278 tasks extending τ²-bench. — [τ-Voice abstract](https://arxiv.org/abs/2603.13686)
  - A voice user simulator supplies accents, noise and turn-taking dynamics.
  - The simulator is decoupled from wall-clock time.
  - The metric is pass@1 task completion.
- Results: GPT-5 text reaches about 85%. Voice agents reach 31–51% in clean conditions and 26–38% in realistic ones, keeping only 30–45% of their text capability. — [τ-Voice abstract](https://arxiv.org/abs/2603.13686)

**Benchmark sets** — [tau2-bench GitHub](https://github.com/sierra-research/tau2-bench)
- `voice-v1`: English, 278 calls (50 airline, 114 retail, 114 telecom).
- `voice-v2` (τ-i18n): 6 languages × 3 domains, 900 calls.
- Voice runs use realtime provider APIs (OpenAI, Gemini, xAI).
- No latency or turn-taking metric is reported. "Judges do not change the task reward."

**τ-Knowledge (arXiv 2603.04370)**
- The `banking_knowledge` domain has about 700 interconnected documents and compares embedding retrieval with terminal-based search. — [τ-Knowledge abstract](https://arxiv.org/abs/2603.04370)
- Frontier models reach about 25.5% pass^1. — [τ-Knowledge abstract](https://arxiv.org/abs/2603.04370)
- It does not measure retrieval latency.
- It can be run in voice with `--audio-native --benchmark none`. — [tau2-bench GitHub](https://github.com/sierra-research/tau2-bench)
- v1.0.1 (2026-07-15) fixed `banking_knowledge` grading, so earlier results on that domain are not comparable. — [tau2-bench GitHub](https://github.com/sierra-research/tau2-bench)

**License and adoption**
- MIT license, 2.4k stars, 627 forks; leaderboard at taubench.com. — [tau2-bench GitHub](https://github.com/sierra-research/tau2-bench)
- Artificial Analysis uses τ-Voice for its "Agentic Performance" S2S chart. In that chart GPT-Live-1 scores 74.5% and Grok Voice 3.0 scores 71.6%. — [AA S2S](https://artificialanalysis.ai/speech-to-speech)

#### VoiceBench (MatthewCYM/VoiceBench; arXiv 2410.17196)

- **What it measures:** spoken-input LLM quality. The subsets are: — [VoiceBench GitHub](https://github.com/MatthewCYM/VoiceBench)
  - open-ended QA: alpacaeval (Google TTS), commoneval (human), wildvoice (1,000 human, diverse accents)
  - multiple-choice: openbookqa, mmsu (3,074, TTS)
  - sd-qa (553, human)
  - mtbench (46, multi-turn, TTS)
  - ifeval (TTS)
  - bbh (1,000, human)
  - advbench (safety, TTS)
- **Data:** a mix of TTS and human audio.
- **Judging and latency:** open-ended subsets are judged by gpt-4o-mini, so an API key is needed. It has no latency metric.
- **License and adoption:** Apache-2.0, 408 stars, 36 forks, leaderboard on GitHub Pages. The most recent news item is HalluAudio, dated 2026-04-20.

#### URO-Bench (arXiv 2502.17810; Findings of EMNLP 2025)

- **What it measures:** Understanding, Reasoning and Oral conversation in speech-to-speech models, with English and Mandarin subsets. About 6,946 instances. (prior notes) — [ACL Anthology](https://preview.aclanthology.org/dashboard/2025.findings-emnlp.933)
- **Adoption:** the HF dataset `Honggao/URO-Bench` had 643 downloads (HF API, 2026-11-06). — [HF](https://huggingface.co/datasets/Honggao/URO-Bench)
- **Latency:** no latency or retrieval-timing metric was found.

#### Big Bench Audio (Artificial Analysis)

- **Data:** 1,000 audio questions in four Big-Bench-Hard categories: Formal Fallacies, Navigate, Object Counting, Web of Lies. — [AA S2S](https://artificialanalysis.ai/speech-to-speech)
- **Use:** it is the reasoning axis and the time-to-first-audio (TTFA) workload for the Artificial Analysis S2S leaderboard. — [AA S2S](https://artificialanalysis.ai/speech-to-speech)
  - TTFA is "average number of seconds to generate the first audio output token on the Big Bench Audio dataset".
  - The top reasoning score is about 99.7%, which suggests the benchmark is near saturation.
- **Adoption:** HF `ArtificialAnalysis/big_bench_audio` had 7,076 downloads and 39 likes, last modified 2024-12-20. — [HF](https://huggingface.co/datasets/ArtificialAnalysis/big_bench_audio)

#### Artificial Analysis leaderboards (speech-to-speech; STT; streaming STT)

- **S2S index:** combines Big Bench Audio, FDB-based conversational dynamics, τ-Voice, arena preference Elo, and TTFA. — [AA S2S](https://artificialanalysis.ai/speech-to-speech)
  - Cascaded "default systems" are listed, such as Deepgram Voice Agent, ElevenLabs Agents and Cartesia Line.
  - It has no per-stage latency breakdown.
- **STT leaderboard:** AA-WER is computed over AA-AgentTalk (50%), VoxPopuli-Cleaned (25%) and Earnings22-Cleaned (25%). It also reports a speed factor and price. — [AA STT](https://artificialanalysis.ai/speech-to-text)
- **Streaming STT:** reports two latencies and WER at both points: — [AA streaming STT](https://artificialanalysis.ai/speech-to-text/streaming)
  - Time to Final: Silero-VAD end of speech to the final transcript.
  - Time to First Partial.
- **What it lacks:** it does not measure interim revision stability. — [AA streaming STT](https://artificialanalysis.ai/speech-to-text/streaming)
- **Reproducibility:** this is a proprietary measurement service. Method pages exist, but the harness is not open (not verified in detail).

#### Talk Arena (talkarena.org, Stanford SALT; arXiv 2502.15919)

- **Method:** pairwise human preference over large audio models. About 5,000 Prolific votes compared GPT-4o, Gemini-1.5-pro, Typhoon, Qwen2-Audio and DiVA. — [HF papers](https://huggingface.co/papers/2502.15919); [HF blog](https://huggingface.co/blog/WillHeld/talk-arena)
- **Finding:** none of 18 static benchmarks correlated strongly with interactive preference (τ ≤ 0.33). — [HF papers](https://huggingface.co/papers/2502.15919)
- **Latency:** none measured.
- **Current status:** current leaderboard state was not verified.

#### VERA (Voice Evaluation of Reasoning Ability; arXiv 2509.26542)

- **Data:** 2,931 voice-native episodes in five tracks. — [arXiv](https://arxiv.org/html/2509.26542v1)
  - Math (AIME 2025), Web (BrowseComp), Science (GPQA Diamond), Long-Context (MRCR), Factual (SimpleQA).
  - Audio is reportedly synthesized with Boson Higgs Audio 2, under CC BY 4.0. This comes from a mirror listing and is not confirmed on the primary page. — [hyper.ai](https://hyper.ai/en/datasets/46644)
- **Results:** the best text models reach 54.0% macro accuracy versus 11.3% for the best voice systems. Fast voice systems cluster around 10%. — [arXiv](https://arxiv.org/html/2509.26542v1)
- **Relevance:** it frames an accuracy/latency trade-off but does not measure stage latency.

#### openbenchmarks-labs/voice-agent-latency

- **What it measures:** TTFAB (silence from the end of the caller's speech to the start of the agent's audio), measured on real phone calls placed through Plivo. — [GitHub](https://github.com/openbenchmarks-labs/voice-agent-latency)
  - Platforms tested: Telnyx, ElevenLabs, Bland, Vapi, Retell.
  - Speech detection uses Silero VAD.
  - Turns that fail quality gates are discarded, and the discards are published by reason.
- **Not measured:** no per-stage breakdown, and no answer quality.
- **Reproducibility:** `tools/verify_run.py` re-derives the published numbers from the published audio without credentials. Fresh runs need Plivo and platform accounts. — [GitHub](https://github.com/openbenchmarks-labs/voice-agent-latency)
- **License and adoption:** MIT, 5 stars, 2 commits, leaderboard generated 2026-08-01. — [GitHub](https://github.com/openbenchmarks-labs/voice-agent-latency)

#### Daily / Pipecat aiewf-eval (kwindla/aiewf-eval; `pipecat-ai/aiewf-eval` returns 404)

- **Format:** 30-turn scripted conversations with a knowledge base placed *in the prompt* (about 12K tokens for medium, about 40K for long), so no retrieval step is involved. — [GitHub](https://github.com/kwindla/aiewf-eval)
- **Scoring:** tool use, instruction following, KB grounding, and (for speech) turn-taking. — [GitHub](https://github.com/kwindla/aiewf-eval)
- **Latency metrics:** — [GitHub](https://github.com/kwindla/aiewf-eval)
  - TTFAT P50/P95/Max (time to the first user-visible answer token or tool call).
  - For speech: voice-to-voice latency, pipeline TTFB, and silence padding.
- **Judge and keys:** a Claude judge is used, so `ANTHROPIC_API_KEY` is required, plus provider keys. — [GitHub](https://github.com/kwindla/aiewf-eval)
- **Saturation:** top text models score 99.9–100%. — [GitHub](https://github.com/kwindla/aiewf-eval)
- **License and adoption:** MIT, 169 stars, 21 forks. — [GitHub](https://github.com/kwindla/aiewf-eval)
- **Vendor use:** Ultravox cites it in marketing. — [Ultravox blog](https://www.ultravox.ai/blog/why-speech-to-speech-is-the-future-for-ai-voice-agents-unpacking-the-aiewf-eval)

#### Stream RAG / AudioCRAG (Meta + CMU; arXiv 2510.02044)

- **Data:** AudioCRAG-Synthetic (1,862 TTS queries) and AudioCRAG-Human (618 human-recorded). The authors "will open source our training code and AudioCRAG-Human benchmark". — [arXiv PDF](https://arxiv.org/pdf/2510.02044)
- **Partial transcripts:** simulated every 500 ms from OWSM-CTC word timestamps. These are truncated forced-aligned text, not real interim revisions. (prior notes) — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Metrics:** LLM-judge accuracy and staged first-token latency. (prior notes)
- **Release status as of 2026-11-06:**
  - arXiv still shows only v1 (2025-10-02), with no code or data link. — [arXiv abs](https://arxiv.org/abs/2510.02044)
  - A Hugging Face dataset search for "AudioCRAG" returned nothing. — [HF API search](https://huggingface.co/api/datasets?search=AudioCRAG)
  - An ICML 2026 poster page exists. — [ICML](https://icml.cc/virtual/2026/poster/64464)
  - So the human split is presented at ICML but **still appears unreleased**.

#### Galbraith, "When Does Streaming Tool Use Help?" (arXiv 2606.20113, 2026-06-18)

- **Setup:** 1,371 CRAG validation questions, BM25 with a dense replication. Input is **simulated as uniform word streams** at δ = 2, 3 or 4 words per second, not real speech or ASR. — [arXiv HTML](https://arxiv.org/html/2606.20113)
- **Metrics:** — [arXiv HTML](https://arxiv.org/html/2606.20113)
  - stabilization point φ (mean φ_suf = 0.26)
  - volatility (top-1 changes after stabilization for 20.9% of questions)
  - a bound H on hideable latency
  - streamable fraction: 73.9% at L = 600 ms, δ = 3 w/s
  - net-negative saving rate: 1.7% (1 of 60 replayed queries)
- **Stated limitations:** "Real ASR pacing is variable, and partial hypotheses get revised", deferred to future work. It also does not report speculative call counts or cost. — [arXiv HTML](https://arxiv.org/html/2606.20113)
- **Code:** github.com/elroy-galbraith/stablize_CRAG exists. — [GitHub](https://github.com/elroy-galbraith/stablize_CRAG)
  - Cloned this session: last commit 2026-06-21.
  - Contents: results CSVs (latency splits, φ distributions, HotpotQA).
  - No LICENSE file at the repo root, so it is not clearly reusable.
- **Authorship:** single author; affiliation not stated.

#### DSTC10 Track 2 (Amazon Alexa AI, 2021)

- **Tasks:** knowledge-grounded task-oriented dialogue on spoken conversations, with knowledge-seeking turn detection, knowledge selection, and response generation. — [repo README](https://github.com/alexa/alexa-with-dstc10-track2-dataset)
- **Data:** ASR outputs, not audio. A clone of the repo (299 MB) contained no .wav or .flac files. Test labels were released 2021-10-11. — [repo README](https://github.com/alexa/alexa-with-dstc10-track2-dataset)
- **License:** Apache-2.0. — [repo README](https://github.com/alexa/alexa-with-dstc10-track2-dataset)
- **Leaderboard:** a post-challenge leaderboard runs on eval.ai. — [repo README](https://github.com/alexa/alexa-with-dstc10-track2-dataset)
- **Paper:** arXiv 2109.13489.
- **Timing:** there are no word timings, so it cannot drive a prefix-timing replay.

#### SpokenWOZ (NeurIPS 2023 D&B)

- **Data:** 203k turns, 5.7k dialogues, 249 h of real human-to-human speech, CC BY-NC 4.0, with MultiWOZ-style DST and DB grounding (not passages). (prior notes) — [arXiv 2305.13040](https://arxiv.org/pdf/2305.13040)
- **HF availability:** third-party HF mirrors exist (e.g. `ssz1111/SpokenWOZ-Train-Audio`, 781 downloads), but they are not official. — [HF](https://huggingface.co/datasets/ssz1111/SpokenWOZ-Train-Audio)

#### inCLINC (NLP4ConvAI 2021)

- **Data:** human intent annotations on utterance prefixes from CLINC150. (prior notes) — [ACL Anthology](https://aclanthology.org/2021.nlp4convai-1.6)
- **Argument:** it warns against scoring prefixes against the final label and proposes an entropy-reduction metric.
- **Relevance:** this is the conceptual precedent for forehear's "accuracy of speculative calls" metric. It is typed text only, with no timing.

#### Other 2026 research touching speculation (system papers, not benchmarks)

- **Voice-Light (arXiv 2609.20995):** speculative generation promoted after final ASR checks. Over 36 turns, promoted turns had a median latency of 667 ms against 1,513 ms for non-promoted turns. The authors call this observational, not causal. — [arXiv](https://arxiv.org/html/2609.20995v1)
- **Endpoint Anticipation (arXiv 2606.13450):** caches look-ahead audio before the endpoint. — [arXiv](https://arxiv.org/pdf/2606.13450)
- **Speculative ASR (arXiv 2407.04641):** introduces SOWER, a metric for speculative ASR hypotheses. — [arXiv](https://arxiv.org/pdf/2407.04641)

#### Commercial eval / observability

- **Coval:** — [SiliconANGLE](https://siliconangle.com/?p=773355); [Pulse 2.0](https://pulse2.com/coval-raises-28-million-series-a-to-advance-voice-ai-evaluation-platform/)
  - $28M Series A in June 2026, led by Norwest, with Base10, Twilio Ventures and YC participating. Total raised is $31M.
  - More than 60 customers, including Zoom and Deepgram.
  - Offers simulation, monitoring and human review.
  - The founder previously led evaluation infrastructure at Waymo.
  - Its latency metric definitions were not found.
- **Hamming:**
  - Publishes self-reported production baselines for cascades: P50 of about 1.5–1.7 s, P90 of about 3 s, P95 of about 5 s. — [Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it)
  - Gives per-component ranges: STT 200–400 ms, LLM 300–1,000 ms, TTS TTFB 150–500 ms, turn detection 200–800 ms. — [Hamming metrics guide](https://hamming.ai/resources/voice-agent-evaluation-metrics-guide)
  - Claims P50/P95/P99 per component and more than 50K concurrent test calls.
- **Cekura:** — [Cekura latency guide](https://www.cekura.ai/blogs/voice-ai-latency-guide)
  - Measures latency from recorded audio, so it is architecture-agnostic.
  - Reports P25 through P99 per turn.
  - Decomposes slow turns into endpointing, ASR, LLM TTFT, TTS, and transport spans.
- **Bluejay:** $4M seed (August 2025); simulates "replicas of real customers" and monitors live agents. — [Homebrew](https://homebrew.co/blog/2025/08/27/ai-models-are-evolving-fast-but-their-use-is-gated-by-how-easy-it-is-to-test-bluejay-makes-testing-voice-and-text-ai-agents-easy-with-a-usd4-million-seed)
- **Roark:** YC W25; observability and QA; replays real caller inputs against an updated agent; more than 10M call minutes in six months. — [YC](https://www.ycombinator.com/companies/roark)
- **Vapi:** Test Suites are deprecated in favour of Simulations. In Test Suites, a testing agent calls the agent and an LLM grades the transcript against a rubric. — [Vapi docs](https://docs.vapi.ai/test/test-suites)
- **Retell:** offers LLM simulation testing with personas and built-in metrics. — [Retell docs](https://docs.retellai.com/test/llm-simulation-testing.md)
- **Langfuse:** has a Pipecat OpenTelemetry integration with one trace per conversation and STT, LLM and TTS service spans. — [Langfuse](https://langfuse.com/integrations/frameworks/pipecat)
- **Arize Phoenix:** traces Pipecat through `openinference-instrumentation-pipecat`. — [Pipecat docs](https://docs.pipecat.ai/pipecat/evals/platforms/arize.md)
- **What no source showed:** none of these vendors' pages describes a metric for speculative or preemptive retrieval, retrieval readiness at EOT, or wasted calls.

### Inferences

**How each family relates to forehear**

| Benchmark family | Relationship to forehear |
|---|---|
| **EVA** | The most direct "neighbour". It measures the end-to-end latency that forehear aims to reduce, admits it does not use speculation, and has a code comment calling speculative execution "a possible future enhancement". forehear can be the component-level lever whose gain EVA-X would register. |
| **FDB-v3** | The only benchmark that counts pre-EOT tool calls. It treats them as a behavioural rate of closed S2S models, not as a policy to optimize, and does not grade whether each early call was correct or wasted. forehear's coverage, accuracy and calls/turn give that missing scoring, on 40× more real utterances (4,018 vs 100). |
| **Galbraith** | The closest analytic competitor. It names forehear's two main design choices as its own open limitations: real ASR pacing/revisions, and call cost. forehear can position itself explicitly as the "speech-real" follow-up. |
| **AudioCRAG** | Would be the strongest competing *dataset* if released, but it uses truncated forced-aligned prefixes, not real interim revisions. |
| **VoiceBench, URO-Bench, VERA, Big Bench Audio, Talk Arena** | Orthogonal (model capability), not competitors. |
| **Commercial platforms and OpenTelemetry tracers** | Measure production per-stage latency but have no notion of a speculative call. They are a distribution channel (forehear metrics as span attributes) rather than a competitor. |

### Gaps
- Exact citation counts (Semantic Scholar or Google Scholar) for EVA, FDB, VoiceBench and τ-Voice were not retrieved.
- The URO-Bench repo's stars and license were not checked.
- The Big Bench Audio audio source (TTS or human) was not verified.
- The Talk Arena leaderboard's current state was not checked.
- Coval's latency metric definitions were not found.
- Whether Hamming, Cekura or Coval have *any* speculation metric was checked only through public marketing and docs pages, not product UIs.
- The license of the FDB code is unconfirmed.
- The Galbraith repo has no visible license.

---

## 2. Does any benchmark score whether retrieved context is ready at end-of-turn, or count wasted speculative calls?

### Takeaway
No. No benchmark found scores context-ready-at-EOT, calls per turn, or wasted speculative retrievals under real streaming-ASR revisions. The nearest partial overlaps:
- FDB-v3's pre-emptive tool-call *rate*: it counts pre-EOT calls but does not grade them.
- Galbraith's streamable fraction and net-negative rate: text prefixes only, no call counts.
- Stream RAG's fixed-interval versus model-triggered latency/accuracy comparison: synthetic prefixes, and the human split is unreleased.

### Cited Findings
- **FDB-v3:**
  - Reports the share of tool calls "invoked before the user finishes speaking", from 10.8% for GPT-Realtime to 41.6% for Grok. — [FDB-v3](https://arxiv.org/html/2604.04847)
  - Shows a failure case where an early call locked in a stale argument. — [FDB-v3](https://arxiv.org/html/2604.04847)
  - Has no metric for wasted or superseded calls. — [FDB-v3](https://arxiv.org/html/2604.04847)
- **Galbraith:** measures when BM25 top-1 stabilizes on word prefixes and a net-negative saving rate of 1.7%, but "does not report the number of speculative retrieval calls, calls per turn, or any cost measure". It explicitly defers real ASR pacing and revisions. — [arXiv 2606.20113](https://arxiv.org/html/2606.20113)
- **EVA:** lists speculative execution and response pre-fetching as not used and only logs the potential eager-to-final head start as a diagnostic. — [EVA paper](https://arxiv.org/html/2605.13841); [EVA code](https://github.com/ServiceNow/eva)
- **Artificial Analysis streaming STT:** measures Time to First Partial and WER at the first partial, but not interim revision stability. — [AA streaming STT](https://artificialanalysis.ai/speech-to-text/streaming)
- **Community landscape table (13 benchmarks):** records no benchmark measuring retrieval timing or speculative execution. Only openbenchmarks TTFAB is marked as measuring latency. — [HF landscape](https://huggingface.co/datasets/chatjesus/voice-agent-benchmark-landscape)
- **Targeted search:** found only system papers (Voice-Light, Endpoint Anticipation, Speculative ASR), no benchmark for speculative KB retrieval with wrong-retrieval cost. — [Voice-Light](https://arxiv.org/html/2609.20995v1); [Endpoint Anticipation](https://arxiv.org/pdf/2606.13450)
- **forehear does report these quantities:** — [forehear RESULTS.md](file:///home/user/Infinity/results/RESULTS.md)
  - "ready at EOT" (e.g. `stable_prefix` hosted_kb at 67%, oracle at 100%)
  - calls per turn (1.00 to 5.40)
  - coverage, accuracy and recall@k Δ per policy and tool-latency profile
  - all on real Vosk interims

### Inferences
- forehear's benchmark appears to be the first open benchmark to measure retrieval readiness at EOT and speculative call cost on real streaming-ASR interim revisions. This claim holds only with the qualifier "found no counterexample as of 2026-11-06". The two near-misses that must be cited honestly are FDB-v3 (counts pre-emptive calls in S2S models) and Galbraith (stabilization on text prefixes).
- FDB-v3's "stale destination" case is an independent example of the cost forehear's accuracy and coverage metrics capture. It is useful motivation.

### Gaps
- The full FDB-v3 paper might include a per-call correctness breakdown of pre-emptive calls beyond the case study. The fetched sections showed none.
- The AudioCRAG code, if released later, may include a calls-per-turn count. The paper compares a fixed 1 s interval against model-triggered calls but, from prior notes, reports latency and accuracy rather than wasted calls.

---

## 3. Which benchmarks are most cited / used by voice AI teams in 2026, and by whom?

### Takeaway
By observable 2026 usage, the most influential public benchmarks are those behind the Artificial Analysis S2S leaderboard (Big Bench Audio, Full-Duplex-Bench v1/v1.5, τ-Voice), plus τ²-bench, which has by far the most stars. EVA is the newest enterprise-focused contender and has the most active leaderboard additions. Practitioner latency work runs mostly on commercial platforms (Coval, Hamming, Cekura) and vendor-cited harnesses (aiewf-eval), not on academic benchmarks.

### Cited Findings
- **GitHub stars (rendered pages, 2026-11-06):**

| Repo | Stars | Forks |
|---|---|---|
| tau2-bench | 2.4k | 627 |
| VoiceBench | 408 | 36 |
| Full-Duplex-Bench | 340 | 36 |
| EVA | 236 | 41 |
| aiewf-eval | 169 | 21 |
| openbenchmarks voice-agent-latency | 5 | — |

  Sources: [tau2](https://github.com/sierra-research/tau2-bench); [VoiceBench](https://github.com/MatthewCYM/VoiceBench); [FDB](https://github.com/DanielLin94144/Full-Duplex-Bench); [EVA](https://github.com/ServiceNow/eva); [aiewf](https://github.com/kwindla/aiewf-eval); [openbenchmarks](https://github.com/openbenchmarks-labs/voice-agent-latency)
- **HF downloads:**
  - Big Bench Audio: 7,076
  - URO-Bench: 643
  - EVA-bench: 186
  - Sources: [HF API](https://huggingface.co/datasets/ArtificialAnalysis/big_bench_audio); [HF](https://huggingface.co/datasets/Honggao/URO-Bench); [HF](https://huggingface.co/datasets/ServiceNow-AI/eva-bench)
- **Artificial Analysis S2S leaderboard:** the industry-facing scoreboard combines Big Bench Audio, an FDB v1/v1.5 subset, τ-Voice, arena Elo and TTFA. — [AA S2S](https://artificialanalysis.ai/speech-to-speech)
  - It lists vendor cascades: Deepgram Voice Agent, ElevenLabs Agents, Cartesia Line, Inworld Realtime.
  - It lists S2S models: GPT-Live-1, Grok Voice 3.0, Phonic, StepAudio.
- **EVA leaderboard:** covers ElevenAgents, OpenAI Realtime, Gemini Live and Cartesia Managed Agents. Deepgram Voice Agent is planned. — [EVA limitations/roadmap](https://github.com/ServiceNow/eva/blob/main/website/src/components/limitations/LimitationsSection.tsx)
- **NVIDIA NeMo harness:** the community landscape lists an "NVIDIA NeMo Voice Agent Evaluation" harness built on EVA and τ² scenarios. This is secondary and was not verified at the NVIDIA source. — [HF landscape](https://huggingface.co/datasets/chatjesus/voice-agent-benchmark-landscape)
- **aiewf-eval:** built by Daily/Pipecat co-founder Kwindla Kramer and cited by Ultravox in vendor marketing. — [Ultravox](https://www.ultravox.ai/blog/why-speech-to-speech-is-the-future-for-ai-voice-agents-unpacking-the-aiewf-eval); [voiceaispace](https://www.voiceaispace.com/knowledge/repo/aiewf-eval)
- **Commercial uptake:** Coval reports more than 60 customers, including Zoom and Deepgram. — [SiliconANGLE](https://siliconangle.com/?p=773355)
- **Roark:** reports more than 10M call minutes. — [YC](https://www.ycombinator.com/companies/roark)

### Inferences
- **Where to publish:** for forehear's benchmark to be noticed, the venues that matter are the AA-style leaderboards and the EVA / τ ecosystem. A contribution such as a forehear-enabled cascade on EVA, or a τ-Knowledge voice run with speculative retrieval, would put forehear numbers where voice teams already look.
- **Star counts:** forehear's benchmark is unlikely to beat these on stars. Its niche value is being the only CPU-only, key-free and deterministic one.

### Gaps
- Citation counts were not retrieved.
- No source reliably attributes specific in-house benchmark usage to named voice-AI companies, beyond leaderboard listings and vendor blogs.

---

## 4. Weaknesses forehear's benchmark avoids, what it lacks, and recommended positioning

### Takeaway
forehear's benchmark avoids the weaknesses that recur across existing benchmarks:
- API-key dependence and cost
- non-deterministic, network-dependent latency
- synthetic TTS callers
- truncated forced-aligned prefixes in place of real interim revisions
- no notion of speculative work

Its own gaps:
- single-turn, read-aloud SQuAD-style questions
- one ASR engine (Vosk)
- BM25 over Wikipedia rather than an enterprise KB
- modelled tool latencies rather than measured ones
- no end-to-end LLM answer quality or TTS/turn-taking

**Recommended positioning:** "a component benchmark for the retrieval-timing layer". It complements EVA, τ-Voice and FDB, which judge whole agents, and it is the speech-real successor to Galbraith's text-prefix stabilization analysis and Stream RAG's synthetic-prefix protocol.

### Cited Findings

**Weaknesses of others, and what forehear does instead**
- **Commercial API keys and run-to-run variance:**
  - EVA needs OpenAI, ElevenLabs, Google Vertex and AWS Bedrock credentials. Its latency "will vary depending on APIs, deployments, and hardware". — [EVA](https://github.com/ServiceNow/eva)
  - FDB-v3 and τ-Voice evaluate commercial realtime APIs and use LLM judges. — [FDB-v3](https://arxiv.org/html/2604.04847); [tau2](https://github.com/sierra-research/tau2-bench)
  - aiewf-eval needs an Anthropic judge key. — [aiewf](https://github.com/kwindla/aiewf-eval)
  - VoiceBench needs gpt-4o-mini for open-ended subsets. — [VoiceBench](https://github.com/MatthewCYM/VoiceBench)
  - forehear: "All numbers are deterministic; rerun with `forehear bench`". — [forehear RESULTS.md](file:///home/user/Infinity/results/RESULTS.md)
- **Synthetic callers:**
  - EVA's own limitations say the simulator "may not fully replicate the natural disfluencies, hesitations" of real callers, and that it relies on a commercial system whose behaviour can change across versions. — [EVA limitations](https://github.com/ServiceNow/eva/blob/main/website/src/components/limitations/LimitationsSection.tsx)
  - VERA, Big Bench Audio and most VoiceBench subsets are TTS. — [VoiceBench](https://github.com/MatthewCYM/VoiceBench); [hyper.ai VERA](https://hyper.ai/en/datasets/46644)
- **Prefix realism:** Stream RAG uses 500 ms truncations of forced-aligned words, and Galbraith uses uniform word streams, acknowledging that "partial hypotheses get revised". — [Stream RAG](https://arxiv.org/html/2510.02044); [Galbraith](https://arxiv.org/html/2606.20113)
- **Scale of real-speech sets:** FDB-v3 has 100 real recordings from 12 speakers, against forehear's 4,018 human-recorded questions. — [FDB-v3](https://arxiv.org/html/2604.04847)
- **Leaderboard ignores speculation:** EVA runs speculative and non-speculative vendor stacks side by side without separating the effect. — [EVA experiment_setup](https://github.com/ServiceNow/eva/blob/main/docs/experiment_setup.md)
- **Static benchmarks may not predict user preference:** Talk Arena found τ ≤ 0.33. This is a caution that applies to forehear too. — [Talk Arena](https://huggingface.co/papers/2502.15919)

**What forehear's benchmark lacks, by its own documentation**
- Single-turn questions only.
- One ASR engine. Vosk revises differently from Deepgram and others.
- DSTC10 Track 2 is named as a possible multi-turn source. — [forehear docs/benchmark.md](file:///home/user/Infinity/docs/benchmark.md)
  - DSTC10 ships ASR text and n-best lists but no audio (verified by clone this session). It therefore cannot supply real interim timing without new recordings. — [DSTC10 repo](https://github.com/alexa/alexa-with-dstc10-track2-dataset)
- Tool latency comes from four modelled profiles (local, hosted_kb, rerank, web_search), not live measurement. — [forehear RESULTS.md](file:///home/user/Infinity/results/RESULTS.md)
- SQuAD-derived questions overlap lexically with their passages. (prior notes, inference) — [prior notes](file:///home/user/Infinity/docs/research/notes/benchmarks_datasets.md)

### Inferences

**Suggested positioning statement**
"forehear-bench measures *when* retrieved context is ready relative to end of turn, and *what it costs*, under real streaming-ASR revisions. It is deterministic, offline and key-free. Use it to choose a speculation policy; use EVA, τ-Voice or FDB-v3 to check that the whole agent got better."

**Claims to make, and caveats to keep**
- Claim novelty on three axes: (1) real interim revisions, (2) ready-at-EOT and calls/turn metrics, (3) determinism on CPU.
- Explicitly cite FDB-v3's pre-emptive-call rate and Galbraith's stabilization as prior and adjacent work.
- Avoid claiming "first to study speculative retrieval". Stream RAG, Galbraith and FDB-v3 all predate it.

**Highest-value extensions**

| Extension | Purpose |
|---|---|
| A second ASR (e.g. Whisper-streaming or NeMo FastConformer) | Answers the single-engine critique |
| A CRAG-based split | Allows direct comparison with Stream RAG and Galbraith; Galbraith's gold-passage labels are in its repo, though license is unclear |
| An adapter that emits forehear metrics as OpenTelemetry span attributes in Pipecat traces (Langfuse/Phoenix) | Makes production observability a distribution channel |
| An EVA cascade run with and without forehear | Shows an end-to-end EVA-X latency gain; EVA itself flags this as future work |

### Gaps
- No public multi-turn spoken dataset was confirmed that has KB passage labels, raw audio, and permissive licensing together. SpokenWOZ has audio but no passages and is non-commercial. DSTC10 has passages but no audio.
- Whether AudioCRAG-Human will be released, and under what license, is unknown.
- Whether EVA's maintainers would accept a speculative-retrieval cascade configuration is unknown.
