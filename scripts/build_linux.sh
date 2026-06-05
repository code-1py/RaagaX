#!/bin/bash
# ============================================================
#  RaagaX — Linux Build Script
#  Run from project root: bash scripts/build_linux.sh
# ============================================================

set -e

# ============================================================
#  Detect package manager
# ============================================================

if command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
elif command -v pacman &>/dev/null; then
    PKG_MANAGER="pacman"
else
    echo "[RaagaX] WARNING: Could not detect package manager."
    echo "         Please manually install libwebkit2gtk and python3-gi before running."
    PKG_MANAGER="unknown"
fi

# ============================================================
#  Install system dependencies
# ============================================================

echo "[RaagaX] Checking system dependencies..."

install_apt() {
    echo "[RaagaX] Installing $1..."
    sudo apt-get install -y "$@"
}

if [ "$PKG_MANAGER" = "apt" ]; then

    # libwebkit2gtk — try 4.1 first, fall back to 4.0
    if ! dpkg -l | grep -q libwebkit2gtk; then
        echo "[RaagaX] Installing libwebkit2gtk..."
        install_apt libwebkit2gtk-4.1-dev || install_apt libwebkit2gtk-4.0-dev
    else
        echo "[RaagaX] libwebkit2gtk already installed."
    fi

    # python3-gi (PyGObject) — required by pywebview GTK backend
    if ! python3 -c "import gi" &>/dev/null; then
        echo "[RaagaX] Installing python3-gi (PyGObject)..."
        # Try webkit2gtk 4.1 GIR first, fall back to 4.0
        install_apt python3-gi python3-gi-cairo gir1.2-webkit2-4.1 || \
        install_apt python3-gi python3-gi-cairo gir1.2-webkit2-4.0
    else
        echo "[RaagaX] python3-gi already installed."
    fi

elif [ "$PKG_MANAGER" = "dnf" ]; then

    echo "[RaagaX] Installing system dependencies via dnf..."
    sudo dnf install -y webkit2gtk4.1 python3-gobject || \
    sudo dnf install -y webkit2gtk python3-gobject

elif [ "$PKG_MANAGER" = "pacman" ]; then

    echo "[RaagaX] Installing system dependencies via pacman..."
    sudo pacman -S --noconfirm webkit2gtk python-gobject

fi

# ============================================================
#  Verify python3-gi is importable (catches venv vs system issues)
# ============================================================

if ! python3 -c "import gi" &>/dev/null; then
    echo ""
    echo "[RaagaX] ERROR: python3-gi could not be imported even after installation."
    echo "         If you are inside a virtual environment, pywebview's GTK backend"
    echo "         needs access to the system python3-gi package."
    echo "         Try: python -m venv venv --system-site-packages"
    echo "         Then re-activate and re-run this script."
    echo ""
    exit 1
fi

echo "[RaagaX] All system dependencies satisfied."

# ============================================================
#  Python dependencies
# ============================================================

echo "[RaagaX] Installing Python dependencies..."
pip3 install -r requirements.txt

# ============================================================
#  Build
# ============================================================

echo "[RaagaX] Cleaning previous build..."
rm -rf build dist

echo "[RaagaX] Building with PyInstaller..."
pyinstaller RaagaX.spec

echo "[RaagaX] Copying frontend files..."
cp -r frontend dist/RaagaX/frontend

echo "[RaagaX] Setting executable permission..."
chmod +x dist/RaagaX/RaagaX

echo ""
echo "[RaagaX] Done! Output: dist/RaagaX/RaagaX"