# Stage 3 Feature Engineering Report

## Purpose

Stage 3 converts the seasonal Sentinel-2 composites into machine-learning features.

The final feature stack contains **27 raster features**:

- 6 spectral bands × 3 seasons = 18 band features;
- NDVI, NDBI and NDWI × 3 seasons = 9 engineered features.

## Spectral-index definitions

- **NDVI** = (NIR − Red) / (NIR + Red)
- **NDBI** = (SWIR1 − NIR) / (SWIR1 + NIR)
- **NDWI** = (Green − NIR) / (Green + NIR)

NDWI refers here to the Green–NIR form commonly associated with surface-water enhancement.

## Stack QA

- Feature count: **27**
- Pixels valid across all features: **1,467,614**
- Pixels used for correlation QA: **100,000**

## Index summary by season

| Feature | P02 | Median | P98 |
|---|---:|---:|---:|
| spring_ndvi | 0.039 | 0.486 | 0.828 |
| spring_ndbi | -0.405 | 0.001 | 0.310 |
| spring_ndwi | -0.754 | -0.501 | -0.057 |
| summer_ndvi | 0.029 | 0.693 | 0.900 |
| summer_ndbi | -0.501 | -0.211 | 0.225 |
| summer_ndwi | -0.823 | -0.636 | -0.043 |
| autumn_ndvi | 0.030 | 0.725 | 0.912 |
| autumn_ndbi | -0.534 | -0.219 | 0.249 |
| autumn_ndwi | -0.836 | -0.656 | -0.043 |

## Interpretation

The spectral-index rasters are derived from the quality-masked seasonal median composites, so they inherit the spatial alignment and cloud-screening decisions from Stage 2.

The correlation table is a QA diagnostic rather than a feature-selection decision. Strong correlation between some bands and indices is expected because the indices are algebraically derived from the same spectral inputs.

## Next stage

Stage 4 will clip and remap the WorldCover 2021 reference layer, inspect class balance, and construct reproducible training and validation samples.