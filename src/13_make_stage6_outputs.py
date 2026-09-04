from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

MODEL_ORDER = ["Random Forest", "HistGradientBoosting"]
FEATURE_ORDER = ["bands_only", "bands_plus_indices"]


def config_label(model, feature_set):
    suffix = "Bands" if feature_set == "bands_only" else "Bands + indices"
    short_model = "RF" if model == "Random Forest" else "HGB"
    return f"{short_model}\n{suffix}"


def make_validation_comparison():
    df = pd.read_csv(OUT / "stage6_validation_summary.csv")

    configs = [
        (model, fs)
        for model in MODEL_ORDER
        for fs in FEATURE_ORDER
    ]
    x = np.arange(len(configs))
    width = 0.34

    fig, ax = plt.subplots(figsize=(8.2, 5.2))

    for i, validation in enumerate(["random_5fold", "spatial_5fold"]):
        sdf = df[df["validation"] == validation].set_index(
            ["model", "feature_set"]
        )

        means = np.array([
            100 * sdf.loc[c, "mean_macro_f1"] for c in configs
        ])
        sds = np.array([
            100 * sdf.loc[c, "sd_macro_f1"] for c in configs
        ])

        offset = (-0.5 if i == 0 else 0.5) * width
        bars = ax.bar(
            x + offset,
            means,
            width=width,
            yerr=sds,
            capsize=3,
            label=(
                "Random 5-fold"
                if validation == "random_5fold"
                else "Spatial 5-fold"
            ),
        )

        for bar, value in zip(bars, means):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.7,
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_xticks(x)
    ax.set_xticklabels([config_label(*c) for c in configs])
    ax.set_ylabel("Macro F1 (%)")
    ax.set_title(
        "Random versus spatial validation",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.legend(frameon=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linewidth=0.5, alpha=0.25)
    ax.set_axisbelow(True)

    ymin = max(
        0,
        100 * df["mean_macro_f1"].min()
        - 2 * 100 * df["sd_macro_f1"].max()
        - 6,
    )
    ax.set_ylim(ymin, 100)

    ax.text(
        0.0,
        -0.20,
        "Bars show mean macro F1 across five folds; error bars show ±1 SD. Spatial folds keep complete 2 km blocks together.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure10_random_vs_spatial_validation.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_validation_gap():
    gap = pd.read_csv(OUT / "stage6_validation_gap.csv")
    gap["label"] = [
        config_label(m, f).replace("\n", " — ")
        for m, f in zip(gap["model"], gap["feature_set"])
    ]
    gap = gap.sort_values("macro_f1_gap", ascending=True)

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    values = 100 * gap["macro_f1_gap"]

    bars = ax.barh(gap["label"], values)

    ax.axvline(0, linewidth=0.8)
    ax.set_xlabel("Random − spatial macro F1 (percentage points)")
    ax.set_title(
        "Validation optimism gap",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linewidth=0.5, alpha=0.25)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, values):
        ha = "left" if value >= 0 else "right"
        offset = 0.12 if value >= 0 else -0.12
        ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f} pp",
            va="center",
            ha=ha,
            fontsize=8.5,
        )

    ax.text(
        0.0,
        -0.16,
        "Positive values indicate that random pixel validation reports higher performance than spatially separated validation.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure11_validation_optimism_gap.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_best_spatial_class_f1():
    summary = pd.read_csv(OUT / "stage6_validation_summary.csv")
    spatial = summary[summary["validation"] == "spatial_5fold"].sort_values(
        ["mean_macro_f1", "mean_accuracy"],
        ascending=False,
    )
    best = spatial.iloc[0]

    classes = pd.read_csv(OUT / "stage6_class_fold_results.csv")
    sdf = classes[
        (classes["validation"] == "spatial_5fold")
        & (classes["model"] == best["model"])
        & (classes["feature_set"] == best["feature_set"])
    ]

    agg = (
        sdf.groupby("class_name", as_index=False)
        .agg(mean_f1=("f1", "mean"), sd_f1=("f1", "std"))
        .sort_values("mean_f1", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.barh(
        agg["class_name"],
        100 * agg["mean_f1"],
        xerr=100 * agg["sd_f1"],
        capsize=3,
    )
    ax.set_xlabel("Spatial-validation F1 (%)")
    ax.set_title(
        "Class-level spatial generalisation",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linewidth=0.5, alpha=0.25)
    ax.set_axisbelow(True)

    ax.text(
        0.0,
        -0.16,
        f"Best spatial configuration: {best['model']} / {best['feature_set']}; bars show five-fold mean ±1 SD.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure12_best_spatial_class_f1.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def write_report():
    summary = pd.read_csv(OUT / "stage6_validation_summary.csv")
    gap = pd.read_csv(OUT / "stage6_validation_gap.csv")
    fold_qa = pd.read_csv(OUT / "stage6_spatial_fold_qa.csv")

    spatial = summary[summary["validation"] == "spatial_5fold"].sort_values(
        ["mean_macro_f1", "mean_accuracy"],
        ascending=False,
    )
    best = spatial.iloc[0]

    max_overlap = int(fold_qa["block_overlap"].max())

    lines = [
        "# Stage 6 Spatial Validation Report",
        "",
        "## Purpose",
        "",
        "Stage 6 tests whether conventional random pixel validation overstates model performance when spatial dependence is present.",
        "",
        "Two matched five-fold validation designs are compared:",
        "",
        "- **Random 5-fold:** stratified pixel-level folds;",
        "- **Spatial 5-fold:** stratified group folds that keep complete 2 km spatial blocks together.",
        "",
        "## Spatial-fold QA",
        "",
        f"- Number of folds: **{len(fold_qa)}**",
        f"- Maximum train/test block overlap: **{max_overlap}**",
        "",
        "A block overlap of zero confirms that the spatial folds do not place samples from the same 2 km block in both training and testing subsets.",
        "",
        "## Validation results",
        "",
        "| Model | Feature set | Random macro F1 | Spatial macro F1 | Gap |",
        "|---|---|---:|---:|---:|",
    ]

    merged = gap.sort_values("spatial_mean_macro_f1", ascending=False)
    for _, row in merged.iterrows():
        lines.append(
            f"| {row['model']} | {row['feature_set']} | "
            f"{row['random_mean_macro_f1']:.3f} ± {row['random_sd_macro_f1']:.3f} | "
            f"{row['spatial_mean_macro_f1']:.3f} ± {row['spatial_sd_macro_f1']:.3f} | "
            f"{100*row['macro_f1_gap']:.2f} pp |"
        )

    lines += [
        "",
        "## Best spatial-validation configuration",
        "",
        f"- Model: **{best['model']}**",
        f"- Feature set: **{best['feature_set']}**",
        f"- Mean spatial macro F1: **{best['mean_macro_f1']:.3f}**",
        f"- Fold SD: **{best['sd_macro_f1']:.3f}**",
        "",
        "## Interpretation",
        "",
        "The random-versus-spatial gap is the main Stage 6 result.",
        "",
        "A positive gap indicates that random pixel validation is more optimistic than spatially separated validation. "
        "This is consistent with the idea that nearby image pixels share spectral and land-cover characteristics.",
        "",
        "The spatial result should still not be interpreted as independent real-world accuracy because the target labels come from WorldCover rather than field ground truth.",
        "",
        "## Why five folds?",
        "",
        "Using five folds reduces dependence on one arbitrary train/test partition and allows variability across folds to be reported.",
        "",
        "## Next stage",
        "",
        "Stage 7 will focus on interpretation: class-specific errors, confidence/uncertainty, feature importance under the selected spatially validated configuration, and the spatial distribution of model mistakes.",
    ]

    (OUT / "STAGE6_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    make_validation_comparison()
    make_validation_gap()
    make_best_spatial_class_f1()
    write_report()
    print("Created Stage 6 spatial-validation figures and report.")


if __name__ == "__main__":
    main()
