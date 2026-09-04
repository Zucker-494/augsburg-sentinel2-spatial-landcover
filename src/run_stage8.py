from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "src" / "16_make_final_outputs.py")], check=True, cwd=ROOT)
print("Stage 8 complete.")
