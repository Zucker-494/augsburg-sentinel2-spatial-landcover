# Augsburg Sentinel-2 Spatial Land-Cover Classification

Project04 is a reproducible remote-sensing and spatial machine-learning project designed for readers who may have **no previous remote-sensing experience**.

The project asks:

> How well can Sentinel-2 multispectral imagery reproduce major land-cover patterns in Augsburg, and how do feature engineering and spatial validation change the apparent performance of the classifier?

## Why this is more than a basic classification demo

A basic workflow would stop at:

```text
Sentinel-2 → Random Forest → land-cover map → accuracy
```

Project04 adds several GIScience-oriented steps:

```text
Sentinel-2 Level-2A
        ↓
multi-season scene selection
        ↓
cloud / quality filtering
        ↓
spectral bands + indices
        ↓
model comparison
        ↓
random validation
        ↓
spatial block validation
        ↓
feature interpretation
        ↓
classification uncertainty
```

The most important methodological comparison is **random versus spatial validation**. Neighbouring image pixels are spatially autocorrelated, so a random pixel split can produce overly optimistic performance estimates.

## Beginner?

Start with:

**[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)**

It explains bands, NIR, SWIR, NDVI, NDBI, NDWI, pixels, GeoTIFF, CRS, Random Forest, F1, spatial autocorrelation, spatial validation, and uncertainty.

## Study area

Augsburg, Germany.

The study area uses the actual municipal administrative boundary corresponding to OpenStreetMap relation **62407**, rather than a rectangular bounding box.

## Data sources

### Sentinel-2

Stage 1 searches public Sentinel-2 Level-2A metadata through the Element 84 Earth Search STAC API.

For temporal consistency with the first reference-label workflow, the initial project uses 2021 imagery.

### ESA WorldCover 2021

ESA WorldCover 2021 v200 is used as a **reference-label layer**.

This is an important methodological limitation:

> WorldCover is not independent field truth, and agreement with WorldCover must not be reported as independent real-world classification accuracy.

WorldCover itself was derived from Earth-observation data, including Sentinel imagery. The first version of Project04 therefore evaluates spatial generalisation relative to this reproducible reference product.

## Stage 1

Stage 1 does not train a classifier yet.

It:

1. downloads the Augsburg municipal boundary;
2. searches spring, summer and autumn Sentinel-2 scenes;
3. calculates scene coverage of the municipal area;
4. ranks scenes by AOI coverage and reported cloud cover;
5. selects a small candidate set for each season;
6. checks the WorldCover reference source;
7. generates a data-discovery report.

Run:

```bash
python src/run_stage1.py
```

Expected outputs:

```text
outputs/scene_inventory.csv
outputs/selected_scenes.csv
outputs/figure01_scene_cloud_cover.png
outputs/STAGE1_REPORT.md
outputs/study_area_summary.json
outputs/worldcover_source_check.json
```

## Planned later stages

- seasonal Sentinel-2 composites;
- cloud and shadow masking;
- 10 m band alignment;
- NDVI, NDBI and NDWI;
- WorldCover class remapping;
- Random Forest baseline;
- second tree-based model;
- random train/test validation;
- spatial block validation;
- class-level F1 and confusion matrices;
- feature importance;
- prediction-confidence mapping;
- final land-cover map and interactive presentation.

## Reproducibility

The repository includes a GitHub Actions workflow for Stage 1 so the data-discovery step can be executed in a clean cloud environment.

## Scope

This is a portfolio and methods-learning project. It is not presented as a new operational land-cover product for Augsburg.
