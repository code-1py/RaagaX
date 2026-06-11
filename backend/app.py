from backend.logger import logger
from fastapi import FastAPI, Request  , HTTPException
from fastapi.responses import HTMLResponse , RedirectResponse , JSONResponse , FileResponse
from fastapi.staticfiles import StaticFiles
from backend.settings import get_user_customization, set_update_user_customization
import traceback
from backend.utils import BASE_DIR
from backend.media import get_playlist_info, get_songs_info
from contextlib import asynccontextmanager
from backend.discord_presence import rpc

@asynccontextmanager
async def lifespan(app: FastAPI):
    rpc.connect()    # Connect to Discord RPC when the application starts
    yield            
    rpc.disconnect() # Disconnect from Discord RPC when the application shuts down

app = FastAPI(lifespan=lifespan)

FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/css",StaticFiles(directory=str(FRONTEND_DIR / "css")),name="css") # CSS Files Mount
app.mount("/js",StaticFiles(directory=str(FRONTEND_DIR / "js")),name="js") # JS Files Mount


# main route to serve the frontend

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
    
@app.post("/user_customization_update",response_class=JSONResponse)
async def user_customization_update(request:Request):
    try:
        data = await request.json()
        theme = data.get("display_mode")
        if theme not in ["light", "dark"]:
            return JSONResponse(content={"error": "Invalid theme value"}, status_code=400)
        set_update_user_customization(theme)
        return JSONResponse({"success": True})
    
    except Exception as e:
        logger.error(f"Error updating user customization: {traceback.format_exc()}")
        return JSONResponse(content={"error": "Failed to update user customization"}, status_code=500)
    
@app.post("/get-song", response_class=JSONResponse)
async def get_song(request: Request):
    try:
        data: dict = await request.json()
        link = data.get("link")
        if not link:
            return JSONResponse(content={"error": "Missing 'link' parameter"}, status_code=400)

        playlist_info:dict = get_playlist_info(link)
        if playlist_info.get("is_playlist"):
            song_count = playlist_info.get("count", 0)
            if song_count > 50:
                return JSONResponse(content={"error": "Playlist too large. Maximum allowed is 50 songs."}, status_code=400)
        
        success , songs_info = get_songs_info(link)
        if not success:
            return JSONResponse(content={"error": songs_info}, status_code=400)
        
        if len(songs_info) == 0:
            return JSONResponse(content={"error": "No songs found at the provided link"}, status_code=404)
        
        response = {
            "multiple_song": playlist_info.get("is_playlist", False),
            "song": songs_info
        }
        if songs_info and len(songs_info) == 1:
            response["song"] = songs_info[0]  # Return single song as an object instead of a list
            

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error fetching song: {traceback.format_exc()}")
        traceback.print_exc()
        return JSONResponse(content={"error": "Failed to fetch song"}, status_code=500)
    

# Discord RPC Handling routes

@app.post("/rpc/update", response_class=JSONResponse)
async def rpc_update(request: Request):
    try:
        data = await request.json()
        title = data.get("title")
        artist = data.get("artist")
        thumbnail_url = data.get("thumbnail_url")
        duration = data.get("duration")
        position = data.get("position", 0)
        paused = data.get("paused", False)
 
        if not title:
            return JSONResponse(content={"error": "Missing 'title'"}, status_code=400)
 
        rpc.update(
            title=title,
            artist=artist,
            thumbnail_url=thumbnail_url,
            duration=duration,
            position=position,
            paused=paused,
        )
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"[RPC] /rpc/update error: {traceback.format_exc()}")
        return JSONResponse(content={"error": "Failed to update RPC"}, status_code=500)