# Contributing

Thanks for helping make voice agents faster.

## Setup

```bash
git clone https://github.com/sagarthegreat/Infinity && cd Infinity
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,plots]"
pytest --ignore=tests/integrations       # core suite, < 5 s
pip install -e ".[pipecat,livekit]" && pytest tests/integrations
```

Before opening a PR:

```bash
ruff check src tests scripts examples && ruff format --check src tests scripts && mypy && pytest
```

## Good first contributions

* **A new policy** that beats `stable_prefix_eager` at fewer calls per turn.
  Add it to `forehear/policies.py`, register it in
  `forehear/bench/runner.py::standard_policies`, and paste `forehear bench`
  output in the PR. Negative results are welcome too: say what you tried.
* **New traces**: other ASR engines (Deepgram, AssemblyAI, Whisper-streaming,
  Parakeet), other languages, multi-turn dialogues (DSTC10 Track 2,
  SpokenWOZ), or anonymised production logs in the format in `data/README.md`.
* **Adapters** for more voice frameworks (TEN, Vocode, jambonz, NVIDIA ACE,
  OpenAI Agents SDK voice pipeline).
* **Latency profiles** measured on real stacks, with a source.

## Principles

* The controller stays **sans-IO** and dependency-free.
* Every benchmark number must be **reproducible** from the repository with one
  command, offline.
* Speculative work must stay **read-only**.
