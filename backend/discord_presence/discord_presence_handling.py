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
            logger.warning(f"Failed to connect to Discord RPC: {traceback.format_exc()}")