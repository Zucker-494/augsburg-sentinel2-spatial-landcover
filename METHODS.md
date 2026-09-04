# Methods

## Project purpose

Project04 is designed as a progression from vector and network GIS toward raster GIS, remote sensing, and spatial machine learning.

The project deliberately separates **data discovery and quality assurance** from model fitting. Classification is not started until the input imagery, spatial coverage, cloud conditions, and reference-label source have been checked.

## Stage 1: study area

The Augsburg municipal boundary is retrieved from OpenStreetMap relation 62407 and saved as GeoJSON.

Area calculations are performed in UTM Zone 32N (EPSG:32632).

## Stage 1: Sentinel-2 search

Sentinel-2 Level-2A items are searched through the public Earth Search STAC API.

Initial temporal windows:

- spring: March–May 2021;
- summer: June–August 2021;
- autumn: September–November 2021.

Candidate scenes are filtered by metadata cloud cover and ranked using:

1. proportion of the Augsburg municipal polygon covered by the STAC item footprint;
2. reported `eo:cloud_cover`.

The initial target is to retain up to five high-coverage, low-cloud scenes per season. These scenes will later support seasonal median composites.

Scene-level cloud-cover metadata is used only for discovery. Pixel-level cloud, cloud-shadow, and quality masking will be performed later using the Sentinel-2 Scene Classification Layer (SCL).

## Reference labels

The first workflow uses ESA WorldCover 2021 v200.

WorldCover is a 10 m global land-cover product and is used here because it provides a reproducible reference layer aligned to the same reference year.

However, WorldCover is not independent field truth. It was itself derived from Earth-observation data, including Sentinel observations. Therefore:

- reported agreement with WorldCover must not be interpreted as independent ground-truth accuracy;
- the project evaluates model behaviour relative to the reference product;
- spatial validation addresses spatial leakage but does not remove reference-label dependence;
- independent validation is a possible later extension.

## Planned feature sets

### Model feature set A: spectral bands

- B2 Blue
- B3 Green
- B4 Red
- B8 NIR
- B11 SWIR1
- B12 SWIR2

### Model feature set B: bands plus indices

Feature set A plus:

- NDVI
- NDBI
- NDWI

## Planned validation comparison

### Random validation

Pixels are randomly divided into training and test subsets.

### Spatial validation

Pixels are grouped into spatial blocks. Whole blocks are assigned to training or testing so neighbouring pixels are less likely to appear in both sets.

The comparison is intended to show how spatial autocorrelation can affect reported classification performance.

## Planned model comparison

- Random Forest
- HistGradientBoosting

The purpose is not to find a universally best classifier. The purpose is to compare model behaviour while holding the input data and validation design constant.

## Planned evaluation

- overall accuracy;
- macro F1;
- class-level precision, recall and F1;
- confusion matrix;
- random versus spatial validation gap;
- prediction confidence;
- feature importance / permutation importance where appropriate.

## Planned uncertainty output

The final classification will be accompanied by a confidence or uncertainty layer derived from class probabilities.

The uncertainty map is intended to identify locations where the model's final class label is weakly supported.

## Data-source references

- Copernicus Sentinel-2 Level-2A product documentation
- Element 84 Earth Search STAC API
- ESA WorldCover 2021 v200

Source access URLs are recorded in `config.json`.
