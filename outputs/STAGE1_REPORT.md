# Stage 1 Data Discovery Report

## Study area

- Augsburg municipal area: **146.76 km²**
- Boundary source: OpenStreetMap relation **62407**
- Analysis CRS for area/coverage checks: **EPSG:32632**

## Sentinel-2 search

- Candidate scenes found: **51**
- Selected candidate scenes: **15**

### Autumn

- 2021-09-03T10:27:28.066000Z: cloud **0.3%**, AOI coverage **100.0%**, item `S2A_32UPU_20210903_2_L2A`
- 2021-09-03T10:27:28.066000Z: cloud **0.3%**, AOI coverage **100.0%**, item `S2A_32UPU_20210903_1_L2A`
- 2021-09-03T10:27:28.066000Z: cloud **0.3%**, AOI coverage **100.0%**, item `S2A_32UPU_20210903_0_L2A`
- 2021-09-08T10:27:23.531000Z: cloud **3.5%**, AOI coverage **100.0%**, item `S2B_32UPU_20210908_1_L2A`
- 2021-09-18T10:27:23.588000Z: cloud **3.8%**, AOI coverage **100.0%**, item `S2B_32UPU_20210918_0_L2A`

### Spring

- 2021-03-02T10:27:26.069000Z: cloud **3.3%**, AOI coverage **100.0%**, item `S2B_32UPU_20210302_1_L2A`
- 2021-05-31T10:27:27.915000Z: cloud **3.7%**, AOI coverage **100.0%**, item `S2B_32UPU_20210531_0_L2A`
- 2021-05-31T10:27:27.915000Z: cloud **4.7%**, AOI coverage **100.0%**, item `S2B_32UPU_20210531_1_L2A`
- 2021-03-02T10:27:26.069000Z: cloud **5.1%**, AOI coverage **100.0%**, item `S2B_32UPU_20210302_0_L2A`
- 2021-04-01T10:27:25.288000Z: cloud **19.5%**, AOI coverage **100.0%**, item `S2B_32UPU_20210401_0_L2A`

### Summer

- 2021-08-14T10:27:29.646000Z: cloud **0.1%**, AOI coverage **100.0%**, item `S2A_32UPU_20210814_1_L2A`
- 2021-08-14T10:27:29.646000Z: cloud **0.3%**, AOI coverage **100.0%**, item `S2A_32UPU_20210814_0_L2A`
- 2021-06-17T10:17:31.041000Z: cloud **0.4%**, AOI coverage **95.4%**, item `S2B_32UPU_20210617_0_L2A`
- 2021-07-30T10:27:28.855000Z: cloud **3.3%**, AOI coverage **100.0%**, item `S2B_32UPU_20210730_1_L2A`
- 2021-07-30T10:27:28.854000Z: cloud **3.4%**, AOI coverage **100.0%**, item `S2B_32UPU_20210730_0_L2A`

## WorldCover reference source

- HTTP source check: **206**
- Tile: **N48E009**
- Reference year/version: **2021 v200**

## Interpretation

Stage 1 is a QA gate. The selected scenes should be inspected before any classifier is trained.

The WorldCover layer is used as a reproducible reference-label source, **not as independent field truth**.

Next stage: load the selected Sentinel-2 assets, apply SCL quality masking, align all bands to 10 m, and build seasonal composites.