from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

DISPLAY_MODEL_ORDER = ["Random Forest", "HistGradientBoosting"]
DISPLAY_FEATURE_ORDER = ["bands_only", "bands_plus_indices"]


def make_model_comparison():
    df = pd.read_csv(OUT / "stage5_random_validation_results.csv")

    x = np.arange(len(DISPLAY_MODEL_ORDER))
    width = 0.34

    fig, ax = plt.subplots(figsize=(7.4, 4.8))

    for offset_i, feature_set in enumerate(DISPLAY_FEATURE_ORDER):
        sdf = (
            df[df["feature_set"] == feature_set]
            .set_index("model")
            .reindex(DISPLAY_MODEL_ORDER)
        )

        offset = (-0.5 if offset_i == 0 else 0.5) * width
        bars = ax.bar(
            x + offset,
            100 * sdf["macro_f1"].to_numpy(),
            width=width,
            label=(
                "Bands only"
                if feature_set == "bands_only"
                else "Bands + indices"
            ),
        )

        for bar, value in zip(bars, 100 * sdf["macro_f1"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(DISPLAY_MODEL_ORDER)
    ax.set_ylabel("Macro F1 (%)")
    ax.set_title(
        "Random-validation model comparison",
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

    ymin = max(0, 100 * df["macro_f1"].min() - 8)
    ax.set_ylim(ymin, 100)

    ax.text(
        0.0,
        -0.18,
        "Stage 5 uses a stratified random pixel split; spatial block validation is evaluated separately in Stage 6.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure08_random_validation_model_comparison.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_best_feature_importance():
    results = pd.read_csv(OUT / "stage5_random_validation_results.csv")
    best = results.sort_values(
        ["macro_f1", "accuracy"],
        ascending=False,
    ).iloc[0]

    safe_name = (
        best["model"].lower().replace(" ", "_")
        + "__"
        + best["feature_set"]
    )
    imp = pd.read_csv(OUT / f"stage5_importance_{safe_name}.csv").head(12)
    imp = imp.sort_values("importance_mean", ascending=True)

    fig, ax = plt.subplots(figsize=(7.4, 5.8))
    ax.barh(
        imp["feature"],
        imp["importance_mean"],
        xerr=imp["importance_sd"],
        capsize=2,
    )

    ax.set_xlabel("Permutation importance (Δ macro F1)")
    ax.set_title(
        f"Most informative features — {best['model']}",
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
        -0.12,
        f"Feature set: {best['feature_set']}; importance estimated by permutation on a fixed test subset.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure09_best_model_feature_importance.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def write_report():
    df = pd.read_csv(OUT / "stage5_random_validation_results.csv")
    best = df.sort_values(
        ["macro_f1", "accuracy"],
        ascending=False,
    ).iloc[0]

    lines = [
        "# Stage 5 Machine-Learning Baseline Report",
        "",
        "## Purpose",
        "",
        "Stage 5 establishes the conventional random-validation baseline before spatial validation is introduced.",
        "",
        "Two feature designs are compared:",
        "",
        "- **Bands only:** 18 multi-season Sentinel-2 spectral-band features;",
        "- **Bands + indices:** all 27 features, including seasonal NDVI, NDBI and NDWI.",
        "",
        "Two classifiers are compared:",
        "",
        "- Random Forest;",
        "- HistGradientBoosting.",
        "",
        "All four comparisons use the same stratified 70/30 random train/test split.",
        "",
        "## Random-validation results",
        "",
        "| Model | Feature set | Features | Accuracy | Macro F1 | Fit time (s) |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for _, row in df.iterrows():
        lines.append(
            f"| {row['model']} | {row['feature_set']} | "
            f"{int(row['feature_count'])} | "
            f"{row['accuracy']:.3f} | "
            f"{row['macro_f1']:.3f} | "
            f"{row['fit_seconds']:.1f} |"
        )

    lines += [
        "",
        "## Best random-validation configuration",
        "",
        f"- Model: **{best['model']}**",
        f"- Feature set: **{best['feature_set']}**",
        f"- Accuracy: **{best['accuracy']:.3f}**",
        f"- Macro F1: **{best['macro_f1']:.3f}**",
        "",
        "## Interpretation",
        "",
        "These scores are deliberately treated as a baseline rather than final performance estimates.",
        "",
        "Neighbouring Sentinel-2 pixels are spatially autocorrelated. A random pixel split can therefore place highly similar nearby observations in both training and testing data.",
        "",
        "Stage 6 will repeat the comparison using spatially separated 2 km blocks. The difference between random and spatial validation is a central Project04 result.",
        "",
        "## Feature importance",
        "",
        "Permutation importance is reported for the best random-validation configuration. It measures the reduction in macro F1 when a feature is shuffled while all other features remain unchanged.",
        "",
        "Importance should be interpreted as predictive usefulness within the fitted model, not as a causal effect.",
        "",
        "## Next stage",
        "",
        "Stage 6 will replace the random pixel split with block-based spatial validation and quantify the validation gap.",
    ]

    (OUT / "STAGE5_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    make_model_comparison()
    make_best_feature_importance()
    write_report()
    print("Created Stage 5 comparison figures and report.")


if __name__ == "__main__":
    main()
