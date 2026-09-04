# Project04 Development Plan

## Stage 1 — Data discovery and QA

Status: **passed**

Observed Stage 1 snapshot:
- 51 Sentinel-2 candidate scenes;
- 15 selected scenes;
- 5 scenes per season;
- predominantly complete Augsburg coverage;
- one summer scene with approximately 95.4% AOI footprint coverage;
- spring includes one scene close to the 20% scene-level cloud-search threshold;
- WorldCover reference source reachable.

## Stage 2 — Raster preprocessing

Status: **passed**

Observed QA:
- ≥1 valid observation: 100% for all three seasons;
- ≥3 valid observations: Spring 99.8%, Summer 99.5%, Autumn 100%;
- median valid observations: 5 for all three seasons;
- P10 valid observations: 5 for all three seasons;
- true-colour composites show no obvious cloud, alignment or coverage failure.

## Stage 3 — Feature engineering

Status: **ready to run**

Processing:
- derive NDVI, NDBI and NDWI for spring, summer and autumn;
- retain six original spectral bands for each season;
- build a 27-band multi-season raster feature stack;
- create a band manifest;
- calculate feature distribution QA;
- calculate a sampled feature-correlation matrix;
- create representative summer index quicklooks.

Decision gate:
Do not proceed to reference-label sampling until feature ranges and index maps are checked.

## Stage 4 — Reference labels

Planned:
- clip WorldCover 2021;
- remap selected classes;
- remove unsupported / ambiguous classes;
- stratified sampling;
- document class balance.

## Stage 5 — Machine learning

Planned:
- Random Forest;
- HistGradientBoosting;
- identical feature sets and evaluation data.

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

Planned outputs:
- true-colour image;
- false-colour image;
- NDVI map;
- final land-cover classification;
- confusion matrices;
- model-comparison figure;
- random-versus-spatial-validation figure;
- feature-importance figure;
- uncertainty map;
- interactive web map;
- concise final report.
