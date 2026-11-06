# Commercial Voice-AI Platforms and Contact-Center Products as Competitors/Substitutes for forehear (as of Nov 6, 2026)

Method note: This builds on the earlier notes at `docs/research/notes/commercial_platforms.md` (Nov 3, 2026). Those findings were re-checked where possible and the gaps were filled. Marking conventions:
- **(verified)**: the primary page was fetched this session.
- **(snippet)**: rests on a search-result summary of a primary page.
- **(third-party)** or **(competitor)**: not the vendor's own words.
- **Documented**: describes product behaviour in docs or API references.
- **Marketing**: a product-page or blog claim.

Tool budget was limited (about 40 calls). Several platforms still have thin primary coverage, and these are listed under Gaps.

## Q1. Does ANY platform advertise retrieval that starts before the user finishes speaking?

### Takeaway
No commercial voice-agent platform found advertises knowledge-base retrieval that starts before the user finishes speaking, i.e. on interim or partial transcripts, as a product feature.

The closest documented items fall into three groups:
- **Speculative LLM generation, not retrieval:**
  - ElevenLabs `speculativeTurn` speculates on "LLM responses during silence".
  - Deepgram Flux `EagerEndOfTurn` is the one primary source that explicitly recommends eager processing for RAG pipelines.
- **Speculative or parallel runtime language from Sierra:** "parallel and speculatively", "predictive prefetching". This is keyed on session context, such as a known caller, not on partial speech.
- **Raw partial-turn access for developers:** Twilio ConversationRelay `partialPrompts`, and Retell `update_only` live-transcript events. A developer, or forehear, could build speculative retrieval on top of these, but the vendors do not do it themselves.

Contact-center agent assist (Google PGKA, Genesys, NICE, Cresta) retrieves "as the customer speaks" in marketing language. Google's docs, however, show triggering per finalized message or utterance.

### Cited Findings

**Closest to "retrieval before end of speech": Deepgram Flux**
- Deepgram's eager end-of-turn guide says eager processing is most valuable for pipelines with "complex RAG (Retrieval-Augmented Generation) or Function Calling" — [Deepgram eager EOT guide (llms.txt)](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- On `EagerEndOfTurn` you start a draft. On `TurnResumed` you discard it. "The transcript in EagerEndOfTurn will exactly match the transcript in the subsequent EndOfTurn event (if no TurnResumed occurs)" — [Deepgram eager EOT guide](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- Stated benefit: it can "cut hundreds of milliseconds", or trims "that last 100-200ms". Stated cost: "50-70% more LLM calls" — [Deepgram eager EOT guide](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- This is developer guidance for Flux STT users. It is not a hosted retrieval feature.

**ElevenLabs Agents Platform: speculation covers the LLM only**
- SDK `TurnConfig.speculativeTurn`: "When enabled, starts generating LLM responses during silence before full turn confidence is reached, reducing perceived latency. May increase LLM costs." — [ElevenLabs JS SDK TurnConfig.d.ts v2.39.0](https://cdn.jsdelivr.net/npm/@elevenlabs/elevenlabs-js@2.39.0/api/types/TurnConfig.d.ts)
- `turnEagerness` takes Low, Standard or High — same source.
- The current RAG docs make no mention of speculative or preemptive retrieval. Retrieval modes are "Every turn", "On demand" or "Prompt only" — [ElevenLabs RAG docs](https://elevenlabs.io/docs/agents-platform/customization/knowledge-base/rag) (verified)
- ElevenLabs' RAG engineering blog (Sep 12, 2025, updated Sep 8, 2026) says RAG "runs on every query" in the request pipeline. It does not describe starting retrieval before the user finishes — [ElevenLabs: How we engineered RAG to be 50% faster](https://elevenlabs.io/blog/engineering-rag) (verified)

**Sierra: speculative and parallel runtime, keyed on context rather than partial speech**
- Exact quotes:
  - "Running agent tasks in parallel and speculatively (rather than sequentially) keeps the pipeline fast"
  - "Independent tasks — abuse detection, retrieval, API calls — run in parallel, synchronizing only when dependencies require it"
  - "Predictive prefetching ... The runtime precomputes the likely next steps." Example: "When a known customer calls, their order data loads immediately so 'Where's my package?' can be answered instantly."

  Source: [Sierra blog: Engineering low-latency voice agents (Oct 9, 2025; Wenqi Shao and Danny Lee)](https://sierra.ai/blog/voice-latency) (verified)
- The post does not say retrieval starts on partial user speech. Its VAD claim is: "predicts speech completion earlier and more accurately than off-the-shelf alternatives ... cutting reaction lag by hundreds of milliseconds" — [Sierra blog](https://sierra.ai/blog/voice-latency) (verified)
- A secondary summary of a Sierra talk says: "The agent might begin retrieving knowledge from a database simultaneously while a smarter model reasons about whether that retrieval is even necessary... otherwise, the speculative work is discarded" — [ZenML LLMOps database](https://www.zenml.io/llmops-database/building-production-ai-agents-with-advanced-testing-voice-architecture-and-multi-model-orchestration) (secondary). This describes speculation in parallel with decision-making, not speculation on partial speech.

**Twilio ConversationRelay: exposes partial turns, does no retrieval**
- `partialPrompts`: "Sends unfinalized prompts and eager end-of-turn events to the WebSocket, denoted with `last=False`." Default `false` — [Twilio ConversationRelay noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun) (verified)
- `eotThreshold` (0.5–0.9, default 0.8) "Only applies when `Deepgram` is selected as the `transcriptionProvider` and `flux` is selected as the `speechModel`" — [Twilio ConversationRelay noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun) (verified)
- Telnyx's ConversationRelay-compatible product also has `partialPrompts` with `last=false` — [Telnyx Conversation Relay docs](https://developers.telnyx.com/docs/voice/programmable-voice/conversation-relay) (snippet)

**Retell: streams live transcript updates to a custom-LLM server**
- "update_only: This event is simply an update containing the latest transcript or turntaking information, no response required." Retell "would send an event when the transcript updates -- either the user speaks, or the agent speaks." Each event carries the "Complete live transcript collected in the call so far", with per-word timings — [Retell LLM WebSocket API reference](https://docs.retellai.com/api-references/llm-websocket) (verified)
- The update frequency, and whether partial words are included, is not documented.

**OpenAI Realtime and Azure Voice Live: eagerness tuning only**
- `semantic_vad` with `eagerness` (low, medium, high, auto) changes when the turn is committed. No draft-then-cancel event exists — [OpenAI Realtime VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad) (snippet)
- Azure Voice Live offers `azure_semantic_vad` and semantic EOU. No eager event was found — [Microsoft Learn: Voice Live](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-voice-live-evaluate) (snippet)

**Contact-center agent-assist marketing that sounds like during-speech retrieval**
- NICE CXone Copilot is described as suggesting complete responses from an approved KB "as the customer speaks or types" — [NICE AI agent assist page](https://www.nice.com/generative-ai-in-customer-service/ai-agent-assist) (snippet, marketing)
- Cresta Knowledge Agent "continuously listens and delivers precise answers in real time" — [Cresta Knowledge Assist](https://cresta.com/knowledge-assist) (snippet, marketing)
- Google PGKA's documented trigger options are `CUSTOMER_MESSAGE` (default), `AGENT_MESSAGE` and `END_OF_UTTERANCE`. All of these are post-utterance — [Google Agent Assist PGKA docs](https://docs.cloud.google.com/agent-assist/docs/pgka) (snippet)

### Inferences
- The specific claim "retrieval that starts on interim transcripts before end-of-turn, with commit or discard" appears unoccupied as an advertised commercial feature. forehear's positioning is open on that front. The ingredients are commoditizing, though:
  - Deepgram and Twilio expose eager turn events.
  - ElevenLabs and LiveKit speculate on the LLM.
  - Sierra runs parallel speculative tasks.
- Agent-assist marketing such as "as the customer speaks" should not be read as mid-utterance retrieval. The only documented triggers (Google) fire per finalized message.

### Gaps
- I could not confirm whether ElevenLabs `speculativeTurn` also triggers "Every turn" RAG speculatively. The docs are silent; testing would be needed.
- I could not confirm whether Sierra's speculative retrieval is ever keyed on partial speech.
- No primary engineering content on retrieval timing was found for PolyAI, Decagon, Bland, Synthflow or Parloa.

## Q2. Platform-by-platform: KB/RAG feature, when retrieval runs, pricing

### Takeaway
Two retrieval-timing patterns dominate:
1. **Automatic on every user turn, after the final transcript:**
   - ElevenLabs "Every turn".
   - Vapi custom KB, "Queried on every user message".
   - Amazon Q in Connect self-service, with responses generated "at each turn".
2. **Model-chosen tool call:**
   - ElevenLabs "On demand".
   - Vapi Google KB.
   - Ultravox `queryCorpus`.
   - Synthflow, which uses a description of when to look up.
   - OpenAI Realtime, Gemini Live, Nova Sonic and Azure (function or MCP tools).
   - Deepgram Voice Agent functions.
   - Bland and Cartesia Line tools.

Proactive retrieval exists only in contact-center agent assist, which triggers per utterance (see Q5). Separate KB/RAG pricing is almost never public. ElevenLabs folds it into LLM cost.

### Cited Findings

**Speech-to-speech model APIs**

- **OpenAI Realtime (gpt-realtime / 2.x)**
  - Function tools run client-side. Remote MCP tools "are executed by the Realtime API itself". Remote servers "don't automatically receive the full conversation context" — [OpenAI Realtime MCP guide](https://developers.openai.com/api/docs/guides/realtime-mcp) (snippet)
  - No hosted `file_search` for Realtime was found. Community posts say Realtime "does not support file_search or vector" and that developers wrap vector search in a function. One Sep 2025 post claims the Agents SDK passes `file_search` through (unverified) — [OpenAI community thread](https://community.openai.com/t/does-voice-agents-realtime-api-supports-the-vector-stores-or-file-from-platform-open-ai/1311577); [OpenAI community thread 2](https://community.openai.com/t/realtime-api-connection-to-vector-store-similar-to-assistants-api/963959) (snippets)
  - Timing: model-chosen tool call after the turn is committed.

- **Google Gemini Live API + Vertex AI RAG Engine**
  - Live API tools: function calling, code execution, Google Search grounding, and Vertex AI RAG Engine (Preview) — [Vertex AI Live API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api) (snippet)
  - The RAG Engine doc for the Live API describes passing RAG Engine as a tool and a "memory corpus" for session context — [Use Vertex AI RAG Engine in Gemini Live API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-rag-in-multimodal-live?hl=de) (snippet; only non-English versions surfaced)
  - A LiveKit PR proposing a Vertex RAG provider tool claims function-calling RAG with Gemini native audio needs "two inference passes, ~3–5 s" versus "~0.5 s" for server-side retrieval — [livekit/agents PR #5222](https://github.com/livekit/agents/pull/5222) (snippet; PR author's estimate)
  - Timing: model-chosen tool.

- **AWS Nova Sonic / Nova 2 Sonic + Bedrock KB**
  - Tools are defined at `promptStart`, and the model emits `toolUse`. RAG is done by wrapping Bedrock KB Retrieve as a tool — [AWS Nova docs: tool use, RAG](https://docs.aws.amazon.com/nova/latest/userguide/speech-tools.html) (snippet); [CloudThat](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai) (third-party)
  - A third party claims Nova 2 Sonic offers "asynchronous tool use" — [CloudVisor](https://cloudvisor.co/?p=61329) (third-party, unverified)
  - Timing: model-chosen tool.

- **Azure Voice Live + Foundry Agent Service**
  - In the described flow, Voice Live handles speech and the Agent Service "executes workflows or retrieves knowledge". Existing Foundry agents can be voice-enabled — [Microsoft Tech Community: voice-native agents in Foundry](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/public-preview-voice-native-agents-in-microsoft-foundry/4502756) (snippet)
  - Timing: agent hop after transcription.

**Hosted agent platforms**

- **ElevenLabs Agents Platform**
  - Modes: "Every turn", "On demand" ("let the agent search only when it decides it needs to") and "Prompt only". Query: "The user's question is analyzed and reformulated for optimal retrieval."
  - Embedding model: `e5_mistral_7b_instruct`.
  - Index size limit: 1 MB (Free) to 1 GB (Business/Enterprise). Documents under 500 bytes go into the prompt.

  Source: [ElevenLabs RAG docs](https://elevenlabs.io/docs/agents-platform/customization/knowledge-base/rag) (verified)
  - Pricing: no separate RAG fee was found. The agents pricing page lists $0.08/min, with Knowledge Base and RAG among plan features. The LLM is billed on top, and ElevenLabs says RAG reduces input tokens — [ElevenLabs agents pricing](https://elevenlabs.io/pricing/agents); [ElevenLabs: Optimizing LLM costs](https://elevenlabs.io/docs/eleven-agents/customization/llm/optimizing-costs) (snippets)

- **Vapi**
  - Custom KB: "Queried on every user message", with "Lower (direct database query)" latency. Google KB: "Called as tool when needed by assistant", with "Higher (Google Gemini model processing)" latency — [Vapi: Migrating from Trieve](https://docs.vapi.ai/knowledge-base/migrating-from-trieve) (snippet)
  - Custom KB mechanics: `provider: custom-knowledge-base` with a `server.url`. Vapi POSTs `{"message":{"type":"knowledge-base-request","messages":[...]}}`, and the server returns documents or a finished answer — [Vapi custom knowledge base](https://docs.vapi.ai/knowledge-base/custom-knowledge-base); [Vapi: implement custom endpoint](https://docs.vapi.ai/knowledge-base/implement-custom-endpoint) (snippets)
  - Former Trieve backend: aborted after "750 ms", and staff said the timeout cannot be raised — [Vapi support](https://support.vapi.ai/t/28554757/knowledge-base-retrieval-aborted-request-took-too-long-waite) (snippet)

- **Retell AI**
  - The built-in KB is available for single-prompt and conversation-flow agents. The custom LLM WebSocket is the documented path for "your own retrieval pipeline instead of Retell's knowledge base" — [Retell: integrate LLM overview](https://docs.retellai.com/integrate-llm/overview) (snippet)
  - The per-call latency breakdown includes `knowledge_base`: "from triggering retrieval to receiving all relevant context" — [Retell: check actual latency](https://docs.retellai.com/reliability/check-actual-latency.md) (snippet)

- **Bland AI**
  - Docs index entries:
    - A "Knowledge" page: "Add the sources your agent answers from, attach them to an agent, and test what it retrieves".
    - KB ingestion APIs: file, text and web scrape.
    - A "Chat with Knowledge Base Item" endpoint.
    - Legacy "vectors" KBs.
    - v2 Tools "invoked automatically during calls", including custom HTTP tools.
    - An "Agent Speech" page: "Control how readily your agent pauses for callers and how quickly it responds after they stop talking."

    Source: [Bland docs index llms.txt](https://docs.bland.ai/llms.txt) (verified index; individual pages not fetched)
  - Aug 4, 2025 changelog: Knowledge Base overhaul, with web scraping, a playground for testing KB queries, and a suggestions system — [Bland changelog 08/04/2025](https://docs.bland.ai/changelog/08_04_2025) (snippet)
  - Retrieval timing: not documented in what was read.

- **Synthflow**
  - "A knowledge base holds documents and pages your agents can query during calls using retrieval-augmented generation (RAG)." You "describe the situations or user questions that should trigger a lookup". "An agent only runs knowledge base searches when a knowledge base is attached." Call logs show "how long the lookup took" — [Synthflow Knowledge Base docs](https://docs.synthflow.ai/knowledge-base.md) (verified)
  - Sources: URL crawl and Zendesk. API: `POST /knowledge_base` (v2) — [Synthflow create KB API](https://docs.synthflow.ai/api-reference/platform-api/knowledge-bases/create-knowledge-base.md) (snippet)
  - No latency figure, pricing or custom-retriever option is on the page.
  - Timing: a conditional lookup, i.e. LLM- or description-triggered.

- **PolyAI (Agent Studio)**
  - PolyAI's CTO Shawn Wen (SurrealDB stream, Dec 17, 2025) describes two patterns for external knowledge:
    - "Sometimes the external system is basically a content source (say, a KB tool), and PolyAI runs retrieval internally."
    - "Sometimes the external system has vector search and PolyAI just calls it over an API."

    Agent Studio is "Model-agnostic by default". A developer platform and APIs were planned for Q1 2026 — [SurrealDB blog: PolyAI on context-aware voice agents](https://surrealdb.com/blog/polyai-on-building-context-aware-voice-agents-latency-knowledge-bases-and-what-actually-ships) (verified)
  - Release notes: Feb 2026 added latency visualization (LLM request and function timing). Mar 2026 shows which Connected Knowledge files were retrieved on each turn — [PolyAI releases overview](https://docs.poly.ai/releases/overview.md) (snippet)
  - PolyAI has a RAG section in its docs — [PolyAI RAG intro](https://docs.poly.ai/knowledge/faqs/RAG/introduction) (not fetched)

- **Sierra**
  - Parallel and speculative retrieval with predictive prefetching (see Q1). No public KB product docs. Closed platform — [Sierra blog](https://sierra.ai/blog/voice-latency)

- **Decagon**
  - Its public voice-latency work is about model serving:
    - "p90 latency of 342ms", via a custom speculator model and SGLang changes, with 38% higher accept lengths — [Decagon/Modal: real-time voice AI on Modal (Nov 2025)](https://decagon.ai/blog/real-time-voice-ai-on-modal) (snippet)
    - "p95 model latency ... under 400ms" and 6x lower cost per turn — [Together AI: Decagon](https://together.ai/customers/decagon) (vendor case study)
  - No retrieval-timing content found.

- **Cartesia Line (SDK plus hosted agents)**
  - Tools are functions such as "database lookups, handoffs, web search". There are built-in `end_call` and `web_search` tools — [Cartesia Line SDK overview](https://docs.cartesia.ai/line/sdk/overview.md) (snippet)
  - "Background reasoning" example — [cartesia-line on PyPI](https://pypi.org/project/cartesia-line/0.1.2/) (snippet)
  - A third-party skill guide says tools that run longer than about 1 s can use `@loopback_tool(is_background=True)` — [skills.sh cartesia-ai](https://skills.sh/cartesia-ai) (third-party)
  - No built-in KB found. Line is "reasoning agnostic", so retrieval is code you write.

- **Hume EVI**
  - Two options:
    - A supplemental LLM (Claude and others), where EVI sends the transcript plus expression measures.
    - A Custom Language Model (CLM), where "EVI sends requests to your server with textual conversation history and emotional context, and your server responds with the text."

    Sources: [Hume EVI language model config](https://dev.hume.ai/docs/empathic-voice-interface-evi/configuration/language-model); [Hume CLM guide](https://dev.hume.ai/docs/speech-to-speech-evi/guides/custom-language-model) (snippets)
  - No built-in KB found. EVI 3 claims "under 300 ms" response — [Hume: Introducing EVI 3](https://hume.ai/blog/introducing-evi-3) (snippet, marketing)

- **Layercode**
  - The developer's own backend receives webhooks over SSE. Payloads include `transcription_duration_seconds`, `tts_duration_seconds` and `latency`. A newer low-latency WebSocket channel is used for barge-in and token streaming — [Layercode webhook SSE API](https://docs.layercode.com/api-reference/webhook-sse-api) (snippet via mirror)
  - No built-in KB. Retrieval is entirely in the customer backend.

- **Speechmatics Flow**
  - Flow is an STT + LLM + TTS agent API. Agents are templates (prompt, LLM, voice, dictionary) set in the Portal. It supports function calling, and transcript and response events are shared, e.g. `ResponseStarted` — [Speechmatics Flow docs](https://docs.speechmatics.com/voice-agents-flow) (snippet)
  - The July 2024 launch promised answers "from internal documentation" and integration "with any preferred LLM". I found no docs confirming either shipped — [audioXpress: Flow launch](https://audioxpress.com/news/speechmatics-introduces-flow-api-for-advanced-speech-interactions) (snippet; forward-looking)

- **Ultravox (cloud)**
  - The `queryCorpus` built-in tool over hosted corpora is model-invoked. A personal blog claims retrieval runs "inside its inference path ... sub-100ms" — [VoxFlow blog](https://faketut.github.io/2026/05/08/voxflow-06-ultravox-rag-queryCorpus/) (third-party, unverified)
  - Full-Duplex-Bench-v3 measured Ultravox v0.7: first-word latency 3.88 s, the fastest among tested systems, but tool-call latency 6.01 s, the slowest, "because the model speaks before calling a tool" — [arXiv 2604.04847](https://arxiv.org/pdf/2604.04847) (snippet; academic benchmark, general tools)

- **Rime**
  - A TTS model vendor (Mist v3, Coda, Arcana) that integrates with Vapi, LiveKit and others. No agent KB feature — [Rime docs](https://docs.rime.ai/docs/introduction) (snippet)
  - Not a direct competitor.

- **Inworld**
  - Offers TTS, STT, a Realtime speech-to-speech API, and an LLM Router. Realtime supports "built-in web search as well as any custom tool you define" — [Inworld Realtime API](https://inworld.ai/realtime-api) (snippet)
  - Runtime is described as "Graph-based orchestration for models, speech, memory, knowledge and tools" — [Inworld docs](https://docs.inworld.ai/introduction.md) (snippet)
  - No KB timing docs found.

- **Telnyx AI Assistants**
  - Portal Knowledge Bases accept uploaded files and URLs. There is an "Embedding & RAG" docs section, plus a memory feature for caller recall — [Telnyx release notes: fast KB uploads](https://telnyx.com/release-notes/fast-knowledge-base-uploads); [Telnyx AI docs index](https://developers.telnyx.com/development/llms/ai-llms-txt) (snippets)
  - Timing undocumented in what was read.
  - Telnyx resells Deepgram Flux eager EOT and quotes about 150–250 ms saved — [Telnyx EOT parameters](https://developers.telnyx.com/docs/voice/stt/websocket-streaming/parameters/end-of-turn) (snippet)

- **Deepgram Voice Agent API**
  - The `think` stage can use Deepgram-managed models (think-fast, early access), third-party providers, or a custom `endpoint`. Functions run client-side or server-side (Deepgram calls your HTTP endpoint). The architecture docs say the LLM and function calls can reach "embedding models, databases, and retrieval APIs". There is no built-in retrieval — [Deepgram Voice Agent LLM docs](https://developers.deepgram.com/docs/llm/voice-agent.md); [Deepgram voice agent architecture](https://developers.deepgram.com/docs/voice-agent-architecture.md) (snippets)
  - A Deepgram doc titled "WIP: RAG & Multi-Agent Workflows" surfaced in search but returned 404 when fetched — [Deepgram (404)](https://developers.deepgram.com/docs/voice-agent-rag-multi-agent-workflows)

- **Twilio ConversationRelay**
  - Provides STT/TTS transport only, with the LLM and RAG in the customer's WebSocket app. `partialPrompts` is available with Deepgram Flux (see Q1) — [Twilio ConversationRelay noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun) (verified)

- **Enterprise conversational AI (Parloa, Cognigy, Kore.ai, Yellow.ai)**
  - Only competitor or affiliate comparisons surfaced:
    - Cognigy is put at about 500 ms end-to-end and Kore.ai at 800–1,000 ms. Cognigy "uses RAG specifically optimized for enterprise sources like wikis", while Kore.ai uses "semantic search and knowledge graphs" — [Fin.ai comparison](https://fin.ai/learn/cognigy-vs-kore-ai-vs-parloa); [Retell: Cognigy vs Kore.ai](https://retellai.com/blog/cognigy-vs-kore-ai) (competitor content, low reliability)
  - Cognigy is now part of NICE. A 2026 article is framed around "Cognigy alternatives [after the] NICE acquisition" — [Lorikeet article](https://www.lorikeetcx.ai/articles/cognigy-alternatives-nice-acquisition-2026) (snippet; the acquisition date is from training knowledge, not verified here)

- **Daily/Pipecat Cloud and LiveKit Cloud**
  - These are hosting for open-source frameworks. Retrieval is user code. LiveKit Agents has "preemptive generation" for the LLM — [LiveKit docs](https://docs.livekit.io/agents/multimodality/audio/) (snippet)
  - The open-source frameworks researcher covers them in detail.

### Inferences
- Platforms that own the whole pipeline and run "every turn" RAG have the clearest incentive and ability to move retrieval earlier: ElevenLabs, Vapi's custom KB, and PolyAI's internal retrieval. The trigger is already deterministic, so it does not wait on a model decision, and they already own the turn detector. This is the most natural place for forehear's technique to be cloned.
- Platforms where retrieval is a model-chosen tool (speech-to-speech APIs, Ultravox, Synthflow, Bland tools) can't easily speculate without an extra prediction step. This is where forehear-style "predict the query from partials and inject context" is most differentiated, and where it is hardest to integrate.

### Gaps
- KB/RAG pricing is not public for Vapi, Retell, Bland, Synthflow, PolyAI, Telnyx, Ultravox, OpenAI Realtime (no hosted RAG), or Gemini Live + RAG Engine. RAG Engine has its own GCP pricing, which was not fetched.
- A third-party figure of $0.035 per Google Search grounding call is unverified and covers Search grounding, not RAG Engine — [tkmxai blog](https://www.tkmxai.it.com/integrating-the-gemini-api-for-multimodal-rag-pipelines-in-2026)
- Bland's "Knowledge" page and Yellow.ai and Parloa product docs were not fetched.
- Inworld and Speechmatics KB behaviour remains undocumented in sources found.

## Q3. What latency numbers do platforms publish for RAG / knowledge-base turns?

### Takeaway
Only a handful of first-party RAG latency figures exist:
- **ElevenLabs** publishes the only distribution: median 326 ms reduced to 155 ms, p75 436 ms to 250 ms, p95 629 ms to 426 ms. Its docs say "around 250ms".
- **PolyAI** reports about 30 ms for an external vector lookup versus about 31 ms for its internal retrieval.
- **Vapi** enforced a 750 ms Trieve timeout.

Tool-based RAG on speech-to-speech models is reported by practitioners and benchmarks at seconds, not milliseconds.

### Cited Findings
- **ElevenLabs:**
  - Distribution: median 326 ms to 155 ms, p75 436 ms to 250 ms, p95 629 ms to 426 ms.
  - Query rewriting was "more than 80% of RAG latency". The fix was to race several rewriter models, including self-hosted Qwen 3-4B and 3-30B-A3B, so that "The first valid response wins". If nothing returns within 1 s, the raw user message is used.

  Source: [ElevenLabs engineering RAG blog (Sep 12, 2025, updated Sep 8, 2026; Michal Korbela)](https://elevenlabs.io/blog/engineering-rag) (verified)
- **ElevenLabs docs:** "RAG adds on slight latency to the response time of your agent, around 250ms." — [ElevenLabs RAG docs](https://elevenlabs.io/docs/agents-platform/customization/knowledge-base/rag) (verified)
- **PolyAI:**
  - An external SurrealDB vector lookup adds about 30 ms, versus about 31 ms average for PolyAI's internal embedding plus search — [SurrealDB/PolyAI search summary](https://surrealdb.com/blog/polyai-on-building-context-aware-voice-agents-latency-knowledge-bases-and-what-actually-ships); [case study](https://www.casestudies.com/company/surrealdb/case-study/572c-high-performance-customer-service-ai-powered-by-rag) (vendor co-marketing; the figure did not appear in my fetch of the blog page, so it rests on search snippet and case study)
  - The PolyAI CTO's targets: keep turns "under ~1 to 1.5 seconds", past "~2 to 2.5 seconds ... feel clunky", and going dark for more than about 5 s means "people assume something is broken" — [SurrealDB blog](https://surrealdb.com/blog/polyai-on-building-context-aware-voice-agents-latency-knowledge-bases-and-what-actually-ships) (verified)
- **Vapi/Trieve:** a 750 ms abort — [Vapi support](https://support.vapi.ai/t/28554757/knowledge-base-retrieval-aborted-request-took-too-long-waite) (snippet). Trieve claimed a "maximum of 200ms" — [Trieve](https://www.trieve.ai/integrations/vapi) (marketing)
- **Retell:** a per-call `knowledge_base` latency field with no typical value published — [Retell docs](https://docs.retellai.com/reliability/check-actual-latency.md) (snippet). A third party says about 100 ms per lookup — [Waboom](https://www.waboom.ai/blog/the-rag-powered-voice-agent-how-retell-ai-elevates-knowledge-retrieval) (unsourced)
- **Gemini Live function-calling RAG:** about 3–5 s (two passes) versus about 0.5 s server-side, per a LiveKit PR author — [livekit/agents PR #5222](https://github.com/livekit/agents/pull/5222) (estimate)
- **Nova Sonic + Bedrock KB:** 2–5 s per lookup in one build — [CloudThat](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai) (practitioner)
- **Ultravox:** tool-call latency of 6.01 s in Full-Duplex-Bench-v3 (general tools, not corpus-specific) — [arXiv 2604.04847](https://arxiv.org/pdf/2604.04847) (snippet)
- **Cresta:** "near-zero latency" on its product page — [Cresta](https://cresta.com/?p=28765) (marketing). The "under 200 ms" figure appears only in third-party guides — [Macha guide](https://www.getmacha.com/blog/cresta-ai-complete-guide) (third-party)
- **Model-serving (non-RAG) figures for context:**
  - Decagon: p90 342 ms — [Decagon/Modal](https://decagon.ai/blog/real-time-voice-ai-on-modal); p95 under 400 ms — [Together AI](https://together.ai/customers/decagon)
  - Hume EVI 3: under 300 ms — [Hume](https://hume.ai/blog/introducing-evi-3)
- **Deepgram eager EOT:** saves 100–200 ms ("hundreds of milliseconds") at the cost of 50–70% more LLM calls — [Deepgram](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt). Telnyx quotes 150–250 ms — [Telnyx](https://developers.telnyx.com/docs/voice/stt/websocket-streaming/parameters/end-of-turn) (snippet)
- No published RAG latency was found for Bland, Synthflow, Speechmatics, Inworld, Layercode, Cartesia, Telnyx, OpenAI Realtime, Azure, Google PGKA or Amazon Q in Connect. AWS says only that the multistep process "adds time to the interactions" — [AWS admin guide: Q in Connect self-service](https://docs.aws.amazon.com/connect/latest/adminguide/generative-ai-powered-self-service-q.html) (snippet)

### Inferences
- ElevenLabs' own data shows retrieval latency is dominated by the LLM query-rewrite step, not vector search. PolyAI's figure of about 30 ms for vector search supports this. forehear's value is therefore largest where a rewrite or LLM step precedes search, since speculating on partials can hide that step. A pure vector lookup of about 30 ms leaves little to hide.
- ElevenLabs' approach (racing models, a 1 s fallback) shows a well-resourced platform optimizing the post-turn path rather than moving it earlier. This suggests speculative-on-partials is not yet their chosen lever. That is an inference.

### Gaps
- No vendor publishes RAG latency measured from end of user speech to retrieved context, with a stated methodology, other than ElevenLabs' pipeline-internal distribution.
- PolyAI's "~30 ms" figure could not be confirmed in the fetched page text.

## Q4. Which platforms let you bring your own RAG endpoint / custom LLM, so forehear can sit in front?

### Takeaway
The best insertion points are platforms that do two things: stream partial or interim user transcripts to a developer server, and let that server own the LLM or RAG. These are:
- Twilio ConversationRelay, with `partialPrompts` (Flux).
- Retell's custom LLM WebSocket, with `update_only` live transcripts.
- Telnyx Conversation Relay.
- Deepgram Flux used directly.
- Cartesia Line, Layercode, Pipecat and LiveKit, where the code is developer-owned.

Weaker insertion points let you bring your own retriever but call it only after the final turn, so forehear can only serve as a fast cache behind them:
- Vapi custom KB.
- Hume CLM.
- Deepgram Voice Agent custom think endpoint and server functions.
- PolyAI external vector API.
- Bland and Synthflow custom tools.

Closed platforms leave essentially no hook: Sierra, Decagon, Synthflow's built-in KB, and Speechmatics Flow templates.

### Cited Findings
- **Strong hooks: partial transcripts plus developer-owned LLM**
  - **Twilio ConversationRelay:** `partialPrompts` sends "unfinalized prompts and eager end-of-turn events" with `last=False` — [Twilio](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun) (verified)
  - **Retell custom LLM:** "update_only ... the latest transcript", plus `response_required` once a reply is needed. A custom LLM is the path for "your own retrieval pipeline" — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket) (verified); [Retell integrate-LLM overview](https://docs.retellai.com/integrate-llm/overview) (snippet)
    - Caveat from Retell: "You take on latency, uptime, and reconnection handling."
  - **Telnyx Conversation Relay:** `partialPrompts` — [Telnyx](https://developers.telnyx.com/docs/voice/programmable-voice/conversation-relay) (snippet)
  - **Deepgram Flux** used directly: `EagerEndOfTurn` / `TurnResumed` — [Deepgram](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
  - **Layercode:** a customer backend over webhook/SSE or WebSocket — [Layercode](https://docs.layercode.com/api-reference/webhook-sse-api) (snippet). Whether interim transcripts are sent is not confirmed.
  - **Cartesia Line:** an SDK in which retrieval is a user-defined tool, and background tools are supported — [Cartesia Line](https://docs.cartesia.ai/line/sdk/overview.md) (snippet)
- **Bring your own retriever, called post-turn only**
  - **Vapi custom KB:** a `knowledge-base-request` webhook with the message history — [Vapi](https://docs.vapi.ai/knowledge-base/custom-knowledge-base) (snippet)
  - **Hume EVI CLM:** a public endpoint that receives conversation history — [Hume CLM](https://dev.hume.ai/docs/speech-to-speech-evi/guides/custom-language-model) (snippet)
  - **Deepgram Voice Agent:** a custom think `endpoint`, plus server-side functions that Deepgram calls over HTTP — [Deepgram](https://developers.deepgram.com/docs/llm/voice-agent.md) (snippet)
  - **PolyAI:** "the external system has vector search and PolyAI just calls it over an API" — [SurrealDB/PolyAI](https://surrealdb.com/blog/polyai-on-building-context-aware-voice-agents-latency-knowledge-bases-and-what-actually-ships) (verified)
  - **Bland v2 custom API tools:** "call your own backend ... or any HTTP endpoint" — [Bland docs index](https://docs.bland.ai/llms.txt) (verified index)
  - **OpenAI Realtime remote MCP and function tools; Gemini Live function tools; Nova Sonic toolUse** — sources in Q2.
  - **Azure Voice Live:** voice-enables existing Foundry agents, so a custom agent can own retrieval — [Microsoft](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/public-preview-voice-native-agents-in-microsoft-foundry/4502756) (snippet)
- **Little or no hook**
  - Synthflow: the KB docs list only built-in RAG and Zendesk, with no custom retriever — [Synthflow](https://docs.synthflow.ai/knowledge-base.md) (verified)
  - Speechmatics Flow: templates in the Portal, and BYO-LLM is unconfirmed — [Speechmatics](https://docs.speechmatics.com/voice-agents-flow) (snippet)
  - Sierra and Decagon: closed managed platforms with no public developer docs found.

### Inferences
- **Twilio ConversationRelay plus Deepgram Flux is the cleanest commercial fit.** Twilio streams eager or partial prompts to exactly the server where a forehear-style speculative retriever would run. Twilio is a natural partner, or a channel through docs and samples, for a forehear integration.
- **Retell's custom LLM WebSocket is the second-best fit.** It streams live transcripts and is already the documented route for custom retrieval.
- **On the post-turn BYO hooks** (Vapi KB, Hume CLM, Deepgram functions), forehear cannot start early unless it also has a separate STT feed. It could still serve pre-warmed results if it consumed partials from another channel, but those platforms don't expose such a channel. This is an inference.

### Gaps
- I did not confirm whether Vapi's custom-LLM mode or webhooks expose interim transcripts. Training knowledge suggests a `transcript` server message with partials exists, but this is unverified here.
- I did not confirm whether ElevenLabs' custom-LLM mode or its WebSocket exposes interim user transcripts to the developer.
- How often Retell sends `update_only` during user speech is undocumented.

## Q5. Contact-center agent assist: proactive knowledge from live transcripts

### Takeaway
The proactive-retrieval products from Google, Amazon, NICE, Genesys, Cresta, Observe.AI and Talkdesk prove the market for "retrieve without an explicit query from a live transcript". Where triggering is documented, it is per utterance or message:
- Google: `CUSTOMER_MESSAGE`, `AGENT_MESSAGE`, `END_OF_UTTERANCE`.
- Amazon: intents detected from Contact Lens.

None publishes latency for knowledge suggestions. They target human agents, whose latency tolerance is seconds. These vendors are buyers or integrators of fast retrieval, not voice-bot competitors on sub-second retrieval.

### Cited Findings
- **Google Agent Assist PGKA:**
  - Triggers default to `CUSTOMER_MESSAGE`, with `AGENT_MESSAGE` and `END_OF_UTTERANCE` as alternatives. A "Load proactive answers asynchronously" option exists — [Google PGKA docs](https://docs.cloud.google.com/agent-assist/docs/pgka) (snippet)
  - PGKA V2 is GA with "granular control over triggering events". Gemini Transcribe Live (Preview) delivers "quick, reliable intermediate transcriptions". The Pub/Sub intermediate transcription entry is marked preview and also deprecated — [Agent Assist release notes](https://docs.cloud.google.com/gemini-enterprise-cx/agent-assist/release-notes) (snippet)
  - The only official latency notes found concern summarization versions, not knowledge assist — [Agent Assist release notes](https://docs.cloud.google.com/agent-assist/docs/release-notes) (snippet)
- **Amazon Q in Connect:**
  - "Automatically detects customer intent during calls ... proactively generates clickable intents." Voice requires Contact Lens — [AWS admin guide](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-q-connect.html) (snippet)
  - Self-service in voice (IVR) generates responses "at each turn", and AWS notes the multistep process "adds time to the interactions" — [AWS Q in Connect self-service](https://docs.aws.amazon.com/connect/latest/adminguide/generative-ai-powered-self-service-q.html) (snippet)
- **NICE CXone Mpower Copilot for Agents:**
  - Surfaces KB articles when topics arise and suggests responses from an approved KB "as the customer speaks or types" — [NICE AI agent assist](https://www.nice.com/generative-ai-in-customer-service/ai-agent-assist) (snippet, marketing)
  - Real-time transcription feeds Copilot — [NICE help: Transcription for Copilot](https://help.nicecxone.com/content/transcriptionhub/continuoustranscription/transcriptionforcopilot.htm); [NICE help: Copilot for Agents](https://help.nicecxone.com/Content/copilotagents/copilotforagents.htm) (snippets)
  - NICE also owns Cognigy (see Q2).
- **Genesys Cloud Agent Copilot:**
  - Determines customer intent, "automatically surfaces knowledge", and shows the next best action "in a live stream of suggestions during the conversation". Customers load knowledge into Genesys Knowledge Workbench — [Genesys help: Agent Copilot](https://help.genesys.cloud/usecases/genesys-agent-copilot/) (snippet)
  - One community user reported voice knowledge surfacing "with minimal to no lag time". A 2025 follow-up in the same thread asked about latency — [Genesys community thread](https://community.genesys.com/discussion/genesys-copilot-knowledge-surfacing-for-voice-channel) (snippet, anecdotal)
- **Cresta Knowledge Agent / Knowledge Assist:** "continuously listens and delivers precise answers in real time", grounded in conversation and on-screen context. Models are served on Fireworks — [Cresta Knowledge Assist](https://cresta.com/knowledge-assist); [Fireworks: Cresta](https://fireworks.ai/blog/story-cresta-knowledge-assist) (snippets, marketing)
- **Observe.AI Knowledge AI:** "Use GenAI to tap into the collective information across your knowledge bases, FAQs, past agent responses" — [Observe.AI Real-Time AI](https://observe.ai/real-time-ai) (snippet, marketing)
- **Talkdesk Agent Assist:** pulls information from a KB or CRM "as a suggested action in real-time" — [CX Today: Talkdesk Agent Assist](https://www.cxtoday.com/contact-center/talkdesk-launches-talkdesk-agent-assist/) (snippet, press)
- **Five9:** no usable primary source found.

### Inferences
- Agent-assist is the closest existing commercial analogue to forehear's "retrieve from the live transcript before anyone asks". Its latency budget, though, is human reading time. Mid-utterance speculation adds little there, except to make suggestions appear sooner.
- Google, with the PGKA trigger controls plus Gemini Transcribe Live intermediate transcripts, has every ingredient to add mid-utterance triggering if it wanted.

### Gaps
- No latency figures exist for any agent-assist knowledge suggestions.
- Five9 Genius AI and Talkdesk docs were not reached in primary form.

## Q6. Evidence of customer pain about RAG latency

### Takeaway
The pain is real but the evidence is thin and anecdotal:
- Vapi users hit a hard 750 ms KB timeout, and one reports about 10 s with the Gemini-backed KB tool.
- Developers note OpenAI file search makes responses noticeably slower.
- Practitioners report 2–5 s for Nova Sonic + Bedrock KB.

Vendors' own engineering posts confirm the problem matters: ElevenLabs halved RAG latency, and PolyAI says slow retrieval "can't hide behind a spinner". Support threads more often blame the LLM than the KB.

### Cited Findings
- **Vapi:** retrievals aborted after "Waited for 750 ms", and staff said the timeout cannot be raised — [Vapi support](https://support.vapi.ai/t/28554757/knowledge-base-retrieval-aborted-request-took-too-long-waite) (snippet)
- **Vapi:** about 10 s from question to response with the Gemini query tool on about 140 Markdown files — [Vapi community](https://vapi.ai/community/m/1422970715174342706) (snippet, anecdotal)
- **Retell:** a support thread reporting 5–10 s delays blamed the LLM (Claude Sonnet 4.6, median about 4.8 s, p90 about 8.7 s), not the KB — [Retell community: LLM latency issue](https://community.retellai.com/t/llm-latency-issue/1009) (snippet). This is counter-evidence: there, the LLM was the bottleneck.
- **OpenAI file search:** one user saw about 7.7 s before the first chunk, and another said enabling File Search made responses noticeably slower. Both relate to Assistants/Responses, not Realtime — [OpenAI community](https://community.openai.com/t/how-exactly-does-file-search-work-in-chatgpt-is-it-always-necessary-to-enable-it/1248263) (snippet)
- **Nova Sonic + Bedrock KB:** 2–5 s per lookup, worked around with filler speech — [CloudThat](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai)
- **Vendor acknowledgement:**
  - ElevenLabs: RAG "runs on every query, which creates a latency risk"; external LLMs slow during peak hours — [ElevenLabs engineering RAG](https://elevenlabs.io/blog/engineering-rag) (verified)
  - PolyAI CTO: "if the vendor's retrieval isn't fast enough, you can't hide it behind a spinner" — [SurrealDB/PolyAI](https://surrealdb.com/blog/polyai-on-building-context-aware-voice-agents-latency-knowledge-bases-and-what-actually-ships) (verified)
- **Kore.ai:** latency of 800–1,000 ms or more is said to spike "when bots rely heavily on third-party API calls mid-conversation" — [Thunai review](https://www.thunai.ai/blog/kore-ai-review-features) (competitor/affiliate, low reliability)
- **Gaps in this evidence:** no Reddit or ElevenLabs-forum threads on KB latency surfaced in my searches.

### Inferences
- Pain concentrates on two cases: tool-based or managed RAG (seconds), and hard timeouts (Vapi). These are both cases where the retrieval work is large enough that starting it about 200–600 ms earlier, during the user's final words, would materially help. For fast in-platform vector RAG (about 30–250 ms), customers mostly blame the LLM.

### Gaps
- No review-site (G2 or Capterra) evidence specifically about KB latency was collected.

## Q7. Who is most likely to build speculative retrieval in-house, and who are potential adopters or partners?

### Takeaway
**Most likely to build it in-house**, because they own the turn detector, the retrieval pipeline and the LLM, and already speculate on adjacent stages:
- **ElevenLabs:** `speculativeTurn` plus every-turn RAG plus its own rewriter models.
- **Sierra:** already "parallel and speculative", with predictive prefetching.
- **Deepgram:** it authored the eager-EOT-for-RAG guidance and has a Voice Agent API.
- **Google:** PGKA trigger controls, intermediate transcripts, and RAG Engine in Live.
- **PolyAI and Decagon:** vertically integrated, latency-obsessed, with in-house serving.

**Most plausible adopters or partners**, because they expose partial transcripts to developer code or rely on customers' own retrieval: Twilio ConversationRelay, Telnyx, Retell (custom-LLM users), Layercode, Cartesia Line, Hume (CLM users), Vapi (custom-KB users, if partials are available), Pipecat/Daily and LiveKit, and STT vendors such as Deepgram, AssemblyAI and Soniox as a reference integration.

### Cited Findings
- ElevenLabs already speculates on the LLM (`speculativeTurn`) and has invested in RAG latency: racing self-hosted Qwen rewriters, a 1 s fallback, and median latency cut from 326 ms to 155 ms — [ElevenLabs SDK](https://cdn.jsdelivr.net/npm/@elevenlabs/elevenlabs-js@2.39.0/api/types/TurnConfig.d.ts); [ElevenLabs engineering RAG](https://elevenlabs.io/blog/engineering-rag)
- Sierra describes retrieval running "in parallel and speculatively" with "predictive prefetching" — [Sierra](https://sierra.ai/blog/voice-latency)
- Deepgram recommends eager EOT for "complex RAG ... or Function Calling" — [Deepgram](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- Google exposes PGKA triggering controls and intermediate transcription — [Agent Assist release notes](https://docs.cloud.google.com/gemini-enterprise-cx/agent-assist/release-notes) (snippet)
- Decagon built a custom speculator model for speculative decoding, at p90 342 ms — [Decagon/Modal](https://decagon.ai/blog/real-time-voice-ai-on-modal) (snippet)
- PolyAI matches about 30 ms internal retrieval and is building a developer platform (Q1 2026) — [SurrealDB/PolyAI](https://surrealdb.com/blog/polyai-on-building-context-aware-voice-agents-latency-knowledge-bases-and-what-actually-ships)
- Twilio `partialPrompts` and Retell `update_only` expose partial or live transcripts to developer servers — [Twilio](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun); [Retell](https://docs.retellai.com/api-references/llm-websocket) (verified)
- Retell steers most users to built-in agents that come "already tuned for things like latency". Custom-LLM users own their latency — [Retell integrate-LLM overview](https://docs.retellai.com/integrate-llm/overview) (snippet)

### Inferences
- **Highest cloning risk:** ElevenLabs. Extending `speculativeTurn` to cover "Every turn" RAG is a small step for them. Sierra and Decagon probably already do something similar internally, but they are closed and do not compete for developers.
- **Best partner targets:** Twilio (ConversationRelay plus Flux samples), Deepgram (a Flux eager-EOT RAG recipe), and Retell (custom-LLM template). Each lacks a built-in speculative retriever and has developers writing their own retrieval.
- **Speech-to-speech APIs** (OpenAI Realtime, Gemini Live, Nova Sonic, Azure Voice Live) are hard to adopt into. Retrieval is model-initiated, and partial-transcript access during S2S sessions is limited, so forehear would need a pre-turn context-injection pattern. Google could build server-side RAG Engine prefetch natively.
- **Contact-center suites** (NICE/Cognigy, Genesys, Five9, Talkdesk) are unlikely near-term adopters of an OSS library. They are more likely to build in-house or buy, and their agent-assist latency tolerance is loose.

### Gaps
- No public roadmap statements about speculative retrieval were found from any vendor.
- Partnership-readiness signals, such as integration marketplaces or OSS contributions, were not researched for Retell, Twilio or Deepgram.
