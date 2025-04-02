from __future__ import annotations

import asyncio
import contextlib
import sys
import typing as t

import asyncio_atexit
import playwright.async_api
import uvicorn

import rio.app_server
import rio.data_models
from rio.app_server import FastapiServer
from rio.components.component import Key
from rio.components.text import Text
from rio.transports import FastapiWebsocketTransport, MultiTransport
from rio.utils import choose_free_port

from .base_client import BaseClient

__all__ = ["BrowserClient", "prepare_browser_client"]


# When the debugger is active, we'll enable debugging features like making the
# browser visible, visualizing clicks, etc.
#
# Note: Chrome's console doesn't show `console.debug` messages per default. To
# see them, click on "All levels" and check "Verbose".
DEBUGGER_ACTIVE = sys.gettrace() is not None


server_manager: ServerManager | None = None


async def _get_server_manager() -> ServerManager:
    global server_manager

    if server_manager is None:
        server_manager = ServerManager()
        await server_manager.start()

    return server_manager


@contextlib.asynccontextmanager
async def prepare_browser_client():
    """
    Starting a `BrowserClient` can take a while, and can cause unit tests to
    exceed their timeout. This context manager prepares all of the stuff that
    `BrowserClient`s require to function, eliminating most of the overhead.

    To ensure that the expensive preparation happens before the unit tests
    start, use this context manager in a fixture:

    ```python
    @pytest.fixture(scope="session", autouse=True)
    async def prepare():
        async with prepare_browser_client():
            yield
    ```

    Note: There have been issues where pytest would hang when shutting down the
    browser used by `BrowserClient`s. This context manager should also help with
    that.
    """
    await _get_server_manager()

    try:
        yield
    finally:
        if server_manager is not None:
            await server_manager.stop()


class BrowserClient(BaseClient):
    def __post_init__(self) -> None:
        self._page: playwright.async_api.Page | None = None
        self._page_closed_event = asyncio.Event()

    @property
    def playwright_page(self) -> playwright.async_api.Page:
        assert self._page is not None
        return self._page

    @property
    def _window_width_in_pixels(self) -> int:
        assert self._page is not None
        assert self._page.viewport_size is not None

        return self._page.viewport_size["width"]

    @property
    def _window_height_in_pixels(self) -> int:
        assert self._page is not None
        assert self._page.viewport_size is not None

        return self._page.viewport_size["height"]

    async def wait_for_component_to_exist(
        self,
        component_type: type[rio.Component] = rio.Component,
        key: Key | None = None,
    ) -> None:
        assert self._page is not None

        component = self.get_component(key=key, component_type=component_type)
        await self._page.wait_for_selector(f'[dbg-id="{component._id_}"]')

    async def click(
        self,
        x: float,
        y: float,
        *,
        button: t.Literal["left", "middle", "right"] = "left",
        sleep: float = 0.1,
    ) -> None:
        assert self._page is not None

        if isinstance(x, float) and x <= 1:
            x = round(x * self._window_width_in_pixels)

        if isinstance(y, float) and y <= 1:
            y = round(y * self._window_height_in_pixels)

        if DEBUGGER_ACTIVE:
            await self.execute_js(f"""
                const marker = document.createElement('div');
                marker.style.pointerEvents = 'none';
                marker.style.background = 'red';
                marker.style.borderRadius = '50%';
                marker.style.position = 'absolute';
                marker.style.zIndex = '9999';
                marker.style.width = '10px';
                marker.style.height = '10px';
                marker.style.left = `{x}px`;
                marker.style.top = `{y}px`;
                marker.style.transform = 'translate(-50%, -50%)';
                document.body.appendChild(marker);
                
                setTimeout(() => {{
                    marker.remove();
                }}, {sleep} * 1000);
            """)

        await self._page.mouse.click(x, y, button=button)
        await asyncio.sleep(sleep)

    async def double_click(
        self,
        x: float,
        y: float,
        *,
        button: t.Literal["left", "middle", "right"] = "left",
        sleep: float = 0.1,
    ) -> None:
        await self.click(x, y, button=button, sleep=0.1)
        await self.click(x, y, button=button, sleep=sleep)

    async def execute_js(self, js: str) -> t.Any:
        assert self._page is not None
        return await self._page.evaluate(js)

    async def _get_app_server(self) -> rio.app_server.AbstractAppServer:
        manager = await _get_server_manager()
        return manager.app_server

    async def _create_session(self) -> rio.Session:
        manager = await _get_server_manager()

        assert not manager.app_server.sessions, (
            f"App server still has sessions?! {manager.app_server.sessions}"
        )

        manager.app = self._app
        manager.app_server._transport_factory = (
            lambda websocket: MultiTransport(
                FastapiWebsocketTransport(websocket),
                self._recorder_transport,
            )
        )

        self._page = await manager.new_page()
        self._page.on("close", lambda _: self._page_closed_event.set())

        await self._page.goto(f"http://localhost:{manager.port}")

        while True:
            try:
                return manager.app_server.sessions[0]
            except IndexError:
                await asyncio.sleep(0.1)

    async def __aexit__(self, *args: t.Any) -> None:
        if DEBUGGER_ACTIVE:
            await self._page_closed_event.wait()

        if self._page is not None:
            await self._page.close()

        await super().__aexit__(*args)

        manager = await _get_server_manager()
        while manager.app_server.sessions:
            await asyncio.sleep(0.1)


class ServerManager:
    """
    This class is designed to efficiently create many `BrowserClient` objects
    for different GUIs. Starting a web server and a browser every time you need
    a `BrowserClient` has very high overhead, so this class re-uses the existing
    ones when possible.
    """

    def __init__(self) -> None:
        self.port = choose_free_port("localhost")

        self.app = rio.App(
            build=rio.Spacer,
            # JS reports incorrect sizes and positions for hidden elements, and
            # so the tests end up failing because of the icon in the connection
            # lost popup. I think it's because icons have a fixed size, but JS
            # reports the size as 0x0. So we'll get rid of the icon.
            build_connection_lost_message=build_connection_lost_message,
        )
        self._app_server: FastapiServer | None = None
        self._uvicorn_server: uvicorn.Server | None = None
        self._uvicorn_serve_task: asyncio.Task[None] | None = None
        self._playwright: playwright.async_api.Playwright | None = None
        self._browser: playwright.async_api.Browser | None = None
        self._browser_context: playwright.async_api.BrowserContext | None = None

    @property
    def app_server(self) -> FastapiServer:
        assert self._app_server is not None
        return self._app_server

    async def new_page(self) -> playwright.async_api.Page:
        assert self._browser_context is not None
        return await self._browser_context.new_page()

    async def start(self) -> None:
        asyncio_atexit.register(self.stop)

        await self._start_browser()
        await self._start_uvicorn_server()

    async def stop(self) -> None:
        if self._browser_context is not None:
            await self._browser_context.close()

        if self._browser is not None:
            await self._browser.close()

        if self._playwright is not None:
            await self._playwright.stop()

        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True

            assert self._uvicorn_serve_task is not None
            await self._uvicorn_serve_task

    async def _start_uvicorn_server(self) -> None:
        server_is_ready_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def set_server_ready_event() -> None:
            loop.call_soon_threadsafe(server_is_ready_event.set)

        self._app_server = FastapiServer(
            self.app,
            debug_mode=False,
            running_in_window=False,
            internal_on_app_start=set_server_ready_event,
            base_url=None,
        )

        config = uvicorn.Config(
            self._app_server,
            port=self.port,
            log_level="critical",
        )
        self._uvicorn_server = uvicorn.Server(config)

        current_task: asyncio.Task = asyncio.current_task()  # type: ignore
        self._uvicorn_serve_task = asyncio.create_task(
            self._run_uvicorn(current_task)
        )

        await server_is_ready_event.wait()

        # Just because uvicorn says it's ready doesn't mean it's actually ready.
        # Give it a bit more time.
        await asyncio.sleep(1)

    async def _run_uvicorn(self, test_task: asyncio.Task) -> None:
        assert self._uvicorn_server is not None

        try:
            await self._uvicorn_server.serve()
        except BaseException as error:
            test_task.cancel(f"Uvicorn server crashed: {error}")

    async def _start_browser(self) -> None:
        self._playwright = await playwright.async_api.async_playwright().start()

        try:
            self._browser = await self._playwright.chromium.launch(
                headless=not DEBUGGER_ACTIVE
            )
        except Exception:
            raise Exception(
                "Playwright cannot launch chromium. Please execute the"
                " following command:\n"
                "playwright install --with-deps chromium\n"
                "(If you're using a virtual environment, activate it first.)"
            ) from None

        # With default settings, playwright gets detected as a crawler. So we
        # need to emulate a real device.
        kwargs = dict(self._playwright.devices["Desktop Chrome"])
        # The default window size is too large to fit on my screen, which sucks
        # when debugging. Make it smaller.
        kwargs["viewport"] = {"width": 800, "height": 600}
        self._browser_context = await self._browser.new_context(**kwargs)


def build_connection_lost_message() -> Text:
    return rio.Text("Connection Lost")
