# Streaming STT and turn-detection vendors, seen from forehear (Nov 2026)

Research date: 2026-11-06. This builds on and checks `/home/user/Infinity/docs/research/notes/turn_taking_and_latency.md`; facts already sourced there are cited again here rather than repeated in full.

**Labels**
- **[vendor]**: the vendor's own claim.
- **[3p]**: a third-party aggregator or blog.
- **[code]**: read directly from framework source.

**Framework source.** Read from shallow clones, without running any of the code:
- LiveKit Agents at commit `055744e` (2026-11-05)
- Pipecat at commit `6fa9cf2` (2026-11-05)

Code links point at those commits.

## Q0. Vendor-by-vendor capability matrix, and which vendors Pipecat and LiveKit integrate

### Takeaway
Every major cloud STT streams interims. They differ sharply in three ways that matter to forehear:
1. **How a stable prefix is exposed.** Some mark it per token or word (Soniox final/non-final tokens, AWS `Stable`, LocalAgreement). Some give a per-result score (Google `stability`). Others rewrite the whole hypothesis (ElevenLabs partials, Cartesia `turn.update`, Deepgram interims).
2. **Whether they send an eager-EOT event.** Deepgram Flux, Cartesia Ink-2 and Kyutai do; AssemblyAI exposes EOT confidence on every message.
3. **Whether the framework already uses that event to speculate.** LiveKit runs preemptive LLM generation **by default**. Pipecat's eager mixin only fires for Flux and Cartesia Turns.

No vendor publishes revision-rate metrics.

### Cited Findings

**Capability matrix** (blank or "?" = not found; see Gaps). Two rows are turn models rather than STT services (see the note after the table). The LK and Pipecat columns show whether that framework ships an integration.

| Vendor / model | Interims, cadence / first-partial latency | Append-only vs revised | Eager EOT / EOT confidence | EOT latency / accuracy | Word timestamps in interims | Price (streaming) | Retrieval-adjacent | LK | Pipecat |
|---|---|---|---|---|---|---|---|---|---|
| Deepgram Nova-3 | Yes; AA first partial 0.057 s, WER 6.69% | Revised interims, finalized at endpointing | No (endpointing only) | TTFS median ≈247 ms (Daily) | ? | $0.0077/min PAYG, $0.0065 Growth | Keyterm prompting +$0.0013/min; streaming Entity Detection +$0.0017/min; Voice Agent API $0.050–0.163/min | Yes (+ Inference) | Yes |
| Deepgram Flux | Yes; AA first partial 0.019 s, WER 7.36% | `Update` events within a turn | **EagerEndOfTurn + TurnResumed**; `eager_eot_threshold` 0.3–0.9; off by default | ≈260 ms EOT [vendor]; eot-bench 12.9% false cutoffs at 300 ms | ? | $0.0077/min EN, $0.0078 multi (PAYG) | Same add-ons; Voice Agent API | Yes (`stt_v2`, emits PREFLIGHT) | Yes (eager mixin) |
| AssemblyAI Universal-Streaming / U3-3.6 Pro RT | Yes; AA first partial U3 RT Pro 0.47 s; vendor page 0.191 s for U3.5 | ? | `end_of_turn_confidence` on messages; threshold presets; U3 Pro uses punctuation-based detection (confidence threshold has no effect) | `min_turn_silence` 96–800 ms by preset | Yes (LK plugin builds timed words on interims) | $0.15/hr Universal-Streaming; $0.45/hr U3.6 Pro RT; billed on session time | Keyterms (U3.6: 100 terms, updatable mid-stream); "entity-aware endpointing" [vendor]; Voice Agent API "being retired"; LLM Gateway | Yes (+ Inference; PREFLIGHT on "utterance") | Yes (threshold exposed, no eager mixin) |
| Soniox stt-rt-v5 | Yes, token-level; AA first partial 0.05 s | **Final tokens never change; non-final tokens may** | `<end>` endpoint token; LK maps "all tokens final" to PREFLIGHT | eot-bench 5.5% false cutoffs at 600 ms; TTFS ≈249 ms (Daily) | Token-level (format not verified) | $0.12/hr | Translation and diarization in-stream [vendor] | Yes | Yes |
| Speechmatics (Enhanced; Agent STT / linden-1) | `AddPartialTranscript` vs `AddTranscript`, bounded by `max_delay` | Partials revisable; finals arrive incrementally | `EndOfUtterance` (silence trigger), `ForceEndOfUtterance`; Agent STT `END_OF_TURN` pause-based, "smart turn detection coming soon" | Agent STT finalization <350 ms mean, ≈440 ms P95 [vendor]; Pipecat bench 369 ms median; older Enhanced TTFS ≈495 ms | ? | Agent STT launch price $0.30/hr | Flow (agent platform) | Yes (+ Inference linden-1) | Yes |
| Gladia Solaria-1 | Partials "<103 ms" [vendor] | "stabilizing as speech continues" | Adjustable endpointing | Finals ≈270 ms [3p] | ? | ≈$0.75/hr Starter [3p] | — | Yes | Yes |
| Google Chirp 3 (Speech v2) | `interim_results`; AA notes Chirp 3 leads partial WER on VoxPopuli (2.2%) | **`stability` 0.0–1.0 per interim result** | `SPEECH_ACTIVITY_BEGIN/END`; `END_OF_SINGLE_UTTERANCE` only on `latest_short` | ? | ? | ? | — | Yes | Yes |
| AWS Transcribe streaming | `IsPartial` results about every 0.5 s in docs example | **Optional stabilization: per-item `Stable` flag, only last few words can change**; low/med/high | None beyond segment finalization | ? | Yes (items carry Start/EndTime in partials) | ? | Call Analytics variant exists | Yes (stabilization flag exposed) | Yes |
| Azure Speech | `recognizing` events (partial hypotheses) | ? | ? | ? | ? | ? | ? | Yes | Yes |
| OpenAI gpt-live-transcribe (Realtime, transcription intent) | `...transcription.delta` events | Docs tell apps to plan "how your UI should revise partial text when later deltas correct earlier text" | **No server_vad/semantic_vad for this model**; client VAD plus `commit` | `delay` minimal→xhigh trades latency for WER | **No word timestamps or confidence** | ≈$0.017/min for GPT-Realtime-Whisper [competitor-cited] | `keywords`, `prompt` | Yes (+ Inference) | Yes |
| ElevenLabs Scribe v2 Realtime | Yes; AA first partial 0.13 s, WER 3.65% | Partial = current-segment hypothesis (rewritten); committed = history | Commit via VAD (`vad_silence_threshold_secs` default 1.5 s) or manual | — | ? | ? | — | Yes | Yes (Realtime service) |
| Cartesia Ink-2 (Turns) | `turn.update` carries the full current transcript | Rewrite semantics (plugin re-sends only on change) | **`turn.eager_end`**; `turn.resume` (support disputed) | AA final 0.21 s with semantic endpoints | ? | ≈$0.54/hr [3p] | Bundled with Sonic TTS as a stack | Yes (+ Inference ink-2; PREFLIGHT on eager_end) | Yes (`CartesiaTurnsSTTService`, eager mixin) |
| NVIDIA Riva / Parakeet / Nemotron 3.5 ASR | Cache-aware FastConformer RNN-T, 80–1120 ms chunks; AA first partial 0.04 s (Nemotron 3, 80 ms) | ? (Riva reports separate intermediate vs final latency) | ? | ? | ? | Self-hosted | — | Yes | Yes |
| Kyutai STT 1B en/fr | Delayed-streams model, 500 ms text delay | Likely append-only (inference, below) | **Semantic VAD: probability the user is done** (Rust server only) | +500 ms flush after VAD | ? | Open weights | — | No plugin found | No (Pipecat has `gradium`; not checked) |
| Groq Whisper | **No interims**: batch HTTP via `BaseWhisperSTTService` | n/a | n/a | n/a | n/a | ? | — | Yes | Yes (segmented) |
| whisper_streaming (LocalAgreement-2) | Re-decodes a buffer; commits the prefix two consecutive updates agree on | **Confirmed prefix append-only, unconfirmed tail revised** | No | ≈3.3 s average latency (A40) | Yes (Whisper word timestamps drive the cut points) | Open | — | No | No (Pipecat `whisper` is segmented) |
| Moonshine | Pipecat wraps it as a `SegmentedSTTService` (no interims) | n/a | n/a | n/a | ? | Open | — | No | Yes |
| Vosk/Kaldi, Rev.ai | ? | ? | ? | ? | ? | ? | ? | No plugin found | No service found |

Turn models: the LiveKit Turn Detector (v1 and v1-mini) is a LiveKit plugin, and Smart Turn v3 and Krisp VIVA are Pipecat turn analyzers. They take audio and/or text and output a probability, with no transcript of their own. Their figures are in the notes file listed under Turn-detector models below.

**Sources for the matrix**

*Pricing pages*
- Deepgram streaming, add-on and Voice Agent API prices — [Deepgram pricing](https://deepgram.com/pricing). Third-party aggregators disagree on Flux pricing; one lists $0.0065/min for Flux EN PAYG. The official page fetched today shows $0.0077 — [diyai](https://diyai.io/ai-tools/speech-to-text/deepgram-pricing-2026/).
- AssemblyAI prices, session-time billing, keyterms updatable mid-stream, and "Voice Agent API is being retired" — [AssemblyAI pricing](https://www.assemblyai.com/pricing).

*Turn detection and endpointing*
- AssemblyAI U3 Pro: punctuation-based turn detection; `end_of_turn_confidence_threshold` "has no impact" — [AssemblyAI U3 Pro streaming docs](https://www.assemblyai.com/docs/streaming/universal-3-pro).
- AssemblyAI presets and `min_turn_silence` — [AssemblyAI turn detection](https://www.assemblyai.com/docs/streaming/universal-streaming/turn-detection).
- AssemblyAI claim that U3.6 Pro Realtime has the lowest entity error rate (14.41%) and "entity-aware endpointing" [vendor] — [AssemblyAI blog](https://www.assemblyai.com/blog/best-api-models-for-real-time-speech-recognition-and-transcription).
- Soniox `<end>` token "marks all preceding tokens as final" and is meant to trigger downstream LLM calls — [Soniox endpoint detection](https://soniox.com/docs/stt/rt/endpoint-detection).
- Speechmatics `EndOfUtterance`, `ForceEndOfUtterance`, and keeping the silence trigger below `max_delay` — [Speechmatics turn detection](https://docs.speechmatics.com/speech-to-text/realtime/turn-detection).

*Vendor launches and product pages*
- Soniox $0.12/hr for stt-rt-v5 (updated June 2026) — [Soniox pricing comparison](https://soniox.com/pricing/stt/soniox-vs-openai-whisper).
- Speechmatics Agent STT: finalization numbers, pause-based `END_OF_TURN`, "smart turn detection coming soon", $0.30/hr launch price, LiveKit Inference availability — [Speechmatics Agent STT announcement](https://www.speechmatics.com/company/articles-and-news/meet-agent-stt-powered-by-linden-1-fast-accurate-speech-recognition). A secondary source dates the launch to 17 Sep 2026 — [Micdrop](https://micdrop.dev/blog/top-speech-to-text-apis-voice-agents).
- Gladia partials "<103 ms ... stabilizing as speech continues" [vendor] — [Gladia real-time](https://www.gladia.io/product/speech-to-text-api/real-time).
- Gladia $0.75/hr Starter — [Listicler](https://listicler.com/tools/gladia) [3p].
- Cartesia `turn.eager_end` gives "your LLM a head start" [vendor] — [Cartesia Ink](https://www.cartesia.ai/ink).
- Cartesia migration table marks `turn.resume` "No (Flux: yes)" — [Cartesia migrate from Flux](https://docs.cartesia.ai/use-the-api/stt/turns/migrate-from-deepgram-flux.md). This conflicts with Pipecat, whose Cartesia Turns lifecycle includes `turn.resume` — [Pipecat cartesia/turns/stt.py](https://github.com/pipecat-ai/pipecat/blob/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services/cartesia/turns/stt.py).
- Cartesia ≈$0.54/hr — [callmissed](https://www.callmissed.com/models/ink-2) [3p].

*API reference and developer docs*
- Google `stability` is "An estimate of the likelihood that the recognizer will not change its guess about this interim result … 0.0 (completely unstable) to 1.0 (completely stable)" — [Google Speech v2 RPC reference](https://docs.cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v2).
- AWS partial-result stabilization: "only the last few words from the partial results can change"; `Stable` flags; items flagged true "won't change" — [AWS Transcribe streaming partial results](https://docs.aws.amazon.com/transcribe/latest/dg/streaming-partial-results.html).
- OpenAI `gpt-live-transcribe`: no server or semantic VAD, no word timestamps or confidence, `delay` levels, revise-partial guidance — [OpenAI realtime transcription guide](https://developers.openai.com/api/docs/guides/realtime-transcription).
- OpenAI ≈$0.017/min for GPT-Realtime-Whisper, as quoted by a competitor — [Soniox pricing comparison](https://soniox.com/pricing/stt/soniox-vs-openai-whisper).
- ElevenLabs partial vs committed transcripts, VAD defaults (silence 1.5 s, range 0.3–3.0; threshold 0.4) — [ElevenLabs commit strategies](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies).

*Benchmarks, papers and other sources*
- AA-WER Streaming (June 1, 2026): first-partial and final latency and WER per model; "Final is only ≈0.7 pp more accurate than First Partial on average"; GPT Realtime Whisper (7.5%→5.1%) and Voxtral Mini (9.6%→5.3%) improve materially by the final; no revision or stability metric reported — [Artificial Analysis](https://artificialanalysis.ai/articles/new-streaming-speech-to-text-benchmark-aa-wer-streaming).
- Daily TTFS figures (Nova-3 ≈247 ms, Soniox ≈249 ms, Speechmatics ≈495 ms) — [Daily STT benchmark](https://www.daily.co/blog/benchmarking-stt-for-voice-agents/).
- Turn-detector models (LiveKit Turn Detector v1/v1-mini, Smart Turn v3, eot-bench, VAP) — figures as in [notes file](/home/user/Infinity/docs/research/notes/turn_taking_and_latency.md) Q1, including the [LiveKit blog](https://livekit.com/blog/solving-end-of-turn-detection) and the [Daily Smart Turn v3 blog](https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/).
- Kyutai: semantic VAD predicts "the probability that the user is done talking"; 500 ms delay plus flush; Rust server only; 400 streams per H100 — [Kyutai STT](https://kyutai.org/stt); [GitHub delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling).
- NVIDIA Nemotron 3.5 ASR: 600M parameters, cache-aware FastConformer + RNN-T, chunks 80/160/320/560/1120 ms; 240 streams per H100 [vendor via 3p] — [wavect review](https://wavect.io/blog/nvidia-nemotron-3-5-asr-production-review.md).
- Riva measures intermediate (`is_final == false`) and final latency separately — [Riva ASR performance](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/asr/asr-performance.html).
- whisper_streaming: LocalAgreement-2 "applied on the unconfirmed (right) part in two subsequent updates"; 3.3 s latency on ESIC with an A40 — [Macháček et al., arXiv 2307.14743](https://arxiv.org/html/2307.14743).

**Framework integration** [code]

*Pipecat* (`src/pipecat/services`)
- STT-capable integrations include assemblyai, aws, azure, cartesia (including `turns`), deepgram (including `flux` and `flux/sagemaker`), elevenlabs (batch and Realtime), gladia, google (including Gemini), groq, moonshine, nvidia (streaming, segmented, SageMaker), openai (Whisper batch and `OpenAIRealtimeSTTService`), soniox, speechmatics, whisper (local, segmented), plus funasr, sarvam, mistral, xai and gradium.
- No Rev.ai, Vosk or Kyutai service directory.
- Turn analyzers: `smart_turn` (v2, v3, CoreML, HTTP) and `krisp_viva_turn`.
- [Pipecat services tree](https://github.com/pipecat-ai/pipecat/tree/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services); [audio/turn](https://github.com/pipecat-ai/pipecat/tree/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/audio/turn).

*Pipecat eager EOT*
- `EagerEndOfTurnSTTServiceMixin` is used only by `DeepgramFluxSTTBase` (and its SageMaker variant) and `CartesiaTurnsSTTService`.
- Flux `eager_eot_threshold` is "Off by default". When eager mode is enabled without a value, the default is 0.5.
- Cartesia `turn_eager_end_threshold` is documented in Pipecat as "0.3–0.8; Cartesia defaults to 0.6".
- Eager EOT produces a `UserTurnSpeculation`: "a speculative inference … runs against a provisional context and its response is held back until the turn is confirmed".
- Example: `examples/turn-management/turn-management-eager-end-of-turn.py`.
- [Deepgram flux/stt_base.py](https://github.com/pipecat-ai/pipecat/blob/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services/deepgram/flux/stt_base.py); [turns/types.py](https://github.com/pipecat-ai/pipecat/blob/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/turns/types.py).

*Pipecat segmented services*
- Groq is a `BaseWhisperSTTService`; Moonshine and local Whisper are `SegmentedSTTService`s. These give no interims.
- [groq](https://github.com/pipecat-ai/pipecat/tree/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services/groq); [moonshine](https://github.com/pipecat-ai/pipecat/tree/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services/moonshine).

*LiveKit* (`livekit-plugins`)
- Plugins include assemblyai, aws, azure, cartesia, deepgram, elevenlabs, gladia, google, groq, nvidia, openai, soniox, speechmatics, mistralai, xai, krisp, silero, turn-detector and many others.
- No Rev.ai, Vosk, Moonshine or Kyutai plugin.
- [LiveKit plugins tree](https://github.com/livekit/agents/tree/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins).

*LiveKit Inference* (hosted, no separate vendor key)
- Models: deepgram/nova-2·3 and flux-general(-en/-multi), cartesia/ink-whisper and ink-2, assemblyai/universal-streaming(-multilingual), u3-rt-pro, universal-3-5-pro and universal-3-6-pro, xai/stt-1·2, speechmatics/enhanced, standard and linden-1, inworld/inworld-stt-1, google/gemini-3.5-transcribe-live, openai/gpt-live-transcribe.
- [inference/stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/inference/stt.py).

*LiveKit `PREFLIGHT_TRANSCRIPT` event*
- Defined as "emitted when the STT is confident enough that a certain portion of speech will not change … stable enough to be used for preemptive generation" — [stt/stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/stt/stt.py).
- Plugins that emit it:
  - Deepgram `stt_v2` (Flux EagerEndOfTurn)
  - AssemblyAI ("utterance" chunks)
  - Soniox (when "all tokens in this batch are final … This mirrors Deepgram v2's EagerEndOfTurn behavior")
  - Cartesia (`turn.eager_end`)
  - mistralai, nabrah, reson8, fishaudio
- [soniox/stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins/livekit-plugins-soniox/livekit/plugins/soniox/stt.py); [deepgram/stt_v2.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins/livekit-plugins-deepgram/livekit/plugins/deepgram/stt_v2.py); [cartesia auto_finalize stream](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins/livekit-plugins-cartesia/livekit/plugins/cartesia/_recognize_streams/auto_finalize_recognize_stream.py).

*LiveKit Cartesia thresholds*
- The LiveKit plugin documents `turn_eager_end_threshold` as "Range 0.3-0.6", with a Cartesia default of 0.4 per a 3p summary of the LiveKit reference. This conflicts with Pipecat's 0.3–0.8 / 0.6.
- [LiveKit cartesia/stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins/livekit-plugins-cartesia/livekit/plugins/cartesia/stt.py).

*LiveKit preemptive generation*
- Defaults: `{"enabled": True, "preemptive_tts": False, "max_speech_duration": 10.0, "max_retries": 3}`. LLM only by default; skipped for utterances over 10 s "since long utterances are more likely to change".
- `on_preflight_stale` cancels the preemptive generation "once the transcript has moved past the preflight", e.g. on Flux `TurnResumed`.
- [voice/turn.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/voice/turn.py); [voice/audio_recognition.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/voice/audio_recognition.py).

*Integrator default*
- Telnyx turned on Flux eager EOT by default at threshold 0.3 — [Telnyx](https://telnyx.com/release-notes/automatic-eager-end-of-turn-deepgram-flux).

### Inferences
- **forehear's natural hook differs by framework.**
  - In LiveKit, `PREFLIGHT_TRANSCRIPT` plus the existing stale-cancellation path are the obvious eager trigger. They work across Flux, AssemblyAI, Soniox and Cartesia without vendor-specific code.
  - In Pipecat, the only first-class eager trigger is `UserTurnSpeculation` / `EagerTranscriptionFrame` from Flux or Cartesia Turns. For other vendors forehear must fall back to interims, optionally combined with Smart Turn probabilities.
- **Segmented stacks give forehear nothing to work with mid-utterance.** Groq, Moonshine and local Whisper in Pipecat produce no interims; there the only gain is overlapping retrieval with the turn-analyzer wait.
- **Several vendors bundle a turn signal, but none bundle retrieval.** The "competing feature" risk sits in the frameworks, which already speculate on the *LLM* (LiveKit by default). Adding retrieval prefetch to that same path would be a small step for them.

### Gaps
- Pricing could not be confirmed from primary pages for Google Chirp 3, AWS Transcribe, Azure, ElevenLabs Scribe v2 Realtime, Rev.ai, Groq or OpenAI, and Cartesia and Gladia figures are third-party only. Vercel notes ElevenLabs promotional pricing ends 9 Nov 2026 — [Vercel AI Gateway](https://vercel.com/ai-gateway/models/scribe-v2-realtime).
- I did not verify interim cadence (ms between interims) for any vendor beyond AWS's illustrative 0.5 s example.
- I did not verify whether word timestamps appear in interims for Deepgram, Soniox, Google, Speechmatics, ElevenLabs, Cartesia or Gladia.
- Azure (`StablePartialResultThreshold`?), Rev.ai, Vosk/Kaldi, Moonshine's native streaming mode, WhisperLive and Daily's own turn offering were not researched beyond framework presence.
- Deepgram's Flux docs page on the state machine returned 404, so Flux `Update` cadence is unverified.

## Q1. What fraction of production voice stacks have an eager EOT signal versus only interims and final?

### Takeaway
No usage-share data exists in public sources. Structurally, eager signals are available from four widely used vendors: Deepgram Flux, AssemblyAI (via EOT confidence and LiveKit preflight), Soniox (via LiveKit preflight) and Cartesia Ink-2. In LiveKit, any of these turn speculation on by default. My rough estimate is that a large share of LiveKit stacks, but only a minority of Pipecat stacks, have an eager-EOT trigger today. This is speculative.

### Cited Findings
- I found no survey of STT usage among Pipecat or LiveKit builders. Roundups are vendor-affiliated or SEO-style, and rank Deepgram as the most common default and AssemblyAI as most accurate on some benchmarks — [FutureAGI](https://futureagi.com/blog/best-stt-providers-voice-agents-2026/); [Coval](https://www.coval.ai/blog/best-speech-to-text-providers-in-2026-independent-benchmarks-and-how-to-choose/); [Evalgent](https://www.evalgent.com/blog/stt-providers-for-voice-agents).
- LiveKit Inference offers hosted STT from Deepgram, Cartesia, AssemblyAI, xAI, Speechmatics, Inworld, Google and OpenAI. Three of those vendors' models emit preflight: Flux, AssemblyAI and Ink-2 — [inference/stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/inference/stt.py); [LK stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/stt/stt.py).
- LiveKit preemptive generation is enabled by default — [voice/turn.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/voice/turn.py).
- Flux eager EOT is off by default in both Deepgram and Pipecat — [Pipecat flux/stt_base.py](https://github.com/pipecat-ai/pipecat/blob/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services/deepgram/flux/stt_base.py). At least one large integrator (Telnyx) flipped it on by default — [Telnyx](https://telnyx.com/release-notes/automatic-eager-end-of-turn-deepgram-flux).
- Deepgram warns eager mode raises LLM calls by 50–70% — [Deepgram Flux agent docs](https://developers.deepgram.com/docs/flux/agent.md).
- Some stacks have no server turn signal at all.
  - OpenAI `gpt-live-transcribe` requires client VAD and commit — [OpenAI](https://developers.openai.com/api/docs/guides/realtime-transcription).
  - Speechmatics Agent STT is pause-based only for now — [Speechmatics](https://www.speechmatics.com/company/articles-and-news/meet-agent-stt-powered-by-linden-1-fast-accurate-speech-recognition).
  - ElevenLabs commits on VAD silence or manually — [ElevenLabs](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies).

### Inferences
- **Speculative estimate.** It assumes Deepgram is the plurality vendor and Nova-3 is still common alongside Flux.
  - In LiveKit stacks, perhaps half or more run an STT that emits preflight, and speculation is on by default.
  - In Pipecat stacks, only Flux-with-eager or Cartesia Turns users have it. That is probably well under a third.
  - Everyone else (Nova-3, Google, AWS, Azure, ElevenLabs, Speechmatics, OpenAI, Gladia, segmented Whisper) has only interims, finals and a separate turn model (Smart Turn, LiveKit Turn Detector, Krisp).
  - Treat this as a hypothesis to test, for example via PyPI download counts of `livekit-plugins-*` and `pipecat-ai[...]` extras.
- **forehear should support interims as its baseline trigger and treat eager EOT as an optional upgrade.** The interims-only population is likely the majority across all stacks.

### Gaps
- No primary usage data. LiveKit, Daily, Vapi and Retell do not publish STT share; package-download proxies were not collected in this session.
- Unknown share of Flux vs Nova-3 traffic at Deepgram.

## Q2. Do interim revision patterns differ by vendor, and what does that imply for speculative retrieval hit rates?

### Takeaway
Yes, structurally. There are three families:
1. **Explicit stable prefix.** Soniox final tokens, AWS `Stable` items and LocalAgreement's committed prefix are effectively append-only, with a revisable tail.
2. **Scored but unflagged.** Google's per-result `stability` float.
3. **Whole-hypothesis rewrite.** Deepgram interims, ElevenLabs partials, Cartesia `turn.update`, and OpenAI deltas that may "correct earlier text".

No vendor or independent benchmark publishes revision rates. Artificial Analysis finds most models' first partial is already near final accuracy; the exceptions are Whisper-derived and Voxtral models.

### Cited Findings
- AWS stabilization: "only the last few words from the partial results can change". Items flagged `Stable: true` "won't change". The docs example shows tail rewrites even at high stability ("the largest rainfall." → "the largest rain forest.") and, without stabilization, "the law." → "the largest" and "ray" → "rain for" → "rainforest" — [AWS](https://docs.aws.amazon.com/transcribe/latest/dg/streaming-partial-results.html).
- Google: `stability` is the per-interim likelihood that "the recognizer will not change its guess"; `is_final` means no further hypotheses for that portion — [Google RPC](https://docs.cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v2).
- Soniox: tokens are split into final and non-final; LiveKit emits preflight when a batch has no non-final tokens — [LK soniox/stt.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins/livekit-plugins-soniox/livekit/plugins/soniox/stt.py); [Soniox endpoint detection](https://soniox.com/docs/stt/rt/endpoint-detection).
- OpenAI tells apps to plan for "later deltas correct[ing] earlier text"; the `delay` setting trades latency for WER — [OpenAI](https://developers.openai.com/api/docs/guides/realtime-transcription).
- ElevenLabs: "partial transcript is the real-time transcript of the current segment"; committed text is history — [ElevenLabs](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies).
- Cartesia via LiveKit: the plugin forwards `turn.update` only "if there's a change", to avoid "canceling the preflight transcript". This shows the full transcript is resent and any change invalidates speculation — [LK cartesia stream](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-plugins/livekit-plugins-cartesia/livekit/plugins/cartesia/_recognize_streams/auto_finalize_recognize_stream.py).
- LiveKit invalidation is string-based: `transcript_changed = self._audio_transcript != self._audio_preflight_transcript` — [audio_recognition.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/voice/audio_recognition.py).
- AA-WER Streaming: final is ≈0.7 pp better than first partial on average. Scribe v2 RT, Nova-3 and Flux are essentially unchanged. GPT Realtime Whisper (7.5→5.1%) and Voxtral Mini (9.6→5.3%) improve materially by the final — [Artificial Analysis](https://artificialanalysis.ai/articles/new-streaming-speech-to-text-benchmark-aa-wer-streaming).
- Google RNN-T research: UPWR 0.04–0.37 unstable words per final word; emitting partials less often (50→200 ms) cut UPWR by 71.6% at ≈+75 ms delay — [arXiv 2006.01416](https://arxiv.org/abs/2006.01416).
- LocalAgreement-2 commits only text agreed across two consecutive updates — [arXiv 2307.14743](https://arxiv.org/html/2307.14743).
- Kyutai's delayed-streams model emits text with a fixed 500 ms delay behind audio, the lookahead that lets it commit text — [Kyutai STT](https://kyutai.org/stt).

### Inferences
- **Hit-rate implication.** For explicit-prefix vendors (Soniox, AWS with stabilization, LocalAgreement, and likely Kyutai, whose decoder emits time-aligned tokens without re-decoding), forehear can key retrieval on the stable prefix and know that only the tail can move. Speculative queries are invalidated less often and false-cancel rates are lower.
- **Rewrite-style vendors need fuzzy checks.** For Deepgram interims, ElevenLabs, Cartesia and OpenAI, forehear needs its own stability heuristic, for example: words unchanged across N interims, top-k doc overlap, or embedding similarity. Without it, exact string comparison (LiveKit's approach for LLM preflight) will over-cancel on cosmetic edits such as punctuation and casing.
- **Whisper-derived streaming sources are the worst case for early speculation.** AA's partial-to-final WER gap is largest for GPT Realtime Whisper and Voxtral, so forehear should wait longer or weight later interims more on those sources.
- **Retrieval tolerates revision better than LLM preemption.** A revision that leaves the top-k document set unchanged still yields a hit, while LiveKit's string check would discard an LLM run. This argues for forehear measuring hit rate at the document-set level, not the transcript level.

### Gaps
- No published revision or stability metrics (UPWR-style) exist for any commercial vendor. AA explicitly reports none. A forehear-side measurement (revisions per utterance per vendor) would be novel data.
- Deepgram Nova-3 and Flux interim revision behaviour, AssemblyAI Universal-Streaming's partial semantics (immutable vs revised), and Speechmatics' `max_delay` effect on partials were not confirmed from primary docs in this session.
- An arXiv paper, "Beyond Fresh Starts: Stateful Inference for Streaming ASR in Conversational Voice Agents" (2608.22101), surfaced but was not read — [arXiv](https://arxiv.org/pdf/2608.22101).

## Q3. Is any STT or turn vendor moving toward offering retrieval or intent prefetch itself?

### Takeaway
I found no STT or turn vendor that ships retrieval prefetch or streaming intent-triggered tool calls. Movement is adjacent instead:
- vendor agent bundles (Deepgram Voice Agent API, Speechmatics Flow, Cartesia's STT+TTS stack)
- streaming entity detection and mid-stream keyterms
- eager-EOT signals explicitly marketed as an "LLM head start"

The closest competitive threat is framework-level: LiveKit's default-on preemptive generation and Pipecat's `UserTurnSpeculation` already speculate on the LLM. AssemblyAI is retreating from bundling: its Voice Agent API is being retired.

### Cited Findings
- Deepgram Voice Agent API is priced per connection minute ($0.050–0.163). Streaming Entity Detection costs +$0.0017/min and Keyterm Prompting +$0.0013/min — [Deepgram pricing](https://deepgram.com/pricing).
- Deepgram's intent, topic and summarization features are billed per token, not per hour — [Micdrop](https://micdrop.dev/blog/top-speech-to-text-apis-voice-agents) [3p]. Whether these are available on streaming was not verified.
- AssemblyAI: "The Voice Agent API is being retired, so don't quote it for new builds". The LLM Gateway is sold separately, and keyterms are updatable mid-stream on U3.6 Pro RT — [AssemblyAI pricing](https://www.assemblyai.com/pricing).
- AssemblyAI markets "entity-aware endpointing" [vendor] — [AssemblyAI blog](https://www.assemblyai.com/blog/best-api-models-for-real-time-speech-recognition-and-transcription).
- Cartesia: `turn.eager_end` gives "your LLM a head start" — [Cartesia Ink](https://www.cartesia.ai/ink). It is packaged with Sonic-3.5 TTS as a "full voice-agent stack" — [RuntimeWire](https://www.runtimewire.com/article/cartesia-sonic-35-ink-2-voice-agent-benchmarks).
- Speechmatics Flow is an agent platform, and Agent STT is distributed via LiveKit Inference — [Speechmatics Flow](https://www.speechmatics.com/flow); [Speechmatics Agent STT](https://www.speechmatics.com/company/articles-and-news/meet-agent-stt-powered-by-linden-1-fast-accurate-speech-recognition).
- Soniox positions its `<end>` token as the trigger "to call an LLM or execute a command", i.e. downstream action stays the app's job — [Soniox](https://soniox.com/docs/stt/rt/endpoint-detection).
- Practitioner guidance already describes the forehear pattern without a vendor product: start tool calls early at about 0.85 intent confidence and cancel if later partials change intent, with an estimated 2–5% wasted calls [3p, unmeasured] — [FutureAGI latency techniques](https://futureagi.com/blog/how-to-optimize-voice-agent-latency-2026/).
- A search for vendor "intent prefetch" launches found none. The analysis concluded intent classification "generally sits in your application layer, not in the STT API" — [Micdrop](https://micdrop.dev/blog/top-speech-to-text-apis-voice-agents).
- Framework speculation:
  - LiveKit `preemptive_generation` is enabled by default, LLM only, with max 3 retries and a 10 s cap — [voice/turn.py](https://github.com/livekit/agents/blob/055744e1505b1489976d06ca029b3001bc91ea55/livekit-agents/livekit/agents/voice/turn.py).
  - Pipecat holds back a speculative inference until the turn is confirmed — [turns/types.py](https://github.com/pipecat-ai/pipecat/blob/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/turns/types.py).
  - Pipecat ships `mem0` and `mcp_service` integrations in the same services tree, meaning retrieval and memory services sit beside STT in the framework — [Pipecat services tree](https://github.com/pipecat-ai/pipecat/tree/6fa9cf28886036d5d6c7dfd05ed3d6960245241a/src/pipecat/services).

### Inferences
- **Most likely bundlers.** These are the vendors that own both the turn signal and an agent runtime.
  - **Deepgram**: Flux eager EOT plus the Voice Agent API with function calling. Moving its "think" stage to run retrieval at `EagerEndOfTurn` would be a short step.
  - **Cartesia**: Ink-2 plus Sonic, marketed as a stack.
  - **Speechmatics**: Flow.
- **LiveKit is the biggest risk.** Adding a retrieval hook to the existing preemptive-generation path, which already has preflight, stale-cancel and retry limits, would directly compete with forehear's eager mode. It would not cover forehear's mid-utterance interim speculation.
- **Pure-STT vendors look unlikely to build retrieval.** Soniox, Gladia, Google, AWS and AssemblyAI (now unbundling) are moving toward "better signals for your app" (stable tokens, entity-aware endpointing, keyterms). That is complementary to forehear and makes forehear's inputs better.

### Gaps
- Not verified whether Deepgram's Voice Agent API exposes RAG or "knowledge" features, or runs function calls on EagerEndOfTurn. Not checked whether Speechmatics Flow has a knowledge-base feature.
- No changelog evidence found, either way, of OpenAI Realtime or Gemini Live adding server-side retrieval prefetch during user speech. This was not specifically searched this session.
