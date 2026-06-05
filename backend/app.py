from .logger import logger
from fastapi import FastAPI, Request  , HTTPException
from fastapi.responses import HTMLResponse , RedirectResponse , JSONResponse , FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
from .settings import get_user_customization, set_update_user_customization
import traceback

def get_base_dir():
    if getattr(sys, "frozen", False):
        # running as exe
        return Path(sys.executable).parent

    # running from source
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()

STATIC_DIR = BASE_DIR / "assets" / "static" # Static Files Mount Path

app = FastAPI()

FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/css",StaticFiles(directory=str(FRONTEND_DIR / "css")),name="css") # CSS Files Mount
app.mount("/js",StaticFiles(directory=str(FRONTEND_DIR / "js")),name="js") # JS Files Mount

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/user_customization", response_class=JSONResponse)
async def user_customization(request: Request):
    try:
        customization = get_user_customization()
        return JSONResponse({"display_mode": customization})
    except Exception as e:
        logger.error(f"Error fetching user customization: {traceback.format_exc()}")
        return JSONResponse(content={"error": "Failed to fetch user customization"}, status_code=500)