from pathlib import Path
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

url = CONFIG["worldcover"]["source_url"]

headers = {
    "Range": "bytes=0-1023",
    "User-Agent": "project04-augsburg-sentinel2-spatial-landcover/1.0",
}

response = requests.get(url, headers=headers, timeout=120)
ok = response.status_code in (200, 206)

result = {
    "source_url": url,
    "http_status": response.status_code,
    "range_request_ok": ok,
    "content_type": response.headers.get("Content-Type"),
    "content_range": response.headers.get("Content-Range"),
    "reference_year": CONFIG["worldcover"]["year"],
    "version": CONFIG["worldcover"]["version"],
    "tile": CONFIG["worldcover"]["tile"],
    "interpretation": CONFIG["worldcover"]["note"],
}

(OUT / "worldcover_source_check.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)

if not ok:
    raise RuntimeError(
        f"WorldCover source check failed with HTTP {response.status_code}: {url}"
    )

print("WorldCover reference source is reachable.")
