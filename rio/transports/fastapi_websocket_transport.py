import contextlib

import fastapi
import typing_extensions as te

from . import abstract_transport

__all__ = ["FastapiWebsocketTransport"]


class FastapiWebsocketTransport(abstract_transport.AbstractTransport):
    def __init__(self, websocket: fastapi.WebSocket):
        super().__init__()

        self._websocket = websocket
        self._closed_intentionally = False

    @contextlib.contextmanager
    def _catch_exceptions(self):
        import revel

        try:
            yield
            return
        except RuntimeError:
            pass  # Socket is already closed
        except fastapi.WebSocketDisconnect as err:
            revel.debug(f"Websocket closed in send: {err.code} {err!r}")
            self._closed_intentionally = err.code == 1001
        except BaseException as err:
            revel.debug(f"Websocket error in send: {err!r}")
            self._closed_intentionally = False

        self.closed_event.set()

    @te.override
    async def send_if_possible(self, msg: str) -> None:
        with self._catch_exceptions():
            await self._websocket.send_text(msg)

    @te.override
    async def receive(self) -> str:
        import revel

        with self._catch_exceptions():
            return await self._websocket.receive_text()

        revel.debug(
            f"Websocket closed intentionally? {self._closed_intentionally}"
        )
        if self._closed_intentionally:
            raise abstract_transport.TransportClosedIntentionally()
        else:
            raise abstract_transport.TransportInterrupted()

    async def close(self) -> None:
        self._closed_intentionally = True

        try:
            await self._websocket.close()
        except RuntimeError:
            pass  # Websocket already closed

        self.closed_event.set()
