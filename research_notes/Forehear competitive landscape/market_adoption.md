# Forehear: Market Demand, Adoption Channels and Positioning Evidence

Research date: 2026-11-06. Hard numbers (stars, downloads, funding, dated postings) are separated from opinion and vendor claims. Method notes: the `gh api` CLI was blocked for these repos in this session, so star and fork counts come from the ecosyste.ms mirror of GitHub (each repo was last synced between 2026-10-27 and 2026-11-05). PyPI numbers come from the pypistats.org "recent" API, pulled 2026-11-06. Job data comes from the public Ashby and Greenhouse posting APIs, pulled 2026-11-06.

## 1. How big and fast-growing is the voice-AI agent developer market in 2026?

### Takeaway
Analyst estimates put voice-AI agents at roughly $3.3B–5.1B in 2026, and those estimates disagree widely because they define the market differently. The stronger signals are capital and consolidation. ElevenLabs is valued at $11B, Deepgram and LiveKit are each worth over $1B, and Vapi raised $50M. In the 10 days before this research, Deepgram acquired Daily (the maker of Pipecat) and Salesforce agreed to buy Cresta for a reported $2.7B. Developer-framework usage is large and measurable: LiveKit Agents has about 3.6M PyPI downloads a month and Pipecat about 1.0M.

### Cited Findings
**Market size (analyst estimates, low reliability, definitions differ)**
- Estimates for 2026 run from about $3.3B to $5.1B across four research firms. Grand View Research says $3.5B (agent platforms only). Meticulous Research says $5.10B (including speech infrastructure, telephony and testing tools). The spread comes mostly from scope definitions. — [Meticulous Research](https://www.meticulousresearch.com/product/voice-ai-agents-market-6938); [JustCall summary](https://justcall.io/blog/ai-voice-agents-market-and-forecast.html); [Globe Market Research ($113.7B by 2035 forecast)](https://www.globemarketresearch.com/reports/voice-ai-agents-market)

**Funding (hard numbers from announcements, as reported by secondary sources)**
- ElevenLabs raised a $500M Series D at an $11B valuation (Feb 2026). — [AgentVoice market map](https://agentvoice.com/blog/ai-voice-agents-funding-market-map/); [newmarketpitch](https://newmarketpitch.com/blogs/news/ai-voice-agents-top-startups-fundraising)
- Deepgram raised a $130M Series C at a $1.3B valuation (Jan 2026). — [AgentVoice](https://agentvoice.com/blog/ai-voice-agents-funding-market-map/); TechCrunch also confirms Deepgram "reached unicorn status earlier in 2026 with a $130 million Series C" — [TechCrunch, 2026-10-29](https://techcrunch.com/2026/10/29/deepgram-acquires-pipecat-maker-daily-to-bolster-its-voice-ai-infrastructure/)
- LiveKit raised a $100M Series C at a $1B valuation (Jan 2026), for about $174M raised in total according to one secondary source. — [micdrop.dev](https://micdrop.dev/blog/livekit-pricing); [Evalgent](https://www.evalgent.com/blog/livekit-vs-pipecat-vs-dograh)
- Vapi raised a $50M Series B led by Peak XV (May 2026), bringing its total to $72M. The company claims 10x enterprise revenue growth in the prior year and over 1 billion calls handled (company claim). — [newmarketpitch](https://newmarketpitch.com/blogs/news/ai-voice-agents-funding-news)
- Quarterly voice-agent investment fell from $514.1M (Q1 2026) to $336.5M (Q2) and $272.3M (Q3), with deal counts of 20, 15 and 12. The "development platforms" category had 8 deals worth $134.5M in 2026, versus 5 deals worth $66.0M in 2025. Caveat: this is a secondary aggregator with formatting errors, and its trackers disagree with each other. — [newmarketpitch quarterly](https://newmarketpitch.com/blogs/news/ai-voice-agents-funding-deals)

**Consolidation (Oct–Nov 2026)**
- Deepgram announced its acquisition of Daily, maker of Pipecat, on 2026-10-29. The price was not disclosed. Daily had raised more than $62M (PitchBook). Deepgram committed to keeping Pipecat open source. Kwindla Kramer (Daily): "Scott was super committed to Pipecat being open source and vendor-neutral forever." Deepgram also launched the **Real-Time Context Standard (RCS)**, an open protocol co-developed with the Pipecat team. — [TechCrunch, 2026-10-29](https://techcrunch.com/2026/10/29/deepgram-acquires-pipecat-maker-daily-to-bolster-its-voice-ai-infrastructure/); [The AI Insider, 2026-11-02](https://theaiinsider.tech/2026/11/02/deepgram-acquires-daily-maker-of-open-source-voice-ai-framework-pipecat/)
- Salesforce agreed to acquire Cresta (voice agents, agent assist and analytics). The reported price of about $2.7B is not confirmed by Salesforce. — [Dataconomy, 2026-11-03](https://dataconomy.com/2026/11/03/salesforce-agrees-to-acquire-voice-ai-firm-cresta/); [runtimewire](https://runtimewire.com/article/salesforce-acquire-cresta-2-7-billion-voice-agents-service-cloud)
- Other 2026 deals:
  - Aircall acquired Vogent (2026-05-06).
  - Nurix agreed to acquire Verloop.io (2026-07-09).
  - OVHcloud acquired Gladia (2026-07-31). Sources conflict on whether this deal has closed.
  - Google DeepMind acqui-hired Hume (Jan 2026).
  — [Aircall](https://aircall.io/blog/news/aircall-vogent/); [Tracxn](https://tracxn.com/d/sectors/voice-ai/__ooDO2Zv7I7Lr6Wb6_VbfEVpA8rhLHYzpKzl-EEZFlGw)

**Developer-usage proxies (hard numbers, PyPI recent downloads, pulled 2026-11-06)**
| Package | Last day | Last week | Last month |
|---|---|---|---|
| livekit-agents | 218,730 | 1,236,823 | 3,609,910 |
| deepgram-sdk | 167,126 | 917,348 | 3,166,523 |
| livekit-plugins-silero | 174,270 | 970,046 | 2,538,031 |
| silero-vad | 94,781 | 490,426 | 2,007,798 |
| livekit-plugins-turn-detector | 55,879 | 311,717 | 1,184,906 |
| pipecat-ai | 61,321 | 374,140 | 1,043,553 |
| kokoro | 20,807 | 131,356 | 299,596 |
| useful-moonshine-onnx | 516 | 3,986 | 39,401 |
| vocode | 21 | 131 | 890 |
— [pypistats.org API](https://pypistats.org/api/packages/livekit-agents/recent) (the same endpoint pattern was used for each package)

**Demand-side survey signal (weak)**
- A Censuswide survey of 700 leaders and consumers, cited by a vendor, found that 55% of consumers use voice as their primary AI interface, while only 29% of companies have deployed customer-facing voice AI. — [Maven AGI](https://www.mavenagi.com/resources/the-channel-most-enterprises-still-havent-automated-voice)

### Inferences
- Taken together, the PyPI numbers suggest that tens of thousands of developers and CI pipelines install voice-agent frameworks every day. CI inflates download counts, so these are an upper bound on human users. LiveKit Agents' download volume is about 3.5x Pipecat's, even though Pipecat has slightly more GitHub stars.
- The Deepgram–Daily deal changes partnership dynamics. Pipecat now belongs to an STT vendor, and Deepgram just launched an open "real-time context" protocol with the Pipecat team. Interim-transcript retrieval is a natural consumer of streaming-STT partials and a natural fit for an RCS-style context layer. That makes Deepgram/Pipecat both the most aligned partner and the party most likely to build this feature themselves.
- The vocode collapse (890 downloads a month despite 3.8k stars) shows that stars without integration into a dominant framework do not convert into usage.

### Gaps
- No primary analyst report (Gartner, Forrester, a16z, Menlo, CB Insights) was retrieved directly. Market sizes come from commercial research firms and vendor blogs.
- I found no public Discord member counts for Pipecat or LiveKit.
- I did not verify the RCS protocol's scope (whether it covers retrieval or context injection), and it should be checked.

## 2. How much do developers complain about RAG/knowledge-base latency? Is it a top-3 pain?

### Takeaway
Retrieval latency is a real, documented pain. Salesforce AI Research published a paper and repo on exactly this problem, and practitioners recommend avoiding knowledge bases in voice agents because of it. However, the public evidence does not support calling it a top-3 pain overall. Developer threads concentrate on end-of-turn detection, LLM time-to-first-token (TTFT), TTS and telephony overhead. Retrieval shows up mainly as part of "tool-call turns", which measurably add 0.7–1+ s. I found no survey that ranks RAG latency against other components.

### Cited Findings
**Direct evidence that retrieval latency is recognized as a bottleneck**
- Salesforce AI Research's VoiceAgentRAG paper (arXiv 2603.02206, March 2026) frames the retrieval step as incompatible with real-time voice. Its repo describes a 200ms+ vector-DB lookup as over budget. Its fix is a background "slow thinker" agent that prefetches likely context into a cache, reporting a 75% cache hit rate and 110 ms → 0.35 ms retrieval (a claimed 316x speedup). The benchmark is a single setup: 200 queries, 10 scenarios, Qdrant Cloud. The repo had **158 stars** (created 2026-03-02). — [arXiv](https://arxiv.org/html/2603.02206v1); [GitHub](https://github.com/SalesforceAIResearch/VoiceAgentRAG); stars via ecosyste.ms
- Tazo Labs, "Speculative tool calling: cutting voice AI agent latency" (2026-10-02; posted to HN 2026-10-13 for 3 points and 2 comments):
  - The pattern is to fire likely read-only tool calls while the caller is still speaking and commit them only if the LLM later issues the same call. Their wording: "guess early, check later, throw away what's wrong."
  - Worked example: an 800 ms lookup fired 1.2 s early at a 60% hit rate saves about 480 ms per affected turn, at about 0.67 wasted lookups per useful one.
  - It cites SHANKS ("the model completed 56.9% of tool calls before the user finished their turn").
  - It cites Deepgram reply speculation, which trims "the last 100–200ms ... at the cost of 50–70% more LLM calls".
  - It warns that acting on raw partials can fire on wrong values (for example, an order number) and recommends waiting for stable interim transcripts (citing NVIDIA voice-agent-examples). It also flags a privacy risk: speculation can "leak inferred user intent to external services".
  — [Tazo Labs blog](https://tazolabs.com/blog/speculative-tool-calling-voice-ai); [HN](https://news.ycombinator.com/item?id=50069985)
- LiveKit Agents issue #3824, "How to measure latency properly?" (opened 2025-11-07 by marctorsoc), measured silence in Audacity and Langfuse:
  - Tool-call turn: 3.3 s of silence (EOU 1.347 s, LLM TTFT 2.36 s, TTS 0.28 s).
  - Normal turn: 2.6 s (EOU 1.00 s, TTFT 1.07 s, TTS 0.25 s).
  - LiveKit's documented formula did not match the measured silence. A maintainer pointed to the new `MetricsReport` e2e latency metric. The issue was closed "not planned" by a bot on 2026-09-10.
  — [GitHub issue](https://github.com/livekit/agents/issues/3824)
- A third-party LiveKit testing guide says custom RAG placed in `on_user_turn_completed` shows up in `on_user_turn_completed_delay`: "that is where RAG latency hides". It warns that synchronous DB calls in that hook block the turn. — [Evalgent LiveKit testing guide](https://www.evalgent.com/blog/livekit-voice-agent-testing-guide)
- A practitioner Medium post, "Lessons from implementing RAG in a real-time voice agent (LiveKit)", flags that the retrieval step adds latency that matters for real-time voice. — [Medium, Jorge Jarne](https://medium.com/@jorge.jarne/lessons-from-implementing-rag-in-a-real-time-voice-agent-livekit-43f0689bf565)
- Vendor and blog claims (unverified):
  - A healthcare client cut RAG latency from 1200 ms to 350 ms using hierarchical chunks and local caching.
  - A well-structured KB adds about 50 ms, and a poorly structured one 300 ms+.
  - Production voice deployments keep retrieval under 300 ms total using a fast vector store plus a small reranker.
  — [growwstacks](https://growwstacks.com/blog/voice-agent-latency-issues-and-fixes); [optimizesmart](https://optimizesmart.com/blog/voice-ai-knowledge-base-creation-best-practices/); [futureagi](https://futureagi.com/blog/how-to-build-rag-powered-voice-ai-agents-2026/)
- Platform anecdote: after Trieve was sunset, Vapi users reported on Discord that the suggested KB replacement performs worse on both latency and accuracy. This is third-party hearsay. — [CloudTalk Retell vs Vapi](https://www.cloudtalk.io/retell-ai-vs-vapi-ai/)
- A Retell blog post (a competitor source) says Voiceflow's knowledge-base calls degrade latency. — [Retell blog](https://www.retellai.com/blog/vapi-vs-voiceflow)
- A non-voice example: the AgentDesk repo issue #7 reports retrieval latency rising from about 0.1 s to 1.2–1.5 s after a second LLM selection call was added. — [GitHub](https://github.com/Simar00316/AgentDesk/issues/7)

**Evidence that other components dominate developer attention**
- "Show HN: I built a sub-500ms latency voice agent from scratch" (2026-03-02) got **570 points and 153 comments**, the largest voice-latency HN thread found. The comments focus on endpointing (Deepgram Flux, Soniox), LLM inference providers (Cerebras, Groq), co-location and pipelining. None of the extracted top comments mention retrieval. Notable comments:
  - NickNaraghi: "latency is an orchestration problem (not a model problem)".
  - eru: "The model can have a reasonable good guess of what you are trying to say, and use 'speculative' thinking. Just like CPU's use branch prediction."
  - russdill: "continuously predict the speaker... If the prediction is correct, the response can be started with zero latency."
  — [HN 47224295](https://news.ycombinator.com/item?id=47224295)
- Pipecat #2957: a 4–5 s greeting delay was traced to TTS processing and frame-queue delay, not the LLM. Pipecat #3218: severe latency with multiple participants on LiveKit transport. Neither involves retrieval. — [pipecat#2957](https://github.com/pipecat-ai/pipecat/issues/2957); [pipecat#3218](https://github.com/pipecat-ai/pipecat/issues/3218)
- LiveKit #3685, "Latency doubles in telephony contexts", is again not retrieval-related. — [livekit/agents#3685](https://github.com/livekit/agents/issues/3685)
- Turn detection has drawn dedicated open-source models and benchmarks:
  - Pipecat Smart Turn launched on HN on 2025-03-06 with 126 points.
  - LiveKit's "Solving end-of-turn detection" post (2026-06-20).
  - livekit/eot-bench (2026-06-18).
  - CueLight (2026-10-14).
  — [HN 43283317](https://news.ycombinator.com/item?id=43283317); [HN 48614212](https://news.ycombinator.com/item?id=48614212); [HN 48588475](https://news.ycombinator.com/item?id=48588475); [HN 50089154](https://news.ycombinator.com/item?id=50089154)
- Industry latency baselines (vendor or third-party, unverified):
  - 680 ms p50 and 1,180 ms p95 end-to-end across 10+ deployments.
  - Frontier platforms at about 500–900 ms.
  - An arXiv pipeline (Deepgram + ElevenLabs + LLM) at a P50 time-to-first-audio of 947 ms.
  — [destilabs](https://www.destilabs.com/blog/ai-voice-agent-benchmark-2026); [presenc.ai](https://presenc.ai/research/voice-ai-call-agent-benchmarks-2026); [arXiv 2603.05413](https://arxiv.org/html/2603.05413v1)
- Independent platform tests: Vapi averaged 539 ms (Vapi's own FAQ reportedly says about 800 ms), and Retell averaged 714 ms (Retell claims about 600 ms). — [growwstacks showdown](https://growwstacks.com/blog/voice-ai-showdown-vapi-synthflow-retell-latency-test); [Telnyx](https://telnyx.com/resources/voice-ai-agents-compared-latency)

### Inferences
- Retrieval latency is best described as a **conditional, top-3 pain for the KB- and tool-heavy subset** (customer support, healthcare, order lookups). In those agents, a tool-call turn adds a second inference plus the lookup, and #3824 shows tool turns about 0.7 s slower than normal turns. For the general builder population, it ranks below turn detection, LLM TTFT and TTS/telephony.
- The idea is converging from several directions: CPU branch-prediction analogies on HN, Tazo's speculative tool calling, Salesforce VoiceAgentRAG prefetch, SHANKS, and Deepgram's eager end-of-turn. That convergence validates the problem but means "retrieve before the user stops speaking" is not novel as a concept. Forehear's differentiation has to be the open benchmark, the drop-in Pipecat/LiveKit adapters, and measured hit-rate and wasted-work numbers.
- The two objections Tazo raises (wrong values from unstable partials, and leaking inferred intent to external services) are the ones this audience will raise. A credible launch should report results on stable versus unstable partials and restrict speculation to read-only, local retrieval.

### Gaps
- **No Reddit threads were surfaced** by search (r/AI_Agents, r/LocalLLaMA, r/VoiceAI), and no Pipecat or LiveKit Discord posts. I cannot quote any.
- I found no developer survey that ranks latency components. The "State of Voice AI 2026" results are vendor content with conflicting numbers. — [AInora](https://ainora.lt/blog/state-of-ai-voice-agents-report-2026); [harmony.ai](https://harmony.ai/blog/the-2026-state-of-enterprise-voice-ai-original-data)
- I could not fetch the Evalgent "LiveKit vs Pipecat latency: where the time goes" breakdown (HTTP 429). — [Evalgent](https://www.evalgent.com/blog/livekit-vs-pipecat-latency)
- I could not run GitHub issue searches directly (gh API blocked), so the count of RAG-latency issues in pipecat/livekit is unknown.

## 3. How did comparable open-source voice dev-tools gain adoption?

### Takeaway
Stars in this space cluster at 10k–17k for frameworks and model releases, and at 1–2k for focused components like Smart Turn and TEN VAD. Being bundled as a default plugin in a dominant framework drives usage far more than stars do. LiveKit's turn-detector plugin gets about 1.2M downloads a month and its Silero plugin about 2.5M, while standalone vocode has 3.8k stars and under 1k downloads a month. Successful launches pair an HN "Show HN" with an open model or benchmark plus a framework integration.

### Cited Findings
**Stars and forks (ecosyste.ms mirror, synced 2026-10-27 to 2026-11-05)**
| Repo | Stars | Forks | Created |
|---|---|---|---|
| livekit/livekit | 22,033 | 2,530 | 2020-09-30 |
| pipecat-ai/pipecat | 16,961 | 3,018 | 2023-12-27 |
| livekit/agents | 15,096 | 4,070 | 2023-10-19 |
| huggingface/speech-to-speech | 13,612 | 1,683 | 2024-08-07 |
| kyutai-labs/moshi | 11,346 | 1,050 | 2024-08-07 |
| moonshine-ai/moonshine | 11,304 | 624 | 2024-10-04 |
| TEN-framework/ten-framework | 11,214 | 1,369 | 2024-06-19 |
| snakers4/silero-vad | 10,575 | 879 | 2020-11-23 |
| KoljaB/RealtimeSTT | 10,212 | 863 | 2023-08-29 |
| hexgrad/kokoro | 9,818 | 1,098 | 2025-01-10 |
| dograh-hq/dograh | 6,024 | 1,541 | 2025-09-09 |
| remsky/Kokoro-FastAPI | 5,612 | 937 | 2024-12-30 |
| vocodedev/vocode-core | 3,808 | 655 | 2023-02-24 |
| ufal/whisper_streaming | 3,679 | 411 | 2023-04-05 |
| TEN-framework/ten-vad | 2,298 | 181 | 2025-04-29 |
| pipecat-ai/smart-turn | 1,644 | 110 | 2025-03-05 |
| pipecat-ai/pipecat-flows | 627 | 119 | 2024-11-16 |
| SalesforceAIResearch/VoiceAgentRAG | 158 | 29 | 2026-03-02 |
| livekit/eot-bench | 73 | 12 | 2026-06-09 |
| NVIDIA/voice-agent-examples | 66 | 25 | 2025-04-18 |
— source: [repos.ecosyste.ms API](https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pipecat-ai/pipecat) (the same endpoint pattern was used for each repo). fixie-ai/ultravox was not returned by the mirror.

- A secondary source refers to Pipecat as the "17,000-star Pipecat kit" at the time of the Deepgram acquisition, which matches the mirror's 16,961. — [FourWeekMBA](https://fourweekmba.com/ai-deepgram-buys-daily-maker-of-the-17000-star-pipecat-kit/)

**Launch channels and spread mechanics (observed)**
- Pipecat Smart Turn: "Show HN: Open-source, native audio turn detection model" (2025-03-06) got 126 points and 28 comments, one day after the repo was created. The repo is a first-party Pipecat project. — [HN 43283317](https://news.ycombinator.com/item?id=43283317)
- LiveKit turn detector: launched via the LiveKit blog and HN (8 points for "LiveKit Solves Turn Detection", 2026-06-20) and paired with an open benchmark, eot-bench (73 stars). It still reaches about 1.18M downloads a month as `livekit-plugins-turn-detector`, which suggests distribution through the framework's default templates rather than launch buzz. — [HN 48614212](https://news.ycombinator.com/item?id=48614212); [pypistats](https://pypistats.org/api/packages/livekit-plugins-turn-detector/recent)
- Silero VAD has 10.6k stars, but `livekit-plugins-silero` gets about 2.5M downloads a month and `silero-vad` about 2.0M. It has become the default VAD in frameworks. — [pypistats](https://pypistats.org/api/packages/livekit-plugins-silero/recent)
- Individual Show HN posts for voice-agent side projects usually get under 10 points (Stimm 3, Axiom 2, Dograh 4, CueLight 1). The exception is a deep technical write-up with measured latency (the ntik.me post: 570 points). — HN: [46241699](https://news.ycombinator.com/item?id=46241699), [46926344](https://news.ycombinator.com/item?id=46926344), [47591510](https://news.ycombinator.com/item?id=47591510), [50089154](https://news.ycombinator.com/item?id=50089154), [47224295](https://news.ycombinator.com/item?id=47224295)
- LiveKit maintains a blog roundup, "best open source frameworks for building realtime voice and video AI agents", which is a curation channel. — [LiveKit blog](https://livekit.com/blog/best-open-source-voice-and-video-ai-agent-frameworks)

### Inferences
- The highest-leverage channel is **becoming a plugin or extra referenced by Pipecat and LiveKit docs or templates**, because downloads follow framework defaults. The second is a **write-up with hard, reproducible latency numbers**. HN rewards "here's where every millisecond went" posts far more than product Show HNs.
- Recent latency components that launched with benchmarks (eot-bench, VoiceAgentRAG) gathered fewer than 200 stars. A benchmark alone does not spread. It needs either a dominant-framework sponsor or a viral technical post.
- The realistic star range for a focused component is 1–2k (Smart Turn, TEN VAD) if it is adopted by a framework, and under 200 otherwise.

### Gaps
- I could not access star-history time series (GitHub API blocked), so star growth rates are unavailable. Only point-in-time counts are reported.
- I did not verify the launch histories of Kokoro (HF/TTS Arena), Moonshine or Ultravox. Their spread channels are not sourced here.
- I found no Discord member counts.

## 4. Plausible adopters, partners and acquirers

### Takeaway
The most aligned party is now Deepgram plus Daily/Pipecat. They own a framework and streaming STT, and they just launched an open real-time context protocol. LiveKit is next (Agents framework, turn-detector precedent, $1B valuation). Contact-center consolidators (Salesforce/Cresta, Aircall, Nurix) and agent platforms (Vapi, Retell, Sierra, Decagon) are adopters or acquirers of teams rather than of a library. Salesforce AI Research is simultaneously prior art and a potential collaborator.

### Cited Findings
- Deepgram acquired Daily (Pipecat) on 2026-10-29. Pipecat stays "open source and vendor-neutral", and Deepgram launched the Real-Time Context Standard (RCS) with the Pipecat team. Deepgram's CEO said developers should use the best model for their use case "even if it isn't Deepgram's". — [TechCrunch](https://techcrunch.com/2026/10/29/deepgram-acquires-pipecat-maker-daily-to-bolster-its-voice-ai-infrastructure/)
- LiveKit: $100M Series C at a $1B valuation (Jan 2026). It ships first-party turn-detection models and benchmarks (eot-bench), and it documents "preemptive generation" (cited in the Tazo post). — [micdrop.dev](https://micdrop.dev/blog/livekit-pricing); [HN eot-bench](https://news.ycombinator.com/item?id=48588475); [Tazo Labs](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- Salesforce is acquiring Cresta (reportedly about $2.7B) to add voice agents to Service Cloud. Salesforce AI Research also authored VoiceAgentRAG (prefetch caching for voice RAG). — [runtimewire](https://runtimewire.com/article/salesforce-acquire-cresta-2-7-billion-voice-agents-service-cloud); [GitHub](https://github.com/SalesforceAIResearch/VoiceAgentRAG)
- Other 2026 acquirers in voice: Aircall (Vogent), Nurix (Verloop.io), OVHcloud (Gladia), Google DeepMind (Hume acqui-hire). — [Aircall](https://aircall.io/blog/news/aircall-vogent/); [Tracxn](https://tracxn.com/d/sectors/voice-ai/__ooDO2Zv7I7Lr6Wb6_VbfEVpA8rhLHYzpKzl-EEZFlGw)
- Deepgram Flux exposes `EagerEndOfTurn` and `TurnResumed` events, which are speculation hooks a library like forehear would consume. NVIDIA's voice-agent-examples recommends acting only on stable interim transcripts. — [Tazo Labs](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- Tazo Labs (Kodimo, Inc.) is commercializing speculative tool calling inside its "audio decision model". It is an adjacent commercial competitor. — [Tazo Labs](https://tazolabs.com/blog/speculative-tool-calling-voice-ai)
- Vapi: $72M raised and a claimed 1B+ calls. It has KB-latency complaints after the Trieve sunset (anecdotal). — [newmarketpitch](https://newmarketpitch.com/blogs/news/ai-voice-agents-funding-news); [CloudTalk](https://www.cloudtalk.io/retell-ai-vs-vapi-ai/)

### Inferences
- Partner priority:
  1. Pipecat/Deepgram (an RCS integration, plus interim-transcript retrieval powered by Flux eager-EOT events).
  2. LiveKit Agents (a plugin next to turn-detector, hooked into `on_user_turn_completed` and preemptive generation).
  3. Vector-DB vendors (Qdrant was used in the VoiceAgentRAG benchmark), as co-marketing partners.
- Acquisition of a small Apache-2.0 library is unlikely as a deal in its own right. The realistic outcomes are framework upstreaming, or the project serving as a hiring signal for its author. Both are consistent with Deepgram–Daily and with the DeepMind–Hume acqui-hire pattern.
- Risk: Deepgram/Pipecat or LiveKit could implement interim-transcript prefetch natively, since both already ship eager or preemptive turn primitives. Positioning forehear as the neutral benchmark and reference implementation they can adopt reduces that risk.

### Gaps
- I did not verify whether RCS already includes speculative or interim retrieval semantics.
- I did not verify whether Retell, Vapi, Sierra or Decagon publicly describe interim-transcript prefetch in their stacks.

## 5. What are top voice-AI employers hiring for in 2026 that forehear demonstrates?

### Takeaway
Across these companies, the dominant open role families are **Forward Deployed Engineer / Solutions Engineer**, **Agent platform / agent harness software engineers**, and **research engineers on inference and evals**. Forehear demonstrates the skill set behind real-time pipeline latency optimization, agent-framework integration (Pipecat/LiveKit) and benchmark/eval design, which fits FDE, "Software Engineer, Agents" and "Voice Agent" engine roles directly.

### Cited Findings
These are the open postings returned by public ATS APIs on 2026-11-06, filtered for voice, agent, real-time and research titles. Dates are publishedAt or updated_at. I read titles only, not full job descriptions.
- **LiveKit** (30 open roles):
  - Software Engineer, Agents (2026-08-11) — [link](https://jobs.ashbyhq.com/livekit/1757f49e-7e19-4c45-85f7-e4637dff66fb)
  - Forward Deployed Engineer: NY (2026-03-17), UK (2026-06-29), Ireland (2026-07-08), Spanish/English Miami (2026-08-26) — [NY](https://jobs.ashbyhq.com/livekit/b889ef16-4d5d-4b71-b0a9-682026a0a1ee)
  - Research Engineer (RL) (2026-08-18) — [link](https://jobs.ashbyhq.com/livekit/b0c02c3f-790f-4cd8-960d-220800d35367)
  - Solutions Architect: UK and Germany (Oct 2026) — [UK](https://jobs.ashbyhq.com/livekit/63cec43b-4627-4494-b70d-cb7f8041a4b1)
- **Deepgram** (69 open roles):
  - Backend Software Engineer – Engine Team (Voice Agent) (2026-02-18) — [link](https://jobs.ashbyhq.com/deepgram/7c7064bb-2bf0-4f64-81cc-14afe79a15c1)
  - Research Staff, Voice AI Foundations (US/NL/UK/AU, Aug–Oct 2026) — [link](https://jobs.ashbyhq.com/deepgram/7cf277bc-a192-4007-a77a-fafbf8276a5e)
  - Research Staff, LLMs (2026-08-23) — [link](https://jobs.ashbyhq.com/deepgram/39c2b79b-0269-4711-9354-be5ccf747a98)
  - Staff PM, Agentic Experiences (Former Engineer) (2026-07-29) — [link](https://jobs.ashbyhq.com/deepgram/17f95148-fa1c-4c34-82c8-333589bef789)
- **ElevenLabs** (141 open roles):
  - Forward Deployed Engineer – Software Engineer: SF (2026-10-14), UK and Argentina (2026-10-04) — [SF](https://jobs.ashbyhq.com/elevenlabs/6c4c57c1-ec72-42ba-af3a-eb7aebbde2e6)
  - Research Engineer – Inference (2026-08-28) — [link](https://jobs.ashbyhq.com/elevenlabs/2d7f9a7c-a9e6-4877-bb38-34e4d989054c)
  - Product Marketing – Agents – Government (2026-11-02) — [link](https://jobs.ashbyhq.com/elevenlabs/33bb01d0-993c-47fa-ae91-81c0c84f367e)
- **Cartesia** (24 open roles):
  - Software Engineer, Agent Harness (2026-05-15) — [link](https://jobs.ashbyhq.com/cartesia/16cd6cd7-454b-4e44-9a04-6a4677a3e920)
  - Researcher, Evals (2025-10-21) — [link](https://jobs.ashbyhq.com/cartesia/53fb0b93-d49d-47c7-a679-35ee76b007c5)
- **Decagon** (132 open roles, 60 matched):
  - Staff Software Engineer, Voice Agent (2025-12-01) — [link](https://jobs.ashbyhq.com/decagon/2351ca53-b7fd-4835-b967-4ae2b976b5b4)
  - Engineering Manager, Agent Orchestration (2026-02-10) — [link](https://jobs.ashbyhq.com/decagon/b295b323-3d01-4126-94c1-9fc7489ebdf0)
  - Software Engineer, Agents (London, 2026-05-06) — [link](https://jobs.ashbyhq.com/decagon/28366d07-ae89-428c-8593-1840591bfc18)
- **Sierra** (216 open roles, 79 matched):
  - Research Engineer, Applied Research (2026-10-05) — [link](https://jobs.ashbyhq.com/sierra/ddae4a0c-2f6c-4cc3-80aa-da74a0dd667a)
  - Many "Software Engineer, Agent" and "Agent Development" roles — [link](https://jobs.ashbyhq.com/sierra/e9f5fdb6-91ee-4c55-9230-41ec8865650e)
- **AssemblyAI** (17 open roles):
  - Software Engineer, Agent Experience (2026-10-16) — [link](https://job-boards.greenhouse.io/assemblyai/jobs/4744387005)
  - Forward Deployed Engineer, Triage (NYC/SF/SG, 2026-10-30) — [link](https://job-boards.greenhouse.io/assemblyai/jobs/4747340005)
- **Vapi** (5 open roles): Solutions Engineer, SF (2026-10-22) and NY (2026-10-27) — [link](https://jobs.ashbyhq.com/vapi/0ac869b1-0697-479d-a22b-17a5e160ffe5)
- **Speechmatics** (13 open roles): Solutions Engineer, Mexico City and Belgrade (Sep 2026) — [link](https://job-boards.eu.greenhouse.io/speechmatics/jobs/4989838101)
- **OpenAI** (822 open roles): Forward Deployed Software Engineer, Manager of FDE NYC (2026-09-23), and Agent Infrastructure SWE — [link](https://jobs.ashbyhq.com/openai/5bbc43df-558a-4e4b-a0cf-83f185c664d7)
- **Outside the target list:** a ServiceNow Senior Staff SWE, Voice AI Agent Prompting posting asks for experience handling "latency, cost, and failure modes unique to a live audio channel" and lists real-time latency optimization. — [ServiceNow](https://careers.servicenow.com/jobs/744000159735140/senior-staff-software-engineer_voice-ai-agent-prompting/)

### Inferences
- Forehear maps best onto these roles:
  - FDE/Solutions roles at LiveKit, ElevenLabs, AssemblyAI and Vapi (customer latency debugging on Pipecat/LiveKit).
  - "Voice Agent" and "Agent Harness/Orchestration" engineering at Deepgram, Cartesia and Decagon (pipeline-level speculation).
  - Evals research at Cartesia and Sierra (the benchmark component).
- A reproducible benchmark with p50/p95 latency savings, hit rate and wasted-compute cost is the artifact most legible to these hiring managers, since multiple postings and platforms emphasize measured end-to-end latency.

### Gaps
- The Greenhouse/Ashby boards for Daily, PolyAI, Retell and Google DeepMind returned no matching postings. PolyAI returned 3 roles, none matched. The others likely use different board slugs or ATS providers, so their hiring is uncovered here.
- Full job descriptions were not fetched, so specific requirements (for example "RAG", "streaming ASR", "Pipecat") are unconfirmed for each posting.

## Positioning implications (synthesized from the sections above)

### Takeaway
The most credible claims are narrow and measured: milliseconds saved on tool/KB turns at a stated hit rate and wasted-work ratio, on an open benchmark, with drop-in Pipecat and LiveKit adapters. Overclaiming general "voice latency" wins would be weak, because the audience sees turn detection and LLM TTFT as the dominant costs.

### Cited Findings
- The comparable figures this audience already sees:
  - VoiceAgentRAG: 75% hit rate, 316x retrieval speedup.
  - Tazo: about 480 ms per affected turn at 60% hit rate, about 0.67 wasted lookups per useful one.
  - SHANKS: 56.9% of tool calls completed before the user finished speaking.
  - Deepgram eager-EOT: 100–200 ms saved for 50–70% more LLM calls.
  — [Tazo Labs](https://tazolabs.com/blog/speculative-tool-calling-voice-ai); [VoiceAgentRAG](https://github.com/SalesforceAIResearch/VoiceAgentRAG)
- HN readers rewarded a per-stage latency teardown with 570 points, and commenters framed latency as "an orchestration problem (not a model problem)". — [HN 47224295](https://news.ycombinator.com/item?id=47224295)
- Developers want trustworthy per-component latency attribution, and tool-call turns are where measured silence diverges most from the documented formulas. — [livekit/agents#3824](https://github.com/livekit/agents/issues/3824)

### Inferences
- Suggested headline framing: "Cut X ms off knowledge-base turns in Pipecat/LiveKit by retrieving on stable interim transcripts. Open benchmark, reported hit rate and wasted queries." Avoid claiming novelty for the speculation idea. Cite VoiceAgentRAG, Tazo and SHANKS as related work, and differentiate on being framework-native, open and benchmarked.
- Address the known objections up front: unstable partials (wrong entity values), privacy (no external calls on speculative branches), and compute overhead.

### Gaps
- No user research or survey quantifies willingness to adopt a retrieval-speculation library. Demand here is inferred from adjacent signals.
