# Project04 Development Plan

## Stage 1 — Data discovery and QA
Status: **passed**

## Stage 2 — Raster preprocessing
Status: **passed**

Observed QA:
- ≥1 valid observation: 100% for all three seasons;
- ≥3 valid observations: Spring 99.8%, Summer 99.5%, Autumn 100%;
- median valid observations: 5 for all three seasons.

## Stage 3 — Feature engineering
Status: **passed**

Observed QA:
- 27 multi-season features created;
- 1,467,614 pixels valid across all features;
- 100,000 pixels used for feature-correlation QA;
- NDVI, NDBI and NDWI maps show spatially plausible patterns.

## Stage 4 — Reference labels and sampling
Status: **ready to run**

Processing:
- align ESA WorldCover 2021 v200 to the Project04 10 m feature grid;
- retain Tree cover, Grassland, Cropland, Built-up and Permanent water;
- quantify selected-class coverage and class balance;
- draw up to 6,000 reproducible samples per class;
- assign each sample to a 2 km spatial block;
- generate reference-map, class-balance and sample-distribution QA figures.

Decision gate:
Do not train classifiers until reference coverage, class counts, block coverage and spatial alignment are checked.

## Stage 5 — Machine learning
Planned:
- extract 27 features at reference samples;
- Random Forest;
- HistGradientBoosting;
- compare bands-only and bands-plus-indices feature sets.

## Stage 6 — Spatial validation
Core GIScience step:
- random pixel split;
- spatial block split;
- compare performance difference.

## Stage 7 — Interpretation
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
- feature-importance figure;
- uncertainty map;
- interactive web map;
- concise final report.
