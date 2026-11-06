# Academic systems overlapping with forehear (speculative retrieval on interim ASR), status as of 6 Nov 2026

This file builds on /home/user/Infinity/docs/research/notes/academic_speculative_retrieval.md and related_techniques.md, re-checking and extending them.

**Method.** About 30 tool calls on 6 Nov 2026:
- arXiv abs/HTML pages and the arXiv API
- Semantic Scholar citation lists for Stream RAG, SHANKS and PredGen
- GitHub repository search via `gh api search/repositories`
- the Hugging Face model and dataset search API
- project pages

**Limits on what "not found" means.** The session could search GitHub but could not open repository metadata directly (403 on `repos/...`), so licences come from the search API's `license` field. "Not found as of Nov 2026" means that neither GitHub repo search nor Hugging Face search, using the paper's title or keywords, returned a repository. It does not prove that none exists.

**forehear claims used for comparison** (from /home/user/Infinity/README.md):
- 43% of turns retrieve a correct passage from the interim transcript 1 s before the last word; 76% do from the final transcript.
- About 3.5 retrieval calls per turn by default, and about 2.6 for the lean or Adaptive(budget=3) variants.
- Reuse validators trade recall@5 for latency.
- LocalAgreement-2 loses to a plain timer.
- The benchmark uses real human speech.

---

## Q1. Has any of these released code that would let others do what forehear does? Which is closest to a usable library? (Per-paper status records)

### Takeaway
No academic group has released a reusable library that does what forehear does: firing policies, reuse validators, cancellation and waste accounting for retrieval on interim ASR, plus an offline benchmark on real human speech.

What has been released falls into three groups:
- **Research harnesses with no licence:**
  - Galbraith's `stablize_CRAG` (simulated text streams, no ASR)
  - RASSG (`daijinhu/RASSG`)
  - Endpoint Anticipation (`bloodraven66/EndpointAnticipation`)
  - Voice-Light (`BertilBraun/Voice-Light`)
- **Model releases where retrieval is triggered by the model, not on interim ASR:** MoshiRAG weights (CC-BY 4.0) with MIT/Apache code; NVIDIA NemotronLabs VoiceChat weights.
- **A packaged library with a different trigger:** Salesforce's VoiceAgentRAG prefetches predicted *follow-up* topics into a semantic cache per utterance, not on interim transcripts.

Stream RAG (Meta/CMU) promised its training code and the AudioCRAG-Human benchmark more than a year ago, and still has not released them. It is still v1 on arXiv, with no repository and no Hugging Face dataset. On the code side, the closest thing to "usable" is VoiceAgentRAG, which is a library but uses a different mechanism. On the mechanism side, the closest is Heartbeat Thinking (Ant International), which has no code.

### Cited Findings

#### Core "retrieval/tool calls on partial speech" papers

**1. Stream RAG: Instant and Accurate Spoken Dialogue Systems with Streaming Tool Usage** (closest prior art)
- **Authors:** 17 authors: Siddhant Arora, Haidar Khan, Kai Sun, Xin Luna Dong, Sajal Choudhary, Seungwhan Moon, Xinyuan Zhang, Adithya Sagar, Surya Teja Appini, Kaushik Patnaik, Sanat Sharma, Shinji Watanabe, Anuj Kumar, Ahmed Aly, Yue Liu, Florian Metze, Zhaojiang Lin. Affiliation is Meta plus CMU (Arora, Watanabe) — [arXiv abs](https://arxiv.org/abs/2510.02044)
- **Venue/date:** arXiv 2510.02044, v1 2 Oct 2025, still the only version on 6 Nov 2026. No venue in the Comments field — [arXiv abs](https://arxiv.org/abs/2510.02044); [arXiv API listing](https://arxiv.org/abs/2510.02044v1)
- **Mechanism, two variants** — [arXiv HTML](https://arxiv.org/html/2510.02044v1)
  - *Fixed-Interval:* a query every 1 s block, B parallel tool threads, and an end-of-speech "reflector" that reuses the earliest block whose top-5 web docs or KG output match the final query's.
  - *Model-Triggered:* post-trained to emit NO_QUERY or a new query every 500 ms. A single thread, where a new query cancels the in-flight call. Negative sampling at p=0.1 teaches recovery from wrong queries.
- **Headline numbers:**
  - QA accuracy rises from 11.1% (closed book) to 34.2% on AudioCRAG, "up to 200% relative"; tool-use latency falls about 20% — [arXiv abs](https://arxiv.org/abs/2510.02044)
  - Tool-latency savings of 20.7% on synthetic speech and 53.4% on human speech, and 10.7% for the fixed-interval variant — [arXiv HTML](https://arxiv.org/html/2510.02044v1)
- **Release status:**
  - The paper says the authors "will open source our training code and AudioCRAG-Human benchmark" — [arXiv HTML](https://arxiv.org/html/2510.02044v1)
  - As of Nov 2026, no repository is linked on the abs page — [arXiv abs](https://arxiv.org/abs/2510.02044)
  - GitHub search for "AudioCRAG" and "stream rag spoken" returned no official repository.
  - Hugging Face dataset search for "AudioCRAG" returned nothing.
  - **Not found as of Nov 2026.** The underlying text benchmark is public: [facebookresearch/CRAG](https://github.com/facebookresearch/CRAG) (313 stars, licence NOASSERTION, last push Jun 2025).
- **Community emulation:** [ehzawad/streamRAG-audio](https://github.com/ehzawad/streamRAG-audio) is an MIT-licensed, 0-star, single-GPU emulation of the Model-Triggered policy (Qwen3.5-9B + bge-large + faster-whisper + Chatterbox), created Jul 2026 (GitHub search API metadata).
- **Overlap with forehear:** the same problem, retrieval while the user speaks. The fixed-interval variant plus reflector maps onto forehear's timer policy plus a ResultOverlap-style validator; the reflector's test is exact top-5 identity.
- **Differences from forehear:**
  - Web search and KG over CRAG rather than a private passage index.
  - A trained LLM trigger rather than training-free policies.
  - No calls/turn or waste accounting is reported.
  - AudioCRAG-Human (618 human-recorded queries) is read speech of CRAG questions, not spontaneous interim ASR streams.

**2. When Does Streaming Tool Use Help? Characterizing Tool-Intent Stabilization in Streaming RAG**
- **Authors:** Elroy Galbraith, SMG Labs (single author) — [arXiv HTML v2](https://arxiv.org/html/2606.20113v2)
- **Venue/date:** arXiv 2606.20113. v1 18 Jun 2026, v2 19 Jun 2026; cs.CL and cs.IR; no venue — [arXiv abs](https://arxiv.org/abs/2606.20113)
- **Mechanism:** an analysis paper.
  - Each CRAG question is streamed as a *uniform simulated word sequence* at cadence δ (words/s). There is no audio or ASR.
  - Retrieval is BM25 over 120-word windows, with a dense all-MiniLM-L6-v2 arm.
  - The harness is fixed-interval Trigger + Threads + Reflector, calibrated to Stream RAG's stage latencies.
  - It defines self-consistency stabilization t_sc and sufficiency stabilization t_suf (first prefix whose top-k contains the gold passage), and derives the bound H = min(L, max(0, (n − t*)/δ)).
  - Source: [arXiv HTML v2](https://arxiv.org/html/2606.20113v2)
- **Headline numbers** (all from [arXiv HTML v2](https://arxiv.org/html/2606.20113v2)):
  - 73.9% of queries are "streamable" at L=600 ms, δ=3 w/s, θ=0.8. That rises to 95.2% on the 21.3% retrieved-gold subset.
  - Mean φ_suf is 0.26 (median 0.14). Mean φ_sc is 0.67 (median 0.73).
  - In a 60-question replay, measured savings were 1122 ms against a 590 ms bound.
  - The bound does not rank individual queries (Spearman ρ ≈ +0.13).
  - Net-negative savings occurred in 1.7% of queries.
  - Dense retrieval moves mean φ_suf to 0.31.
  - Calls/turn is not reported.
- **Code:** [github.com/elroy-galbraith/stablize_CRAG](https://github.com/elroy-galbraith/stablize_CRAG), which includes gold-passage labels — [arXiv HTML v2](https://arxiv.org/html/2606.20113v2). GitHub search metadata: 0 stars, no licence detected, created 17 Jun 2026, last push 22 Jun 2026.
- **Overlap with forehear:** the same question of how early the query is retrievable. Its "sufficiency" criterion, gold passage in top-k, matches forehear's retrievability metric.
- **Differences from forehear:**
  - Text simulation with no ASR revisions; the paper names this as a limitation.
  - Only a fixed-interval trigger; it suggests but does not test stability-gated triggers.
  - No validator or recall trade-off, and no cost per turn.

**3. Hiding Tool Latency in On-Device Cascaded Voice Agent through Speculative Execution**
- **Authors:** Kyudan Jung (a Qualcomm Technologies intern and KAIST student), Hyunsin Park, Yoonhyung Lee, Jinhwan Park, Jinhyeok Yang, KiHyun Nam, Jaegul Choo and Jinkyu Lee. Affiliations are Qualcomm AI Research and KAIST AI — [arXiv HTML](https://arxiv.org/html/2610.07641)
- **Venue/date:** arXiv 2610.07641 (cs.SD), 6 Oct 2026, 5 pages; no venue — [arXiv HTML](https://arxiv.org/html/2610.07641)
- **Mechanism:**
  - A *rule-based* predictor runs on the partial ASR after 6 words, every 5 further words, or after a pause over 300 ms.
  - It splits the transcript into clauses on punctuation and conjunctions and maps each clause to a tool tuple from 12 topic categories.
  - It executes the search (Exa API), caches the result, and injects valid cached results into a Llama-3.2-3B prompt on the NPU of a Galaxy S26 Ultra.
  - A rule-based self-correction check, and a fallback of looking up the cache first and calling the tool on a miss.
  - Read-only tools only.
  - Source: [arXiv HTML](https://arxiv.org/html/2610.07641)
- **Headline numbers:**
  - Median time-to-first-audio 5.79 → 4.60 s; p99 19.76 → 15.10 s.
  - Tool-call F1 44.8% → 60.6%.
  - Cache-ready rate 47.7%.
  - Wasted speculative calls 47 (prefetch-only) → 5 (final method).
  - 146 *TTS-synthesized* utterances (Gemini TTS), not human speech.
  - Source: [arXiv HTML](https://arxiv.org/html/2610.07641)
- **Code:** none linked in the paper. Not found as of Nov 2026.
- **Overlap with forehear:** the word-count trigger is close to forehear's StablePrefix. It has cache-and-validate, and it counts wasted calls.
- **Differences from forehear:** web search via an on-device LLM, not passage retrieval; synthetic speech; no recall metric; no calls/turn.

**4. Heartbeat Thinking: Speculative Reasoning and Tool Execution While Listening in Realtime Voice Agents** (NEW, the closest new mechanism)
- **Authors:** Zhenyu Zhang, Kewei Fu, Yongqi Tong, Chenzhi Zheng, Wei Wu, Jiang-Ming Yang and Jianshe Li, all at Ant International — [arXiv HTML](https://arxiv.org/html/2610.26233)
- **Venue/date:** arXiv 2610.26233, 19 Oct 2026; no venue — [arXiv HTML](https://arxiv.org/html/2610.26233)
- **Mechanism:**
  - A "Thinker" LLM runs every Δ=500 ms on the latest partial ASR plus completed results. At most K=2 run at once, and a trigger is skipped when both slots are busy.
  - It outputs noop, think, or think plus tool calls. Tools run asynchronously and results are keyed by tool-call ID.
  - At VAD end of speech, all unfinished Thinker and tool jobs (including queued calls) are cancelled.
  - The Responder checks the completed preparation against the full request with ReAct, reuses matching results, and runs missing calls itself.
  - Source: [arXiv HTML](https://arxiv.org/html/2610.26233)
- **Headline numbers:**
  - FDBench v3: mean final-response latency 6.90 → 4.39 s (−36.4%), 45.7% below Pipecat; tool coverage 34.67% → 50.67%; Pass@1 57 → 65.
  - AudioCRAG: correct-answer rate 57.24% → 55.49%, a *drop*.
  - SpeechFCEval: accuracy 67.95% → 66.85%, a *drop*.
  - About 4% hallucination from outdated speculative results.
  - Token, cost and wasted-call accounting is not reported and is listed as future work.
  - Source: [arXiv HTML](https://arxiv.org/html/2610.26233)
- **Code:** no Heartbeat repository is linked. It uses the public [FunAudioLLM/SpeechFCEval](https://huggingface.co/datasets/FunAudioLLM/SpeechFCEval) and [Full-Duplex-Bench](https://github.com/DanielLin94144/Full-Duplex-Bench) — [arXiv HTML](https://arxiv.org/html/2610.26233). Not found as of Nov 2026.
- **Overlap with forehear:** a fixed-interval policy on interim ASR, with a concurrency cap, cancellation at end of turn and reuse validation. It benchmarks against Pipecat and LiveKit.
- **Differences from forehear:**
  - The LLM is the trigger and the validator; forehear uses cheap rules and result overlap.
  - Generic tool calls, not passage retrieval.
  - No calls/turn.

**5. RASSG: Repair-Aware Semantic Survival Gating for Streaming Tool Execution** (NEW; tests LocalAgreement directly)
- **Authors:** Daijin Hu and Xi Wang, Beihang University — [arXiv HTML](https://arxiv.org/html/2610.14659)
- **Venue/date:** arXiv 2610.14659 (cs.AI), 10 Oct 2026 — [arXiv abs](https://arxiv.org/abs/2610.14659)
- **Mechanism:**
  - **Launch:** fire when 3 consecutive ASR hypotheses contain identical non-empty arguments, a stricter LocalAgreement.
  - **Cancel:** combine calibrated argument-invalidity risk with execution cost, and cancel at the last point before the tool's effect becomes irreversible.
  - Targets *side-effecting* tools under user self-repairs.
  - Source: [arXiv abs](https://arxiv.org/abs/2610.14659)
- **Headline numbers** (stale-execution rate / delay on successful trajectories) — [arXiv HTML](https://arxiv.org/html/2610.14659)

  | Method | ReCAST | FDB-v3 | Audio2Tool |
  |---|---|---|---|
  | End of utterance | 0.58% / 8.676 s | 40.00% / 23.880 s | 52.73% / 9.196 s |
  | LocalAgreement-2 | 50.00% / 3.954 s | 65.00% / 9.210 s | 62.91% / 8.135 s |
  | Stream RAG | 50.00% / 5.312 s | 86% / 19.997 s | 84.50% / 8.255 s |
  | Speculative Tool Calling | 50.00% / 3.480 s | 77% / 9.280 s | 81.05% / 8.216 s |
  | RASSG | 3.15% / 3.676 s | 57% / 11.072 s | 54.65% / 8.797 s |

  ReCAST is synthetic speech.
- **Code:** [github.com/daijinhu/RASSG](https://github.com/daijinhu/RASSG) — [arXiv abs](https://arxiv.org/abs/2610.14659). GitHub search metadata: 0 stars, no licence detected, created and last pushed 24 Sep 2026.
- **Overlap with forehear:** firing and cancellation policies on interim ASR, with LocalAgreement-2 and Stream RAG as baselines.
- **Difference from forehear:** it optimizes *staleness of irreversible actions*, not retrieval recall or calls/turn, and does not separate read-only tools.

**6. Heard Enough to Act: Early Tool Calling in Spoken Dialogue Systems** (NEW)
- **Authors:** Yizhou Peng, Chen Chen, Donghang Wu, Hexin Liu and Eng Siong Chng. The abs page shows no affiliation; Chng's group is at NTU Singapore, which is an unverified inference. Submitted to ICASSP 2027 — [arXiv abs](https://arxiv.org/abs/2610.34653)
- **Venue/date:** arXiv 2610.34653, 26 Oct 2026 — [arXiv abs](https://arxiv.org/abs/2610.34653)
- **Mechanism:** a synthetic TTS corpus labelled with the "earliest actionable point": 26,694 dialogues, 786 h, 48 domains, plus an audio rendering of τ²-bench. An omni-modal LM makes causal chunk-level decisions on whether to call a tool, and emits partial transcripts — [arXiv abs](https://arxiv.org/abs/2610.34653)
- **Numbers:** tool-state macro-F1 of 0.48 (held-out) and 0.47 (τ²-bench). For correct calls, the mean lead over a turn-end cascade is 1.8–2.0 s in-domain and 1.1 s on τ²-bench — [arXiv abs](https://arxiv.org/abs/2610.34653)
- **Code:** the authors say they "will open-source the pipeline and the training scripts". Not found as of Nov 2026 — [arXiv abs](https://arxiv.org/abs/2610.34653)

#### Thinking-while-listening and speculative-generation papers

**7. SHANKS: Simultaneous Hearing and Thinking for Spoken Language Models**
- **Authors and affiliations:** Cheng-Han Chiang (NTU and Microsoft), Hung-yi Lee (NTU), and Xiaofei Wang, Linjie Li, Chung-Ching Lin, Kevin Lin, Shujie Liu, Zhendong Wang, Zhengyuan Yang and Lijuan Wang (Microsoft) — [project page](https://d223302.github.io/SHANKS/)
- **Venue/date:** arXiv 2510.06917, v2; Comments say "Work in progress"; no venue — [arXiv API](https://arxiv.org/abs/2510.06917)
- **Mechanism:** after each fixed-duration audio chunk it produces unspoken chain-of-thought, which may interrupt the user or call tools.
- **Numbers:** completes 56.9% of tool calls (ComplexFuncBench, Booking.com APIs) before the user finishes; interruption accuracy is 37.1% higher.
- **Code:** none on the project page — [project page](https://d223302.github.io/SHANKS/). Not found as of Nov 2026.
- **Overlap:** the timing of tool calls during speech. It is used as the "Window Thinking" baseline in Heartbeat — [Heartbeat HTML](https://arxiv.org/html/2610.26233)

**8. Can Speech LLMs Think While Listening?**
- **Authors:** Yi-Jen Shih, Desh Raj, Chunyang Wu, Wei Zhou, SK Bong, Yashesh Gaur, Jay Mahadeokar, Ozlem Kalinli and Mike Seltzer. The names match Meta's speech team, but that is unverified on the abs page.
- **Venue/date:** arXiv 2510.07497, Oct 2025.
- **Mechanism:** an entropy-based "question completeness" signal to start reasoning early.
- **Numbers:** +4% on ARC-Easy at equal latency; DPO cuts latency 70% with no accuracy loss.
- **Code:** none was found in the prior notes; not re-searched this session.
- Source: [arXiv abs](https://arxiv.org/abs/2510.07497)
- **Overlap:** the completeness signal is a learned "when to fire" policy, but for reasoning, not retrieval.

**9. PredGen: Accelerated Inference of LLMs through Input-Time Speculation for Real-Time Speech Interaction**
- **Authors:** Shufan Li and Aditya Grover (UCLA is probable, not verified).
- **Venue/date:** arXiv 2506.15556, v2 Oct 2025; no venue in the comments ("16 pages, 4 figures") — [arXiv API](https://arxiv.org/abs/2506.15556)
- **Mechanism:** speculative *response generation* on partial input, then verify against the final input and accept, partially reuse or discard.
- **Numbers:** about 2x latency reduction in simulation (LMSys, MT-Bench) — [arXiv abs](https://arxiv.org/abs/2506.15556)
- **Code:** GitHub search "PredGen input-time speculation" found nothing. Not found as of Nov 2026.
- **Difference from forehear:** speculates LLM output, not retrieval.

**10. Endpoint Anticipation for Low-Latency Spoken Dialogue**
- **Authors:** Sathvik Udupa, Shinji Watanabe, Petr Schwarz and Jan Černocký (Brno University of Technology and CMU).
- **Venue/date:** accepted at Interspeech 2026; arXiv 2606.13450, Jun 2026 — [arXiv API listing](https://arxiv.org/abs/2606.13450); [arXiv HTML](https://arxiv.org/html/2606.13450)
- **Mechanism:** a 25M-parameter streaming transformer forecasts end of turn 320–2560 ms ahead and forks the LLM and TTS speculatively.
- **Numbers:** −505 ms latency (1195 → 690 ms) at 28.4% expected redundant compute.
- **Code:** [github.com/bloodraven66/EndpointAnticipation](https://github.com/bloodraven66/EndpointAnticipation). GitHub search metadata: 7 stars, no licence detected, last push 15 Jun 2026.
- **Overlap with forehear:** the trigger is the anticipated endpoint, which is an eager-EOT analogue that forehear treats as its bar. Its waste accounting is in compute fraction.

**11. Voice-Light: A Full-Duplex Cascaded Voice Agent with Causal Turn-Taking and Speculative Generation**
- **Authors:** Bertil Braun (single author; affiliation not listed). Licence CC BY 4.0.
- **Venue/date:** arXiv 2609.20995, 17 Sep 2026.
- **Mechanism:** private speculative response generation and tool calls that run alongside "bridge" speech. Measured on 36 turns from live microphone sessions: median 758 ms from VAD endpoint to first audio. 1,673 real-conversation silence candidates are used for turn-taking.
- Source: [arXiv abs](https://arxiv.org/abs/2609.20995)
- **Code:** [github.com/BertilBraun/Voice-Light](https://github.com/BertilBraun/Voice-Light). GitHub search metadata: 10 stars, no licence detected, last push 17 Oct 2026; demo at voice.bertil-braun.de.
- **Overlap:** a complete agent, not a retrieval-speculation library. Whether its speculation runs on interim transcripts was not confirmed on the abs page.

**12. Speculative Interaction Agents: Building Real-Time Agents with Asynchronous I/O and Speculative Tool Calling**
- **Authors:** Coleman Hooper, Minwoo Kang, Suhong Moon, Nicholas Lee, Eric Wen, John Wawrzynek, Michael W. Mahoney, Yakun Sophia Shao, Amir Gholami and Kurt Keutzer (UC Berkeley / SqueezeAILab group).
- **Venue/date:** arXiv 2605.13360, v1 13 May 2026, v2 14 May 2026; "17 pages", no venue.
- **Numbers:** 1.3–1.7x speedups with cloud real-time APIs; 1.6–2.2x for 3B models with clock-based training.
- Source: [arXiv abs](https://arxiv.org/abs/2605.13360)
- **Code:** none linked. GitHub search within the SqueezeAILab org for "speculative" returned no matching repository. Not found as of Nov 2026.
- **Mechanism note:** Heartbeat describes SIA as "interrupt-on-update" generation, where new input interrupts ongoing generation — [Heartbeat HTML](https://arxiv.org/html/2610.26233)

**13. Speculative Actions: A Lossless Framework for Faster Agentic Systems**
- **Authors:** Naimeng Ye, Arnav Ahuja, Georgios Liargkovas, Yunan Lu, Kostis Kaffes and Tianyi Peng (Columbia).
- **Venue/date:** arXiv 2510.04371, v2. The ICLR 2026 acceptance is from the prior notes' Columbia-hosted PDF — [arXiv API](https://arxiv.org/abs/2510.04371); [ICLR'26 PDF](https://www.cs.columbia.edu/~kkaffes/papers/speculative-actions-iclr26.pdf)
- **Numbers:** up to 55% next-action accuracy and up to 20% latency reduction.
- **Code:** no official repository found. One community demo, [armaan-25/Chess-Speculation-Framework](https://github.com/armaan-25/Chess-Speculation-Framework), has 0 stars and no licence. Not found as of Nov 2026.
- **Difference from forehear:** speculates the agent's next action, not the user's incomplete query.

**14. Predictive Prefetching for Retrieval-Augmented Generation**
- **Authors:** Wuyang Zhang and Shichao Pei (University of Massachusetts Boston).
- **Venue/date:** ICML 2026 poster 66231; arXiv 2605.17989, 18 May 2026, "Accepted by ICML 2026" — [ICML virtual](https://icml.cc/virtual/2026/poster/66231); [arXiv](https://arxiv.org/abs/2605.17989)
- **Mechanism:** mid-generation retrieval prefetch, not on user speech.
- **Numbers:** TTFT −62.4%; 38.7% false-positive triggers, 72% of which are later reused; about 8% net overhead — [paper notes](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/)
- **Code:** GitHub search found nothing. Not found as of Nov 2026.

#### Knowledge-injection speech models

**15. MoshiRAG: Asynchronous Knowledge Retrieval for Full-Duplex Speech Language Models**
- **Authors:** Chung-Ming Chien, Manu Orsini, Eugene Kharitonov, Neil Zeghidour, Karen Livescu and Alexandre Défossez. Kyutai, with Chien and Livescu likely at TTIC (unverified).
- **Venue/date:** accepted to ICML 2026; arXiv 2604.12928, v3 — [arXiv API](https://arxiv.org/abs/2604.12928)
- **Mechanism:** the model emits a retrieval-trigger token. The conversation context goes to a text backend LLM (recommended: gemma-3-27b-it on vLLM), and the returned text is injected while dialogue continues. The repository warns that retrieval delays over 3 s hurt quality — [GitHub](https://github.com/kyutai-labs/moshi-rag)
- **Release:**
  - Code: [kyutai-labs/moshi-rag](https://github.com/kyutai-labs/moshi-rag), 196 stars, last push 9 Sep 2026. Python is MIT, Rust Apache-2.0, client MIT. Inference only; no training code is mentioned.
  - Weights: [kyutai/moshika-rag-pytorch-bf16](https://huggingface.co/kyutai/moshika-rag-pytorch-bf16) and the candle variant, CC-BY 4.0.
  - Source: [GitHub](https://github.com/kyutai-labs/moshi-rag)
- **Overlap with forehear:** retrieval hidden inside conversation latency.
- **Difference from forehear:** an end-to-end S2S model decides when to trigger; there is no interim-ASR policy and no validator. Community forks such as moshirag-jp and voxreach-poc show adoption (GitHub search).

**16. KAME: Tandem Architecture for Enhancing Knowledge in Real-Time Speech-to-Speech Conversational AI**
- **Authors:** So Kuroki, Yotaro Kubo, Takuya Akiba and Yujin Tang.
- **Venue/date:** published at IEEE ICASSP 2026; arXiv 2510.02327 — [arXiv API](https://arxiv.org/abs/2510.02327)
- **Mechanism:** a back-end LLM reads partial transcripts and its text is injected into a real-time S2S front end.
- **Release:** a Hugging Face model [SakanaAI/kame](https://huggingface.co/SakanaAI/kame) exists, which confirms the Sakana AI affiliation. Its licence was not checked, and no GitHub code was found.

**17. Chronological Thinking in Full-Duplex Spoken Dialogue Language Models**
- **Authors:** Donghang Wu, Haoyang Zhang, Chen Chen, Tianyu Zhang, Fei Tian, Xuerui Yang, Gang Yu, Hexin Liu, Nana Hou, Yuchen Hu and Eng Siong Chng. It shares authors with "Heard Enough to Act".
- **Venue/date:** accepted by SIGDIAL 2026; arXiv 2510.05150, v3 — [arXiv API](https://arxiv.org/abs/2510.05150)
- **Mechanism:** reasoning while listening with no extra latency, without tools or retrieval.
- **Code:** GitHub search found nothing. Not found as of Nov 2026.

**18. Never Stop Thinking: Continuous-Time Language Agents**
- **Authors:** Bojie Li and Noah Shi (affiliation not listed).
- **Venue/date:** arXiv 2609.17416, v1 dated 11 Jul 2026.
- **Mechanism:** an interrupt-and-resume orchestrator that thinks while listening and while speaking.
- **Numbers:** −19% live-pipeline latency overall and about half in the targeted regime; ReactiveBench (120 scenarios); RL raises streaming completion from 48% to 73±5%. The abstract also reports that an LLM-judge advantage reversed sign under an independent judge.
- **Code:** none linked. Not found as of Nov 2026.
- Source: [arXiv abs](https://arxiv.org/abs/2609.17416)

#### Speech-retrieval (no streaming) papers

**19. DUPAR: Dual-Path Conversational Retrieval via Speech Retriever with Cross-Turn Evidence Caching**
- **Authors:** Yuanjun Li, Yiwen Liu, Dapeng Li, Zhiwei Xu, Bin Zhang, Shengtao Zhang and Rong Shen.
- **Venue/date:** arXiv 2609.18042, 16 Sep 2026, 5 pages — [arXiv API](https://arxiv.org/abs/2609.18042)
- **Mechanism:** a cross-turn evidence cache with a fast audio-encoder path; nothing runs before end of turn.
- **Numbers:** about 3.75x query-side speedup — [arXiv abs](https://arxiv.org/abs/2609.18042)
- **Code:** none found.

**20. WavRAG: Audio-Integrated Retrieval Augmented Generation for Spoken Dialogue Models**
- **Authors:** Yifu Chen, Shengpeng Ji, Haoxiao Wang, Ziqing Wang, Siyu Chen, Jinzheng He, Jin Xu and Zhou Zhao (Zhejiang University and Alibaba).
- **Venue/date:** ACL 2025; arXiv 2502.14727 — [arXiv API](https://arxiv.org/abs/2502.14727); [ACL Anthology](https://preview.aclanthology.org/setup/2025.acl-long.613)
- **Mechanism:** retrieval on the complete spoken query.
- **Code:** GitHub search "wavrag" returned nothing. Not found as of Nov 2026.

**21. Speech Retrieval-Augmented Generation without Automatic Speech Recognition (SpeechRAG)**
- **Authors:** Do June Min, Karel Mundnich, Andy Lapastora, Erfan Soltanmohammadi, Srikanth Ronanki and Kyu Han (AWS AI Labs).
- **Venue/date:** ICASSP 2025; arXiv 2412.16500, v3 — [arXiv API](https://arxiv.org/abs/2412.16500)
- **Mechanism:** retrieval on the complete spoken query.
- **Code:** no official repository found.

#### Industry backends and pre-LLM prior art

**22. NVIDIA "A frontend-backend architecture for tool calls in full-duplex speech models"**
- **Authors:** Ke Hu, Slyne Deng, Chen Chen, Elena Rastorgueva, Edresson Casanova, Punit Kumar, Dharmendra Choudhary, Nikhil Srihari, Ameya Sunil Mahabaleshwarkar, Viet Anh Trinh, Slim Essid, Oluwatobi Olabiyi and Zhehuai Chen. The abs page lists no affiliation. Slim Essid also co-authors NVIDIA's NemotronLabs VoiceChat paper, and the names match NVIDIA NeMo speech staff, so NVIDIA is an inference.
- **Venue/date:** arXiv 2609.19334, v1 16 Sep 2026, v2 18 Sep 2026. Comments: "To be submitted to ICASSP'27".
- **Mechanism:** a duplex speech-to-text front end emits a *delegation token* and streams ASR transcripts to a text backend LLM, which makes the tool calls. Results return through "prefill-and-repeat".
- **Numbers:** 92–97% tool-call recall; 81.2% correct rejection of irrelevant calls; beats GPT-realtime-mini and Qwen3-Omni on EVA-Bench with a Qwen3-235B backend.
- **Code:** none linked. Not found as of Nov 2026.
- Source: [arXiv abs](https://arxiv.org/abs/2609.19334)
- **Related NVIDIA releases:**
  - NemotronLabs VoiceChat (arXiv 2609.21967; Jagadeesh Balam plus 53 co-authors including Boris Ginsburg) has parallel output streams for agent text and function calls, with 82.5% tool-selection F1 on Full-Duplex-Bench 3.0 — [arXiv abs](https://arxiv.org/abs/2609.21967)
  - Weights are on Hugging Face as [nvidia/NVIDIA-NemotronLabs-VoiceChat-11B](https://huggingface.co/nvidia/NVIDIA-NemotronLabs-VoiceChat-11B) (Hugging Face API search).
  - Pipecat ships a [DGX Spark runner](https://github.com/pipecat-ai/nemotron-voicechat-dgx-spark) (Apache-2.0, 24 stars).
  - The Nemotron Voice Agent blueprint v2.0.0 (Jul 2026) reportedly added a frontend/backend agent example — [GitHub blueprint](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent) (search summary, not opened)
  - Whether the backend starts calls before end of speech was not confirmed on the abs page.

**23. Google: Low Latency Speech Recognition using End-to-End Prefetching**
- **Authors:** Shuo-Yiin Chang, Bo Li, David Rybach, Yanzhang He, Wei Li, Tara N. Sainath and Trevor Strohman (Google).
- **Venue:** Interspeech 2020.
- **Mechanism:** fetches responses early from partial recognition results, using an end-to-end prefetch decision.
- **Numbers:** about 200 ms saved; 120 ms better than silence-based prefetch at an equal prefetch rate.
- **Code:** none known (not re-searched).
- Source: [Google Research](https://research.google/pubs/low-latency-speech-recognition-using-end-to-end-prefetching/)

**24. Amazon: Personalized Predictive ASR for Latency Reduction in Voice Assistants**
- **Authors:** Andreas Schwarz, Di He, Maarten Van Segbroeck, Mohammed Hethnawi and Ariya Rastrow (Amazon).
- **Venue:** Interspeech 2023; arXiv 2305.13794.
- **Mechanism:** predicts the full utterance from a partial one and prefetches the response; a failed prefetch costs compute but no latency.
- **Code:** none known (not re-searched).
- Source: [arXiv abs](https://arxiv.org/abs/2305.13794)

**25. Salesforce VoiceAgentRAG** (closest *packaged* code, but a different trigger)
- **Authors:** Jielin Qiu, Jianguo Zhang, …, Caiming Xiong, Silvio Savarese and Huan Wang (Salesforce AI Research).
- **Venue/date:** arXiv 2603.02206, Mar 2026 — [arXiv abs](https://arxiv.org/abs/2603.02206)
- **Mechanism:**
  - A "Slow Thinker" predicts 3–5 follow-up topics "on each user utterance" and prefetches chunks into a FAISS semantic cache (similarity threshold 0.40, TTL 300 s).
  - A "Fast Talker" reads from the cache and falls back to the vector DB on a miss.
- **Numbers:** 75% cache hit rate (150/200 queries); retrieval latency 110 → 0.35 ms — [GitHub](https://github.com/SalesforceAIResearch/VoiceAgentRAG)
- **Release:** [SalesforceAIResearch/VoiceAgentRAG](https://github.com/SalesforceAIResearch/VoiceAgentRAG), 161 stars, last push 2 Jun 2026, install from source only.
- **Licence conflict:** GitHub detects Apache-2.0, but the README's licence section says CC-BY-NC-4.0 — [GitHub](https://github.com/SalesforceAIResearch/VoiceAgentRAG)
- **Overlap:** a voice-agent prefetch cache.
- **Difference from forehear:** it predicts the *next* turn's topics, not the current interim query; there is no interim-ASR policy, no cancellation, and no real-speech benchmark. A community port, [rohansx/primd](https://github.com/rohansx/primd) (3 stars), also exists.

### Inferences
- **No released academic artifact is a drop-in library for forehear's job** (retrieval on interim ASR with pluggable policies, validators, cancellation and cost accounting).
  - The research harnesses (stablize_CRAG, RASSG, EndpointAnticipation, Voice-Light) have no licence, so legally they are "all rights reserved" and not reusable as dependencies.
  - Each has fewer than 15 stars.
- **The repository most likely to become a competing library is VoiceAgentRAG**: Salesforce brand, 161 stars, a prefetch-into-cache abstraction for voice. A Stream RAG release from Meta/CMU would be the most direct competitor if it ever lands, but 13 months after the promise there is no sign of it.
- **MoshiRAG and NemotronLabs VoiceChat are substitutes rather than competitors.** They move the "when to retrieve" decision inside an end-to-end speech model, which competes with cascaded pipelines as a whole rather than with a retrieval-speculation layer.

### Gaps
- Licences could not be read from repository files directly (the session's GitHub access was limited to search), so "no licence detected" comes from GitHub's licence detector.
- Code for Shih et al. (2510.07497), the Google 2020 paper and the Amazon 2023 paper was not re-searched this session.
- The licence of SakanaAI/kame on Hugging Face was not checked.
- The full text of VoiceAgentRAG was not read; whether prefetch can run on interim transcripts is unconfirmed.
- Whether NVIDIA's frontend-backend system delegates before end of speech is unconfirmed (only the abs page was read).
- Author affiliations not shown on abs pages (Heard Enough to Act, Never Stop Thinking, PACT-SLM, Context Spanning) remain unverified.

---

## Q2. Which groups (Meta, Berkeley, NVIDIA, Google, Amazon, Apple, others) are actively working on this and could ship a competing open-source system or product?

### Takeaway
- **Most active on tool calls or retrieval during or alongside speech in 2026:** NVIDIA (two Sep 2026 papers plus open weights and a blueprint), Kyutai (open MoshiRAG weights and code), Ant International (Heartbeat Thinking, Oct 2026), Qualcomm/KAIST (on-device speculation, Oct 2026), and the NTU Singapore cluster (Chng: Chronological Thinking and Heard Enough to Act).
- **Meta/CMU:** Stream RAG has not been followed up and Arora's 2026 papers moved to other topics.
- **Berkeley:** published SIA (May 2026) with no code.
- **Google, Amazon, Apple:** no 2026 paper on retrieval or tool calls during user speech was found.

### Cited Findings
- **Meta/CMU.**
  - Stream RAG is still v1 (Oct 2025) with no code — [arXiv abs](https://arxiv.org/abs/2510.02044)
  - Siddhant Arora's 2026 arXiv papers are on multiparty voice agents (MP-Bench, EMNLP 2026 Findings), vLLM audio inference, TTS, ESPnet3, meeting turn prediction, PlanRAG-Audio for long-form audio, and RLAIF for dialogue. None is on streaming retrieval — [arXiv API author query, e.g. MP-Bench 2609.13076](https://arxiv.org/abs/2609.13076); [PlanRAG-Audio 2605.20414](https://arxiv.org/abs/2605.20414)
  - CRAG-MM, Meta's multimodal RAG benchmark repository, was pushed in Jul 2026 — [GitHub](https://github.com/facebookresearch/CRAG-MM)
  - **Shinji Watanabe (CMU)** is a co-author of Stream RAG and of Endpoint Anticipation (Interspeech 2026, code released), so CMU/WavLab remains active on anticipatory speculation — [arXiv HTML](https://arxiv.org/html/2606.13450)
- **Berkeley (Keutzer/Gholami, SqueezeAILab).**
  - SIA, arXiv 2605.13360 (May 2026), reports 1.3–2.2x speedups with no code — [arXiv abs](https://arxiv.org/abs/2605.13360)
  - The group has a record of releasing agent-systems code: [LLMCompiler](https://github.com/SqueezeAILab/LLMCompiler) and TinyAgent appear in the SqueezeAILab org (GitHub search). Nothing for SIA was found.
- **NVIDIA.**
  - Frontend-backend delegation paper, arXiv 2609.19334 (Sep 2026, ICASSP'27 target) — [arXiv abs](https://arxiv.org/abs/2609.19334)
  - NemotronLabs VoiceChat, arXiv 2609.21967 (54 authors, tool calling, open weights on Hugging Face) — [arXiv abs](https://arxiv.org/abs/2609.21967); [HF model](https://huggingface.co/nvidia/NVIDIA-NemotronLabs-VoiceChat-11B)
  - Pipecat integration repository — [GitHub](https://github.com/pipecat-ai/nemotron-voicechat-dgx-spark)
- **Kyutai.** MoshiRAG (ICML 2026) has open code (MIT/Apache) and CC-BY weights, with ongoing pushes through Sep 2026 — [GitHub](https://github.com/kyutai-labs/moshi-rag)
- **Microsoft + NTU Taiwan.** SHANKS is still "work in progress" with no code — [project page](https://d223302.github.io/SHANKS/)
- **Ant International.** Heartbeat Thinking (Oct 2026) benchmarks directly against Pipecat and LiveKit Agents — [arXiv HTML](https://arxiv.org/html/2610.26233)
- **Qualcomm AI Research + KAIST.** On-device speculative tool execution on a Snapdragon phone (Oct 2026) — [arXiv HTML](https://arxiv.org/html/2610.07641)
- **NTU Singapore / Chng group** (inferred from author overlap). Chronological Thinking (SIGDIAL 2026) and Heard Enough to Act (Oct 2026), which promises open-source code — [arXiv abs](https://arxiv.org/abs/2610.34653); [arXiv abs](https://arxiv.org/abs/2510.05150)
- **Salesforce AI Research.** VoiceAgentRAG has open code (161 stars) — [GitHub](https://github.com/SalesforceAIResearch/VoiceAgentRAG)
- **Sakana AI.** KAME (ICASSP 2026), with a model on Hugging Face — [HF](https://huggingface.co/SakanaAI/kame); [arXiv](https://arxiv.org/abs/2510.02327)
- **Google and Amazon.** Their known work in this line is pre-LLM: Google 2020 end-to-end prefetching and Amazon 2023 predictive ASR — [Google Research](https://research.google/pubs/low-latency-speech-recognition-using-end-to-end-prefetching/); [arXiv](https://arxiv.org/abs/2305.13794)
  - AWS's 2024 SpeechRAG is ASR-free retrieval on complete queries — [arXiv](https://arxiv.org/abs/2412.16500)
  - Searches did not surface a 2026 Google or Amazon paper on retrieval during user speech.
- **Apple.** The only 2026 Apple speech-latency result surfaced was "Principled Coarse-Grained Acceptance for Speculative Decoding in Speech", which speeds up TTS token generation, not tool calls or retrieval — [search summary via TechRepublic](https://www.techrepublic.com/article/news-apple-siri-sound-human/) (secondary source; primary not fetched)

### Inferences
- **Most likely to ship something that overlaps forehear in open source: NVIDIA.** It has open weights, blueprints and an existing Pipecat partnership. Its approach is delegation from a duplex model rather than speculative retrieval on interim ASR, but a "backend gets streaming transcripts" design could add early firing cheaply.
- **Most likely to publish a direct academic competitor with code: the Chng/NTU group** ("will open-source the pipeline") and possibly **CMU/WavLab** (Watanabe), given its history of releases (ESPnet, EndpointAnticipation).
- **Meta looks least active** despite having the closest paper.
- **Google, Amazon and Apple** may well work on this inside their products (Gemini Live, Alexa+, Siri), but nothing public in 2026 was found. That is absence of evidence, not evidence of absence.

### Gaps
- Product-side features (Gemini Live, Alexa+, OpenAI Realtime, Siri) were not in scope and were not checked here.
- Affiliations for several new papers are inferred from author names, not stated on the pages.

---

## Q3. Which results support or contradict forehear's findings?

### Takeaway
Overall, the 2026 literature *supports* forehear's main claims:
- Much of the needed information arrives before end of speech.
- Speculation trades a little quality for latency.
- Agreement-based "settling" policies are slower than eager ones.

No paper reports calls/turn for retrieval, so forehear's ~3.5 calls/turn has no direct comparison. The only quantified waste figures come from other settings (28.4% redundant compute; 47 → 5 wasted calls; 38.7% false triggers).

The one apparent contradiction is RASSG. For *side-effecting* tools, a stricter agreement policy (3 identical consecutive hypotheses) is the winner, because stale irreversible actions are its cost metric. That is consistent with forehear's latency finding but marks a boundary: forehear's conclusion holds for read-only retrieval.

### Cited Findings

**LocalAgreement losing (forehear: LocalAgreement-2 is worse than a plain timer).**
- *Supports, on latency.* On ReCAST, RASSG's measurements put LocalAgreement-2 at 3.954 s delay, slower than the eager "Speculative Tool Calling" baseline (3.480 s). LocalAgreement-2 also had a 50.00% stale rate, the same as the eager baseline, so the extra wait bought no reduction in staleness — [arXiv HTML](https://arxiv.org/html/2610.14659)
- *Qualifies.* RASSG's own policy is an agreement rule (3 consecutive identical arguments) combined with risk-based cancellation. It reaches 3.15% staleness at 3.676 s on ReCAST, but 57% and 54.65% staleness on FDB-v3 and Audio2Tool with longer delays than LocalAgreement-2 (11.072 s vs 9.210 s on FDB-v3) — [arXiv HTML](https://arxiv.org/html/2610.14659)
- *Mechanism agrees.* Jung et al.'s trigger fires on word count or pause (after 6 words, every 5 words, or a pause over 300 ms) rather than hypothesis agreement — [arXiv HTML](https://arxiv.org/html/2610.07641)
- *Mechanism agrees.* Heartbeat and Stream RAG both use fixed-interval timers (500 ms / 1 s) — [Heartbeat](https://arxiv.org/html/2610.26233); [Stream RAG](https://arxiv.org/html/2510.02044v1)
- No paper other than RASSG benchmarks LocalAgreement for retrieval or tools.

**~3.5 calls/turn and waste accounting.**
- *No direct comparison.* Stream RAG, Galbraith and Heartbeat do not report calls per turn — [Galbraith HTML](https://arxiv.org/html/2606.20113v2); [Heartbeat HTML](https://arxiv.org/html/2610.26233)
- *Implied scale.* Stream RAG's fixed-interval variant (1 s blocks) and Heartbeat (500 ms, at most 2 in flight) imply roughly one call per 0.5–1 s of speech, which is the same order as forehear's 3.5 for typical 3–5 s turns. This is an inference, not a reported number.
- *Absolute counts only.* Jung et al. report 47 → 5 wasted calls over 100 standard samples, with no per-turn normalisation — [arXiv HTML](https://arxiv.org/html/2610.07641)
- *Other settings.* Endpoint Anticipation: 28.4% expected redundant compute — [arXiv HTML](https://arxiv.org/html/2606.13450). Predictive Prefetching: 38.7% false triggers, about 8% net overhead — [paper notes](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/)
- *Supports "LLM calls cost more than retrieval calls."* Heartbeat lists cost accounting as future work, and its speculation consists of LLM Thinker invocations, a more expensive unit than forehear's retrieval-only calls — [arXiv HTML](https://arxiv.org/html/2610.26233)

**Recall/quality trade-off of reuse (forehear: accepting 80% content-word overlap costs about 3 pt recall@5; ResultOverlap(0.9) is lossless).**
- *Supports.* Heartbeat Thinking loses a little quality from speculation:
  - AudioCRAG correct-answer rate 57.24% → 55.49%, with missing answers 14.33% → 16.84%.
  - SpeechFCEval accuracy 67.95% → 66.85%.
  - About 4% of FDBench recordings hallucinate outdated speculative results.
  - Source: [arXiv HTML](https://arxiv.org/html/2610.26233)
- *Supports forehear's choice of validator.* Stream RAG's reflector uses exact top-5 identity, the strictest result-overlap validator — [arXiv HTML](https://arxiv.org/html/2510.02044v1)
- *Supports.* Galbraith finds 20.9% of questions change top-1 after first reaching the final top-1, a direct measure of why naive early acceptance costs recall — [arXiv HTML v2](https://arxiv.org/html/2606.20113v2)
- *Apparent contradiction.* Stream RAG and Jung et al. report quality *gains*: accuracy 26.3 → 34.2, and tool-call F1 44.8% → 60.6% — [Stream RAG](https://arxiv.org/html/2510.02044v1); [Jung](https://arxiv.org/html/2610.07641)
  - These gains come from training or query rewriting (Stream RAG) or a structured injection pipeline (Jung), compared against weaker baselines.
  - They do not compare speculative results with the system's own final-transcript retrieval, so they don't contradict forehear's like-for-like recall Δ.

**"43% retrievable 1 s before end of speech" (final transcript: 76%).**
- *Same direction, more optimistic.*
  - Galbraith: 73.9% of CRAG queries are "streamable" (L=600 ms); median φ_suf is 0.14 on the retrieved-gold subset; mean φ_sc is 0.67.
  - But the input is a uniform simulated word stream at 3 words/s with no ASR revisions, which the paper names as a limitation.
  - Only 21.3% of questions have gold retrievable at all under BM25.
  - Source: [arXiv HTML v2](https://arxiv.org/html/2606.20113v2)
  - forehear's lower 43% on real interim ASR is consistent with Galbraith's warning that ASR revisions and real timing would reduce early stabilization.
- *Supports.* SHANKS completes 56.9% of tool calls before the user finishes speaking (ComplexFuncBench) — [project page](https://d223302.github.io/SHANKS/)
- *Supports.* Heard Enough to Act: correct early calls lead a turn-end cascade by 1.8–2.0 s in-domain and 1.1 s on τ²-bench audio, on synthetic TTS — [arXiv abs](https://arxiv.org/abs/2610.34653)
- *Supports.* Heartbeat: correct tool calls finish on average 4.37 s before speech end, against 2.74 s for the window baseline, on FDBench v3 — [arXiv HTML](https://arxiv.org/html/2610.26233)
- *Supports.* Jung et al.: cache-ready rate at ASR finalization of 47.7% (TTS speech, web search). This is numerically close to forehear's 43%, but the metric and setting differ — [arXiv HTML](https://arxiv.org/html/2610.07641)
- *Supports.* PACT-SLM finds acoustic models act on 18.99% of *pre-onset* prefixes (premature) and argues identity and timing must be scored separately — [arXiv abs](https://arxiv.org/abs/2609.38232)

**Real human speech benchmarks (forehear's differentiator).**
- Most 2026 papers evaluate on synthetic TTS:
  - Jung et al.: Gemini TTS — [arXiv HTML](https://arxiv.org/html/2610.07641)
  - Heard Enough to Act: TTS corpus — [arXiv abs](https://arxiv.org/abs/2610.34653)
  - RASSG ReCAST: "synthetic speech" — [arXiv HTML](https://arxiv.org/html/2610.14659)
  - Galbraith: simulated text — [arXiv HTML v2](https://arxiv.org/html/2606.20113v2)
- Exceptions:
  - Stream RAG's AudioCRAG-Human: 618 recorded queries, unreleased — [arXiv HTML](https://arxiv.org/html/2510.02044v1)
  - FDBench v3: 100 recordings from 12 speakers, used by Heartbeat and RASSG — [Heartbeat HTML](https://arxiv.org/html/2610.26233)
  - Voice-Light: 36 live turns — [arXiv abs](https://arxiv.org/abs/2609.20995)
- **Eager end-of-turn as the baseline to beat.** Endpoint Anticipation (−505 ms, Interspeech 2026) is the academic counterpart of the eager-EOT baseline forehear compares against — [arXiv HTML](https://arxiv.org/html/2606.13450)

### Inferences
- **forehear's distinctive empirical contributions remain unduplicated in the literature:**
  - calls/turn cost curves;
  - a validator sweep of recall Δ vs latency saved;
  - LocalAgreement vs timer for *retrieval*;
  - interim-ASR retrievability on real speech.
- **RASSG is the paper to cite on scope.** Agreement-gated launch with cancellation is right when actions are irreversible. For idempotent retrieval, staleness is free and latency dominates, so timers win, which is forehear's result.
- **Galbraith's 73.9% vs forehear's 43% is a useful contrast.** It quantifies the gap between idealized text streaming and real interim ASR. The two are not directly comparable: different metric (H ≥ 0.8L vs gold in top-k at t−1 s), different corpus, different retriever.

### Gaps
- No paper reports retrieval calls/turn or recall@k Δ against final-transcript retrieval, so forehear's key cost and quality numbers have no external replication.
- RASSG launch and cancel counts, and Heartbeat Thinker invocation counts, are not reported, so waste cannot be compared.

---

## Q4. New papers, mid-2026 to Nov 2026: retrieval or tool calls during user speech, streaming speech RAG, anticipatory retrieval, query prediction from partial utterances, speculative tool execution

### Takeaway
Since June 2026 there has been a clear surge of papers, mostly Sep–Nov 2026 and several targeting ICASSP 2027. The most relevant new entries are:
- Galbraith (Jun)
- RASSG (Oct)
- Jung et al. / Qualcomm (Oct)
- Heartbeat Thinking (Oct)
- Heard Enough to Act (Oct)

These are joined by full-duplex "delegation" and "injection" papers (NVIDIA, Context Spanning, NemotronLabs VoiceChat) and evaluation work on *when* an agent has heard enough (PACT-SLM, When Intent Arrives Late). Semantic Scholar shows Stream RAG with about 25 citing papers, which makes it the anchor citation for this subfield.

### Cited Findings
- **Citation counts.** Semantic Scholar lists about 25 citing papers for Stream RAG, including Heard Enough to Act, RASSG, RUBATO, Jung et al., Context Spanning, RePlay, Galbraith, Endpoint Anticipation, MoshiRAG, VoiceAgentRAG and VoxMind — [Semantic Scholar API, citations of arXiv:2510.02044](https://api.semanticscholar.org/graph/v1/paper/arXiv:2510.02044/citations?fields=title)
- **New since mid-2026, not covered in Q1** (arXiv API and Semantic Scholar; abstracts not read unless cited):
  - **Context Spanning: A Communication Framework for Full-Duplex Speech Models and External LLM Backends**
    - Seonghyeon Go, Yongwoo Kim, Hyeonjin Cha and Jaeho Shin; arXiv 2609.33443, 27 Sep 2026, submitted to ICASSP 2027.
    - Injects backend-retrieved text through real-time chunked prefill.
    - Code: [mindlogic-ai/Context-Spanning](https://github.com/mindlogic-ai/Context-Spanning) (MIT, 17 stars; GitHub search). The org name suggests Mindlogic, a company.
    - Source: [arXiv abs](https://arxiv.org/abs/2609.33443)
  - **When Does a Spoken Agent Have Enough Evidence to Act? The PACT-SLM Contract Test**
    - Mengzhe Geng; arXiv 2609.38232, v2 7 Oct 2026.
    - Scores action identity and timing on speech prefixes: 1,600 prefix predictions; WavLM acts on 18.99% of pre-onset prefixes. No code.
    - Source: [arXiv abs](https://arxiv.org/abs/2609.38232)
  - **When Intent Arrives Late: A Benchmark for Full-Duplex Speech Models under Delayed Intent Revelation**
    - Yang Xiao, Tianyi Peng, Hanyu Meng and Ting Dang; arXiv 2610.00272, 24 Sep 2026. Title and authors only.
    - Source: [arXiv](https://arxiv.org/abs/2610.00272)
  - **Answering While You Type: Optimizing Time-to-Answer with Streaming Generation**
    - Dragunov, Mikhalchuk and Razzhigaev; arXiv 2610.26296, 19 Oct 2026.
    - Starts the response from an incomplete request and revises it as input arrives; no retrieval; no numbers in the abstract.
    - Source: [arXiv abs](https://arxiv.org/abs/2610.26296)
  - **Decode Before You Hear: Speculative Listening for Chunk-Interleaved Full-Duplex Speech LMs**
    - arXiv 2611.06982, 4 Nov 2026. Title only.
    - Source: [arXiv](https://arxiv.org/abs/2611.06982)
  - **RUBATO: Decoupled Clocks Allow Full-Duplex Models to Think as Fast as They Can**
    - arXiv 2610.14299. Title only.
    - Source: [arXiv](https://arxiv.org/abs/2610.14299)
  - **VoiceMem: Streaming Dual-Brain Memory for Real-Time Interaction**
    - arXiv 2608.26005. Title only.
    - Source: [arXiv](https://arxiv.org/abs/2608.26005)
  - **RePlay: Retrieval-Based Voice Playback for Multi-Turn Spoken Dialogue**
    - arXiv 2609.31588; cites Stream RAG. Title only.
    - Source: [arXiv](https://arxiv.org/abs/2609.31588)
  - **DuplexAct: How Interactive Are Frontier Full-Duplex Spoken Language Models?**
    - arXiv 2610.17738. Title only.
    - Source: [arXiv](https://arxiv.org/abs/2610.17738)
- **Earlier 2026 papers relevant to the "early preparation" line:**
  - **LTS-VoiceAgent: Listen-Think-Speak via Semantic Triggering and Incremental Reasoning**
    - Wenhao Zou et al.; arXiv 2601.19952, Jan 2026.
    - Source: [arXiv](https://arxiv.org/abs/2601.19952)
  - **RelayS2S: Dual-Path Speculative Generation for Real-Time Dialogue**
    - Long Mai and Junli Liang; EMNLP 2026 Findings; arXiv 2603.23346.
    - Code: [mailong25/relays2s](https://github.com/mailong25/relays2s) (16 stars, no licence detected; GitHub search).
    - Source: [arXiv](https://arxiv.org/abs/2603.23346)
  - **Learning When to Think While Listening in Large Audio-Language Models**
    - Zhiyuan Song, …, Jiatao Gu; arXiv 2605.27190, May 2026.
    - Code: [realAllenSong/Learning-When-to-Think-While-Listening](https://github.com/realAllenSong/Learning-When-to-Think-While-Listening) (3 stars, licence NOASSERTION).
    - Source: [arXiv](https://arxiv.org/abs/2605.27190)
  - **Full-Duplex-Bench-v3: Benchmarking Tool Use for Full-Duplex Voice Agents Under Real-World Disfluency**
    - arXiv 2604.04847. A real-speech tool-use benchmark used by Heartbeat and RASSG.
    - Source: [arXiv](https://arxiv.org/abs/2604.04847)
- **Searches that found no exact match.** The arXiv API queries for "partial transcript" + retrieval/tool, and for speculative/anticipatory/prefetch + speech + retrieval/tool, returned only the papers above. No 2026 paper on *dense passage retrieval* on interim ASR with explicit calls/turn or recall accounting was found — [arXiv API query](https://export.arxiv.org/api/query?search_query=abs:%22partial%20transcript%22)

### Inferences
- **The field is converging on one architecture:** fixed-interval or learned triggers on partial ASR, a concurrency cap, cancellation at end of turn, and reuse validated by an LLM or rules.
- **forehear's niche is the retrieval-specific, cost-accounted, real-speech benchmark layer.** The academic work is mostly about tools and actions in general (Heartbeat, RASSG, Heard Enough to Act) or about end-to-end duplex models (NVIDIA, Kyutai, Context Spanning).
- **ICASSP 2027 submissions** (Heard Enough to Act, NVIDIA delegation, Context Spanning) suggest more code releases around Jan–Apr 2027, with the camera-ready deadline and the conference itself.

### Gaps
- Abstracts were not read for RUBATO, VoiceMem, RePlay, DuplexAct, Decode Before You Hear, When Intent Arrives Late, or LTS-VoiceAgent.
- Semantic Scholar citations of Galbraith (2606.20113) and Jung (2610.07641) returned none. Indexing lag is likely, so later citing work may be missing.
- OpenReview and Papers with Code were not queried separately; Papers with Code has been folded into Hugging Face Papers, which was searched.
