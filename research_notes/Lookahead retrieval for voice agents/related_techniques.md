# Transferable Techniques for Look-ahead Retrieval in Voice Agents (related fields)

Scope: designs, algorithms, and metrics from other fields that carry over to running retrieval on partial ASR transcripts, predicting the final query, prefetching candidates, and cancelling wrong guesses. Research date: Nov 2026.

How verified each source is:
- **[verified]**: I read the primary source (abstract, HTML or PDF) in this session.
- **[snippet]**: comes only from search-result summaries. Check it before quoting numbers.
- **[prior knowledge, not re-fetched]**: from my background knowledge, with the canonical URL. Confirm before citing.

---

## Q1. Search-as-you-type / instant search (Google Instant, QAC, prefix retrieval and caching)

### Takeaway
Google Instant is the best-documented large-scale case of "retrieve on every prefix". It multiplied backend results-page load by 5–7x per query. Google handled that with new high-rate caches, per-user state that avoids re-sending results the user has already seen, and a fixed page frame with only the results updated. It was retired in 2017 for mobile and UX consistency; no source cites cost as the reason. QAC research supplies the "predict the final query from a prefix" machinery and its metrics (MRR at prefix length, context-aware hybrids).

### Cited Findings
- **Google Instant load multiplier.** Google's own engineering post ("Google Instant, behind the scenes", Sept 9, 2010) says the infrastructure team was told it would need to serve **5–7x more results pages per query**. [snippet] — [Google blog](https://googleblog.blogspot.com/2010/09/google-instant-behind-scenes.html); [HighScalability summary](https://highscalability.com/how-did-google-instant-become-faster-with-5-7x-more-results/)
- **How Google absorbed the load.** (1) New caches built for high request rates that still keep results fresh under continuous re-indexing. (2) "User-state data" in the backends that tracks which results pages a user has already been shown, so they are not re-sent. (3) Optimized rendering JavaScript. A spokesperson added that the results-page frame stays fixed while only the results are regenerated inside it. [snippet] — [Datacenter Knowledge](https://www.datacenterknowledge.com/hyperscalers/google-adds-capacity-for-instant-launch)
- **Cost.** Google confirmed it bought additional servers but would not say how many. On the Q3 2010 earnings call, Jonathan Rosenberg called Instant "pretty expensive" in resources. [snippet] — [eWeek](https://www.eweek.com/news/google-instant-costly-as-it-prepares-for-mobile/); [Silicon UK](https://silicon.co.uk/workspace/google-instant-search-is-costly-10713)
- **Discontinuation (July 26, 2017).** Google's stated reason was that most searches happen on mobile and it wanted a consistent experience across devices. Suggestions remained; results stopped loading until the user pressed enter. Coverage notes Instant never shipped on mobile because of bandwidth and resource constraints (several result sets loaded per typed query). — [Engadget](https://www.engadget.com/2017/07/26/google-drops-instant-search-unify-mobile-and-desktop/); [9to5Google](https://9to5google.com/2017/07/26/google-instant-desktop-search-removed/); [Android Police](https://www.androidpolice.com/2017/07/26/google-ditching-instant-search-searches-happen-mobile/)
- **Context-sensitive QAC (Bar-Yossef & Kraus, WWW 2011).** NearestCompletion ranks completions by cosine similarity (term-weighted vectors) between candidates and the user's recent queries. When the context is relevant, its MRR after **1 typed character is 48% higher** than MostPopularCompletion. When the context is irrelevant, its MRR is about 0. HybridCompletion (a blend of both) dominates both baselines, with **+31.5% MRR on average**. Evaluated on the AOL log. — [PDF](https://www.ee.technion.ac.il/people/zivby/papers/consuggest/consuggest.pdf); [DBLP](https://dblp.uni-trier.de/rec/conf/www/Bar-YossefK11.html)
- **QAC survey.** Cai & de Rijke, "A Survey of Query Auto Completion in Information Retrieval", Foundations and Trends in IR, 2016. Covers time-sensitive and user-centered QAC and metrics such as MRR, success rate at top-k, and "keystrokes saved". [prior knowledge, not re-fetched] — [NOW Publishers](https://www.nowpublishers.com/article/Details/INR-055)
- **Prefix-indexed retrieval.** Bast & Weber, "Type Less, Find More: Fast Autocompletion Search with a Succinct Index" (SIGIR 2006). Their HYB index answers prefix + word-completion queries by reusing the result for the previous, shorter prefix and filtering it incrementally. This is the "incremental refinement from the prior prefix's result set" pattern. [prior knowledge, not re-fetched] — [ACM DL](https://dl.acm.org/doi/10.1145/1148170.1148234)

### Inferences
- A voice agent faces the same multiplier: a 3–5 s utterance re-queried every 300–500 ms yields 6–15 retrievals per turn. Google's levers map directly:
  - cache keyed on a normalized partial query;
  - don't re-fetch or re-rank what the session has already seen;
  - keep a stable "frame" (prompt and context skeleton) and swap only the retrieved chunks.
- QAC lessons for predicting the final query:
  - Session context (prior turns) is a strong predictor when it is relevant and harmful when it isn't, so use a hybrid that backs off to popularity priors.
  - Measure prediction quality as a function of prefix length (MRR@prefix-length), not only at the end.
- Instant's retirement is a reminder that speculative results *shown* to users can hurt UX. In voice the speculation is hidden, which removes the UX objection but leaves the cost one.

### Gaps
- I didn't fetch the full text of Google's 2010 blog post, so cache hit rates and the user-state design are unknown.
- No source in this session gives Algolia or Elasticsearch typeahead internals (e.g., edge-ngram / `search_as_you_type` field, completion suggester FSTs, Algolia's prefix-on-last-word default) with published latency numbers. Verify separately.
- I didn't retrieve neural QAC numbers (e.g., Park & Chiba 2017 char-LSTM QAC; Transformer QAC), nor Cai & de Rijke's survey tables.

---

## Q2. Speculative execution, branch prediction, prefetching (CPU, storage, web) and their metrics

### Takeaway
Hardware prefetching has a mature, directly reusable metric triad: **accuracy** (useful/issued), **lateness/timeliness** (useful but arrived too late), and **pollution** (harm to the cache from evicting useful data). It also has a proven controller (Feedback-Directed Prefetching) that throttles aggressiveness per interval from those metrics. Browser speculation (Chrome) adds confidence-threshold tiers: preconnect at about 30%, prerender at about 50%. It also adds hard caps on concurrent speculations with FIFO eviction, and suppression under resource pressure.

### Cited Findings
- **FDP metric definitions (Srinath, Mutlu, Kim, Patt, HPCA 2007).** [verified]
  - *Prefetch accuracy* = Useful prefetches / prefetches sent to memory. A prefetch counts as useful if a demand request touches the block while it is still resident.
  - *Prefetch lateness* = late useful prefetches / useful prefetches. A prefetch is late if its data hasn't returned by the time the demand access arrives.
  - *Pollution* = demand misses caused by the prefetcher / total demand misses. A miss is "caused by the prefetcher" if it would not have occurred without it.
  - Hardware tracking: a pref-bit per cache tag, counters `pref-total` and `used-total`, and MSHR flags for lateness.
  - — [Srinath et al. PDF](https://users.ece.cmu.edu/~omutlu/pub/srinath_hpca07.pdf)
- **Empirical break-even.** On benchmarks where prefetch accuracy was **<40%**, the stream prefetcher *always* degraded performance versus no prefetching. Above 40% (except mcf) it improved performance significantly, and higher aggressiveness helped only when accuracy was high. [verified] — [Srinath et al.](https://users.ece.cmu.edu/~omutlu/pub/srinath_hpca07.pdf)
- **FDP controller.** [verified]
  - Every **8192 L2 evictions** (one interval), it classifies accuracy as high/medium/low (thresholds **A_high = 0.75, A_low = 0.40**), lateness as late/not late (**T_lateness = 0.01**), and pollution as high/low (**T_pollution = 0.005**).
  - It then increments or decrements a "Dynamic Configuration Counter" that selects prefetch distance and degree. Levels range from Very Conservative (distance 4, degree 1) to Very Aggressive (distance 64, degree 4).
  - Pollution also selects the insertion position (thresholds P_low = 0.005, P_high = 0.25).
  - Prefetches get the **lowest priority** so they never delay demand requests.
  - The authors suggest raising A_high and A_low when bandwidth contention is higher.
  - Results: **+13.6% performance** at similar bandwidth versus a conventional stream prefetcher, or **18.7% less bandwidth** at matching the best stream config. Versus a GHB delta-correlation prefetcher, **+9.9%**.
  - The paper also notes prefetching is a positive-feedback loop (prefetch-induced misses trigger more prefetches) and needs a negative-feedback throttle.
  - — [Srinath et al.](https://users.ece.cmu.edu/~omutlu/pub/srinath_hpca07.pdf); [UT TR version](https://utw10235.utweb.utexas.edu/pub/TR-HPS-2006-006.pdf)
- **Chrome address-bar predictive loading.** Chrome learns from typing and selection history. At about **30% confidence** it preconnects; at about **50%** it prerenders (inspect at `chrome://predictors`). [verified] — [Chrome: Prerender pages](https://developer.chrome.com/blog/prerender-pages/)
- **Speculation Rules API eagerness tiers.** [verified]
  - `conservative`: pointer/touch down; default for document rules.
  - `moderate`: desktop hover ≥200 ms or pointerdown; mobile 500 ms after scrolling stops.
  - `eager`: desktop 10 ms hover; mobile 50 ms after the link enters the viewport (per the page, a Chrome 143 / Jan 2026 change).
  - `immediate`: as soon as the rules are seen; default for list rules.
  - — [Chrome: Prerender pages](https://developer.chrome.com/blog/prerender-pages/)
- **Caps and suppression.** [verified]
  - `immediate`: 50 prefetches / 10 prerenders (dynamic).
  - `eager`/`moderate`: mobile 6 prefetch / 2 prerender; desktop 2/2.
  - `conservative`: 2/2.
  - All FIFO: a new user-triggered speculation cancels the oldest.
  - Speculation is suppressed under Save-Data, Energy Saver on low battery, memory pressure, in background tabs, or when the user disables preload.
  - Chrome warns that over-speculation costs users bandwidth, memory and CPU, and that prerender is much more expensive than prefetch.
  - — [Chrome: Prerender pages](https://developer.chrome.com/blog/prerender-pages/); [Chrome: Speculation rules improvements](https://developer.chrome.com/blog/speculation-rules-improvements)

### Inferences
- **Use the FDP triad as the look-ahead retrieval dashboard:**
  - *Accuracy*: speculative retrievals whose results were used in the final context / speculative retrievals issued.
  - *Coverage*: final retrievals served fully or partly from speculation / total final retrievals. This is the standard prefetch-coverage notion; I didn't verify it in FDP itself.
  - *Lateness*: useful speculative retrievals still in flight at end-of-turn / useful ones.
  - *Pollution*: cases where speculative chunks displaced better chunks in a fixed-size context or cache, i.e. final answer quality fell versus non-speculative retrieval.
- **Transferable policy.** Throttle speculation per session or per tenant with interval-based feedback, using tiers analogous to FDP: few speculative queries at low accuracy, more at high accuracy. Start with A_low of about 0.4 as a "don't bother" floor, since below it hardware prefetching was net-negative. The real break-even depends on retrieval cost versus latency value; see Q6.
- **Confidence tiers à la Chrome.** Below about 30% predicted-final-query confidence, do only cheap warming (e.g., embed the partial text, warm the ANN shard or connection, or a BM25 prefix probe). Above about 50%, run full retrieval plus rerank, or even prefill LLM KV with retrieved docs ("prerender").
- **Cap concurrent speculations** (Chrome uses 2 for low-confidence triggers), with FIFO or "newest wins" cancellation. Give speculative work lowest scheduling priority so it can't delay the non-speculative path.

### Gaps
- I didn't retrieve CPU branch-predictor accuracy figures (e.g., TAGE MPKI) or storage/DB prefetch numbers (e.g., Linux readahead, database prefetch accuracy). They are less directly needed.
- I didn't find published Chrome field data on speculation hit rate or waste. The "Measuring performance" section (e.g., `activationStart`, prerender final-status reasons) wasn't read.

---

## Q3. Speculative decoding and speculative tool calling / actions in LLM agents

### Takeaway
A 2025–2026 literature now exists on speculatively executing tool calls before the LLM commits to them. One line of work (Speculative Actions, PASTE, SMC) uses a cheap predictor plus verify-and-commit. Another (Stream RAG, Speculative Interaction Agents) applies the same idea directly to *partial user speech*, which is precisely the voice look-ahead problem. Reported gains are 20–53% lower tool latency, or 1.3–2.2x end-to-end speedups. Next-action prediction accuracy tops out around 55% in general agent domains.

### Cited Findings
- **Stream RAG (Arora et al., Meta + CMU, arXiv 2510.02044, Oct 2025): the closest prior art.** [verified, HTML]
  - *Fixed-interval variant.* A query is generated every **1 s** block, so B parallel tool threads run and each block's results are cached. At end-of-speech a "reflector" picks the earliest block b* whose query matches the final query: **top-5 web docs identical**, or identical KG results. Later calls are terminated and R_{b*} is used. It needs no training but costs compute, and its gains are limited by the reflector. Reported: **10.7%** tool-latency reduction (Open Book Qwen-Omni, 3.37 s baseline).
  - *Model-triggered variant.* Audio arrives in **500 ms** blocks. Word-level timestamps (OWSM CTC v4) build the partial transcripts, and words straddling a block boundary are dropped. After each block the model emits either `NO_QUERY` or a new query, conditioned on audio so far and the last non-empty query. **Only one tool thread** runs at a time: a new query immediately cancels the in-flight call. There is no reflector; the latest results are used.
  - *Training.* Labels are NO_QUERY when the pseudo-ground-truth query is "similar" to the previous one (exact match for KG; unchanged top-5 docs for web). Pseudo-GT queries come from Llama-4-Maverick. **Negative sampling** replaces the previous query with a wrong one at p = 0.1 so the model learns to recover; accuracy is 39.8 with it vs 36.5 without. 16K TriviaQA-derived training questions.
  - *Results (Qwen2.5-7B, AudioCRAG).* Accuracy 26.3 → **34.2** (synthetic) and 26.9 → 37.4 (human speech) vs Open Book; closed book is 11.1. Tool-use latency savings are **20.7% (synthetic) and 53.4% (human-recorded)**. P50 tool latency 2.78 → 2.20 s and P90 4.90 → 4.37 s; P50 first-token latency 5.90 → 5.32 s. Latencies **exclude endpoint detection**, which the authors say would make the savings larger. The paper reports no wasted-call counts.
  - — [arXiv abs](https://arxiv.org/abs/2510.02044); [HTML](https://arxiv.org/html/2510.02044v1)
- **Speculative Interaction Agents (Hooper, Kang, Moon, … Gholami, Keutzer; Berkeley; arXiv 2605.13360, May 2026).** Asynchronous I/O decouples the reason/act loop from waiting on user or environment. "Speculative tool calling" executes tools while the agent is unsure it has full info, or while more user input may still arrive. A clock-based training method adapts small models to streaming input. Results: **1.3–1.7x** speedups with "minor accuracy loss" for cloud models on real-time APIs, and **1.6–2.2x** for Qwen2.5-3B / Llama-3.2-3B across tool-calling benchmarks. [verified, abstract only] A search summary says it holds sensitive or side-effecting tools until confirmed [snippet, unverified]. — [arXiv](https://arxiv.org/abs/2605.13360)
- **Speculative Actions (Ye, Ahuja, Liargkovas, Lu, Kaffes, Peng; Columbia; arXiv 2510.04371; ICLR 2026).** Faster models predict the next actions and execute them in parallel; results are committed only if they match the actual action ("lossless"). Next-action accuracy is **up to 55%** and latency reduction **up to 20%**, across gaming, e-commerce and web search, plus a lossy OS-tuning extension. It includes a cost–latency analysis of *speculative breadth* (number of branches) and "selective branch launching". [verified, abstract] — [arXiv](https://arxiv.org/abs/2510.04371); [ICLR'26 PDF](https://www.cs.columbia.edu/~kkaffes/papers/speculative-actions-iclr26.pdf)
- **PASTE / "Act While Thinking" (Microsoft Research, arXiv 2603.18897).** Pattern-aware speculative tool execution exploits recurring tool-call sequences and parameter dependencies; it reports **48.5%** lower average task completion time. [snippet] — [MSR page](https://www.microsoft.com/en-us/research/publication/act-while-thinking-accelerating-llm-agents-via-pattern-aware-speculative-tool-execution/)
- **Speculative Macro Commit (arXiv 2609.03236).** A drafter executes predicted multi-step action chains on an environment snapshot and commits them when the actor's next call matches. It reports **10.23%** lower latency than the Speculative Actions baseline on τ²-Bench Telecom. [snippet] — [arXiv PDF](https://arxiv.org/pdf/2609.03236)
- **Speculative tool calls in serving (arXiv 2512.15834).** Speculates tool work and keeps prompts resident in the inference engine, with reported throughput gains of hundreds of tokens/s. [snippet] — [arXiv PDF](https://www.arxiv.org/pdf/2512.15834)
- **LLMCompiler (Kim et al., ICML 2024).** A planner builds a DAG of function calls; a task-fetching unit dispatches calls in parallel as soon as their dependencies resolve. Versus ReAct: up to **3.7x** latency speedup, **6.7x** lower cost, about 9% higher accuracy (HotpotQA 1.80x / Movie Rec 3.74x speedup). **1.35x** faster than OpenAI parallel function calling. [snippet, consistent across mirrors] — [arXiv](https://arxiv.org/abs/2312.04511)
- **RAGCache (Jin et al., arXiv 2404.12457).** "Dynamic speculative pipelining" overlaps vector search with LLM prefill: it starts generating on intermediate ANN results and restarts if the final top-k differs. It also caches KV states of retrieved docs in a GPU/host "knowledge tree". **Up to 4x lower TTFT** and 2.1x throughput vs vLLM+Faiss; 3.5x TTFT vs SGLang. [snippet] — [arXiv](https://arxiv.org/abs/2404.12457)
- **Speculative decoding (Leviathan, Kalman, Matias, ICML 2023).** A draft model proposes γ tokens and the target verifies them in parallel, with rejection sampling preserving the exact output distribution. With acceptance rate α, the expected tokens per target step is (1 − α^{γ+1}) / (1 − α). The paper reports **2–3x** speedups on T5-XXL. [prior knowledge, not re-fetched] — [arXiv 2211.17192](https://arxiv.org/abs/2211.17192); see also Chen et al. 2023 [arXiv 2302.01318](https://arxiv.org/abs/2302.01318)
- Others surfaced but not examined: SPORK (arXiv 2607.03333) and "Speculate While You Reason" (arXiv 2607.25816). [snippet only] — [arXiv 2607.03333](https://arxiv.org/abs/2607.03333)

### Inferences
- **Two architectures from Stream RAG to choose between:**
  - *(a) Fan-out + reflector:* parallel, no training, higher waste, and a match/verify step at end-of-turn.
  - *(b) Single-thread, model-triggered, "newest wins" cancellation:* trained `NO_QUERY` gating, minimal waste.
  - Option (b) suits cost-sensitive production. Its `NO_QUERY` gate is effectively a learned "result-set-stability" predictor, trained on whether the top-5 would change.
- **Verification criterion for reuse.** "Top-k of the speculative query equals top-k of the final query" (Stream RAG used k = 5) is a cheap, model-agnostic commit test, analogous to speculative decoding's accept/reject. A relaxed version uses RBO or Jaccard@k ≥ threshold; see Q5.
- **Side effects.** Speculate only on read-only or idempotent tools (retrieval qualifies). Gate side-effecting tools on confirmation, as Speculative Interaction Agents reportedly do and as browser prerender defers "intrusive APIs" until activation.
- **Speculate one layer deeper (RAGCache).** Prefill the LLM's KV cache with speculative documents and discard it if the final retrieval differs. This is the "prerender" analog, while running only the retrieval is the "prefetch" analog.

### Gaps
- Full-paper details (waste rates, branch counts, cancellation costs) for Speculative Actions, Speculative Interaction Agents, PASTE and SMC weren't read; only abstracts or snippets.
- No source reported wasted-retrieval ratios for voice look-ahead specifically.

---

## Q4. Simultaneous machine translation: deciding when partial input is enough, and latency/stability metrics

### Takeaway
SiMT has two transferable policies. **Wait-k** is a fixed lag: act after k source tokens. **Re-translation** recomputes on every prefix and measures flicker with **Normalized Erasure**, aiming for NE < 0.2. Its metrics carry straight over: **Average Lagging** (tokens or seconds behind an ideal "wait-0" oracle) for latency, and **erasure / revision rate** for how often the speculative result changes.

### Cited Findings
- **Wait-k / STACL (Ma et al., ACL 2019).** The model is trained prefix-to-prefix: each target token y_t is predicted from source prefix x_{1..t+k}, often before the corresponding source word is seen ("implicit anticipation"). **Average Lagging (AL)** measures how many source tokens the output lags behind an ideal wait-0 policy, averaged up to the cut-off step τ (when the full source has been read): AL = (1/τ) Σ_{i=1..τ} [g(i) − (i−1)/r], where g(i) is the number of source tokens read when emitting target i and r = |y|/|x|. Wait-k has AL ≈ k. — [arXiv 1810.08398](https://arxiv.org/abs/1810.08398); formula restated in [arXiv 2210.12357](https://arxiv.org/pdf/2210.12357)
- **AL critiques.** AL can reward over-generation; Papi et al. propose length-adaptive AL (LAAL). Cherry & Foster (2019) propose Differentiable AL (DAL), which the re-translation papers prefer. [snippet] — [AutoSimTrans 2022](https://aclanthology.org/events/autosimtrans-2022/); [Arivazhagan et al. 2020](https://arxiv.org/abs/2004.03643)
- **Re-translation and erasure (Arivazhagan et al., 2019/2020).**
  - *Erasure* = number of tokens deleted from the previous output's suffix to produce the next one.
  - *Normalized Erasure (NE)* = total erasure / final output length.
  - The "low-revision" operating point is **NE < 0.2**, i.e. fewer than 1 revised token per 5 output tokens.
  - *Biased beam search* (bias decoding toward the previous output's prefix) combined with wait-k inference reduces revisions "to negligible levels".
  - Re-translation was found competitive with or better than streaming wait-k on the quality–latency trade-off.
  - [snippet + abstract] — [arXiv 2004.03643](https://arxiv.org/abs/2004.03643); [arXiv 1912.03393](https://arxiv.org/abs/1912.03393)
- **NE limitation.** NE counts only from the first point of difference, which motivates "Normalized Click-N-Edit" (2021). Dynamic masking (hold back the last few unstable tokens of the prefix) improves stability. [snippet] — [arXiv 2012.14681](https://arxiv.org/abs/2012.14681); [arXiv 2006.00249](https://arxiv.org/abs/2006.00249)
- An open-source implementation of NE exists in simulstream. — [simulstream docs](https://simulstream.readthedocs.io/en/stable/generated/simulstream.metrics.stats.NormalizedErasure.html)

### Inferences
- **The "re-translation" model applies directly:** re-run query prediction and retrieval on each ASR partial. Then:
  - Track a **retrieval erasure rate**: top-k items that drop out between successive prefixes, normalized by k × number of updates.
  - Apply **biased decoding** in the query rewriter (condition on the previous predicted query, as Stream RAG does) to suppress churn.
  - Apply **dynamic masking**: drop the last 1–2 ASR words, which are the least stable. Stream RAG already drops words straddling a block boundary.
- **Wait-k analog:** don't issue retrieval until k content words have been recognized, or until the predicted query is stable for N consecutive partials.
- **Latency metric analog:** "retrieval lag", the time between the moment the final top-k first appeared in the speculative stream and end-of-speech (negative values are good). Compute it AL-style, against an oracle that knows the final query.

### Gaps
- I didn't re-verify the exact NE formula or DAL equations from the PDFs.
- There's no SiMT work on retrieval specifically; the mapping is my inference.

---

## Q5. Prefix/semantic caching of RAG results, incremental re-ranking, result-set stability metrics

### Takeaway
To decide whether a speculative result "has converged", use top-weighted rank-similarity metrics (RBO, or simple Jaccard / overlap@k) between successive prefixes and between speculative and final results. For caching, key on the predicted-query embedding and reuse KV states of retrieved docs (RAGCache).

### Cited Findings
- **Rank-Biased Overlap (Webber, Moffat, Zobel, ACM TOIS 2010).**
  - Agreement at depth d = |S_{1:d} ∩ T_{1:d}| / d.
  - RBO = (1 − p) Σ_d p^{d−1} · A_d. This is the geometrically weighted average of agreements; written with the "(1 − p)/p" normalizer when the sum is indexed differently.
  - The result lies in [0, 1]: 0 for disjoint lists, 1 for identical ones.
  - *p* is the persistence probability that a user continues from depth d to d+1. Small p weights the top heavily.
  - Handles non-conjoint, truncated ("indefinite") rankings, with a residual for the unseen tail.
  - [snippet via 2024 ties paper] — [Original TOIS paper (ACM DL)](https://dl.acm.org/doi/10.1145/1852102.1852106); [arXiv 2406.07121](https://arxiv.org/abs/2406.07121)
- **Exact top-k match as the reuse test.** Stream RAG uses exact top-5 web-document identity (or identical KG output) to decide that a speculative query is equivalent to the final one, both for reuse (reflector) and for `NO_QUERY` training labels. [verified] — [Stream RAG HTML](https://arxiv.org/html/2510.02044v1)
- **RAGCache.** A knowledge tree caches KV states of retrieved docs across GPU and host memory, shared across requests. Speculative pipelining overlaps retrieval with prefill. Up to 4x TTFT gain. [snippet] — [arXiv 2404.12457](https://arxiv.org/abs/2404.12457)

### Inferences
- **Stability signal for "stop speculating / commit".** Compute RBO (p ≈ 0.9, top-heavy over about the top 10) or Jaccard@5 between retrieval results for prefix t and t−1. Commit once it stays ≥ τ (e.g., 0.8) for 2 consecutive partials. Hysteresis is the SiMT/FDP-style negative feedback against flip-flopping.
- **Offline accuracy metric.** RBO(speculative top-k at time t, final top-k), plotted against the fraction of the utterance heard, gives a "convergence curve". The area under it is a single score for comparing query predictors.
- **Cache keys.** Normalized partial transcript (exact), plus an embedding of the predicted query with a cosine threshold (semantic). Prior turns provide the Bar-Yossef–style context features.

### Gaps
- No reliable source found in this session for semantic-cache hit rates or false-hit rates (GPTCache, MeanCache, "Proximity" approximate RAG caching). Search returned nothing; verify separately.
- I didn't find papers on incremental re-ranking across successive prefixes, beyond Bast & Weber's incremental prefix filtering (Q1).

---

## Q6. Cost/benefit models and decision policies for when to speculate

### Takeaway
Every field above uses the same shape: speculate when P(correct) × latency value saved > cost of the speculation (+ pollution and contention harm). Cap breadth and throttle by measured accuracy. Published designs operationalize this with confidence tiers (Chrome 30%/50%), accuracy-band throttling (FDP 0.40/0.75), a learned trigger (Stream RAG `NO_QUERY`), and explicit breadth–cost analysis (Speculative Actions).

### Cited Findings
- FDP classifies accuracy, lateness and pollution per interval and adjusts aggressiveness. Below 40% accuracy, prefetching was net-harmful on every benchmark observed. [verified] — [Srinath et al.](https://users.ece.cmu.edu/~omutlu/pub/srinath_hpca07.pdf)
- Chrome uses confidence-tiered actions (≥30% preconnect, ≥50% prerender) plus hard per-tier concurrency caps. [verified] — [Chrome docs](https://developer.chrome.com/blog/prerender-pages/)
- Speculative Actions formalizes the trade-off between speculative breadth (number of branches launched) and time saved, and uses "selective branch launching" to avoid prohibitive cost growth. [verified, abstract] — [arXiv 2510.04371](https://arxiv.org/abs/2510.04371)
- Stream RAG contrasts B parallel threads (fixed interval) with 1 thread (model-triggered), noting the compute overhead of the former. [verified] — [Stream RAG HTML](https://arxiv.org/html/2510.02044v1)
- In speculative decoding, the speedup depends on acceptance rate α and draft length γ, so tuning γ trades verify cost against expected accepted tokens. [prior knowledge, not re-fetched] — [arXiv 2211.17192](https://arxiv.org/abs/2211.17192)
- Google Instant ran at 5–7x backend load and was described as "pretty expensive". This is a concrete upper bound for naive per-keystroke speculation. [snippet] — [Datacenter Knowledge](https://www.datacenterknowledge.com/hyperscalers/google-adds-capacity-for-instant-launch); [eWeek](https://www.eweek.com/news/google-instant-costly-as-it-prepares-for-mobile/)

### Inferences
These are my synthesis, not taken from any one source.
- **Per-partial decision rule.** Issue a speculative retrieval for predicted query q̂ at time t iff
  p_t(q̂ = q_final or top-k equivalent) × E[latency saved | hit] × V_latency > C_retrieval + C_rerank + λ · contention_cost.
  - E[latency saved | hit] ≈ min(retrieval latency, expected remaining speech + endpoint delay).
  - Because remaining speech time shrinks, a late speculation saves less. This is the "lateness" analog: a speculation that finishes after end-of-turn has value of about 0 beyond a cache hit.
- **Expected waste.** Expected waste per turn = Σ_t (1 − p_t) · C_t. Fixed-interval fan-out with B blocks costs about B × C. Single-thread "newest-wins" costs at most (number of query changes) × C, minus work cancelled early.
- **Calibrate p_t** with a QAC-style predictor (context + popularity hybrid) or a learned `NO_QUERY` gate. Monitor online accuracy, coverage, lateness and pollution per FDP and throttle per interval.
- **Breadth.** Mirroring Chrome's caps of 2 and Speculative Actions' selective branching, keep 1–2 concurrent speculative queries per turn. Use the second slot only when the top-2 predicted queries are close in probability.

### Gaps
- I found no published voice-specific cost model with fitted parameters, such as dollar or GPU cost per wasted retrieval versus value per 100 ms of latency.
- The Speculative Actions cost–latency equations weren't extracted; read the full paper (Section on cost-latency analysis) for formulas.
