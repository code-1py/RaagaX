import asyncio
import traceback
from contextlib import asynccontextmanager

from backend.discord_presence import rpc
from backend.logger import logger
from backend.media import iter_songs_info
from backend.media.yt_dlp_service import SongInfoError, SongInfoFailure
from backend.settings import get_user_customization, set_update_user_customization
from backend.utils import BUNDLE_DIR
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import iterate_in_threadpool


@asynccontextmanager
async def lifespan(app: FastAPI):
    rpc.connect()
    yield
    rpc.disconnect()


app = FastAPI(lifespan=lifespan)

FRONTEND_DIR = BUNDLE_DIR / "frontend"

app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    send_lock = asyncio.Lock()
    tasks: set[asyncio.Task] = set()

    async def send(message: dict) -> None:
        async with send_lock:
            await websocket.send_json(message)

    async def handle_request(message: dict) -> None:
        request_id = message.get("id")
        action = message.get("action")
        data = message.get("data") or {}

        try:
            if not isinstance(data, dict):
                await send({"id": request_id, "type": "error", "error": "Invalid request data"})
                return

            if action == "theme_get":
                await send({
                    "id": request_id,
                    "type": "result",
                    "display_mode": get_user_customization(),
                })
            elif action == "theme_set":
                theme = data.get("display_mode")
                if theme not in ("light", "dark"):
                    await send({"id": request_id, "type": "error", "error": "Invalid theme value"})
                    return
                set_update_user_customization(theme)
                await send({"id": request_id, "type": "result", "success": True})
            elif action == "get_song":
                link = data.get("link")
                if not isinstance(link, str) or not link.strip():
                    await send({"id": request_id, "type": "error", "error": "Missing 'link' parameter"})
                    return

                count = 0
                failed_count = 0
                async for item in iterate_in_threadpool(iter_songs_info(link.strip())):
                    if isinstance(item, SongInfoFailure):
                        failed_count += 1
                        await send({
                            "id": request_id,
                            "type": "song_error",
                            "error": f'Failed to fetch "{item.title}": {item.message}. Skipping track.',
                        })
                        continue
                    count += 1
                    await send({"id": request_id, "type": "song", "song": item})

                if count == 0 and failed_count == 0:
                    await send({"id": request_id, "type": "error", "error": "No songs found at the provided link"})
                    return
                await send({
                    "id": request_id,
                    "type": "complete",
                    "count": count,
                    "failed_count": failed_count,
                })
            elif action == "rpc_update":
                title = data.get("title")
                if not title:
                    await send({"id": request_id, "type": "error", "error": "Missing 'title'"})
                    return
                rpc.update(
                    title=title,
                    artist=data.get("artist"),
                    thumbnail_url=data.get("thumbnail_url"),
                    duration=data.get("duration"),
                    position=data.get("position", 0),
                    paused=data.get("paused", False),
                )
                await send({"id": request_id, "type": "result", "success": True})
            elif action == "rpc_clear":
                rpc.clear()
                await send({"id": request_id, "type": "result", "success": True})
            else:
                await send({"id": request_id, "type": "error", "error": "Unknown action"})
        except SongInfoError as e:
            await send({"id": request_id, "type": "error", "error": str(e)})
        except Exception:
            logger.error(f"WebSocket request failed: {traceback.format_exc()}")
            await send({"id": request_id, "type": "error", "error": "Request failed"})

    def request_finished(task: asyncio.Task) -> None:
        tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            logger.error(f"WebSocket response failed: {task.exception()}")

    try:
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                await send({"type": "error", "error": "Invalid request"})
                continue
            task = asyncio.create_task(handle_request(message))
            tasks.add(task)
            task.add_done_callback(request_finished)
    except WebSocketDisconnect:
        pass
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
