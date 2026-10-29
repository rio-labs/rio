import asyncio
import contextlib
import json
import logging
import re
import typing as t
import urllib.request

import pytest
import uvicorn
import websockets.asyncio.client
import websockets.exceptions

import rio
from rio import data_models, serialization
from rio.app_server import UvicornServer


@contextlib.asynccontextmanager
async def _run_server() -> t.AsyncIterator[str]:
    """
    Runs a Rio app in a real uvicorn server and yields its URL.
    """
    app = rio.App(build=lambda: rio.Text("Hello"))
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
    try:
        while not server.started:
            await asyncio.sleep(0.01)

        port = server.servers[0].sockets[0].getsockname()[1]
        yield f"http://127.0.0.1:{port}/"
    finally:
        server.should_exit = True
        await serve_task


async def _load_page(page_url: str) -> tuple[str, str | None]:
    """
    Loads the page like a browser would. Returns the session token baked into
    the HTML, as well as the `Cache-Control` header.
    """
    # Without a browser user agent, we'd be treated as a crawler and wouldn't
    # get a session token
    request = urllib.request.Request(
        page_url,
        headers={"User-Agent": "Mozilla/5.0 Firefox/140.0"},
    )

    def load() -> tuple[str, str | None]:
        with urllib.request.urlopen(request) as response:
            return (
                response.read().decode(),
                response.headers.get("Cache-Control"),
            )

    html, cache_control = await asyncio.to_thread(load)

    match = re.search(r'SESSION_TOKEN = "([^"]+)"', html)
    assert match is not None
    return match.group(1), cache_control


def _websocket_url(page_url: str, session_token: str, reconnect: bool) -> str:
    # Must match `createWebsocket()` in `rpc.ts`
    ws_url = page_url.replace("http://", "ws://")
    return f"{ws_url}rio/ws?session_token={session_token}&reconnect={str(reconnect).lower()}"


def _initial_message(url: str) -> str:
    # This is what `sendInitialMessage()` in `rpc.ts` sends as soon as a
    # freshly loaded page has opened its websocket
    return json.dumps(
        serialization.json_serde.as_json(
            data_models.InitialClientMessage.from_defaults(url=url)
        )
    )


async def _receive_methods(
    ws: websockets.asyncio.client.ClientConnection,
    duration: float,
) -> list[str]:
    methods = list[str]()

    try:
        async with asyncio.timeout(duration):
            while True:
                message = json.loads(await ws.recv())
                methods.append(message.get("method"))
    except TimeoutError:
        pass

    return methods


async def test_index_html_is_not_cacheable() -> None:
    # The HTML contains a single-use session token. If it were cached, it
    # could be re-used by another page load.
    async with _run_server() as page_url:
        _, cache_control = await _load_page(page_url)

    assert cache_control == "no-store"


async def test_fresh_page_with_reused_session_token_is_rejected(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR, logger="unicall")

    async with _run_server() as page_url:
        session_token, _ = await _load_page(page_url)
        ws_url = _websocket_url(page_url, session_token, reconnect=False)

        # First page load: The server creates a session and sends the theme,
        # fonts and components.
        async with websockets.asyncio.client.connect(ws_url) as ws:
            await ws.send(_initial_message(page_url))
            methods = await _receive_methods(ws, 1)

        assert "applyTheme" in methods
        assert "updateComponentStates" in methods

        # The connection is gone, but the session stays alive in case the
        # client reconnects. Now the *same HTML* is executed again (e.g.
        # restored from a cache), so a fresh page presents the old token. This
        # must not be mistaken for a reconnect - the server must reject the
        # token, so the client reloads the page and gets a new one.
        #
        # Note: The server may close the connection before we even get to send
        # the initial message.
        async with websockets.asyncio.client.connect(ws_url) as ws:
            with pytest.raises(websockets.exceptions.ConnectionClosed) as info:
                await ws.send(_initial_message(page_url))
                await _receive_methods(ws, 3)

        assert info.value.rcvd is not None
        assert info.value.rcvd.code == 3000

    # The initial message must not have ended up in the RPC handler
    assert not [
        record
        for record in caplog.records
        if record.getMessage() == "Error in RPC request:"
    ]


async def test_reconnect_reuses_session(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR, logger="unicall")

    async with _run_server() as page_url:
        session_token, _ = await _load_page(page_url)

        async with websockets.asyncio.client.connect(
            _websocket_url(page_url, session_token, reconnect=False)
        ) as ws:
            await ws.send(_initial_message(page_url))
            await _receive_methods(ws, 1)

        # A genuine reconnect doesn't send an initial message. The server
        # re-attaches it to the existing session and re-sends all components.
        async with websockets.asyncio.client.connect(
            _websocket_url(page_url, session_token, reconnect=True)
        ) as ws:
            methods = await _receive_methods(ws, 3)

        assert "updateComponentStates" in methods

    assert not [
        record
        for record in caplog.records
        if record.getMessage() == "Error in RPC request:"
    ]
