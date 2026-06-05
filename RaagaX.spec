# RaagaX.spec
# PyInstaller spec file — works for Windows, Mac, Linux
# Run with: pyinstaller RaagaX.spec

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ============================================================
#  Platform
# ============================================================

IS_WINDOWS = sys.platform == "win32"
IS_MAC     = sys.platform == "darwin"
IS_LINUX   = sys.platform.startswith("linux")

# ============================================================
#  Collect yt-dlp data files (extractors, etc.)
# ============================================================

yt_dlp_datas    = collect_data_files("yt_dlp")
yt_dlp_hiddens  = collect_submodules("yt_dlp")

# ============================================================
#  Collect pywebview data files
# ============================================================

webview_datas   = collect_data_files("webview")
webview_hiddens = collect_submodules("webview")

# ============================================================
#  Frontend files — copied NEXT TO exe, not inside _MEIPASS
#  We handle this via COLLECT below, not datas
# ============================================================

# ============================================================
#  Hidden imports — things PyInstaller misses
# ============================================================

hidden_imports = [
    # uvicorn internals
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.loops.uvloop",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.off",
    "uvicorn.lifespan.on",
    # fastapi / starlette
    "fastapi",
    "starlette",
    "starlette.staticfiles",
    "starlette.responses",
    "anyio",
    "anyio._backends._asyncio",
    "anyio._backends._trio",
    # encoding
    "encodings",
    "encodings.utf_8",
    "encodings.ascii",
    # other
    "h11",
    "httptools",
    "email.mime.text",
    "email.mime.multipart",
] + yt_dlp_hiddens + webview_hiddens

# ============================================================
#  Analysis
# ============================================================

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=yt_dlp_datas + webview_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PIL",
        "test",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# ============================================================
#  EXE
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,      # binaries go into COLLECT, not inside exe
    name="RaagaX",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                   # compress — reduces size
    console=False,              # no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico" if IS_WINDOWS else (
        "assets/icon.icns" if IS_MAC else None
    ),
)

# ============================================================
#  COLLECT — output folder with exe + all dependencies
# ============================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RaagaX",              # output folder name: dist/RaagaX/
)

# ============================================================
#  Mac — wrap in .app bundle
# ============================================================

if IS_MAC:
    app = BUNDLE(
        coll,
        name="RaagaX.app",
        icon="assets/icon.icns",
        bundle_identifier="com.raagax.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription": "RaagaX does not use the microphone",
            "LSMinimumSystemVersion": "10.14.0",
        },
    )
