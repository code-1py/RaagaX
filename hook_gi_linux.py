import os
import sys

# When running as a frozen PyInstaller binary on Linux,
# gi (PyGObject) needs to find the system typelib files.
# Point GI_TYPELIB_PATH at the standard system locations.
if getattr(sys, "frozen", False) and sys.platform.startswith("linux"):
    typelib_paths = [
        "/usr/lib/x86_64-linux-gnu/girepository-1.0",
        "/usr/lib/girepository-1.0",
        "/usr/local/lib/girepository-1.0",
    ]
    existing = [p for p in typelib_paths if os.path.isdir(p)]
    if existing:
        current = os.environ.get("GI_TYPELIB_PATH", "")
        merged  = ":".join(filter(None, existing + [current]))
        os.environ["GI_TYPELIB_PATH"] = merged