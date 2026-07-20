import sys
import subprocess
from pathlib import Path

def get_active_python():
    return sys.executable

def export_dependencies(output_file="requirements.txt"):
    python_exe = get_active_python()

    result = subprocess.run(
        [python_exe, "-m", "pip", "freeze"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"pip freeze failed:\n{result.stderr}")

    Path(output_file).write_text(result.stdout, encoding="utf-8")
    return output_file

if __name__ == "__main__":
    out = export_dependencies()
    print(f"✅ Dependencies exported to {out}")
    print(f"🐍 Python used: {sys.executable}")
    print(f"📦 Total packages: {len(open(out).readlines())}")