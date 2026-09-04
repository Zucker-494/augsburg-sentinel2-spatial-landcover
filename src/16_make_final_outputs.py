from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import pandas as pd
import rasterio
from rasterio.plot import plotting_extent
from rasterio.warp import transform_bounds

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
BOUNDARY = ROOT / "data" / "raw" / "augsburg_boundary.geojson"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

CLASS_INFO = [
    (10, "Tree cover", "#2E7D32"),
    (30, "Grassland", "#A8C96F"),
    (40, "Cropland", "#D8B365"),
    (50, "Built-up", "#C45A52"),
    (80, "Permanent water", "#4C78A8"),
]


def read_classification():
    path = PROCESSED / "final_hgb_classification.tif"
    with rasterio.open(path) as src:
        arr = src.read(1)
        extent = plotting_extent(src)
        crs = src.crs
        bounds_wgs84 = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)
    return arr, extent, crs, bounds_wgs84


def read_confidence():
    path = PROCESSED / "final_hgb_confidence.tif"
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        extent = plotting_extent(src)
        crs = src.crs
        bounds_wgs84 = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)
    return arr, extent, crs, bounds_wgs84


def make_final_classification_map():
    arr, extent, crs, _ = read_classification()
    boundary = gpd.read_file(BOUNDARY).to_crs(crs)

    display = np.full(arr.shape, np.nan, dtype="float32")
    colors = [c for _, _, c in CLASS_INFO]
    for idx, (code, _, _) in enumerate(CLASS_INFO, start=1):
        display[arr == code] = idx

    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(0.5, len(CLASS_INFO) + 1.5), cmap.N)

    fig, ax = plt.subplots(figsize=(7.6, 7.6))
    ax.imshow(display, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
    boundary.boundary.plot(ax=ax, linewidth=0.8)

    handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", markerfacecolor=color,
                   markeredgecolor="none", markersize=8, label=name)
        for _, name, color in CLASS_INFO
    ]
    ax.legend(handles=handles, title="Predicted class", frameon=False,
              loc="lower left", fontsize=8.5, title_fontsize=9)
    ax.set_title("Final Project04 land-cover classification", loc="left",
                 fontsize=13, fontweight="semibold", pad=10)
    ax.text(0.0, -0.055,
            "HistGradientBoosting using 27 multi-season Sentinel-2 features; selected by 5-fold spatial validation.",
            transform=ax.transAxes, fontsize=8.5, va="top")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT / "figure17_final_landcover_classification.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_project_summary_table():
    stage6 = pd.read_csv(OUT / "stage6_validation_summary.csv")
    best = (stage6[stage6["validation"] == "spatial_5fold"]
            .sort_values(["mean_macro_f1", "mean_accuracy"], ascending=False).iloc[0])
    rows = [
        ("Study area", "Augsburg municipality"),
        ("Sentinel-2 scenes", "15 selected scenes"),
        ("Temporal design", "Spring / Summer / Autumn 2021"),
        ("Feature stack", "27 features"),
        ("Reference samples", "30,000"),
        ("Spatial block size", "2 km"),
        ("Selected model", str(best["model"])),
        ("Selected feature set", str(best["feature_set"])),
        ("Spatial macro F1", f"{best['mean_macro_f1']:.3f} ± {best['sd_macro_f1']:.3f}"),
    ]
    pd.DataFrame(rows, columns=["item", "value"]).to_csv(OUT / "FINAL_PROJECT_SUMMARY.csv", index=False)


def rgba_classification(arr):
    rgba = np.zeros((*arr.shape, 4), dtype=np.uint8)
    for code, _, hex_color in CLASS_INFO:
        rgb = tuple(int(hex_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        mask = arr == code
        rgba[mask, 0] = rgb[0]
        rgba[mask, 1] = rgb[1]
        rgba[mask, 2] = rgb[2]
        rgba[mask, 3] = 205
    return rgba


def rgba_confidence(arr):
    cmap = plt.get_cmap("viridis")
    normed = np.clip((arr - 0.5) / 0.5, 0, 1)
    rgba = (cmap(normed) * 255).astype(np.uint8)
    rgba[~np.isfinite(arr), 3] = 0
    rgba[np.isfinite(arr), 3] = 190
    return rgba


def make_web_assets():
    class_arr, _, _, class_bounds = read_classification()
    conf_arr, _, _, _ = read_confidence()
    plt.imsave(ASSETS / "classification_overlay.png", rgba_classification(class_arr))
    plt.imsave(ASSETS / "confidence_overlay.png", rgba_confidence(conf_arr))
    gpd.read_file(BOUNDARY).to_crs(4326).to_file(ASSETS / "augsburg_boundary.geojson", driver="GeoJSON")
    return class_bounds


def make_index_html(class_bounds):
    left, bottom, right, top = class_bounds
    legend_html = "".join(
        f'<div><span style="display:inline-block;width:12px;height:12px;background:{color};margin-right:6px;"></span>{name}</div>'
        for _, name, color in CLASS_INFO
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Project04 - Augsburg Sentinel-2 Land Cover</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
html, body {{ height: 100%; margin: 0; font-family: Arial, sans-serif; }}
#map {{ height: 100%; }}
.info {{ background: rgba(255,255,255,0.94); padding: 10px 12px; line-height: 1.4; box-shadow: 0 1px 5px rgba(0,0,0,0.25); border-radius: 4px; max-width: 320px; }}
.legend {{ font-size: 13px; }}
.title {{ font-size: 15px; font-weight: 700; margin-bottom: 6px; }}
.note {{ font-size: 11px; color: #444; margin-top: 6px; }}
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map');
const bounds = [[{bottom}, {left}], [{top}, {right}]];
const osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}}).addTo(map);
const classification = L.imageOverlay('assets/classification_overlay.png', bounds, {{opacity: 0.78}}).addTo(map);
const confidence = L.imageOverlay('assets/confidence_overlay.png', bounds, {{opacity: 0.70}});
fetch('assets/augsburg_boundary.geojson').then(r => r.json()).then(data => {{
  const boundary = L.geoJSON(data, {{style: {{color: '#333333', weight: 1.5, fillOpacity: 0}}}}).addTo(map);
  L.control.layers({{'OpenStreetMap': osm}}, {{'Land-cover classification': classification, 'Model confidence': confidence, 'Augsburg boundary': boundary}}, {{collapsed: false}}).addTo(map);
}});
map.fitBounds(bounds);
const info = L.control({{position: 'bottomleft'}});
info.onAdd = function() {{
  const div = L.DomUtil.create('div', 'info legend');
  div.innerHTML = `<div class="title">Project04 - Augsburg land cover</div>{legend_html}<div class="note">Sentinel-2 2021 multi-season features; HistGradientBoosting selected by 5-fold spatial validation. Confidence is relative model confidence, not calibrated probability of correctness.</div>`;
  return div;
}};
info.addTo(map);
</script>
</body>
</html>"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")


def write_final_report():
    s6 = pd.read_csv(OUT / "stage6_validation_summary.csv")
    gap = pd.read_csv(OUT / "stage6_validation_gap.csv")
    conf = pd.read_csv(OUT / "stage7_class_confidence_summary.csv")
    imp = pd.read_csv(OUT / "stage7_spatial_permutation_importance_summary.csv").head(8)
    best = (s6[s6["validation"] == "spatial_5fold"]
            .sort_values(["mean_macro_f1", "mean_accuracy"], ascending=False).iloc[0])
    best_gap = gap[(gap["model"] == best["model"]) & (gap["feature_set"] == best["feature_set"])].iloc[0]

    lines = [
        "# Project04 Final Report", "", "## Project title", "",
        "**Augsburg Sentinel-2 Spatial Land-Cover Classification**", "",
        "## Research question", "",
        "How well can multi-season Sentinel-2 imagery reproduce major land-cover patterns in Augsburg, and how do feature engineering and spatial validation change apparent model performance?", "",
        "## Key results", "",
        f"- Best spatially validated model: **{best['model']} / {best['feature_set']}**",
        f"- Spatial macro F1: **{best['mean_macro_f1']:.3f} ± {best['sd_macro_f1']:.3f}**",
        f"- Matched random 5-fold macro F1: **{best_gap['random_mean_macro_f1']:.3f} ± {best_gap['random_sd_macro_f1']:.3f}**",
        f"- Random-minus-spatial gap: **{100*best_gap['macro_f1_gap']:.2f} percentage points**", "",
        "Random pixel validation is mildly optimistic rather than dramatically misleading under the 2 km block design used here.", "",
        "## Class-specific interpretation", "",
        "| Class | Spatial OOF accuracy | Median confidence | Confidence < 0.60 |",
        "|---|---:|---:|---:|",
    ]
    for _, row in conf.iterrows():
        lines.append(f"| {row['class_name']} | {row['accuracy']:.3f} | {row['median_confidence']:.3f} | {row['low_confidence_below_0_60_pct']:.1f}% |")
    lines += ["", "Permanent water is the most stable class. Grassland is the most difficult, consistent with spectral overlap among grassland, cropland and other vegetated surfaces.", "", "## Most useful spatially validated features", "", "| Feature | Mean permutation importance |", "|---|---:|"]
    for _, row in imp.iterrows():
        lines.append(f"| {row['feature']} | {row['mean_importance']:.4f} |")
    lines += [
        "", "SWIR features remain dominant after moving from random to spatial validation. Spectral indices add useful information but do not replace the predictive value of the original bands.", "",
        "## What makes this more than a basic classification demo", "",
        "- multi-season rather than single-scene input;", "- explicit cloud and quality QA;", "- bands-only versus bands-plus-indices comparison;", "- two machine-learning models;", "- matched random and spatial five-fold validation;", "- spatially validated feature importance;", "- out-of-fold error mapping;", "- relative confidence mapping;", "- reproducible GitHub Actions workflow;", "- interactive final map.", "",
        "## Limitations", "",
        "1. ESA WorldCover is a reproducible reference-label product, not independent field ground truth.",
        "2. Spatial validation uses a fixed 2 km block size; other scales could change the validation gap.",
        "3. HistGradientBoosting confidence values are not calibrated probabilities.",
        "4. The workflow uses selected 2021 observations and does not test temporal transfer to other years.",
        "5. The final classification reproduces the selected five-class reference scheme rather than providing a new operational land-cover product.", "",
        "## Final interpretation", "",
        "Project04 shows that a relatively simple tree-based remote-sensing classifier can achieve stable spatial performance when the data pipeline is carefully controlled. The stronger methodological contribution is the explicit comparison of random and spatial validation, together with uncertainty and class-specific error analysis."
    ]
    (OUT / "FINAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def write_readme():
    text = """# Augsburg Sentinel-2 Spatial Land-Cover Classification

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
- model-confidence overlay;
- Augsburg municipal boundary.

## Project status

**Complete / frozen after Stage 8 QA.**
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8")


def write_status():
    text = """# Project04 Status

## Final status

**Stage 8 generated — pending final visual QA.**

Completed stages:

- Stage 1: data discovery and scene QA
- Stage 2: raster preprocessing
- Stage 3: feature engineering
- Stage 4: reference labels and spatial sampling
- Stage 5: random-validation ML baseline
- Stage 6: spatial cross-validation
- Stage 7: interpretation and uncertainty
- Stage 8: final presentation and portfolio packaging

No model or analytical changes should be made after final Stage 8 QA unless a reproducibility or methodological defect is identified.
"""
    (ROOT / "PROJECT_STATUS.md").write_text(text, encoding="utf-8")


def main():
    make_final_classification_map()
    make_project_summary_table()
    class_bounds = make_web_assets()
    make_index_html(class_bounds)
    write_final_report()
    write_readme()
    write_status()
    print("Stage 8 final portfolio outputs created.")


if __name__ == "__main__":
    main()
