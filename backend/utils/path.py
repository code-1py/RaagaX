from pathlib import Path
import sys

if getattr(sys, "frozen", False):
    BASE_DIR   = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", sys.executable)).resolve()
else:
    BASE_DIR   = Path(__file__).resolve().parent.parent.parent
    BUNDLE_DIR = BASE_DIR