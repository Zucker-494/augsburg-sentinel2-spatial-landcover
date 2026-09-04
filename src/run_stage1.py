from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

scripts = [
    "00_download_boundary.py",
    "01_search_sentinel.py",
    "02_check_worldcover.py",
    "03_make_stage1_report.py",
]

for script in scripts:
    print(f"\n=== Running {script} ===")
    subprocess.run(
        [sys.executable, str(ROOT / "src" / script)],
        check=True,
        cwd=ROOT,
    )

print("\nStage 1 complete.")
