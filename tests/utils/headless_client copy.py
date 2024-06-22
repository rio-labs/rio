import asyncio
from collections.abc import Callable

import uvicorn
from selenium import webdriver
from typing_extensions import Self

import rio
from rio.app_server import FastapiServer
from rio.debug.layouter import Layouter
from rio.utils import choose_free_port

__all__ = ["HeadlessClient"]


class HeadlessClient:
    def __init__(
        self,
        window_size: tuple[float, float],
        build: Callable[[], rio.Component],
    ):
        self.window_size = window_size
        self.build = build

        self._port = choose_free_port("localhost")

        self._session: rio.Session | None = None
        self._uvicorn_server: uvicorn.Server | None = None
        self._uvicorn_serve_task: asyncio.Task[None] | None = None
        self._webdriver = None

    async def __aenter__(self) -> Self:
        self._uvicorn_server, app_server = await self._start_uvicorn_server()
        self._webdriver = self._start_webdriver()
        self._session = await self._create_session(app_server)

        return self

    async def _start_uvicorn_server(self):
        server_is_ready_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def set_server_ready_event():
            loop.call_soon_threadsafe(server_is_ready_event.set)

        app = rio.App(build=self.build)
        app_server = FastapiServer(
            app,
            debug_mode=False,
            running_in_window=False,
            internal_on_app_start=set_server_ready_event,
        )

        config = uvicorn.Config(
            app_server,
            port=self._port,
            # log_level="critical",
        )
        uvicorn_server = uvicorn.Server(config)

        current_task: asyncio.Task = asyncio.current_task()  # type: ignore
        self._uvicorn_serve_task = asyncio.create_task(
            self._run_uvicorn(uvicorn_server, current_task)
        )

        await server_is_ready_event.wait()

        # Just because uvicorn says it's ready doesn't mean it's actually ready.
        # Give it a bit more time.
        await asyncio.sleep(1)

        return uvicorn_server, app_server

    async def _run_uvicorn(
        self, uvicorn_server: uvicorn.Server, test_task: asyncio.Task
    ):
        try:
            await uvicorn_server.serve()
        except BaseException as error:
            test_task.cancel(f"Uvicorn server crashed: {error}")

    def _start_webdriver(self):
        # Start the browser and connect to the server
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        options.add_argument(
            f"--window-size={self.window_size[0]},{self.window_size[1]}"
        )

        # Silence annoying terminal output
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("browserVersion", "117")

        return webdriver.Chrome(options=options)

    async def _create_session(self, app_server: FastapiServer):
        assert self._webdriver is not None

        self._webdriver.get(f"http://localhost:{self._port}")

        while not app_server.sessions:
            await asyncio.sleep(0.1)

        return app_server.sessions[0]

    async def __aexit__(self, *_) -> None:
        print("Exiting")

        if self._webdriver is not None:
            self._webdriver.quit()

        if self._session is not None:
            await self._session._close(close_remote_session=False)

        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True

    async def verify_dimensions(self) -> None:
        assert self._session is not None

        print("Creating layouter")
        layouter = await Layouter.create(self._session)

        for component_id, layout_should in layouter._layouts_should.items():
            print("Verifying layout of component", component_id)
            layout_is = layouter._layouts_are[component_id]

            assert layout_is == layout_should
