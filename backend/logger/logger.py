from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import logging
import sys


# ============================================================
# Base Directory
# ============================================================

if getattr(sys, "frozen", False):
    # Running as packaged executable
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Running from source
    BASE_DIR = Path(__file__).resolve().parent.parent


# ================#
# Logs Directory  #
# ================#

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "raagax.log"


# =================#
# Cleanup Old Logs #
# =================#

LOG_RETENTION_DAYS = 7

try:
    cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)

    for file in LOG_DIR.glob("raagax.log*"):
        try:
            modified = datetime.fromtimestamp(file.stat().st_mtime)

            if modified < cutoff:
                file.unlink()

        except Exception as exc:
            pass

except Exception as exc:
    pass

# =======#
# Logger #
# =======#
 
logger = logging.getLogger("RaagaX")

if not logger.handlers:

    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.propagate = False


# =================#
# Startup Log      #
# =================#

logger.info("Logger initialized")