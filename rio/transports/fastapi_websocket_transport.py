import asyncio

import fastapi
import typing_extensions as te

from . import abstract_transport

__all__ = ["FastapiWebsocketTransport"]


class FastapiWebsocketTransport(abstract_transport.AbstractTransport):
    def __init__(self, websocket: fastapi.WebSocket):
        super().__init__()

        self._websocket = websocket
        self._closed_intentionally = False

    @te.override
    async def send(self, msg: str) -> None:
        try:
            await self._websocket.send_text(msg)
        except RuntimeError:
            pass  # Socket is already closed

    @te.override
    async def receive(self) -> str:
        try:
            return await self._websocket.receive_text()
        except RuntimeError:
            pass  # Socket is already closed
        except fastapi.WebSocketDisconnect as err:
            self._closed_intentionally = err.code == 1001

        if self._closed_intentionally:
            raise abstract_transport.TransportClosedIntentionally
        else:
            raise abstract_transport.TransportInterrupted

    def close(self) -> None:
        self._closed_intentionally = True
        asyncio.create_task(self._close_websocket())

    async def _close_websocket(self):
        try:
            await self._websocket.close()
        except RuntimeError:
            pass  # websocket already closed

        self.closed.set()
