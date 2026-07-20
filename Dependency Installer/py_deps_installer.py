import sys
import subprocess
import time
from pathlib import Path

def install_dependencies(requirements_file="requirements.txt"):
    python_exe = subprocess.check_output(["python", "-c", "import sys; print(sys.executable)"], text=True).strip()

    req_path = Path(requirements_file)

    if not req_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")

    print(f"Using Python: {python_exe}")
    print(f"Installing dependencies from: {req_path}")

    command = [
        python_exe,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "pip"
    ]

    subprocess.check_call(command)

    install_cmd = [
        python_exe,
        "-m",
        "pip",
        "install",
        "-r",
        str(req_path)
    ]

    subprocess.check_call(install_cmd)

    print("Dependency installation completed successfully")

if __name__ == "__main__":
    try:
        install_dependencies()
        time.sleep(5)
    except Exception as e:
        print(f"Installation failed: {e}")
        sys.exit(1)