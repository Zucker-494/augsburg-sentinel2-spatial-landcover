from __future__ import annotations

from pathlib import Path
import json
import math
import os

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

BOUNDARY_PATH = ROOT / "data" / "raw" / "augsburg_boundary.geojson"
SELECTED_PATH = ROOT / "outputs" / "selected_scenes.csv"
ITEMS_PATH = ROOT / "data" / "metadata" / "sentinel_search_items.json"

PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
PROCESSED.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

TARGET_CRS = f"EPSG:{CONFIG['aoi']['utm_epsg']}"
TARGET_RES = 10.0
BANDS = ["blue", "green", "red", "nir", "swir16", "swir22"]

# Sentinel-2 Scene Classification Layer:
# 0 no data, 1 saturated/defective, 3 cloud shadow,
# 8 medium cloud probability, 9 high cloud probability,
# 10 cirrus, 11 snow/ice are excluded.
INVALID_SCL = {0, 1, 3, 8, 9, 10, 11}


def to_https(href: str) -> str:
    """Convert common public S3 Sentinel COG hrefs to unsigned HTTPS."""
    if href.startswith("s3://sentinel-cogs/"):
        return href.replace(
            "s3://sentinel-cogs/",
            "https://sentinel-cogs.s3.us-west-2.amazonaws.com/",
            1,
        )
    return href


def load_item_lookup() -> dict[str, dict]:
    raw = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    lookup = {}
    for items in raw.values():
        for item in items:
            lookup[item["id"]] = item
    return lookup


def build_target_grid():
    boundary = gpd.read_file(BOUNDARY_PATH).to_crs(TARGET_CRS)
    geom = boundary.geometry.union_all()
    minx, miny, maxx, maxy = geom.bounds

    left = math.floor(minx / TARGET_RES) * TARGET_RES
    bottom = math.floor(miny / TARGET_RES) * TARGET_RES
    right = math.ceil(maxx / TARGET_RES) * TARGET_RES
    top = math.ceil(maxy / TARGET_RES) * TARGET_RES

    width = int(round((right - left) / TARGET_RES))
    height = int(round((top - bottom) / TARGET_RES))
    transform = from_origin(left, top, TARGET_RES, TARGET_RES)

    inside = geometry_mask(
        [geom.__geo_interface__],
        out_shape=(height, width),
        transform=transform,
        invert=True,
    )
    return boundary, geom, transform, width, height, inside


def read_asset(
    href: str,
    transform,
    width: int,
    height: int,
    resampling: Resampling,
) -> np.ndarray:
    href = to_https(href)
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
    ):
        with rasterio.open(href) as src:
            with WarpedVRT(
                src,
                crs=TARGET_CRS,
                transform=transform,
                width=width,
                height=height,
                resampling=resampling,
            ) as vrt:
                arr = vrt.read(1)
    return arr


def write_float_tif(path, arr, transform):
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": TARGET_CRS,
        "transform": transform,
        "nodata": -9999.0,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(out, 1)


def write_uint8_tif(path, arr, transform):
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": TARGET_CRS,
        "transform": transform,
        "nodata": 0,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr.astype("uint8"), 1)


def main():
    if not BOUNDARY_PATH.exists():
        raise FileNotFoundError("Missing Augsburg boundary. Run Stage 1 first.")
    if not SELECTED_PATH.exists() or not ITEMS_PATH.exists():
        raise FileNotFoundError("Missing Stage 1 scene-selection outputs.")

    selected = pd.read_csv(SELECTED_PATH)
    lookup = load_item_lookup()
    _, _, transform, width, height, inside = build_target_grid()

    print(f"Target grid: {width} x {height} pixels at 10 m")

    summary_rows = []

    for season in CONFIG["sentinel"]["seasons"]:
        sdf = selected[selected["season"] == season].copy()
        if sdf.empty:
            raise RuntimeError(f"No selected scenes found for {season}.")

        band_stacks = {band: [] for band in BANDS}
        valid_masks = []

        print(f"\n=== {season.upper()} ({len(sdf)} scenes) ===")

        for _, row in sdf.iterrows():
            item_id = row["item_id"]
            item = lookup.get(item_id)
            if item is None:
                raise KeyError(f"STAC item metadata not found: {item_id}")

            assets = item["assets"]
            missing = [a for a in BANDS + ["scl"] if a not in assets]
            if missing:
                raise KeyError(f"{item_id} is missing assets: {missing}")

            print(
                f"{item_id}: cloud={row['cloud_cover_pct']:.1f}%, "
                f"coverage={row['aoi_coverage_ratio']*100:.1f}%"
            )

            scl = read_asset(
                assets["scl"]["href"],
                transform,
                width,
                height,
                Resampling.nearest,
            )
            valid = inside & ~np.isin(scl, list(INVALID_SCL))
            valid_masks.append(valid)

            for band in BANDS:
                arr = read_asset(
                    assets[band]["href"],
                    transform,
                    width,
                    height,
                    Resampling.bilinear,
                ).astype("float32")

                # Sentinel-2 L2A reflectance is commonly stored as scaled integers.
                # Convert to reflectance-like values where needed.
                finite_positive = arr[np.isfinite(arr) & (arr > 0)]
                if finite_positive.size and np.nanmedian(finite_positive) > 2:
                    arr = arr / 10000.0

                arr[~valid] = np.nan
                arr[~inside] = np.nan
                band_stacks[band].append(arr)

        valid_count = np.sum(np.stack(valid_masks, axis=0), axis=0).astype("uint8")
        valid_count[~inside] = 0

        write_uint8_tif(
            PROCESSED / f"{season}_valid_observation_count.tif",
            valid_count,
            transform,
        )

        for band, arrays in band_stacks.items():
            stack = np.stack(arrays, axis=0)
            with np.errstate(all="ignore"):
                composite = np.nanmedian(stack, axis=0).astype("float32")
            composite[~inside] = np.nan
            write_float_tif(
                PROCESSED / f"{season}_{band}_median.tif",
                composite,
                transform,
            )

        inside_counts = valid_count[inside]
        summary_rows.append({
            "season": season,
            "selected_scenes": int(len(sdf)),
            "aoi_pixels": int(inside.sum()),
            "pixels_with_at_least_1_valid_obs_pct": float(
                100 * np.mean(inside_counts >= 1)
            ),
            "pixels_with_at_least_3_valid_obs_pct": float(
                100 * np.mean(inside_counts >= 3)
            ),
            "median_valid_observations": float(np.median(inside_counts)),
            "p10_valid_observations": float(np.percentile(inside_counts, 10)),
            "min_valid_observations": int(np.min(inside_counts)),
            "max_valid_observations": int(np.max(inside_counts)),
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "stage2_composite_summary.csv", index=False)
    print("\nSaved seasonal 10 m composites and QA summary.")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
