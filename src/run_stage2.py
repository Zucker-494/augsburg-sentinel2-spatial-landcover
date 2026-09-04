from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

scripts = [
    "04_build_seasonal_composites.py",
    "05_make_stage2_outputs.py",
]

for script in scripts:
    print(f"\n=== Running {script} ===")
    subprocess.run(
        [sys.executable, str(ROOT / "src" / script)],
        check=True,
        cwd=ROOT,
    )

print("\nStage 2 complete.")
