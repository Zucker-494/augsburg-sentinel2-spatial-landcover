from pathlib import Path
import json
import requests
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

RELATION_ID = 62407
URL = (
    "https://nominatim.openstreetmap.org/lookup"
    f"?osm_ids=R{RELATION_ID}&format=geojson&polygon_geojson=1"
)

headers = {
    "User-Agent": "project04-augsburg-sentinel2-spatial-landcover/1.0"
}

response = requests.get(URL, headers=headers, timeout=120)
response.raise_for_status()
geojson = response.json()

if not geojson.get("features"):
    raise RuntimeError("No geometry returned for Augsburg OSM relation 62407.")

boundary_path = RAW / "augsburg_boundary.geojson"
boundary_path.write_text(json.dumps(geojson), encoding="utf-8")

gdf = gpd.read_file(boundary_path)
if gdf.empty:
    raise RuntimeError("Downloaded boundary is empty.")

gdf_utm = gdf.to_crs(32632)
area_km2 = float(gdf_utm.geometry.area.sum() / 1_000_000)

summary = {
    "osm_relation_id": RELATION_ID,
    "name": "Augsburg",
    "source_crs": str(gdf.crs),
    "analysis_crs": "EPSG:32632",
    "area_km2": area_km2,
    "feature_count": int(len(gdf)),
}
(OUT / "study_area_summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)

print(f"Saved {boundary_path}")
print(f"Augsburg municipal area: {area_km2:.2f} km²")
