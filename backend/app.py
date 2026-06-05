from backend.logger import logger
from fastapi import FastAPI, Request  , HTTPException
from fastapi.responses import HTMLResponse , RedirectResponse , JSONResponse , FileResponse
from fastapi.staticfiles import StaticFiles
from backend.settings import get_user_customization, set_update_user_customization
import traceback
from backend.utils import BASE_DIR

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