# Turn-taking prediction, full-duplex dialogue models, and latency budgets in voice agents (2022–2026)

Research date: 2026-11-03. Vendor numbers are labelled **[vendor]**. Independent or academic measurements are labelled **[measured]**. Numbers I could not re-verify in this session are labelled **[unverified]**.

## Q1. What end-of-turn / semantic turn-detection models exist, how do they work, how accurate and fast are they, and are they open?

### Takeaway
End-of-turn (EOT) detection has moved from fixed silence timeouts (about 500 ms to 2 s) to learned models. These fall into three groups: text-only transformers on the partial transcript (early LiveKit models), audio-only classifiers (Smart Turn, VAP), and fused audio and text models built into the STT (Deepgram Flux, AssemblyAI, LiveKit v1, OpenAI semantic_vad). The best published operating points reach about 10% false cutoffs at about 300 ms of post-speech latency, or about 5% at about 550–600 ms. In practice the system "knows" the user is done roughly 150–600 ms after speech stops. Several vendors now emit an *early/eager* EOT signal so that speculative work can start before the final decision.

### Cited Findings
**LiveKit turn detector**
- Older generation: a text-only model fine-tuned from Qwen2.5-0.5B-Instruct (396 MB) that runs on the STT transcript, at about 50–160 ms per inference. English model: 98.8% true positive and 87.5% true negative. Multilingual examples: Hindi 99.4% / 93.6%, Korean 99.3% / 88.7% **[vendor]** — [LiveKit docs](https://docs.livekit.io/agents/logic/turns/turn-detector)
- "Turn Detector v1" (blog dated 2026-06-17) adds audio. A semantic branch (audio encoder, adapter into the LLM embedding space, fine-tuned LM) is fused with an acoustic branch (encoder plus recurrent layer for prosody and timing). It reads audio directly, with no transcript wait, and uses only the current user turn. It covers 14 languages. **[vendor]** — [LiveKit blog](https://livekit.com/blog/solving-end-of-turn-detection)
- LiveKit's eot-bench results **[vendor-run, but the benchmark is open]**:
  - At a 300 ms budget: 9.9% false cutoffs, vs Deepgram Flux 12.9% and ultraVAD 27.7%.
  - At 600 ms: 4.5%, vs Soniox 5.5% and Flux 9.9%.
  - Mean latency is 295 ms at a 10% false-cutoff target and 543 ms at 5%.
  - A prior text-based version "cut unwanted interruptions by 39%".
  - Smart Turn, OpenAI and AssemblyAI were not in the comparison. — [LiveKit blog](https://livekit.com/blog/solving-end-of-turn-detection)
- Licensing: "v1-mini" is open-weight (pruned, quantized, for CPU). Code is Apache-2.0; weights use the LiveKit Model License. The full v1 is free on LiveKit Cloud. — [LiveKit blog](https://livekit.com/blog/solving-end-of-turn-detection)

**Pipecat Smart Turn (Daily)**
- Open-source, audio-only EOT classifier. — [GitHub pipecat-ai/smart-turn](https://github.com/pipecat-ai/smart-turn)
- v3 inference time: about 12 ms on CPU including preprocessing; 3.3 ms on L40S, 3.6 ms on L4, 4.3 ms on A100, 6.6 ms on T4 **[vendor]**. — [Daily blog v3](https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/)
- On a Pipecat Cloud 1x instance it takes about 65–70 ms. The unquantized GPU v3.1 is about 1% more accurate than the int8 build. — [GitHub](https://github.com/pipecat-ai/smart-turn); [Daily v3.1 blog](https://www.daily.co/blog/improved-accuracy-in-smart-turn-v3-1/)
- A third party reports v3.2 fp32 on Pipecat's 31,527-clip test set: 93.71% accuracy, F1 0.937, 3.51% false-positive rate, median 10.2 ms **[third-party, not verified against Pipecat]**. — [OpenHRI model card](https://huggingface.co/OpenHRI/smart-turn-streaming)

**Deepgram Flux** (STT with built-in EOT)
- About 260 ms EOT detection **[vendor]**. `eot_threshold` defaults to 0.7. — [Deepgram Flux docs](https://developers.deepgram.com/docs/flux/quickstart)
- Optional `eager_eot_threshold` (range 0.3–0.9) emits `EagerEndOfTurn` and `TurnResumed` events so the LLM can start speculatively. Deepgram warns this raises LLM calls by 50–70%. — [Deepgram Flux agent docs](https://developers.deepgram.com/docs/flux/agent.md)
- Telnyx (Jan 2026) turned eager EOT on by default at threshold 0.3. It reports about 150 ms lower median response latency when eager fires and about 350 ms savings in the top 5% tail. If the transcript changes, it falls back to standard handling **[vendor/integrator]**. — [Telnyx release note](https://telnyx.com/release-notes/automatic-eager-end-of-turn-deepgram-flux)

**AssemblyAI Universal-Streaming / Universal-3 Pro Streaming**
- Semantic plus acoustic turn detection. The current docs give these defaults: `end_of_turn_confidence_threshold` 0.4, `min_turn_silence` 400 ms (silence needed before a semantic EOT may fire), `max_turn_silence` 1280 ms (acoustic fallback).
- Presets: "fast" = 0.4 / 160 ms / 400 ms; "conservative" = 0.7 / 800 ms / 3600 ms.
- The older Universal-Streaming docs used a default threshold of 0.7.
- Universal-3.5 Pro uses punctuation-based detection, with `min_turn_silence` of 96 / 224 / 800 ms (min_latency / balanced / max_accuracy). — [AssemblyAI turn detection docs](https://www.assemblyai.com/docs/streaming/universal-streaming/turn-detection); [optimizing latency](https://www.assemblyai.com/docs/streaming/getting-started/optimizing-accuracy-and-latency)

**OpenAI Realtime API**
- `server_vad` is the default mode. Its `silence_duration_ms` sets how much silence ends a turn; the docs' example uses 500 ms. — [OpenAI VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad)
- `semantic_vad` uses a classifier on the user's words to judge completeness, with `eagerness` set to low, medium, high or auto. `low` waits longest. OpenAI does not publish accuracy or latency figures; the default `auto` is stated only by a third party. — [OpenAI VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad); [Bolna docs](https://www.bolna.ai/docs/openai-realtime.md)

**VAP (Voice Activity Projection)** (Ekstedt & Skantze 2022; real-time version by Inoue et al., IWSDS 2024)
- Takes stereo audio from both speakers and predicts their future voice activity, giving continuous hold or shift probabilities.
- Architecture: CPC encoder, per-channel self-attention, and cross-attention transformer.
- Runs in real time on CPU with a shortened context and "minimal performance degradation".
- The paper notes practical systems usually use 1–2 s silence timeouts.
- Open source. — [arXiv 2401.04868](https://arxiv.org/abs/2401.04868); [GitHub ErikEkstedt/VoiceActivityProjection](https://github.com/ErikEkstedt/VoiceActivityProjection); [inokoj/VAP-Realtime](https://github.com/inokoj/VAP-Realtime)

**Other**
- Krisp VIVA is named by Daily as a production turn-detection option. — [Daily STT benchmark](https://www.daily.co/blog/benchmarking-stt-for-voice-agents/)
- Community LiveKit-compatible detectors exist, e.g. Namo and a Scicom Qwen3-4B variant. The Scicom model reports 88.24% accuracy on only 238 synthetic samples, which is weak evidence. — [PyPI namo](https://pypi.org/project/livekit-plugins-namo-turn-detector/); [Featherless](https://featherless.ai/models/Scicom-intl/turn-detector-Qwen3-4B)

### Inferences
- Even the best EOT systems need about 250–550 ms after the last word to commit at acceptable false-cutoff rates (5–10%). This post-speech window is "free" time in every cascaded pipeline. Work started at the last word or earlier is hidden behind it.
- Eager EOT is the vendor-sanctioned form of speculation, and it already costs 50–70% more LLM calls. Look-ahead retrieval is the same idea moved earlier and onto a cheaper resource (retrieval rather than the LLM).
- A system that triggers on "eager EOT" (≈ last word plus 100–200 ms) gets much of the look-ahead benefit for KB-RAG with very little wasted work. Triggering mid-utterance only pays off when retrieval takes longer than the EOT window, as with web search, multi-hop retrieval or rerankers.

### Gaps
- No independent head-to-head benchmark covering all of LiveKit v1, Smart Turn, Flux, AssemblyAI and OpenAI semantic_vad under identical conditions. eot-bench is open but run by LiveKit; Daily said a turn-detection benchmark is "future".
- OpenAI semantic_vad accuracy and latency are unpublished.
- I did not verify a published end-of-turn latency for AssemblyAI's model, beyond its silence parameters.

## Q2. Do full-duplex / speech-native dialogue models do retrieval or tool use, and do they "think while listening"? How do they ground knowledge?

### Takeaway
First-generation full-duplex models (dGSLM, Moshi, SyncLLM, LSLM) have no retrieval or tools; they rely on parametric knowledge from small backbones. During 2025–2026 a research line appeared that does exactly "look-ahead" during user speech:
- Stream RAG (Meta, Oct 2025) predicts tool queries from partial speech.
- SHANKS (Microsoft/NTU, Oct 2025) does unspoken reasoning on each audio chunk and finishes 56.9% of tool calls before the user ends the turn.
- "Can speech LLMs think while listening?" (Meta, Oct 2025) uses an entropy-based question-completeness trigger.
- MoshiRAG (Kyutai, ICML 2026) retrieves asynchronously in the gap after the response starts.
- NVIDIA's frontend–backend delegation (Sep 2026) sends tool calls to a text LLM.
Production speech-native systems (GPT-Realtime, Gemini Live, Step-Audio 2) support tool calls. Latency in tool scenarios is still several seconds.

### Cited Findings
**First-generation full-duplex models**
- **Moshi** (Kyutai, 2024): full-duplex speech-text model. Theoretical latency is 160 ms (80 ms Mimi frame plus 80 ms acoustic delay); practical latency is about 200 ms on an L4 GPU. "Inner Monologue" predicts time-aligned text tokens alongside audio. The paper contrasts this with the 230 ms average human gap across 10 languages (Stivers et al.). No retrieval in the base model. — [arXiv 2410.00037](https://arxiv.org/abs/2410.00037); [GitHub kyutai-labs/moshi](https://github.com/kyutai-labs/moshi)
- dGSLM (Nguyen et al. 2022) is a two-channel textless dialogue model; LSLM ("Language Model Can Listen While Speaking", 2024) and SyncLLM (Meta/UW, 2024) are other early full-duplex designs. None ground knowledge externally. — [dGSLM arXiv 2203.16502](https://arxiv.org/abs/2203.16502); [LSLM arXiv 2408.02622](https://arxiv.org/abs/2408.02622); [SyncLLM arXiv 2409.15594](https://arxiv.org/abs/2409.15594) **[descriptions from prior knowledge; abstracts not re-fetched this session]**

**Stream RAG** (Arora et al., Meta + CMU, arXiv 2510.02044, Oct 2025)
- Method: issues tool or web/KG queries *during* user speech.
  - Fixed-Interval variant: a query every 1 s, with parallel threads.
  - Model-Triggered variant: decides every 500 ms block whether to query, one thread at a time.
- Backbone: Qwen2.5-Omni-7B, plus OpusLM. Dataset: AudioCRAG (CRAG queries rendered as speech).
- Results:
  - QA accuracy rises from 11.1% to 34.2% (vs no retrieval).
  - Tool-use latency falls by about 20%: P50 about 3.37 s to about 2.2 s; P90 4.9 s to 4.37 s.
  - First-token latency on human-spoken queries falls from 5.4 s to 3.6 s; on synthetic speech, from 5.9 s to 5.32 s.
  - Most tool latency comes from chunking and reranking web documents.
- Partial-speech errors happen. "Who founded rare" produced the query "Red Bull founder" before the correct "Who founded rare beauty". Training uses negative sampling and a NO_QUERY token to suppress redundant queries.
- The paper says the approach works for typed input too. — [arXiv abs](https://arxiv.org/abs/2510.02044); [HTML](https://arxiv.org/html/2510.02044)

**SHANKS** (Chiang et al., arXiv 2510.06917, Oct 2025)
- Streams input in fixed chunks and generates unspoken chain-of-thought after each chunk.
- 56.9% of tool calls complete before the user's turn ends.
- Interruption accuracy is 37.1% higher than a no-thinking baseline in a math scenario.
- No absolute latency figure. — [arXiv 2510.06917](https://arxiv.org/abs/2510.06917)

**"Can speech LLMs think while listening?"** (Shih et al., Meta, arXiv 2510.07497)
- An entropy-based "question completeness" metric decides when to start reasoning before the query ends.
- +4% accuracy on ARC-Easy at equal latency; DPO gives a 70% latency reduction with no accuracy loss; CoT gives 2.4x accuracy on spoken reasoning tasks. — [arXiv 2510.07497](https://arxiv.org/abs/2510.07497)

**MoshiRAG** (Chien, ..., Zeghidour, Défossez; arXiv 2604.12928, ICML 2026)
- A compact full-duplex model selectively queries stronger knowledge sources.
- Retrieval runs asynchronously in the gap between starting to respond and delivering the core content.
- Claims factuality comparable to the best public non-duplex speech LMs; retrievers are swappable without retraining. No latency numbers in the abstract. — [arXiv 2604.12928](https://arxiv.org/abs/2604.12928)

**NVIDIA frontend–backend delegation** (Hu et al., arXiv 2609.19334, Sep 2026)
- A duplex speech-to-text frontend emits a delegation token and forwards streaming ASR to a text backend (e.g. Qwen3-235B-A22B) that makes the tool calls.
- Results come back into the frontend via "prefill-and-repeat".
- 92–97% tool-call recall; 81.2% correct rejection of irrelevant calls.
- Beats GPT-realtime-mini and Qwen3-Omni-30B-A3B on EVA-Bench. No numeric latency. — [arXiv 2609.19334](https://arxiv.org/abs/2609.19334)

**Full-Duplex-Bench-v3** (Lin, Chen, Chen, Lee; arXiv 2604.04847, Apr 2026)
- Real human audio with five disfluency categories; chained API calls.
- GPT-Realtime has the best Pass@1 (0.600).
- Gemini Live 3.1 is fastest at 4.25 s; the cascaded Whisper → GPT-4o → TTS baseline is slowest at 10.12 s but has a perfect turn-take rate.
- Self-correction and multi-step reasoning are weak across all systems. — [arXiv 2604.04847](https://arxiv.org/abs/2604.04847)

**Step-Audio 2** (StepFun, arXiv 2507.16632)
- End-to-end audio LLM with RAG and tool calls (web search; audio search for timbre switching).
- On its own StepEval-Audio-Toolcall, web-search trigger precision/recall is 88.4 / 95.5 and type accuracy 98.4% **[vendor]**. — [arXiv 2507.16632](https://arxiv.org/abs/2507.16632); [GitHub](https://github.com/stepfun-ai/Step-Audio2)

**FireRedChat**: turns half-duplex pipelines into full duplex and invokes tools through a dialogue manager. — [arXiv 2509.06502](https://arxiv.org/html/2509.06502v1)

**Other models in scope** — not re-verified in this session; listed for completeness **[unverified]**:
- Qwen2.5-Omni (Thinker–Talker, [arXiv 2503.20215](https://arxiv.org/abs/2503.20215))
- Qwen3-Omni ([arXiv 2509.17765](https://arxiv.org/abs/2509.17765))
- MinMo ([arXiv 2501.06282](https://arxiv.org/abs/2501.06282); full-duplex latency recalled as about 600 ms theoretical / 800 ms practical — unverified)
- Freeze-Omni (frozen LLM backbone, [arXiv 2411.00774](https://arxiv.org/abs/2411.00774))
- GLM-4-Voice ([arXiv 2412.02612](https://arxiv.org/abs/2412.02612))
- Ultravox (speech-in, text-out adapter on an open LLM; [GitHub fixie-ai/ultravox](https://github.com/fixie-ai/ultravox)). Ultravox v0.7 is evaluated in FDB-v3.
- Sesame CSM (context-conditioned speech generation, i.e. a TTS-side model, not a full-duplex reasoner)

### Inferences
- "Look-ahead retrieval on partial input" is already validated in research (Stream RAG, SHANKS), but only for speech-native models. Measured savings are about 20% of tool latency, or about 1.8 s of first-token latency on human speech, where the baseline tool path takes several seconds (web search, chunking, reranking).
- The savings are large when retrieval is slow (seconds). For fast KB retrieval (around 100 ms) the gain is bounded by the retrieval time itself.
- Partial-query errors ("Red Bull founder") are a real failure mode. Systems need re-querying or deduplication logic (NO_QUERY, top-5 doc-set comparison) rather than committing to the first speculative query.
- MoshiRAG's trick is complementary: start speaking a filler or preamble and hide retrieval behind the first words of the response. This covers the same latency post-EOT rather than pre-EOT.

### Gaps
- Stream RAG does not report how early (as a fraction of the utterance) the correct query becomes predictable. SHANKS gives only the 56.9% completion rate.
- No paper found that applies look-ahead retrieval in a *cascaded* STT → LLM → TTS production stack and reports end-to-end savings. Salesforce VoiceAgentRAG (Q3) prefetches *between* turns, not during speech.

## Q3. Where does latency go in a cascaded voice agent? What does RAG add? What are human norms and vendor targets?

### Takeaway
Humans leave about 200–250 ms between turns but start planning their reply mid-way through the other person's turn. Cascaded agents typically land at 0.8–2 s voice-to-voice, and vendors target under 800 ms to 1 s.

Typical stage costs:
- **Endpointing / EOT wait:** 200–600 ms (the largest fixed cost)
- **STT finalization after VAD stop:** about 250–500 ms median
- **LLM time-to-first-token:** 100–800 ms, sometimes more than 2 s; the most variable stage
- **TTS first byte:** 40–500 ms

KB-RAG adds about 50–300 ms for a remote vector DB call, plus about 30–200 ms for embedding, plus up to about 0.6–1.3 s if a cross-encoder reranker is used. Web or tool calls add seconds.

### Cited Findings
**Human norms**
- Stivers et al. 2009 (PNAS 106(26):10587–10592): 10 languages; overlap avoided, gaps short. Language means fall within about 250 ms of the cross-language mean. — [PubMed](https://pubmed.ncbi.nlm.nih.gov/19553212/)
- The Moshi paper cites the cross-language average as 230 ms. — [Moshi arXiv](https://arxiv.org/abs/2410.00037)
- Human response planning begins mid-way through the incoming question (EEG). Production latencies for even a single word (about 600 ms or more) exceed typical gaps, so listeners must plan in overlap. — [Bögels, Magyari & Levinson 2015, Sci. Rep.](https://doi.org/10.1038/srep12881); [Levinson & Torreira 2015, Front. Psychol.](https://doi.org/10.3389/fpsyg.2015.00731) **[descriptions from prior knowledge; not re-fetched this session]**

**Vendor targets**
- LiveKit: conversations feel natural under 1 s end-to-end. — [LiveKit docs](https://docs.livekit.io/agents/models/pipelines/)
- Hamming: end-to-end target under 800 ms. — [Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it)
- VoiceAgentRAG: a voice budget of about 200 ms. — [arXiv 2603.02206](https://arxiv.org/html/2603.02206v1)

**Stage breakdowns** (practitioner and vendor blogs; indicative, not benchmarks)
- STT: 150–500 ms (100–200 ms when streaming). LLM TTFT: 200 ms to over 2 s as context grows. TTS first byte: 40–100 ms for fast streaming, 100–500 ms for standard. — [Hamming](https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it); [AlterSquare/Medium](https://altersquare.medium.com/voice-agent-latency-where-the-2-3-second-delay-actually-lives-in-the-pipeline-and-how-to-reduce-it-50d54c2bd211)
- Fast hosted LLMs: 100–200 ms TTFT; frontier models: 400–800 ms. — [Sayna](https://sayna.ai/blog/sub-second-voice-agent-latency-practical-architecture-guide)
- Perceived latency ≈ end-of-utterance delay + LLM TTFT + TTS TTFB, with STT folded into the EOU delay. — [HF latency playbook](https://huggingface.co/blog/dvalle08/voice-agent-latency-playbook)
- Deepgram publishes a per-turn latency report split into STT, LLM TTFT and TTS segments. — [Deepgram latency report](https://developers.deepgram.com/docs/voice-agent-latency-report)

**STT finalization** (Daily STT benchmark, Feb 2026) **[measured, single-vendor-run]**
- Setup: 1,000 real English utterances, 20 ms realtime chunks, Silero VAD with a 200 ms stop threshold.
- Time from VAD stop to final transcript (TTFS) median: Deepgram Nova-3 about 247 ms, Soniox about 249 ms, Speechmatics about 495 ms. Medians vary about 5x across vendors.
- Services without an explicit finalization signal force the app to wait about the P95 on every turn. — [Daily blog](https://www.daily.co/blog/benchmarking-stt-for-voice-agents/); [GitHub pipecat-ai/stt-benchmark](https://github.com/pipecat-ai/stt-benchmark)

**End-to-end in tool scenarios**
- Gemini Live 3.1 averages 4.25 s; a Whisper → GPT-4o → TTS cascade averages 10.12 s. — [FDB-v3](https://arxiv.org/abs/2604.04847)

**RAG costs**
- VoiceAgentRAG (Salesforce, Mar 2026):
  - Remote Qdrant Cloud query: 97–307 ms, mean about 110–120 ms. Remote embedding API: about 200 ms. GPT-4o-mini generation: 500–8000 ms.
  - A semantic cache hit takes 0.35 ms, saving about 110 ms per hit (75% hit rate on 200 scripted queries). Local FAISS on 76 chunks takes about 0.1 ms.
  - The authors concede that LLM variance dominates, so retrieval savings are "often invisible" end-to-end. — [arXiv 2603.02206](https://arxiv.org/html/2603.02206v1); [GitHub](https://github.com/SalesforceAIResearch/VoiceAgentRAG)
- A production vector DB query usually costs 50–300 ms of network round trip. — [arXiv 2603.02206](https://arxiv.org/pdf/2603.02206)
- Reranker: median retrieval latency rose from about 20 ms (hybrid search) to 585 ms with 10 candidates and to 1,258 ms with 20 candidates, with no nDCG gain in that test **[single blog benchmark]**. Embedding adds about 30 ms (local). — [DEV Community](https://dev.to/neeraj_singhi_golang/retrieval-latency-budgets-in-rag-pipelines-vector-search-reranking-and-the-timeout-cascade-55jk)
- Practitioner budget for query rewrite + vector search + rerank: about 200–300 ms within a sub-800 ms target. Practitioners already recommend starting retrieval on partial ASR transcripts. — [FutureAGI](https://futureagi.com/blog/how-to-build-rag-powered-voice-ai-agents-2026/)
- Web/tool path: about 3.4 s P50 tool latency in Stream RAG's open-book baseline (web retrieval plus chunking and reranking). — [Stream RAG HTML](https://arxiv.org/html/2510.02044)

### Inferences
Illustrative budget for a well-tuned cascaded agent with KB-RAG, assembled from the sources above (not a measured run):

| Stage | Time |
|---|---|
| EOT wait | about 300 ms |
| STT final | overlaps the EOT wait or adds about 0–250 ms |
| Query embedding + remote vector search | about 150–300 ms |
| Reranking | 0–600 ms |
| LLM TTFT | about 200–500 ms |
| TTS first byte | about 100 ms |
| Network/transport | about 50–100 ms |

This totals about 0.8–1.6 s. Retrieval is about 10–35% of the total without a reranker and can be the largest single item with a reranker or web search.

- Look-ahead retrieval can at best remove the retrieval term from the critical path. That is about 100–300 ms for remote vector KB, about 0.5–1.3 s with a reranker, and seconds for web search or tools.
- Part of that saving is already free if retrieval simply starts at the eager-EOT or VAD-stop signal, since retrieval can overlap the remaining EOT confirmation and STT finalization (about 250–500 ms).

### Gaps
- No independent, multi-vendor, end-to-end cascaded latency benchmark with a per-stage breakdown was found. Most stage ranges come from vendor or practitioner blogs.
- No measured web-search API latency in isolation (e.g. Bing, Brave, Exa) was found in this session.

## Q4. How long are user utterances, and how many seconds of "free" compute exist between when intent becomes predictable and end-of-turn?

### Takeaway
Evidence is thin. Voice search queries average about 2.4–3.9 words, roughly 1–2 s of speech. Conversational and agent turns are longer but under-measured. No study was found that directly measures the lead time between "query intent predictable" and end of turn in a voice-agent setting. The closest proxies are SHANKS (56.9% of tool calls finished before the turn ended), Stream RAG (correct query sometimes emitted before the utterance ends; tool latency down about 20%), and human EEG evidence that planning starts mid-question.

### Cited Findings
- Voice search queries: about 3.9 words on average, vs about 10.6 words for LibriSpeech sentences. — [Mondegreen, arXiv 2105.09930](https://arxiv.org/pdf/2105.09930)
- Spoken queries: 2.43 terms on average vs 2.21 for typed. — [Du & Crestani 2004 (Strathclyde)](https://strathprints.strath.ac.uk/22479/)
- Baidu: no significant difference in query length between voice and text search. — [arXiv 1911.11063](https://arxiv.org/pdf/1911.11063)
- Lab study with complex TREC topics: voice queries average 23.1 words vs 9.5 for text. Long, task-driven spoken requests are much longer than search queries. — [Crestani & Du 2006, "Written versus spoken queries"](https://strathprints.strath.ac.uk/60362/)
- Vendor claims of 29-word average voice queries have no stated methodology and conflict with the academic data. — [DigitalApplied](https://www.digitalapplied.com/blog/voice-search-statistics-2026-data-points)
- SHANKS: 56.9% of tool calls complete before the user's turn ends. — [arXiv 2510.06917](https://arxiv.org/abs/2510.06917)
- Stream RAG: first-token latency on *human* speech drops 1.8 s (5.4 to 3.6 s), much more than on synthetic speech (0.58 s). This suggests natural human queries leave more mid-utterance slack, plausibly because of disfluencies and slower delivery. — [Stream RAG HTML](https://arxiv.org/html/2510.02044)
- The entropy-based "question completeness" signal gives finer control over when to start reasoning than heuristics. — [arXiv 2510.07497](https://arxiv.org/abs/2510.07497)
- VoiceAgentRAG notes the background prefetcher gets about 3–7 s per turn *between* turns (during agent speech and user think time). The benefit shrinks when exchanges come faster than about 2 s. — [arXiv 2603.02206](https://arxiv.org/html/2603.02206v1)

### Inferences
- At about 2.5–3 words per second, a 4–10-word query lasts about 1.5–4 s. If the content words (entity, intent) arrive in the final third, which is common for English questions like "what's the return policy for *orders shipped internationally*", the predictable-intent lead time before the last word is often only a few hundred ms to about 1 s. Adding the EOT wait (about 250–550 ms) and STT finalization gives a total pre-response window of roughly 0.5–1.5 s for typical short queries.
- Longer agentic requests ("I'd like to change my flight from Tuesday to ... because ...") likely give several seconds, but the final intent can also change late (self-corrections). FDB-v3 found self-correction a consistent failure point.
- The *between-turn* window (3–7 s while the agent speaks) is larger than the *within-utterance* window. Predictive prefetch on the dialogue state (VoiceAgentRAG style) may be worth comparing with partial-transcript look-ahead.

### Gaps
- No corpus study found that measures "time from intent-identifiability to end of turn" for task-oriented voice agents, e.g. in call-centre data.
- No distribution (median/P90) of user-turn durations in production voice agents was found from a primary source.

## Q5. Interim/partial ASR transcripts: stability, revision rates, and interim latency

### Takeaway
Partials arrive fast: first-partial latency is about 20–130 ms for top streaming APIs, per Artificial Analysis. Most modern models already reach their final accuracy at the first partial. Partials do get revised, though. Google's RNN-T analysis found 0.04–0.37 unstable words per final word, and longer partial-emission intervals sharply improve stability at a latency cost. For retrieval, the semantic error from partials is usually in the last one or two words, the very words that often carry the entity.

### Cited Findings
**Google RNN-T stability study** (Shangguan et al., Interspeech 2020)
- Metrics:
  - UPWR (unstable partial word ratio): unstable words divided by words in the final hypotheses.
  - UPSR (unstable partial segment ratio): revised segments divided by utterances.
- Results:
  - Single-domain models: UPWR 0.11–0.21, UPSR 0.43–0.82.
  - Multi-domain: UPWR 0.37 / UPSR 1.19, i.e. more than one revision per utterance.
  - Adding text normalization and domain-id: UPWR 0.14 / UPSR 0.48.
  - Raising the partial emission interval from 50 to 200 ms cut UPWR by 71.6% (to 0.04) and UPSR by 68.8% (to 0.15), at about +75 ms mean partial delay.
  - Mixed-case and multi-domain training improved quality but degraded stability. — [arXiv 2006.01416](https://arxiv.org/abs/2006.01416); [ar5iv](https://ar5iv.labs.arxiv.org/html/2006.01416)

**Artificial Analysis AA-WER Streaming** **[independent]**
- First-partial latency and WER: Deepgram Flux about 0.019 s / 7.36%; Deepgram Nova-3 Realtime about 0.057 s / 6.69%; Cartesia Ink-2 about 0.072 s / 4.33%; ElevenLabs Scribe v2 Realtime about 0.132 s / 3.65%.
- "Most models reach their final accuracy by the first partial." — [Artificial Analysis](https://artificialanalysis.ai/articles/new-streaming-speech-to-text-benchmark-aa-wer-streaming)

**AssemblyAI benchmark page** **[vendor]**
- U3.5 Realtime Pro: 0.191 s minimum latency, 4.02% WER. Nova-3 Realtime: 0.066 s, 6.59%. Speechmatics Realtime Enhanced: 0.317 s, 8.05%. — [AssemblyAI benchmarks](https://www.assemblyai.com/benchmarks)
- Hamming production data cited by AssemblyAI: Universal-3 Pro Streaming 307 ms P50 / 8.14% WER vs Nova-3 516 ms / 9.87% over 4M+ calls **[vendor-cited, secondhand]**. — [AssemblyAI blog](https://www.assemblyai.com/blog/deepgram-alternatives)

**Deepgram docs**
- Nova-3 targets sub-300 ms streaming latency.
- Finals are delayed by endpointing, which mixes transcript latency with EOT latency. — [Deepgram measuring streaming latency](https://developers.deepgram.com/docs/measuring-streaming-latency.mdx)

**Whisper-based streaming (WhisperPipe, arXiv 2604.25611)**
- Uses a similarity-based stability score for re-decoded prefixes.
- Cutting audio at word timestamps rather than fixed chunks reduces mid-word cuts that inflate revision rates. — [arXiv 2604.25611](https://arxiv.org/pdf/2604.25611)

**Stream RAG partial-query errors**
- Partial speech yields wrong intermediate retrieval queries, e.g. "Who founded rare" became "Red Bull founder".
- Removing negative-sample training dropped accuracy from 39.8 to 36.5. — [Stream RAG HTML](https://arxiv.org/html/2510.02044)

**Eager EOT reverts**: Telnyx's eager EOT falls back when "the transcript changes mid-turn", i.e. partial revisions do occur at the end of turns in production. — [Telnyx](https://telnyx.com/release-notes/automatic-eager-end-of-turn-deepgram-flux)

### Inferences
- With first partials at 20–130 ms and near-final accuracy, the transcript stream is not the bottleneck for look-ahead retrieval. The question is semantic: has the user said the retrieval-relevant part yet?
- The tail of a partial (the most recent one or two words) is the unstable part. A look-ahead system should weight or embed only the stable prefix, or re-query when the top-k document set changes, as Stream RAG's NO_QUERY rule does with the top-5 overlap.
- Retrieval keyed on embeddings is likely more tolerant of small revisions than exact-match KG queries. Stream RAG treats web queries (doc-set overlap) differently from KG queries (exact match), which supports this.

### Gaps
- No vendor publishes partial revision rates (UPWR-style) for Deepgram, AssemblyAI, Google, AWS Transcribe, NVIDIA Riva/Parakeet or Whisper-streaming. I found no independent stability benchmark across commercial APIs.
- AWS Transcribe "partial results stabilization" and Google's `stability` field on interim results exist (known from docs, not re-fetched here). No published accuracy-vs-stability numbers for them were found in this session.
- NVIDIA Riva/Parakeet streaming partial latency and stability figures were not located in this session.
