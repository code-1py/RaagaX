# ◈ RaagaX

A modern, self-contained music player built as a desktop application. Paste any link or search by name — RaagaX fetches and plays it instantly, no downloads, no accounts.

> **v1.1.0:** All tracks now display as audio with thumbnail art. Discord Rich Presence added. Frontend is bundled inside the application binary.

---

## Features

- Play music from links or search by name
- Thumbnail art display for all tracks
- Discord Rich Presence — shows track title, art, and live progress on your profile
- Queue management with drag and drop reordering
- Playlist support — tracks stream into the queue one at a time with no fixed playlist-size limit
- Persistent WebSocket connection for track lookup, settings, and Discord Rich Presence updates
- Seek bar, volume control, loop, skip, and keyboard shortcuts
- Light and dark theme, saved automatically

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
- Windows 10/11 or Linux with `libwebkit2gtk`

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

# Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

---

## Build the Application

Build produces a standalone folder at `dist\RaagaX\` that runs without Python installed. The frontend (HTML, CSS, JS) is bundled inside the binary — no separate folder is needed.

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
└── frontend/            # Bundled into binary at build time
    ├── index.html
    ├── css/
    └── js/
```

---

## Roadmap

- macOS support

---

## Discord Rich Presence

RaagaX shows what you're listening to on your Discord profile in real time.

- Displays track title, thumbnail art, and a live progress timer
- Presence clears automatically when playback stops or the app closes
- Requires Discord to be running — if it isn't, RaagaX continues playing normally and presence is silently skipped
- No configuration needed, it works out of the box

---

## Logs

Application logs are written to `logs/raagax.log` next to the executable (or project root in dev mode). Logs rotate automatically and entries older than 7 days are cleaned up.

---