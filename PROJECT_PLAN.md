# Project04 Development Plan

## Stage 1 — Data discovery and QA
Status: **passed**

## Stage 2 — Raster preprocessing
Status: **passed**

## Stage 3 — Feature engineering
Status: **passed**

Observed QA:
- 27 multi-season features created;
- 1,467,614 pixels valid across all features.

## Stage 4 — Reference labels and sampling
Status: **passed**

Observed QA:
- selected reference classes cover 99.76% of jointly valid pixels;
- 30,000 stratified reference samples;
- 6,000 samples per class;
- 2 km block coverage ranges from 31 blocks for Permanent water to 54 blocks for Tree cover;
- no obvious reference-grid alignment failure.

## Stage 5 — Machine-learning baseline
Status: **ready to run**

Comparison:
- 18 multi-season spectral bands;
- 27 bands + NDVI/NDBI/NDWI features;
- Random Forest;
- HistGradientBoosting;
- common stratified 70/30 random pixel split;
- accuracy and macro F1;
- class-level metrics and confusion matrices;
- permutation feature importance.

Decision gate:
Do not interpret Stage 5 scores as final spatial generalisation. They are the conventional random-validation baseline.

## Stage 6 — Spatial validation
Planned:
- spatial block train/test separation;
- hold entire 2 km blocks together;
- compare random versus spatial performance;
- quantify the validation gap.

## Stage 7 — Interpretation and uncertainty
Planned:
- confusion matrices;
- per-class F1;
- feature importance;
- uncertainty / confidence map;
- spatial pattern of classification errors.

## Stage 8 — Final presentation
Planned:
- final classification;
- validation comparison;
- uncertainty map;
- interactive web map;
- concise final report.
