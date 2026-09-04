# Project04 Development Plan

## Stage 1 — Data discovery and QA
Status: **passed**

## Stage 2 — Raster preprocessing
Status: **passed**

## Stage 3 — Feature engineering
Status: **passed**

## Stage 4 — Reference labels and sampling
Status: **passed**

Observed QA:
- five selected WorldCover classes cover 99.76% of jointly valid pixels;
- 30,000 stratified reference samples;
- 6,000 samples per class;
- each class represented across multiple 2 km spatial blocks.

## Stage 5 — Machine-learning baseline
Status: **passed**

Observed random 70/30 baseline:
- HistGradientBoosting + bands + indices: Accuracy 0.891, Macro F1 0.890;
- Random Forest + bands only: Accuracy 0.888, Macro F1 0.888;
- HistGradientBoosting + bands only: Accuracy 0.887, Macro F1 0.887;
- Random Forest + bands + indices: Accuracy 0.888, Macro F1 0.887.

Interpretation:
- spectral indices provide only a small improvement for HistGradientBoosting;
- they do not improve Random Forest in this single random split;
- SWIR features dominate the best-model permutation-importance ranking.

## Stage 6 — Spatial validation
Status: **ready to run**

Core comparison:
- stratified random 5-fold CV;
- stratified grouped spatial 5-fold CV;
- complete 2 km spatial blocks kept within folds;
- identical four model / feature-set configurations;
- mean ± SD across folds;
- random-minus-spatial validation gap;
- class-level F1 under the best spatial configuration.

Decision gate:
Do not proceed to final interpretation until block leakage is confirmed to be zero and all classes are represented in each spatial fold.

## Stage 7 — Interpretation and uncertainty
Planned:
- fit selected model;
- class-specific confusion patterns;
- spatial error distribution;
- prediction confidence / uncertainty;
- feature importance under the selected configuration.

## Stage 8 — Final presentation
Planned:
- final classification;
- uncertainty map;
- core validation figures;
- interactive web map;
- concise final report.
