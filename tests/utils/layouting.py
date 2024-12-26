from __future__ import annotations

import asyncio
import typing as t

import asyncio_atexit
import playwright.async_api
import uvicorn

import rio.app_server
import rio.data_models
from rio.app_server import FastapiServer
from rio.components.text import Text
from rio.debug.layouter import Layouter
from rio.utils import choose_free_port

__all__ = ["BrowserClient", "verify_layout", "setup", "cleanup"]


# For debugging. Set this to a number > 0 if you want to look at the browser.
#
# Note: Chrome's console doesn't show `console.debug` messages per default. To
# see them, click on "All levels" and check "Verbose".
DEBUG_SHOW_BROWSER_DURATION = 0


server_manager: ServerManager | None = None


async def _get_server_manager() -> ServerManager:
    global server_manager

    if server_manager is None:
        server_manager = ServerManager()
        await server_manager.start()

    return server_manager


async def setup() -> None:
    """
    The functions in this module require a fairly expensive one-time setup,
    which often causes tests to fail because they exceed their timeout. Calling
    this function in a fixture solves that problem.
    """
    await _get_server_manager()


async def cleanup() -> None:
    if server_manager is not None:
        await server_manager.stop()


class BrowserClient:
    def __init__(
        self, build: t.Callable[[], rio.Component], *, debug_mode: bool = False
    ) -> None:
        self._build = build
        self._debug_mode = debug_mode
        self._session: rio.Session | None = None
        self._page: playwright.async_api.Page | None = None

    @property
    def session(self) -> rio.Session:
        assert self._session is not None
        return self._session

    async def execute_js(self, js: str) -> t.Any:
        assert self._page is not None
        return await self._page.evaluate(js)

    async def __aenter__(self) -> BrowserClient:
        manager = await _get_server_manager()

        assert (
            not manager.app_server.sessions
        ), f"App server still has sessions?! {manager.app_server.sessions}"

        manager.app._build = self._build
        manager.app_server.debug_mode = self._debug_mode

        self._page = await manager.browser.new_page()
        await self._page.goto(f"http://localhost:{manager.port}")

        while not manager.app_server.sessions:
            await asyncio.sleep(0.1)

        self._session = manager.app_server.sessions[0]

        return self

    async def __aexit__(self, *args: t.Any) -> None:
        # Sleep to keep the browser open for debugging
        await asyncio.sleep(DEBUG_SHOW_BROWSER_DURATION)

        if self._page is not None:
            await self._page.close()

        if self._session is not None:
            await self._session._close(close_remote_session=False)


async def verify_layout(
    build: t.Callable[[], rio.Component],
) -> Layouter:
    """
    Rio contains two layout implementations: One on the client side, which
    determines the real layout of components, and a second one on the server
    side which is used entirely for testing.

    This function verifies that the results from the two layouters are the same.
    """
    async with BrowserClient(build) as client:
        layouter = await Layouter.create(client.session)

    for component_id, layout_should in layouter._layouts_should.items():
        layout_is = layouter._layouts_are[component_id]

        differences = list[str]()
        for attribute in rio.data_models.ComponentLayout.__annotations__:
            # Not all attributes are meant to be compared
            if attribute == "parent_id":
                continue

            value_should = getattr(layout_should, attribute)
            value_is = getattr(layout_is, attribute)

            difference = abs(value_is - value_should)
            if difference > 0.2:
                differences.append(f"{attribute}: {value_is} != {value_should}")

        if differences:
            component = layouter.get_component_by_id(component_id)
            raise ValueError(
                f"Layout of component {component} is incorrect:\n- "
                + "\n- ".join(differences)
            )

    return layouter


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
        self._playwright_context = None
        self._browser = None

    @property
    def app_server(self) -> FastapiServer:
        assert self._app_server is not None
        return self._app_server

    @property
    def uvicorn_server(self) -> uvicorn.Server:
        assert self._uvicorn_server is not None
        return self._uvicorn_server

    @property
    def browser(self) -> playwright.async_api.BrowserContext:
        assert self._browser is not None
        return self._browser

    async def start(self) -> None:
        asyncio_atexit.register(self.stop)

        await self._start_browser()
        await self._start_uvicorn_server()

    async def stop(self) -> None:
        if self._browser is not None:
            await self._browser.close()

        if self._playwright_context is not None:
            await self._playwright_context.__aexit__()

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
        self._playwright_context = playwright.async_api.async_playwright()

        playwright_obj = await self._playwright_context.__aenter__()

        try:
            browser = await playwright_obj.chromium.launch(
                headless=DEBUG_SHOW_BROWSER_DURATION == 0
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
        kwargs = dict(playwright_obj.devices["Desktop Chrome"])
        # The default window size is too large to fit on my screen, which sucks
        # when debugging. Make it smaller.
        kwargs["viewport"] = {"width": 800, "height": 600}
        self._browser = await browser.new_context(**kwargs)


def build_connection_lost_message() -> Text:
    return rio.Text("Connection Lost")
