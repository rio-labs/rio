from __future__ import annotations

import socket

import uvicorn

import rio

__all__ = [
    "UvicornServer",
]


class UvicornServer(uvicorn.Server):
    """
    A `uvicorn.Server` whose shutdown always includes the lifespan shutdown.

    uvicorn's shutdown can crash halfway through: it tries to send a close
    frame on websockets that the client is already closing, which raises
    `websockets.exceptions.InvalidState`. This happens regularly when an app
    window is closed, because the window closes its websocket right as the
    server shuts down. The exception skips the lifespan shutdown, so the app's
    `on_app_close` handlers and the session cleanup only run if something
    cancels the lifespan task later (`asyncio.run` happens to, on exit). And
    the exception is printed as a big, scary traceback.

    Use this class instead of `uvicorn.Server` everywhere.
    """

    async def shutdown(
        self,
        sockets: list[socket.socket] | None = None,
    ) -> None:
        try:
            await super().shutdown(sockets=sockets)
        except Exception as error:
            rio._logger.debug(
                f"uvicorn's shutdown crashed ({error!r}). Running the"
                + " lifespan shutdown anyway."
            )

            # Same condition uvicorn itself uses
            if not self.force_exit:
                await self.lifespan.shutdown()
