# Benchmarks and Datasets for Offline Evaluation of Look-Ahead Retrieval for Voice Agents

Scope: datasets/benchmarks that let you simulate a stream of partial ASR transcripts over time, run retrieval on each prefix, and score whether the right passages are ready at end-of-turn (EOT). Also: metrics and voice-agent latency benchmarks.

Verification legend: items marked **[verified this session]** were checked via a web search or fetch in this session. Items marked **[prior knowledge, not re-verified]** come from the researcher's background knowledge, with the canonical URL. The report writer should treat their license and size details as needing confirmation.

---

## 1. Spoken QA / spoken retrieval datasets (audio + retrieval corpus + relevance labels)

### Takeaway
No public dataset was built for retrieval over partial or streaming spoken queries. Several spoken-QA sets can be repurposed because each spoken question is tied to a gold passage, which serves as the relevance label:
- **HeySQuAD** (CC BY 4.0, human-recorded audio)
- **SLUE-SQA-5** (CC BY-SA 4.0 / Apache 2.0, real spoken questions, Spoken Wikipedia corpus)
- **Spoken-SQuAD**
- **AudioCRAG** (from Stream RAG, Meta 2025; human split promised but not confirmed released)

Of these, AudioCRAG is the only one whose authors already simulated 500 ms partial transcripts from word timestamps, which is exactly the look-ahead setup.

### Cited Findings

**AudioCRAG (Stream RAG paper, arXiv 2510.02044, 2025)** [verified this session]
- The closest existing work to look-ahead retrieval. It is the spoken version of the CRAG benchmark's 2,706 text queries. — [Stream RAG](https://arxiv.org/html/2510.02044)
- It has two splits. — [Stream RAG](https://arxiv.org/html/2510.02044)
  - **AudioCRAG-Synthetic:** 1,862 queries from in-house TTS, filtered to drop any utterance with Whisper word errors or UTMOS below 3.5.
  - **AudioCRAG-Human:** 618 queries recorded by a diverse pool of participants.
- The paper says the training code and AudioCRAG-Human "will be released upon acceptance". No link or license was found on the page, so availability is unconfirmed as of this session. — [Stream RAG](https://arxiv.org/html/2510.02044)
- How partial transcripts are simulated: — [Stream RAG](https://arxiv.org/html/2510.02044)
  - Word-level timestamps come from the OWSM CTC v4 1B ASR model.
  - A partial transcript is emitted every 500 ms. A word that falls on a block boundary is left out of that block.
  - The fixed-interval baseline issues a tool query every 1 s. The model-triggered variant decides after each 500 ms block.
- Metrics: — [Stream RAG](https://arxiv.org/html/2510.02044)
  - Accuracy: a three-way LLM-judge score (Llama 4 Maverick) of +1 accurate, 0 missing, −1 incorrect.
  - Latency: first-token latency split into query generation, tool result, and response generation, reported at P50 and P90.
- Results with Qwen2.5-7B: — [Stream RAG](https://arxiv.org/html/2510.02044)
  - Accuracy rises from 26.3% to 34.2% on synthetic audio and from 26.9% to 37.4% on human audio (open-book versus model-triggered streaming RAG).
  - Tool-use latency is 3.37 s at baseline, cut by 20.7%.
  - The paper reports both a 9.8% P50 first-token reduction (Section 5.3) and 20.7% (Table 1) without reconciling them.
- The underlying CRAG text benchmark (Meta, KDD Cup 2024) brings its own web-page and mock-API retrieval corpus. — CRAG [prior knowledge, not re-verified]: [arXiv 2406.04744](https://arxiv.org/abs/2406.04744)

**HeySQuAD (Wu et al., 2023, arXiv 2304.13689)** [verified this session]
- Contents: — [arXiv](https://arxiv.org/abs/2304.13689v1); [HF human](https://huggingface.co/datasets/yijingwu/HeySQuAD_human/blob/main/README.md)
  - About 76k human-spoken and 97k machine-generated (TTS) questions over SQuAD contexts.
  - The human split is 71,990 train and 4,158 validation examples.
  - Each example includes audio, transcription, question, context, and answers.
- License: the HF cards (`yijingwu/HeySQuAD_human`, `yijingwu/HeySQuAD_machine`) list CC BY 4.0. This was seen in search snippets and the README was recently updated, so confirm on the live card. — [HF machine](https://huggingface.co/datasets/yijingwu/HeySQuAD_machine/tree/main)
- Use for look-ahead: the corpus is the SQuAD/Wikipedia paragraphs and the gold label is the paragraph containing the answer. Word timestamps are not provided, so they would have to be generated with forced alignment (see Section 2).

**SLUE-SQA-5 (SLUE Phase-2, ASAPP)** [verified this session for license; size from prior knowledge]
- Hosted as the `sqa5` config of `asapp/slue-phase-2` on HF. — [HF card](https://huggingface.co/datasets/asapp/slue-phase-2/blame/main/README.md)
- The questions are real spoken recordings of text questions from SQuAD 1.1, Natural Questions, WebQuestions, CuratedTREC, and TriviaQA. The documents are Spoken Wikipedia audio with transcripts and text-to-speech alignments. — [HF card](https://huggingface.co/datasets/asapp/slue-phase-2/blame/29adfa7523945441b2b33121c135f16ca74e17de/README.md)
- Licenses: — [HF card](https://huggingface.co/datasets/asapp/slue-phase-2/blame/main/README.md); [loader](https://huggingface.co/datasets/asapp/slue-phase-2/blob/73b36dce32e0626c7f6e8c52e5557c3c352187ec/slue-phase-2.py)
  - Questions from TriviaQA: Apache 2.0.
  - Questions from the other four sources: CC BY-SA 4.0.
  - Spoken Wikipedia documents and alignments: CC BY-SA 4.0.
  - Loader script: MIT.
- Paper: SLUE Phase-2. — [arXiv 2212.10525](https://arxiv.org/abs/2212.10525) [prior knowledge, not re-verified]
- Size, from memory: about 46k train, 1.9k dev, and 2.4k test questions. [prior knowledge, not re-verified; confirm on card]
- Used as a retrieval benchmark by: — [SpeechDPR](https://arxiv.org/abs/2401.13463); [WavRAG](https://arxiv.org/pdf/2502.14727); [VoiceTrace](https://arxiv.org/pdf/2609.18521)
  - SpeechDPR (spoken passage retrieval, top-k retrieval accuracy)
  - WavRAG
  - VoiceTrace-Bench (speech-to-speech retrieval)
- Its strength is real human question audio. Its passage collection is spoken, which is less typical of a voice-agent KB, but the transcripts can be used as a text corpus.

**Spoken-SQuAD (Li et al., Interspeech 2018)** [prior knowledge, not re-verified]
- SQuAD contexts were converted to speech with Google TTS and then passed through ASR, while the questions stay as text. About 37k train and 5.4k test QA pairs. — [arXiv 1804.00320](https://arxiv.org/abs/1804.00320); [GitHub chiahsuan156/Spoken-SQuAD](https://github.com/chiahsuan156/Spoken-SQuAD)
- Because the spoken side is the passage, not the question, it is a poor fit for spoken-query look-ahead. WavRAG still used it for evaluation. — [WavRAG](https://arxiv.org/pdf/2502.14727) [verified this session]
- No explicit license was found (flag).

**NMSQA (Natural Multi-Speaker Spoken QA; DUAL paper, Lin et al., 2022)** [prior knowledge, not re-verified]
- SQuAD v1.1 with TTS-synthesized passages and questions, plus human-spoken test questions. — [arXiv 2203.04911](https://arxiv.org/abs/2203.04911); HF: `voidful/NMSQA` (verify)
- Includes word or frame alignments for answer spans. License uncertain.

**Spoken-CoQA (You et al., 2020/2022)** [prior knowledge, not re-verified]
- A conversational spoken QA set built from CoQA with TTS audio and ASR transcripts. It is multi-turn, which makes it useful for conversation-history-aware look-ahead. — [arXiv 2010.08923](https://arxiv.org/abs/2010.08923)
- License and current download status uncertain.

**SD-QA (Spoken Dialectal QA, Faisal et al., Findings of EMNLP 2021)** [prior knowledge, not re-verified]
- Spoken versions of TyDi-QA questions in 5 languages and many dialects (English, Arabic, Bengali, Kiswahili, Korean). TyDi supplies the Wikipedia passages that act as relevance labels. — [arXiv 2109.12072](https://arxiv.org/abs/2109.12072); [GitHub ffaisal93/SD-QA](https://github.com/ffaisal93/SD-QA)
- Good for robustness to accents. License to verify.

**LibriSQA** [prior knowledge, not re-verified]
- Spoken QA over LibriSpeech, where the speech is the content, not the query. Poor fit for look-ahead. — [arXiv 2308.10390](https://arxiv.org/abs/2308.10390)

**Speech-native RAG papers and their eval sets (2024–2026)** [verified this session unless noted]
- **WavRAG (arXiv 2502.14727):** — [WavRAG](https://arxiv.org/pdf/2502.14727)
  - Evaluated on HotpotQA, Spoken-SQuAD, SLUE-SQA-5, and a custom mixed-modality set.
  - Trained on 1.5M samples across five retrieval scenarios.
  - Reports retrieval comparable to ASR-then-text RAG with about a 10x speedup.
- **SpeechRAG (Min et al., arXiv 2412.16500):** — [SpeechRAG](https://arxiv.org/html/2412.16500v2)
  - Retrieves audio passages directly through a speech adapter on a frozen LLM retriever, evaluated on spoken QA datasets.
  - The authors say code and dataset will be released (release status unconfirmed).
- **Speech-to-speech dialogue with end-to-end RAG (arXiv 2505.00028):** reportedly released a speech version of HotpotQA. Seen only as a search snippet. — [alphaxiv](https://www.alphaxiv.org/abs/2505.00028.md)
- **VoxRAG (MAGMAR 2025):** — [ACL Anthology](https://aclanthology.org/2025.magmar-1.3.pdf)
  - Transcription-free speech-to-speech RAG using CLAP embeddings and FAISS.
  - Eval set is only 50 queries from a single native speaker, scored with Recall@10 and nDCG.
  - Too small to serve as a benchmark.
- **TextlessRAG (arXiv 2509.07538):** speech-in, speech-out RAG over visual documents, with a new bilingual benchmark and a Chinese visual-doc RAG dataset. — [arXiv](https://arxiv.org/pdf/2509.07538)
- **VoiceTrace-Bench (arXiv 2609.18521):** "hybrid speech retrieval" in which a reference sample names the speaker and the query asks for content. It reuses SLUE-SQA-5. The arXiv ID was seen only in search results, so confirm before relying on it. — [arXiv](https://arxiv.org/pdf/2609.18521)
- **CORAL (Findings of NAACL 2025):** a text-only multi-turn conversational RAG benchmark covering passage retrieval, generation, and citation. It could be paired with TTS. — [ACL Anthology](https://aclanthology.org/2025.findings-naacl.72/)

### Inferences
- **Best real-speech starting points:**
  - **SLUE-SQA-5:** real spoken questions and a Wikipedia corpus, with permissive-ish CC BY-SA and Apache licenses (share-alike applies).
  - **HeySQuAD-human:** CC BY 4.0, very large, but the questions are SQuAD-style and lean on lexical overlap with the passage.
- **AudioCRAG** is the most on-target design (open-domain, web-style queries, 500 ms partial transcripts). If AudioCRAG-Human has not been released, its protocol can be rebuilt from public CRAG text plus TTS.
- **SQuAD-derived question bias:** SQuAD-derived spoken questions (HeySQuAD, Spoken-SQuAD, NMSQA) were written while looking at the passage, so they overlap lexically with it. Prefixes may therefore be unrealistically easy to retrieve on. NQ and TriviaQA-derived questions in SLUE-SQA-5, and CRAG, are more natural.
- **Question placement:** for look-ahead, what matters is where the content words fall inside the question. SQuAD-style "What year did X..." questions put the entity late, which makes early retrieval hard and the test informative.

### Gaps
- No dataset could be confirmed for any of these names: "Spoken Natural Questions / SpokenNQ", "Spoken TriviaQA", "VoxPopuli QA", "spoken MS MARCO", "spoken BEIR", or a spoken TextVQA. SLUE-SQA-5 already contains spoken NQ and TriviaQA questions. Treat the others as possibly nonexistent unless another researcher finds them.
- AudioCRAG-Human release status and license are unknown.
- The SpeechRAG dataset release status is unknown.
- NMSQA and Spoken-CoQA licenses were not checked.

---

## 2. Word-level timestamps for spoken queries (needed to simulate the partial-transcript stream)

### Takeaway
Almost no spoken-QA dataset ships word-level timestamps for its questions. SLUE-SQA-5 has alignments for its documents. The standard approach, which Stream RAG uses, is to generate word timestamps with a CTC or forced-alignment model, then emit cumulative prefixes on a fixed clock (for example every 500 ms). That makes any audio+text QA set usable, and TTS makes any text QA set usable.

### Cited Findings
- Stream RAG's reference method: OWSM CTC v4 1B produces word timestamps, and partial transcripts are cut every 500 ms, excluding any word that straddles a boundary. — [Stream RAG](https://arxiv.org/html/2510.02044) [verified this session]
- In SLUE-SQA-5, the Spoken Wikipedia documents include text-to-speech alignments under CC BY-SA 4.0. — [HF card](https://huggingface.co/datasets/asapp/slue-phase-2/blame/main/README.md) [verified this session]
- In DSTC10 Track 2, each user turn comes with an ASR n-best list, which supports testing robustness to ASR noise. Word timestamps are not mentioned. — [DSTC10 Track 2 paper](https://cdn.amazon.science/cb/32/e83c54de4b0f9b00c023d2150258/knowledge-grounded-task-oriented-dialogue-modeling-on-spoken-conversations-track-at-dstc10.pdf) [verified this session]
- Alignment tools [prior knowledge, not re-verified]:
  - **WhisperX:** word timestamps via wav2vec2 forced alignment, BSD-2 license. — [arXiv 2303.00747](https://arxiv.org/abs/2303.00747); [GitHub m-bain/whisperX](https://github.com/m-bain/whisperX)
  - **Montreal Forced Aligner:** MIT license. — [docs](https://montreal-forced-aligner.readthedocs.io/)
  - **torchaudio CTC forced alignment (MMS):** — [tutorial](https://pytorch.org/audio/stable/tutorials/ctc_forced_alignment_api_tutorial.html)
  - **NeMo Forced Aligner.**
  - **TTS engines that return word-level timing** natively (e.g., Azure TTS word-boundary events, Amazon Polly speech marks), which avoids alignment entirely for synthetic queries.
- AmazonQAC includes timestamps for each typed prefix, but these are keystroke timings, not speech timings. — [HF README](https://huggingface.co/datasets/amazon/AmazonQAC/blame/main/README.md) [verified this session]

### Inferences
- A realistic simulation should use a streaming ASR's real interim hypotheses (which revise earlier words) rather than truncated final transcripts. Truncated forced-aligned transcripts overstate prefix quality because they lack the "flicker" of interim results.
  - Recommended: run both an "oracle prefix" condition (forced-aligned ground-truth words) and a "streaming ASR interim" condition (for example, replaying audio through an open streaming ASR such as NeMo FastConformer, or Whisper in a streaming wrapper).
- Using a TTS speaking rate around 150 words per minute versus human audio changes how much lead time exists. Results should be reported on human audio where available (HeySQuAD-human, SLUE-SQA-5, AudioCRAG-Human).

### Gaps
- No public spoken-QA set was found that ships interim (unstable) streaming ASR hypotheses with timestamps. This would have to be generated.

---

## 3. Conversational / customer-support datasets with audio or spoken turns plus a knowledge base

### Takeaway
DSTC10 Track 2 (and its DSTC9 Track 1 text precursor) is the only benchmark found that combines real spoken human-human task dialogue with an unstructured FAQ knowledge base and turn-level knowledge-snippet labels. That makes it the most directly relevant knowledge-grounded spoken benchmark for a "voice agent with KB" setting.
- SpokenWOZ offers large real-speech audio (CC BY-NC 4.0), but the grounding is slot/DB, not passages.
- Doc2Dial, MultiDoc2Dial, and ABCD are text-only but have document or KB grounding and could be voiced with TTS.

### Cited Findings

**DSTC10 Track 2 (Knowledge-grounded Task-oriented Dialogue Modeling on Spoken Conversations, Amazon Alexa AI)** [verified this session]
- Contents: — [track paper](https://cdn.amazon.science/cb/32/e83c54de4b0f9b00c023d2150258/knowledge-grounded-task-oriented-dialogue-modeling-on-spoken-conversations-track-at-dstc10.pdf); [arXiv 2109.13489](https://arxiv.org/pdf/2109.13489)
  - Spoken human-human dialogues about touristic information.
  - Subtasks: knowledge-seeking turn detection, knowledge selection, and knowledge-grounded response generation.
  - The validation set re-releases 263 spoken conversations from the DSTC9 test set, ASR-transcribed, with an n-best list per user turn.
  - The challenge drew 99 entries.
- Under ASR errors, knowledge-seeking turn detection F1 drops from 0.9911 (text) to 0.7602. — [arXiv 2209.02251](https://arxiv.org/pdf/2209.02251v1.pdf)
- Follow-up work aggregates the N-best lists for knowledge selection. — [Interspeech 2023](https://www.isca-archive.org/interspeech_2023/zhu23e_interspeech.pdf)
- The data is reportedly on GitHub at `alexa/alexa-with-dstc10-track2-dataset`, which was not verified this session. Its license is also not verified, though the DSTC9 Track 1 repo was Apache 2.0 from memory [prior knowledge, not re-verified].
- Caveat: as far as is known, the released data is ASR transcripts and n-best lists rather than raw audio. Confirm on the repo.
- Use for look-ahead: the knowledge selection subtask is retrieval with labels. Prefix simulation needs word timing, which is absent unless audio was released.

**SpokenWOZ (Si et al., NeurIPS 2023 Datasets and Benchmarks)** [verified this session]
- 203k turns, 5.7k dialogues, and 249 hours of real human-to-human spoken conversation. License CC BY-NC 4.0 (non-commercial). Downloads are on the project site. — [arXiv 2305.13040](https://arxiv.org/pdf/2305.13040); [site](https://spokenwoz.github.io)
- The grounding is MultiWOZ-style DST and database, not free-text passages. It works for "entity / DB-row look-ahead" retrieval, but not for passage RAG without adaptation.

**DSTC11 Track 3 "Speech-Aware Dialog Systems" (spoken MultiWOZ)** [prior knowledge, not re-verified]
- MultiWOZ user turns as TTS and human-read audio, with ASR transcripts and timing. Useful for DST under speech conditions; not knowledge-passage grounded. — [DSTC11 site](https://dstc11.dstc.community/tracks)

**Text-only knowledge-grounded dialogue sets that could be voiced with TTS** [prior knowledge, not re-verified]
- **Doc2Dial / MultiDoc2Dial (IBM):** goal-oriented dialogues grounded in government-service documents, with grounding-span labels. Doc2Dial is CC BY 3.0 per memory. — [Doc2Dial arXiv 2011.06623](https://arxiv.org/abs/2011.06623); [MultiDoc2Dial arXiv 2109.12595](https://arxiv.org/abs/2109.12595)
- **ABCD (Action-Based Conversations Dataset, ASAPP):** about 10k customer-service dialogues with agent guidelines (a "KB" of action flows), MIT license per memory. — [arXiv 2104.00783](https://arxiv.org/abs/2104.00783); [GitHub asappresearch/abcd](https://github.com/asappresearch/abcd)
- **Taskmaster-1/2/3 (Google):** includes spoken two-person dialogues (Taskmaster-1 has "spoken" and "written" splits), released as transcripts without audio. CC BY 4.0 per memory. — [arXiv 1909.05358](https://arxiv.org/abs/1909.05358)
- **τ-Knowledge (`banking_knowledge` domain in τ²-bench):** a knowledge-retrieval customer-support domain that can be run in voice mode with `--audio-native`. — [tau2-bench repo](https://github.com/sierra-research/tau2-bench) [verified this session; paper arXiv 2603.04370 per repo, not fetched]

### Inferences
- For a customer-support voice-agent KB evaluation, the strongest options are:
  - DSTC10 Track 2 (real spoken, FAQ KB, snippet labels).
  - τ-Knowledge in voice mode (an end-to-end agent context, KB retrieval, MIT-licensed harness).
  - Doc2Dial or MultiDoc2Dial voiced with TTS and timestamps (document passages with grounding labels).
- SpokenWOZ's real conversational audio, with disfluencies and fillers, is valuable for stress-testing prefix stability, even without passage labels.

### Gaps
- The DSTC10 Track 2 repo license and whether raw audio was released were not confirmed.
- No spoken version of ABCD, Doc2Dial, or MultiDoc2Dial was found.

---

## 4. Voice agent benchmarks measuring latency, turn-taking, and full-duplex behavior

### Takeaway
Latency and turn-taking benchmarks exist, but none score retrieval readiness. Their metrics (first-token or first-audio latency, P50/P90, turn-take rate, interruption handling) can be borrowed and combined with retrieval metrics.
- **Full-Duplex-Bench v1/v2/v3:** v3 targets tool use under disfluent real speech, with a latency breakdown.
- **τ-Voice / τ²-bench voice mode:** task success, MIT license.
- **Stream RAG:** the per-stage latency decomposition is the most relevant design to copy.

### Cited Findings
- **Full-Duplex-Bench v1 (arXiv 2503.04721):** evaluates pause handling, backchanneling, turn-taking, and user interruption for full-duplex spoken dialogue models. Code and data are on GitHub. — [arXiv](https://arxiv.org/html/2503.04721v3) [verified this session]
- **Full-Duplex-Bench v2:** — [ACL 2026 short](https://aclanthology.org/2026.acl-short.4.pdf); [emergentmind summary](https://www.emergentmind.com/topics/full-duplex-bench-v2-fdb-v2)
  - Multi-turn streaming with an automated examiner, under Fast and Slow pacing.
  - Task families: daily, correction, entity tracking, and safety.
  - Turn-taking is rated 1–5 per turn on handoff naturalness, overlap, and latency.
- **Full-Duplex-Bench v3 (arXiv 2604.04847, April 2026):** — [arXiv](https://arxiv.org/abs/2604.04847); [HF paper page](https://huggingface.co/papers/2604.04847.md)
  - Tool use under real human disfluent audio annotated for 5 disfluency categories, with chained API-call scenarios.
  - Metrics: tool-use accuracy, turn-taking, and a latency breakdown across listening, tool execution, and speech generation.
  - An aggregator reports Gemini Live 3.1 as fastest (4.25 s, 78.0% turn-take rate) and a cascaded Whisper→GPT-4o→TTS baseline as slowest (10.12 s, perfect turn-taking). These figures come from secondary aggregator pages and were not confirmed against the primary paper.
- **τ²-bench voice (τ-Voice):** — [tau2-bench repo](https://github.com/sierra-research/tau2-bench) [verified this session]
  - Runs full-duplex evaluation through realtime audio APIs (OpenAI, Gemini, xAI) with a simulated caller.
  - `voice-v1`: English, 278 calls (50 airline, 114 retail, 114 telecom).
  - `voice-v2` (τ-i18n): 6 languages × 3 domains × 50 tasks, for 900 calls.
  - Repo license is MIT.
  - Post-run judges score naturalness, speech fidelity, and tool use. The README does not describe latency or turn-taking metrics.
  - The repo lists the τ-Voice paper as arXiv 2603.13686 (not fetched).
- **Telephony audio:** one review notes that τ-Voice is the closest public benchmark to a real support call, but phone conditions need 8 kHz μ-law conversion. — [Evalgent blog](https://www.evalgent.com/blog/voice-agent-benchmarks-explained) (secondary)
- **Open-source latency harnesses:** — [GitHub](https://github.com/openbenchmarks-labs/voice-agent-latency); [Daily blog](https://www.daily.co/blog/benchmarking-llms-for-voice-agent-use-cases/)
  - `openbenchmarks-labs/voice-agent-latency` measures TTFAB (time to first audio byte) from the end of user speech.
  - Daily's aiewf-eval tests latency, tool calling, instruction following, and knowledge grounding in long multi-turn conversations.
- **Tool-call latency (secondary source):** median perceived latency was 1,392 ms overall versus 3,384 ms on tool-call turns. — [HF blog: Voice Agent Latency Playbook](https://huggingface.co/blog/dvalle08/voice-agent-latency-playbook) (small study, community blog)
- **Other 2026 benchmarks (titles seen only):**
  - EVA-Bench, an end-to-end voice agent evaluation framework. — [arXiv 2605.13841](https://arxiv.org/pdf/2605.13841)
  - "Voice Agents under Acoustic Stress". — [arXiv 2609.29452](https://arxiv.org/pdf/2609.29452)
  - A community landscape table of voice-agent benchmarks. — [HF dataset](https://huggingface.co/datasets/chatjesus/voice-agent-benchmark-landscape)
- **Speech-LLM capability benchmarks (not latency-focused):** — [VocalBench](https://arxiv.org/html/2505.15727v3); [URO-Bench](https://preview.aclanthology.org/dashboard/2025.findings-emnlp.933)
  - **VoiceBench** (arXiv 2410.17196): about 5,982 instances covering general knowledge, instruction following, safety, and robustness to speaker and environment variation.
  - **URO-Bench** (arXiv 2502.17810, Findings of EMNLP 2025): about 6,946 instances covering Understanding, Reasoning, and Oral conversation, with Mandarin subsets.
- **Big Bench Audio:** a speech reasoning benchmark. Only thin descriptions were found. — [llmreference](https://www.llmreference.com/benchmark/big-bench-audio)
  - From prior knowledge (not re-verified): Artificial Analysis released it on HF as `ArtificialAnalysis/big_bench_audio`, with about 1,000 audio questions adapted from Big Bench Hard.
- **Talk Arena (talkarena.org, Stanford SALT) and VERA:** not searched this session. They are named in the assignment but unverified.
- **Commercial eval platforms (Coval, Hamming, Cekura):** not searched this session. From prior knowledge they are platforms (simulation and observability) rather than public benchmark datasets.

### Inferences
- None of these benchmarks measure retrieval readiness at EOT. The natural combination is:
  - Stream RAG's per-stage first-token latency decomposition (P50/P90)
  - Full-Duplex-Bench v3's disfluent real audio, as a stress test for prefix-triggered retrieval
  - τ-Knowledge voice for end-to-end task success with KB retrieval
- The cascaded baseline's 10 s figure in FDB-v3 (if accurate) suggests that retrieval and tool latency after EOT dominates in cascaded stacks, which is exactly what look-ahead targets.

### Gaps
- Talk Arena, VERA, and the vendor platforms were not verified.
- FDB-v3's primary numbers were not confirmed.
- No benchmark reports "retrieval completed before EOT" rates.

---

## 5. Existing benchmarks for retrieval or understanding on partial / incremental queries

### Takeaway
Two kinds of resources exist:
- **Incremental-intent resources** (inCLINC, incremental ATIS).
- **Query auto-completion (QAC) datasets** with real typed prefixes: AmazonQAC (395M samples, 2024) and legacy AOL logs.

These are the main precedents for scoring predictions on partial inputs. No benchmark was found for passage retrieval on spoken prefixes other than the AudioCRAG/Stream RAG setup.

### Cited Findings
- **AmazonQAC (Everaert, Patki, Zheng, Potts; EMNLP 2024; arXiv 2411.04129):** — [arXiv](https://arxiv.org/pdf/2411.04129); [HF README](https://huggingface.co/datasets/amazon/AmazonQAC/blame/main/README.md)
  - About 395M training samples and a 20k test set.
  - Each row pairs the final query with the actual sequence of typed prefixes ("s", "si", "sin" ... "sink rack"), plus query ID, session ID, and timestamps.
  - Earlier QAC datasets synthesized prefixes rather than recording what users typed.
  - Fine-tuned LLMs did best but reached only about half the theoretical maximum.
  - License not checked this session. From prior knowledge it is CC BY-NC 4.0, which needs confirming.
- **inCLINC (Hrycyk, Zarcone, Hahn; NLP4ConvAI 2021):** — [ACL Anthology](https://aclanthology.org/2021.nlp4convai-1.6)
  - Partial and full utterances, derived from CLINC150, with human annotations of the plausible intents at each prefix.
  - The authors argue that scoring partial-input predictions against the final label is problematic. They propose entropy reduction (how fast annotators converge) and warn that a classifier converging before humans may be exploiting artifacts.
  - Prefixes were cut at surprisal peaks and troughs. Word-savings metrics are reported on SNIPS.
- **Incremental online SLU (arXiv 1910.10287):** intent detection on streamed ATIS without utterance boundaries. Intent can often be detected accurately before end-of-sentence. — [arXiv](https://arxiv.org/pdf/1910.10287)
- **AOL query log (2006)** [prior knowledge, not re-verified]:
  - The classic QAC benchmark, with prefixes synthesized from complete queries.
  - It has known privacy issues, and its availability and ethics are contested. Use with caution.
  - The ir_datasets "aol-ia" variant links to Internet Archive documents. — [ir_datasets AOL-IA](https://ir-datasets.com/aol-ia.html)
- **MS MARCO / ORCAS** [prior knowledge, not re-verified]:
  - Real web queries with relevance labels, often used for synthetic-prefix retrieval experiments.
  - No spoken version was found (see Section 1 gaps).

### Inferences
- **Metrics to borrow from QAC:** MRR and success@k per prefix length, and keystrokes or words saved before the target appears in the top-k. In speech these map onto "milliseconds (or words) before EOT at which the gold passage first enters the top-k and stays there".
- **Metrics to borrow from inCLINC:** human-plausibility labels and entropy. Early retrieval against an ambiguous prefix should be judged against the set of plausible intents, not only the final one, because a speculative retrieval for the wrong but plausible intent is not a "bug".
- **Proposed look-ahead metrics** (researcher's synthesis; not an established standard):
  1. **Recall@k at EOT** of the look-ahead cache versus retrieval on the full transcript (quality parity).
  2. **Time-to-ready / lead time:** time between the gold passage's first stable appearance in the top-k and EOT. Report its distribution and the percentage with lead time ≥ 0 (ready by EOT).
  3. **Prefix recall curve:** Recall@k as a function of the fraction of utterance elapsed, or of absolute ms before EOT (the analogue of QAC per-prefix MRR).
  4. **Post-EOT retrieval latency saved,** and end-to-end first-token or first-audio latency at P50/P90 (Stream RAG; TTFAB).
  5. **Cost:** number of retrieval calls per turn, and wasted retrievals (Stream RAG's fixed 1 s versus model-triggered comparison is the precedent).
  6. **Downstream answer accuracy** with an LLM judge (+1 / 0 / −1, as in Stream RAG and CRAG).

### Gaps
- No benchmark was found that scores passage retrieval on incremental spoken (or typed) queries with relevance labels, other than the AudioCRAG/Stream RAG setup.
- inCLINC's download location and license were not confirmed.
- AmazonQAC's license was not confirmed.
