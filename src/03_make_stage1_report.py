from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config.json"

inventory = pd.read_csv(OUT / "scene_inventory.csv")
selected = pd.read_csv(OUT / "selected_scenes.csv")
area = json.loads((OUT / "study_area_summary.json").read_text(encoding="utf-8"))
wc = json.loads((OUT / "worldcover_source_check.json").read_text(encoding="utf-8"))
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}

season_order = ["spring", "summer", "autumn"]
season_label = {"spring": "Spring", "summer": "Summer", "autumn": "Autumn"}
cloud_threshold = float(config.get("sentinel", {}).get("cloud_cover_max", 20))
min_aoi_coverage = float(config.get("sentinel", {}).get("minimum_aoi_coverage", 0.95))

selected = selected.copy()
selected["date"] = pd.to_datetime(selected["datetime"], errors="coerce")
selected["cloud_cover_pct"] = pd.to_numeric(selected["cloud_cover_pct"], errors="coerce")
selected["aoi_coverage_ratio"] = pd.to_numeric(selected["aoi_coverage_ratio"], errors="coerce")

# -----------------------------------------------------------------------------
# Figure 1: compact seasonal QA view.
# The purpose is not to reproduce every metadata field. It should let a reader
# see scene quality immediately and notice the few scenes that deserve QA.
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.4, 5.8))

for x_pos, season in enumerate(season_order):
    sdf = selected[selected["season"] == season].copy()
    if sdf.empty:
        continue

    sdf = sdf.sort_values(["cloud_cover_pct", "date"], na_position="last")
    if len(sdf) == 1:
        offsets = np.array([0.0])
    else:
        offsets = np.linspace(-0.13, 0.13, len(sdf))

    xs = x_pos + offsets
    ax.scatter(xs, sdf["cloud_cover_pct"], s=72, alpha=0.9, zorder=3)

    # Only annotate scenes that are genuine QA exceptions. This keeps the plot
    # readable while still surfacing the information that matters.
    for x, (_, row) in zip(xs, sdf.iterrows()):
        labels = []
        if pd.notna(row["cloud_cover_pct"]) and row["cloud_cover_pct"] >= 10:
            if pd.notna(row["date"]):
                labels.append(row["date"].strftime("%d %b"))
        if pd.notna(row["aoi_coverage_ratio"]) and row["aoi_coverage_ratio"] < 0.99:
            labels.append(f"{row['aoi_coverage_ratio'] * 100:.1f}% AOI")

        if labels:
            ax.annotate(
                "\n".join(labels),
                xy=(x, row["cloud_cover_pct"]),
                xytext=(6, 7),
                textcoords="offset points",
                fontsize=8.5,
                ha="left",
                va="bottom",
            )

ax.axhline(cloud_threshold, linestyle="--", linewidth=1.1, alpha=0.65, zorder=1)
ax.text(
    len(season_order) - 0.52,
    cloud_threshold + 0.35,
    f"Search threshold: {cloud_threshold:.0f}%",
    fontsize=8.5,
    ha="right",
    va="bottom",
    alpha=0.8,
)

ax.set_xticks(range(len(season_order)))
ax.set_xticklabels([season_label[s] for s in season_order])
ax.set_ylabel("Scene-level cloud cover (%)")
ax.set_title(
    "Cloud conditions of selected Sentinel-2 scenes",
    loc="left",
    fontsize=14,
    fontweight="bold",
    pad=14,
)

max_cloud = selected["cloud_cover_pct"].max(skipna=True)
if pd.isna(max_cloud):
    max_cloud = cloud_threshold
ax.set_ylim(0, max(cloud_threshold + 2.5, float(max_cloud) + 3.0))
ax.grid(axis="y", alpha=0.22, linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(
    0.01,
    0.012,
    "Each point represents one selected scene. Scene cloud cover is a discovery filter; AOI coverage is checked separately.",
    fontsize=8.5,
    alpha=0.75,
)
fig.subplots_adjust(left=0.10, right=0.98, top=0.87, bottom=0.13)
fig.savefig(OUT / "figure01_scene_cloud_cover.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# -----------------------------------------------------------------------------
# Stage 1 report: compact summary first; detailed scene metadata remains
# available, but is collapsed so the report reads like a QA document rather
# than a raw terminal dump.
# -----------------------------------------------------------------------------
lines = [
    "# Stage 1 Data Discovery Report",
    "",
    "> **Purpose.** Confirm study-area geometry, identify suitable Sentinel-2 observations, and verify the reference-label source before raster preprocessing or model training.",
    "",
    "![Cloud conditions of selected Sentinel-2 scenes](figure01_scene_cloud_cover.png)",
    "",
    "## QA at a glance",
    "",
    "| Check | Result |",
    "|---|---:|",
    f"| Augsburg municipal area | **{area['area_km2']:.2f} km²** |",
    f"| Sentinel-2 candidate scenes | **{len(inventory)}** |",
    f"| Selected scenes | **{len(selected)}** |",
    f"| Scene cloud-cover search threshold | **<{cloud_threshold:.0f}%** |",
    f"| Minimum target AOI coverage | **{min_aoi_coverage * 100:.0f}%** |",
    f"| WorldCover source check | **HTTP {wc['http_status']}** |",
    "",
    "## Seasonal scene summary",
    "",
    "| Season | Candidates | Selected | Cloud cover range | AOI coverage range |",
    "|---|---:|---:|---:|---:|",
]

for season in season_order:
    inv_s = inventory[inventory["season"] == season]
    sel_s = selected[selected["season"] == season]
    if sel_s.empty:
        cloud_range = "—"
        aoi_range = "—"
    else:
        cloud_range = f"{sel_s['cloud_cover_pct'].min():.1f}–{sel_s['cloud_cover_pct'].max():.1f}%"
        aoi_range = f"{sel_s['aoi_coverage_ratio'].min() * 100:.1f}–{sel_s['aoi_coverage_ratio'].max() * 100:.1f}%"
    lines.append(
        f"| {season_label[season]} | {len(inv_s)} | {len(sel_s)} | {cloud_range} | {aoi_range} |"
    )

lines += [
    "",
    "## Study area",
    "",
    f"- Boundary: OpenStreetMap relation **{area['osm_relation_id']}**.",
    f"- Municipal area: **{area['area_km2']:.2f} km²**.",
    f"- CRS used for metric area and coverage checks: **{area['analysis_crs']}**.",
    "",
    "## Selected-scene details",
    "",
    "The main report keeps scene-level metadata collapsed. Expand a season when exact acquisition times, cloud-cover values, AOI coverage, or STAC item IDs are needed.",
    "",
]

for season in season_order:
    sdf = selected[selected["season"] == season].sort_values(["date", "cloud_cover_pct"])
    lines += [
        "<details>",
        f"<summary><strong>{season_label[season]}</strong> — {len(sdf)} selected scene(s)</summary>",
        "",
        "| Acquisition | Cloud cover | AOI coverage | STAC item |",
        "|---|---:|---:|---|",
    ]
    if sdf.empty:
        lines.append("| — | — | — | — |")
    else:
        for _, row in sdf.iterrows():
            acquisition = row["date"].strftime("%Y-%m-%d %H:%M UTC") if pd.notna(row["date"]) else str(row["datetime"])
            lines.append(
                f"| {acquisition} | {row['cloud_cover_pct']:.1f}% | "
                f"{row['aoi_coverage_ratio'] * 100:.1f}% | `{row['item_id']}` |"
            )
    lines += ["", "</details>", ""]

# Surface only the few items that need human attention.
qa_notes = []
low_cov = selected[selected["aoi_coverage_ratio"] < 0.99]
high_cloud = selected[selected["cloud_cover_pct"] >= 10]

if low_cov.empty:
    qa_notes.append("- All selected scenes provide at least 99% AOI coverage.")
else:
    qa_notes.append(
        f"- **Coverage check:** {len(low_cov)} selected scene(s) provide less than 99% AOI coverage; these should be inspected during compositing."
    )

if high_cloud.empty:
    qa_notes.append("- All selected scenes have scene-level cloud cover below 10%.")
else:
    qa_notes.append(
        f"- **Cloud check:** {len(high_cloud)} selected scene(s) have scene-level cloud cover of 10% or more. Pixel-level SCL masking remains necessary."
    )

lines += [
    "## QA notes",
    "",
    *qa_notes,
    "",
    "## Reference labels",
    "",
    f"- Product: **ESA WorldCover {wc['reference_year']} {wc['version']}**.",
    f"- Tile: **{wc['tile']}**.",
    f"- Source check: **HTTP {wc['http_status']}**.",
    "",
    "> **Important limitation:** WorldCover is a reproducible reference-label layer, not independent field truth. Agreement with WorldCover must not be presented as independent real-world classification accuracy.",
    "",
    "## Stage 1 decision",
    "",
    "Stage 1 is a data-quality gate. The selected scenes should be reviewed before classifier training.",
    "",
    "**Next step:** load the selected Sentinel-2 assets, apply Scene Classification Layer (SCL) masking, align bands to 10 m, and build seasonal composites.",
]

(OUT / "STAGE1_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
print("Created polished Stage 1 report and seasonal scene-quality figure.")
