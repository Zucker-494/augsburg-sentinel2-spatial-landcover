from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

scripts = [
    "10_train_random_validation_models.py",
    "11_make_stage5_outputs.py",
]

for script in scripts:
    print(f"\n=== Running {script} ===")
    subprocess.run(
        [sys.executable, str(ROOT / "src" / script)],
        check=True,
        cwd=ROOT,
    )

print("\nStage 5 complete.")
