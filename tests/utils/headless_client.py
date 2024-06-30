import asyncio
from collections.abc import Callable

import uvicorn
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from typing_extensions import Self

import rio
from rio.app_server import FastapiServer
from rio.debug.layouter import Layouter
from rio.utils import choose_free_port

__all__ = ["HeadlessClient"]


# Make sure playwright is set up
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser.close()
except Exception:
    raise Exception(
        "Playwright cannot launch chromium. Please execute the following"
        " command:\n"
        "playwright install --with-deps chromium\n"
        "(If you're using a virtual environment, activate it first.)"
    ) from None


class HeadlessClient:
    def __init__(self, build: Callable[[], rio.Component]):
        self.build = build

        self._port = choose_free_port("localhost")

        self._session: rio.Session | None = None
        self._uvicorn_server: uvicorn.Server | None = None
        self._uvicorn_serve_task: asyncio.Task[None] | None = None
        self._playwright_context = None
        self._browser = None

    async def __aenter__(self) -> Self:
        app_server = await self._start_uvicorn_server()
        await self._start_browser()
        await self._create_session(app_server)

        return self

    async def _start_uvicorn_server(self):
        server_is_ready_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def set_server_ready_event():
            loop.call_soon_threadsafe(server_is_ready_event.set)

        app = rio.App(
            build=self.build,
            # JS reports incorrect sizes and positions for hidden elements, and
            # so the tests end up failing because of the icon in the connection
            # lost popup. I think it's because icons have a fixed size, but JS
            # reports the size as 0x0. So we'll get rid of the icon.
            build_connection_lost_message=build_connection_lost_message,
        )
        app_server = FastapiServer(
            app,
            debug_mode=False,
            running_in_window=False,
            internal_on_app_start=set_server_ready_event,
        )

        config = uvicorn.Config(
            app_server,
            port=self._port,
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

        return app_server

    async def _run_uvicorn(self, test_task: asyncio.Task):
        assert self._uvicorn_server is not None

        try:
            await self._uvicorn_server.serve()
        except BaseException as error:
            test_task.cancel(f"Uvicorn server crashed: {error}")

    async def _start_browser(self):
        self._playwright_context = async_playwright()

        playwright = await self._playwright_context.__aenter__()

        browser = await playwright.chromium.launch()

        # With default settings, playwright gets detected as a crawler. So we
        # need to emulate a real device.
        self._browser = await browser.new_context(
            **playwright.devices["Desktop Chrome"]
        )

    async def _create_session(self, app_server: FastapiServer):
        assert self._browser is not None

        page = await self._browser.new_page()
        await page.goto(f"http://localhost:{self._port}")

        while not app_server.sessions:
            await asyncio.sleep(0.1)

        self._session = app_server.sessions[0]

    async def __aexit__(self, *_) -> None:
        if self._browser is not None:
            await self._browser.close()

        if self._playwright_context is not None:
            await self._playwright_context.__aexit__(*_)

        if self._session is not None:
            await self._session._close(close_remote_session=False)

        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True

    def get_component_by_id(self, component_id: int) -> rio.Component:
        assert self._session is not None

        try:
            return self._session._weak_components_by_id[component_id]
        except KeyError:
            raise ValueError(f"There is no component with id {component_id}")

    async def create_layouter(self) -> Layouter:
        assert self._session is not None

        return await Layouter.create(self._session)

    async def verify_layout(self) -> None:
        layouter = await self.create_layouter()

        for component_id, layout_should in layouter._layouts_should.items():
            layout_is = layouter._layouts_are[component_id]

            assert layout_is == layout_should


def build_connection_lost_message():
    return rio.Text("Connection Lost")
