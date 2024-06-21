import asyncio
import threading
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
        self._webdriver = None

    async def __aenter__(self) -> Self:
        app = rio.App(build=self.build)
        app_server = FastapiServer(
            app,
            debug_mode=False,
            running_in_window=False,
            internal_on_app_start=self._on_app_start,
        )

        config = uvicorn.Config(
            app_server,
            port=self._port,
            # log_level="critical",
        )
        self._uvicorn_server = uvicorn.Server(config)

        threading.Thread(
            target=self._run_uvicorn,
            args=[self._uvicorn_server, asyncio.current_task()],
        ).start()

        print("Uvicorn thread started")

        while not app_server.sessions:
            await asyncio.sleep(0.1)

        self._session = app_server.sessions[0]
        print("Session:", self._session)

        return self

    def _run_uvicorn(
        self, uvicorn_server: uvicorn.Server, test_task: asyncio.Task
    ):
        try:
            uvicorn_server.run()
        except BaseException as error:
            test_task.cancel(f"Uvicorn server crashed: {error}")

    def _on_app_start(self):
        # Start the browser and connect to the server
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument(
            f"--window-size={self.window_size[0]},{self.window_size[1]}"
        )

        # Silence annoying terminal output
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.set_capability("browserVersion", "117")

        self._webdriver = webdriver.Chrome(options=options)

        self._webdriver.get(f"localhost:{self._port}")

    async def __aexit__(self, *_) -> None:
        if self._webdriver is not None:
            self._webdriver.quit()

        if self._session is not None:
            await self._session._close(close_remote_session=False)

        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True

    async def verify_dimensions(self) -> None:
        assert self._session is not None

        layouter = await Layouter.create(self._session)

        for component_id, layout_should in layouter._layouts_should.items():
            layout_is = layouter._layouts_are[component_id]

            assert layout_is == layout_should
