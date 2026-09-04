from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

for script in [
    "12_run_spatial_validation.py",
    "13_make_stage6_outputs.py",
]:
    print(f"\n=== Running {script} ===")
    subprocess.run(
        [sys.executable, str(ROOT / "src" / script)],
        check=True,
        cwd=ROOT,
    )

print("\nStage 6 complete.")
