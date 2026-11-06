# Architectural threat to forehear from speech-to-speech (S2S) and full-duplex voice models (as of 2026-11-06)

Context: forehear (this repo) runs retrieval speculatively on *interim* streaming-ASR transcripts so results are ready at end of turn, with Pipecat and LiveKit adapters (see /home/user/Infinity/README.md). The threat studied here: end-to-end S2S models that take audio in and give audio out may leave the app without interim transcripts or any control over when retrieval runs.

Research note: about 18 tool calls. Primary sources are vendor docs, two arXiv papers, and one forum thread. Most "market share" material is vendor or consultancy blogs with a commercial stake, so it is flagged as opinion. Several model and product names that appear in Nov-2026 docs (gpt-realtime-2.1, gemini-3.8-live, gpt-live-transcribe, gpt-realtime-whisper, gemini-3.5-transcribe-live) are newer than my training data. I report them as the fetched pages give them and did not cross-check them.

## Q1. What share of production voice agents in 2026 are cascaded vs S2S, and why?

### Takeaway
No source gives a measured, neutral production share. Every source found says cascaded STT→LLM→TTS is still the production default in 2026. The only number is an unverified "~90% of LiveKit production agents are cascaded" from a dev shop. The reasons given are observability and debugging, instruction following, tool and RAG reliability, compliance transcripts, and cost predictability. S2S is growing: Vapi launched an S2S beta in Oct 2026, and hybrid S2S-front plus cascade-back designs are emerging. On benchmarks, S2S is now faster and, for top models, more accurate on tool use than a naive cascade.

### Cited Findings
**Share and trend claims (all opinion or vendor positions, none measured)**
- "Cascade remains the production default for most voice agent workloads." Deepgram blog, 2026-05-21. Deepgram sells cascade components and a bundled cascade Voice Agent API. — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture)
- Gradium (founded by ex-Kyutai/Moshi people, now selling STT/TTS cascade components) says cascade "dominates production deployments in 2026" and that S2S "exists at the research and prototype stage". Published 2026-05-27, updated 2026-09-10. It gives typical production cascade latency as 1.5–3 s and STT median time-to-first-token (Coval, May 2026) as 992 ms (Deepgram Nova-3) to 2,080 ms (ElevenLabs Scribe v2). — [Gradium](https://gradium.ai/content/cascaded-voice-agent-vs-speech-to-speech-2026)
- "About 90% of LiveKit production agents still run a cascaded STT→LLM→TTS pipeline in 2026." This comes from Forasoft, a development agency. It is unverified and has no methodology. Forasoft also describes a hybrid in which S2S handles greetings and small talk and a pipeline handles tool calls. — [Forasoft](https://www.forasoft.com/blog/article/livekit-ai-agents-guide)
- Vapi announced a speech-to-speech beta alongside its modular pipeline on 2026-10-02. This is a secondary report. — [Blockchain.News](https://blockchain.news/news/vapi-livekit-retell-pipecat-voice-agent-stack-production)
- Retell offers S2S options (OpenAI gpt-realtime models) and a standard LLM pipeline. — [Retell](https://www.retellai.com/blog/best-speech-to-speech-ai-apis-phone-calls)
- AssemblyAI calls native duplex models a research and roadmap direction, not something to build on yet. Coval says S2S is "catching up". Modulate, by contrast, says the industry is moving toward S2S while arguing that cascade is better for enterprise. — [AssemblyAI](https://www.assemblyai.com/blog/speech-to-speech-for-voice-agents); [Coval](https://www.coval.ai/blog/voice-ai-agents-architecture-deployment-evaluation/); [Modulate](https://www.modulate.ai/ebooks/beat-the-black-box-why-cascade-beats-speech-to-speech-for-enterprise-voice-agents)
- Hybrid pattern: run S2S for the live turn and send the same audio through a cascaded ASR pass in parallel for logging and evaluation. — [Superteams](https://www.superteams.ai/courses/building-voice-ai-agents-in-production/03-cascaded-vs-native-speech-to-speech/)
- One source recommends cascade for agents with 5+ tools and strict schemas, and S2S for simpler agents. Seen only as a search snippet. — [FutureAGI](https://futureagi.com/blog/cascaded-voice-ai-vs-speech-to-speech-2026/)
- Daily's CTO says the cascade's main advantage is observability, not latency. — [WebRTC.ventures](https://webrtc.ventures/2026/01/watch-webrtc-live-109-agentic-workflows-that-work-in-production/)
- Market structure: Deepgram is acquiring Daily, the company behind Pipecat (reported 2026-10-30). — [audioXpress](https://audioxpress.com/news/deepgram-acquires-daily-to-build-open-conversational-voice-ai-platform-around-pipecat)

**Reasons given**
- Controllability and debugging: engineers "specifically cite monitoring, debugging, and instruction-following as weaker in S2S APIs today". S2S failures are often silent, for example interruption race conditions and VAD misconfiguration on 8 kHz telephony. — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture)
- Tool reliability: S2S supports function calling, "but support isn't the same as reliability". — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture)
- Cost: token-billed S2S costs "can reach 4x theoretical minimums" because the OpenAI Realtime API re-sends the full conversation history each turn. — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture)
- Compliance: compliance teams treat transcripts as audit artifacts under HIPAA audit controls, SOC 2 and NIST AI RMF. Cascade produces them as a by-product, while S2S "needs a parallel transcription layer". — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture)
- For cascade, Gradium cites swappable LLMs, standard prompting, function calling and RAG, CRM and DB integration, and vendor SLAs. For S2S it cites no stacked latency, preserved paralinguistics and full duplex. — [Gradium](https://gradium.ai/content/cascaded-voice-agent-vs-speech-to-speech-2026)
- Robustness claim: a March 2026 benchmark reportedly found S2S agents completed only 26–38% of tasks with background noise and accents. This is second-hand and the original was not found. — [JustCall](https://justcall.io/blog/speech-to-speech-vs-cascaded-voice-agents.html)

**Counter-evidence: S2S is faster, and top models are more accurate on tool use, than a naive cascade**
- Full-Duplex-Bench-v3 (arXiv 2604.04847, Apr 2026) uses real disfluent speech and tool use via LiveKit. Pass@1: GPT-Realtime 0.600, Gemini Live 3.1 0.540, Gemini Live 2.5 0.490, Cascaded (Whisper→GPT-4o→OpenAI TTS) 0.450, Grok 0.430, Ultravox v0.7 0.410. The paper concludes that end-to-end models are "significantly faster" than cascaded pipelines. — [FDB-v3](https://arxiv.org/html/2604.04847v1)

### Inferences
- Cascaded pipelines, the setting forehear targets, probably still carry most production enterprise traffic in late 2026. The evidence is soft but consistent, and it is consensus opinion rather than measurement. The trend points toward more S2S. Every major orchestrator (LiveKit, Pipecat, Retell, and now Vapi) supports both, so switching costs for end customers are falling.
- Deepgram's acquisition of Daily/Pipecat puts a cascade-component vendor in charge of one of forehear's two integration targets. In the short term that probably strengthens Pipecat's cascade path. It also means Deepgram may build eager or speculative features natively.
- FDB-v3's cascade baseline is weak: Whisper, which is not streaming, and no eager end-of-turn. So "S2S beats cascade" on that benchmark does not settle the question for an optimized streaming cascade, which is what forehear assumes.

### Gaps
- No neutral survey or telemetry on cascade vs S2S call share (LiveKit, Pipecat, Vapi, Retell, a16z) was found. A Daily/Pipecat "state of voice AI" report was not located. The a16z voice reports were not searched.
- The Hamming AI "4M+ production calls" analysis that Modulate cites could not be verified.
- No public per-minute price comparison of gpt-realtime vs a typical cascade was retrieved.

## Q2. How do S2S and full-duplex models do knowledge grounding (tools, MCP, file search, RAG engines, "think while listening")?

### Takeaway
In every commercial S2S API reviewed, knowledge grounding works through model-initiated tool calls. Built-in options are limited: Google Search on Gemini Live, and server-executed remote MCP on OpenAI Realtime. No built-in file search was confirmed on any S2S API. The model decides when to retrieve, and that decision normally comes after it has heard enough of the user's speech, so retrieval latency adds to the turn. Research systems (MoshiRAG, NVIDIA frontend-backend delegation) add asynchronous retrieval triggers to full-duplex models, which partly removes the bottleneck forehear addresses.

### Cited Findings
**OpenAI Realtime (gpt-realtime family)**
- Function-calling flow: the model emits a `function_call` item with `name`, `arguments` and `call_id`. The app replies with `conversation.item.create` of type `function_call_output` using the same `call_id`, then sends `response.create`. Apps can also add arbitrary items with `conversation.item.create`, and can create out-of-band responses with `response.create` and `response.conversation: "none"`. Models named in the guide: `gpt-realtime-2.1`, `gpt-realtime-2`, `gpt-realtime`. — [OpenAI Realtime conversations guide](https://developers.openai.com/api/docs/guides/realtime-conversations)
- Remote MCP: the tool is `type: "mcp"` with `server_label` and `server_url` (or a `connector_id`, deprecated for models released after 2026-09-01; `tunnel_id` reaches local servers). Optional fields: `allowed_tools`, `require_approval`, `headers`, `authorization`. "remote MCP tools are executed by the Realtime API itself", so the client never sees or returns a `function_call_output`. Error events: `mcp_list_tools.failed` and `response.mcp_call.failed`. These details come from search snippets of the guide; the full page was not read. — [OpenAI Realtime with tools (MCP)](https://developers.openai.com/api/docs/guides/realtime-mcp)
- The conversations guide does not mention a built-in file search or retrieval tool for Realtime. — [OpenAI Realtime conversations guide](https://developers.openai.com/api/docs/guides/realtime-conversations)

**Google Gemini Live API**
- Supported tools, per the Live API tools page as fetched: Google Search grounding on 3.8 Live, 3.8 Live Extended Thinking, 3.1 Flash Live Preview and 2.5 Flash Live Preview. Function calling: "Sync and async" (3.8 Live), "Async only" (3.8 Live Extended Thinking), "Sync only" (3.1 Flash Live), "Sync and async" (2.5 Flash Live). Google Maps, code execution and URL context: No. File search and MCP are not mentioned. — [Gemini Live API tools](https://aistudio.google.com/docs/live-api/tools)
- Async tools: a function declared with `behavior: "NON_BLOCKING"` runs without pausing the conversation. Its `FunctionResponse` takes `scheduling` set to `"INTERRUPT"`, `"WHEN_IDLE"` or `"SILENT"`. With `SILENT` the result "is stored for later use without announcing it". Tool responses go through `session.send_tool_response` / `sendToolResponse`, and automatic tool handling is not supported. — [Gemini Live API tools](https://aistudio.google.com/docs/live-api/tools)
- Vertex RAG Engine integration with Live API was not confirmed in this research (see Gaps).

**AWS Nova Sonic**
- "With Amazon Nova Sonic, RAG is implemented through tool use." The example is a `knowledgeBase` tool with a `query` string. The app queries the vector store and returns results as a tool result. Nova 2 Sonic has a separate tool-configuration guide that was not read. — [AWS Nova docs, RAG](https://docs.aws.amazon.com/nova/latest/userguide/speech-rag.html); [AWS Nova docs, tools](https://docs.aws.amazon.com/nova/latest/userguide/speech-tools.html)
- Third-party implementation: Bedrock Knowledge Base lookups "can take several seconds", so the app injects a filler phrase as soon as a tool call is detected. — [CloudThat](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai)

**Azure Voice Live**
- Voice Live bundles speech recognition, a generative model and Azure TTS into one realtime session, and can also use native-voice azure-realtime models. Voice Live with Foundry Agent Service went to public preview in March 2026: the agent reasons, calls tools and retrieves knowledge, then the reply is spoken. Whether the agent path is cascaded or native audio was not established. — [Pipecat docs, Azure Voice Live](https://docs.pipecat.ai/api-reference/server/services/s2s/azure-voice-live); [Microsoft Tech Community](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/public-preview-voice-native-agents-in-microsoft-foundry/4502756); [MS Learn quickstart](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-quickstart)

**Research: full-duplex retrieval and tools**
- MoshiRAG (Kyutai and others, arXiv 2604.12928, ICML 2026): adds a `⟨ret⟩` retrieval trigger token to Moshi. The model keeps speaking "pre-RAG content" while retrieval runs, using "the natural timing gap between response onset and core information". The target is retrieval within 2 s. It improves factuality on Llama Questions, Web Questions, TriviaQA and HaluEval, and lowers takeover rates on Full-Duplex-Bench. Code and weights are reportedly released (kyutai-labs/moshi-rag). — [arXiv 2604.12928](https://arxiv.org/html/2604.12928v2); [ICML poster](https://icml.cc/virtual/2026/poster/66336)
- "A frontend-backend architecture for tool calls in full-duplex speech models" (Hu, Chen et al., arXiv 2609.19334, Sep 2026). The author list matches NVIDIA NeMo researchers, but the abstract page lists no affiliations. A duplex speech-to-text frontend emits a delegation token and streams ASR transcripts to a text backend LLM, which makes the tool calls. Results return via "prefill-and-repeat" and are spoken through streaming TTS. It reports 92–97% tool-call recall and 81.2% correct rejection of irrelevant calls. With a Qwen3-235B-A22B backend it is competitive on FDB-v3, and it "significantly outperforms" gpt-realtime-mini and Qwen3-Omni-30B-A3B on EVA-Bench. The abstract gives no latency numbers. — [arXiv 2609.19334](https://arxiv.org/abs/2609.19334)

### Inferences
- In commercial S2S, retrieval timing belongs to the model: it emits a tool call when it decides to. The app keeps one strong lever, because it executes function tools (OpenAI function tools, Gemini function calling, Nova tools). The app can therefore have the answer ready before the model asks. It loses that lever for OpenAI remote MCP, which runs server-side, and for Gemini Google Search.
- Gemini's `NON_BLOCKING` plus `SILENT` scheduling is an explicit channel for pushing context into a live session without interrupting it. That fits the pattern "retrieve speculatively, then push quietly". This is my reading of the docs, not a documented pattern.
- The NVIDIA-style delegation design is structurally a cascade behind a duplex front end: the backend gets streaming ASR text. That is exactly forehear's input, so forehear-style prefetch would plug into it directly.
- MoshiRAG addresses latency by talking during retrieval. That competes with forehear's value (no dead air) but does not remove it: forehear can make the "post-RAG" content arrive sooner or remove the need for filler.

### Gaps
- Gemini Live + Vertex AI RAG Engine (Vertex `retrieval` tool in Live) was not verified. The AI Studio tools page does not list it.
- Whether OpenAI Realtime offers `file_search` or vector-store tools was not confirmed. The guide does not mention them.
- Hume EVI, Sesame CSM, Ultravox's own tool and RAG model, Step-Audio 2, Qwen3-Omni, MiniCPM-o, GLM-4-Voice and Freeze-Omni were not researched individually, beyond Ultravox and Qwen3-Omni appearing as benchmark subjects. No "think while listening" vendor docs were retrieved.
- Nova 2 Sonic specifics (async tools, AgentCore) were not found.

## Q3. Can speculative or early retrieval apply to S2S? Do S2S APIs expose streaming input transcripts an app could use to prefetch and then inject?

### Takeaway
Partly yes. Both OpenAI and Google expose input-transcription events, and both let the app inject retrieved content (as tool results or conversation items). The timing differs by vendor:
- **Gemini Live** documents `interim_input_transcription`, "speculative partial hypotheses updated while the speaker is actively talking". This is a usable early signal.
- **OpenAI Realtime** documents `conversation.item.input_audio_transcription.delta`, but in speech-to-speech sessions with server VAD, developers report that deltas arrive only after speech stops or commit. That makes them useless for prefetch. OpenAI's newer dedicated streaming model (`gpt-live-transcribe`) streams during speech, but in a separate transcription session.

So forehear could work with S2S by running a parallel streaming ASR or a vendor interim stream, prefetching, and then answering the model's tool call instantly or pre-injecting context. The app cannot shorten the model's own decision of when to call the tool.

### Cited Findings
**OpenAI**
- Event names: `conversation.item.input_audio_transcription.delta`, `.completed` and `.failed`, plus `input_audio_buffer.append`, `input_audio_buffer.commit` and `input_audio_buffer.committed`. `gpt-live-transcribe` "returns transcript deltas as speech arrives and a final transcript when your application commits each audio turn". For `gpt-transcribe`, after "Append audio and send `input_audio_buffer.commit`" the model "can then emit transcript deltas before the final completion event", so its deltas come after the commit. "Ordering between completion events from different speech turns isn't guaranteed." Transcription sessions with `gpt-live-transcribe` use `turn_detection: null`, so client VAD sends the commit. — [OpenAI realtime transcription guide](https://developers.openai.com/api/docs/guides/realtime-transcription)
- Delta payload fields: `event_id`, `type`, `item_id`, `content_index`, `delta`, and optional `logprobs`. — [openai-client-base (Rust)](https://docs.rs/crate/openai-client-base/latest/source/docs/RealtimeBetaServerEventConversationItemInputAudioTranscriptionDelta.md); [Ruby SDK](https://www.rubydoc.info/gems/openai/OpenAI/Models/Realtime/ConversationItemInputAudioTranscriptionDeltaEvent)
- Developer report (Jan–Feb 2026, `gpt-4o-mini-transcribe`, server_vad): "don't get any transcription deltas back until the user stops talking". Observed sequence: speech_started → speech_stopped → burst of deltas → completed. "No transcription is returned until the accumulated audio is deemed ready." Workarounds were frequent manual commits ("awful" accuracy), lower `silence_duration_ms`, `semantic_vad` eagerness high (each "slightly better"), or a separate Whisper with client VAD. There were no staff replies. — [OpenAI Community forum](https://community.openai.com/t/realtime-streaming-transcription/1371205)
- In push-to-talk mode, committing audio will "kick off input transcription (if enabled)". This confirms that in conversation sessions transcription is tied to commit. — [OpenAI Realtime conversations guide](https://developers.openai.com/api/docs/guides/realtime-conversations)
- A streaming model, `gpt-realtime-whisper`, that "returns text while audio is still arriving" is listed as arriving 2026-05-07. This naming conflicts with `gpt-live-transcribe` in OpenAI's own guide; they may be the same or different products. — [Vercel AI Gateway](https://vercel.com/ai-gateway/models/gpt-realtime-whisper); [DataCamp](https://www.datacamp.com/de/tutorial/gpt-live-transcribe-api)
- Injection paths: `conversation.item.create` (any item, including a `function_call_output` matched by `call_id`) and out-of-band `response.create` with `conversation: "none"`. — [OpenAI Realtime conversations guide](https://developers.openai.com/api/docs/guides/realtime-conversations)

**Google**
- Config is `input_audio_transcription` / `inputAudioTranscription`. Results come in `server_content.input_transcription` (final) and `server_content.interim_input_transcription` (interim). Interim = "low-latency, speculative partial hypotheses updated while the speaker is actively talking". Final = "emitted when the speaker pauses, the turn completes, or speech is finalized". Input transcription with `custom_vocabulary` is listed as a feature of the `gemini-3.8-live` agent model. Dedicated model: `gemini-3.5-transcribe-live`. The page does not state whether interim results are emitted in agent (native-audio) sessions as well as transcription sessions. — [Gemini Live transcription docs](https://aistudio.google.com/docs/live-api/live-transcribe)
- Injection: `send_tool_response` with `NON_BLOCKING` + `scheduling: "SILENT"`/`"WHEN_IDLE"`. `send_client_content` is shown only for the initial prompt; mid-session use was not confirmed. — [Gemini Live API tools](https://aistudio.google.com/docs/live-api/tools)

**Is tool and RAG latency still a bottleneck in S2S? (numbers)**
- FDB-v3, Table 6 means (s), first word / tool call / task completion: GPT-Realtime 6.36 / 3.89 / 6.89; Gemini Live 2.5 7.03 / 4.61 / 7.26; Gemini Live 3.1 3.95 / 2.21 / 4.25; Grok 5.97 / 0.63 / 6.65; Ultravox 3.88 / 6.01 / 8.40; Cascaded 8.78 / 3.15 / 10.12. — [FDB-v3](https://arxiv.org/html/2604.04847v1)
- FDB-v3: "Self-correction handling remains the hardest challenge: even GPT-Realtime succeeds on fewer than 59%" (0.588). Failures come from models committing intermediate parameters before a correction arrives. The cascade scores 0.176 on self-correction because Whisper finalizes before the correction. Gemini Live 3.1 shows a "silent worker" pattern: 22% of cases had no speech, and 86% of those still executed tool calls. Turn-take rate is 78.0%. Caveats: 100 recordings, 12 speakers, mock APIs, one region, and network variability included. — [FDB-v3](https://arxiv.org/html/2604.04847v1)
- Nova Sonic + Bedrock KB: lookups "can take several seconds", mitigated with filler speech (third-party). — [CloudThat](https://www.cloudthat.com/resources/blog/rag-powered-voice-assistants-for-grounded-speech-to-speech-ai)
- MoshiRAG targets retrieval within 2 s, so that it fits inside the gap before core content. — [arXiv 2604.12928](https://arxiv.org/html/2604.12928v2)

### Inferences
- In S2S models, time-to-tool-call is still seconds after the end of a disfluent utterance: 2.2–4.6 s for Gemini and GPT-Realtime on FDB-v3, with Grok an outlier at 0.63 s. Task completion is 4–8 s. That leaves room for prefetch. If the tool backend is a retriever, an app that has already retrieved on interim text can return the `function_call_output` / `FunctionResponse` almost immediately, saving the retrieval time (often hundreds of ms to seconds) from each tool round trip. This is inference; I found no published measurement of prefetch on S2S.
- FDB-v3's self-correction finding is relevant to forehear's design. Early commitment to wrong parameters is the main failure mode, which matches forehear's need for stability or revision policies (`stable_prefix`, `adaptive`). Speculative retrieval must be cheap to discard, and it applies to read-only retrieval, not actions, as the README already scopes it.
- On OpenAI, the in-session transcription stream is effectively post-commit, so forehear would need a parallel streaming ASR on the same audio, such as a `gpt-live-transcribe` session or Deepgram. That adds cost and the risk that the transcript diverges from what the S2S model "heard". On Gemini, the `interim_input_transcription` field may provide this natively, if it is emitted in agent sessions; that needs confirmation.
- Prefetch can only save retrieval time. It cannot save the S2S model's own reasoning before and after the tool call. The app also cannot force the model to call the tool. Pre-injecting retrieved context as a conversation item (OpenAI) or a `SILENT` tool response (Gemini) is a possible way around tool-call latency altogether. It is untested, and it costs tokens on every turn.
- The ceiling for forehear on server-executed tools (OpenAI remote MCP, Gemini Google Search) is zero, because the app never sees those calls.

### Gaps
- No official OpenAI statement was found on whether `conversation.item.input_audio_transcription.delta` in a gpt-realtime-2.x speech-to-speech session (as opposed to a transcription session) can stream during speech. The evidence is one forum thread from early 2026 plus the commit-triggered wording in the docs.
- Whether Gemini Live agent sessions emit `interim_input_transcription` or only final `input_transcription` is not stated.
- No measured S2S tool-call latency breakdown separates model decision time from tool execution time. FDB-v3 uses mock APIs, so its "tool call" latency is mostly model-side.
- No one was found publishing or productizing "prefetch on input transcript, then answer the tool call" for S2S. That is absence of evidence from a limited search, not confirmation that nobody has.

## Q4. What does this mean for forehear's addressable market and roadmap?

### Takeaway
S2S is a real but slow-moving threat. The cascaded market forehear targets is still the large majority of production traffic in 2026, though that rests on opinion rather than measurement. The commercial S2S APIs still execute app-side function tools, which leaves a prefetch insertion point. Forehear's position weakens where vendors execute retrieval server-side (MCP, Google Search, possibly RAG Engine), and where duplex models learn their own asynchronous retrieval triggers (MoshiRAG). Hybrid architectures, such as an S2S front end with a cascade or text backend, or NVIDIA-style delegation, look like the most likely future, and those still run on streaming text.

### Cited Findings
- Cascade is the production default according to Deepgram, Gradium and Forasoft (~90% of LiveKit agents, unverified). — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture); [Gradium](https://gradium.ai/content/cascaded-voice-agent-vs-speech-to-speech-2026); [Forasoft](https://www.forasoft.com/blog/article/livekit-ai-agents-guide)
- S2S is available in all major orchestrators, including Vapi (S2S beta, 2026-10-02) and Retell. — [Blockchain.News](https://blockchain.news/news/vapi-livekit-retell-pipecat-voice-agent-stack-production); [Retell](https://www.retellai.com/blog/best-speech-to-speech-ai-apis-phone-calls)
- Top S2S models beat a naive cascade on tool accuracy and latency in FDB-v3. — [FDB-v3](https://arxiv.org/html/2604.04847v1)
- OpenAI remote MCP tools run server-side, so the client never handles them. — [OpenAI Realtime MCP](https://developers.openai.com/api/docs/guides/realtime-mcp)
- The frontend-backend delegation design streams ASR transcripts to a text backend LLM for tool calls. — [arXiv 2609.19334](https://arxiv.org/abs/2609.19334)
- Gemini Live exposes interim speculative transcripts and NON_BLOCKING/SILENT tool responses. — [Gemini transcription](https://aistudio.google.com/docs/live-api/live-transcribe); [Gemini tools](https://aistudio.google.com/docs/live-api/tools)
- Compliance pushes S2S deployments to add a parallel transcription layer. — [Deepgram](https://deepgram.com/blog/speech-to-speech-vs-cascade-voice-agent-architecture); [Superteams](https://www.superteams.ai/courses/building-voice-ai-agents-in-production/03-cascaded-vs-native-speech-to-speech/)

### Inferences (opinion, for the report writer)
- **Addressable market now:** cascaded agents on Pipecat and LiveKit (the current adapters) are probably most production traffic, especially in enterprise and regulated, tool-heavy settings. That is forehear's core market for at least the next 12–24 months. The confidence is moderate, because no measured share exists.
- **Addressable market S2S-adjacent (expandable):** S2S deployments that use app-executed function tools for RAG (OpenAI function tools, Gemini function calling, Nova Sonic `knowledgeBase` tool, LiveKit/Pipecat realtime-model plugins). There, forehear could act as a "tool-result cache": retrieve on a parallel or interim transcript, then answer the tool call instantly. Compliance-driven parallel transcription layers already in S2S stacks could supply the interim text at no extra ASR cost.
- **Not addressable:** server-side tools (OpenAI remote MCP, Gemini Google Search, managed vendor RAG) and fully self-grounded duplex models with internal retrieval tokens (MoshiRAG-style), unless those expose a pluggable retriever. MoshiRAG's backend is "plug-and-play", so forehear could feed it, but forehear would not control timing.
- **Roadmap candidates:**
  1. A "realtime-model" adapter for LiveKit and Pipecat S2S plugins that taps a parallel streaming ASR or the Gemini `interim_input_transcription`, prefetches, and returns cached results on `function_call`.
  2. An optional "pre-inject" mode: `conversation.item.create` (OpenAI) or a `SILENT` tool response (Gemini), with a token-cost accounting.
  3. A benchmark extension that measures tool-call-to-result savings on FDB-v3-style disfluent audio, especially self-corrections.
  4. Positioning for hybrid and delegation architectures (NVIDIA-style), where the backend already consumes streaming ASR text.
  5. Watch Deepgram–Daily (Pipecat) for native speculative features that could absorb forehear's function.
- **Main risk:** vendors move retrieval inside the model or server (Realtime MCP, file search, RAG Engine). Once that happens, the app has no seam, and the competing approach becomes "speak filler while retrieving" (MoshiRAG, Ultravox's speak-before-tool pattern in FDB-v3).

### Gaps
- No data on how many S2S production deployments use app-executed function tools versus server-side MCP or search for knowledge grounding.
- No vendor roadmap statements on built-in file search or RAG for OpenAI Realtime or Gemini Live were found in this pass.
- Cost of running a parallel streaming ASR alongside S2S was not quantified.
