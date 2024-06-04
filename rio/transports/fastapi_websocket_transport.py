import asyncio

import fastapi
from uniserde import JsonDoc

from .abstract_transport import *

__all__ = ["FastapiWebsocketTransport"]


class FastapiWebsocketTransport(AbstractTransport):
    def __init__(self, websocket: fastapi.WebSocket):
        super().__init__()

        self._websocket = websocket
        self._closed_intentionally = False

    async def send(self, msg: str) -> None:
        try:
            await self._websocket.send_text(msg)
        except RuntimeError:
            pass  # Socket is already closed

    async def receive(self) -> JsonDoc:
        try:
            return await self._websocket.receive_json()
        except RuntimeError:
            pass  # Socket is already closed
        except fastapi.WebSocketDisconnect as err:
            self._closed_intentionally = err.code == 1001

        if self._closed_intentionally:
            raise TransportClosedIntentionally
        else:
            raise TransportInterrupted

    def close(self) -> None:
        self._closed_intentionally = True
        asyncio.create_task(self._close_websocket())

    async def _close_websocket(self):
        try:
            await self._websocket.close()
        except RuntimeError:
            pass  # websocket already closed

        self.closed.set()
