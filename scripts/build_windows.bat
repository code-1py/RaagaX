@echo off
REM ============================================================
REM  RaagaX — Windows Build Script
REM  Run from project root: build\build_windows.bat
REM ============================================================

echo [RaagaX] Installing dependencies...
python -m pip install --upgrade -r requirements.txt

echo [RaagaX] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [RaagaX] Building with PyInstaller...
pyinstaller RaagaX.spec

echo [RaagaX] Done!
echo Output: dist\RaagaX\RaagaX.exe
pause
