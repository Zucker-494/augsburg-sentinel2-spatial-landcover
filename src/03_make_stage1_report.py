from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

inventory = pd.read_csv(OUT / "scene_inventory.csv")
selected = pd.read_csv(OUT / "selected_scenes.csv")
area = json.loads((OUT / "study_area_summary.json").read_text(encoding="utf-8"))
wc = json.loads((OUT / "worldcover_source_check.json").read_text(encoding="utf-8"))

# Figure: cloud cover of selected scenes.
plot_df = selected.copy()
plot_df["date"] = pd.to_datetime(plot_df["datetime"]).dt.date.astype(str)
plot_df["label"] = plot_df["season"] + "\n" + plot_df["date"]

fig, ax = plt.subplots(figsize=(10, 5.5))
x = range(len(plot_df))
ax.bar(x, plot_df["cloud_cover_pct"])
ax.set_xticks(list(x))
ax.set_xticklabels(plot_df["label"], rotation=45, ha="right")
ax.set_ylabel("Scene-level cloud cover (%)")
ax.set_title("Selected Sentinel-2 candidate scenes")
ax.set_ylim(bottom=0)
fig.tight_layout()
fig.savefig(OUT / "figure01_scene_cloud_cover.png", dpi=180)
plt.close(fig)

lines = [
    "# Stage 1 Data Discovery Report",
    "",
    "## Study area",
    "",
    f"- Augsburg municipal area: **{area['area_km2']:.2f} km²**",
    f"- Boundary source: OpenStreetMap relation **{area['osm_relation_id']}**",
    f"- Analysis CRS for area/coverage checks: **{area['analysis_crs']}**",
    "",
    "## Sentinel-2 search",
    "",
    f"- Candidate scenes found: **{len(inventory)}**",
    f"- Selected candidate scenes: **{len(selected)}**",
    "",
]

for season, sdf in selected.groupby("season"):
    lines += [
        f"### {season.capitalize()}",
        "",
    ]
    for _, row in sdf.sort_values("cloud_cover_pct").iterrows():
        lines.append(
            f"- {row['datetime']}: cloud **{row['cloud_cover_pct']:.1f}%**, "
            f"AOI coverage **{row['aoi_coverage_ratio']*100:.1f}%**, "
            f"item `{row['item_id']}`"
        )
    lines.append("")

lines += [
    "## WorldCover reference source",
    "",
    f"- HTTP source check: **{wc['http_status']}**",
    f"- Tile: **{wc['tile']}**",
    f"- Reference year/version: **{wc['reference_year']} {wc['version']}**",
    "",
    "## Interpretation",
    "",
    "Stage 1 is a QA gate. The selected scenes should be inspected before any classifier is trained.",
    "",
    "The WorldCover layer is used as a reproducible reference-label source, **not as independent field truth**.",
    "",
    "Next stage: load the selected Sentinel-2 assets, apply SCL quality masking, align all bands to 10 m, and build seasonal composites.",
]

(OUT / "STAGE1_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
print("Created Stage 1 report and scene-cloud-cover figure.")
