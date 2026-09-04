# Project04 Final Report

## Project title

**Augsburg Sentinel-2 Spatial Land-Cover Classification**

## Research question

How well can multi-season Sentinel-2 imagery reproduce major land-cover patterns in Augsburg, and how do feature engineering and spatial validation change apparent model performance?

## Key results

- Best spatially validated model: **HistGradientBoosting / bands_plus_indices**
- Spatial macro F1: **0.884 ± 0.008**
- Matched random 5-fold macro F1: **0.891 ± 0.003**
- Random-minus-spatial gap: **0.72 percentage points**

Random pixel validation is mildly optimistic rather than dramatically misleading under the 2 km block design used here.

## Class-specific interpretation

| Class | Spatial OOF accuracy | Median confidence | Confidence < 0.60 |
|---|---:|---:|---:|
| Tree cover | 0.834 | 0.991 | 10.3% |
| Grassland | 0.825 | 0.923 | 13.6% |
| Cropland | 0.870 | 0.987 | 8.3% |
| Built-up | 0.919 | 0.963 | 9.1% |
| Permanent water | 0.978 | 1.000 | 1.2% |

Permanent water is the most stable class. Grassland is the most difficult, consistent with spectral overlap among grassland, cropland and other vegetated surfaces.

## Most useful spatially validated features

| Feature | Mean permutation importance |
|---|---:|
| summer_swir22 | 0.0822 |
| spring_swir16 | 0.0752 |
| autumn_swir16 | 0.0541 |
| spring_ndwi | 0.0461 |
| autumn_ndvi | 0.0341 |
| spring_swir22 | 0.0297 |
| autumn_swir22 | 0.0238 |
| summer_swir16 | 0.0194 |

SWIR features remain dominant after moving from random to spatial validation. Spectral indices add useful information but do not replace the predictive value of the original bands.

## What makes this more than a basic classification demo

- multi-season rather than single-scene input;
- explicit cloud and quality QA;
- bands-only versus bands-plus-indices comparison;
- two machine-learning models;
- matched random and spatial five-fold validation;
- spatially validated feature importance;
- out-of-fold error mapping;
- relative confidence mapping;
- reproducible GitHub Actions workflow;
- interactive final map.

## Limitations

1. ESA WorldCover is a reproducible reference-label product, not independent field ground truth.
2. Spatial validation uses a fixed 2 km block size; other scales could change the validation gap.
3. HistGradientBoosting confidence values are not calibrated probabilities.
4. The workflow uses selected 2021 observations and does not test temporal transfer to other years.
5. The final classification reproduces the selected five-class reference scheme rather than providing a new operational land-cover product.

## Final interpretation

Project04 shows that a relatively simple tree-based remote-sensing classifier can achieve stable spatial performance when the data pipeline is carefully controlled. The stronger methodological contribution is the explicit comparison of random and spatial validation, together with uncertainty and class-specific error analysis.