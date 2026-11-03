# Academic work on speculative, streaming and anticipatory retrieval for voice agents (2019–2026)

Scope note: the research used about 22 tool calls (searches, fetches and PDF reads) in November 2026. arXiv IDs starting 26xx are 2026 preprints. Unless a fetched page said otherwise, numbers are the authors' own claims, taken from abstracts or HTML pages. "Closeness" rates each paper against the target system: retrieval on partial ASR, predicting the final query, prefetching, cancelling wrong guesses, and context ready at end of turn.
- **EXACT:** the paper does essentially this.
- **PARTIAL:** it covers a substantial subset.
- **ADJACENT:** related mechanism or setting.

## Q1. Are there papers that explicitly run retrieval/RAG on partial ASR transcripts or incomplete utterances?

### Takeaway
Yes. Since late 2025 a small but real literature exists. The first explicit instance is Meta/CMU's **Stream RAG** (Arora et al., Oct 2025): it issues retrieval and tool queries on partial ASR or audio every 500 ms to 1 s while the user speaks. 2026 follow-ups add a theory and measurement of when speculation can help (Galbraith, "tool-intent stabilization") and an on-device cascaded implementation with a cache and self-correction validation (Jung et al., Oct 2026). The idea of prefetching a response from a partial ASR hypothesis is older: Google's Interspeech 2020 end-to-end prefetching paper and Amazon's Interspeech 2023 predictive ASR.

### Cited Findings

**Stream RAG: Instant and Accurate Spoken Dialogue Systems with Streaming Tool Usage (EXACT, closest match found)**
- Siddhant Arora (Meta and CMU) and about 15 Meta co-authors, including Xin Luna Dong, Kai Sun, Florian Metze, Zhaojiang Lin and Shinji Watanabe (CMU). arXiv:2510.02044, Oct 2025 — [arXiv HTML](https://arxiv.org/html/2510.02044)
- It is the first approach to put tool use (web search and knowledge-graph APIs) directly into speech-in, speech-out systems. It predicts tool queries in parallel with user speech, before the user finishes — [arXiv HTML](https://arxiv.org/html/2510.02044); [search summary / ResearchGate](https://www.researchgate.net/publication/396142571_Stream_RAG_Instant_and_Accurate_Spoken_Dialogue_Systems_with_Streaming_Tool_Usage)
- **Variant 1, Fixed-Interval Streaming RAG (no training):** issues a query on each block of incoming speech, with 1 s intervals reported. A "reflector" checks whether an early query's results match the final query's results (same top-5 web documents, or identical KG results). This is a direct analogue of "cancel wrong guesses / reuse correct ones." It cut tool-use latency by 10.7% for open-book Qwen-Omni — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Variant 2, Model-Triggered Streaming RAG:** post-trained to emit NO_QUERY or a new query on each 500 ms block of partial input. It runs single-threaded with no reflector. A label is NO_QUERY when the new query is similar to the previous one. Negative sampling (10% of cases) teaches recovery from wrong early queries; the ablation gives 39.8 accuracy with it vs 36.5 without — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Data:** AudioCRAG-Synthetic (1,862 queries, filtered from 2,706 CRAG queries) and AudioCRAG-Human (618 human-recorded queries). Post-training uses 16k TriviaQA questions. Retrieval uses about 100k CRAG web documents with a BGE re-ranker (top 50) plus the CRAG mock KG API — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Accuracy (Qwen2.5-7B, synthetic/human):** closed book 11.1/13.1; open book 26.3/26.9; Model-Triggered Streaming RAG 34.2/37.4. The abstract says accuracy rises "up to 200%" relative to closed book — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Latency:** average tool-use latency is 3.37 s, and the abstract reports about a 20% reduction (20.7%). First-token latency savings are 20.7% (synthetic) and 53.4% (human) for Qwen, and 14.8% and 41.5% for OpusLM. The paper says the method is modality-agnostic and applies to typed input too — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Code:** the authors say they "will open source our training code and AudioCRAG-Human benchmark." No repository link was found in the paper text. Release status is UNVERIFIED — [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Related work:** the paper does not cite speculative-retrieval or prefetching work from the ASR literature. The nearest work it cites is Feng et al. 2025 (end-to-end speech-to-text RAG) and AURA (Maben et al. 2025, a cascaded voice agent with web tools) — [arXiv HTML](https://arxiv.org/html/2510.02044)

**When Does Streaming Tool Use Help? Characterizing Tool-Intent Stabilization in Streaming RAG (EXACT setting; analysis paper)**
- Elroy Galbraith (single author). arXiv:2606.20113, Jun 2026 — [arXiv abs](https://arxiv.org/abs/2606.20113v1)
- **Tool-intent stabilization** is the point in the input stream where a speculative query's retrieval converges on the answer-bearing result. The paper derives a model-agnostic bound H on hideable tool latency as a function of tool latency L and input cadence δ. It validates the bound on a working streaming pipeline, where realized savings were at or above the bound. No training is needed, and it runs on commodity CPU — [arXiv abs](https://arxiv.org/abs/2606.20113v1)
- **Numbers (L=600 ms, δ=3 words/s, θ=0.8, CRAG validation, 1,371 questions):**
  - 73.9% of queries admit substantial latency hiding.
  - In the 21.3% slice where gold evidence is verbatim-present and BM25-retrievable, 95.2% are streamable.
  - The sufficiency fraction φ_suf is bracketed to [0.26, 0.281] on the favorable slice. Read as "stabilizes after about 26–28% of input" is my interpretation; the page does not spell this out.
  - Question type gives a significant but coarse early/late split (Kruskal-Wallis p=0.017, ε²=0.04).
  - Source: [arXiv abs](https://arxiv.org/abs/2606.20113v1)
- **Code:** no repository link on the abs page — [arXiv abs](https://arxiv.org/abs/2606.20113v1)

**Hiding Tool Latency in On-Device Cascaded Voice Agent through Speculative Execution (EXACT for tool calls / prefetch + cache + validation)**
- Kyudan Jung, Hyunsin Park, Yoonhyung Lee, Jinhwan Park, Jinhyeok Yang, KiHyun Nam, Jaegul Choo and Jinkyu Lee. The abs page lists no affiliation, and the organization is UNVERIFIED. arXiv:2610.07641 (cs.SD), 6 Oct 2026 — [arXiv abs](https://arxiv.org/abs/2610.07641); [HF papers](https://huggingface.co/papers/2610.07641)
- **Method:**
  - A Predictor module predicts tool requests from partial ASR hypotheses, executes them while the user speaks, and caches the results.
  - Cached results are injected into the LLM prompt.
  - Rule-based validation handles user self-corrections and injects only valid cached results; this is the cancel-wrong-guess step.
  - The LLM can still call tools itself, so worst-case latency is bounded by the serial pipeline.
  - It is implemented as a real Android voice assistant.
  - Source: [arXiv abs](https://arxiv.org/abs/2610.07641)
- **Numbers:** median time-to-first-audio falls from 5.79 s to 4.60 s, and its standard deviation from 3.49 s to 2.81 s. Speculation hit rate and wasted calls are not reported on the abs page. No code link — [arXiv abs](https://arxiv.org/abs/2610.07641)

**Low Latency Speech Recognition using End-to-End Prefetching (PARTIAL; the earliest clear "prefetch on partial ASR" paper found)**
- Shuo-Yiin Chang, Bo Li, David Rybach, Yanzhang He, Wei Li, Tara N. Sainath and Trevor Strohman (Google). Interspeech 2020, pp. 1962–1966, doi:10.21437/Interspeech.2020-1898 — [Google Research](https://research.google/pubs/low-latency-speech-recognition-using-end-to-end-prefetching/)
- Fetches responses early from partial recognition results. It compares decoder-silence, acoustic-silence and end-to-end prefetch decision models on a streaming RNN-T first pass with LAS rescoring. Prefetching cut latency by about 200 ms. End-to-end prefetching gave the best cost/latency balance, 120 ms faster than silence-based prefetching at a fixed prefetch rate — [Google Research](https://research.google/pubs/low-latency-speech-recognition-using-end-to-end-prefetching/); [ISCA mirror](https://unpaywall.org/10.21437%2FInterspeech.2020-1898)
- The "prefetch" here is the downstream voice-assistant response or fulfilment, not LLM-era RAG. The paper treats the prefetch rate as a cost, which makes it an explicit cost/latency tradeoff — [Google Research](https://research.google/pubs/low-latency-speech-recognition-using-end-to-end-prefetching/)

**Personalized Predictive ASR for Latency Reduction in Voice Assistants (PARTIAL; predicts the full utterance, then prefetches)**
- Andreas Schwarz, Di He, Maarten Van Segbroeck, Mohammed Hethnawi and Ariya Rastrow (Amazon; the PDF is hosted on amazon.science). Interspeech 2023. arXiv:2305.13794 — [arXiv abs](https://arxiv.org/abs/2305.13794); [Amazon Science PDF](https://assets.amazon.science/7f/99/6ecd06364b04b00110b8d601febd/personalized-predictive-asr-for-latency-reduction-in-voice-assistants.pdf)
- "Predictive ASR" predicts the full utterance from a partially observed one and prefetches the response for the predicted utterance. Two personalization approaches are evaluated on internal data and on SLURP. The abstract frames a tradeoff between latency gains from correct predictions and cost from failed ones. Specific latency and hit-rate numbers were not visible on the abs page — [arXiv abs](https://arxiv.org/abs/2305.13794)
- When the final ASR confirms a prediction, the prefetched result is reused. A failed prefetch is discarded and regenerated, which costs compute but adds no latency — [search summary of arXiv 2305.13794](https://arxiv.org/pdf/2305.13794)

**Predictive Speech Recognition and End-of-Utterance Detection Towards Spoken Dialog Systems (ADJACENT)**
- Zink et al., arXiv:2409.19990 (2024). Uses the decoder of an encoder-decoder ASR model to predict upcoming words and the end of utterance early. It is cited by the endpoint-anticipation paper below as prior work for early processing — [arXiv](https://arxiv.org/pdf/2409.19990); [cited in arXiv 2606.13450](https://arxiv.org/html/2606.13450)

**DUPAR: Dual-Path Conversational Retrieval via Speech Retriever with Cross-Turn Evidence Caching (ADJACENT; the cache is relevant, but nothing runs before end of turn)**
- Yuanjun Li, Yiwen Liu, Dapeng Li, Zhiwei Xu, Bin Zhang, Shengtao Zhang and Rong Shen. arXiv:2609.18042 (2026) — [arXiv abs](https://arxiv.org/abs/2609.18042)
- **Fast path:** searches a cross-turn evidence cache with an audio encoder aligned to frozen BGE-M3. **Slow path:** full-index retrieval over audio and ASR embeddings when cache confidence is low. Evidence refreshes the cache through one-hop graph expansion. Streaming or partial-utterance retrieval is not mentioned — [arXiv abs](https://arxiv.org/abs/2609.18042)
- **Numbers:** about 3.75x query-side speedup over ASR + text encoder. Average Recall@10 under noise rises from 0.771 to 0.875. Recall@1 improves 4.2 points across speaking styles. No code link — [arXiv abs](https://arxiv.org/abs/2609.18042)

**Practitioner signal (non-academic, for context only)**
- **Pipecat issue #6511:** proposes speculative KV-cache prefill from interim ASR transcripts and reports a TTFT reduction of 73–97% on CPU in the author's local measurement. It is a proposal, not a merged feature; Pipecat aggregators currently drop interim frames — [GitHub issue](https://github.com/pipecat-ai/pipecat/issues/6511)
- Speculative tool calling during user speech is also discussed in vendor blogs and recipes — [Stream blog](https://getstream.io/blog/speculative-tool-calling-voice/); [Deepgram recipes issue #694](https://github.com/deepgram/recipes/issues/694)
- **Cresta:** letting the LLM predict the user's full utterance could give "negative latency," but Cresta has not found it practical yet — [Cresta blog](https://cresta.com/blog/engineering-for-real-time-voice-agent-latency)

### Inferences
- **No paper found combines every element of the target system.** The missing combination is: (a) explicit final-query prediction or completion (as in predictive ASR), (b) a multi-candidate prefetch of passages from a vector index, (c) cancellation or rollback, and (d) cost accounting. Stream RAG covers (a)-lite (rewriting the query from the partial input) plus the reflector, a form of (c). Jung et al. covers prefetch, cache and validation for tool calls. Galbraith covers the theory of when it can help.
- **None of these papers evaluates dense-retrieval prefetch of top-k passages from a private corpus with explicit waste metrics.** Stream RAG uses web search and KG. Galbraith uses BM25 on CRAG. This looks like an open niche.
- **Stream RAG's reflector criterion (same top-5 documents) is a reusable definition of a correct speculation.** Galbraith's stabilization point is a reusable measure of how early.

### Gaps
- A Stream RAG code or benchmark repository could not be confirmed. Search for "AudioCRAG-Human" on GitHub or Hugging Face.
- Exact hit rates and wasted-call rates for Jung et al. (2610.07641) and Schwarz et al. (2305.13794) were not visible on the abs pages; the full PDFs are needed.
- Feng et al. 2025 (end-to-end speech-to-text RAG) and AURA (Maben et al. 2025) are cited by Stream RAG. Their arXiv IDs and details were not fetched.

## Q2. "Speculative RAG" and other "speculative retrieval" papers: is any of them about incomplete input?

### Takeaway
No. Papers named "Speculative RAG" or "speculative retrieval" before Stream RAG are about generation-time or serving-time speculation on a *complete* query: drafting or verification, local-cache lookups during iterative retrieval, or prefetching the next retrieval during decoding. None runs on an incomplete user input. Their mechanisms (draft-then-verify, cache-then-verify, predict-then-fallback) transfer conceptually, and their waste numbers are useful priors.

### Cited Findings

**Speculative RAG: Enhancing Retrieval Augmented Generation through Drafting (ADJACENT; not about incomplete input)**
- Wang et al. (UCSD + Google), arXiv:2407.08223, ICLR 2025 — [arXiv abs](https://arxiv.org/abs/2407.08223v2); [HF](https://huggingface.co/papers/2407.08223)
- A small distilled specialist LM drafts answers in parallel from subsets of the retrieved documents. A larger generalist LM verifies the drafts in one pass. Accuracy rises up to 12.97% on PubHealth while latency falls about 51% vs conventional RAG. The query is complete; "speculative" refers to drafting, as in speculative decoding — [arXiv HTML](https://arxiv.org/html/2407.08223v2)

**Accelerating Retrieval-Augmented Language Model Serving with Speculation (RaLMSpec) (ADJACENT)**
- Zhang et al., arXiv:2401.14021, ICML 2024 (PMLR v235) — [arXiv](https://arxiv.org/abs/2401.14021); [PMLR](https://proceedings.mlr.press/v235/zhang24cq.html)
- Replaces the costly retrievals of iterative RaLM with speculative lookups in a per-request local cache. Batched verification corrects wrong speculations, preserving output quality. Adds prefetching and an optimal speculation-stride scheduler. Reported speedups are 1.75–2.39x, 1.04–1.39x and 1.31–1.77x across settings with an exact dense retriever. Speculation happens during generation, not on partial input — [arXiv](https://arxiv.org/pdf/2401.14021)

**PipeRAG: Fast Retrieval-Augmented Generation via Algorithm-System Co-design (ADJACENT)**
- Jiang et al. (Amazon/ETH), arXiv:2403.05676, KDD 2025 — [arXiv](https://arxiv.org/pdf/2403.05676v1.pdf); [Amazon Science](https://www.amazon.science/publications/piperag-fast-retrieval-augmented-generation-via-adaptive-pipeline-parallelism)
- Prefetches retrieval content using a slightly stale query window to overlap retrieval with inference. Uses flexible retrieval intervals and a performance model. Up to 2.6x latency speedup vs RETRO. Code: [github.com/amazon-science/piperag](https://awesome.ecosyste.ms/projects/github.com%2Famazon-science%2Fpiperag) — [Amazon Science PDF](https://cdn.amazon.science/fc/c3/0933db464ba4b8b31871028755af/piperag-fast-retrieval-augmented-generation-via-adaptive-pipeline-parallelism.pdf)
- The idea of retrieving on a stale or approximate query and tolerating mismatch is conceptually close to retrieving on a partial utterance — [arXiv](https://arxiv.org/pdf/2403.05676v1.pdf)

**TeleRAG: Efficient RAG Inference with Lookahead Retrieval (ADJACENT)**
- UW SyFI Lab, arXiv:2502.20969 — [SyFI page](https://syfi.cs.washington.edu/publications/telerag); [similar-papers listing](https://arxiv.deeppaper.ai/papers/2502.20969/similar?locale=en)
- From memory, not verified this session: it predicts which IVF index clusters will be needed and prefetches them CPU-to-GPU during LLM generation. This is a systems-level form of lookahead, not partial-utterance retrieval — [SyFI page](https://syfi.cs.washington.edu/publications/telerag)

**Predictive Prefetching for Retrieval-Augmented Generation (ADJACENT; strong waste numbers)**
- ICML 2026, arXiv:2605.17989. Authors were not listed on the notes page fetched; code is "to be confirmed" — [paper notes](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/); [emergentmind](https://www.emergentmind.com/papers/2605.17989)
- **Method:** a RetrievalPredictor reads mid-layer LLM signals to forecast an entropy spike within the next 10 tokens. A T5-small QueryGenerator then issues a future-oriented query asynchronously. On a miss, it falls back to synchronous retrieval, so worst-case latency stays at the baseline — [paper notes](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/)
- **Numbers (Llama-3.1-8B, HotpotQA vs Sync-RAG):**
  - TTFT 287 → 108 ms (−62.4%).
  - End-to-end latency 9.2 → 5.2 s (−43.5%).
  - Retrievals per 1k tokens 86 → 59.
  - EM 68.7 vs 69.2 (−0.5).
  - False positives are 38.7% of triggers; about 72% of those are reused within 50 tokens and 28% are wasted. That waste adds about 8% net overhead.
  - Source: [paper notes](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/)

**PCR: A Prefetch-Enhanced Cache Reuse System for Low-Latency RAG Serving (ADJACENT; serving-side prefetch)**
- arXiv:2603.23049 (2026). It appeared in search, but its details were not fetched — [alphaXiv](https://www.alphaxiv.org/abs/2603.23049.md)

### Inferences
- **Precise answer for the report:** "Speculative RAG" (Google/UCSD 2024) is draft-and-verify over retrieved document subsets for a fully known question. It has nothing to do with incomplete user input. The same holds for RaLMSpec, PipeRAG, TeleRAG and Predictive Prefetching, which all speculate within generation or serving.
- Predictive Prefetching's numbers are the best quantified prior for "how wasteful is speculative retrieval when predicted by a small model": about 39% false triggers, mostly reused later, with about 8% net overhead. They come from a different setting (mid-generation), so transferring them to partial-utterance prefetch is an assumption.

### Gaps
- TeleRAG's specific numbers and the author list of the ICML 2026 Predictive Prefetching paper were not verified.

## Q3. Incremental NLU: how early can intent or query be predicted?

### Takeaway
The classic incremental-NLU literature (2009–2021) shows that intent is often identifiable before the end of the utterance. It also warns that "early" accuracy is inflated by dataset artifacts. The best human-grounded data point is inCLINC (2021): even humans correctly predict the final intent for only about 66% of partial utterances. For retrieval specifically, Galbraith (2026) is the only quantitative "how early does the query stabilize" study found, and on a favorable slice it suggests stabilization after roughly a quarter of the input.

### Cited Findings

**Not So Fast, Classifier – Accuracy and Entropy Reduction in Incremental Intent Classification (inCLINC)**
- Lianna Hryczyk (LumenVox), Alessandra Zarcone and Luzian Hahn (Fraunhofer IIS). NLP4ConvAI 2021, pp. 52–67 — [ACL Anthology PDF](https://aclanthology.org/2021.nlp4convai-1.6.pdf)
- **Dataset:** built from CLINC150 with 37 intents plus out-of-scope. Partial utterances are cut at peaks in DistilGPT-2 surprisal. 630 stimuli covering 152 complete utterances; after cleaning, 538 annotated utterances (121 complete, 417 partial), with 6–9 MTurk annotations each. It is publicly released at fordatis.fraunhofer.de/handle/fordatis/213 — [ACL Anthology PDF](https://aclanthology.org/2021.nlp4convai-1.6.pdf)
- **Results on partial utterances:**
  - Humans reach 66.43% accuracy, edit overhead 0.39 and 2.43 word-chunk savings.
  - DistilBERT reaches 56.35% accuracy, EO 0.45 and 1.94 word-chunk savings, against 94.56% on complete utterances.
  - Humans had zero word-chunk savings for about 6% of utterances (13% for DistilBERT), and only one chunk saved for about 28% (28% for DistilBERT).
  - "For many partial utterances, the complete utterance's intent is not discernible."
  - Source: [ACL Anthology PDF](https://aclanthology.org/2021.nlp4convai-1.6.pdf)
- **Artifact warning:** on SNIPS, DistilBERT predicts PlayMusic after "I want to hear" (word 4 of 9) only because that phrase appears only in PlayMusic training data. The authors argue that early "correct" predictions before humans can converge reflect overfitting, and that entropy reduction across human interpretations tracks real information gain (McNemar p<0.001) — [ACL Anthology PDF](https://aclanthology.org/2021.nlp4convai-1.6.pdf)

**Earlier incremental-NLU papers**
- **Shivakumar et al., "RNN based Incremental Online SLU"** (USC, SLT 2021, arXiv:1910.10287): processes ASR output as a continuous word stream for early intent detection before end of sentence. It reports lower latency with no significant accuracy loss; the exact timing numbers were not extracted — [arXiv](https://arxiv.org/abs/1910.10287); [USC PDF](https://sail.usc.edu/publications/files/Shivakumar-SLT2021.pdf)
- **Constantin et al., "Incremental processing of noisy user utterances in the SLU task"** (arXiv:1909.13790, 2019): a model-agnostic method for incrementally produced partial utterances, with gains of up to 47.91 absolute F1 points — [arXiv](https://arxiv.org/pdf/1909.13790)
- **DeVault et al., "Detecting the Status of a Predictive Incremental Speech Understanding Model"** (Interspeech 2011): predicts the full meaning from partial speech and detects the point of "maximal understanding" during the utterance. It is the conceptual ancestor of "when to fire retrieval" — [ISCA](https://www.isca-archive.org/interspeech_2011/devault11_interspeech.pdf)
- inCLINC cites Kennington & Schlangen (2016), whose assistant displayed incremental intent hypotheses live. It notes that incremental processing can "access time-consuming external services (e.g. database queries) before the end of a user's turn," a 2021 statement of the target system's motivation — [ACL Anthology PDF](https://aclanthology.org/2021.nlp4convai-1.6.pdf)

**LLM-era "when is the question complete" measures**
- Shih et al.'s entropy-based "question completeness" (2510.07497; see Q5).
- Galbraith's tool-intent stabilization point (2606.20113; see Q1).
- Sources: [arXiv 2510.07497](https://arxiv.org/abs/2510.07497); [arXiv 2606.20113](https://arxiv.org/abs/2606.20113v1)

### Inferences
- **A sound evaluation should not label partial utterances with the final intent or query.** It should measure when speculative retrieval results converge with final-query results, as in Stream RAG's reflector and Galbraith's stabilization. inCLINC is the strongest citation for why.
- **No source gives a universal "X% of the utterance is enough" figure.** Evidence is task-dependent:
  - inCLINC: humans are correct on about two-thirds of mid-utterance cuts.
  - Galbraith: φ_suf is about 0.26–0.28 on the BM25-favorable slice of CRAG.
  - Endpoint anticipation (Q5): end of turn can be forecast up to about 2.56 s ahead, with high premature rates at long horizons.

### Gaps
- Word-savings or percentage-of-utterance curves from Shivakumar 2021 and Constantin 2019 were not extracted.
- Madureira & Schlangen 2020 (incremental processing with Transformers) and Coman et al. 2019 are cited in inCLINC but were not fetched.

## Q4. Voice-RAG and end-to-end speech retrievers: do any address latency or streaming?

### Takeaway
Several ASR-free speech-RAG systems exist (SpeechRAG/AWS 2024, WavRAG/ACL 2025, DUPAR 2026). They report speedups from skipping ASR or using caches, but they retrieve on the *complete* spoken query. Only Stream RAG (Q1) retrieves during speech.

### Cited Findings
- **Speech Retrieval-Augmented Generation without Automatic Speech Recognition (SpeechRAG; ADJACENT):** AWS AI Labs, arXiv:2412.16500 (Dec 2024). A speech adapter maps audio into a frozen text retriever's embedding space. A speech LM generates directly from audio passages. Retrieval matches the text baseline and beats ASR cascades, and the system beats cascades at high WER — [arXiv HTML v2](https://arxiv.org/html/2412.16500v2)
- **WavRAG: Audio-Integrated Retrieval Augmented Generation for Spoken Dialogue Models (ADJACENT):** Zhejiang University, Alibaba and Beijing University of Technology. ACL 2025 (long), pp. 12505–12523; arXiv:2502.14727. WavRetriever handles hybrid text-audio retrieval over a unified knowledge base, with chain-of-thought for using retrieved content. Retrieval is comparable to ASR-text RAG with about 10x acceleration, in the authors' report — [ACL Anthology](https://preview.aclanthology.org/setup/2025.acl-long.613); [arXiv](https://arxiv.org/pdf/2502.14727.pdf)
- **DUPAR (ADJACENT):** arXiv:2609.18042. Fast-path evidence cache with an audio encoder aligned to BGE-M3, and about 3.75x query-side speedup (see Q1) — [arXiv abs](https://arxiv.org/abs/2609.18042)
- **Stream RAG:** the only voice-RAG paper found that measures streaming retrieval latency during speech (see Q1) — [arXiv HTML](https://arxiv.org/html/2510.02044)

### Inferences
- **End-to-end speech retrievers could in principle run on partial audio chunks, but none of these papers evaluates that.** Combining a WavRAG/SpeechRAG-style speech encoder with Stream RAG-style interval triggering appears untested.

### Gaps
- Code availability for SpeechRAG and WavRAG was not checked. Feng et al. 2025 (cited by Stream RAG) was not located.

## Q5. "Thinking while listening" and speculative response generation during user speech (2024–2026)

### Takeaway
There is a dense 2025–2026 cluster.
- **Reasoning while listening:** SHANKS, Shih et al., Chronological Thinking, KAME.
- **Speculative response generation on partial input:** PredGen; Voice-Light; endpoint anticipation.

SHANKS is the most retrieval-relevant: it completes 56.9% of tool calls before the user finishes speaking. Endpoint Anticipation gives the cleanest waste number: 28.4% redundant computation for a 505 ms gain.

### Cited Findings

**SHANKS: Simultaneous Hearing and Thinking for Spoken Language Models (PARTIAL; tool calls while listening)**
- Cheng-Han Chiang, Xiaofei Wang, Linjie Li, Chung-Ching Lin, Kevin Lin, Shujie Liu, Zhendong Wang, Zhengyuan Yang, Hung-yi Lee and Lijuan Wang. The affiliations are likely NTU and Microsoft, but that is UNVERIFIED because the abs page lists none. arXiv:2510.06917 (Oct 2025) — [arXiv abs](https://arxiv.org/abs/2510.06917)
- Streams input in fixed-duration chunks and produces unspoken chain-of-thought after each chunk. That reasoning decides whether to interrupt the user and when to call tools — [arXiv abs](https://arxiv.org/abs/2510.06917)
- **Numbers:** interruption accuracy is 37.1% higher than a no-thinking baseline in a math scenario. In tool-augmented dialogue, 56.9% of tool calls complete before the user finishes the turn. No code link; there is a project page at d223302.github.io/SHANKS — [arXiv abs](https://arxiv.org/abs/2510.06917)
- SHANKS describes Stream RAG as focused on when to issue retrieval or tool queries while listening, without explicit silent chain-of-thought — [arXiv HTML](https://arxiv.org/html/2510.06917v2)

**Can Speech LLMs Think while Listening? (PARTIAL; reasoning onset on incomplete questions)**
- Yi-Jen Shih, Desh Raj, Chunyang Wu, Wei Zhou, SK Bong, Yashesh Gaur, Jay Mahadeokar, Ozlem Kalinli and Mike Seltzer. The authors appear to be Meta-affiliated, but that is UNVERIFIED because the abs page lists none. arXiv:2510.07497 (Oct 2025) — [arXiv abs](https://arxiv.org/abs/2510.07497)
- **Method:** chain-of-thought fine-tuning of multi-stream speech LLMs. An entropy-based "question completeness" metric decides when to start reasoning before the user finishes. DPO on rejection-sampled preferences improves the accuracy/latency trade-off — [arXiv abs](https://arxiv.org/abs/2510.07497)
- **Numbers:** text reasoning gives 2.4x average accuracy across spoken reasoning tasks. At equal latency, the completeness-based approach gains +4% on ARC-Easy. DPO cuts latency 70% with no accuracy loss. No code link — [arXiv abs](https://arxiv.org/abs/2510.07497)

**Chronological Thinking in Full-Duplex Spoken Dialogue Language Models (ADJACENT)**
- arXiv:2510.05150. Reasons incrementally over streaming audio with no lookahead, inside the listening window, so it adds no latency. Details were not fetched — [arXiv abs](https://arxiv.org/abs/2510.05150)

**KAME: Tandem Architecture for Enhancing Knowledge in Real-Time Speech-to-Speech Conversational AI (ADJACENT)**
- So Kuroki, Yotaro Kubo, Takuya Akiba and Yujin Tang. The organization (possibly Sakana AI) is UNVERIFIED. arXiv:2510.02327, ICASSP 2026 — [arXiv abs](https://arxiv.org/abs/2510.02327)
- A real-time S2S model plus a back-end LLM whose text response is injected in real time to guide speech output. It approaches cascaded accuracy on speech MT-Bench at S2S latency; the abstract gives no figures — [arXiv abs](https://arxiv.org/abs/2510.02327)
- The endpoint-anticipation paper describes KAME as using a secondary LLM to reason over partial transcripts — [arXiv 2606.13450](https://arxiv.org/html/2606.13450)

**Thinking While Speaking: Inference-Time Knowledge Transfer for Responsive and Intelligent Conversational Voice Agents (ADJACENT)**
- arXiv:2511.07397. Pairs a fast real-time model with a stronger model. It thinks while speaking, not while listening — [arXiv abs](https://arxiv.org/abs/2511.07397)

**Never Stop Thinking: Continuous-Time Language Agents (ADJACENT)**
- arXiv:2609.17416. Per the search snippet (not fetched), it reports that thinking while listening hides latency only when the thinking fits within the remaining speech window. That is the same bound logic as Galbraith's H — [arXiv HTML](https://arxiv.org/html/2609.17416)

**PredGen: Accelerated Inference of LLMs through Input-Time Speculation for Real-Time Speech Interaction (PARTIAL; speculative response generation on partial input)**
- Shufan Li and Aditya Grover (affiliation, likely UCLA, UNVERIFIED). arXiv:2506.15556 (v1 Jun 2025, v2 Oct 2025) — [arXiv abs](https://arxiv.org/abs/2506.15556)
- Generates candidate responses while the user is still speaking so TTS can start almost immediately. Candidates are verified against the final input and accepted, partially reused, or discarded. About 2x latency reduction in simulations on LMSys and MT-Bench, with "minimal additional computation." No code link — [arXiv abs](https://arxiv.org/abs/2506.15556); [arXiv PDF](https://arxiv.org/pdf/2506.15556)

**Endpoint Anticipation for Low-Latency Spoken Dialogue (PARTIAL; speculative execution triggered by forecast end of turn)**
- Sathvik Udupa, Shinji Watanabe, Petr Schwarz and Jan Černocký (Brno University of Technology and CMU). arXiv:2606.13450 (Jun 2026) — [arXiv HTML](https://arxiv.org/html/2606.13450)
- **Method:** a 25M-parameter streaming Transformer on Mimi codec features at 12.5 Hz forecasts end of turn 320–2560 ms ahead. On a forecast, the system forks the LLM, pre-synthesizes a TTS cache, and releases it if the endpoint is confirmed, otherwise discards it — [arXiv HTML](https://arxiv.org/html/2606.13450)
- **Numbers:**
  - In the Unmute integration, average latency falls from 1195 ms to 690 ms (−505 ms) at h=960 ms, at 28.4% expected redundant computation.
  - At ERC about 33% (h=640 ms), the premature anticipation rate is 66.2%.
  - At ERC about 15% (h=1280 ms), it is 34.3%.
  - Code: [github.com/bloodraven66/EndpointAnticipation](https://github.com/bloodraven66/EndpointAnticipation). Source: [arXiv HTML](https://arxiv.org/html/2606.13450)

**Voice-Light: A Full-Duplex Cascaded Voice Agent with Causal Turn-Taking and Speculative Generation (PARTIAL)**
- arXiv:2609.20995 (2026). Holds speculative candidates until the final ASR and transcript-revision checks pass; only minor revisions (case, punctuation) keep the speculative work. Details were not fetched — [arXiv PDF](https://arxiv.org/pdf/2609.20995)

**Discourse-Aware Dual-Track Streaming Response for Low-Latency Spoken Dialogue Systems (ADJACENT)**
- arXiv:2602.23266 (2026). It appeared in search but was not fetched — [arXiv PDF](https://arxiv.org/pdf/2602.23266)

### Inferences
- **The 2025–2026 "think while listening" papers mostly treat retrieval as one kind of tool call.** SHANKS's 56.9% pre-turn-end tool completion and Stream RAG's 20–53% first-token savings are the best published evidence that retrieval during speech pays off in LLM voice agents.
- **Validate-on-final-transcript is converging as a standard design pattern.** Jung et al., Voice-Light, PredGen and Endpoint Anticipation all gate speculative work on the final transcript or endpoint, and fall back to the serial pipeline on a mismatch.

### Gaps
- No code was found for SHANKS, PredGen, Shih et al. or Jung et al.
- Voice-Light, Chronological Thinking and Discourse-Aware Dual-Track were not fetched for numbers.

## Q6. Cost and waste tradeoffs of speculative prefetching in LLM and voice pipelines

### Takeaway
Only a handful of papers quantify waste, and none does so for passage prefetch on partial utterances. The available numbers come from response prefetch, end-of-turn speculation, mid-generation retrieval prefetch, and Stream RAG's design choices. Every system bounds the worst case at the serial baseline through a fallback.

### Cited Findings
- **Chang et al. 2020 (Google):** treats prefetch rate as the cost axis. End-to-end prefetching is 120 ms faster than silence-based prefetching at the same prefetch rate, with about 200 ms total saving — [Google Research](https://research.google/pubs/low-latency-speech-recognition-using-end-to-end-prefetching/)
- **Schwarz et al. 2023 (Amazon):** frames the problem as latency gain from successful predictions vs cost from failed prefetches. A failed prefetch costs compute but no latency — [arXiv abs](https://arxiv.org/abs/2305.13794); [arXiv PDF](https://arxiv.org/pdf/2305.13794)
- **Endpoint Anticipation 2026:** 28.4% expected redundant computation buys a 505 ms average latency cut. Waste falls to about 15% at a longer horizon with fewer premature triggers (premature anticipation rate 34.3%) — [arXiv HTML](https://arxiv.org/html/2606.13450)
- **Predictive Prefetching for RAG (ICML 2026):** 38.7% of triggers are false positives; 72% of those are reused and 28% wasted, for about 8% net overhead. Total retrievals still drop 31% — [paper notes](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/)
- **Stream RAG:** two cost designs.
  - **Fixed-interval:** queries every 1 s, with a reflector to decide reuse; this costs many queries per utterance.
  - **Model-triggered:** emits NO_QUERY unless the query changes materially, which suppresses redundant tool calls.
  - Source: [arXiv HTML](https://arxiv.org/html/2510.02044)
- **Galbraith 2026:** the hideable-latency bound H(L, δ) gives an ex-ante way to decide whether speculation is worth it for a given tool latency and speaking rate — [arXiv abs](https://arxiv.org/abs/2606.20113v1)
- **RaLMSpec:** uses a speculation-stride scheduler to balance verification cost against speculation depth — [arXiv](https://arxiv.org/pdf/2401.14021)

### Inferences
- **The literature gives approximate priors of about 15–40% redundant compute for speculation that saves hundreds of milliseconds.** In this design, cheap retrieval (vector search costing a few to tens of ms) makes waste much less costly than speculative LLM generation. That suggests aggressive multi-hypothesis prefetch is economically easier than PredGen-style speculative generation. This is an inference, not a measured result.

### Gaps
- No paper found reports dollars or tokens wasted per conversation for partial-utterance retrieval prefetch.
- No paper found explicitly studies multi-candidate (top-N predicted completions) passage prefetch with cancellation.
