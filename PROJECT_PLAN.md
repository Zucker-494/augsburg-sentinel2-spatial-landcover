# Project04 Development Plan

## Stage 1 — Data discovery and QA

Status: **ready**

Outputs:
- exact Augsburg municipal boundary;
- Sentinel-2 seasonal scene inventory;
- selected low-cloud candidate scenes;
- WorldCover source check;
- Stage 1 report.

Decision gate:
Do not proceed to modelling until scene coverage and cloud conditions are inspected.

## Stage 2 — Raster preprocessing

Planned:
- read selected COG assets;
- crop to Augsburg;
- apply reflectance scaling;
- cloud and cloud-shadow masking from SCL;
- resample B11/B12 from 20 m to 10 m;
- create seasonal median composites;
- verify CRS, transform, shape and nodata consistency.

## Stage 3 — Feature engineering

Planned:
- original bands;
- NDVI;
- NDBI;
- NDWI;
- optional multi-season features.

Comparison:
- bands only;
- bands + engineered indices.

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
