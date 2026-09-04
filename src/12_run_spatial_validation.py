from __future__ import annotations

from pathlib import Path
import json
import time

import numpy as np
import pandas as pd
import rasterio

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

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


def load_samples_and_features():
    samples = pd.read_csv(SAMPLE_PATH)

    with rasterio.open(STACK_PATH) as src:
        names = list(src.descriptions)
        if not all(names):
            names = [f"band_{i}" for i in range(1, src.count + 1)]

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


def feature_sets(names):
    bands_only = [
        i for i, n in enumerate(names)
        if not n.endswith(("ndvi", "ndbi", "ndwi"))
    ]
    return {
        "bands_only": bands_only,
        "bands_plus_indices": list(range(len(names))),
    }


def make_model(name):
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=500,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
    if name == "HistGradientBoosting":
        return HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=300,
            max_leaf_nodes=31,
            l2_regularization=0.1,
            random_state=RANDOM_SEED,
        )
    raise ValueError(name)


def build_splits(y, groups):
    random_cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_SEED,
    )
    spatial_cv = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_SEED,
    )

    random_splits = list(random_cv.split(np.zeros(len(y)), y))
    spatial_splits = list(spatial_cv.split(np.zeros(len(y)), y, groups=groups))

    return {
        "random_5fold": random_splits,
        "spatial_5fold": spatial_splits,
    }


def validate_spatial_folds(splits, y, groups):
    rows = []

    for fold, (train_idx, test_idx) in enumerate(splits, start=1):
        train_groups = set(groups[train_idx])
        test_groups = set(groups[test_idx])

        overlap = train_groups.intersection(test_groups)
        if overlap:
            raise RuntimeError(
                f"Spatial leakage in fold {fold}: overlapping groups {sorted(overlap)}"
            )

        train_classes = set(np.unique(y[train_idx]))
        test_classes = set(np.unique(y[test_idx]))
        expected = set(CLASS_ORDER)

        if train_classes != expected or test_classes != expected:
            raise RuntimeError(
                f"Fold {fold} does not contain all classes in both train and test."
            )

        rows.append({
            "fold": fold,
            "train_samples": len(train_idx),
            "test_samples": len(test_idx),
            "train_blocks": len(train_groups),
            "test_blocks": len(test_groups),
            "block_overlap": len(overlap),
        })

    pd.DataFrame(rows).to_csv(
        OUT / "stage6_spatial_fold_qa.csv",
        index=False,
    )


def evaluate_configuration(
    validation_name,
    splits,
    model_name,
    feature_set_name,
    X,
    y,
    feature_idx,
):
    fold_rows = []
    class_rows = []

    Xs = X[:, feature_idx]

    for fold, (train_idx, test_idx) in enumerate(splits, start=1):
        model = make_model(model_name)

        start = time.perf_counter()
        model.fit(Xs[train_idx], y[train_idx])
        fit_seconds = time.perf_counter() - start

        pred = model.predict(Xs[test_idx])

        accuracy = accuracy_score(y[test_idx], pred)
        macro_f1 = f1_score(y[test_idx], pred, average="macro")

        fold_rows.append({
            "validation": validation_name,
            "model": model_name,
            "feature_set": feature_set_name,
            "feature_count": len(feature_idx),
            "fold": fold,
            "train_samples": len(train_idx),
            "test_samples": len(test_idx),
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "fit_seconds": fit_seconds,
        })

        precision, recall, f1, support = precision_recall_fscore_support(
            y[test_idx],
            pred,
            labels=CLASS_ORDER,
            zero_division=0,
        )
        for code, p, r, f, s in zip(
            CLASS_ORDER, precision, recall, f1, support
        ):
            class_rows.append({
                "validation": validation_name,
                "model": model_name,
                "feature_set": feature_set_name,
                "fold": fold,
                "class_code": code,
                "class_name": CLASS_NAMES[code],
                "precision": p,
                "recall": r,
                "f1": f,
                "support": int(s),
            })

        print(
            f"{validation_name} | {model_name} | {feature_set_name} | "
            f"fold {fold}: macro F1={macro_f1:.4f}"
        )

    return fold_rows, class_rows


def main():
    samples, X, y, groups, names = load_samples_and_features()
    fs = feature_sets(names)
    splits = build_splits(y, groups)

    validate_spatial_folds(splits["spatial_5fold"], y, groups)

    all_folds = []
    all_classes = []

    for validation_name, split_list in splits.items():
        for feature_set_name, feature_idx in fs.items():
            for model_name in ["Random Forest", "HistGradientBoosting"]:
                fold_rows, class_rows = evaluate_configuration(
                    validation_name,
                    split_list,
                    model_name,
                    feature_set_name,
                    X,
                    y,
                    feature_idx,
                )
                all_folds.extend(fold_rows)
                all_classes.extend(class_rows)

    folds = pd.DataFrame(all_folds)
    classes = pd.DataFrame(all_classes)

    folds.to_csv(OUT / "stage6_fold_results.csv", index=False)
    classes.to_csv(OUT / "stage6_class_fold_results.csv", index=False)

    summary = (
        folds.groupby(["validation", "model", "feature_set"], as_index=False)
        .agg(
            mean_accuracy=("accuracy", "mean"),
            sd_accuracy=("accuracy", "std"),
            mean_macro_f1=("macro_f1", "mean"),
            sd_macro_f1=("macro_f1", "std"),
            mean_fit_seconds=("fit_seconds", "mean"),
        )
    )
    summary.to_csv(OUT / "stage6_validation_summary.csv", index=False)

    random = (
        summary[summary["validation"] == "random_5fold"]
        .drop(columns=["validation"])
        .rename(columns={
            "mean_accuracy": "random_mean_accuracy",
            "sd_accuracy": "random_sd_accuracy",
            "mean_macro_f1": "random_mean_macro_f1",
            "sd_macro_f1": "random_sd_macro_f1",
            "mean_fit_seconds": "random_mean_fit_seconds",
        })
    )
    spatial = (
        summary[summary["validation"] == "spatial_5fold"]
        .drop(columns=["validation"])
        .rename(columns={
            "mean_accuracy": "spatial_mean_accuracy",
            "sd_accuracy": "spatial_sd_accuracy",
            "mean_macro_f1": "spatial_mean_macro_f1",
            "sd_macro_f1": "spatial_sd_macro_f1",
            "mean_fit_seconds": "spatial_mean_fit_seconds",
        })
    )

    gap = random.merge(spatial, on=["model", "feature_set"])
    gap["macro_f1_gap"] = (
        gap["random_mean_macro_f1"] - gap["spatial_mean_macro_f1"]
    )
    gap["accuracy_gap"] = (
        gap["random_mean_accuracy"] - gap["spatial_mean_accuracy"]
    )
    gap.to_csv(OUT / "stage6_validation_gap.csv", index=False)

    metadata = {
        "n_splits": N_SPLITS,
        "random_seed": RANDOM_SEED,
        "spatial_group_field": "block_id",
        "spatial_block_size_m": 2000,
        "note": (
            "Random and spatial validation are both evaluated with five folds. "
            "Spatial folds keep complete 2 km blocks together."
        ),
    }
    (OUT / "stage6_run_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("\nValidation summary:")
    print(summary.to_string(index=False))
    print("\nRandom minus spatial validation gap:")
    print(
        gap[
            ["model", "feature_set", "macro_f1_gap", "accuracy_gap"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
