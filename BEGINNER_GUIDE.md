# Beginner Guide: Remote Sensing and Machine Learning Basics

This file is written for readers with **no previous background in remote sensing or machine learning**.

Project04 uses Sentinel-2 satellite imagery to classify major land-cover types in Augsburg. Before looking at the code, it helps to understand what the main data, abbreviations, and formulas actually mean.

---

## 1. What is remote sensing?

**Remote sensing (RS)** means observing the Earth's surface without touching it directly.

Satellites carry sensors that measure how much electromagnetic energy is reflected from the ground. Different materials reflect energy differently.

For example:

- healthy vegetation reflects strongly in near-infrared wavelengths;
- water absorbs much of the near-infrared energy;
- buildings and bare soil often have different responses in short-wave infrared wavelengths.

This is why satellite images can be used to distinguish land-cover types.

---

## 2. A satellite image is not just a photograph

A normal photograph usually combines visible red, green, and blue light.

A multispectral satellite image contains several separate image layers called **bands**.

Each band records reflectance in a different wavelength range.

For the same ground location, one pixel may therefore contain several values:

```text
Blue   = 0.08
Green  = 0.10
Red    = 0.09
NIR    = 0.33
SWIR1  = 0.17
SWIR2  = 0.14
```

For a machine-learning model, this pixel can be represented as a feature vector:

```text
[B2, B3, B4, B8, B11, B12]
```

The model then learns which combinations of values are typical of water, vegetation, built-up land, and other classes.

---

## 3. What is Sentinel-2?

**Sentinel-2** is an Earth-observation satellite mission operated as part of the European Copernicus programme.

It provides multispectral imagery that is widely used for land-cover mapping, vegetation monitoring, water detection, urban analysis, and agricultural analysis.

Project04 uses **Sentinel-2 Level-2A** data.

Level-2A products contain surface reflectance values that have already undergone atmospheric correction. This makes them suitable for land-surface analysis without requiring us to perform atmospheric correction from scratch.

---

## 4. Important Sentinel-2 bands in Project04

Project04 does not need all Sentinel-2 bands.

The main bands are:

| Band | Meaning | Typical resolution | Why it matters |
|---|---|---:|---|
| B2 | Blue | 10 m | visible blue light |
| B3 | Green | 10 m | visible green light |
| B4 | Red | 10 m | important for vegetation analysis |
| B8 | Near Infrared (NIR) | 10 m | strongly reflected by healthy vegetation |
| B11 | Short-Wave Infrared 1 (SWIR1) | 20 m | useful for soil, moisture and built-up surfaces |
| B12 | Short-Wave Infrared 2 (SWIR2) | 20 m | useful for moisture and material differences |

The 20 m SWIR bands must be resampled before they can be stacked with the 10 m bands.

All input rasters used together must have the same:

```text
CRS
pixel size
spatial extent
number of rows
number of columns
```

This process is called **spatial alignment**.

---

## 5. NIR

**NIR = Near Infrared**

Near-infrared light is outside the visible range of the human eye.

Healthy vegetation usually reflects a large amount of NIR energy.

A simplified vegetation pattern is therefore:

```text
Red reflectance: relatively low
NIR reflectance: relatively high
```

This difference is the basis of NDVI.

---

## 6. SWIR

**SWIR = Short-Wave Infrared**

Sentinel-2 B11 and B12 are SWIR bands.

SWIR information is useful because it can respond differently to built-up surfaces, soil, vegetation moisture, dry vegetation, and other surface materials.

SWIR is therefore useful when trying to separate built-up land, vegetation, and bare surfaces.

---

## 7. NDVI

**NDVI = Normalized Difference Vegetation Index**

NDVI is one of the most widely used vegetation indices.

For Sentinel-2:

```text
NDVI = (B8 - B4) / (B8 + B4)
```

where:

```text
B8 = Near Infrared
B4 = Red
```

Example:

```text
Red = 0.10
NIR = 0.50
```

Then:

```text
NDVI = (0.50 - 0.10) / (0.50 + 0.10)
     = 0.67
```

A relatively high positive NDVI often indicates vegetation.

However, NDVI is **not a complete land-cover classifier**. It is only one feature that helps describe the spectral behaviour of a pixel.

---

## 8. NDBI

**NDBI = Normalized Difference Built-up Index**

NDBI is commonly used to highlight built-up surfaces.

A common Sentinel-2 form is:

```text
NDBI = (B11 - B8) / (B11 + B8)
```

where:

```text
B11 = SWIR1
B8  = Near Infrared
```

NDBI can help identify urban and built-up areas, but it may also respond to bare soil.

For this reason, Project04 does not use NDBI alone. It is used together with the original spectral bands and other indices.

---

## 9. NDWI

**NDWI = Normalized Difference Water Index**

Several indices are called NDWI in remote-sensing literature.

For Project04, when NDWI is used for water detection, it refers to the Green-NIR form:

```text
NDWI = (B3 - B8) / (B3 + B8)
```

where:

```text
B3 = Green
B8 = Near Infrared
```

Water often absorbs near-infrared energy strongly, which helps this index distinguish water from many land surfaces.

---

## 10. What is a spectral index?

A **spectral index** combines two or more bands into a new numerical feature.

For example:

```text
Original bands:
B3, B4, B8, B11

Derived features:
NDVI, NDBI, NDWI
```

These indices do not create new observations. Instead, they reorganize existing spectral information in a way that may make certain surface properties easier to distinguish.

In machine learning, this is a form of **feature engineering**.

---

## 11. What is a pixel?

A **pixel** is the smallest raster cell in an image.

For a 10 m Sentinel-2 band, one pixel represents approximately a:

```text
10 m × 10 m
```

area on the ground.

Each pixel contains one numerical value for each band.

Therefore, one location can have a feature vector such as:

```text
[B2, B3, B4, B8, B11, B12, NDVI, NDBI, NDWI]
```

This feature vector becomes the input to the machine-learning model.

---

## 12. CRS

**CRS = Coordinate Reference System**

A CRS defines how geographic locations are represented on a map.

It tells GIS software where a raster or vector feature belongs on the Earth.

If two datasets use different CRS definitions or are spatially misaligned, their pixels and features may not refer to the same physical locations.

Project04 therefore checks that all raster layers are spatially aligned before classification.

---

## 13. GeoTIFF

**GeoTIFF = Geographic Tagged Image File Format**

A normal TIFF stores image pixels.

A GeoTIFF also contains geographic information such as coordinate reference system, pixel size, spatial extent, and geographic position.

Files such as these can therefore be placed correctly on a map:

```text
B4_10m.tif
NDVI.tif
classification.tif
```

GeoTIFF is one of the most common raster formats in GIS and remote sensing.

---

## 14. SAFE

**SAFE = Standard Archive Format for Europe**

Sentinel products are commonly distributed in a directory structure ending in:

```text
.SAFE
```

A SAFE product is not one single image.

It is a folder containing metadata, image bands, quality information, product information, and supporting files.

A Sentinel-2 product may therefore look complicated at first because several files belong to the same satellite observation.

Project04 only extracts the files needed for the analysis.

---

## 15. ML

**ML = Machine Learning**

Machine learning is a way of building models that learn patterns from examples.

In Project04, each training pixel has:

1. a set of input features;
2. a known land-cover class.

Example:

```text
Features:
B2, B3, B4, B8, B11, B12, NDVI, NDBI, NDWI

Known class:
Vegetation
```

After learning from many labelled examples, the model predicts the class of pixels it has not seen before.

---

## 16. RF

**RF = Random Forest**

Random Forest is the main classification algorithm used in Project04.

A Random Forest contains many decision trees. Each tree makes a classification decision, and the forest combines their results.

A simplified idea is:

```text
Pixel features
      ↓
many decision trees
      ↓
combined vote
      ↓
predicted land-cover class
```

Random Forest is useful for this project because it works well with nonlinear relationships, handles many input features, is widely used in remote sensing, can estimate feature importance, and does not require the input data to follow a normal distribution.

---

## 17. Land cover versus land use

These terms are related but not identical.

**Land cover** describes what is physically present on the surface.

Examples:

```text
water
vegetation
built-up surface
grassland
cropland
```

**Land use** describes how people use the land.

Examples:

```text
residential
industrial
commercial
recreational
```

Project04 focuses on **land cover**, because Sentinel-2 mainly observes physical surface properties.

---

## 18. Accuracy

Classification accuracy asks:

> How often did the model predict the correct class?

Overall accuracy is useful, but it can hide poor performance in small classes.

For example, a model may achieve high overall accuracy while still performing badly on water if water represents only a small part of the dataset.

This is why Project04 also uses class-based metrics.

---

## 19. Precision

**Precision** asks:

> Of all pixels predicted as a certain class, how many were actually that class?

For example:

> Of all pixels predicted as water, how many were really water?

---

## 20. Recall

**Recall** asks:

> Of all real pixels belonging to a class, how many did the model successfully identify?

For example:

> Of all actual water pixels, how many were detected as water?

---

## 21. F1 score

**F1 score** combines precision and recall.

Its formula is:

```text
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

A high F1 score means the classifier is performing well in both directions: it is not producing too many false positives, and it is not missing too many true examples.

Project04 uses F1 because it is more informative than overall accuracy alone when class sizes differ.

---

## 22. Confusion matrix

A **confusion matrix** compares predicted classes with known reference classes.

A simple example:

| Reference / Predicted | Built-up | Vegetation | Water |
|---|---:|---:|---:|
| Built-up | 90 | 8 | 2 |
| Vegetation | 7 | 91 | 2 |
| Water | 1 | 2 | 97 |

Values on the diagonal represent correct predictions.

Values outside the diagonal show which classes are being confused with each other.

This makes the confusion matrix one of the most useful diagnostic tools in classification.

---

## 23. Feature importance

Random Forest can estimate how useful different input variables are for classification.

For example, the model may show that:

```text
B8
NDVI
B11
NDBI
```

contribute more strongly than some visible bands.

Feature importance does not automatically prove a causal relationship. It is mainly a diagnostic showing which variables were most useful to the fitted model.

---

## 24. Project04 model comparison

Project04 compares two feature sets.

### Model A: original spectral bands

```text
B2
B3
B4
B8
B11
B12
```

### Model B: bands plus spectral indices

```text
B2
B3
B4
B8
B11
B12
NDVI
NDBI
NDWI
```

The purpose is to ask:

> Do the engineered spectral indices improve land-cover classification beyond the original Sentinel-2 bands?

The models are compared using metrics such as:

```text
Overall accuracy
Macro F1
Confusion matrix
```

---

## 25. The most important idea to remember

A Sentinel-2 pixel is **not simply a colour**.

It is a set of measurements collected in different wavelength bands.

For example:

```text
Pixel
  ↓
B2, B3, B4, B8, B11, B12
  ↓
NDVI, NDBI, NDWI
  ↓
feature vector
  ↓
machine-learning model
  ↓
land-cover class
```

This is the core logic behind Project04.

---

## Glossary

| Abbreviation | Full name | Simple meaning |
|---|---|---|
| GIS | Geographic Information System | software and methods for spatial data |
| RS | Remote Sensing | observing the Earth's surface remotely |
| ML | Machine Learning | learning patterns from labelled examples |
| RF | Random Forest | tree-based machine-learning classifier |
| CRS | Coordinate Reference System | defines where spatial data belongs |
| NIR | Near Infrared | wavelength strongly reflected by healthy vegetation |
| SWIR | Short-Wave Infrared | useful for moisture, soil and built-up surfaces |
| NDVI | Normalized Difference Vegetation Index | vegetation-related spectral index |
| NDBI | Normalized Difference Built-up Index | built-up-related spectral index |
| NDWI | Normalized Difference Water Index | water-related spectral index |
| F1 | F1 Score | combines precision and recall |
| SAFE | Standard Archive Format for Europe | Sentinel product folder structure |
| GeoTIFF | Geographic Tagged Image File Format | georeferenced raster image format |

---

## Suggested reading order

If you are completely new to the topic, read these sections first:

1. What is remote sensing?
2. A satellite image is not just a photograph
3. Important Sentinel-2 bands
4. NIR and SWIR
5. NDVI, NDBI and NDWI
6. What is a pixel?
7. Random Forest
8. Accuracy, F1 and confusion matrix

After that, the Project04 workflow should be much easier to follow.

---

## 31. What is ESA WorldCover?

ESA WorldCover is a global land-cover product with 10 m spatial resolution.

Project04 uses the 2021 v200 product as a reproducible source of reference labels.

The selected Project04 classes are:

```text
10  Tree cover
30  Grassland
40  Cropland
50  Built-up
80  Permanent water
```

WorldCover is used to tell the machine-learning model which land-cover class is associated with selected training pixels.

---

## 32. Reference labels are not the same as ground truth

A **reference label** is the class value used as the target in model training or evaluation.

A true independent ground-truth dataset would ideally come from field observation, manually verified interpretation, or another source that is independent from the imagery used to build the model.

WorldCover is itself an Earth-observation product. It was produced using satellite data, including Sentinel observations.

Therefore Project04 must not say:

> The model achieved independent ground-truth accuracy of X%.

A more accurate interpretation is:

> The model reproduced the selected WorldCover reference classes with X% agreement under this validation design.

This distinction is important for scientifically responsible interpretation.

---

## 33. Class balance

**Class balance** describes how many training or reference observations belong to each class.

For example:

```text
Built-up: 100,000 pixels
Water:      5,000 pixels
```

If all pixels are used directly, a model may be dominated by the large class.

Project04 therefore creates a stratified modelling sample with a target number of pixels per class.

The original class proportions are still recorded separately.

---

## 34. Stratified sampling

**Stratified sampling** means sampling observations separately within predefined groups.

In Project04, the groups are land-cover classes.

A simplified example is:

```text
Tree cover      → 6,000 samples
Grassland       → 6,000 samples
Cropland        → 6,000 samples
Built-up        → 6,000 samples
Permanent water → 6,000 samples
```

This helps prevent the largest land-cover class from dominating model fitting.

---

## 35. Spatial blocks

Project04 assigns each sampled pixel to a 2 km spatial block.

The block ID records which part of Augsburg the sample belongs to.

Later, spatial validation can keep entire blocks together when separating training and testing data.

This is different from randomly splitting neighbouring pixels across both sets.

The block design is one of the main steps that makes Project04 a spatial machine-learning workflow rather than only a conventional image-classification exercise.

---

## 36. What is a training/test split?

A supervised machine-learning model should be evaluated using data that were not used to fit the model.

Project04 therefore divides the reference samples into:

```text
training data → used to fit the classifier
test data     → used to evaluate predictions
```

Stage 5 uses a conventional stratified random split.

The word **stratified** means that the land-cover classes are kept in approximately the same proportions in both subsets.

---

## 37. Why compare feature sets?

Project04 asks whether engineered spectral indices add useful predictive information beyond the original Sentinel-2 bands.

The two Stage 5 feature sets are:

```text
Bands only:
18 features = 6 bands × 3 seasons

Bands + indices:
27 features = 18 bands + 9 seasonal indices
```

If the 27-feature model performs better, the indices may be helping the classifier organise spectral information.

If performance barely changes, the original bands may already contain most of the useful information.

---

## 38. HistGradientBoosting

**HistGradientBoosting** is a tree-based machine-learning method.

Unlike Random Forest, which combines many independently grown trees, gradient boosting builds trees sequentially.

Each new tree focuses on patterns that earlier trees did not model well.

Project04 uses HistGradientBoosting as a second classifier so the results do not depend on only one machine-learning algorithm.

---

## 39. Permutation importance

Permutation importance asks:

> How much worse does the model become if one feature is randomly shuffled?

If shuffling a feature causes a large decrease in macro F1, that feature was useful to the fitted model.

If performance barely changes, the model may not depend strongly on that feature.

Permutation importance measures predictive usefulness within the fitted model. It does not prove that a feature has a causal effect on land cover.

# Stage 6 Beginner Guide Addition

## Spatial leakage

Spatial leakage happens when training and testing data are separated statistically but remain too close or too similar in space.

For example:

```text
same agricultural field:
pixel A → training
pixel B → testing
```

The model may appear to generalise well even though the test pixel is almost identical to data already seen during training.

## Cross-validation

Cross-validation repeats model evaluation across several train/test partitions.

In five-fold cross-validation:

```text
Fold 1 → test part 1
Fold 2 → test part 2
Fold 3 → test part 3
Fold 4 → test part 4
Fold 5 → test part 5
```

Every observation is used for testing once.

The project reports the mean performance and the variability across folds.

## StratifiedGroupKFold

Project04 uses `StratifiedGroupKFold` for spatial validation.

Two requirements are combined:

1. samples from the same 2 km spatial block stay together;
2. the class distribution is kept as balanced across folds as possible.

This makes the test data more spatially independent than a random pixel split.

## Validation gap

Project04 defines:

```text
validation gap =
random-validation macro F1
-
spatial-validation macro F1
```

A positive value means random validation reports better performance.

A large positive gap suggests that spatial dependence may have made the random test artificially easy.

## Mean and standard deviation

Five-fold results are reported as:

```text
mean ± standard deviation
```

The mean describes average performance across folds.

The standard deviation describes how much performance changes between different folds.

A model with slightly lower mean performance but much smaller fold-to-fold variation may sometimes be more spatially stable.

# Stage 7 Beginner Guide Addition

## Out-of-fold prediction

An **out-of-fold prediction** is made for an observation by a model that was not trained on that observation's validation fold.

In Project04 spatial validation, this means a sample is predicted by a model that did not train on the sample's own 2 km spatial block.

Out-of-fold predictions are therefore appropriate for inspecting validation errors and confidence.

## Confusion matrix

A confusion matrix shows which classes are confused with each other.

Rows represent reference classes and columns represent predicted classes.

The Stage 7 matrix is row-normalized, so each row adds to 100%.

This makes it easier to answer questions such as:

> What percentage of reference grassland pixels were predicted as cropland?

## Model confidence

For each pixel, HistGradientBoosting produces a probability-like score for each class.

Project04 defines confidence as:

```text
maximum predicted class probability
```

A value near 1 means one class strongly dominates the model's prediction.

A lower value means the model is less decisive.

These probabilities are not calibrated in Project04, so they should be interpreted as relative confidence rather than literal probabilities of correctness.

## Error map

The spatial error map plots reference samples that were predicted incorrectly during spatial cross-validation.

This helps answer:

> Are model errors scattered randomly, or do they cluster in certain parts of Augsburg?

A spatial pattern can reveal where land-cover classes or spectral conditions are harder for the fitted model.

## Spatially validated feature importance

Stage 5 calculated importance from a random test split.

Stage 7 recalculates permutation importance within the spatial validation folds.

This is more relevant to generalisation because each importance estimate is measured on spatially separated test data.
