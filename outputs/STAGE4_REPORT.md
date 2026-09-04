# Stage 4 Reference Labels and Sampling Report

## Purpose

Stage 4 prepares a reproducible reference-label layer for supervised classification.

ESA WorldCover 2021 v200 is aligned to the same 10 m grid used by the 27-feature Sentinel-2 stack.

## Selected reference classes

| Code | Class | Pixels | Area (km²) | Share of jointly valid area |
|---:|---|---:|---:|---:|
| 10 | Tree cover | 584,159 | 58.42 | 39.80% |
| 30 | Grassland | 197,274 | 19.73 | 13.44% |
| 40 | Cropland | 258,933 | 25.89 | 17.64% |
| 50 | Built-up | 402,323 | 40.23 | 27.41% |
| 80 | Permanent water | 21,457 | 2.15 | 1.46% |

Together, the selected classes represent **99.76%** of pixels that are valid across all 27 Project04 features.

Pixels belonging to WorldCover classes outside this modelling set are retained in the QA tables but excluded from model sampling.

## Stratified reference sampling

Target sample size: **6,000 pixels per class**.

| Class | Samples | 2 km spatial blocks represented |
|---|---:|---:|
| Tree cover | 6,000 | 54 |
| Grassland | 6,000 | 53 |
| Cropland | 6,000 | 47 |
| Built-up | 6,000 | 43 |
| Permanent water | 6,000 | 31 |

Total reference samples: **30,000**

Each sample is assigned to a **2 km spatial block**. These block IDs will later be used to construct spatially separated validation rather than mixing neighbouring pixels randomly.

## Important limitation

WorldCover is a reproducible reference product, **not independent field ground truth**.

Project04 therefore measures how the classifiers reproduce this reference labelling scheme under different feature and validation designs. Agreement with WorldCover must not be interpreted as independent real-world mapping accuracy.

## Decision gate

Before model fitting, check:

- whether the five selected classes cover most of the valid Augsburg study area;
- whether every class has enough reference pixels;
- whether the reference samples are spatially distributed across multiple 2 km blocks;
- whether the reference map contains obvious alignment errors.

## Next stage

If Stage 4 passes QA, Stage 5 will extract the 27 Sentinel-2 features at these reference pixels and fit the first supervised classifiers.