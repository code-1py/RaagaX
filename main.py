import threading
import time
import sys
import platform
import urllib.request
import uvicorn
import webview
from backend.logger import logger

# ============================================================
#  Platform detection
# ============================================================

OS = platform.system()  # "Windows", "Darwin", "Linux"

# ============================================================
#  Config
# ============================================================

HOST = "127.0.0.1"
PORT = 18420
URL  = f"http://{HOST}:{PORT}"

# ============================================================
#  Uvicorn
# ============================================================

server: uvicorn.Server | None = None

def start_server() -> None:
    global server
    config = uvicorn.Config(
        app="backend.app:app",
        host=HOST,
        port=PORT,
        log_level="error",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info(f"Starting uvicorn on {URL}")
    server.run()


def stop_server() -> None:
    global server
    if server:
        logger.info("Shutting down uvicorn")
        server.should_exit = True


# ============================================================
#  Wait for server
# ============================================================

def wait_for_server(timeout: int = 20) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.15)
    return False


# ============================================================
#  Linux — check WebKit availability before doing anything
# ============================================================

def check_linux_webkit() -> bool:
    try:
        import ctypes
        # Try 4.1 first (newer distros), then 4.0 (older)
        for lib in ("libwebkit2gtk-4.1.so.0", "libwebkit2gtk-4.0.so.37"):
            try:
                ctypes.CDLL(lib)
                logger.info(f"WebKit found: {lib}")
                return True
            except OSError:
                continue
        return False
    except Exception:
        return False


# ============================================================
#  Window events
# ============================================================

def on_closed() -> None:
    logger.info("Window closed — shutting down")
    stop_server()


# ============================================================
#  Launch webview
# ============================================================

def launch_window() -> None:
    # private_mode breaks localStorage on Mac (WKWebView) and some Linux builds
    # Only enable on Windows where it works correctly
    use_private = OS == "Windows"

    window = webview.create_window(
        title="RaagaX",
        url=URL,
        width=1280,
        height=760,
        min_size=(900, 600),
        resizable=True,
        text_select=False,
        confirm_close=False,
        easy_drag=False,
    )

    window.events.closed += on_closed

    webview.start(
        debug=False,
        private_mode=use_private,
    )


# ============================================================
#  Entry point
# ============================================================

if __name__ == "__main__":

    # Linux — warn early if WebKit is missing
    if OS == "Linux" and not check_linux_webkit():
        print(
            "ERROR: libwebkit2gtk not found.\n"
            "Install it with:\n"
            "  Ubuntu/Debian: sudo apt install libwebkit2gtk-4.1-dev\n"
            "  Fedora:        sudo dnf install webkit2gtk4.1\n"
            "  Arch:          sudo pacman -S webkit2gtk\n"
        )
        logger.error("libwebkit2gtk not found — cannot launch UI")
        sys.exit(1)

    # Start uvicorn in background daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    logger.info("Waiting for server to be ready...")
    ready = wait_for_server(timeout=20)

    if not ready:
        logger.error("Server failed to start within timeout — exiting")
        stop_server()
        sys.exit(1)

    logger.info(f"Server ready on {OS} — launching window")
    launch_window()

    server_thread.join(timeout=3)
    logger.info("RaagaX exited cleanly")
    sys.exit(0)