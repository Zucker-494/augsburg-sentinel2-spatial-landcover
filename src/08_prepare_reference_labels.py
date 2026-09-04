from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

PROCESSED = ROOT / "data" / "processed"
SAMPLES = ROOT / "data" / "samples"
OUT = ROOT / "outputs"

PROCESSED.mkdir(parents=True, exist_ok=True)
SAMPLES.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

STACK_PATH = PROCESSED / "multiseason_feature_stack.tif"
WORLD_COVER_URL = CONFIG["worldcover"]["source_url"]

SELECTED_CLASSES = {
    10: "Tree cover",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    80: "Permanent water",
}

TARGET_SAMPLES_PER_CLASS = 6000
SPATIAL_BLOCK_SIZE_M = 2000
RANDOM_SEED = 42


def read_worldcover_to_stack_grid():
    if not STACK_PATH.exists():
        raise FileNotFoundError("Missing Stage 3 feature stack.")

    with rasterio.open(STACK_PATH) as stack:
        target_crs = stack.crs
        target_transform = stack.transform
        width = stack.width
        height = stack.height
        masks = stack.read_masks()
        jointly_valid = np.all(masks > 0, axis=0)

    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff",
    ):
        with rasterio.open(WORLD_COVER_URL) as src:
            with WarpedVRT(
                src,
                crs=target_crs,
                transform=target_transform,
                width=width,
                height=height,
                resampling=Resampling.nearest,
            ) as vrt:
                wc = vrt.read(1).astype("uint8")

    return wc, jointly_valid, target_crs, target_transform


def write_reference_raster(path, arr, crs, transform):
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": crs,
        "transform": transform,
        "nodata": 0,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr.astype("uint8"), 1)


def sample_class_pixels(reference, valid_mask, transform):
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    left = transform.c
    top = transform.f

    for class_code, class_name in SELECTED_CLASSES.items():
        rows, cols = np.where(valid_mask & (reference == class_code))
        n_available = len(rows)

        if n_available == 0:
            print(f"WARNING: no eligible pixels for class {class_code} {class_name}")
            continue

        n_take = min(TARGET_SAMPLES_PER_CLASS, n_available)
        chosen = rng.choice(n_available, size=n_take, replace=False)

        sample_rows = rows[chosen]
        sample_cols = cols[chosen]

        xs = (
            transform.c
            + (sample_cols + 0.5) * transform.a
            + (sample_rows + 0.5) * transform.b
        )
        ys = (
            transform.f
            + (sample_cols + 0.5) * transform.d
            + (sample_rows + 0.5) * transform.e
        )

        block_x = np.floor((xs - left) / SPATIAL_BLOCK_SIZE_M).astype(int)
        block_y = np.floor((top - ys) / SPATIAL_BLOCK_SIZE_M).astype(int)
        block_ids = [
            f"B{by:02d}_{bx:02d}" for by, bx in zip(block_y, block_x)
        ]

        for r, c, x, y, block_id in zip(
            sample_rows, sample_cols, xs, ys, block_ids
        ):
            records.append(
                {
                    "class_code": class_code,
                    "class_name": class_name,
                    "row": int(r),
                    "col": int(c),
                    "x": float(x),
                    "y": float(y),
                    "block_id": block_id,
                }
            )

    return pd.DataFrame(records)


def main():
    wc, jointly_valid, crs, transform = read_worldcover_to_stack_grid()

    selected_reference = np.zeros(wc.shape, dtype="uint8")
    for class_code in SELECTED_CLASSES:
        selected_reference[
            jointly_valid & (wc == class_code)
        ] = class_code

    write_reference_raster(
        PROCESSED / "worldcover_selected_reference.tif",
        selected_reference,
        crs,
        transform,
    )

    valid_wc = wc[jointly_valid]
    total_valid = int(valid_wc.size)

    class_rows = []
    all_codes, all_counts = np.unique(valid_wc, return_counts=True)
    count_lookup = dict(zip(all_codes.astype(int), all_counts.astype(int)))

    for class_code, class_name in SELECTED_CLASSES.items():
        count = int(count_lookup.get(class_code, 0))
        class_rows.append(
            {
                "class_code": class_code,
                "class_name": class_name,
                "pixel_count": count,
                "area_km2": count * 100.0 / 1_000_000.0,
                "share_of_joint_valid_area_pct": (
                    100.0 * count / total_valid if total_valid else np.nan
                ),
            }
        )

    selected_count = sum(r["pixel_count"] for r in class_rows)
    selected_share = 100.0 * selected_count / total_valid

    class_summary = pd.DataFrame(class_rows)
    class_summary.to_csv(OUT / "stage4_reference_class_summary.csv", index=False)

    samples = sample_class_pixels(wc, jointly_valid, transform)
    samples.to_csv(SAMPLES / "reference_samples.csv", index=False)

    sample_summary = (
        samples.groupby(["class_code", "class_name"])
        .agg(
            sample_count=("class_code", "size"),
            spatial_blocks=("block_id", "nunique"),
        )
        .reset_index()
    )
    sample_summary.to_csv(OUT / "stage4_sample_summary.csv", index=False)

    qa = pd.DataFrame(
        [
            {
                "joint_valid_pixels": total_valid,
                "selected_reference_pixels": selected_count,
                "selected_reference_coverage_pct": selected_share,
                "sample_rows": len(samples),
                "target_samples_per_class": TARGET_SAMPLES_PER_CLASS,
                "spatial_block_size_m": SPATIAL_BLOCK_SIZE_M,
                "random_seed": RANDOM_SEED,
            }
        ]
    )
    qa.to_csv(OUT / "stage4_reference_qa.csv", index=False)

    # Record all WorldCover codes present, including classes not used for modelling.
    all_class_table = pd.DataFrame(
        {
            "worldcover_code": [int(c) for c in all_codes],
            "pixel_count": [int(c) for c in all_counts],
        }
    )
    all_class_table["share_pct"] = (
        100.0 * all_class_table["pixel_count"] / total_valid
    )
    all_class_table.to_csv(
        OUT / "stage4_all_worldcover_codes.csv", index=False
    )

    print(class_summary.to_string(index=False))
    print()
    print(sample_summary.to_string(index=False))
    print()
    print(f"Selected-class reference coverage: {selected_share:.2f}%")
    print(f"Reference samples created: {len(samples):,}")


if __name__ == "__main__":
    main()
