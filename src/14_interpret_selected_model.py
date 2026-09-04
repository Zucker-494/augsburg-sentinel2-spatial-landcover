from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
import rasterio

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLES = ROOT / "data" / "samples"
OUT = ROOT / "outputs"

OUT.mkdir(parents=True, exist_ok=True)

STACK_PATH = PROCESSED / "multiseason_feature_stack.tif"
SAMPLE_PATH = SAMPLES / "reference_samples.csv"

RANDOM_SEED = 42
N_SPLITS = 5

CLASS_ORDER = [10, 30, 40, 50, 80]
CLASS_NAMES = {
    10: "Tree cover",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    80: "Permanent water",
}


def build_model():
    return HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_iter=300,
        max_leaf_nodes=31,
        l2_regularization=0.1,
        random_state=RANDOM_SEED,
    )


def load_data():
    samples = pd.read_csv(SAMPLE_PATH)

    with rasterio.open(STACK_PATH) as src:
        names = list(src.descriptions)
        rows = samples["row"].to_numpy(dtype=int)
        cols = samples["col"].to_numpy(dtype=int)

        X = np.empty((len(samples), src.count), dtype="float32")
        for b in range(1, src.count + 1):
            arr = src.read(b)
            vals = arr[rows, cols].astype("float32")
            if src.nodata is not None:
                vals[vals == src.nodata] = np.nan
            X[:, b - 1] = vals

    valid = np.all(np.isfinite(X), axis=1)
    samples = samples.loc[valid].reset_index(drop=True)
    X = X[valid]

    y = samples["class_code"].to_numpy(dtype=int)
    groups = samples["block_id"].astype(str).to_numpy()
    return samples, X, y, groups, names


def main():
    samples, X, y, groups, feature_names = load_data()

    cv = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_SEED,
    )

    oof_pred = np.empty(len(y), dtype=int)
    oof_conf = np.empty(len(y), dtype="float32")
    oof_fold = np.empty(len(y), dtype=int)

    importance_rows = []

    for fold, (train_idx, test_idx) in enumerate(
        cv.split(X, y, groups=groups),
        start=1,
    ):
        model = build_model()
        model.fit(X[train_idx], y[train_idx])

        prob = model.predict_proba(X[test_idx])
        pred = model.classes_[np.argmax(prob, axis=1)]
        conf = np.max(prob, axis=1)

        oof_pred[test_idx] = pred
        oof_conf[test_idx] = conf
        oof_fold[test_idx] = fold

        # Spatially validated permutation importance on a deterministic subset.
        rng = np.random.default_rng(RANDOM_SEED + fold)
        n_imp = min(2500, len(test_idx))
        sub = rng.choice(len(test_idx), size=n_imp, replace=False)

        perm = permutation_importance(
            model,
            X[test_idx][sub],
            y[test_idx][sub],
            scoring="f1_macro",
            n_repeats=4,
            random_state=RANDOM_SEED + fold,
            n_jobs=1,
        )

        for feature, mean, sd in zip(
            feature_names,
            perm.importances_mean,
            perm.importances_std,
        ):
            importance_rows.append({
                "fold": fold,
                "feature": feature,
                "importance_mean": mean,
                "importance_sd": sd,
            })

        print(f"Completed spatial interpretation fold {fold}")

    out = samples.copy()
    out["observed_class"] = y
    out["predicted_class"] = oof_pred
    out["predicted_name"] = [
        CLASS_NAMES[int(c)] for c in oof_pred
    ]
    out["confidence"] = oof_conf
    out["correct"] = (y == oof_pred)
    out["fold"] = oof_fold
    out.to_csv(
        OUT / "stage7_spatial_oof_predictions.csv",
        index=False,
    )

    # Aggregate confusion matrix.
    cm = confusion_matrix(y, oof_pred, labels=CLASS_ORDER)
    cm_df = pd.DataFrame(
        cm,
        index=[CLASS_NAMES[c] for c in CLASS_ORDER],
        columns=[CLASS_NAMES[c] for c in CLASS_ORDER],
    )
    cm_df.to_csv(OUT / "stage7_spatial_confusion_counts.csv")

    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm = np.divide(
        cm,
        row_sums,
        out=np.zeros_like(cm, dtype=float),
        where=row_sums != 0,
    )
    pd.DataFrame(
        cm_norm,
        index=[CLASS_NAMES[c] for c in CLASS_ORDER],
        columns=[CLASS_NAMES[c] for c in CLASS_ORDER],
    ).to_csv(OUT / "stage7_spatial_confusion_row_normalized.csv")

    imp = pd.DataFrame(importance_rows)
    imp.to_csv(
        OUT / "stage7_spatial_permutation_importance_folds.csv",
        index=False,
    )
    imp_summary = (
        imp.groupby("feature", as_index=False)
        .agg(
            mean_importance=("importance_mean", "mean"),
            sd_between_folds=("importance_mean", "std"),
        )
        .sort_values("mean_importance", ascending=False)
    )
    imp_summary.to_csv(
        OUT / "stage7_spatial_permutation_importance_summary.csv",
        index=False,
    )

    # Confidence summaries.
    conf_rows = []
    for class_code, class_name in CLASS_NAMES.items():
        mask = y == class_code
        conf_rows.append({
            "class_code": class_code,
            "class_name": class_name,
            "samples": int(mask.sum()),
            "accuracy": float(np.mean(oof_pred[mask] == y[mask])),
            "median_confidence": float(np.median(oof_conf[mask])),
            "p10_confidence": float(np.percentile(oof_conf[mask], 10)),
            "low_confidence_below_0_60_pct": float(
                100 * np.mean(oof_conf[mask] < 0.60)
            ),
        })
    pd.DataFrame(conf_rows).to_csv(
        OUT / "stage7_class_confidence_summary.csv",
        index=False,
    )

    # Fit the selected final model on all 30k reference samples for full-grid prediction.
    final_model = build_model()
    final_model.fit(X, y)

    with rasterio.open(STACK_PATH) as src:
        profile = src.profile.copy()
        height, width = src.height, src.width

        class_profile = profile.copy()
        class_profile.update(
            count=1,
            dtype="uint8",
            nodata=0,
            compress="deflate",
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )
        conf_profile = profile.copy()
        conf_profile.update(
            count=1,
            dtype="float32",
            nodata=-9999.0,
            compress="deflate",
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )

        class_path = PROCESSED / "final_hgb_classification.tif"
        conf_path = PROCESSED / "final_hgb_confidence.tif"

        with rasterio.open(class_path, "w", **class_profile) as class_dst, \
             rasterio.open(conf_path, "w", **conf_profile) as conf_dst:

            for _, window in src.block_windows(1):
                cube = src.read(window=window).astype("float32")
                h, w = cube.shape[1], cube.shape[2]
                Xw = np.moveaxis(cube, 0, -1).reshape(-1, cube.shape[0])

                if src.nodata is not None:
                    Xw[Xw == src.nodata] = np.nan

                valid = np.all(np.isfinite(Xw), axis=1)

                class_out = np.zeros(len(Xw), dtype="uint8")
                conf_out = np.full(len(Xw), -9999.0, dtype="float32")

                if np.any(valid):
                    prob = final_model.predict_proba(Xw[valid])
                    pred = final_model.classes_[np.argmax(prob, axis=1)]
                    conf = np.max(prob, axis=1)

                    class_out[valid] = pred.astype("uint8")
                    conf_out[valid] = conf.astype("float32")

                class_dst.write(
                    class_out.reshape(h, w), 1, window=window
                )
                conf_dst.write(
                    conf_out.reshape(h, w), 1, window=window
                )

    metadata = {
        "selected_model": "HistGradientBoosting",
        "selected_feature_set": "bands_plus_indices",
        "feature_count": len(feature_names),
        "spatial_validation": "5-fold StratifiedGroupKFold",
        "spatial_block_size_m": 2000,
        "final_model_fit": (
            "Final full-grid prediction model fitted to all 30,000 reference samples "
            "after model selection. Raster confidence is model probability, not calibrated probability."
        ),
    }
    (OUT / "stage7_run_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("Stage 7 interpretation outputs created.")


if __name__ == "__main__":
    main()
