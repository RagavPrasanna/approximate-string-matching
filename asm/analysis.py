"""Turn benchmark CSV into figures and markdown tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PALETTE = {
    "sellers_full": "#1f77b4",
    "sellers_rolling": "#2ca02c",
    "sellers_pruned": "#ff7f0e",
    "landau_vishkin": "#d62728",
    "kmp": "#9467bd",
    "distance_rolling": "#1f77b4",
    "distance_banded": "#ff7f0e",
}
LABELS = {
    "sellers_full": "Sellers full matrix",
    "sellers_rolling": "Sellers rolling rows",
    "sellers_pruned": "Sellers threshold-pruned",
    "landau_vishkin": "Landau-Vishkin + LCE",
    "kmp": "KMP (k = 0)",
    "distance_rolling": "Rolling-row Levenshtein",
    "distance_banded": "Banded Levenshtein",
}
MARKERS = {
    "sellers_full": "o",
    "sellers_rolling": "s",
    "sellers_pruned": "^",
    "landau_vishkin": "D",
    "kmp": "P",
    "distance_rolling": "o",
    "distance_banded": "s",
}


def load(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame["status"] == "ok"].copy()
    for column in ("n", "m", "k", "median_ms", "peak_kib", "matches"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def line_plot(
    frame: pd.DataFrame,
    experiment: str,
    x: str,
    y: str,
    title: str,
    ylabel: str,
    output: Path,
    *,
    logx: bool = False,
    logy: bool = False,
) -> None:
    data = frame[frame["experiment"] == experiment]
    if data.empty:
        return
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for algorithm in data["algorithm"].unique():
        subset = data[data["algorithm"] == algorithm].sort_values(x)
        ax.plot(
            subset[x],
            subset[y],
            marker=MARKERS.get(algorithm, "o"),
            linewidth=1.8,
            markersize=5,
            color=PALETTE.get(algorithm),
            label=LABELS.get(algorithm, algorithm),
        )
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel(x if x != "n" else "Text length n")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170)
    plt.close(fig)


def bar_plot(
    frame: pd.DataFrame,
    experiment: str,
    title: str,
    output: Path,
) -> None:
    data = frame[frame["experiment"] == experiment]
    if data.empty:
        return
    cases = list(dict.fromkeys(data["case"]))
    algorithms = list(dict.fromkeys(data["algorithm"]))
    width = 0.8 / max(1, len(algorithms))
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    for index, algorithm in enumerate(algorithms):
        subset = data[data["algorithm"] == algorithm].set_index("case")
        values = [subset["median_ms"].get(case, float("nan")) for case in cases]
        offsets = [i + (index - (len(algorithms) - 1) / 2) * width for i in range(len(cases))]
        ax.bar(
            offsets,
            values,
            width=width,
            label=LABELS.get(algorithm, algorithm),
            color=PALETTE.get(algorithm),
            alpha=0.9,
        )
    ax.set_xticks(range(len(cases)))
    ax.set_xticklabels([case.replace("-dna", "") for case in cases], rotation=15, ha="right")
    ax.set_ylabel("Median runtime (ms)")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170)
    plt.close(fig)


def growth_plot(frame: pd.DataFrame, output: Path) -> None:
    data = frame[(frame["experiment"] == "text_length") & (frame["algorithm"].isin(
        ["sellers_rolling", "sellers_pruned", "landau_vishkin"]
    ))].copy()
    if data.empty:
        return
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for algorithm in data["algorithm"].unique():
        subset = data[data["algorithm"] == algorithm].sort_values("n")
        ax.plot(
            subset["n"],
            subset["median_ms"],
            marker=MARKERS.get(algorithm, "o"),
            color=PALETTE.get(algorithm),
            label=LABELS.get(algorithm, algorithm),
        )
    # Visual reference slopes anchored at the smallest measured point.
    n0 = float(data["n"].min())
    t0 = float(data[data["n"] == n0]["median_ms"].min())
    ns = sorted(data["n"].unique())
    ax.plot(ns, [t0 * (n / n0) ** 1 for n in ns], "k--", linewidth=0.9, label="linear reference")
    ax.plot(ns, [t0 * (n / n0) ** 2 for n in ns], "k:", linewidth=0.9, label="quadratic reference")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Text length n")
    ax.set_ylabel("Median runtime (ms, log scale)")
    ax.set_title("Empirical growth against reference slopes")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170)
    plt.close(fig)


def markdown_table(
    frame: pd.DataFrame,
    experiment: str,
    value: str = "median_ms",
    by_case: bool = False,
    sort_fields: tuple[str, ...] | None = None,
) -> str:
    data = frame[frame["experiment"] == experiment].copy()
    if data.empty:
        return ""
    data["algorithm"] = data["algorithm"].map(lambda x: LABELS.get(x, x))
    if by_case:
        if sort_fields:
            data = data.sort_values(list(sort_fields))
        order = list(dict.fromkeys(data["case"]))
        data["case"] = pd.Categorical(data["case"], categories=order, ordered=True)
    index = ["case"] if by_case else ["n", "m", "k"]
    pivot = data.pivot_table(
        index=index,
        columns="algorithm",
        values=value,
        aggfunc="first",
    )
    if value == "median_ms":
        pivot = pivot.round(3)
    else:
        pivot = pivot.round(1)
    pivot.columns.name = None
    text = pivot.to_markdown()
    return text.replace("nan", "—")


def write_report(frame: pd.DataFrame, output: Path) -> None:
    lines = [
        "# Generated benchmark analysis",
        "",
        "All times are per-call medians from interleaved, batched timing rounds. "
        "The tables use the lower envelope across three independent benchmark "
        "suite runs to reduce shared-machine noise. End positions are 0-based "
        "and exclusive.",
        "",
        "## Runtime versus text length",
        "",
        markdown_table(frame, "text_length"),
        "",
        "## Runtime versus pattern length",
        "",
        markdown_table(frame, "pattern_length"),
        "",
        "## Runtime versus error threshold",
        "",
        markdown_table(frame, "threshold"),
        "",
        "## Alphabet and natural language",
        "",
        markdown_table(
            frame, "alphabet", by_case=True, sort_fields=("alphabet", "case")
        ),
        "",
        "## Adversarial inputs",
        "",
        markdown_table(frame, "adversarial", by_case=True, sort_fields=("case",)),
        "",
        "## Runtime scaling (same-machine control run)",
        "",
        markdown_table(frame, "memory_scaling"),
        "",
        "## Peak traced memory scaling",
        "",
        markdown_table(frame, "memory_scaling", value="peak_kib"),
        "",
        "## Banded versus rolling-row edit distance",
        "",
        markdown_table(
            frame, "banded_distance", by_case=True, sort_fields=("k", "n", "m")
        ),
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/benchmark_raw.csv"))
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args(argv)

    frame = load(args.input)
    figdir = args.outdir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    line_plot(
        frame,
        "text_length",
        "n",
        "median_ms",
        "Runtime versus text length (m = 80, k = 2, DNA)",
        "Median runtime (ms)",
        figdir / "runtime_vs_text_length.png",
    )
    line_plot(
        frame,
        "text_length",
        "n",
        "median_ms",
        "Log-log runtime versus text length",
        "Median runtime (ms, log scale)",
        figdir / "runtime_vs_text_length_loglog.png",
        logx=True,
        logy=True,
    )
    growth_plot(frame, figdir / "growth_vs_theory.png")
    line_plot(
        frame,
        "text_length",
        "n",
        "peak_kib",
        "Peak traced memory versus text length",
        "Peak memory (KiB)",
        figdir / "memory_vs_text_length.png",
        logy=True,
    )
    line_plot(
        frame,
        "memory_scaling",
        "n",
        "peak_kib",
        "Peak traced memory versus input size (m = 80)",
        "Peak memory (KiB)",
        figdir / "memory_scaling.png",
        logy=True,
    )
    line_plot(
        frame,
        "pattern_length",
        "m",
        "median_ms",
        "Runtime versus pattern length (n = 4000, k = 3)",
        "Median runtime (ms)",
        figdir / "runtime_vs_pattern_length.png",
        logy=True,
    )
    line_plot(
        frame,
        "threshold",
        "k",
        "median_ms",
        "Runtime versus error threshold (n = 4000, m = 100)",
        "Median runtime (ms)",
        figdir / "runtime_vs_k.png",
        logy=True,
    )
    bar_plot(frame, "alphabet", "Alphabet and natural-language inputs", figdir / "alphabet.png")
    bar_plot(frame, "adversarial", "Highly repetitive and adversarial inputs", figdir / "adversarial.png")
    line_plot(
        frame,
        "banded_distance",
        "k",
        "median_ms",
        "Banded vs rolling-row edit distance (length 1000)",
        "Median runtime (ms)",
        figdir / "banded_distance.png",
        logy=True,
    )

    write_report(frame, args.outdir / "analysis.md")
    print(f"Figures written to {figdir}")
    print(f"Tables written to {args.outdir / 'analysis.md'}")


if __name__ == "__main__":
    main()
