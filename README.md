# ◈ RaagaX

A modern, self-contained music and video player built as a desktop application. Paste any link or search by name — RaagaX fetches and plays it instantly, no downloads, no accounts.

---

## Features

- Play music and video from links or search by name
- Queue management with drag and drop reordering
- Playlist support — paste a playlist link and all tracks load automatically
- Seek bar, volume control, loop, skip, and keyboard shortcuts
- Queue persists across restarts
- Light and dark theme, saved automatically
- Fully offline after launch — no browser needed

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `→` | Forward 10s |
| `←` | Rewind 10s |
| `↑` | Volume up |
| `↓` | Volume down |
| `N` | Next track |
| `P` | Previous track |
| `L` | Toggle loop |

---

## Requirements

### To run from source
- Python 3.11 or higher
- Windows 10/11, macOS 10.14+, or Linux with `libwebkit2gtk`

### To run the built application
- **Windows** — Windows 10 or 11 (Edge WebView2 is built in, nothing else needed)
- **Linux** — `libwebkit2gtk-4.1` system library

---

## Run from Source

```bash
# 1. Clone the repository
git clone https://github.com/code-1py/RaagaX
cd RaagaX

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

---

## Build the Application

Build produces a standalone folder at `dist\RaagaX\` that runs without Python installed.

### Windows

```bat
scripts\build_windows.bat
```

Output: `dist\RaagaX\RaagaX.exe`

### Linux

```bash
bash scripts/build_linux.sh
```

Output: `dist/RaagaX/RaagaX`

> **Note:** Build must be run on the target OS. You cannot build a Linux binary on Windows or vice versa.

---

## Distribute the Application

After building, the entire `dist\RaagaX\` folder is your application.

**To share it:**
1. Zip the `dist\RaagaX\` folder
2. Send the zip to anyone
3. They extract it and run `RaagaX.exe` (Windows) or `./RaagaX` (Linux)

The folder must stay intact — do not move just the executable out of it, it needs the files alongside it to run.

---

## Linux System Dependency

On Linux, install the WebKit library before running or building:

```bash
# Ubuntu / Debian
sudo apt install libwebkit2gtk-4.1-dev

# Fedora
sudo dnf install webkit2gtk4.1

# Arch
sudo pacman -S webkit2gtk
```

---

## Project Structure

```
RaagaX/
├── main.py              # Entry point
├── requirements.txt
├── RaagaX.spec          # PyInstaller build spec
├── scripts/
│   ├── build_windows.bat
│   └── build_linux.sh
├── backend/
│   ├── app.py           # FastAPI application
│   ├── logger/          # Logging setup
│   ├── media/           # Media fetching
│   ├── settings/        # User preferences
│   └── utils/           # Shared utilities
└── frontend/
    ├── index.html
    ├── css/
    └── js/
```

---

## Roadmap

- WebSocket support for real-time playback sync
- Delayed/progressive loading for large playlists
- Large playlist handling with smart queuing
- macOS support

---

## Logs

Application logs are written to `logs/raagax.log` next to the executable (or project root in dev mode). Logs rotate automatically and entries older than 7 days are cleaned up.

---