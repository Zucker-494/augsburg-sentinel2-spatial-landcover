# Stage 2 Raster Preprocessing Report

## Purpose

Stage 2 converts the selected Sentinel-2 scenes into spatially aligned seasonal composites.

The workflow performs:

- 10 m target-grid construction in EPSG:32632;
- SCL-based cloud, cloud-shadow, snow/ice and invalid-pixel masking;
- bilinear resampling of spectral bands to the common 10 m grid;
- nearest-neighbour resampling of the categorical SCL layer;
- seasonal per-pixel median compositing;
- valid-observation counting for QA.

## Composite QA

| Season | Scenes | ≥1 valid obs | ≥3 valid obs | Median valid obs | P10 valid obs |
|---|---:|---:|---:|---:|---:|
| Spring | 5 | 100.0% | 99.8% | 5.0 | 5.0 |
| Summer | 5 | 100.0% | 99.5% | 5.0 | 5.0 |
| Autumn | 5 | 100.0% | 100.0% | 5.0 | 5.0 |

## QA decision rule

The next stage should proceed only if the seasonal composites provide broad municipal coverage after pixel-level quality masking.

Particular attention should be paid to the spring composite because Stage 1 contained one scene close to the 20% scene-level cloud-search threshold.

## Important interpretation

Scene-level `eo:cloud_cover` was used only for discovery. Stage 2 uses the Sentinel-2 Scene Classification Layer to remove invalid pixels before compositing.

The seasonal median therefore represents the median of the remaining valid observations for each pixel, not the median of all raw scene values.

## Next stage

If Stage 2 passes QA, Stage 3 will derive NDVI, NDBI and NDWI and prepare the multi-season feature stack for machine learning.