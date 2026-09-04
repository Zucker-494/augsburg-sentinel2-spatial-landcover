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

Status: **ready to run**

Processing:
- construct a 10 m Augsburg target grid in EPSG:32632;
- read selected Sentinel-2 COG assets;
- apply SCL-based quality masking;
- resample spectral bands to the common grid;
- build spring, summer and autumn median composites;
- count valid observations per pixel;
- create true-colour and valid-observation QA figures.

Decision gate:
Do not proceed to feature engineering until seasonal coverage after masking is checked.

## Stage 3 — Feature engineering

Planned:
- original bands;
- NDVI;
- NDBI;
- NDWI;
- multi-season feature stack.

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
