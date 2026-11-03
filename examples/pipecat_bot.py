"""A Pipecat voice bot whose knowledge-base lookups start while the user is still talking.

Requires API keys for the services you choose (this example: Deepgram, OpenAI,
Cartesia) and a microphone/speaker for the local transport:

    pip install "forehear[pipecat]" "pipecat-ai[deepgram,openai,cartesia,silero,local]"
    export DEEPGRAM_API_KEY=... OPENAI_API_KEY=... CARTESIA_API_KEY=...
    python examples/pipecat_bot.py

The only forehear-specific lines are marked with ``# forehear``.
"""

from __future__ import annotations

import asyncio
import os

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.workers.runner import WorkerRunner

from forehear import BM25Index, Lookahead, with_latency  # forehear
from forehear.integrations.pipecat import lookahead_processors  # forehear

# Stand-in for your real knowledge base. `with_latency` makes it behave like a
# hosted one; replace with e.g. an async call to your vector DB. Must be read-only.
KB = BM25Index(
    [
        ("returns", "Damaged items can be returned within 30 days for a full refund or a replacement."),
        ("shipping", "Standard shipping takes 3 to 5 business days; express arrives next day."),
        ("warranty", "Electronics carry a one-year limited warranty covering manufacturing defects."),
    ]
)
search_kb = with_latency(lambda q: KB.search(q, 2), 350)


def build_worker() -> PipelineWorker:
    transport = LocalAudioTransport(LocalAudioTransportParams(audio_in_enabled=True, audio_out_enabled=True))
    stt = DeepgramSTTService(api_key=os.environ.get("DEEPGRAM_API_KEY", ""))
    llm = OpenAILLMService(
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        settings=OpenAILLMService.Settings(model="gpt-4o-mini"),
    )
    tts = CartesiaTTSService(
        api_key=os.environ.get("CARTESIA_API_KEY", ""),
        settings=CartesiaTTSService.Settings(voice="71a7ad14-091c-4e8e-a314-022ece01c121"),
    )
    system = "You are a concise support agent. Use the passages provided."
    context = LLMContext(messages=[{"role": "system", "content": system}])
    aggregators = LLMContextAggregatorPair(
        context, user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer())
    )

    lookahead = Lookahead(retrieve=search_kb)  # forehear
    tap, inject = lookahead_processors(lookahead)  # forehear

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            tap,  # forehear: watches interim transcripts, starts retrieval early
            aggregators.user(),
            inject,  # forehear: adds the (already retrieved) context before the LLM
            llm,
            tts,
            transport.output(),
            aggregators.assistant(),
        ]
    )
    return PipelineWorker(pipeline)


async def main() -> None:
    await WorkerRunner().run(build_worker())


if __name__ == "__main__":
    asyncio.run(main())
