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
            daemon=True,
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