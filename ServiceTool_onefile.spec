# -*- mode: python ; coding: utf-8 -*-

# ServiceTool.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_all
import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

block_cipher = None

# SPECPATH is provided by PyInstaller when executing the spec.
# This avoids relying on __file__, which might not be set in the spec namespace.
project_root = Path(globals().get("SPECPATH", Path.cwd())).resolve()

# Entry point (adjust if your entry differs)
entry_script = project_root / "client" / "main.py"

# --- Collect PyQt6 (plugins, binaries, datas, hidden imports)
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all("PyQt6")

# --- (Optional) Collect pytef if it is importable in this venv / via pathex
# If pytef isn't importable, skip this collect_all and instead ensure pathex contains its root.
try:
    pytef_datas, pytef_binaries, pytef_hiddenimports = collect_all("pytef")
except Exception:
    pytef_datas, pytef_binaries, pytef_hiddenimports = [], [], []

# --- Your resource folders (equivalent to --add-data ...)
datas = [
    # Equivalent to: --add-data "client\resources\styles;resources\styles"
    (str(project_root / "client" / "resources" / "styles"), "resources/styles"),
    # Equivalent to: --add-data "client\resources\icons;resources\icons"
    (str(project_root / "client" / "resources" / "icons"),  "resources/icons"),
]

# Add collected package datas
datas += pyqt6_datas + pytef_datas

# Binaries and hidden imports
binaries = pyqt6_binaries + pytef_binaries
hiddenimports = pyqt6_hiddenimports + pytef_hiddenimports

a = Analysis(
    [str(entry_script)],
    pathex=[
        str(project_root),

        # --- Add extra module roots only if you need them (your earlier PYTHONPATH)
        r"C:\Workspace-Pytef-V02.01-modular\pytef",
        r"C:\Workspace-SV-Devel\SV-TestEnv\configs\pytef_01\V02_00\default",
        r"C:\Workspace-Pytef-Common\tool_ServiceTool\src\server",
        r"C:\Workspace-Pytef-Common\tool_ServiceTool\src\client",
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Strongly recommended to avoid mixed Qt bindings:
        "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets",
        # Noise:
        "tests", "test", "pytest", "__pycache__",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ServiceTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,        # keep False to reduce AV false positives
    console=False,    # GUI app (equivalent to --noconsole)
    icon=str(project_root / "client" / "resources" / "icons" / "service_tool.ico"),  # adjust if needed
)

# NOTE:
# Build as one-file using the CLI:
#   pyinstaller --clean --onefile ServiceTool.spec
#
# Build as one-folder (more AV-friendly):
#   pyinstaller --clean ServiceTool.spec
