import time
import asyncio
import threading
from pypresence import AioPresence, DiscordNotFound , ActivityType
import aiohttp
from backend.logger import logger
import traceback


#---------Config----------#

CLIENT_ID = "1514464813760249916"

#--------Discord RPC------#

class DiscordRPC:
    def __init__(self):
        self.rpc = None
        self.connected = False

        # One persistent background thread with one event loop.
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True, # Daemon thread will exit when main program exits
            name="DiscordRPC-Loop"
        )
        self._thread.start()

    
    def connect(self)-> None:
        future = asyncio.run_coroutine_threadsafe(self._connect(),self._loop)
        try:
            future.result(timeout=10) # wait for 10s to connect
        except Exception as e:
            logger.warning(f"[RPC] Failed to connect to Discord RPC: {traceback.format_exc()}")

    async def _connect(self) -> None:
        for attempt in range(3):  # try 3 times
            try:
                self.rpc = AioPresence(CLIENT_ID, loop=self._loop)
                await self.rpc.connect()
                self.connected = True
                logger.info("[RPC] Connected to Discord")
                return
            except (DiscordNotFound, ConnectionRefusedError, FileNotFoundError):
                logger.info("[RPC] Discord not running — Rich Presence disabled")
                self.connected = False
                return
            except Exception as e:
                logger.warning(f"[RPC] Attempt {attempt+1} failed: {e}")
                await asyncio.sleep(2)  # wait 2s before retry
        logger.warning("[RPC] Could not connect after 3 attempts")
        self.connected = False

    async def _update(self, title, artist, thumbnail_url, duration=None, position=0, paused=False):
        try:
            large_image = thumbnail_url if thumbnail_url else "raagax_logo"

            now = int(time.time())
            start = now - position if (duration and not paused) else None
            end   = start + duration if (duration and not paused) else None     

            await self.rpc.update(
                activity_type=ActivityType.LISTENING,
                details=title[:128] if title else "Playing",
                state=f"by {artist[:128]}" if artist else None,
                large_image=large_image,
                large_text=title or "RaagaX",
                small_image="raagax_logo",
                small_text="RaagaX",
                start=start,
                end=end,
            )
            logger.info(f"[RPC] Updated: {title}")
        except Exception as e:
            logger.warning(f"[RPC] Failed to update presence: {traceback.format_exc()}")
            self.connected = False
        
    async def _clear(self) -> None:
        try:
            await self.rpc.clear()
            logger.info("[RPC] Cleared presence")
        except Exception:
            pass

    async def _disconnect(self) -> None:
        await self._clear()
        try:
            await self.rpc.close()
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("[RPC] Disconnected")

rpc = DiscordRPC()