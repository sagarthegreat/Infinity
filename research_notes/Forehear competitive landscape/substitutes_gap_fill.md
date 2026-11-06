# Substitutes gap-fill: caches, managed retrieval, prompt caching, in-process search, and serving-side tricks vs forehear

This file adds to `latency_substitutes.md` and does not repeat it. Items already covered there are cited only where a new number changes them: VoiceAgentRAG, Proximity, RAGCache, CacheBlend/LMCache, TurboRAG, the Turbopuffer warm-cache doc, Anthropic prompt-caching mechanics, Redis LangCache, and the Mem0/Zep figures.

Labels: **[measured]** = paper or benchmark with a stated method. **[vendor]** = vendor claim or vendor-run benchmark. **[competitor-run]** = benchmark run by a rival vendor. **[secondary]** = blog or aggregator with weak or no method. **[anecdote]** = a single user report.

forehear reference numbers (from the brief, not re-verified): hosted vector DB wait 280→76 ms; with reranker 806→392 ms; about 3.5 retrieval calls per turn. Its latency profiles: hosted_kb median 250 / p95 550 ms; rerank 750 / 1400 ms; web_search 1600 / 3500 ms.

---

## Q1. Gateway / semantic caches: do any target voice or support traffic, and what hit rates and latencies are published?

### Takeaway
None of the gateway or semantic caches surveyed (Cloudflare, Portkey, Helicone, LiteLLM, GPTCache, Upstash, Momento) markets itself for voice or real-time traffic, and none publishes a measured hit rate on voice or call-center traffic. Cloudflare AI Gateway is exact-match only, so it is nearly useless for ASR transcripts. Portkey's 18–60% hit rates and "20x faster" are vendor claims. Semantic-hit lookups are fast (sub-ms in-process, about 20–40 ms p95 for a managed vector lookup) but need an embedding call. Read the hit-rate numbers as text-RAG figures; voice is likely lower.

### Cited Findings
**Cloudflare AI Gateway**
- Caching is exact match on the entire request. Any difference in messages, tools or model parameters creates a separate entry. The docs say semantic caching is "planned for the future". It is off by default, TTL ranges from 60 s to one month, and the `cf-aig-cache-status` header reports HIT/MISS. Only text and image responses are cached — [Cloudflare AI Gateway caching docs (preview mirror)](https://03cfcb76.previews.developers.cloudflare.com/ai-gateway/features/caching/); [index.md mirror](https://codex-container-api-docs.previews.developers.cloudflare.com/ai-gateway/features/caching/index.md). These are preview mirrors. The canonical page is developers.cloudflare.com/ai-gateway/features/caching/ and was not fetched.
- A third-party 2026 guide claims Cloudflare does similarity-based caching. That contradicts the docs and is treated as unreliable — [Redwerk](https://redwerk.com/blog/cloudflare-ai-gateway/)
- This settles the gap from the earlier notes: Cloudflare is exact-match only.

**Portkey**
- **[vendor]** Early hit rate about 20% at 99% accuracy for Q&A/RAG use cases. A later post reports 18% to 60% in RAG use cases with "accurate results 99% of the time". It claims cached requests are served "up to 20x faster and cheaper" — [Portkey blog](https://portkey.ai/blog/reducing-llm-costs-and-latency-semantic-cache/); [Portkey docs](https://docs.portkey.ai/docs/product/ai-gateway/cache-simple-and-semantic)
- Constraints: semantic cache only applies to requests under 8,191 tokens and with 4 or fewer messages. A multi-turn voice conversation with history will often exceed the message limit. The self-hosted gateway's default cosine threshold is reported as 0.95. Sources conflict on whether the threshold is user-configurable — [Portkey docs](https://docs.portkey.ai/docs/product/ai-gateway/cache-simple-and-semantic); [Portkey dev.to on thresholds](https://dev.to/portkey/semantic-caching-thresholds-and-why-they-matter-4ab3)
- **[secondary]** A Mintlify-hosted mirror of the gateway docs lists cache-hit latency of about 0.1–1 ms in-memory or about 1–5 ms with Redis. It is unclear whether these figures include the embedding call needed for a semantic lookup — [Mintlify mirror](https://www.mintlify.com/portkey-AI/gateway/concepts/caching)

**Bifrost (gateway, cited as a threshold data point)**
- **[secondary]** A threshold of 0.97 gave about 20% hits. Tuning down to 0.92 gave 58% hits, and p50 latency on hits fell from about 900 ms to about 40 ms (flaky-test summariser workload, not support or voice) — [dev.to case study](https://dev.to/claire_nguyen/semantic-caching-our-flaky-test-summariser-58-fewer-llm-calls-3c53)

**GPTCache (Zilliz)**
- An in-process Python library, so a hit is a function call, not a network hop. **[secondary, informal]** One third-party load test reported hit latency around 0.03 ms. No official hit-rate benchmark was found — [FerroCache benchmark page](https://nickleodoen.github.io/ferrocache/production/benchmarks/) (competitor page; all GPTCache cells are N/A); [e2enetworks guide](https://www.e2enetworks.com/blog/how-to-speed-up-large-language-model-pipelines-using-gptcache-a-guide-and-performance-comparison)
- **[secondary]** A review of published figures argues the "honest range" for production semantic caching is a 20–45% hit rate, depending heavily on use case — [dev.to "95% hit rate myth"](https://dev.to/gauravdagde/llm-semantic-caching-the-95-hit-rate-myth-and-what-production-data-actually-shows-8ga)

**LiteLLM**
- **[secondary, unofficial mirror]** Proxy overhead is P50 2 ms and P95 8 ms at 1000 RPS. It claims Redis cache response under 5 ms vs 1–5 s from the provider — [LiteLLM performance (Mintlify mirror)](https://www.mintlify.com/BerriAI/litellm/deployment/performance). Supported cache modes include Redis and semantic modes — [LiteLLM caching docs](https://docs.litellm.ai/docs/proxy/caching.md). A guide notes the semantic-mode cost is the embedding call, not the Redis lookup — [TrueFoundry](https://www.truefoundry.com/blog/litellm-caching)

**Helicone**
- Caching is enabled with a request header, and the post covers hit/miss tracking. No latency or hit-rate numbers are published — [Helicone blog](https://helicone.ai/blog/effective-llm-caching)

**Upstash**
- Ships an `@upstash/semantic-cache` library on Upstash Vector, and its docs recommend a small embedding model such as bge-small-en-v1.5 when latency matters — [PyPI upstash-semantic-cache](https://pypi.org/project/upstash-semantic-cache/); [Upstash blog](https://upstash.com/blog/semantic-caching-for-speed-and-savings)
- **[secondary]** A same-region estimate puts a vector-based semantic lookup at about 20–40 ms p95, vs about 5–8 ms for an exact-match Redis lookup — [dev.to Redis vs vector cache](https://dev.to/rikuq/redis-vs-vector-cache-for-llm-responses-latency-cost-and-when-to-use-each-458c)

**Momento**
- Positions itself as a serverless low-latency cache for LLM prompts and responses (LangChain integration). No semantic-cache latency or hit-rate data was found — [LangChain Momento provider](https://python.langchain.com/docs/integrations/providers/momento)

**Voice-specific**
- A voice-AI vendor guide recommends tracking time-to-first-audio together with false-positive hit rate. It warns that a cache cutting p99 by 40% while doubling escalations is failing — [FutureAGI audio caching guide](https://futureagi.com/blog/audio-caching-latency-reduction-voice-ai-2026/)
- Vapi has a blog post titled "audio caching for latency reduction". It was surfaced in search but not fetched, so its content is unverified — [Vapi blog](https://vapi.ai/blog/audio-caching-for-latency-reduction)

### Inferences
- **Classification.** All response-level caches here are substitutes on a hit and complements overall, as in the earlier notes. Cloudflare's exact-match cache is effectively **irrelevant** for voice: ASR transcripts almost never repeat byte-for-byte, and history in the request body changes every turn.
- Portkey's 4-message cap means it only caches single-shot or stateless Q&A unless history is stripped. That makes it a poor fit for multi-turn voice. LiteLLM, GPTCache and Upstash have no such documented cap.
- A semantic lookup costs an embedding call. On a hosted embedding API that is about 130–150 ms (see Q2). That is comparable to the vector-DB wait forehear hides, so a cache *miss* adds latency unless the lookup is also started speculatively on interim transcripts. That is a natural integration point for forehear.
- Pricing and adoption: no pricing was collected beyond the free/open-source nature of GPTCache, LiteLLM and the Upstash library. Gateway pricing (Portkey, Helicone, Cloudflare) was not retrieved.

### Gaps
- No measured semantic-cache hit rate on real voice or call-center traffic, from any vendor.
- GPTCache GitHub stars and license were not verified (believed MIT, unverified).
- Momento and Helicone: no latency numbers found. Cloudflare AI Gateway pricing: not fetched.
- The Vapi audio-caching post was not read.

---

## Q2. What retrieval latencies do real managed stacks have in 2026? Do forehear's profiles hold up?

### Takeaway
Measured 2026 numbers broadly support forehear's profiles, with caveats.
- **hosted_kb 250/550:** consistent with embedding plus hosted vector search over the network. ElevenLabs measured its own voice-agent RAG at 326 ms median / 629 ms p95 before optimisation and 155 / 426 after. Voyage embedding alone has a median of about 135–150 ms. Serverless cold starts (Pinecone 271 ms, unpinned Turbopuffer 2.0 s first query) produce the long tail.
- **rerank 750/1400:** plausible as an end-to-end figure (retrieve, then rerank). Voyage rerank-2.5 alone has a median of about 330 ms at K=50, 480 ms at K=100 and 580–670 ms at K=150–200, with provider-side spikes to about 2.9 s. Cohere Rerank 3.5 measured 171–459 ms in a competitor-run test.
- **web_search 1600/3500:** pessimistic for 2026's fast tiers (Exa Instant about 400 ms mean, Brave about 520–670 ms). It is realistic for Tavily basic (1.88 s) and Perplexity (1.38 s), or for any pipeline that also fetches page contents.

### Cited Findings
**Hosted KB / embedding plus vector search**
- **[measured, vendor-own system]** ElevenLabs Agents RAG overall latency, before → after replacing query rewriting with parallel self-hosted Qwen3-4B / Qwen3-30B-A3B racing external LLMs (1 s timeout falls back to the raw user message): median 326→155 ms, p75 436→250 ms, p95 629→426 ms. Query rewriting had been more than 80% of RAG latency. RAG runs on every query. The post says that for very small KBs "it can be simpler to pass everything into the prompt directly". Published Sep 12 2025, updated Sep 8 2026 — [ElevenLabs engineering blog](https://elevenlabs.io/blog/engineering-rag)
- **[measured, arXiv 2511.09545, Dallaire, Nov 2025]** Voyage embedding API median 134.0–141.2 ms (voyage-3-large), 134.0–149.2 ms (voyage-3.5) and 133.0–140.8 ms (voyage-3.5-lite). Local Elasticsearch 9.1.6 vector search median 47.6 ms flat vs 35.4 ms HNSW-f32 (n=50 queries, on a Mac laptop). Corpus size was not captured in the extract — [arXiv 2511.09545 HTML](https://arxiv.org/html/2511.09545v1)
- **[secondary]** A voice-AI test reported Pinecone at 300 ms embedding plus 150 ms search, 450 ms total — [growwstacks](https://growwstacks.com/blog/fastest-rag-solution-voice-ai-agents/)
- **[vendor-run, Zilliz VDBBench cost-aware, 10 May 2026, AWS us-west-2, LAION 100M × 768d]** First query after 24 h or more idle vs first warm query: Zilliz Capacity 55/54 ms, Turbopuffer pinned 64/45 ms, Zilliz Tiered 122/57 ms, **Pinecone Serverless 271/60 ms (4.5×)**, **Turbopuffer unpinned 2,048/322 ms (6.4×)**. P99 at *saturation* (max concurrency, topK 100): Zilliz 158–299 ms, Turbopuffer 2.34 s, Pinecone Serverless 4.85 s. Pinecone was throttled by read-unit limits at concurrency 4–5. Under a 99.9% filter, Turbopuffer P99 was 7.03 s. Cost crossover: Turbopuffer is cheaper below about 8 sustained QPS, Zilliz Tiered above — [Zilliz VDBBench blog](https://zilliz.com/blog/vdbbench-adds-cost-aware-benchmarking-for-vector-databases.md). This is a Zilliz-run benchmark of competitors, so treat it as vendor-biased.
- A secondary review says Turbopuffer cold-namespace queries can reach p99 of up to 4 s — [modern-datatools](https://modern-datatools.com/alternatives/turbopuffer)
- **[anecdote]** Pinecone mean query latency spiked to 4.1 s vs an 80 ms baseline in one personal postmortem — [dev.to postmortem](https://dev.to/johalputt/postmortem-a-vector-db-latency-spike-in-pinecone-20-caused-our-rag-pipeline-to-time-out-for-1k-408k)

**Rerankers**
- **[measured, arXiv 2511.09545]** Voyage rerank-2.5 median: about 331–339 ms at K=50 (332.9 ms in Table 8), about 478–483 ms at K=100, about 580–670 ms at K=150–200. rerank-2.5-lite: about 340–405 ms at K=50, about 640–715 ms at K=200, so "lite" was not faster here. Provider-side discontinuity: with voyage-3.5 candidates at K≥150, medians jumped to about 2.7–3.0 s (2,931 ms at K=200). Candidates were about 500 tokens each. Three runs at different times of day, client region not stated — [arXiv 2511.09545 HTML](https://arxiv.org/html/2511.09545v1)
- **[secondary, OpenRouter listing]** Voyage rerank-2.5 P50 0.39 s and rerank-3-lite P50 0.23 s (best provider, end-to-end through a gateway) — [OpenRouter rerank-3-lite](https://openrouter.ai/voyageai/rerank-3-lite-20260930); [OpenRouter rerank-2.5 mirror](https://or-api.corpsoft24.ru/voyageai/rerank-2.5)
- **[competitor-run, ZeroEntropy, Jul 2025]** Cohere Rerank 3.5: 171.5 ± 106.8 ms on 12 KB payloads and 459.2 ± 87.9 ms on 150 KB payloads. zerank-1: 149.7 / 314.4 ms. No method, hardware or document count given — [ZeroEntropy](https://zeroentropy.dev/articles/lightning-fast-reranking-with-zerank-1)
- **[secondary]** Cohere rerank-v3.5 typical P50 about 100 ms and P95 about 300 ms on 100 docs, community skill doc with no method — [cohere-performance-tuning skill](https://cdn.jsdelivr.net/npm/@intentsolutionsio/cohere-pack@1.0.2/skills/cohere-performance-tuning/SKILL.md). A reranker leaderboard lists Cohere Rerank v3 at about 0.73–0.76 s per call (composite, unclear boundaries) — [Hindsight reranker leaderboard](https://benchmarks.hindsight.vectorize.io/leaderboard/reranker)
- **[vendor]** The Vertex AI ranking API (the reranker for RAG Engine) is described as under 100 ms per request — [Google Cloud docs](https://cloud.google.com/vertex-ai/generative-ai/docs/retrieval-and-ranking)

**Managed RAG platforms**
- **Vertex AI RAG Engine [anecdote]:** a forum user reported about 30 s per query via the TypeScript library vs about 1 s in AI Studio. This points to a client or config problem, not a benchmark — [Google Developer forum](https://discuss.google.dev/t/slow-rag-engine-response-with-vertex-ai-typescript-library-30s-vs-ai-studio-1s/192069)
- **Azure AI Search vs Vertex RAG Engine [secondary, qualitative, Jun 2025]:** a single-author FRAMES test called Azure AI Search "the fastest overall" for query and ingestion. Vertex RAG Engine was fast to query once indexed but slow to ingest. A CrewAI agentic pipeline (Pinecone + OpenAI + Cohere) took about 30 s per query. No other numbers were given — [Trilogy AI Substack](https://trilogyai.substack.com/p/agentic-retrieval-deepdive)
- **Amazon Bedrock Knowledge Bases:** no published millisecond figure was found. Latency depends on the embedding model, vector store, chunking and number of results. `RetrieveAndGenerateStream` (Dec 2024) streams output — [AWS what's new](https://aws.amazon.com/about-aws/whats-new/2024/12/amazon-bedrock-agents-flows-knowledge-optimized-models); [skills.sh Bedrock KB notes](https://skills.sh/adaptationio/skrillz/bedrock-knowledge-bases)
- Azure AI Search exposes an average search-latency metric (seconds) per service, but there is no public baseline — [Datadog integration](https://docs.datadoghq.com/integrations/azure_ai_search)

**Web search APIs (web_search profile)**
- **[vendor-reported, citing Openbenchmarks boards, Sept 2026, single client, mean latency]** factual-lookup board: Parallel Turbo 348 ms, Exa Instant 398 ms, Brave 601–630 ms (523 ms search-only on hard retrieval), Parallel Fast 942 ms, Perplexity (low) 1.38 s, Tavily basic 1.88 s — [Parallel.ai report](https://parallel.ai/articles/best-web-search-api-for-ai-applications.md)
- **[vendor-run, Parallel.ai, Aug 2026, p50]** Exa Instant about 361 ms, Tavily Ultra Fast 357 ms, Brave 430 ms — [Parallel.ai Aug 2026](https://parallel.ai/articles/best-web-search-api-for-ai-applications)
- **[independent-style, AIMultiple]** Brave about 669 ms (top quality score), Tavily about 998 ms, Exa about 1,200 ms, Parallel Search Pro 13,600 ms. Perplexity was slower than Exa — [AIMultiple agentic search](https://aimultiple.com/agentic-search)
- Cost per 1,000 benchmark *questions* (LLM tokens plus tool calls, not per-request API price): Perplexity $275 frontier / $37.10 low-cost on BrowseComp; Exa $971 / $53.40; Tavily $935 / $176 — [Parallel.ai report](https://parallel.ai/articles/best-web-search-api-for-ai-applications.md)

### Inferences
- **hosted_kb 250/550 is a realistic, slightly conservative profile** for embed (about 140 ms) plus hosted search (about 50–150 ms warm), plus network. ElevenLabs' pre-optimisation 326/629 is close to it, and its post-optimisation 155/426 shows a well-tuned stack can beat it. forehear's measured 280 ms baseline sits right in this range. VoiceAgentRAG's Qdrant Cloud 97–307 ms (earlier notes) agrees.
- **The p95 tail is dominated by cold starts and provider spikes, not ANN search.** Pinecone Serverless is 4.5× slower on the first query after idle, unpinned Turbopuffer 6.4×, and Voyage rerank showed a 2.9 s anomaly. Speculative early retrieval hides exactly this tail: a first-turn cold query issued during the user's speech absorbs the cold-start penalty.
- **rerank 750/1400** matches retrieve (about 250) plus rerank at K=50–100 (about 330–480 ms median) end-to-end. If the profile models rerank *alone*, it is pessimistic for K≤100 and realistic for K≈150–200. The doc should state which.
- **web_search 1600/3500** is about 2–4× slower than 2026's fastest search APIs (about 350–650 ms) for snippet-only search. It fits Tavily basic, Perplexity, or search plus page fetch or extraction. Consider adding a "fast_web_search" profile (median about 450, p95 about 1,200; inferred, not measured).
- Managed RAG platforms (Vertex, Bedrock, Azure, Ragie, Vectara, Pinecone Assistant, Contextual AI, LlamaCloud) publish no p50/p95. They bundle embed, retrieve, rerank and sometimes generation, so they likely sit at or above the rerank profile. That makes them **complements** for forehear, not substitutes: they are slower backends to hide.

### Gaps
- No published latency was found for Ragie, Vectara, Pinecone Assistant, Contextual AI or LlamaCloud. These need first-hand measurement.
- Jina reranker v3 latency and Cohere Embed v4 latency: not found.
- Azure AI Search and Bedrock KB: no millisecond baselines.
- Arize/Artificial Analysis-style independent retrieval-API latency boards: none found beyond Openbenchmarks (cited via a competitor) and AIMultiple.

---

## Q3. Prompt / context caching as a RAG replacement: at what KB size does "put it all in the prompt" beat RAG for voice?

### Takeaway
Measured cached-prefix TTFT gains are modest at voice-relevant sizes. With a 10K-token system prompt, caching cut TTFT only 6–31% depending on provider. At 50K tokens it cut GPT-4o TTFT from 4.29 s to 1.70 s, still far over a voice budget. Practical inference: "KB in a cached prompt" substitutes for forehear only for KBs of roughly a few thousand tokens, up to perhaps about 10K, on a fast model. Above that, cached-context TTFT alone exceeds the 250–550 ms retrieval wait it would replace.

### Cited Findings
- **[measured, arXiv 2601.06007 v2, Lumer et al., Jan 2026]** 10,000-token system prompt, 40 sessions per condition. TTFT improvement from caching (system-prompt-only mode): GPT-5.2 10.5%, Claude Sonnet 4.5 22.9%, Gemini 2.5 Pro 6.1%, GPT-4o 30.9%. Full-context mode: GPT-4o −8.8% and Gemini 6.0%. Cost reduction 41–81% — [arXiv 2601.06007 HTML](https://arxiv.org/html/2601.06007v2)
- Same paper, ablation at 50K tokens: GPT-4o TTFT **4,290 ms → 1,699 ms (60%)**. Cost savings 89% (GPT-5.2), 88% (Sonnet 4.5), 54% (GPT-4o). The ablation also ran 500, 2K, 5K and 20K tokens, but per-size TTFT values were not in the extract. The abstract (13–31%) and Table 1 (6–31%) are inconsistent — [arXiv 2601.06007 HTML](https://arxiv.org/html/2601.06007v2)
- Cache minimums per the paper (Jan 2026): 1,024 tokens for GPT-4o, GPT-5.2 and Sonnet 4.5; 4,096 for Gemini 2.5 Pro. Gemini context-cache storage costs $4.50 per M tokens per hour — [arXiv 2601.06007 HTML](https://arxiv.org/html/2601.06007v2)
- **OpenAI prompt caching (current docs).** Cached input is "discounted up to 95%". For GPT-5.6 and later, reads cost 0.1× (0.05× for GPT-6.1 Sol/Terra) and writes cost 1.25× (30 min TTL, default) or 2.5× (12 h TTL). The minimum is 1,024 tokens. Caches are **per machine**: a hit requires routing to a machine holding the entry, and traffic above about 15 requests/min per prefix can overflow to other machines. The docs give no latency percentage, only "reduce the time spent processing input" — [OpenAI prompt caching guide](https://developers.openai.com/api/docs/guides/prompt-caching)
- **[secondary]** OpenAI cache hits come in 128-token blocks. Gemini implicit caching can report cached tokens even in a "no-cache" control because an earlier test warmed it — [agnt5 benchmark](https://agnt5.com/blog/prompt-caching-benchmark)
- **Gemini.** Implicit caching is on by default for 2.5 and newer. Current docs list a 4,096-token minimum for Gemini 3.x Flash and 3.1 Pro Preview and 2,048 for 2.5 Flash/Pro; an older page lists 1,024 / 4,096, so they conflict. Implicit caching carries no cost-saving guarantee; explicit caching does. No latency figure is published — [Gemini caching docs](https://ai.google.dev/gemini-api/docs/generate-content/caching); [Interactions API caching](https://ai.google.dev/gemini-api/docs/interactions/caching.md.txt)
- **[anecdote]** A May 2026 single-run harness: OpenAI 0.46 s TTFT on the first call, with the second call *slower* despite 2,816 of 3,077 tokens cached. Gemini 2.5 Pro took about 8.8–9.5 s without explicit caching — [toolbrain build log](https://toolbrain-astro.pages.dev/blog/build-log-prompt-caching-benchmarks-2026/)
- **[vendor, voice platform]** Recommends a system prompt budget of about 1,500 tokens plus a sliding window of turns and RAG context. It estimates a 5-minute support call adds about 2,250 tokens of transcript — [Simba Voice](https://simbavoice.ai/resources/why-context-windows-matter-less-than-you-think-for-voice)
- ElevenLabs (voice platform) uses RAG on every query and says only "very small" KBs should be inlined — [ElevenLabs](https://elevenlabs.io/blog/engineering-rag)
- Context from the earlier notes: Anthropic's 2024 cached 100K-token example took 2.4 s **[vendor]**.

### Inferences
- **Threshold estimate (inferred, not measured):** cached TTFT at 50K tokens is about 1.7 s (GPT-4o) and at 100K about 2.4 s (Anthropic, 2024). A cached prefix would need to stay under roughly 5–10K tokens to keep TTFT within about 300–500 ms of a no-KB prompt on mainstream hosted models. That is about 10–25 pages of FAQ. Below this, inlining the KB is a **true substitute** for forehear. Above it, retrieval plus forehear wins on latency.
- Prompt caching's TTFT gain shrinks or vanishes when the cache misses. OpenAI's per-machine routing (above about 15 RPM overflow) and implicit caching make hits probabilistic, so p95 TTFT for "KB in prompt" is worse than the median suggests. Retrieval's p95 is bounded differently, by DB and reranker tails.
- Prompt caching is not a substitute at large KB sizes. It is a **complement** that makes the static system-prompt part of a RAG prompt cheap and fast.

### Gaps
- Per-size TTFT curve (500 → 50K tokens) for current models (GPT-5.6+, Claude 5.x, Gemini 3.x): the paper's ablation figures were not extracted, and no other controlled study was found.
- No head-to-head study of answer accuracy for voice support with "KB in prompt" vs RAG.

---

## Q4. In-process vector search latency (FAISS, USearch, LanceDB, sqlite-vec, hnswlib) at about 10k–1M vectors

### Takeaway
At 10k–1M vectors, in-process or embedded search is single-digit to tens of ms (LanceDB p95 about 5 ms at 10k; LanceDB Enterprise P50 25 ms at 1M × 1536d; sqlite-vec brute force about 50 ms at 1M × 768d), and sub-ms for small FAISS indexes (per the earlier notes). This erases the hosted DB stage forehear hides (280 ms), but not embedding (about 135–150 ms via API) or reranking (330–480 ms).

### Cited Findings
- **[vendor]** LanceDB Enterprise: P50 25 ms, P90 26 ms, P99 35 ms on the 1M-vector dbpedia-entities-openai dataset (1536 dims), warmed cache — [LanceDB benchmark docs](https://lancedb.com/docs/enterprise/benchmark)
- **[secondary, open-source harness]** Vector Arena (ChromaDB, LanceDB, Qdrant, FAISS, USearch) baseline at 10,000 vectors and 100 queries: LanceDB single-query p95 about 5.3 ms — [Vector Arena](https://github.com/M4iKZ/Vector-Arena)
- **[secondary, blog]** sqlite-vec is exact brute-force search, so latency grows linearly, reaching about 50 ms at 1M × 768d. Main results are at 10K–100K — [dev.to sqlite vector search](https://dev.to/hypernexus/sqlite-vector-search-the-dependency-free-ai-memory-stack-that-outperforms-pinecone-5d27)
- **[measured, independent maintainer of USearch]** The RetriEval project benchmarks USearch v2.25 vs FAISS v1.12.0 on Wiki 1M up to 100M on a dual-socket Xeon 6. At 100M, FAISS was killed at 9 h while USearch completed. Exact per-query latencies were not extracted — [RetriEval](https://github.com/ashvardanian/RetriEval)
- **[measured]** Local Elasticsearch HNSW median 35.4 ms vs flat 47.6 ms (laptop, n=50) — [arXiv 2511.09545](https://arxiv.org/html/2511.09545v1)

### Inferences
- **Classification: partial substitute.** It removes the DB stage entirely and leaves embedding and reranking. With an in-process embedding model too (for example bge-small, as Upstash suggests), the remaining wait is reranking. forehear's 806→392 ms rerank win still applies.
- For voice KBs in the 10k–1M chunk range, a co-located HNSW index (FAISS, USearch, hnswlib, LanceDB) should be well under 10 ms at 10k–100k. Brute-force sqlite-vec is fine to about 100k and borderline (about 50 ms) at 1M (inferred from the figures above).

### Gaps
- ANN-benchmarks and VectorDBBench per-query latency for FAISS-HNSW, hnswlib and USearch at 1M (e.g. glove-100, sift-128) were not fetched. Most ANN-benchmarks report QPS at recall, not latency.
- No hnswlib-specific numbers collected.

---

## Q5. Serving-side: vLLM automatic prefix caching, SGLang RadixAttention, speculative decoding, and interaction with early retrieval

### Takeaway
Prefix caching cuts TTFT for repeated prefixes (one unsourced data point: 850→320 ms with a 4,096-token shared prompt on a 70B model). It only helps RAG if the retrieved chunks sit in a reused prefix, or with non-prefix reuse (CacheBlend). Speculative decoding (EAGLE-3) speeds *decode* 2–3× in practice (up to 6.5× in the paper) but does not touch TTFT or retrieval. Both are complements. The useful interaction is that forehear's early top-k lets the server **prefill retrieved chunks during the user's speech**, so at end of turn only the user's final words need prefill.

### Cited Findings
- **[secondary, unsourced]** vLLM prefix caching on A100 80GB, Llama 3.1 70B, 4,096-token shared system prompt: TTFT 850→320 ms (about 62%) — [jisaku glossary](https://jisaku.com/glossary/llm-caching-prefix-cache)
- **[secondary]** SGLang claims of 6.4× (no method) and 20–40% lower TTFT on prefix-heavy RAG workloads. At concurrency 1 on Llama 3.3 70B / H100, TTFT p50 was 45 ms (vLLM) vs 42 ms (SGLang), with SGLang p95 5–8% lower. vLLM uses block-hash APC and SGLang a radix tree with arbitrary-boundary sharing — [Spheron vLLM vs SGLang 2026](https://www.spheron.network/blog/vllm-vs-sglang-2026/); [techsy](https://techsy.io/en/blog/vllm-vs-sglang)
- **[secondary]** Moving dynamic content out of the cacheable prefix raised one deployment's prefix-cache hit rate from 7% to 74% — [Spheron](https://www.spheron.network/blog/vllm-vs-sglang-2026/)
- **[measured, paper]** EAGLE-3 speedup up to 6.5× (about 1.4× over EAGLE-2), and 1.38× throughput in SGLang at batch 64 — [EAGLE-3 arXiv 2503.01840](https://arxiv.org/html/2503.01840v3)
- **[vendor/LMSYS]** EAGLE-3 on SGLang with Llama 4 Scout (Vertex AI): 2–3× decode-latency speedup — [LMSYS blog](https://lmsys.org/blog/2025-12-01-eagle3-vertex/)
- **[secondary]** vLLM EAGLE-3: about 2.3× at 1–5 concurrent requests. Gains shrink with batch size, and tail latency can worsen if acceptance rate is not measured — [morphllm](https://www.morphllm.com/vllm-speculative-decoding); [Spheron spec-decoding guide](https://www.spheron.network/blog/speculative-decoding-production-guide/)
- Hosted-API equivalents of pre-filling: Anthropic supports `max_tokens: 0` pre-warm (earlier notes). OpenAI caches are per machine with 128-token block granularity and charge 1.25×/2.5× write fees on GPT-5.6+ — [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching); [agnt5](https://agnt5.com/blog/prompt-caching-benchmark)

### Inferences
- **Interaction with forehear (inferred, untested):** once speculative top-k stabilises before end-of-turn, the agent can send a prefill-only request with [system + history + retrieved chunks]. With vLLM APC or SGLang Radix self-hosted, or a cache pre-warm on hosted APIs, the final request then only prefills the user utterance suffix. That moves both retrieval *and* chunk prefill off the critical path.
- Constraints for that interaction:
  - Chunks must precede the user message in prompt order.
  - A speculation miss wastes a prefill, and on OpenAI/Anthropic it also costs a cache-write premium.
  - OpenAI's per-machine routing makes the hit probabilistic.
- Speculative decoding is **irrelevant to retrieval wait** but complements forehear. It shortens time-to-first-sentence for TTS by speeding decode, which makes retrieval a larger share of the remaining turn latency.

### Gaps
- No primary vLLM or LMSYS benchmark of APC / RadixAttention TTFT on RAG-shaped prompts was fetched. The 850→320 ms and 6.4× figures are unsourced secondary claims.
- No system was found that prefills retrieved chunks during user speech. The combination is unmeasured.

---

## Q6. When is each substitute sufficient on its own, and when does forehear still add value?

### Takeaway
forehear is fully substituted only when (a) the KB fits in roughly ≤5–10K cached tokens, (b) a response cache hits (likely a minority of voice turns), or (c) the entire retrieval path (embed + search, no rerank) is in-process. In every 2026 managed configuration measured here, a hideable wait of about 150–650 ms remains (hosted embed + search, rerank, web search), plus cold-start tails of 0.3–2 s. forehear adds value on top of all of them.

### Cited Findings
- Hosted embed + search: median 155–326 ms and p95 426–629 ms (ElevenLabs) — [ElevenLabs](https://elevenlabs.io/blog/engineering-rag)
- Embedding API median about 135–150 ms; rerank median 330–670 ms by K, with 2.9 s spikes — [arXiv 2511.09545](https://arxiv.org/html/2511.09545v1)
- Cold-start first-query penalties: Pinecone Serverless 271 ms, unpinned Turbopuffer 2,048 ms — [Zilliz VDBBench](https://zilliz.com/blog/vdbbench-adds-cost-aware-benchmarking-for-vector-databases.md)
- Fast web search: about 350–650 ms; slow tiers 1.4–1.9 s — [Parallel.ai/Openbenchmarks](https://parallel.ai/articles/best-web-search-api-for-ai-applications.md); [AIMultiple](https://aimultiple.com/agentic-search)
- Cached 10K-token prompt TTFT improvement only 6–31%; at 50K, 1.7 s TTFT — [arXiv 2601.06007](https://arxiv.org/html/2601.06007v2)
- Cloudflare AI Gateway cache is exact match only — [Cloudflare docs mirror](https://03cfcb76.previews.developers.cloudflare.com/ai-gateway/features/caching/). Portkey semantic cache is limited to 4 or fewer messages — [Portkey docs](https://docs.portkey.ai/docs/product/ai-gateway/cache-simple-and-semantic)

### Inferences
Classification for voice agents (my judgement):

| Substitute | Class | Sufficient alone when… | forehear still adds value when… |
|---|---|---|---|
| Cloudflare AI Gateway cache (exact-match) | Irrelevant | Scripted IVR prompts with byte-identical requests | Always (no hits on ASR text) |
| Portkey / LiteLLM / GPTCache / Upstash / Helicone semantic cache | Substitute on hit; complement overall | Narrow FAQ with high repetition, at a threshold that keeps false hits acceptable | On every miss (likely the majority). Speculative cache lookup on interim transcripts also hides the embedding call the lookup needs |
| Momento (serverless KV) | Complement (storage backend) | Never on its own (no semantic matching found) | Always |
| Managed RAG (Vertex RAG Engine, Bedrock KB, Azure AI Search, Ragie, Vectara, Pinecone Assistant, Contextual AI, LlamaCloud) | Complement (slower backends) | Never: they are the wait | Always. These bundle embed + retrieve + rerank, likely at or above the rerank profile |
| Fast rerankers (Vertex ranking under 100 ms vendor claim, rerank-3-lite 0.23 s, zerank-1 150–314 ms) | Partial substitute for the rerank stage | Small K, low latency budget | Remaining 150–400 ms plus tails |
| Fast web search tiers (Exa Instant, Parallel Turbo, Brave) | Partial substitute for the web profile | Snippets suffice | Still 350–650 ms mean; contents fetch adds more |
| OpenAI / Gemini / Anthropic prompt caching with KB in prompt | True substitute for small KBs; complement otherwise | KB ≲5–10K tokens (inferred) | Larger KBs; also keeps the static prefix cheap under RAG |
| In-process ANN (FAISS, USearch, hnswlib, LanceDB, sqlite-vec) | Partial substitute (DB stage) | In-process embedding and no reranker | Remote embedding (about 140 ms) or any reranker (330 ms and up) |
| Pinned/warm serverless namespaces (Turbopuffer pinned, `hint_cache_warm`) | Partial substitute for cold tails | Warm path already single-digit to tens of ms | Embed + network + rerank remain |
| vLLM APC / SGLang Radix | Complement (prefill stage) | n/a: they don't touch retrieval | Early top-k enables chunk prefill during speech |
| Speculative decoding (EAGLE-3) | Complement (decode stage) | n/a | Retrieval share of latency grows as decode shrinks |

- forehear's strongest 2026 case is reranked or managed-RAG pipelines and first-turn cold starts, where waits are 400 ms to 2 s. Its weakest case is a small static KB (inline it) or a fully local embed + ANN stack without rerank.
- Potential selling point: none of the caches or managed stacks surveyed do anything with *interim* transcripts. Speculative semantic-cache lookup and speculative chunk prefill are both unclaimed niches (no counter-example found).

### Gaps
- No end-to-end voice benchmark compares these substitutes against speculative retrieval on the same pipeline.
- Pricing for gateways (Portkey, Helicone, Cloudflare), managed RAG platforms and reranker per-search costs was mostly not collected within the tool budget.
