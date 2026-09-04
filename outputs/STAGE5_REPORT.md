# Stage 5 Machine-Learning Baseline Report

## Purpose

Stage 5 establishes the conventional random-validation baseline before spatial validation is introduced.

Two feature designs are compared:

- **Bands only:** 18 multi-season Sentinel-2 spectral-band features;
- **Bands + indices:** all 27 features, including seasonal NDVI, NDBI and NDWI.

Two classifiers are compared:

- Random Forest;
- HistGradientBoosting.

All four comparisons use the same stratified 70/30 random train/test split.

## Random-validation results

| Model | Feature set | Features | Accuracy | Macro F1 | Fit time (s) |
|---|---|---:|---:|---:|---:|
| HistGradientBoosting | bands_plus_indices | 27 | 0.891 | 0.890 | 1.4 |
| Random Forest | bands_only | 18 | 0.888 | 0.888 | 7.5 |
| HistGradientBoosting | bands_only | 18 | 0.887 | 0.887 | 1.2 |
| Random Forest | bands_plus_indices | 27 | 0.888 | 0.887 | 9.5 |

## Best random-validation configuration

- Model: **HistGradientBoosting**
- Feature set: **bands_plus_indices**
- Accuracy: **0.891**
- Macro F1: **0.890**

## Interpretation

These scores are deliberately treated as a baseline rather than final performance estimates.

Neighbouring Sentinel-2 pixels are spatially autocorrelated. A random pixel split can therefore place highly similar nearby observations in both training and testing data.

Stage 6 will repeat the comparison using spatially separated 2 km blocks. The difference between random and spatial validation is a central Project04 result.

## Feature importance

Permutation importance is reported for the best random-validation configuration. It measures the reduction in macro F1 when a feature is shuffled while all other features remain unchanged.

Importance should be interpreted as predictive usefulness within the fitted model, not as a causal effect.

## Next stage

Stage 6 will replace the random pixel split with block-based spatial validation and quantify the validation gap.