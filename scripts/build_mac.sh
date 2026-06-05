#!/bin/bash
# ============================================================
#  RaagaX — Mac Build Script
#  Run from project root: bash build/build_mac.sh
# ============================================================

set -e

echo "[RaagaX] Installing dependencies..."
pip3 install -r requirements.txt

echo "[RaagaX] Cleaning previous build..."
rm -rf build dist

echo "[RaagaX] Building with PyInstaller..."
pyinstaller RaagaX.spec

echo "[RaagaX] Copying frontend files..."
cp -r frontend dist/RaagaX/frontend

echo "[RaagaX] Done!"
echo "Output: dist/RaagaX.app"