from __future__ import annotations

import asyncio
import typing as t

import playwright.async_api
import playwright.sync_api
import uvicorn

import rio.app_server
import rio.data_models
from rio.app_server import FastapiServer
from rio.components.text import Text
from rio.debug.layouter import Layouter
from rio.session import Session
from rio.utils import choose_free_port

__all__ = ["verify_layout", "cleanup"]


layouter_factory: LayouterFactory | None = None


async def verify_layout(
    build: t.Callable[[], rio.Component],
) -> Layouter:
    """
    Rio contains two layout implementations: One on the client side, which
    determines the real layout of components, and a second one on the server
    side which is used entirely for testing.

    This function verifies that the results from the two layouters are the same.
    """
    global layouter_factory

    if layouter_factory is None:
        layouter_factory = LayouterFactory()
        await layouter_factory.start()

    layouter = await layouter_factory.create_layouter(build)

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


async def cleanup() -> None:
    if layouter_factory is not None:
        await layouter_factory.stop()


class LayouterFactory:
    """
    This class is designed to efficiently create many `Layouter` objects for
    different GUIs. Starting a web server and a browser every time you need a
    `Layouter` has very high overhead, so this class re-uses the existing ones
    when possible.
    """

    def __init__(self) -> None:
        self._port = choose_free_port("localhost")

        self._app = rio.App(
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

    async def start(self) -> None:
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

    async def create_layouter(
        self, build: t.Callable[[], rio.Component]
    ) -> Layouter:
        self._app._build = build
        session, page = await self._create_session()

        # FIXME: Give the client some time to process the layout
        await asyncio.sleep(0.5)

        layouter = await Layouter.create(session)

        await page.close()
        await session._close(close_remote_session=False)

        return layouter

    async def _start_uvicorn_server(self) -> None:
        server_is_ready_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def set_server_ready_event() -> None:
            loop.call_soon_threadsafe(server_is_ready_event.set)

        self._app_server = FastapiServer(
            self._app,
            debug_mode=False,
            running_in_window=False,
            internal_on_app_start=set_server_ready_event,
            base_url=None,
        )

        config = uvicorn.Config(
            self._app_server,
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
            browser = await playwright_obj.chromium.launch()
        except Exception:
            raise Exception(
                "Playwright cannot launch chromium. Please execute the"
                " following command:\n"
                "playwright install --with-deps chromium\n"
                "(If you're using a virtual environment, activate it first.)"
            ) from None

        # With default settings, playwright gets detected as a crawler. So we
        # need to emulate a real device.
        self._browser = await browser.new_context(
            **playwright_obj.devices["Desktop Chrome"]
        )

    async def _create_session(self) -> tuple[Session, t.Any]:
        assert (
            self._app_server is not None
        ), "Uvicorn isn't running for some reason"
        assert self._browser is not None

        assert (
            not self._app_server.sessions
        ), f"App server still has sessions?! {self._app_server.sessions}"

        page = await self._browser.new_page()
        await page.goto(f"http://localhost:{self._port}")

        while not self._app_server.sessions:
            await asyncio.sleep(0.1)

        return self._app_server.sessions[0], page


def build_connection_lost_message() -> Text:
    return rio.Text("Connection Lost")
