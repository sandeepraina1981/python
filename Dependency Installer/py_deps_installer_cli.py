import sys
import argparse
import subprocess
from pathlib import Path

def install(req_file):
    python_exe = sys.executable
    if not Path(req_file).exists():
        raise FileNotFoundError(req_file)

    subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python_exe, "-m", "pip", "install", "-r", req_file])

def main():
    parser = argparse.ArgumentParser(description="Python Dependency Installer")
    parser.add_argument(
        "-r", "--requirements",
        default="requirements.txt",
        help="Path to requirements file"
    )
    args = parser.parse_args()

    install(args.requirements)

if __name__ == "__main__":
    main()