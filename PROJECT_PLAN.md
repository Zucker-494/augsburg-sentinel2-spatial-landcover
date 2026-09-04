# Project04 Development Plan

## Stage 1 — Data discovery and QA
Status: **passed**

## Stage 2 — Raster preprocessing
Status: **passed**

## Stage 3 — Feature engineering
Status: **passed**

## Stage 4 — Reference labels and sampling
Status: **passed**

## Stage 5 — Machine-learning baseline
Status: **passed**

Observed random baseline:
- best single random split: HistGradientBoosting + bands + indices;
- Accuracy 0.891;
- Macro F1 0.890.

## Stage 6 — Spatial validation
Status: **passed**

Observed 5-fold validation:
- HistGradientBoosting + bands + indices: random macro F1 0.891 ± 0.003; spatial 0.884 ± 0.008; gap 0.72 pp;
- HistGradientBoosting + bands only: 0.889 ± 0.004 vs 0.883 ± 0.008; gap 0.57 pp;
- Random Forest + bands only: 0.890 ± 0.002 vs 0.881 ± 0.007; gap 0.91 pp;
- Random Forest + bands + indices: 0.889 ± 0.003 vs 0.880 ± 0.008; gap 0.93 pp;
- spatial train/test block overlap: 0.

Interpretation:
- random pixel validation is mildly optimistic;
- the observed gap is approximately 0.6–0.9 percentage points rather than a large collapse;
- HistGradientBoosting + bands + indices remains the best spatially validated configuration.

## Stage 7 — Interpretation and uncertainty
Status: **ready to run**

Processing:
- regenerate spatial out-of-fold predictions for the selected configuration;
- row-normalized spatial confusion matrix;
- spatial distribution of out-of-fold errors;
- class-specific confidence summaries;
- permutation importance averaged across spatial folds;
- fit selected model to all reference samples;
- predict full-study classification and relative confidence rasters.

Decision gate:
Check confusion structure, error geography, confidence patterns and spatial feature importance before assembling final outputs.

## Stage 8 — Final presentation
Planned:
- final land-cover map;
- final confidence map;
- core model/validation figures;
- interactive web map;
- final README and concise project report.
