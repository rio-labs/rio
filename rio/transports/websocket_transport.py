import fastapi
from uniserde import JsonDoc

from .abstract_transport import *

__all__ = ["WebsocketTransport"]


class WebsocketTransport(AbstractTransport):
    def __init__(self, websocket: fastapi.WebSocket):
        self._websocket = websocket
        self._closed_intentionally = False

    async def send(self, msg: str) -> None:
        try:
            await self._websocket.send_text(msg)
        except RuntimeError:  # Socket is already closed
            pass

    async def receive(self) -> JsonDoc:
        try:
            return await self._websocket.receive_json()
        except RuntimeError:  # Socket is already closed
            pass
        except fastapi.WebSocketDisconnect as err:
            self._closed_intentionally = err.code == 1001

        if self._closed_intentionally:
            raise TransportClosedIntentionally
        else:
            raise TransportInterrupted

    async def close(self) -> None:
        self._closed_intentionally = True
        await self._websocket.close()
