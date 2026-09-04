# Stage 6 Spatial Validation Report

## Purpose

Stage 6 tests whether conventional random pixel validation overstates model performance when spatial dependence is present.

Two matched five-fold validation designs are compared:

- **Random 5-fold:** stratified pixel-level folds;
- **Spatial 5-fold:** stratified group folds that keep complete 2 km spatial blocks together.

## Spatial-fold QA

- Number of folds: **5**
- Maximum train/test block overlap: **0**

A block overlap of zero confirms that the spatial folds do not place samples from the same 2 km block in both training and testing subsets.

## Validation results

| Model | Feature set | Random macro F1 | Spatial macro F1 | Gap |
|---|---|---:|---:|---:|
| HistGradientBoosting | bands_plus_indices | 0.891 ± 0.003 | 0.884 ± 0.008 | 0.72 pp |
| HistGradientBoosting | bands_only | 0.889 ± 0.004 | 0.883 ± 0.008 | 0.57 pp |
| Random Forest | bands_only | 0.890 ± 0.002 | 0.881 ± 0.007 | 0.91 pp |
| Random Forest | bands_plus_indices | 0.889 ± 0.003 | 0.880 ± 0.008 | 0.93 pp |

## Best spatial-validation configuration

- Model: **HistGradientBoosting**
- Feature set: **bands_plus_indices**
- Mean spatial macro F1: **0.884**
- Fold SD: **0.008**

## Interpretation

The random-versus-spatial gap is the main Stage 6 result.

A positive gap indicates that random pixel validation is more optimistic than spatially separated validation. This is consistent with the idea that nearby image pixels share spectral and land-cover characteristics.

The spatial result should still not be interpreted as independent real-world accuracy because the target labels come from WorldCover rather than field ground truth.

## Why five folds?

Using five folds reduces dependence on one arbitrary train/test partition and allows variability across folds to be reported.

## Next stage

Stage 7 will focus on interpretation: class-specific errors, confidence/uncertainty, feature importance under the selected spatially validated configuration, and the spatial distribution of model mistakes.