from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

scripts = [
    "08_prepare_reference_labels.py",
    "09_make_stage4_outputs.py",
]

for script in scripts:
    print(f"\n=== Running {script} ===")
    subprocess.run(
        [sys.executable, str(ROOT / "src" / script)],
        check=True,
        cwd=ROOT,
    )

print("\nStage 4 complete.")
