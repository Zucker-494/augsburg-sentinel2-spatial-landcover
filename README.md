# Augsburg Sentinel-2 Spatial Land-Cover Classification

A beginner-friendly but methodologically progressive remote-sensing and spatial machine-learning project for Augsburg, Germany.

## Main question

**How well can multi-season Sentinel-2 imagery reproduce major land-cover patterns, and how do feature engineering and spatial validation change apparent model performance?**

## Final workflow

```text
15 Sentinel-2 scenes
→ seasonal SCL-masked composites
→ 27 multi-season spectral features
→ WorldCover reference labels
→ 30,000 stratified samples
→ Random Forest vs HistGradientBoosting
→ random vs spatial five-fold validation
→ confidence and error analysis
→ final land-cover map
```

## Core result

The best configuration was **HistGradientBoosting with bands + indices**.

- Random 5-fold macro F1: approximately **0.891**
- Spatial 5-fold macro F1: approximately **0.884**
- Random-minus-spatial gap: approximately **0.7 percentage points**

Random pixel validation was therefore mildly optimistic, but spatial validation did not produce a large performance collapse.

## What makes this more than a basic classification demo

- multi-season Sentinel-2 input;
- 10 m band alignment;
- SCL cloud/shadow masking;
- NDVI, NDBI and NDWI feature engineering;
- model comparison;
- spatial block validation;
- spatial out-of-fold error analysis;
- permutation importance under spatial validation;
- confidence mapping;
- reproducible GitHub Actions;
- interactive web map.

## Beginner guide

Start with **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)**.

## Important limitation

ESA WorldCover 2021 is used as a reproducible **reference-label product**, not independent field ground truth. Reported scores therefore describe agreement with this reference scheme under the stated validation design.

## Interactive map

After GitHub Pages is enabled from the `/docs` folder, the map provides:

- OpenStreetMap basemap;
- final classification;
- relative model-confidence view;
- Augsburg municipal boundary.

## Project status

**Complete / frozen after Stage 8 QA.**
