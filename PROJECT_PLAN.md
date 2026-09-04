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

## Stage 6 — Spatial validation
Status: **passed**

Best spatial configuration:
- HistGradientBoosting;
- bands + indices;
- mean spatial macro F1: 0.884 ± 0.008;
- random-minus-spatial gap: approximately 0.72 percentage points.

## Stage 7 — Interpretation and uncertainty
Status: **passed**

Observed:
- Permanent water: highest spatial OOF accuracy (0.978);
- Grassland: lowest spatial OOF accuracy (0.825);
- low-confidence share highest for Grassland (13.6%);
- SWIR features dominate spatial permutation importance;
- spring NDWI and autumn NDVI add predictive information.

## Stage 8 — Final portfolio packaging
Status: **ready to run**

Outputs:
- final land-cover classification figure;
- final report and summary;
- polished README;
- project-freeze status;
- GitHub Pages interactive map;
- classification and confidence overlays.

Final decision gate:
Inspect the final classification and interactive map. If both are visually and spatially correct, freeze Project04.
