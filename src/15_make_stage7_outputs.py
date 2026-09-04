from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import pandas as pd
import rasterio
from rasterio.plot import plotting_extent

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
BOUNDARY = ROOT / "data" / "raw" / "augsburg_boundary.geojson"

CLASS_INFO = [
    (10, "Tree cover", "#2E7D32"),
    (30, "Grassland", "#A8C96F"),
    (40, "Cropland", "#D8B365"),
    (50, "Built-up", "#C45A52"),
    (80, "Permanent water", "#4C78A8"),
]


def make_confusion_matrix():
    cm = pd.read_csv(
        OUT / "stage7_spatial_confusion_row_normalized.csv",
        index_col=0,
    )

    fig, ax = plt.subplots(figsize=(7.0, 6.2))
    im = ax.imshow(cm.to_numpy() * 100, vmin=0, vmax=100)

    ax.set_xticks(np.arange(len(cm.columns)))
    ax.set_xticklabels(cm.columns, rotation=35, ha="right")
    ax.set_yticks(np.arange(len(cm.index)))
    ax.set_yticklabels(cm.index)

    ax.set_xlabel("Predicted class")
    ax.set_ylabel("Reference class")
    ax.set_title(
        "Spatial-validation confusion matrix",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            value = 100 * cm.iloc[i, j]
            text_color = "white" if value >= 55 else "black"
            ax.text(
                j, i, f"{value:.1f}",
                ha="center", va="center",
                fontsize=8.5,
                color=text_color,
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Row-normalized share (%)")

    fig.tight_layout()
    fig.savefig(
        OUT / "figure13_spatial_confusion_matrix.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_error_map():
    df = pd.read_csv(OUT / "stage7_spatial_oof_predictions.csv")
    boundary = gpd.read_file(BOUNDARY).to_crs(32632)

    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    boundary.boundary.plot(ax=ax, linewidth=0.8)

    correct = df[df["correct"] == True]
    error = df[df["correct"] == False]

    rng = np.random.default_rng(42)

    if len(correct) > 1800:
        correct = correct.iloc[
            rng.choice(len(correct), 1800, replace=False)
        ]
    if len(error) > 1800:
        error = error.iloc[
            rng.choice(len(error), 1800, replace=False)
        ]

    ax.scatter(
        correct["x"], correct["y"],
        s=4, alpha=0.25,
        label="Correct OOF prediction",
        linewidths=0,
    )
    ax.scatter(
        error["x"], error["y"],
        s=9, alpha=0.75,
        label="Spatial OOF error",
        linewidths=0,
    )

    ax.legend(
        frameon=False,
        loc="lower left",
        fontsize=8.5,
    )
    ax.set_title(
        "Spatial distribution of validation errors",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.text(
        0.0,
        -0.055,
        "Out-of-fold predictions from 5-fold spatial validation; display thinned for readability.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )
    ax.set_axis_off()

    fig.tight_layout()
    fig.savefig(
        OUT / "figure14_spatial_validation_errors.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_spatial_importance():
    imp = pd.read_csv(
        OUT / "stage7_spatial_permutation_importance_summary.csv"
    ).head(12)
    imp = imp.sort_values("mean_importance", ascending=True)

    fig, ax = plt.subplots(figsize=(7.4, 5.8))
    ax.barh(
        imp["feature"],
        imp["mean_importance"],
        xerr=imp["sd_between_folds"].fillna(0),
        capsize=2,
    )

    ax.set_xlabel("Mean permutation importance (Δ macro F1)")
    ax.set_title(
        "Feature importance under spatial validation",
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
        "Mean across five spatial folds; error bars show between-fold SD.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure15_spatial_feature_importance.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_confidence_map():
    path = PROCESSED / "final_hgb_confidence.tif"
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        arr[arr == src.nodata] = np.nan
        extent = plotting_extent(src)
        crs = src.crs

    boundary = gpd.read_file(BOUNDARY).to_crs(crs)

    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    im = ax.imshow(
        arr,
        extent=extent,
        origin="upper",
        vmin=0.5,
        vmax=1.0,
        interpolation="nearest",
    )
    boundary.boundary.plot(ax=ax, linewidth=0.8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Maximum class probability")

    ax.set_title(
        "Model confidence across Augsburg",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.text(
        0.0,
        -0.055,
        "Maximum HistGradientBoosting class probability; not a calibrated probability of correctness.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )
    ax.set_axis_off()

    fig.tight_layout()
    fig.savefig(
        OUT / "figure16_model_confidence.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def write_report():
    conf = pd.read_csv(OUT / "stage7_class_confidence_summary.csv")
    imp = pd.read_csv(
        OUT / "stage7_spatial_permutation_importance_summary.csv"
    ).head(10)

    lines = [
        "# Stage 7 Interpretation and Uncertainty Report",
        "",
        "## Selected configuration",
        "",
        "- Model: **HistGradientBoosting**",
        "- Feature set: **bands + indices (27 features)**",
        "- Selection basis: best mean macro F1 under 5-fold spatial validation",
        "",
        "## Why Stage 7 uses out-of-fold predictions",
        "",
        "Class-specific errors and confidence summaries are calculated from spatial out-of-fold predictions. "
        "Each reference sample is therefore predicted by a model that was not trained on its own 2 km spatial block.",
        "",
        "## Class-level confidence and accuracy",
        "",
        "| Class | Spatial OOF accuracy | Median confidence | P10 confidence | Confidence < 0.60 |",
        "|---|---:|---:|---:|---:|",
    ]

    for _, row in conf.iterrows():
        lines.append(
            f"| {row['class_name']} | "
            f"{row['accuracy']:.3f} | "
            f"{row['median_confidence']:.3f} | "
            f"{row['p10_confidence']:.3f} | "
            f"{row['low_confidence_below_0_60_pct']:.1f}% |"
        )

    lines += [
        "",
        "## Most useful features under spatial validation",
        "",
        "| Feature | Mean permutation importance | Between-fold SD |",
        "|---|---:|---:|",
    ]

    for _, row in imp.iterrows():
        lines.append(
            f"| {row['feature']} | "
            f"{row['mean_importance']:.4f} | "
            f"{row['sd_between_folds']:.4f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "The class-level results should be read together with the spatial confusion matrix and error map.",
        "",
        "Classes with lower F1 or confidence are more spectrally ambiguous under this reference scheme. "
        "In particular, grassland can overlap spectrally with cropland and other vegetated surfaces, especially when seasonal states are similar.",
        "",
        "The feature-importance ranking is calculated within spatial validation rather than only from a random split. "
        "This makes it more relevant to the model's spatial generalisation behaviour.",
        "",
        "## Confidence map",
        "",
        "The full Augsburg confidence raster is produced by a final HistGradientBoosting model fitted to all 30,000 reference samples after the model-selection stage.",
        "",
        "The displayed value is the maximum predicted class probability. "
        "HistGradientBoosting probabilities are not calibrated here, so the map should be interpreted as **relative model confidence**, not a literal probability that a pixel is correct.",
        "",
        "## Important limitation",
        "",
        "All performance and uncertainty interpretation remains conditional on ESA WorldCover as the reference-label source. "
        "The project does not claim independent field-validated land-cover accuracy.",
        "",
        "## Next stage",
        "",
        "Stage 8 will assemble the final classification map, confidence map, core validation figures, documentation and interactive presentation into the finished Project04 portfolio.",
    ]

    (OUT / "STAGE7_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    make_confusion_matrix()
    make_error_map()
    make_spatial_importance()
    make_confidence_map()
    write_report()
    print("Created Stage 7 interpretation figures and report.")


if __name__ == "__main__":
    main()
