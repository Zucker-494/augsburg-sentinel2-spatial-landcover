from __future__ import annotations

from pathlib import Path
import json

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
OUT.mkdir(parents=True, exist_ok=True)

SEASONS = ["spring", "summer", "autumn"]


def read_float(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        extent = plotting_extent(src)
        crs = src.crs
    return arr, extent, crs


def robust_rgb(red, green, blue):
    rgb = np.dstack([red, green, blue]).astype("float32")
    finite = rgb[np.isfinite(rgb)]
    if finite.size == 0:
        raise RuntimeError("RGB composite contains no finite data.")

    # Shared robust stretch preserves relative colour balance.
    lo, hi = np.nanpercentile(finite, [2, 98])
    if hi <= lo:
        hi = lo + 1e-6
    rgb = np.clip((rgb - lo) / (hi - lo), 0, 1)
    rgb[~np.isfinite(rgb)] = 1.0
    return rgb


def make_true_colour(season):
    red, extent, crs = read_float(PROCESSED / f"{season}_red_median.tif")
    green, _, _ = read_float(PROCESSED / f"{season}_green_median.tif")
    blue, _, _ = read_float(PROCESSED / f"{season}_blue_median.tif")

    rgb = robust_rgb(red, green, blue)
    boundary = gpd.read_file(BOUNDARY).to_crs(crs)

    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    ax.imshow(rgb, extent=extent, origin="upper")
    boundary.boundary.plot(ax=ax, linewidth=0.9)

    ax.set_title(
        f"{season.capitalize()} Sentinel-2 median composite",
        loc="left",
        fontsize=13,
        fontweight="semibold",
        pad=10,
    )
    ax.text(
        0.0,
        -0.055,
        "True-colour view (B4/B3/B2); SCL-masked selected scenes; 10 m target grid",
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
    )
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(
        OUT / f"figure02_{season}_true_colour.png",
        dpi=240,
        bbox_inches="tight",
    )
    plt.close(fig)


def make_valid_obs_qa():
    # One separate figure per season, keeping plots readable and reusable.
    for season in SEASONS:
        path = PROCESSED / f"{season}_valid_observation_count.tif"
        with rasterio.open(path) as src:
            arr = src.read(1)
            extent = plotting_extent(src)
            crs = src.crs

        boundary = gpd.read_file(BOUNDARY).to_crs(crs)

        masked = np.ma.masked_where(arr == 0, arr)
        fig, ax = plt.subplots(figsize=(7.2, 7.2))
        im = ax.imshow(
            masked,
            extent=extent,
            origin="upper",
            vmin=1,
            vmax=5,
            interpolation="nearest",
        )
        boundary.boundary.plot(ax=ax, linewidth=0.9)

        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cbar.set_label("Valid observations")

        ax.set_title(
            f"{season.capitalize()} valid-observation count",
            loc="left",
            fontsize=13,
            fontweight="semibold",
            pad=10,
        )
        ax.text(
            0.0,
            -0.055,
            "Count after Sentinel-2 Scene Classification Layer masking",
            transform=ax.transAxes,
            fontsize=8.5,
            va="top",
        )
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(
            OUT / f"figure03_{season}_valid_observations.png",
            dpi=240,
            bbox_inches="tight",
        )
        plt.close(fig)


def write_report():
    summary = pd.read_csv(OUT / "stage2_composite_summary.csv")

    lines = [
        "# Stage 2 Raster Preprocessing Report",
        "",
        "## Purpose",
        "",
        "Stage 2 converts the selected Sentinel-2 scenes into spatially aligned seasonal composites.",
        "",
        "The workflow performs:",
        "",
        "- 10 m target-grid construction in EPSG:32632;",
        "- SCL-based cloud, cloud-shadow, snow/ice and invalid-pixel masking;",
        "- bilinear resampling of spectral bands to the common 10 m grid;",
        "- nearest-neighbour resampling of the categorical SCL layer;",
        "- seasonal per-pixel median compositing;",
        "- valid-observation counting for QA.",
        "",
        "## Composite QA",
        "",
        "| Season | Scenes | ≥1 valid obs | ≥3 valid obs | Median valid obs | P10 valid obs |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for _, row in summary.iterrows():
        lines.append(
            f"| {row['season'].capitalize()} | "
            f"{int(row['selected_scenes'])} | "
            f"{row['pixels_with_at_least_1_valid_obs_pct']:.1f}% | "
            f"{row['pixels_with_at_least_3_valid_obs_pct']:.1f}% | "
            f"{row['median_valid_observations']:.1f} | "
            f"{row['p10_valid_observations']:.1f} |"
        )

    lines += [
        "",
        "## QA decision rule",
        "",
        "The next stage should proceed only if the seasonal composites provide broad municipal coverage after pixel-level quality masking.",
        "",
        "Particular attention should be paid to the spring composite because Stage 1 contained one scene close to the 20% scene-level cloud-search threshold.",
        "",
        "## Important interpretation",
        "",
        "Scene-level `eo:cloud_cover` was used only for discovery. Stage 2 uses the Sentinel-2 Scene Classification Layer to remove invalid pixels before compositing.",
        "",
        "The seasonal median therefore represents the median of the remaining valid observations for each pixel, not the median of all raw scene values.",
        "",
        "## Next stage",
        "",
        "If Stage 2 passes QA, Stage 3 will derive NDVI, NDBI and NDWI and prepare the multi-season feature stack for machine learning.",
    ]

    (OUT / "STAGE2_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    for season in SEASONS:
        make_true_colour(season)
    make_valid_obs_qa()
    write_report()
    print("Created Stage 2 quicklooks and QA report.")


if __name__ == "__main__":
    main()
