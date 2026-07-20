import subprocess
import sys
import time
from pathlib import Path

REQUIREMENTS_FILE = "requirements.txt"


def find_pythons():
    """Find Python executables using `where python` (Windows only)."""
    try:
        output = subprocess.check_output(
            ["where", "python"],
            text=True,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return []

    candidates = []
    for line in output.splitlines():
        p = line.strip()
        if (
                p.lower().endswith("python.exe")
                and "windowsapps" not in p.lower()
        ):
            candidates.append(p)

    return list(dict.fromkeys(candidates))  # dedupe


def is_working_python(python_exe):
    """Check if python executable actually runs."""
    try:
        subprocess.check_output(
            [python_exe, "-c", "import sys; print(sys.version)"],
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return True
    except Exception:
        return False


def select_python(pythons):
    print("\nAvailable Python installations:\n")
    for idx, p in enumerate(pythons, 1):
        print(f"[{idx}] {p}")

    while True:
        choice = input("\nSelect Python to install dependencies into: ")
        if choice.isdigit() and 1 <= int(choice) <= len(pythons):
            return pythons[int(choice) - 1]
        print("❌ Invalid selection, try again.")


def parse_requirements():
    if not Path(REQUIREMENTS_FILE).exists():
        raise FileNotFoundError(REQUIREMENTS_FILE)

    reqs = []
    for line in Path(REQUIREMENTS_FILE).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            reqs.append(line)
    return reqs


def get_missing_packages(python_exe, requirements):
    missing = []

    for req in requirements:
        pkg = req.split("==")[0]
        try:
            subprocess.check_output(
                [python_exe, "-c", f"import {pkg.replace('-', '_')}"],
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            missing.append(req)

    return missing


def install_packages(python_exe, packages):
    subprocess.check_call(
        [python_exe, "-m", "pip", "install", *packages]
    )


def main():
    print("🔍 Discovering Python installations...")

    pythons = [
        p for p in find_pythons()
        if is_working_python(p)
    ]

    if not pythons:
        print("❌ No usable Python installations found.")
        sys.exit(1)

    python_exe = select_python(pythons)
    print(f"\n🐍 Selected Python:\n{python_exe}")

    requirements = parse_requirements()
    missing = get_missing_packages(python_exe, requirements)

    if not missing:
        print("\n✅ All dependencies are already installed.")
        return

    print("\n📦 Missing dependencies:")
    for m in missing:
        print(f"  - {m}")

    print("\n⬇ Installing missing dependencies...")
    install_packages(python_exe, missing)

    print("\n✅ Dependency installation complete.")
    time.sleep(5)


if __name__ == "__main__":
    main()