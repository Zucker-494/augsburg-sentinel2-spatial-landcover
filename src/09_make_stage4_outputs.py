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
SAMPLES = ROOT / "data" / "samples"
OUT = ROOT / "outputs"
BOUNDARY = ROOT / "data" / "raw" / "augsburg_boundary.geojson"

CLASS_INFO = [
    (10, "Tree cover", "#2E7D32"),
    (30, "Grassland", "#A8C96F"),
    (40, "Cropland", "#D8B365"),
    (50, "Built-up", "#C45A52"),
    (80, "Permanent water", "#4C78A8"),
]


def read_reference():
    path = PROCESSED / "worldcover_selected_reference.tif"
    with rasterio.open(path) as src:
        arr = src.read(1)
        extent = plotting_extent(src)
        crs = src.crs
    return arr, extent, crs


def make_reference_map():
    arr, extent, crs = read_reference()
    boundary = gpd.read_file(BOUNDARY).to_crs(crs)

    codes = [x[0] for x in CLASS_INFO]
    colors = [x[2] for x in CLASS_INFO]

    display = np.full(arr.shape, np.nan, dtype="float32")
    for idx, code in enumerate(codes, start=1):
        display[arr == code] = idx

    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(0.5, len(codes) + 1.5), cmap.N)

    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    ax.imshow(
        display,
        extent=extent,
        origin="upper",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
    )
    boundary.boundary.plot(ax=ax, linewidth=0.8)

    handles = [
        plt.Line2D(
            [0], [0],
            marker="s",
            linestyle="",
            markerfacecolor=color,
            markeredgecolor="none",
            markersize=8,
            label=name,
        )
        for _, name, color in CLASS_INFO
    ]
    ax.legend(
        handles=handles,
        title="Reference class",
        loc="lower left",
        frameon=False,
        fontsize=8.5,
        title_fontsize=9,
    )

    ax.set_title(
        "WorldCover reference classes used in Project04",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.text(
        0.0,
        -0.055,
        "ESA WorldCover 2021 v200, aligned to the 10 m Project04 feature grid",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )
    ax.set_axis_off()

    fig.tight_layout()
    fig.savefig(
        OUT / "figure05_worldcover_reference_classes.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_class_balance():
    summary = pd.read_csv(OUT / "stage4_reference_class_summary.csv")
    summary = summary.sort_values(
        "share_of_joint_valid_area_pct", ascending=True
    )

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    bars = ax.barh(
        summary["class_name"],
        summary["share_of_joint_valid_area_pct"],
    )

    ax.set_xlabel("Share of jointly valid Augsburg pixels (%)")
    ax.set_title(
        "Reference-class composition",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linewidth=0.5, alpha=0.25)
    ax.set_axisbelow(True)

    for bar, value in zip(
        bars, summary["share_of_joint_valid_area_pct"]
    ):
        ax.text(
            bar.get_width() + 0.35,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=8.5,
        )

    ax.text(
        0.0,
        -0.17,
        "Class proportions describe the aligned WorldCover reference layer, not independent field observations.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )

    fig.tight_layout()
    fig.savefig(
        OUT / "figure06_reference_class_balance.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_sample_map():
    samples = pd.read_csv(SAMPLES / "reference_samples.csv")
    boundary = gpd.read_file(BOUNDARY).to_crs(32632)

    color_lookup = {name: color for _, name, color in CLASS_INFO}

    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    boundary.boundary.plot(ax=ax, linewidth=0.9)

    rng = np.random.default_rng(42)
    for class_name, sdf in samples.groupby("class_name"):
        if len(sdf) > 350:
            idx = rng.choice(len(sdf), 350, replace=False)
            sdf_plot = sdf.iloc[idx]
        else:
            sdf_plot = sdf

        ax.scatter(
            sdf_plot["x"],
            sdf_plot["y"],
            s=5,
            alpha=0.65,
            label=class_name,
            color=color_lookup[class_name],
            linewidths=0,
        )

    ax.legend(
        title="Reference sample",
        loc="lower left",
        frameon=False,
        fontsize=8.5,
        title_fontsize=9,
    )
    ax.set_title(
        "Spatial distribution of reference samples",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.text(
        0.0,
        -0.055,
        "Display is thinned for readability; the modelling sample table retains all selected pixels.",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )
    ax.set_axis_off()

    fig.tight_layout()
    fig.savefig(
        OUT / "figure07_reference_sample_distribution.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def write_report():
    classes = pd.read_csv(OUT / "stage4_reference_class_summary.csv")
    samples = pd.read_csv(OUT / "stage4_sample_summary.csv")
    qa = pd.read_csv(OUT / "stage4_reference_qa.csv").iloc[0]

    lines = [
        "# Stage 4 Reference Labels and Sampling Report",
        "",
        "## Purpose",
        "",
        "Stage 4 prepares a reproducible reference-label layer for supervised classification.",
        "",
        "ESA WorldCover 2021 v200 is aligned to the same 10 m grid used by the 27-feature Sentinel-2 stack.",
        "",
        "## Selected reference classes",
        "",
        "| Code | Class | Pixels | Area (km²) | Share of jointly valid area |",
        "|---:|---|---:|---:|---:|",
    ]

    for _, row in classes.iterrows():
        lines.append(
            f"| {int(row['class_code'])} | {row['class_name']} | "
            f"{int(row['pixel_count']):,} | {row['area_km2']:.2f} | "
            f"{row['share_of_joint_valid_area_pct']:.2f}% |"
        )

    lines += [
        "",
        f"Together, the selected classes represent **{qa['selected_reference_coverage_pct']:.2f}%** "
        "of pixels that are valid across all 27 Project04 features.",
        "",
        "Pixels belonging to WorldCover classes outside this modelling set are retained in the QA tables but excluded from model sampling.",
        "",
        "## Stratified reference sampling",
        "",
        f"Target sample size: **{int(qa['target_samples_per_class']):,} pixels per class**.",
        "",
        "| Class | Samples | 2 km spatial blocks represented |",
        "|---|---:|---:|",
    ]

    for _, row in samples.iterrows():
        lines.append(
            f"| {row['class_name']} | {int(row['sample_count']):,} | "
            f"{int(row['spatial_blocks'])} |"
        )

    lines += [
        "",
        f"Total reference samples: **{int(qa['sample_rows']):,}**",
        "",
        f"Each sample is assigned to a **{int(qa['spatial_block_size_m']/1000)} km spatial block**. "
        "These block IDs will later be used to construct spatially separated validation rather than mixing neighbouring pixels randomly.",
        "",
        "## Important limitation",
        "",
        "WorldCover is a reproducible reference product, **not independent field ground truth**.",
        "",
        "Project04 therefore measures how the classifiers reproduce this reference labelling scheme under different feature and validation designs. "
        "Agreement with WorldCover must not be interpreted as independent real-world mapping accuracy.",
        "",
        "## Decision gate",
        "",
        "Before model fitting, check:",
        "",
        "- whether the five selected classes cover most of the valid Augsburg study area;",
        "- whether every class has enough reference pixels;",
        "- whether the reference samples are spatially distributed across multiple 2 km blocks;",
        "- whether the reference map contains obvious alignment errors.",
        "",
        "## Next stage",
        "",
        "If Stage 4 passes QA, Stage 5 will extract the 27 Sentinel-2 features at these reference pixels and fit the first supervised classifiers.",
    ]

    (OUT / "STAGE4_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    make_reference_map()
    make_class_balance()
    make_sample_map()
    write_report()
    print("Created Stage 4 reference-label QA figures and report.")


if __name__ == "__main__":
    main()
