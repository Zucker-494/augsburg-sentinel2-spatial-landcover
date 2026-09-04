from __future__ import annotations

from pathlib import Path
import json
import time

import numpy as np
import pandas as pd
import rasterio

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLES = ROOT / "data" / "samples"
OUT = ROOT / "outputs"
MODEL_DIR = ROOT / "data" / "models"

OUT.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

STACK_PATH = PROCESSED / "multiseason_feature_stack.tif"
SAMPLE_PATH = SAMPLES / "reference_samples.csv"

RANDOM_SEED = 42
TEST_SIZE = 0.30

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
        feature_names = list(src.descriptions)
        if not all(feature_names):
            feature_names = [f"band_{i}" for i in range(1, src.count + 1)]

        rows = samples["row"].to_numpy(dtype=int)
        cols = samples["col"].to_numpy(dtype=int)

        X = np.empty((len(samples), src.count), dtype="float32")
        for band_idx in range(1, src.count + 1):
            arr = src.read(band_idx)
            vals = arr[rows, cols].astype("float32")
            if src.nodata is not None:
                vals[vals == src.nodata] = np.nan
            X[:, band_idx - 1] = vals

    valid = np.all(np.isfinite(X), axis=1)
    if not np.all(valid):
        print(f"Dropping {(~valid).sum()} samples with non-finite features.")
        samples = samples.loc[valid].reset_index(drop=True)
        X = X[valid]

    y = samples["class_code"].to_numpy(dtype=int)
    return samples, X, y, feature_names


def build_feature_sets(feature_names):
    band_only = [
        i for i, name in enumerate(feature_names)
        if not name.endswith(("ndvi", "ndbi", "ndwi"))
    ]
    full = list(range(len(feature_names)))

    return {
        "bands_only": band_only,
        "bands_plus_indices": full,
    }


def build_models():
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=500,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=300,
            max_leaf_nodes=31,
            l2_regularization=0.1,
            random_state=RANDOM_SEED,
        ),
    }


def evaluate_model(
    model_name,
    model,
    feature_set_name,
    X_train,
    X_test,
    y_train,
    y_test,
    selected_feature_names,
):
    start = time.perf_counter()
    model.fit(X_train, y_train)
    fit_seconds = time.perf_counter() - start

    start = time.perf_counter()
    pred = model.predict(X_test)
    predict_seconds = time.perf_counter() - start

    accuracy = accuracy_score(y_test, pred)
    macro_f1 = f1_score(y_test, pred, average="macro")

    cm = confusion_matrix(y_test, pred, labels=CLASS_ORDER)
    cm_df = pd.DataFrame(
        cm,
        index=[CLASS_NAMES[c] for c in CLASS_ORDER],
        columns=[CLASS_NAMES[c] for c in CLASS_ORDER],
    )
    safe_name = (
        model_name.lower().replace(" ", "_")
        + "__"
        + feature_set_name
    )
    cm_df.to_csv(OUT / f"stage5_confusion_{safe_name}.csv")

    report = classification_report(
        y_test,
        pred,
        labels=CLASS_ORDER,
        target_names=[CLASS_NAMES[c] for c in CLASS_ORDER],
        output_dict=True,
        zero_division=0,
    )
    report_rows = []
    for class_name in [CLASS_NAMES[c] for c in CLASS_ORDER]:
        row = report[class_name]
        report_rows.append({
            "model": model_name,
            "feature_set": feature_set_name,
            "class_name": class_name,
            "precision": row["precision"],
            "recall": row["recall"],
            "f1": row["f1-score"],
            "support": int(row["support"]),
        })
    pd.DataFrame(report_rows).to_csv(
        OUT / f"stage5_class_metrics_{safe_name}.csv",
        index=False,
    )

    # Permutation importance is calculated on a deterministic subset
    # to keep cloud runtime manageable and comparable across models.
    rng = np.random.default_rng(RANDOM_SEED)
    n_imp = min(4000, len(X_test))
    imp_idx = rng.choice(len(X_test), size=n_imp, replace=False)

    perm = permutation_importance(
        model,
        X_test[imp_idx],
        y_test[imp_idx],
        scoring="f1_macro",
        n_repeats=5,
        random_state=RANDOM_SEED,
        n_jobs=1,
    )
    importance_df = pd.DataFrame({
        "feature": selected_feature_names,
        "importance_mean": perm.importances_mean,
        "importance_sd": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)
    importance_df.to_csv(
        OUT / f"stage5_importance_{safe_name}.csv",
        index=False,
    )

    return {
        "model": model_name,
        "feature_set": feature_set_name,
        "feature_count": len(selected_feature_names),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "fit_seconds": fit_seconds,
        "predict_seconds": predict_seconds,
    }


def main():
    samples, X, y, feature_names = load_samples_and_features()
    feature_sets = build_feature_sets(feature_names)

    # One common stratified train/test split is reused for every comparison.
    train_idx, test_idx = train_test_split(
        np.arange(len(y)),
        test_size=TEST_SIZE,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    split_table = samples.copy()
    split_table["random_split"] = "train"
    split_table.loc[test_idx, "random_split"] = "test"
    split_table.to_csv(
        OUT / "stage5_random_split_assignments.csv",
        index=False,
    )

    results = []

    for feature_set_name, feature_idx in feature_sets.items():
        selected_names = [feature_names[i] for i in feature_idx]

        X_fs = X[:, feature_idx]
        X_train = X_fs[train_idx]
        X_test = X_fs[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]

        for model_name, model in build_models().items():
            print(f"\n=== {model_name} | {feature_set_name} ===")
            result = evaluate_model(
                model_name,
                model,
                feature_set_name,
                X_train,
                X_test,
                y_train,
                y_test,
                selected_names,
            )
            results.append(result)
            print(
                f"Accuracy={result['accuracy']:.4f}, "
                f"Macro F1={result['macro_f1']:.4f}"
            )

    results_df = pd.DataFrame(results).sort_values(
        ["macro_f1", "accuracy"],
        ascending=False,
    )
    results_df.to_csv(
        OUT / "stage5_random_validation_results.csv",
        index=False,
    )

    metadata = {
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "total_samples": len(samples),
        "class_order": CLASS_ORDER,
        "class_names": CLASS_NAMES,
        "feature_names": feature_names,
        "note": (
            "Stage 5 uses random stratified pixel validation only. "
            "Spatial block validation is intentionally reserved for Stage 6."
        ),
    }
    (OUT / "stage5_run_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("\nStage 5 model comparison:")
    print(results_df.to_string(index=False))


if __name__ == "__main__":
    main()
