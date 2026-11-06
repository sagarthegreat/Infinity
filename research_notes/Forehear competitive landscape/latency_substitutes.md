# Latency Substitutes and Complements for forehear (speculative retrieval on interim transcripts)

Reference point for every comparison below. forehear's own measured numbers (from the brief, not re-verified here): hosted vector DB wait 280 to 76 ms, reranker 806 to 392 ms, at about 3.5 retrieval calls per turn. forehear works *within a turn*: it hides retrieval behind the user's own speech. Everything below is judged against that.

Labels used: **[measured]** = number from a paper or benchmark with stated method; **[vendor]** = vendor or marketing claim; **[secondary]** = aggregator or blog repeating someone else; **[unverified]** = could not trace to a primary source.

Classification key: **SUBSTITUTE** = makes forehear unnecessary in some situation. **COMPLEMENT** = stacks with it. **IRRELEVANT** = acts on a different problem or a different deployment shape.

---

## Q0. What other ways exist to cut or hide retrieval latency? (inventory by category)

### Takeaway
The nearest relative is Salesforce's VoiceAgentRAG. It prefetches *across turns* into a sub-millisecond FAISS cache, so it covers the other half of the timeline from forehear (which works within a turn). Most other techniques either act on a different pipeline stage (LLM prefill, LLM decode, TTS) or speed up the retrieval backend. They stack with speculative retrieval rather than replace it. The exceptions are a KB small enough to sit in a cached prompt, and response-level semantic-cache hits.

### Cited Findings

**Category 4: cross-turn prefetch and memory (closest relatives)**
- VoiceAgentRAG (Salesforce AI Research, arXiv 2603.02206, March 2026). A background "Slow Thinker" LLM predicts 3–5 follow-up topics from the last 6 turns and prefetches top-10 chunks per prediction into an in-memory FAISS IndexFlatIP cache (τ=0.40, TTL 300 s, max 2000 entries, LRU). A foreground "Fast Talker" reads only from the cache. On a miss, it fires a priority retrieval with 2× top-k — [arXiv HTML v2](https://arxiv.org/html/2603.02206v2)
- VoiceAgentRAG latency **[measured]**: Qdrant Cloud (AWS us-west-2) average retrieval 110.4 ms vs cache 0.35 ms (316×). Qdrant per-query range 97–307 ms, with a mean of 120 ms in §3.2 (the paper's two figures are not reconciled). Saves about 110 ms per hit, 16.5 s total across 150 hits. Remote embedding call about 200 ms. LLM generation 500–8000 ms — [arXiv HTML v2](https://arxiv.org/html/2603.02206v2)
- VoiceAgentRAG hit rate **[measured, synthetic]**: 75% overall (150/200), 79% on warm turns. By depth: turns 1–4 58%, turns 5–9 86%, 10–14 78%, 15–19 82%. By scenario: from 95% (feature comparison) down to 55% (mixed rapid-fire) and 45% (existing-customer upgrade). The evaluation uses a synthetic 12-document, 76-chunk "NovaCRM" KB and 200 queries — [arXiv HTML v2](https://arxiv.org/html/2603.02206v2)
- VoiceAgentRAG limitations, as stated by the authors: turn 1 always misses, and the cache is typically warm only by turns 3–4. It needs 3–7 s of inter-turn time, and exchanges under 2 s reduce the benefit. Threshold sensitivity is high (τ=0.55 gives 15% hits, τ=0.30 gives 90% at lower precision). With local FAISS over 76 docs (about 0.1 ms) the gain is negligible. The authors also say LLM generation dominates end-to-end latency, so retrieval savings are "often invisible". The paper does **not** use interim or partial STT transcripts — [arXiv HTML v2](https://arxiv.org/html/2603.02206v2)
- VoiceAgentRAG code is at github.com/SalesforceAIResearch/VoiceAgentRAG, and the paper says it is open source. No license is named in the paper text. A trade write-up headlined it "cuts voice RAG retrieval latency by 316x" — [arXiv HTML v2](https://arxiv.org/html/2603.02206v2); [pulse.bot summary](https://www.pulse.bot/ai/news/salesforce-ai-research-releases-voiceagentrag-a-dual-agent-memory-router-that-cuts-voice-rag-retriev-1c3d901a-1165-4d02-8b81-12e819e35100/)
- Mem0 **[vendor paper]**: p95 search latency 0.200 s. p50 and p95 total latency 0.708 s and 1.440 s, vs 17.117 s p95 for full-context prompting. Graph variant Mem0g: p50 1.091 s, p95 2.590 s — [Mem0 arXiv 2504.19413](https://arxiv.org/pdf/2504.19413)
- Zep/Graphiti **[vendor]**: 87 ms p50 and 155 ms p95 retrieval on LoCoMo, with 94.7% accuracy claimed — [Zep research](https://www.getzep.com/research/). Zep's rebuttal to Mem0 reports a 0.632 s p95 search latency "when configured correctly for concurrent searches" (AWS us-west-2 behind NAT) and disputes Mem0's 65.99% score for Zep — [Zep blog](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/)
- Letta: no published retrieval latency found. A secondary piece reports that a plain-file-plus-grep agent scored 74.0% on LoCoMo vs Mem0's 68.5% **[secondary, paywalled]** — [Towards AI](https://pub.towardsai.net/mem0-vs-zep-vs-letta-a-folder-of-text-files-shouldnt-beat-the-61k-star-memory-layer-9d7e65c5799c)
- Memory layers are retrieval *backends* (Mem0's search alone is about 200 ms p95). None of the sources above describes them prefetching before the user finishes speaking — [Mem0 arXiv](https://arxiv.org/pdf/2504.19413); [Zep research](https://www.getzep.com/research/)

**Category 1: semantic / response caching**
- Redis LangCache is a managed semantic cache on Redis Cloud, also available self-managed, and is described as in preview. Redis claims lookups take "milliseconds" vs hundreds of ms or more for LLM generation **[vendor, no benchmark]**. Its docs' 50% hit-rate example is illustrative, not measured — [Redis LangCache docs](https://redis.io/docs/latest/develop/ai/langcache); [Redis tutorial](https://redis.io/tutorials/semantic-caching-with-redis-langcache/)
- Redis AI Research published a method and repo for measuring LangCache hit ratio and precision on your own data. It warns that thresholds tuned on toy data are "far too aggressive" on real queries — [Redis AI research post](https://redis-ai-research-redis.static.hf.space/posts/evaluating-langcache-on-your-data.html)
- Threshold vs hit rate, from a blog guide **[secondary, unverified method]**: 0.97 gives about 5% hits, 0.93 gives 20–30%, 0.85 gives 35–45% "but risk returning a slightly-off answer". The same guide estimates 3–7% of hits are wrong at those thresholds — [llm-academy.dev](https://llm-academy.dev/gateway/semantic-caching/); [preto.ai](https://preto.ai/blog/semantic-caching-llm/)

**Category 2: RAG-specific caching and serving**
- Proximity (Bergman et al., arXiv 2503.05530, Middleware '25). This is an approximate KV cache in front of the vector DB: key = past query embedding, value = retrieved docs, plus an LSH variant. **[measured]** v1 reports retrieval latency down up to 59% (MMLU) and 70.8% (MedRAG). v3 reports Proximity-LSH on skewed MedRAG cuts DB calls 77.2% and retrieval latency 72.5% "while maintaining test accuracy" — [arXiv 2503.05530 v3](https://arxiv.org/html/2503.05530v3); [v1](https://arxiv.org/html/2503.05530v1)
- RAGCache (arXiv 2404.12457) caches KV states of retrieved docs across requests. Its *speculative pipelining* splits vector search into stages and feeds candidate docs to the LLM early, keeping the output if the final top-k matches. **[measured]** Up to 4× lower TTFT and 2.1× throughput vs vLLM+Faiss — [arXiv 2404.12457](https://arxiv.org/pdf/2404.12457)
- CacheBlend / LMCache (EuroSys '25 best paper) reuses KV cache for *non-prefix* chunks, so retrieved chunks hit cache in any order. **[measured]** TTFT 2.2–3.3× lower and throughput 2.8–5× higher vs full recompute. Its blog headline is 3× TTFT reduction on 2WikiMQA with 512-token chunks. The LMCache README claims 3–10× "delay savings" with vLLM **[vendor]** — [LMCache blog](https://blog.lmcache.ai/2025-03-31-eurosys); [awesomepapers summary](https://awesomepapers.io/large-language-models/publications/yao2024cacheblend)
- TurboRAG (EMNLP 2025) precomputes per-chunk KV caches offline and stitches them with independent attention and reordered RoPE. It requires fine-tuning the model. **[measured]** TTFT up to 9.4× lower (8.6× average) vs conventional RAG — [Underline EMNLP 2025](https://underline.io/lecture/130086-turborag-accelerating-retrieval-augmented-generation-with-precomputed-kv-caches-for-chunked-text)
- TeleRAG (arXiv 2502.20969) uses "lookahead retrieval": it prefetches likely IVF clusters CPU to GPU while the LLM generates. **[measured]** Up to 1.72× lower end-to-end latency (v1), revised to up to 1.53× single-query on an RTX 4090 (v2) — [TeleRAG v2](https://arxiv.org/html/2502.20969v2); [v1](https://arxiv.org/html/2502.20969v1)
- PipeRAG is described by later work as running retrieval in parallel with generation using stale context as the query. TeleRAG is described as using a fixed lookahead window — [arXiv 2605.17989](https://arxiv.org/html/2605.17989v1)
- Predictive Prefetching for RAG (Zhang & Pei, UMass Boston, ICML 2026, arXiv 2605.17989) has three parts: a retrieval predictor, a context monitor, and a query generator. It predicts *when* and *what* to retrieve from "semantic precursors" several tokens before uncertainty peaks, and falls back to synchronous retrieval when prefetch fails. **[measured]** Up to 43.5% lower end-to-end latency and 62.4% better TTFT. Secondary summaries add HotpotQA EM 68.7% vs 69.2% for sync RAG and P95 33% lower (not checked against the paper). The code release is listed as "TBD" — [ICML poster](https://icml.cc/virtual/2026/poster/66231); [arXiv](https://arxiv.org/html/2605.17989v1); [papernotes summary](https://en.papernotes.org/ICML2026/information_retrieval/predictive_prefetching_for_retrieval-augmented_generation/)

**Category 3: faster retrieval infrastructure**
- Qdrant p50 4 ms and p99 25 ms at 1M vectors **[secondary dataset, method unclear]**. A separate open-source matched-recall test gives Qdrant p50 2.6 ms and pgvector p50 3.9 ms. Write-to-visible freshness p50: Redis 2 ms, Weaviate 4 ms, Qdrant 9 ms, Milvus 12 ms, pgvector 14 ms — [salttechno benchmark 2026](https://www.salttechno.ai/datasets/vector-database-performance-benchmark-2026/); [AIMultiple](https://aimultiple.com/open-source-vector-databases)
- Pinecone: p50 about 45 ms and p99 about 96 ms at 600 QPS on 135M vectors in one roundup, vs 8 ms p50 and 45 ms p99 at 10M in another. Scales and loads differ, and the roundups note Pinecone's methodology is thin **[secondary]** — [Firecrawl](https://www.firecrawl.dev/blog/best-vector-databases); [effoma](https://effoma.com/blog/vector-database-performance-benchmark-comparison-2026/)
- Turbopuffer: warm namespace p50 8 ms and p99 35 ms (768-dim, 1M docs) vs **cold** p50 343 ms and p99 554 ms. Namespaces are cached on NVMe after the first query. A `hint_cache_warm` endpoint pre-warms, and is free if already warm or warming — [turbopuffer docs (warm cache)](https://turbopuffer.com/docs/warm-cache); figures repeated at [aitoolsatlas](https://aitoolsatlas.ai/compare/turbopuffer-vs-qdrant)
- Turbopuffer pricing: query prices cut "up to 94%" for the largest namespaces in February 2026 **[secondary]**. A $64/month launch plan is reported by third parties and may be stale — [turbopuffer marketplace docs](https://marketplace.turbopuffer.com/docs/warm-cache); [aitoolsatlas](https://aitoolsatlas.ai/tools/turbopuffer)
- These are mostly *server-side* query times. VoiceAgentRAG's 97–307 ms to Qdrant Cloud shows that network round-trip, not ANN search, dominates hosted retrieval — [VoiceAgentRAG](https://arxiv.org/html/2603.02206v2)

**Category 5: conversation-design tricks**
- Inline preamble: the model speaks a short "let me check" acknowledgment in the same stream *before* the tool call, which avoids a race with a separate filler and adds no latency. This works in Pipecat because its OpenAI LLM service streams text to TTS before running function calls — [protoVoice natural fillers](https://protolabsai.github.io/protoVoice/explanation/natural-fillers.html); [protoVoice pipeline shape](https://protolabsai.github.io/protoVoice/reference/pipeline-shape.html)
- LiveKit closed issue #3030 as "not planned", treating filler as a prompt concern. Pipecat PR #714 (filler) was closed in favor of inline handling — [protoVoice natural fillers](https://protolabsai.github.io/protoVoice/explanation/natural-fillers.html)
- **[measured, single-author blog]** P50 for the model's *decision to call a tool* was about 913 ms, vs about 586 ms for the final answer. The blog recommends a thinking sound or spoken acknowledgment during tool calls — [HF voice agent latency playbook](https://huggingface.co/blog/dvalle08/voice-agent-latency-playbook)
- Pre-recorded filler clips cached in S3 play with no TTS delay, but a loudness mismatch with the live voice was audible. The same author says the idea applies to KB searches — [AWS Builder Center](https://builder.aws.com/content/3KREFKYYAEJuEwaL5XiDMgG1ann/killing-dead-air-how-we-made-a-phone-agent-sound-like-it-is-listening)
- Anthropic prompt caching (current docs): minimum cacheable prefix is 512 tokens on current-generation models (1,024–4,096 on older ones). TTL is 5 min (refreshed free on each use) or 1 h. Writes cost 1.25× (5 min) or 2× (1 h) base input. Reads cost 0.1× base, or 0.05× on Opus 5.5 and Sonnet 5.5. Pre-warming with `max_tokens: 0` removes the first-request miss penalty. The docs give no millisecond latency figures — [Claude prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- Anthropic's 2024 launch claimed up to 85% latency reduction for long prompts. Its 100K-token cached-book example went from 11.5 s to 2.4 s (79%) **[vendor, via secondary coverage]** — [SD Times](https://sdtimes.com/ai/anthropic-introduces-prompt-caching-to-reduce-latency-and-costs); [Maginative](https://www.maginative.com/article/anthropics-new-prompt-caching-feature-can-cut-costs-up-to-90/)
- Mem0 reports full-context prompting at 17.117 s p95 on LoCoMo conversations vs 1.44 s with retrieval (uncached full context) — [Mem0 arXiv](https://arxiv.org/pdf/2504.19413)

**Category 6: faster LLM serving**
- Artificial Analysis-derived data for gpt-oss-120b at 10K input tokens: Groq median TTFT 0.67 s, but time to first *answer* token 4.91 s because of reasoning. Cerebras 1.66 s, Together 3.96 s, SambaNova 4.02 s on the answer-token metric **[secondary citing AA]** — [Fast.io](https://fast.io/resources/fastest-ai-2026/); [costbench](https://costbench.com/best/fastest-llm-inference/)
- Other sources conflict: an editorial claims Groq is under 100 ms TTFT vs Cerebras 80–150 ms, while an April 2025 comparison reported Groq 400–600 ms vs Cerebras 1.2–1.8 s on Llama 3.1 70B. These are not reconcilable **[secondary]** — [tooldirectory.ai](https://tooldirectory.ai/compare/cerebras-ai-training-wafer-scale-technology-vs-groq-ultra-fast-ai-language-processing); [DeployBase](https://deploybase.ai/articles/groq-vs-cerebras-pricing-speed-and-benchmark-comparison)

### Inferences
- Per-item classification (my judgement, using the findings above):

| Technique | Class | Why |
|---|---|---|
| VoiceAgentRAG (cross-turn prefetch) | Partial substitute / strong complement | It covers warm turns with slow cadence. It misses turn 1, early turns (58% hit), rapid exchanges, and topic jumps, which are exactly where interim-transcript speculation helps. The two can share one cache. |
| Mem0 / Zep / Letta / Cognee memory | Complement (backend) | These are slow-ish retrieval targets (155–632 ms p95). forehear can call them speculatively like any retriever. |
| Response-level semantic cache (LangCache, GPTCache, gateways) | Substitute on hits; complement overall | A hit skips retrieval *and* the LLM. On a miss (most support traffic, per Q2) forehear still applies. |
| Proximity (approximate retrieval cache) | Complement | It dedupes forehear's ~3.5 near-duplicate interim queries per turn into cache hits. |
| RAGCache / CacheBlend / LMCache / TurboRAG / vLLM APC / SGLang Radix | Complement (different stage) | These cut LLM prefill on retrieved chunks. Retrieving early means chunk KV can be prefilled while the user is still talking. |
| TeleRAG / PipeRAG / Predictive Prefetching | Mostly irrelevant to hosted voice stacks; complement in self-hosted | These overlap retrieval with *generation* (multi-hop, long outputs). Voice turns are short, single retrievals before generation. |
| In-process / edge vector search (FAISS, LanceDB, sqlite-vec, USearch, warm Turbopuffer) | Partial substitute (vector-DB stage only) | It shrinks DB wait to single-digit ms, so forehear's 280 to 76 ms win disappears for that stage. Remote embedding (~200 ms) and reranking (806 ms) remain. |
| KB in cached system prompt | True substitute for small KBs | Retrieval disappears. |
| Filler / preamble utterances | Complement (perceptual) | Filler masks the delay without removing it, and it costs naturalness. Speculation makes the filler shorter or unnecessary. |
| Fast LLM serving | Complement (raises forehear's relative value) | As LLM time shrinks, retrieval becomes a larger share of the turn. |

- VoiceAgentRAG's authors concede that LLM generation dominates end-to-end time. forehear's 806 to 392 ms reranker saving is larger than VoiceAgentRAG's ~110 ms per-hit saving, because reranking is not cached by VoiceAgentRAG at all. Its cache returns raw chunks matched at τ=0.40.

### Gaps
- GPTCache (Zilliz): stars, license (MIT per prior knowledge), and any published hit-rate or latency numbers were not retrieved. One search returned nothing on it.
- Portkey, Helicone, LiteLLM, Upstash semantic cache, Momento, and Cloudflare AI Gateway caching were not researched within the tool budget. No pricing or latency numbers were collected. Cloudflare AI Gateway caching is believed to be exact-match only, not semantic, but this is unverified.
- vLLM automatic prefix caching and SGLang RadixAttention: no numbers fetched. Both are known to cache shared-prefix KV, which helps system-prompt and history reuse in multi-turn voice, but no sourced figures are included.
- PipeRAG's own paper was not fetched. Only a third-party description is included.
- Managed RAG APIs (Ragie, Vectara, Pinecone Assistant, Cohere, Contextual AI, LlamaCloud): no latency figures collected.
- LanceDB, sqlite-vec, FAISS, and USearch in-process benchmarks, ANN-benchmarks, and VectorDBBench were not fetched. The hosted-vs-local contrast rests on VoiceAgentRAG's single local FAISS figure (~0.1 ms over 76 docs).
- Cognee and Letta latency: none found.
- OpenAI and Gemini prompt/context caching specifics (thresholds, TTL, discount) were not fetched.
- Speculative decoding numbers were not collected.
- Adoption metrics (GitHub stars, downloads, customers) were not collected for most projects. The LMCache star count found (623) is from a stale mirror and should not be used.

---

## Q1. Which of these are true substitutes, and in which situations?

### Takeaway
forehear is fully substituted in three situations: (a) the KB is small enough to live in a cached system prompt, (b) the answer comes from a response-level semantic-cache hit, which skips retrieval and the LLM, and (c) retrieval is already in-process and reranking is not used. Cross-turn prefetch (VoiceAgentRAG) substitutes only on warm, slow-cadence, on-topic turns. It explicitly fails on turn 1, rapid exchanges, and topic jumps, so it is a partial substitute.

### Cited Findings
- Prompt caching makes "KB in context" cheap to repeat: 0.1× (or 0.05×) read price, 512-token minimum, 5 min or 1 h TTL, and pre-warming to avoid the first-turn miss — [Claude prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- Even cached, very large contexts stay slow for voice: the 100K-token cached-book example still took 2.4 s **[vendor 2024]** — [SD Times](https://sdtimes.com/ai/anthropic-introduces-prompt-caching-to-reduce-latency-and-costs). Uncached full-context conversation memory reached 17.1 s p95 — [Mem0 arXiv](https://arxiv.org/pdf/2504.19413)
- Local FAISS search over a small KB takes about 0.1 ms, which VoiceAgentRAG's authors call a negligible gain from caching. The retrieval-latency problem only exists for networked DBs (97–307 ms measured) — [VoiceAgentRAG](https://arxiv.org/html/2603.02206v2)
- Warm Turbopuffer gives 8 ms p50 vs 343 ms cold. Pre-warming via `hint_cache_warm` (for example at call start) removes most of the hosted-DB wait — [turbopuffer docs](https://turbopuffer.com/docs/warm-cache)
- VoiceAgentRAG fails where forehear operates: turn 1 always misses, turns 1–4 hit only 58%, inter-turn gaps under 2 s reduce the benefit, and the mixed rapid-fire scenario hits 55% — [VoiceAgentRAG](https://arxiv.org/html/2603.02206v2)

### Inferences
- The small-KB substitute threshold is uncertain. A 2.4 s TTFT at 100K cached tokens is too slow for voice. KBs of a few thousand to perhaps ~20–30K tokens are probably the practical ceiling for "put it all in the prompt", but this is not directly measured; teams should measure TTFT for their model. Below that, forehear adds complexity for no gain.
- An in-process vector index is only a partial substitute for forehear. It removes the 280 to 76 ms DB stage. If the pipeline also calls a remote embedding API (~200 ms per VoiceAgentRAG) or a cross-encoder reranker (forehear measured 806 ms), speculation still hides those.
- Semantic-cache substitution is per-turn, not per-deployment. It replaces forehear only on the fraction of turns that hit, which is likely a minority in support traffic (see Q2).
- Fast LLM serving is never a substitute. It removes a *different* stage and makes retrieval proportionally more visible.

### Gaps
- No source directly measured TTFT vs cached-prefix size on current models (Claude 5.x, GPT-5.x, Gemini 3.x) for voice-sized outputs. The 2.4 s figure is from 2024 models.
- No measured comparison of "KB in prompt" vs RAG answer accuracy for voice support KBs was found.

---

## Q2. Which complement forehear and could be combined?

### Takeaway
Most of the landscape stacks with forehear. The best combinations are: a semantic or approximate retrieval cache (Proximity-style) that dedupes forehear's repeated interim queries; cross-turn prefetch (VoiceAgentRAG) filling the same cache between turns; KV-cache reuse for retrieved chunks (CacheBlend/LMCache, TurboRAG, RAGCache), prefilled while the user is still speaking; cache pre-warming on serverless vector DBs; and spoken preambles as a fallback when speculation misses.

### Cited Findings
- Proximity's approximate query-embedding cache cuts retrieval latency 59–72.5% and DB calls 77.2% on skewed workloads. The paper says accuracy was maintained — [arXiv 2503.05530 v3](https://arxiv.org/html/2503.05530v3)
- VoiceAgentRAG already implements "cache-on-miss" plus background prefetch into one FAISS cache, with sub-ms lookups — [VoiceAgentRAG](https://arxiv.org/html/2603.02206v2)
- RAGCache's speculative pipelining feeds *candidate* docs to the LLM before vector search finishes and keeps the result if top-k matches. This is the same "speculate, then verify" pattern applied at the LLM side, with up to 4× TTFT gain — [arXiv 2404.12457](https://arxiv.org/pdf/2404.12457)
- CacheBlend reuses non-prefix chunk KV caches for 2.2–3.3× lower TTFT — [LMCache blog](https://blog.lmcache.ai/2025-03-31-eurosys). TurboRAG reports 8.6× average TTFT reduction from precomputed chunk KV — [Underline](https://underline.io/lecture/130086-turborag-accelerating-retrieval-augmented-generation-with-precomputed-kv-caches-for-chunked-text)
- Turbopuffer `hint_cache_warm` is free when the namespace is already warm or warming — [turbopuffer docs](https://turbopuffer.com/docs/warm-cache)
- Tool-call decision turns are slow (913 ms P50 vs 586 ms for answers), and the playbook recommends acknowledgments — [HF playbook](https://huggingface.co/blog/dvalle08/voice-agent-latency-playbook). Inline preambles add no latency in Pipecat — [protoVoice](https://protolabsai.github.io/protoVoice/explanation/natural-fillers.html)
- Predictive Prefetching's design falls back to synchronous retrieval on prefetch failure. This is the same safety property speculative retrieval needs — [arXiv 2605.17989](https://arxiv.org/html/2605.17989v1)

### Inferences
- **Semantic cache in front of speculative retrieval:** look up the response cache on *interim* transcripts as well. A hit before end-of-utterance lets the agent start TTS immediately. On a miss, forehear's speculative retrieval is already in flight. Nothing found shows any vendor doing interim-transcript cache lookups, so this is a possible differentiator or integration point.
- **Proximity-style cache under forehear:** about 3.5 calls per turn on successive interim transcripts are highly similar queries, which is the skewed, near-duplicate workload where Proximity reports its best numbers (72.5%). Combining them should cut forehear's extra-call cost (DB QPS, reranker spend), which is likely its main objection.
- **VoiceAgentRAG plus forehear:** they cover disjoint time windows (between turns vs during the user's speech) and could write to the same cache. forehear covers turn 1 and rapid or topic-shifting turns where VoiceAgentRAG hits 45–58%.
- **Early retrieval enables early prefill:** once the speculative top-k stabilizes before end-of-turn, chunk KV (CacheBlend/LMCache) or the full prompt prefix could be prefilled during user speech. This would move LLM prefill off the critical path too. It applies only to self-hosted vLLM/SGLang stacks, not hosted APIs.
- **Tool-call elimination:** if forehear injects context proactively, the agent may skip the model's "decide to call a retrieval tool" round-trip (~913 ms P50 in one measurement). This could be a bigger saving than the DB wait itself, but it is not measured.
- **Fast LLMs (Groq/Cerebras):** when LLM TTFT drops to a few hundred ms, a 280 ms DB wait plus an 806 ms rerank becomes the dominant stage. So fast inference increases forehear's relative value.

### Gaps
- No published system combines interim-transcript speculation with semantic caching or KV prefill. All of the combinations above are untested inferences.
- No measurement was found of how much the tool-call decision step can be removed by proactive context injection.

---

## Q3. What numbers exist for semantic-cache hit rates in voice/support traffic?

### Takeaway
There is no rigorous published hit rate for *voice* traffic. For text support and conversational traffic, the most conservative figures are 10–15% (support chatbot) and 12% (conversational chat), from an IBM/Red Hat-affiliated arXiv paper, but its table is unsourced and illustrative. Vendor and blog figures of 20–60% exist but lack method. The closest voice-specific number is VoiceAgentRAG's 75% *retrieval-chunk* cache hit rate, which is a different kind of cache on a synthetic 76-chunk KB.

### Cited Findings
- Category-aware semantic caching paper (Wang et al., arXiv 2510.26835) gives these hit rates: code generation 55%, API docs 45%, **conversational chat 12%**, **customer support chatbot 10–15%**, financial 8%, legal 10%, medical 6%. It describes the table as "a representative production workload serving 100K queries/hour" but cites no source and has no experimental results. Its break-even figures are internally inconsistent — [arXiv 2510.26835 HTML](https://arxiv.org/html/2510.26835v1)
- The same paper argues head categories reach 40–60% while tail categories reach 5–15%, and that conversational queries show minimal repetition — [arXiv 2510.26835](https://arxiv.org/html/2510.26835v1)
- Blog and vendor claims: "40 to 60% common on mature support deployments" and 25–40% "healthy for support chat" **[secondary, no method]** — [getmaxim.ai](https://www.getmaxim.ai/articles/what-is-semantic-caching-a-technical-deep-dive/); [preto.ai](https://preto.ai/blog/semantic-caching-llm/); [getnadir.com (30–50% of calls)](https://getnadir.com/blog/semantic-caching-llm-cost-reduction/)
- Hit rate depends on threshold: about 5% at 0.97, 20–30% at 0.93, 35–45% at 0.85, with an estimated 3–7% wrong hits **[secondary]** — [llm-academy.dev](https://llm-academy.dev/gateway/semantic-caching/)
- One source warns that hits concentrate on cheap, short requests, so the savings are smaller than the hit rate implies — [respan.ai](https://www.respan.ai/articles/semantic-cache-llm)
- Redis LangCache publishes only an illustrative 50% and recommends measuring hit ratio and precision on your own data — [Redis docs](https://redis.io/docs/latest/develop/ai/langcache); [Redis AI research](https://redis-ai-research-redis.static.hf.space/posts/evaluating-langcache-on-your-data.html)
- Voice-adjacent: VoiceAgentRAG chunk-cache hit rate is 75% overall, ranging from 45% to 95% by scenario. This is a synthetic benchmark and caches retrieved chunks, not responses — [VoiceAgentRAG](https://arxiv.org/html/2603.02206v2)

### Inferences
- Voice transcripts are noisier than typed queries (disfluencies, ASR errors, longer phrasing). Response-cache hit rates for voice are therefore plausibly *at or below* the 10–15% text-support figure at safe thresholds. This is unmeasured and should be flagged as such.
- At realistic 10–30% response-cache hit rates, 70–90% of turns still need retrieval. A semantic cache is therefore a complement to forehear for most deployments, not a replacement. The exception is narrow FAQ or IVR-style flows.
- Chunk-level caches (VoiceAgentRAG, Proximity) hit far more often (59–86% in their benchmarks) than response-level caches, because a chunk is reused across differently-worded questions. This favours chunk or retrieval caching as the layer to pair with forehear.

### Gaps
- No public, measured semantic-cache hit rate on real voice-agent or call-center traffic was found, from Vapi, Retell, LiveKit, Pipecat/Daily, Deepgram, or any cache vendor.
- GPTCache's own published hit-rate numbers were not retrieved.
- No source measured the wrong-answer rate of semantic caches on spoken (ASR) input.
