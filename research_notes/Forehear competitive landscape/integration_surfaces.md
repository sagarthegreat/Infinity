# Integration surfaces for forehear beyond Pipecat and LiveKit (verified as of 2026-11-06)

**Scope.** forehear needs three things from a host platform:
- (a) interim or partial user transcripts while the user is speaking;
- (b) optionally, an eager end-of-turn (EOT) signal;
- (c) a way to inject retrieved context before the LLM generates.

This note checks primary API docs (official docs pages, their `.md`/`llms.txt` exports, and AsyncAPI specs) to see which commercial platforms expose these to a developer's server. All pages were fetched on 2026-11-06.

**Tags.** **[V]** means verified from primary docs. Quotes are verbatim. **[I]** means inferred by me. **[U]** means unverified or not documented.

**Scope boundary.** This note does not repeat KB/RAG pricing, latency claims or competitive positioning. Those are in `commercial_platforms.md` and `s2s_threat.md`.

---

## Q1. Which surfaces give partial transcripts DURING speech to the developer's server? (with the full integration-surface matrix)

### Takeaway
**Strong fit.** Only a handful of commercial surfaces document user partials streamed to the developer's server *during* speech:
- Twilio ConversationRelay (`partialPrompts`, Flux-based eager EOT);
- Telnyx Conversation Relay (`last:false` prompts plus `eagerEndOfTurn` and `turnResumed` frames);
- Vapi server messages (`transcript` with `transcriptType:"partial"`), plus its custom-transcriber socket, which hands you the raw audio;
- Gemini Live, but only clearly documented for the dedicated `gemini-3.5-transcribe-live` model.

**Possible fit.**
- Retell's `update_only` "live transcript" is likely an in-turn hook, but the docs do not state that it updates mid-utterance.
- Deepgram's Voice Agent API sends no partials. It does run a documented "speculative window": the LLM request goes to your BYO `think.endpoint`, and function calls are dispatched before the turn is confirmed.

**No partials during speech.**
- OpenAI Realtime in speech-to-speech (S2S) sessions: transcription starts on commit. The streaming model `gpt-live-transcribe` is "Not supported" on `v1/realtime`.
- Nova 2 Sonic: user ASR is `FINAL` only.
- ElevenLabs Agents and Speech Engine: `user_transcript` is "finalized".
- Cartesia Managed Agents: "The user's speech is not streamed incrementally".
- Telnyx AI Assistants event stream.
- Bland and Synthflow.

**Platform changes found.**
- Cartesia stops hosting code-first Line SDK agents on Dec 1, 2026.
- `docs.layercode.com` now 301-redirects to toyo.ai.
- Hume's developer docs index no longer lists EVI.

### Cited Findings

#### Integration-surface matrix

Fit ratings are mine **[I]**. Event names and quotes are **[V]** unless marked otherwise.

| Platform / surface | Partial user transcript: event/field | Streams DURING speech? | Eager / early EOT | Injection mechanism | Latency / budget constraints | Fit and forehear pattern |
|---|---|---|---|---|---|---|
| **Twilio ConversationRelay** | `prompt` message, `voicePrompt`, `last=False` when `partialPrompts="true"` | **Yes [V]** ("unfinalized prompts") | Eager EOT events are also delivered with `last=False`, using Deepgram `flux` and `eotThreshold` | The developer owns the LLM. The app streams `text` tokens back, so context injection happens inside its own prompt | `speechTimeout` is `auto` or 600–5000 ms, forwarded to Flux as max silence. Partial update cadence is not documented **[U]** | **Strong.** forehear sits in the WebSocket server: speculate on `last=False`, commit on `last=True` |
| **Telnyx Conversation Relay** (TeXML / Call Control) | `prompt` frame with `last:false` | **Yes [V]** | `eagerEndOfTurn` frame (with `voicePrompt`) and `turnResumed` frame | Same as Twilio: the developer owns the LLM. Call Control equivalent: `interim_results` and `eager_eot_threshold` | Not documented | **Strong.** It is the same protocol shape as Twilio, so one adapter covers both |
| **Telnyx AI Assistants** (hosted LLM) | Conversation Event Stream: `conversation.item.created` (finished text), `response.text.delta` (assistant only) | **No [V/I]**. No user interim event is listed | None found | `conversation.item.create` over the event-stream socket. `POST /v2/calls/{id}/actions/ai_assistant_add_messages` with `role:"system"` | The stream is "Beta" and a "live view, not a system of record" | **Possible.** Tool or Add-Messages injection only, with a parallel STT needed for early signal |
| **Vapi** | Server message `type:"transcript"`, `transcriptType:"partial"`, `role:"user"` | **Yes [V]** ("Partial and final transcripts from the transcriber"). Cadence and HTTP fan-out latency are not documented **[U]** | None as an event. `call.endpointing.request` lets *your* server choose the endpointing timeout | `controlUrl` `add-message` (`role:"system"`, `triggerResponseEnabled:false` = "added silently... uses it on its next turn"); custom LLM (OpenAI-compatible); `knowledge-base-request` (custom KB); custom transcriber WebSocket (raw PCM to you, you return `transcriber-response` partial/final) | `assistant-request` must answer within "7.5 seconds end-to-end" (call setup only). Tool timeouts are configurable | **Strong.** (1) Custom transcriber: forehear sees the audio and partials first-hand. (2) Partial server messages, then pre-warm, then answer `knowledge-base-request` or the custom-LLM call from cache, or `add-message` silently |
| **Retell AI custom LLM WS** | `update_only` with `transcript` ("Complete live transcript collected in the call so far") and `turntaking` | **Unclear [U].** Docs say the event fires "when the transcript updates -- either the user speaks, or the agent speaks" but do not say mid-utterance | `response_required` may be requested speculatively: "not all responses Retell asks for would get spoken out (as user might continue to speak)" | The developer owns the LLM and the prompt. `update_agent` changes `responsiveness` | `auto_reconnect` ping_pong every 2 s; closes after 5 s silent | **Strong-to-possible.** Speculate on `update_only`, commit on `response_required`, drop stale `response_id` |
| **Deepgram Voice Agent API** | `ConversationText` (user). "The user message is held as non-final until the turn is confirmed" | **No [V]** | Internal speculative window: `eager_eot_threshold`, `eot_threshold`, `eot_timeout_ms`, `ForceEndTurn`. On resume: `UserStartedSpeaking`, `FunctionCallCancelled` | `UpdatePrompt`, `InjectUserMessage`, `agent.context.messages` (History), `FunctionCallResponse`, BYO LLM via `agent.think.endpoint.url` (OpenAI Chat Completions-compatible) | Function calls dispatch "as soon as the LLM emits it, inside the speculative window" unless `defer_until_eot`. Sessions are capped at 2 h | **Possible.** forehear acts as an OpenAI-compatible proxy at `think.endpoint`, or as the function backend. It gets the request at eager EOT (not during speech) and must tolerate cancellations |
| **Deepgram Flux STT (direct)** | `Update` / interim turn text (covered in prior notes) | Yes | `EagerEndOfTurn`, `TurnResumed`, `EndOfTurn` | n/a (STT only) | Prior note: 100–200 ms saved, 50–70% more LLM calls | **Strong** as the *parallel STT* for every "no partials" platform |
| **OpenAI Realtime (S2S, `v1/realtime`)** | `conversation.item.input_audio_transcription.delta` | **No in S2S [V/I].** Commit "kick[s] off input transcription (if enabled)". `gpt-live-transcribe` Realtime endpoint: "Not supported". A developer forum reports deltas only after speech stops | `semantic_vad` `eagerness` (low/medium/high/auto) only; no draft/cancel event | `conversation.item.create` (system/user message or `function_call_output`); `response.create` with `conversation:"none"` (out-of-band); `turn_detection.create_response:false` lets the app gate replies | `server_vad` `silence_duration_ms` default 500 in example | **Possible.** Run a parallel `gpt-live-transcribe` transcription session ("returns transcript deltas as speech arrives"), prefetch, then inject before `response.create` (with `create_response:false`) or answer the tool call from cache |
| **OpenAI Realtime transcription session** (`v1/realtime/transcription_sessions`, `gpt-live-transcribe`) | `conversation.item.input_audio_transcription.delta` | **Yes [V]** | None (VAD unsupported; client commits) | n/a | $0.017/min | Parallel-STT source for OpenAI S2S |
| **Azure Voice Live** | Same events as Azure OpenAI Realtime. Input models include `azure-speech`, `mai-transcribe-2`, `mai-transcribe-2-streaming`, `gpt-4o-transcribe` | **Undocumented [U]** whether deltas arrive mid-speech | `azure_semantic_vad`, `azure_semantic_vad_multilingual`, `eagerness` (semantic_vad only); no eager event found | Realtime events (`conversation.item.create`, `session.update` `instructions`); BYOM and Foundry Agent Service (Foundry resources only). "instructions" is not supported with a custom agent | n/a | **Possible** (S2S pattern). Cascaded `azure-speech` mode may give better deltas **[U]** |
| **Google Gemini Live** | `server_content.interim_input_transcription` / `interimInputTranscription`: "Low latency transcription updated while the user is speaking" | **Yes on `gemini-3.5-transcribe-live` [V].** **Undocumented for agent models [U]**: the agent-model capability page shows only `input_transcription` | None beyond VAD sensitivity; manual `activityStart` / `activityEnd` | `send_client_content` (turns with `turn_complete=false` to add context without triggering); `NON_BLOCKING` function responses with scheduling `SILENT` / `WHEN_IDLE` / `INTERRUPTED` (Gemini 3.8 Live); `initial_history_in_client_content` | `inputTranscription` has "no guaranteed ordering". Gemini 3.1 Flash Live function calling is "synchronous only" | **Possible.** Parallel `gemini-3.5-transcribe-live` session (or interim field if present), prefetch, then `send_client_content(turn_complete=false)` or answer the tool from cache |
| **AWS Nova 2 Sonic** | `textOutput` with `role:"USER"`, `generationStage:"FINAL"` | **No [V].** The ASR block is the first block of the *response* sequence | None | Cross-modal `textInput` (`interactive` flag), `toolResult`, async tools | n/a | **Possible** via parallel STT plus `textInput` or tool cache |
| **ElevenLabs Agents** (client WS / custom LLM) | `user_transcript`: "Contains finalized speech-to-text results". AsyncAPI events list has no tentative or interim user event | **No [V]** | None exposed (`vad_score` only) | `contextual_update` ("non-interrupting background information"); custom LLM (OpenAI Chat Completions or Responses-compatible server URL); custom LLM is unusable with Realtime models | Buffer-words trick ("... ") for slow custom LLMs | **Possible.** forehear as the custom-LLM server (retrieval after turn), or a client-side parallel STT plus `contextual_update` |
| **ElevenLabs Speech Engine** (ElevenLabs connects to *your* `wsUrl`) | `user_transcript` = full history up to latest user turn, `event_id` | **No [V]** (per-turn) | Implicit: a newer `event_id` supersedes; "Cancel your in-flight LLM call" | You own the LLM (stream `agent_response`, `is_final`) | Outdated `event_id` responses are "silently discarded" | **Possible.** Post-turn hook only, similar to Retell without partials |
| **Ultravox** | Data message `transcript` (`role`, `text`/`delta`, `final`, `ordinal`) | **Unclear [U]** for user role. The schema supports non-final user transcripts, but cadence is not stated | None found | `user_text_message` with `urgency:"later"` ("considered during the next natural generation without forcing a new generation"); HTTP or data-connection tools; Threads (`SpawnThread` forks history for side generations); call stages; REST injection | n/a | **Possible.** Inject via `urgency:"later"`. Speculative side-generation threads exist natively, but Ultravox is a speech-native LLM, so early signal needs a parallel STT **[I]** |
| **Cartesia Managed Agents** (Line successor) | `turn_ended` carries finalized user text: "The user's speech is not streamed incrementally" | **No [V]** | None | Tools (`client_tool_call` / `client_tool_result`) | Line SDK code-first hosting ends **Dec 1, 2026** | **None / weak.** Tool-level only |
| **Hume EVI** | n/a | **[U]** | n/a | Previously: custom language model | `dev.hume.ai` index lists only "Audio Decisions" and "Expression Measurement". The EVI overview URL 308-redirects to Audio Decisions | **None (currently unverifiable)** |
| **Layercode** | n/a | n/a | n/a | n/a | `docs.layercode.com` 301 to `toyo.ai`, whose metadata names "Layercode Inc" | **None (product appears pivoted)** |
| **Bland** | No live-transcript server event found (post-call webhooks, pathway webhooks, tools) | **No [V/I]** | None | Tools and webhook steps inside pathways. Bland "owns the full voice AI stack" | n/a | **None.** Tool-level only |
| **Synthflow** | Only post-call and inbound webhooks; "Custom Actions" | **No [V/I]** | None | Custom Actions ("before or during a call"); inbound webhook context | n/a | **None.** Tool-level only |

#### Twilio ConversationRelay [V]
- `partialPrompts`: "Sends unfinalized prompts and eager end-of-turn events to the WebSocket, denoted with last=False." Default `false`. — [Twilio ConversationRelay noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun)
- `eotThreshold`: "Confidence required to finish a turn. Prompts with last=True designate the result of a final turn event. Allowed values are 0.5 - 0.9. Note: Only applies when Deepgram is selected as the transcriptionProvider and flux is selected as the speechModel." Default 0.8. — [Twilio noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun)
- `partialPromptOnHangup`: "sends a pending unfinalized prompt to the WebSocket when the call ends." Default `true`. — [Twilio noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun)
- With `flux`, `speechTimeout` "is instead forwarded to Deepgram as a maximum silence duration — Deepgram handles turn boundary detection server-side". — [Twilio noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun)
- `reportInputDuringAgentSpeech` "controls whether your application receives prompt and DTMF messages while the agent is speaking." `preemptible` lets the next talk cycle's tokens interrupt current TTS. — [Twilio noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun)
- Prompt message format is `{"type":"prompt","voicePrompt":"...","lang":"en-US","last":true}`. "The last field indicates whether the caller has finished speaking". — [Twilio WebSocket messages](https://www.twilio.com/docs/voice/conversationrelay/websocket-messages)
- **[U]** The WebSocket-messages page does not document a distinct eager-EOT message type. Eager events seem to share the `last=False` prompt format. The partial cadence is undocumented.

#### Telnyx Conversation Relay [V]
- Frames sent by Telnyx include:
  - `prompt` ("Partial transcripts use last: false; final transcripts use last: true");
  - `eagerEndOfTurn` ("The caller has likely finished speaking. Sent before the final prompt when partial prompts are on");
  - `turnResumed` ("The caller kept speaking after an eagerEndOfTurn").
  - — [Telnyx Conversation Relay](https://developers.telnyx.com/docs/voice/programmable-voice/conversation-relay)
- "With Deepgram Flux, you can receive the caller's speech while they are still talking, together with an early signal that their turn is likely over." The `eagerEndOfTurn` `voicePrompt` "is the transcript the final prompt is expected to match". — [Telnyx](https://developers.telnyx.com/docs/voice/programmable-voice/conversation-relay)
- Call Control equivalent: "adding the interim_results and eager_eot_threshold options to transcription_engine_config on Start Conversation Relay." — [Telnyx](https://developers.telnyx.com/docs/voice/programmable-voice/conversation-relay)

#### Telnyx AI Assistants [V]
- Conversation Event Stream: "Telnyx opens a WebSocket to a server you host... streaming transcript, response, telephony and delegation events... Your server can push messages back to inject a turn." Use cases listed include "Nudge the assistant mid-call... Send `conversation.item.create`". — [Telnyx Conversation Event Stream](https://developers.telnyx.com/docs/inference/ai-assistants/conversation-event-stream.md)
- The stream is Beta. The completed item "carries the final text — use it as the source of truth". No user interim event is listed (**[I]** from the event inventory). — [Telnyx event stream](https://developers.telnyx.com/docs/inference/ai-assistants/conversation-event-stream.md)
- Add Messages API: `POST /v2/calls/{call_control_id}/actions/ai_assistant_add_messages` with `"role": "system"`. It "Injects new context into an active conversation". — [Telnyx Async Tools](https://developers.telnyx.com/docs/inference/ai-assistants/async-tools.md)
- Custom LLMs: "any OpenAI-compatible endpoint as an LLM provider". — [Telnyx assistants index](https://developers.telnyx.com/public/llms/ai/assistants.txt)

#### Vapi [V]
- Server events: "Transcript — Partial and final transcripts from the transcriber." Example: `{"type":"transcript","role":"user","transcriptType":"partial","transcript":"I'd like to book..."}`. "For final-only events, you may receive `type: \"transcript[transcriptType=\"final\"]\"`." — [Vapi Server events](https://docs.vapi.ai/server-url/events.md)
- Events must be listed in `assistant.serverMessages`. "`status-update` is included by default". **[U]** Whether `transcript` is on by default is not stated. — [Vapi Server events](https://docs.vapi.ai/server-url/events.md)
- `model-output`: "Tokens or tool-call outputs as the model generates", with `turnId`. `user-interrupted` carries the interrupted `turnId`. — [Vapi Server events](https://docs.vapi.ai/server-url/events.md)
- `knowledge-base-request`: sent if `assistant.knowledgeBase.provider = "custom-knowledge-base"`. You respond with `documents` (`content`, `similarity`, `uuid`). — [Vapi Server events](https://docs.vapi.ai/server-url/events.md)
- `call.endpointing.request` goes to `assistant.startSpeakingPlan.smartEndpointingPlan.server.url`. You "Respond with the timeout before considering the user's speech finished". — [Vapi Server events](https://docs.vapi.ai/server-url/events.md)
- `assistant-request`: respond "within **7.5 seconds end-to-end**". — [Vapi Server events](https://docs.vapi.ai/server-url/events.md)
- Custom transcriber:
  - "Vapi connects to your custom transcriber endpoint... via WebSocket" and "streams binary PCM audio to your server".
  - You reply with `transcriber-response`. `transcriptType` `"partial"` = "provisional and may be superseded... Each partial replaces the previous one until a `"final"` arrives."
  - — [Vapi Custom transcriber](https://docs.vapi.ai/customization/custom-transcriber.md)
- Live call control `add-message`: `role` of `system`, `user`, or `assistant`. `triggerResponseEnabled: false` means "The message is added silently. The assistant uses it on its next turn." — [Vapi Live call control](https://docs.vapi.ai/calls/call-features.md)
- Custom LLM: Vapi "sends a POST request containing conversation context and metadata to the configured endpoint". — [Vapi custom LLM guide](https://docs.vapi.ai/customization/custom-llm/using-your-server.md)

#### Retell AI [V]
- "This socket shall connect directly to your server, where you would get live transcript". Events from Retell: `update_only` ("real-time updates about the call like live transcript"), `response_required`, `reminder_required`. — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket.md)
- `update_only`: "Retell would send an event when the transcript updates -- either the user speaks, or the agent speaks. Retell also sends this event when turntaking happens." `transcript` is the "Complete live transcript collected in the call so far". `turntaking` takes `agent_turn` / `user_turn`. — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket.md)
- Speculative response requests: "Retell would continuously assess if it's a good time for agent to speak, and would ask for content for response / reminder when appropriate, but not all responses Retell asks for would get spoken out (as user might continue to speak)." — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket.md)
- "When a newer event that requires response / reminder is received, you can stop responding to the previous response". — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket.md)
- `auto_reconnect`: "expect ping pong events back from your server every 2s. Once there's 5s without ping pong event, Retell would close the current connection". — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket.md)
- Retell recommends its own single-prompt and conversation-flow modes "for most agents". With a custom LLM, "You take on latency, uptime, and reconnection handling." — [Retell custom LLM overview](https://docs.retellai.com/integrate-llm/overview.md)

#### Deepgram Voice Agent API [V]
- Speculative window: "Speech-to-text is moderately confident the user has stopped, so the agent closes the utterance internally and sends the request to the LLM. The turn is not yet confirmed." — [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- `ConversationText` for the user's message is gated: "The user message is held as non-final until the turn is confirmed." — [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- "Function calls: **No, by default.** A tool call is dispatched as soon as the LLM emits it, inside the speculative window." Set `defer_until_eot` to hold it. — [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- Tuning: `agent.listen.provider.eager_eot_threshold`, `eot_threshold`, `eot_timeout_ms`, and `ForceEndTurn`. "Speculative replies are not specific to Flux." — [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- `FunctionCallCancelled` is sent "when a client-side function call it already sent you is cancelled because the user started speaking again, either inside the speculative window... or after the turn was confirmed". — [Deepgram FunctionCallCancelled](https://developers.deepgram.com/docs/voice-agent-function-call-cancelled.md)
- BYO LLM: "Any LLM endpoint that conforms to the OpenAI Chat Completions API format will work". Set via `agent.think.endpoint.url` / `headers`. — [Deepgram LLM Models](https://developers.deepgram.com/docs/voice-agent-llm-models.md)
- Context levers: `UpdatePrompt` ("Replaces the system prompt for the rest of the session"), `InjectUserMessage`, History in `agent.context.messages`. Sessions "close automatically at 2 hours". — [Deepgram Maintaining Context](https://developers.deepgram.com/docs/voice-agent-conversation-context.md)
- Server events list: `ConversationText`, `UserStartedSpeaking`, `AgentThinking`, `FunctionCallRequest`, `FunctionCallCancelled`, `Latency Report`. There is no interim-transcript event. — [Deepgram Outputs](https://developers.deepgram.com/docs/voice-agent-outputs.md)
- New in 2026: "Think Live" floor-management model. Deepgram-hosted LLMs (`/v1/think`) are Early Access. — [Deepgram llms.txt index](https://developers.deepgram.com/llms.txt)

#### OpenAI Realtime [V]
- Transcription guide: "The recommended model returns transcript deltas as speech arrives and a final transcript when your application commits each audio turn. Start with `gpt-live-transcribe`." — [OpenAI Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription.md)
- "In `gpt-live-transcribe` transcription sessions, omit `audio.input.turn_detection` or set it to `null`. The model doesn't support `server_vad` or `semantic_vad`." — [OpenAI Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription.md)
- `gpt-live-transcribe` model page:
  - Endpoints: "Realtime `v1/realtime` | Not supported"; "Realtime transcription `v1/realtime/transcription_sessions` | Supported".
  - Price: $0.017/minute.
  - — [OpenAI gpt-live-transcribe](https://developers.openai.com/api/docs/models/gpt-live-transcribe.md)
- In S2S sessions, `input_audio_buffer.commit` "will commit the audio written to the input buffer and kick off input transcription (if enabled)". — [OpenAI Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations.md)
- Developer report: no deltas "until the user stops talking". — [OpenAI community thread](https://community.openai.com/t/realtime-streaming-transcription/1371205) (forum, already summarized in `s2s_threat.md`)
- Injection mechanisms. — [OpenAI Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations.md)
  - `conversation.item.create` adds text items and `function_call_output` items.
  - Out-of-band responses via `response.conversation: "none"`.
  - `turn_detection.interrupt_response` and `turn_detection.create_response` can be set `false` to "manually decide when a response is generated".
- VAD: `semantic_vad` "Chunks the audio when the model believes... they have completed their utterance". `server_vad` example uses `silence_duration_ms: 500`. — [OpenAI VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad.md)

#### Azure Voice Live [V]
- "Unless otherwise noted, the Voice Live API uses the same events as the Azure OpenAI Realtime API." — [Microsoft Learn: Voice Live how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to) (updated 2026-11-04)
- Input transcription models:
  - `azure-speech` ("All non-multimodal models and agents");
  - `mai-transcribe`, `mai-transcribe-2`, and `mai-transcribe-2-streaming` (preview);
  - `whisper-1` and `gpt-4o-*-transcribe` (gpt-realtime only).
  - — [Voice Live how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to)
- Turn detection: `server_vad`, `semantic_vad`, `azure_semantic_vad`, `azure_semantic_vad_multilingual`. `eagerness` is "Only available with type `semantic_vad`". — [Voice Live how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to)
- "Azure Speech Services resources don't support Microsoft Foundry Agent Service integration and bring-your-own-model (BYOM)." "The `"instructions"` property isn't supported when you're using a custom agent." — [Voice Live how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to)
- The SDK type `conversation.item.input_audio_transcription.delta` is "Returned when the text value of an input audio transcription content part is updated" (timing not stated). — [@azure/ai-voicelive reference](https://learn.microsoft.com/en-us/javascript/api/@azure/ai-voicelive/servereventconversationiteminputaudiotranscriptiondelta?view=azure-node-latest)

#### Google Gemini Live [V]
- Field definitions in the API reference:
  - `interimInputTranscription`: "Output only. Low latency transcription updated while the user is speaking. This field is subject to frequent updates."
  - `inputTranscription`: "The transcription is sent independently of the other server messages and there is no guaranteed ordering."
  - There is also an `interimTranscriptTimestampEnabled` option.
  - — [Gemini Live API reference](https://ai.google.dev/api/live)
- Live-transcribe guide: `interim_input_transcription` gives "low-latency, speculative partial hypotheses updated while the speaker is actively talking". `input_transcription` is "emitted when the speaker pauses, the turn completes, or speech is finalized". This guide is for model `gemini-3.5-transcribe-live`. — [Gemini Live transcription](https://aistudio.google.com/docs/live-api/live-transcribe)
- The same page contrasts the two modes. **[U]** It does not say whether agent sessions emit interim. — [Gemini Live transcription](https://aistudio.google.com/docs/live-api/live-transcribe)
  - Live Agent supports "input audio transcription with speech biasing... on `gemini-3.8-live`".
  - Live Transcription is "Continuous stream processing as the speaker talks".
- Capabilities page model comparison (columns: Gemini 3.8 Live / 3.8 Live Extended Thinking / 3.1 Flash Live Preview / 2.5 Flash Live Preview). — [Gemini Live capabilities](https://ai.google.dev/gemini-api/docs/live-guide)
  - Async functions: "Supported (default)... Function scheduling (`SILENT`, `WHEN_IDLE`, `INTERRUPTED`) is supported" (3.8 Live); "Only `NON_BLOCKING`" (3.8 ET); "Not supported. Function calling is synchronous only" (3.1 Flash Live).
  - Client content: "`send_client_content` is supported throughout the entire session lifecycle... `turn_complete=true` unconditionally interrupts generation."
  - The guide's only input-transcription example uses `server_content.input_transcription`.

#### AWS Nova 2 Sonic [V]
- "The ASR transcription appears first, delivering the model's understanding of the user's speech with `role: "USER"` and `"additionalModelFields": "{\"generationStage\":\"FINAL\"}"`." ASSISTANT text has `SPECULATIVE` and `FINAL` stages. User text has only `FINAL`. — [Nova 2 Sonic output events](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-output-events.md)
- Cross-modal text input (`contentStart` with `type:"TEXT"`, `interactive: true`, then `textInput`, then `contentEnd`) can be sent mid-session. One listed use is "Guiding the model during async tool calling". — [Nova 2 Sonic cross-modal](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-cross-modal.md)

#### ElevenLabs [V]
- `user_transcript`: "Contains finalized speech-to-text results; Represents complete user utterances". — [ElevenLabs Client events](https://elevenlabs.io/docs/eleven-agents/customization/events/client-events.md)
- The Agent WebSocket AsyncAPI event list contains no tentative or interim user transcript event. It has `user_transcription_event`, `vad_score_event`, `interruption_event`, `agent_response_correction_event` and others. — [ElevenLabs Agent WebSockets reference](https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket.md)
- `contextual_update`: "send non-interrupting background information to the conversation". — [ElevenLabs Client-to-server events](https://elevenlabs.io/docs/eleven-agents/customization/events/client-to-server-events.md)
- Custom LLM:
  - The server "must align with... OpenAI-compatible" Chat Completions (`/v1/chat/completions`) or Responses (`/v1/responses`).
  - "A custom LLM can't be used with a Realtime model."
  - — [ElevenLabs Custom LLM](https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm.md)
- Speech Engine reverses the connection: "ElevenLabs is the WebSocket client and your server is the WebSocket server". — [ElevenLabs Speech Engine upstream](https://elevenlabs.io/docs/api-reference/speech-engine/speech-engine-upstream.md)
  - "As the user speaks, ElevenLabs transcribes the audio and sends `user_transcript` messages with the full conversation history."
  - "If the user speaks again before your server finishes responding, a new `user_transcript` arrives with a higher `event_id`. Cancel your in-flight LLM call".

#### Ultravox [V]
- `transcript` messages (`role` user/agent, `text` or `delta`, `final`: "Whether to expect additional transcript messages for this conversation round"). — [Ultravox Data Messages](https://docs.ultravox.ai/apps/datamessages.md)
- `user_text_message` `urgency`: "later → Message is considered during the next natural generation without forcing a new generation." — [Ultravox Data Messages](https://docs.ultravox.ai/apps/datamessages.md)
- "Data Connection → ... receive messages via a separate WebSocket connection... Server-side applications". `SpawnThread` forks a thread with `additionalMessages` and `toolOverrides`. — [Ultravox Data Messages](https://docs.ultravox.ai/apps/datamessages.md)

#### Cartesia [V]
- "Cartesia stops hosting Line SDK agents on **December 1, 2026**. This covers code-first agents you deploy as Python." — [Cartesia: Migrate from the Line SDK](https://docs.cartesia.ai/agents/migrate-from-line-sdk.md)
- The Line `custom` and `update` events have "No equivalent" in Managed Agents. — [Cartesia: Migrate from the Line SDK](https://docs.cartesia.ai/agents/migrate-from-line-sdk.md)
- Agent WebSocket: "The user's speech is not streamed incrementally. It arrives as finalized text in `turn_ended`." — [Cartesia Agent WebSocket reference](https://docs.cartesia.ai/api-reference/agents/agent-websocket.md)

#### Hume, Layercode, Bland, Synthflow [V for what was observed]
- **Hume.** `https://dev.hume.ai/llms-full.txt` lists Products: "Audio Decisions" and "Expression Measurement" only. `https://dev.hume.ai/docs/speech-to-speech-evi/overview` returns HTTP 308 to `/audio-decisions/docs/overview`. **[U]** Whether EVI or its CLM is still sold is unknown. Secondary sources (low reliability) mention a 2026 DeepMind licensing deal. — [Hume docs index](https://dev.hume.ai/llms-full.txt)
- **Layercode.** `https://docs.layercode.com/` returns HTTP 301 to `https://toyo.ai/`. Toyo's page JSON-LD has `"legalName":"Layercode Inc"` and describes Slack and workflow agents. — [docs.layercode.com](https://docs.layercode.com/)
- **Bland.** The docs index describes the platform as "Bland owns the full voice AI stack: telephony, speech-to-text, language model, text-to-speech, and pathway orchestration". The only in-call surfaces found are tools, webhooks and post-call webhooks. No custom-LLM or live-transcript stream was found. — [Bland docs index](https://docs.bland.ai/llms.txt)
- **Synthflow.** Webhooks are post-call or inbound. "Custom Actions: Send HTTP requests to your own APIs before or during a call". No custom-LLM or live-transcript stream was found. — [Synthflow docs index](https://docs.synthflow.ai/llms.txt)

### Inferences
- Twilio and Telnyx Conversation Relay now share one documented protocol: `prompt` with `last` plus eager EOT and `turnResumed`. Telnyx documents the eager frames more explicitly than Twilio. A single "ConversationRelay adapter" in forehear would cover both. **[I]**
- Vapi is the best-hidden fit. Its custom transcriber means forehear can *be* the STT: it sees the audio, produces the partials and controls speculation, while Vapi keeps the LLM. `add-message` with `triggerResponseEnabled:false` is a clean silent-injection hook, and `knowledge-base-request` lets forehear answer instantly from a pre-warmed cache. **[I]**
- Deepgram's Voice Agent already has a native speculative window at the LLM and tool level. forehear does not get partials there. However, its BYO `think.endpoint` receives the speculative LLM call before turn confirmation, so a forehear proxy at that endpoint can retrieve then. This is "eager-EOT-time" speculation, not "during-speech" speculation. **[I]**
- Several hosted platforms are moving away from code-first developer surfaces: Cartesia (Line SDK sunset), Layercode (pivot) and Hume (EVI gone from docs index). This shrinks the long tail of integration targets. **[I]**
- Sub-second partial cadence is undocumented on every platform (Twilio, Vapi, Retell, Ultravox). Any adapter should measure it. **[I]**

### Gaps
- Retell: no doc states whether `update_only` fires mid-utterance with the user's in-progress words. It needs an empirical test or a Retell statement.
- Vapi: whether `transcript` is in the default `serverMessages`, and the HTTP delivery latency of partial `transcript` server messages, are not documented.
- Twilio: the exact message shape distinguishing an eager-EOT event from an ordinary partial is not documented on the WebSocket-messages page.
- Gemini Live agent models (`gemini-3.8-live`): whether `interimInputTranscription` is emitted is not documented.
- Azure Voice Live: whether input-transcription deltas stream during speech (for example with `azure-speech` or `mai-transcribe-2-streaming`) is not stated.
- Ultravox: the cadence and timing of user-role `transcript` messages are not stated.
- Hume EVI: current product status is unverifiable from primary sources.

---

## Q2. Where partials are unavailable, can forehear still help? (parallel STT, tool-level speculation, pre-injection)

### Takeaway
Yes, in three patterns:
1. **Parallel streaming STT on the same audio**, then prefetch, then **pre-inject** context before the model generates. This needs a platform with a no-trigger injection primitive: OpenAI `conversation.item.create` with `create_response:false`, Gemini `send_client_content(turn_complete=false)`, Nova `textInput`, Vapi `add-message` `triggerResponseEnabled:false`, Ultravox `urgency:"later"`, ElevenLabs `contextual_update`, Deepgram `UpdatePrompt`/`InjectUserMessage`, or Telnyx Add Messages.
2. **Tool-result cache.** forehear backs the retrieval tool and answers the `function_call` / `FunctionCallRequest` / `knowledge-base-request` from results already prefetched on partials. Deepgram even dispatches tool calls speculatively by default.
3. **OpenAI-compatible LLM proxy.** forehear sits at the custom-LLM URL (Vapi, ElevenLabs, Deepgram `think.endpoint`, Telnyx) and injects context into the system prompt. Alone, this has no head start. Combined with (1), it does.

The audio tap is the constraint. It is easy where the developer's server already handles the media (Twilio Media Streams in front of OpenAI/Gemini/Nova, Vapi custom transcriber, browser clients). It is hard on fully hosted phone agents (ElevenLabs, Cartesia Managed, Bland, Synthflow).

### Cited Findings
- **OpenAI parallel STT.** A separate transcription session with `gpt-live-transcribe` "returns transcript deltas as speech arrives" ($0.017/min). — [OpenAI Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription.md); [gpt-live-transcribe](https://developers.openai.com/api/docs/models/gpt-live-transcribe.md)
- **OpenAI gating and injection.** The app can stop auto-replies (`create_response:false`, `interrupt_response:false`) and add items via `conversation.item.create`, including `function_call_output`. — [OpenAI Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations.md)
- **Gemini injection.** `send_client_content` works throughout the session with roles, and `turn_complete=true` interrupts generation. So `turn_complete=false` appends context without forcing a turn. **[I]** for the non-trigger semantics; [Gemini Live capabilities](https://ai.google.dev/gemini-api/docs/live-guide)
- **Gemini parallel STT.** `gemini-3.5-transcribe-live` provides interim hypotheses "while the speaker is actively talking". — [Gemini Live transcription](https://aistudio.google.com/docs/live-api/live-transcribe)
- **Gemini tool scheduling.** On Gemini 3.8 Live, function responses support `NON_BLOCKING` with `SILENT` / `WHEN_IDLE` / `INTERRUPTED` scheduling. — [Gemini Live capabilities](https://ai.google.dev/gemini-api/docs/live-guide)
- **Deepgram speculative tool dispatch.** "Most functions read data, and dispatching them early is where the latency win comes from." — [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- **Deepgram cancellation caveat.** "A server-side function that already reached your endpoint is a different matter. Deepgram discards the response, but your endpoint ran." That suits idempotent retrieval. — [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- **Vapi custom transcriber** gives your server the raw call audio ("streams binary PCM audio to your server"). — [Vapi Custom transcriber](https://docs.vapi.ai/customization/custom-transcriber.md)
- **Nova Sonic** accepts mid-session text input and async tools. — [Nova 2 Sonic cross-modal](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-cross-modal.md)
- **Ultravox** `urgency:"later"` messages are "considered during the next natural generation without forcing a new generation". — [Ultravox Data Messages](https://docs.ultravox.ai/apps/datamessages.md)
- **ElevenLabs** `contextual_update` is "non-interrupting background information". — [ElevenLabs Client-to-server events](https://elevenlabs.io/docs/eleven-agents/customization/events/client-to-server-events.md)
- **Telnyx AI Assistants** support mid-call system-message injection via the Add Messages API, and `conversation.item.create` on the event stream. — [Telnyx Async Tools](https://developers.telnyx.com/docs/inference/ai-assistants/async-tools.md); [Telnyx event stream](https://developers.telnyx.com/docs/inference/ai-assistants/conversation-event-stream.md)
- **S2S tool-call timing.** Prior note: S2S time-to-tool-call is 2.2–4.6 s after a disfluent utterance on FDB-v3, which leaves room for prefetch to win. — see `s2s_threat.md` (not re-verified here)

### Inferences
- **Divergence risk.** A parallel STT can disagree with what the S2S model "heard". forehear's commit-or-discard logic should therefore treat the model's eventual tool arguments, or the final transcript, as the oracle, and fall back to a live query on mismatch. **[I]**
- **Pre-injection vs tool-cache.** Pre-injection (context before `response.create`) only works where the app controls reply timing: OpenAI with `create_response:false`, Gemini manual activity, or a cascaded proxy. Where the platform owns turn-taking, the tool-cache pattern is safer and needs no change to platform behaviour. **[I]**
- **Silent injection with no early hook.** On platforms that expose silent injection but no early transcript (ElevenLabs, Telnyx AI Assistants, Nova), forehear only helps if the integrator can fork the audio: a browser client, or their own media gateway in front of the platform. **[I]**
- **No custom LLM and no audio tap.** For Bland, Synthflow and Cartesia Managed, the only option is a fast retrieval tool backend: a "tool-level speculation" mode that pre-warms on conversation state, such as the previous agent question. This is a weak value proposition. **[I]**

### Gaps
- No platform documents the end-to-end latency of its injection primitives. For example: how quickly an `add-message`, `contextual_update` or `urgency:"later"` message becomes visible to the next generation, and whether it races the auto-triggered reply.
- No primary source quantifies transcript divergence between a parallel STT and an S2S model's internal recognition.

---

## Q3. Top 5 integrations forehear should build next (ranked by reach x feasibility)

### Takeaway
1. **ConversationRelay adapter (Twilio + Telnyx).** Strong fit: documented partials and eager EOT to the developer's own server, plus very large telephony reach.
2. **Vapi adapter.** Strong fit: partial `transcript` server messages, custom transcriber audio tap, silent `add-message`, and `knowledge-base-request` / custom-LLM hooks.
3. **Retell custom-LLM adapter.** Strong-to-possible fit: live transcript plus speculative `response_required`. Mid-utterance cadence needs testing.
4. **Deepgram Voice Agent "speculative-window" proxy.** Possible fit: forehear as the BYO `think.endpoint` or function backend. Deepgram also owns Pipecat, so co-marketing is plausible.
5. **S2S "realtime" adapter for OpenAI Realtime, Gemini Live and Azure Voice Live.** Possible fit: parallel STT plus pre-injection or tool cache. Highest strategic reach, and the hardest to make correct.

Deprioritize the following:
- ElevenLabs: no partials; needs a client-side STT.
- Ultravox: unclear partials; good injection.
- Nova Sonic: FINAL-only ASR; needs an audio tap.
- Cartesia: Line sunset Dec 1, 2026.
- Hume and Layercode: surfaces gone from docs.
- Bland and Synthflow: tools only.

### Cited Findings
- **ConversationRelay feasibility.** `partialPrompts` (Twilio) and `eagerEndOfTurn` / `turnResumed` (Telnyx) map one-to-one onto forehear's speculate, commit and discard loop. — [Twilio noun](https://www.twilio.com/docs/voice/conversationrelay/conversationrelay-noun); [Telnyx Conversation Relay](https://developers.telnyx.com/docs/voice/programmable-voice/conversation-relay)
- **Vapi feasibility:**
  - partial transcripts — [Vapi Server events](https://docs.vapi.ai/server-url/events.md);
  - audio tap — [Vapi Custom transcriber](https://docs.vapi.ai/customization/custom-transcriber.md);
  - silent injection — [Vapi Live call control](https://docs.vapi.ai/calls/call-features.md);
  - custom KB — [Vapi Server events](https://docs.vapi.ai/server-url/events.md).
- **Retell feasibility.** Live transcript plus speculative responses that may not be spoken. — [Retell LLM WebSocket](https://docs.retellai.com/api-references/llm-websocket.md)
- **Deepgram feasibility.** BYO OpenAI-compatible think endpoint, speculative LLM requests, and speculative tool dispatch. — [Deepgram LLM Models](https://developers.deepgram.com/docs/voice-agent-llm-models.md); [Deepgram Speculative Replies](https://developers.deepgram.com/docs/voice-agent-speculative-replies.md)
- **Deepgram owns Pipecat.** Deepgram's acquisition of Daily/Pipecat is noted in `s2s_threat.md` (not re-verified here).
- **S2S feasibility.**
  - OpenAI: parallel `gpt-live-transcribe` session plus `conversation.item.create`. — [OpenAI transcription](https://developers.openai.com/api/docs/guides/realtime-transcription.md); [OpenAI conversations](https://developers.openai.com/api/docs/guides/realtime-conversations.md)
  - Gemini: `interimInputTranscription` plus `send_client_content` and NON_BLOCKING tools. — [Gemini Live API reference](https://ai.google.dev/api/live); [Gemini capabilities](https://ai.google.dev/gemini-api/docs/live-guide)
  - Azure: Voice Live reuses the OpenAI Realtime events. — [Voice Live how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to)
- **Deprioritization evidence:**
  - Cartesia Line sunset — [Cartesia migration](https://docs.cartesia.ai/agents/migrate-from-line-sdk.md)
  - Cartesia user speech not streamed — [Cartesia Agent WS](https://docs.cartesia.ai/api-reference/agents/agent-websocket.md)
  - ElevenLabs finalized-only transcripts — [ElevenLabs Client events](https://elevenlabs.io/docs/eleven-agents/customization/events/client-events.md)
  - Nova FINAL-only USER ASR — [Nova output events](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-output-events.md)
  - Hume docs index — [Hume docs index](https://dev.hume.ai/llms-full.txt)
  - Layercode redirect — [docs.layercode.com](https://docs.layercode.com/)

### Inferences
**Ranking rationale [I]**

1. **ConversationRelay (Twilio + Telnyx).**
   - Reach: Twilio is the default telephony layer for custom agents, and Telnyx doubles coverage with the same protocol.
   - Feasibility: highest. Partials and eager EOT arrive at a server the customer already writes. forehear becomes a library they call inside the `prompt` handler.
   - Deliverables: a Python and Node reference server, and a docs PR or sample to Twilio's ConversationRelay samples.
2. **Vapi.**
   - Reach: large self-serve developer base.
   - Feasibility: high. Two modes:
     - (a) "Observer" mode: subscribe to `transcript` partials, prefetch, then serve `knowledge-base-request` or `add-message(system, triggerResponseEnabled:false)`.
     - (b) "Owner" mode: forehear runs as Vapi's custom transcriber wrapping Deepgram Flux, so it controls partial timing and gets eager EOT natively.
   - Risk: webhook delivery latency for partials is unknown. Owner mode avoids it.
3. **Retell.**
   - Reach: large, but custom-LLM is a minority path; Retell recommends its native modes.
   - Feasibility: high if `update_only` streams mid-utterance. If not, forehear still gets a head start from speculative `response_required` events. Validate before committing.
4. **Deepgram Voice Agent.**
   - Reach: moderate directly, but strategically important because of Deepgram's ownership of Pipecat and its authorship of the eager-EOT-for-RAG guidance.
   - Feasibility: medium. No partials, so speculation starts at eager EOT, not during speech. Still, an OpenAI-compatible forehear proxy at `think.endpoint` (or a function backend tolerant of `FunctionCallCancelled`) is a few hundred lines of code.
   - The pitch to Deepgram: retrieval that starts *before* their speculative window.
5. **S2S realtime adapter (OpenAI Realtime, Gemini Live, Azure Voice Live).**
   - Reach: highest long-term, since S2S share is growing (see `s2s_threat.md`).
   - Feasibility: lowest. It needs an audio fork, a second paid STT session (OpenAI) or a second model session (Gemini transcribe-live), divergence handling, and reply gating.
   - Build order: first as a LiveKit/Pipecat realtime-model plugin, where audio is already in-process; then as a standalone Twilio-Media-Streams-to-OpenAI/Gemini bridge.

**Notable non-picks**
- ElevenLabs: large reach but no partials. Viable only for browser SDK users who can run a client-side STT and push `contextual_update`.
- Ultravox: good injection primitives (`urgency:"later"`, threads). Promote it if user-role `transcript` deltas prove to stream mid-speech.

### Gaps
- No primary data on each platform's developer counts or share of custom-LLM usage was gathered here, so "reach" is judged qualitatively. See `market_adoption.md` for whatever adoption data exists.
- None of the rankings has been validated by an actual prototype. The partial cadence and delivery latency on Twilio, Vapi and Retell should be measured before committing engineering effort.
