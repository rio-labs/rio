import asyncio
import socket

import pytest
import uvicorn

import rio
from rio.app_server import UvicornServer


async def test_lifespan_shutdown_runs_even_if_uvicorn_shutdown_crashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Like uvicorn tripping over a websocket that the client is already
    # closing: stop listening, then crash before the lifespan shutdown.
    async def crashing_shutdown(
        self: uvicorn.Server,
        sockets: list[socket.socket] | None = None,
    ) -> None:
        for server in self.servers:
            server.close()

        raise RuntimeError("connection is closing")

    monkeypatch.setattr(uvicorn.Server, "shutdown", crashing_shutdown)

    closed: list[None] = []

    async def on_app_close(app: rio.App) -> None:
        closed.append(None)

    app = rio.App(build=rio.Spacer, on_app_close=on_app_close)
    fastapi_app = app._as_fastapi(
        debug_mode=False,
        running_in_window=False,
        internal_on_app_start=None,
        base_url=None,
    )
    server = UvicornServer(
        uvicorn.Config(fastapi_app, port=0, log_level="critical")
    )

    serve_task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.01)

    server.should_exit = True
    await serve_task

    assert closed == [None]
