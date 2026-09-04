from pathlib import Path
import json
import math

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from pystac_client import Client
from shapely.geometry import shape
from shapely.ops import transform as shp_transform

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BOUNDARY = ROOT / "data" / "raw" / "augsburg_boundary.geojson"
OUT = ROOT / "outputs"
META = ROOT / "data" / "metadata"
OUT.mkdir(parents=True, exist_ok=True)
META.mkdir(parents=True, exist_ok=True)

if not BOUNDARY.exists():
    raise FileNotFoundError("Run 00_download_boundary.py first.")

aoi_gdf = gpd.read_file(BOUNDARY).to_crs(4326)
aoi_geom = aoi_gdf.geometry.unary_union

# Use a metric CRS for footprint-overlap calculations.
to_utm = Transformer.from_crs(4326, CONFIG["aoi"]["utm_epsg"], always_xy=True).transform
aoi_metric = shp_transform(to_utm, aoi_geom)
aoi_area = aoi_metric.area

client = Client.open(CONFIG["sentinel"]["stac_api"])
collection = CONFIG["sentinel"]["collection"]

records = []
raw_items = {}

for season, (start, end) in CONFIG["sentinel"]["seasons"].items():
    search = client.search(
        collections=[collection],
        intersects=aoi_geom.__geo_interface__,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": CONFIG["sentinel"]["cloud_cover_max"]}},
        max_items=CONFIG["sentinel"]["max_items_per_season"],
    )
    items = list(search.items())
    raw_items[season] = [item.to_dict() for item in items]

    if not items:
        print(f"WARNING: no items found for {season}.")
        continue

    for item in items:
        footprint = shape(item.geometry)
        footprint_metric = shp_transform(to_utm, footprint)
        coverage = footprint_metric.intersection(aoi_metric).area / aoi_area

        props = item.properties
        records.append({
            "season": season,
            "item_id": item.id,
            "datetime": props.get("datetime"),
            "platform": props.get("platform"),
            "cloud_cover_pct": props.get("eo:cloud_cover"),
            "aoi_coverage_ratio": coverage,
            "mgrs_tile": props.get("mgrs:tile"),
            "utm_zone": props.get("mgrs:utm_zone"),
            "latitude_band": props.get("mgrs:latitude_band"),
            "grid_square": props.get("mgrs:grid_square"),
        })

(META / "sentinel_search_items.json").write_text(
    json.dumps(raw_items), encoding="utf-8"
)

df = pd.DataFrame(records)
if df.empty:
    raise RuntimeError("No Sentinel-2 scenes found for any configured season.")

df["cloud_cover_pct"] = pd.to_numeric(df["cloud_cover_pct"], errors="coerce")
df["aoi_coverage_ratio"] = pd.to_numeric(df["aoi_coverage_ratio"], errors="coerce")

df = df.sort_values(
    ["season", "aoi_coverage_ratio", "cloud_cover_pct"],
    ascending=[True, False, True]
).reset_index(drop=True)

df.to_csv(OUT / "scene_inventory.csv", index=False)

selected_parts = []
n_keep = CONFIG["sentinel"]["selected_scenes_per_season"]
min_cov = CONFIG["sentinel"]["minimum_aoi_coverage"]

for season, sdf in df.groupby("season", sort=False):
    eligible = sdf[sdf["aoi_coverage_ratio"] >= min_cov].copy()
    if eligible.empty:
        # Fallback: keep the highest-coverage scenes so the issue is visible in QA.
        eligible = sdf.copy()

    eligible = eligible.sort_values(
        ["cloud_cover_pct", "aoi_coverage_ratio"],
        ascending=[True, False]
    ).head(n_keep)

    selected_parts.append(eligible)

selected = pd.concat(selected_parts, ignore_index=True)
selected.to_csv(OUT / "selected_scenes.csv", index=False)

print(f"Scene inventory: {len(df)} candidates")
for season, sdf in selected.groupby("season"):
    print(
        f"{season}: selected {len(sdf)} scene(s), "
        f"cloud {sdf['cloud_cover_pct'].min():.1f}–{sdf['cloud_cover_pct'].max():.1f}%, "
        f"coverage {sdf['aoi_coverage_ratio'].min():.3f}–{sdf['aoi_coverage_ratio'].max():.3f}"
    )
