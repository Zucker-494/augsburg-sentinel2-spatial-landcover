from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
PROCESSED.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

SEASONS = ["spring", "summer", "autumn"]
BASE_BANDS = ["blue", "green", "red", "nir", "swir16", "swir22"]
INDICES = ["ndvi", "ndbi", "ndwi"]

NODATA = -9999.0


def read_raster(path: Path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        profile = src.profile.copy()
    return arr, profile


def safe_normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = a + b
    out = np.full(a.shape, np.nan, dtype="float32")
    valid = np.isfinite(a) & np.isfinite(b) & (np.abs(denom) > 1e-8)
    out[valid] = (a[valid] - b[valid]) / denom[valid]
    out = np.clip(out, -1.0, 1.0)
    return out.astype("float32")


def write_float(path: Path, arr: np.ndarray, profile: dict):
    p = profile.copy()
    p.update(
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    data = np.where(np.isfinite(arr), arr, NODATA).astype("float32")
    with rasterio.open(path, "w", **p) as dst:
        dst.write(data, 1)


def describe_feature(name: str, arr: np.ndarray) -> dict:
    vals = arr[np.isfinite(arr)]
    if vals.size == 0:
        return {
            "feature": name,
            "valid_pixels": 0,
            "min": np.nan,
            "p02": np.nan,
            "p25": np.nan,
            "median": np.nan,
            "p75": np.nan,
            "p98": np.nan,
            "max": np.nan,
        }

    q = np.percentile(vals, [2, 25, 50, 75, 98])
    return {
        "feature": name,
        "valid_pixels": int(vals.size),
        "min": float(np.min(vals)),
        "p02": float(q[0]),
        "p25": float(q[1]),
        "median": float(q[2]),
        "p75": float(q[3]),
        "p98": float(q[4]),
        "max": float(np.max(vals)),
    }


def main():
    feature_arrays = {}
    summary_rows = []
    reference_profile = None

    for season in SEASONS:
        bands = {}
        for band in BASE_BANDS:
            path = PROCESSED / f"{season}_{band}_median.tif"
            if not path.exists():
                raise FileNotFoundError(f"Missing Stage 2 raster: {path}")
            arr, profile = read_raster(path)
            bands[band] = arr
            if reference_profile is None:
                reference_profile = profile

            feature_name = f"{season}_{band}"
            feature_arrays[feature_name] = arr
            summary_rows.append(describe_feature(feature_name, arr))

        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi = safe_normalized_difference(bands["nir"], bands["red"])

        # NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)
        ndbi = safe_normalized_difference(bands["swir16"], bands["nir"])

        # NDWI (McFeeters) = (Green - NIR) / (Green + NIR)
        ndwi = safe_normalized_difference(bands["green"], bands["nir"])

        for index_name, arr in {
            "ndvi": ndvi,
            "ndbi": ndbi,
            "ndwi": ndwi,
        }.items():
            feature_name = f"{season}_{index_name}"
            feature_arrays[feature_name] = arr
            summary_rows.append(describe_feature(feature_name, arr))
            write_float(
                PROCESSED / f"{feature_name}.tif",
                arr,
                reference_profile,
            )

    # Save feature summary.
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "stage3_feature_summary.csv", index=False)

    # Build a 27-band multi-season stack:
    # spring 9, summer 9, autumn 9.
    ordered_features = []
    for season in SEASONS:
        ordered_features.extend(
            [f"{season}_{b}" for b in BASE_BANDS]
            + [f"{season}_{i}" for i in INDICES]
        )

    stack_path = PROCESSED / "multiseason_feature_stack.tif"
    stack_profile = reference_profile.copy()
    stack_profile.update(
        dtype="float32",
        count=len(ordered_features),
        nodata=NODATA,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )

    with rasterio.open(stack_path, "w", **stack_profile) as dst:
        for band_idx, feature_name in enumerate(ordered_features, start=1):
            arr = feature_arrays[feature_name]
            data = np.where(np.isfinite(arr), arr, NODATA).astype("float32")
            dst.write(data, band_idx)
            dst.set_band_description(band_idx, feature_name)

    manifest = pd.DataFrame({
        "stack_band": range(1, len(ordered_features) + 1),
        "feature": ordered_features,
    })
    manifest.to_csv(OUT / "stage3_feature_manifest.csv", index=False)

    # Correlation QA on a deterministic sample of jointly valid pixels.
    matrices = []
    for feature_name in ordered_features:
        matrices.append(feature_arrays[feature_name].ravel())

    X = np.column_stack(matrices)
    valid = np.all(np.isfinite(X), axis=1)
    X_valid = X[valid]

    if X_valid.shape[0] == 0:
        raise RuntimeError("No pixels are valid across all 27 features.")

    max_sample = 100_000
    if X_valid.shape[0] > max_sample:
        rng = np.random.default_rng(42)
        idx = rng.choice(X_valid.shape[0], size=max_sample, replace=False)
        X_sample = X_valid[idx]
    else:
        X_sample = X_valid

    corr = pd.DataFrame(
        X_sample,
        columns=ordered_features,
    ).corr(method="pearson")

    corr.to_csv(OUT / "stage3_feature_correlation.csv")

    qa = pd.DataFrame([{
        "feature_count": len(ordered_features),
        "jointly_valid_pixels": int(X_valid.shape[0]),
        "correlation_sample_pixels": int(X_sample.shape[0]),
        "stack_path": str(stack_path.relative_to(ROOT)),
    }])
    qa.to_csv(OUT / "stage3_stack_qa.csv", index=False)

    print(f"Created {len(ordered_features)}-feature multi-season stack.")
    print(f"Jointly valid pixels: {X_valid.shape[0]:,}")


if __name__ == "__main__":
    main()
