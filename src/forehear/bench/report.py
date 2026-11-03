"""Render benchmark results as Markdown and (optionally) matplotlib figures."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

__all__ = ["markdown_report", "plot_all", "write_json"]

POLICY_ORDER = [
    "final_only",
    "eager_eot",
    "interval_1000ms",
    "interval_500ms",
    "stable_prefix",
    "stable_prefix_eager",
    "adaptive",
    "oracle",
]


def _order(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rank = {p: i for i, p in enumerate(POLICY_ORDER)}
    return sorted(rows, key=lambda r: rank.get(r["policy"], 99))


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def _ms(x: float) -> str:
    return f"{x:,.0f}"


def policy_table(rows: Sequence[dict[str, Any]]) -> str:
    head = (
        "| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy "
        "| calls/turn | recall@k Δ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    lines = []
    for r in _order(rows):
        lines.append(
            f"| `{r['policy']}` | {_ms(r['wait_mean_ms'])} | {_ms(r['wait_p90_ms'])} | "
            f"{_ms(r['saved_mean_ms'])} | {_pct(r['zero_wait_rate'])} | {_pct(r['coverage'])} | "
            f"{_pct(r['accuracy'])} | {r['calls_per_turn']:.2f} | {100 * r['recall_delta']:+.1f} pt |"
        )
    return head + "\n".join(lines) + "\n"


def headline_table(rows: Sequence[dict[str, Any]], scenario: str) -> str:
    sub = [r for r in rows if r["scenario"] == scenario]
    profiles = list(dict.fromkeys(r["profile"] for r in sub))
    policies = [p for p in POLICY_ORDER if any(r["policy"] == p for r in sub)]
    idx = {(r["policy"], r["profile"]): r for r in sub}
    out = "| policy | " + " | ".join(profiles) + " | calls/turn |\n"
    out += "|---|" + "---:|" * len(profiles) + "---:|\n"
    for p in policies:
        cells = []
        for prof in profiles:
            r = idx.get((p, prof))
            cells.append(f"{_ms(r['wait_mean_ms'])} ms" if r else "-")
        calls = idx.get((p, profiles[-1]))
        out += f"| `{p}` | " + " | ".join(cells) + f" | {calls['calls_per_turn']:.2f} |\n" if calls else ""
    return out


def markdown_report(
    rows: Sequence[dict[str, Any]],
    curve: Sequence[dict[str, float]],
    sweep: Sequence[dict[str, Any]],
    meta: dict[str, Any],
) -> str:
    md = ["# forehear benchmark results\n"]
    md.append(
        f"{meta['turns']:,} human-recorded spoken questions (HeySQuAD dev), streamed through "
        f"{meta['asr']} in {meta['chunk_ms']} ms chunks; retrieval over {meta['corpus']:,} SQuAD v2 "
        f"passages with {meta['retriever']}, top-{meta['k']}. End of turn fires {meta['eot_ms']:.0f} ms "
        "after the last word. Wait = time from end of turn until retrieved context is ready "
        "(lower is better). All numbers are deterministic; rerun with `forehear bench`.\n"
    )
    for scen in dict.fromkeys(r["scenario"] for r in rows):
        md.append(f"\n## Scenario `{scen}`: mean retrieval wait after end of turn\n")
        md.append(headline_table(rows, scen))
        for prof in dict.fromkeys(r["profile"] for r in rows if r["scenario"] == scen):
            sub = [r for r in rows if r["scenario"] == scen and r["profile"] == prof]
            md.append(f"\n### `{scen}` / `{prof}`\n")
            md.append(policy_table(sub))
    if curve:
        md.append("\n## How early is the answer findable?\n")
        md.append(
            "Share of all turns whose *current interim hypothesis* already retrieves a gold passage, "
            "by time relative to the end of the last word.\n\n| t (ms) | retrievable | still speaking |"
            "\n|---:|---:|---:|\n"
        )
        for c in curve:
            md.append(f"| {c['offset_ms']:+.0f} | {_pct(c['retrievable'])} | {_pct(c['speaking'])} |\n")
        md.append(f"\nFinal transcript recall@{meta['k']}: {_pct(curve[0]['final_recall'])}.\n")
    if sweep:
        md.append(f"\n## Reuse threshold sweep (`stable_prefix_eager`, `{sweep[0]['profile']}`)\n")
        md.append("| TokenCoverage threshold | wait mean | coverage | recall@k Δ |\n|---:|---:|---:|---:|\n")
        for s in sweep:
            md.append(
                f"| {s['threshold']:.1f} | {_ms(s['wait_mean_ms'])} | {_pct(s['coverage'])} | "
                f"{100 * s['recall_delta']:+.1f} pt |\n"
            )
    md.append(
        "\n### Column guide\n\n"
        "- **wait mean / p90**: ms from end of turn until context is ready.\n"
        "- **saved mean**: mean per-turn reduction vs. `final_only` (paired: same latency draws).\n"
        "- **ready at EOT**: share of turns with zero wait.\n"
        "- **coverage**: share of turns served by a speculative call.\n"
        "- **accuracy**: speculative calls that served a turn / speculative calls issued "
        "(hardware prefetchers degrade performance below ~40%; here a wrong guess only costs a call).\n"
        "- **calls/turn**: total retrieval calls per turn; `final_only` is 1.00.\n"
        "- **recall@k Δ**: change in gold-passage recall vs. retrieving on the final transcript.\n"
    )
    return "".join(md)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def plot_all(
    out: Path,
    rows: Sequence[dict[str, Any]],
    curve: Sequence[dict[str, float]],
    sweep: Sequence[dict[str, Any]],
) -> list[Path]:
    """Write PNG figures; returns the paths. Requires matplotlib."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    written: list[Path] = []

    if curve:
        fig, ax = plt.subplots(figsize=(7, 3.6))
        xs = [c["offset_ms"] for c in curve]
        ax.plot(
            xs,
            [100 * c["retrievable"] for c in curve],
            marker="o",
            lw=2,
            color="#2563eb",
            label="interim hypothesis retrieves a gold passage",
        )
        ax.plot(
            xs,
            [100 * c["speaking"] for c in curve],
            ls=":",
            color="#64748b",
            label="user has started speaking",
        )
        ax.axhline(100 * curve[0]["final_recall"], ls="--", color="#16a34a", label="final transcript recall")
        ax.axvline(0, color="#0f172a", lw=1)
        ax.text(10, 4, "last word ends", fontsize=8)
        ax.set_xlabel("ms relative to end of speech")
        ax.set_ylabel("% of turns")
        ax.set_ylim(0, 100)
        ax.set_title("How early is the answer findable?")
        ax.legend(loc="upper left", fontsize=8, frameon=False)
        fig.tight_layout()
        p = out / "retrievability.png"
        fig.savefig(p, dpi=160)
        plt.close(fig)
        written.append(p)

    colors = {
        "final_only": "#0f172a",
        "eager_eot": "#9333ea",
        "interval_1000ms": "#f59e0b",
        "interval_500ms": "#ea580c",
        "stable_prefix": "#2563eb",
        "stable_prefix_eager": "#0891b2",
        "adaptive": "#16a34a",
        "oracle": "#94a3b8",
    }
    for scen in dict.fromkeys(r["scenario"] for r in rows):
        sub = [r for r in rows if r["scenario"] == scen]
        profs = list(dict.fromkeys(r["profile"] for r in sub))
        fig, axes = plt.subplots(1, len(profs), figsize=(3.2 * len(profs), 3.4), squeeze=False)
        for ax, prof in zip(axes[0], profs, strict=True):
            for r in _order([r for r in sub if r["profile"] == prof]):
                ax.scatter(
                    r["calls_per_turn"],
                    r["wait_mean_ms"],
                    s=40,
                    color=colors.get(r["policy"], "k"),
                    label=r["policy"],
                    zorder=3,
                )
            ax.set_title(prof, fontsize=10)
            ax.set_xlabel("retrieval calls per turn")
            ax.grid(alpha=0.3)
        axes[0][0].set_ylabel("mean wait after end of turn (ms)")
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=min(8, len(labels)), fontsize=7, frameon=False)
        fig.suptitle(f"Latency vs. cost - scenario: {scen}", fontsize=11)
        fig.tight_layout(rect=(0, 0.1, 1, 1))
        p = out / f"tradeoff_{scen}.png"
        fig.savefig(p, dpi=160)
        plt.close(fig)
        written.append(p)

    if sweep:
        fig, ax1 = plt.subplots(figsize=(6, 3.4))
        th = [s["threshold"] for s in sweep]
        ax1.plot(th, [s["wait_mean_ms"] for s in sweep], marker="o", color="#2563eb", label="mean wait (ms)")
        ax1.set_xlabel("TokenCoverage reuse threshold")
        ax1.set_ylabel("mean wait (ms)", color="#2563eb")
        ax2 = ax1.twinx()
        ax2.plot(
            th, [100 * s["recall_delta"] for s in sweep], marker="s", color="#dc2626", label="recall Δ (pt)"
        )
        ax2.set_ylabel("recall@k change (pt)", color="#dc2626")
        ax2.spines["right"].set_visible(True)
        ax1.set_title(f"Reuse threshold: latency vs. quality ({sweep[0]['profile']})")
        fig.tight_layout()
        p = out / "validator_sweep.png"
        fig.savefig(p, dpi=160)
        plt.close(fig)
        written.append(p)
    return written
