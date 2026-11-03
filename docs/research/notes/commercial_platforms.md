# Commercial Voice AI Platforms: Speculative/Preemptive Retrieval and RAG Latency (as of Nov 2026)

Scope note: Research done 2026-11-03 with a limited tool budget (~30 searches and fetches). Platforms with no usable primary-source findings are listed under Gaps rather than guessed at. Several search tool summaries were cross-checked by fetching the primary page. Where a claim rests only on a search snippet, it is marked "(snippet)".

## Q1. Which platforms expose events or features for starting work before end-of-turn?

### Takeaway
Several speech and agent vendors now ship explicit "start early" hooks. Deepgram Flux has `EagerEndOfTurn`/`TurnResumed`, and its own docs recommend these for "complex RAG ... or Function Calling" pipelines. ElevenLabs Agents has a `speculativeTurn` flag. OpenAI and Azure offer semantic VAD with tunable eagerness. AssemblyAI and Soniox expose end-of-turn confidence and endpoint sensitivity. Except for Deepgram's guidance, all of these are framed around early LLM generation, not early retrieval specifically.

### Cited Findings

**Deepgram Flux (STT with built-in turn detection): EagerEndOfTurn / TurnResumed**
- Setting `eager_eot_threshold` (valid 0.3–0.9, default unset, so eager mode is off) enables the `EagerEndOfTurn` and `TurnResumed` events. It must be less than or equal to `eot_threshold`, or the API returns an error — [Deepgram Flux End-of-Turn Configuration](https://developers.deepgram.com/docs/flux/configuration) (snippet)
- Purpose: start "LLM processing on medium-confidence transcripts" before a high-confidence `EndOfTurn`. The recommended workflow is:
  - On `EagerEndOfTurn`, send the transcript to the LLM and treat the output as a draft.
  - On `TurnResumed` (a "cancellation signal"), discard the draft.
  - On `EndOfTurn`, finalize and deliver. "The transcript in EagerEndOfTurn will exactly match the transcript in the subsequent EndOfTurn event (if no TurnResumed occurs)", so a draft built on the eager transcript can be reused without change.

  Source: [Deepgram: Flux voice agent eager EOT guide](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- Claimed benefit: overlapping LLM generation with user speech can "cut hundreds of milliseconds from your agent's response time." Elsewhere the same guide puts the gain at trimming "that last 100-200ms." Stated cost: "50-70% more LLM calls." Mitigations offered: smaller models for drafts, the full LLM only on `EndOfTurn`, and caching drafts — [Deepgram eager EOT guide](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- The guide explicitly says eager processing is most valuable for pipelines with "complex RAG (Retrieval-Augmented Generation) or Function Calling", because those are slow and expensive — [Deepgram eager EOT guide](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- Telnyx resells Flux with the same parameter ("Deepgram Flux only"). It quotes about 150–250 ms latency savings for about 50–70% more LLM calls in the typical 0.3–0.5 threshold range. This is a third-party figure — [Telnyx end-of-turn parameters](https://developers.telnyx.com/docs/voice/stt/websocket-streaming/parameters/end-of-turn) (snippet)

**ElevenLabs Agents Platform: `speculativeTurn`, `turnEagerness`**
- The official JS SDK type `TurnConfig` (v2.39.0) contains:
  - `speculativeTurn`: "When enabled, starts generating LLM responses during silence before full turn confidence is reached, reducing perceived latency. May increase LLM costs."
  - `turnEagerness`: "Low = less eager (waits longer), Standard = default eagerness, High = more eager (responds sooner)".
  - Also `spellingPatience`, and `softTimeoutConfig`, which "Provides immediate feedback during longer LLM responses."

  Source: [ElevenLabs JS SDK TurnConfig.d.ts](https://cdn.jsdelivr.net/npm/@elevenlabs/elevenlabs-js@2.39.0/api/types/TurnConfig.d.ts)
- An ElevenLabs blog describes speculative turn-taking as a feature of "Eleven v3 Conversational" that pre-triggers LLM generation during user silence. It says the turn-taking model is on by default when v3 Conversational is the TTS model — [ElevenLabs blog: interaction models](https://elevenlabs.io/blog/interaction-models-for-natural-human-ai-communication) (snippet only; a direct fetch returned 404, so the wording is unverified)
- Nothing in the SDK comment says whether knowledge-base retrieval also runs speculatively under `speculativeTurn`. The wording covers "LLM responses" only.

**OpenAI Realtime API: `semantic_vad` with `eagerness`**
- `turn_detection.type = "semantic_vad"` uses a classifier that scores the probability that the user is done speaking, based on the words spoken. `eagerness` takes `low`, `medium`, `high` or `auto` (`auto` equals `medium`). `high` responds sooner, or in transcription mode returns transcription events faster. `low` lets users speak uninterrupted for longer — [OpenAI Realtime VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad) (snippet)
- This setting changes when the model commits a turn. It is not a speculative or draft mechanism: there is no documented "draft response, then cancel" event pair like Deepgram's. Inference from the docs above. `create_response` and `interrupt_response` give apps control over whether a response starts automatically — [OpenAI Realtime VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad) (snippet)

**Microsoft Azure Voice Live API**
- Turn detection options include `server_vad`, `azure_semantic_vad` and `azure_semantic_vad_multilingual`, plus a semantic end-of-utterance (EOU) block. One sample config shows `timeout: 2` (seconds) and `threshold: 0.01` — [Microsoft Learn: Voice Live evaluate](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-voice-live-evaluate) (snippet)
- No speculative or eager event was found.

**AssemblyAI Universal-Streaming**
- Every streaming message carries `end_of_turn_confidence`. The semantic end-of-turn threshold defaults to 0.4 and is user-configurable: 0 forces end of turn as soon as silence is detected, and 1 relies on the `max_turn_silence` window. Partial turns carry rising confidence values. The docs say to rely only on `end_of_turn: true`, not `turn_is_formatted`, to detect turn completion — [AssemblyAI turn detection docs](https://www.assemblyai.com/docs/streaming/turn-detection) (snippet)
- AssemblyAI does not document a dedicated "eager" event. Developers could threshold `end_of_turn_confidence` on partials to start work early, but this is inference, not documented guidance. The docs also vary in which model they name: Universal-3.5 Pro, `universal-streaming-english`/`multilingual`, and `u3-rt-pro` in Pipecat — [AssemblyAI real-time API reference](https://www.assemblyai.com/docs/api-reference/real-time); [Pipecat AssemblyAI models source](https://reference-server.pipecat.ai/en/latest/_modules/pipecat/services/assemblyai/models.html) (snippet)

**Soniox**
- Endpoint detection has tunable latency adjustment, endpoint sensitivity and maximum delay. Higher latency-adjustment levels return endpoints sooner, at the cost of more segmentation. Soniox says it combines acoustic and conversational signals, which is "More than a silence timeout" — [Soniox endpoint detection docs](https://soniox.com/docs/stt/core-concepts/endpoint-detection); [Soniox semantic endpoint detection](https://soniox.com/speech-to-text/features/turn-detection) (snippet)
- No eager or draft event was found.

**Sierra (custom VAD)**
- "We trained a custom voice activity detection (VAD) model optimized for noisy, multi-speaker environments... It predicts speech completion earlier and more accurately than off-the-shelf alternatives," which the post says cuts reaction lag "by hundreds of milliseconds" — [Sierra blog: Voice latency (Oct 9, 2025)](https://sierra.ai/blog/voice-latency)

**Adjacent open-source frameworks (outside this note's scope, for context)**
- LiveKit Agents documents "preemptive generation": it speculatively starts the LLM before end of turn is confirmed, and TTS waits unless preemptive TTS is enabled. It warns this "increases LLM token usage" and pays off less for long utterances — [LiveKit agent speech docs](https://docs.livekit.io/agents/multimodality/audio/) (snippet)
- A 2026 LiveKit PR fixed a case where a formatting-only change to the transcript cancelled the preemptive reply and triggered a redundant second LLM request — [livekit/agents PR #7991](https://github.com/livekit/agents/pull/7991) (snippet)

### Inferences
- Explicit early-start primitives fall into two groups:
  - Event-based speculative drafting: Deepgram Flux `EagerEndOfTurn`/`TurnResumed`, and ElevenLabs `speculativeTurn`.
  - Faster commit tuning: OpenAI `semantic_vad` eagerness, Azure semantic EOU, AssemblyAI confidence threshold, Soniox sensitivity, ElevenLabs `turnEagerness`.
- Deepgram's design makes speculation cheap to reuse because the eager transcript is guaranteed to equal the final transcript when no `TurnResumed` follows. That property also makes it safe to start retrieval on `EagerEndOfTurn` and reuse the results. Deepgram's own guide points at RAG as the target use case.
- The reported cost of eager processing, 50–70% more LLM calls, would apply in the same way to speculative retrieval calls. Retrieval is usually far cheaper than LLM calls, so speculative retrieval is plausibly the more cost-effective place to speculate. This is an inference, not a vendor claim.

### Gaps
- No primary source was found for Deepgram's Voice Agent API (the hosted STT+LLM+TTS agent). I could not confirm whether it uses Flux eager EOT internally to speculatively call functions or retrieval.
- The direct Deepgram eager-EOT doc URL (`/docs/flux/eager-eot`) returned 404, so the llms.txt version was used. The feature launch date was not confirmed; Flux launched around late 2025, per training knowledge, unverified here.
- The ElevenLabs `speculativeTurn` launch date and its interaction with RAG were not confirmed.
- I did not check whether the OpenAI Realtime API or Gemini Live expose interim-transcript events usable for app-side speculation during speech-to-speech sessions.

## Q2. Platform knowledge base / RAG features: how and when retrieval is triggered

### Takeaway
Hosted agent platforms trigger retrieval in one of two ways: automatically on every user turn after the final transcript (ElevenLabs "Every turn", Vapi's custom KB), or as a model-chosen tool call (ElevenLabs "On demand", Vapi's Gemini-backed query tool, OpenAI Realtime function and remote MCP tools, Nova Sonic toolUse, Gemini Live tools). None of the platform docs I read describe retrieval running on partial or interim transcripts. Sierra is the one vendor that publicly describes speculative or parallel retrieval in its runtime.

### Cited Findings

**ElevenLabs Agents Platform**
- Retrieval mode has three settings: "Every turn" searches the KB on every turn, "On demand" lets the agent decide, and "Prompt only" turns retrieval off. The query is "analyzed and reformulated for optimal retrieval" before embedding.
- The example embedding model is `e5_mistral_7b_instruct`. Example limits: `max_vector_distance` 0.6, `max_retrieved_rag_chunks_count` 20, `max_documents_length` 10k–50k.
- Each document is set to "Auto" (retrieved when relevant) or "Prompt" (always in the system prompt). Documents under 500 bytes go into the prompt. The page does not describe any preemptive or speculative retrieval.

  Source: [ElevenLabs RAG docs](https://elevenlabs.io/docs/agents-platform/customization/knowledge-base/rag)

**Vapi**
- After Trieve was sunset (Nov 1, per community; Trieve is being acquired by Mintlify), Vapi's migration guide compares two options. A custom KB is "Queried on every user message" with "Lower (direct database query)" latency. The Google KB is "Called as tool when needed by assistant" with "Higher (Google Gemini model processing)" latency. The guide advises keeping files under 300KB — [Vapi: Migrating from Trieve](https://docs.vapi.ai/knowledge-base/migrating-from-trieve); [Vapi community: Trieve sunset](https://vapi.ai/community/m/1405534522275139648) (snippets)
- Vapi aborted Trieve retrievals after a 750 ms wait ("Waited for 750 ms"). Staff said the timeout cannot be increased — [Vapi support thread](https://support.vapi.ai/t/28554757/knowledge-base-retrieval-aborted-request-took-too-long-waite) (snippet)

**Retell AI**
- The call latency breakdown includes a `knowledge_base` field: "Knowledge base retrieval latency from triggering retrieval to receiving all relevant context. Only populated when the agent uses the knowledge base feature." End-to-end latency is measured "from when the user stops speaking until the AI agent begins responding" — [Retell docs: check actual latency](https://docs.retellai.com/reliability/check-actual-latency.md) (snippet)
- A third-party agency says that when multiple KBs are linked to an agent, all of them are searched on each retrieval — [Waboom blog (June 2025)](https://www.waboom.ai/blog/the-rag-powered-voice-agent-how-retell-ai-elevates-knowledge-retrieval) (snippet, third-party)

**OpenAI Realtime API (gpt-realtime / gpt-realtime-2.x)**
- Two tool types are available:
  - Function tools, which the client executes.
  - Remote MCP tools, which "are executed by the Realtime API itself." These take `server_label`, `server_url` or `connector_id`, plus `allowed_tools` and `require_approval`.

  Docs examples use `gpt-realtime-2.1`. `connector_id` is deprecated for models released after Sept 1, 2026. Apps can wait for `mcp_list_tools.completed` before a turn that needs the tools. Remote servers "don't automatically receive the full conversation context" — [OpenAI Realtime with tools (MCP) guide](https://developers.openai.com/api/docs/guides/realtime-mcp) (snippet)
- Retrieval is therefore model-initiated (a tool call after the turn is committed). No hosted `file_search` tool for Realtime turned up in my searches.

**Google Gemini Live API (Vertex AI)**
- Built-in Live tools: function calling, code execution, grounding with Google Search, and grounding with Vertex AI RAG Engine (Preview) — [Vertex AI Live API tools](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api) (snippet)
- A third-party guide names `gemini-3.1-flash-live-preview` as the current recommended model. It also notes Gemini 2.5 cannot combine native Google Search grounding with function tools — [third-party Gemini Live skill](https://www.skills.sh/xiaolai/gemini-skills/gemini-live-api-dev) (snippet, third-party)

**AWS Amazon Nova Sonic**
- Nova Sonic supports tool use, RAG and agentic flows natively over its bidirectional stream. Tools are defined at `promptStart`, and the model emits `toolUse` events. The v1 docs point to a separate Nova 2 Sonic guide — [AWS Nova docs: Tool use, RAG, agentic flows](https://docs.aws.amazon.com/nova/latest/userguide/speech-tools.html) (snippet)
- RAG is typically done by wrapping a Bedrock Knowledge Base `Retrieve` call as a tool — [CloudThat blog](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai) (snippet, third-party)
- A third party claims Nova 2 Sonic has "asynchronous tool use", so the agent doesn't go silent while fetching records — [CloudVisor](https://cloudvisor.co/?p=61329) (snippet, third-party, unverified with AWS)
- A single aggregator says Nova 2.5 Sonic went GA on Oct 5, 2026 — [llmreference.com](https://www.llmreference.com/model/nova-2-5-sonic/aws-bedrock) (unverified; treat with caution)

**Microsoft Azure Voice Live + Foundry Agent Service**
- Microsoft describes the flow as: user speaks, audio streams through Voice Live, the Agent Service reasons and calls tools, then "executes workflows or retrieves knowledge". Retrieval happens in the agent hop after transcription. Existing Foundry agents can be voice-enabled without code changes to the agent — [Microsoft Tech Community: voice-native agents in Foundry (public preview)](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/public-preview-voice-native-agents-in-microsoft-foundry/4502756) (snippet)

**Sierra (speculative and parallel runtime)**
- See Q3 for the quotes.

**Cartesia Line**
- The Line SDK is "reasoning agnostic" (works with any LLM or agent) and advertises "event-driven design to easily define multi-agent architectures with powerful background reasoning", with a "Background reasoning" example (`examples/sales_with_leads/`). No Line-specific KB or RAG feature was found — [cartesia-line on PyPI (0.1.2)](https://pypi.org/project/cartesia-line/0.1.2/) (snippet)

**Hume EVI**
- EVI 3 is claimed to respond in under 300 ms "on state-of-the-art hardware", with caveats about network and implementation. No KB or RAG details were found — [Hume: Introducing EVI 3](https://hume.ai/blog/introducing-evi-3) (snippet)

### Inferences
- The industry default is post-turn retrieval: either every turn, using the final transcript, or as a tool call the LLM picks. The latency of the "every turn" mode sits directly on the critical path after end of turn. Tool-call mode adds a further LLM round trip, so the two modes are roughly "lower latency, always pay" versus "higher latency, pay only when needed".
- Speech-to-speech APIs (OpenAI Realtime, Gemini Live, Nova Sonic, Azure Voice Live) all expose retrieval only as model-initiated tools. This architecture makes app-side speculative retrieval hard: the app does not control when the model decides to call a tool. One workaround would be prefetching and injecting context into the session before the turn ends. That is an inference; I found no vendor docs describing it.

### Gaps
- No primary documentation was found for these platforms' KB/RAG behavior: Bland AI, Synthflow, PolyAI, Decagon, Speechmatics Flow, Inworld, Layercode, Rime, Cartesia (beyond the SDK blurb). The searches returned competitor marketing or nothing relevant.
- I did not confirm whether OpenAI Realtime supports a hosted `file_search` tool. Training knowledge suggests it does not, as of mid-2026, but this is unverified.
- The Nova 2 Sonic guide was not fetched directly.

## Q3. Does any platform explicitly advertise speculative/preemptive RAG?

### Takeaway
Only two vendor sources explicitly put retrieval inside a speculative or parallel pattern. Sierra's engineering blog (Oct 2025) describes running retrieval "in parallel and speculatively" with predictive prefetching. Deepgram's Flux guide recommends eager end-of-turn for "complex RAG ... or Function Calling" pipelines. No hosted voice-agent platform I checked (ElevenLabs, Vapi, Retell and others) advertises a speculative-RAG product feature. ElevenLabs' `speculativeTurn` covers LLM generation only.

### Cited Findings
- Sierra: "Running agent tasks in parallel and speculatively (rather than sequentially)". Also: "Independent tasks — abuse detection, retrieval, API calls — run in parallel, synchronizing only when dependencies require it." And: "Predictive prefetching. The runtime precomputes the likely next steps." Example: when a known customer calls, their order data loads immediately so "Where's my package?" can be answered instantly. Other tactics in the post: hedging requests across multiple model providers ("fastest valid response wins"), precomputed common phrases, and context-aware interim responses ("Let me pull up your order details"). The post gives no exact figures. Authors: Wenqi Shao and Danny Lee, published Oct 9, 2025 — [Sierra blog: Voice latency](https://sierra.ai/blog/voice-latency)
- A secondary summary of a Sierra talk describes speculative retrieval more concretely: "The agent might begin retrieving knowledge from a database simultaneously while a smarter model reasons about whether that retrieval is even necessary... otherwise, the speculative work is discarded" — [ZenML LLMOps database summary of Sierra](https://www.zenml.io/llmops-database/building-production-ai-agents-with-advanced-testing-voice-architecture-and-multi-model-orchestration) (secondary source; not Sierra's own text)
- Deepgram: eager EOT is suited to workflows with "complex RAG (Retrieval-Augmented Generation) or Function Calling" — [Deepgram eager EOT guide](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt)
- ElevenLabs `speculativeTurn` speculates on "LLM responses during silence". It says nothing about retrieval — [ElevenLabs TurnConfig.d.ts](https://cdn.jsdelivr.net/npm/@elevenlabs/elevenlabs-js@2.39.0/api/types/TurnConfig.d.ts)
- Decagon's public latency story (via Together AI) is about model serving: "p95 model latency per turn ... under 400ms" on inputs up to tens of thousands of tokens, with speculative decoding as a central lever and about 6x lower cost than GPT-5 mini. This is speculative decoding, not speculative retrieval — [Together AI customer story: Decagon](https://together.ai/customers/decagon) (vendor case study)
- Research analogues, for context (likely covered by the academic-literature researcher):
  - An arXiv paper on streaming RAG for speech-to-speech proposes running retrieval in parallel while the user is still speaking — [arXiv 2510.02044](https://arxiv.org/pdf/2510.02044v1) (snippet)
  - "VoiceAgentRAG" moves retrieval into a background task — referenced via [Sierra search result summary / alphaxiv](https://www.alphaxiv.org/overview/2603.02206) (snippet; unverified attribution)
- Open-source and hobby implementations of speculation on interim transcripts include:
  - A phone-agent PR adding "speculation policy, speculative generation, commit-or-cancel logic, and per-turn speculation metrics" — [nolanmak/Jarvis PR #1567](https://github.com/nolanmak/Jarvis/pull/1567) (snippet)
  - A recipe that compares interim and final transcripts by similarity and discards divergent early replies — [Beluga AI recipe](https://beluga-ai.org/docs/recipes/voice/voice-preemptive-gen/) (snippet)

### Inferences
- "Speculative RAG" as an advertised, toggleable product feature does not appear to exist on mainstream voice-agent platforms as of Nov 2026, based on the sources searched. It appears instead as an internal runtime technique (Sierra) or a developer-built pattern on top of eager turn events (Deepgram, LiveKit).
- Sierra's "predictive prefetching" (loading caller data on call start) is a form of anticipatory retrieval keyed on session context rather than partial speech.

### Gaps
- I could not confirm whether Sierra's speculative retrieval is triggered by partial user speech or by conversational state (decision-model parallelism). The blog text is ambiguous, and the ZenML summary suggests the latter.
- PolyAI, Decagon and Bland engineering blogs on retrieval latency were not found.

## Q4. What RAG latency numbers do platforms publish?

### Takeaway
Published RAG-specific numbers are scarce. ElevenLabs says "around 250ms". Vapi enforced a 750 ms retrieval timeout with Trieve. Trieve claimed a maximum of 200 ms. Retell exposes per-call `knowledge_base` latency but publishes no typical figure. Practitioner reports for tool-based RAG on speech-to-speech models are much worse: 2–5 s for Nova Sonic + Bedrock KB, and about 10 s for Vapi's Gemini query tool on a large KB.

### Cited Findings
- **ElevenLabs:** "RAG adds on slight latency to the response time of your agent, around 250ms." — [ElevenLabs RAG docs](https://elevenlabs.io/docs/agents-platform/customization/knowledge-base/rag) (documented vendor claim; no methodology)
- **Trieve (Vapi's former KB backend):** claims a "maximum of 200ms" added latency — [Trieve Vapi integration page](https://www.trieve.ai/integrations/vapi) (vendor marketing, unverified)
- **Vapi:**
  - Trieve retrieval was aborted after "750 ms" — [Vapi support](https://support.vapi.ai/t/28554757/knowledge-base-retrieval-aborted-request-took-too-long-waite) (snippet)
  - One user with about 140 Markdown files reports "~10 seconds" from end of question to response with the Gemini-backed query tool — [Vapi community](https://vapi.ai/community/m/1422970715174342706) (anecdotal, snippet)
- **Retell:** the `knowledge_base` latency metric exists per call, with no typical value published — [Retell docs](https://docs.retellai.com/reliability/check-actual-latency.md). A third-party agency claims each KB lookup adds "roughly 100ms" — [Waboom](https://www.waboom.ai/blog/the-rag-powered-voice-agent-how-retell-ai-elevates-knowledge-retrieval) (unsourced estimate)
- **Nova Sonic + Bedrock KB:** about 2–5 s per KB lookup in one team's build. They inject filler speech while the tool runs — [CloudThat](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai) (single practitioner report). The figure of under 500 ms for Nova 2 Sonic overall comes from a third party and is unverified — [CloudVisor](https://cloudvisor.co/?p=61329)
- **OpenAI Realtime, Gemini Live, Azure Voice Live:** no published retrieval-latency figures were found. A community thread reports high MCP latency, but that thread is about ChatGPT Apps, not Realtime — [OpenAI community](https://community.openai.com/t/high-latency-when-calling-mcp/1363314) (snippet)
- **Overall platform latency claims (not RAG-specific):** These numbers come from a competitor (Retell), so expect bias — [Retell blog: Bland vs Synthflow](https://www.retellai.com/blog/bland-vs-synthflow) (snippet):
  - Synthflow: about 400–500 ms on defaults. The low-latency edge is a $0.04/min add-on.
  - Bland: "claimed sub-400ms (Turbo), measured 700ms to 1,500ms".
  - Retell: about 620–800 ms.
- Other overall-latency claims:
  - GetVoIP puts Bland at about 800 ms and Synthflow at under 500 ms — [GetVoIP](https://getvoip.com/blog/bland-ai-vs-synthflow/) (snippet)
  - Hume EVI 3 claims under 300 ms — [Hume](https://hume.ai/blog/introducing-evi-3)
  - Decagon claims p95 model latency per turn under 400 ms — [Together AI](https://together.ai/customers/decagon)
- **Deepgram:** eager EOT saves "hundreds of milliseconds" or "100-200ms", at "50-70% more LLM calls" — [Deepgram](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot/llms.txt). Telnyx quotes 150–250 ms saved — [Telnyx](https://developers.telnyx.com/docs/voice/stt/websocket-streaming/parameters/end-of-turn) (snippet)

### Inferences
- Documented in-platform vector RAG (ElevenLabs, Trieve) costs about 200–250 ms. Tool-call RAG through an extra LLM or managed-search hop can cost seconds. The 100–250 ms that eager or speculative turn handling saves is about the same size as typical in-platform RAG overhead. Speculation could therefore plausibly hide in-platform RAG cost entirely, though not multi-second tool-based RAG. This is an inference.

### Gaps
- None of the vendors published p50/p95 RAG-latency distributions or benchmarks with a stated methodology.
- No RAG latency figures were found for PolyAI, Synthflow, Bland, Speechmatics Flow, Inworld, Layercode, Rime, Cartesia or Soniox.

## Q5. Contact-center products that retrieve knowledge proactively from live call transcripts

### Takeaway
Contact-center agent-assist products are the most mature commercial form of "anticipatory retrieval during speech". Google Agent Assist's Proactive Generative Knowledge Assist and Amazon Q in Connect both listen to the live transcript and push knowledge suggestions without a query. Google's is configurable to trigger on each customer message, each agent message, or END_OF_UTTERANCE. Amazon Q in Connect detects intents from Contact Lens real-time analytics. Both trigger per utterance, not mid-utterance.

### Cited Findings
- **Google Agent Assist, Proactive Generative Knowledge Assist (PGKA)**
  - Follows the ongoing conversation and generates knowledge suggestions from both agent and customer dialogue. Suggestions appear as clickable tiles — [Google CCAI Platform: Agent Assist](https://docs.cloud.google.com/contact-center/ccai-platform/docs/agent-assist) (snippet)
  - `suggestion_trigger_event` defaults to `CUSTOMER_MESSAGE`. The other options are `AGENT_MESSAGE` and `END_OF_UTTERANCE` ("the feature detects the end of a user utterance").
  - `disable_query_search_context` controls whether search context is used. A "Load proactive answers asynchronously" console option returns query suggestions only.

  Sources: [Google Agent Assist: PGKA docs](https://docs.cloud.google.com/agent-assist/docs/pgka) (snippet)
  - Release notes:
    - PGKA V2 is GA, with "rich search context, multiple suggested queries, and granular control over triggering events" (date not confirmed).
    - Pub/Sub intermediate transcription entered preview in December 2024.
    - Gemini Transcribe Live entered preview on Sept 1, 2026.

    Sources: [Agent Assist release notes](https://docs.cloud.google.com/gemini-enterprise-cx/agent-assist/release-notes) (snippet)
  - Developers use the `BiDiStreamingAnalyzeContent` API to stream audio and get back transcripts or suggestions — [Agent Assist release notes](https://docs.cloud.google.com/agent-assist/docs/release-notes) (snippet)
- **Amazon Q in Connect** (formerly Amazon Connect Wisdom)
  - "Automatically detects customer intent during calls and chats using conversational analytics and natural language understanding (NLU)".
  - It "proactively generates clickable intents". When the agent picks an intent, it generates a cited solution from the configured KB.
  - Voice requires Contact Lens conversational analytics.
  - Launched in Nov 2023 in us-east-1, us-west-2, Sydney, Tokyo, Frankfurt and London (region list may be outdated).

  Sources: [AWS admin guide: Amazon Q in Connect](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-q-connect.html); [AWS What's New, Nov 2023](https://aws.amazon.com/about-aws/whats-new/2023/11/amazon-q-connect-generative-ai-powered-agent-assistance-real-time) (snippets)

### Inferences
- Agent-assist products trigger on each finalized utterance or message. This is anticipatory with respect to the *agent's* next turn, since the agent hasn't asked anything, but not with respect to the *speaker's* current utterance. Google's `END_OF_UTTERANCE` option is the closest to voice-agent turn-end triggering.
- These products prove out "retrieve from live transcript without an explicit query" at enterprise scale. A human agent reads the suggestions, so latency tolerance (seconds) is far looser than in a voice bot.

### Gaps
- NICE (CXone Copilot / Enlighten) and Genesys (Agent Copilot) were not researched within the tool budget. Both are believed to offer real-time knowledge surfacing, but that is unverified.
- No published latency figures were found for Google PGKA or Amazon Q in Connect suggestions.
