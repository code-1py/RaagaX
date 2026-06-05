#!/bin/bash
# ============================================================
#  RaagaX — Linux Build Script
#  Run from project root: bash build/build_linux.sh
# ============================================================

set -e

echo "[RaagaX] Checking system dependencies..."
if ! dpkg -l | grep -q libwebkit2gtk; then
    echo "[RaagaX] Installing libwebkit2gtk..."
    sudo apt-get install -y libwebkit2gtk-4.1-dev || \
    sudo apt-get install -y libwebkit2gtk-4.0-dev
fi

echo "[RaagaX] Installing Python dependencies..."
pip3 install -r requirements.txt

echo "[RaagaX] Cleaning previous build..."
rm -rf build dist

echo "[RaagaX] Building with PyInstaller..."
pyinstaller RaagaX.spec

echo "[RaagaX] Copying frontend files..."
cp -r frontend dist/RaagaX/frontend

echo "[RaagaX] Setting executable permission..."
chmod +x dist/RaagaX/RaagaX

echo "[RaagaX] Done!"
echo "Output: dist/RaagaX/RaagaX"