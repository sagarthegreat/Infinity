"""A LiveKit agent whose knowledge-base lookups start while the user is still talking.

    pip install "forehear[livekit]" "livekit-agents[deepgram,openai,cartesia,silero]"
    export LIVEKIT_URL=... LIVEKIT_API_KEY=... LIVEKIT_API_SECRET=...
    export DEEPGRAM_API_KEY=... OPENAI_API_KEY=... CARTESIA_API_KEY=...
    python examples/livekit_agent.py dev

The only forehear-specific lines are marked with ``# forehear``.
"""

from __future__ import annotations

from livekit.agents import AgentSession, JobContext, WorkerOptions, cli

from forehear import BM25Index, Lookahead, with_latency  # forehear
from forehear.integrations.livekit import LookaheadAgent, attach  # forehear

KB = BM25Index(
    [
        ("returns", "Damaged items can be returned within 30 days for a full refund or a replacement."),
        ("shipping", "Standard shipping takes 3 to 5 business days; express arrives next day."),
        ("warranty", "Electronics carry a one-year limited warranty covering manufacturing defects."),
    ]
)
search_kb = with_latency(lambda q: KB.search(q, 2), 350)  # replace with your read-only KB call


class SupportAgent(LookaheadAgent):  # forehear: instead of livekit.agents.Agent
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a concise support agent. Use the passages provided.",
            lookahead=Lookahead(retrieve=search_kb),  # forehear
        )


async def entrypoint(ctx: JobContext) -> None:
    from livekit.plugins import cartesia, deepgram, openai, silero

    await ctx.connect()
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(),
    )
    agent = SupportAgent()
    attach(session, agent.lookahead)  # forehear: feed interim transcripts
    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
