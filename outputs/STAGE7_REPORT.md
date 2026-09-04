# Stage 7 Interpretation and Uncertainty Report

## Selected configuration

- Model: **HistGradientBoosting**
- Feature set: **bands + indices (27 features)**
- Selection basis: best mean macro F1 under 5-fold spatial validation

## Why Stage 7 uses out-of-fold predictions

Class-specific errors and confidence summaries are calculated from spatial out-of-fold predictions. Each reference sample is therefore predicted by a model that was not trained on its own 2 km spatial block.

## Class-level confidence and accuracy

| Class | Spatial OOF accuracy | Median confidence | P10 confidence | Confidence < 0.60 |
|---|---:|---:|---:|---:|
| Tree cover | 0.834 | 0.991 | 0.595 | 10.3% |
| Grassland | 0.825 | 0.923 | 0.553 | 13.6% |
| Cropland | 0.870 | 0.987 | 0.640 | 8.3% |
| Built-up | 0.919 | 0.963 | 0.620 | 9.1% |
| Permanent water | 0.978 | 1.000 | 0.981 | 1.2% |

## Most useful features under spatial validation

| Feature | Mean permutation importance | Between-fold SD |
|---|---:|---:|
| summer_swir22 | 0.0822 | 0.0103 |
| spring_swir16 | 0.0752 | 0.0085 |
| autumn_swir16 | 0.0541 | 0.0099 |
| spring_ndwi | 0.0461 | 0.0132 |
| autumn_ndvi | 0.0341 | 0.0101 |
| spring_swir22 | 0.0297 | 0.0073 |
| autumn_swir22 | 0.0238 | 0.0057 |
| summer_swir16 | 0.0194 | 0.0033 |
| spring_nir | 0.0142 | 0.0049 |
| spring_ndvi | 0.0118 | 0.0060 |

## Interpretation

The class-level results should be read together with the spatial confusion matrix and error map.

Classes with lower F1 or confidence are more spectrally ambiguous under this reference scheme. In particular, grassland can overlap spectrally with cropland and other vegetated surfaces, especially when seasonal states are similar.

The feature-importance ranking is calculated within spatial validation rather than only from a random split. This makes it more relevant to the model's spatial generalisation behaviour.

## Confidence map

The full Augsburg confidence raster is produced by a final HistGradientBoosting model fitted to all 30,000 reference samples after the model-selection stage.

The displayed value is the maximum predicted class probability. HistGradientBoosting probabilities are not calibrated here, so the map should be interpreted as **relative model confidence**, not a literal probability that a pixel is correct.

## Important limitation

All performance and uncertainty interpretation remains conditional on ESA WorldCover as the reference-label source. The project does not claim independent field-validated land-cover accuracy.

## Next stage

Stage 8 will assemble the final classification map, confidence map, core validation figures, documentation and interactive presentation into the finished Project04 portfolio.