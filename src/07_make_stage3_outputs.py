from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.plot import plotting_extent

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
BOUNDARY = ROOT / "data" / "raw" / "augsburg_boundary.geojson"

REPRESENTATIVE_SEASON = "summer"


def read_float(path: Path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        extent = plotting_extent(src)
        crs = src.crs
    return arr, extent, crs


def make_index_map(index_name: str, title: str, subtitle: str, cmap: str, vmin: float, vmax: float):
    arr, extent, crs = read_float(
        PROCESSED / f"{REPRESENTATIVE_SEASON}_{index_name}.tif"
    )
    boundary = gpd.read_file(BOUNDARY).to_crs(crs)

    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    im = ax.imshow(
        arr,
        extent=extent,
        origin="upper",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )
    boundary.boundary.plot(ax=ax, linewidth=0.8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label(index_name.upper())

    ax.set_title(
        title,
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.text(
        0.0,
        -0.055,
        subtitle,
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )
    ax.set_axis_off()

    fig.tight_layout()
    fig.savefig(
        OUT / f"figure04_{REPRESENTATIVE_SEASON}_{index_name}.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def write_report():
    summary = pd.read_csv(OUT / "stage3_feature_summary.csv")
    qa = pd.read_csv(OUT / "stage3_stack_qa.csv").iloc[0]

    lines = [
        "# Stage 3 Feature Engineering Report",
        "",
        "## Purpose",
        "",
        "Stage 3 converts the seasonal Sentinel-2 composites into machine-learning features.",
        "",
        "The final feature stack contains **27 raster features**:",
        "",
        "- 6 spectral bands × 3 seasons = 18 band features;",
        "- NDVI, NDBI and NDWI × 3 seasons = 9 engineered features.",
        "",
        "## Spectral-index definitions",
        "",
        "- **NDVI** = (NIR − Red) / (NIR + Red)",
        "- **NDBI** = (SWIR1 − NIR) / (SWIR1 + NIR)",
        "- **NDWI** = (Green − NIR) / (Green + NIR)",
        "",
        "NDWI refers here to the Green–NIR form commonly associated with surface-water enhancement.",
        "",
        "## Stack QA",
        "",
        f"- Feature count: **{int(qa['feature_count'])}**",
        f"- Pixels valid across all features: **{int(qa['jointly_valid_pixels']):,}**",
        f"- Pixels used for correlation QA: **{int(qa['correlation_sample_pixels']):,}**",
        "",
        "## Index summary by season",
        "",
        "| Feature | P02 | Median | P98 |",
        "|---|---:|---:|---:|",
    ]

    idx = summary[summary["feature"].str.endswith(("ndvi", "ndbi", "ndwi"))]
    for _, row in idx.iterrows():
        lines.append(
            f"| {row['feature']} | "
            f"{row['p02']:.3f} | "
            f"{row['median']:.3f} | "
            f"{row['p98']:.3f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "The spectral-index rasters are derived from the quality-masked seasonal median composites, so they inherit the spatial alignment and cloud-screening decisions from Stage 2.",
        "",
        "The correlation table is a QA diagnostic rather than a feature-selection decision. Strong correlation between some bands and indices is expected because the indices are algebraically derived from the same spectral inputs.",
        "",
        "## Next stage",
        "",
        "Stage 4 will clip and remap the WorldCover 2021 reference layer, inspect class balance, and construct reproducible training and validation samples.",
    ]

    (OUT / "STAGE3_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    make_index_map(
        "ndvi",
        "Summer vegetation signal",
        "NDVI derived from the quality-masked summer Sentinel-2 median composite",
        "YlGn",
        -0.2,
        0.9,
    )
    make_index_map(
        "ndbi",
        "Summer built-up spectral contrast",
        "NDBI derived from SWIR1 and NIR; positive values can also occur on bare surfaces",
        "PuOr",
        -0.6,
        0.6,
    )
    make_index_map(
        "ndwi",
        "Summer surface-water spectral contrast",
        "Green–NIR NDWI; intended as a water-related feature rather than a standalone classifier",
        "Blues",
        -0.6,
        0.6,
    )
    write_report()
    print("Created Stage 3 index quicklooks and report.")


if __name__ == "__main__":
    main()
