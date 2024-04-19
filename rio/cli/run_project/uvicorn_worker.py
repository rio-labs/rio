import asyncio
import socket
from typing import *  # type: ignore

import revel
import uvicorn
import uvicorn.lifespan.on

import rio
import rio.app_server
import rio.cli

from .. import nice_traceback
from . import run_models


class UvicornWorker:
    def __init__(
        self,
        *,
        push_event: Callable[[run_models.Event], None],
        app: rio.App,
        socket: socket.socket,
        quiet: bool,
        debug_mode: bool,
        run_in_window: bool,
        on_server_is_ready_or_failed: asyncio.Future[None],
    ) -> None:
        self.push_event = push_event
        self.app = app
        self.socket = socket
        self.quiet = quiet
        self.debug_mode = debug_mode
        self.run_in_window = run_in_window
        self.on_server_is_ready_or_failed = on_server_is_ready_or_failed

        # The app server used to host the app
        self.app_server: rio.app_server.AppServer | None = None

    async def run(self) -> None:
        rio.cli._logger.debug("Uvicorn worker is starting")

        # Set up a uvicorn server, but don't start it yet
        app_server = self.app._as_fastapi(
            debug_mode=self.debug_mode,
            running_in_window=self.run_in_window,
            validator_factory=None,
            internal_on_app_start=lambda: self.on_server_is_ready_or_failed.set_result(
                None
            ),
        )
        assert isinstance(app_server, rio.app_server.AppServer)
        self.app_server = app_server

        config = uvicorn.Config(
            self.app_server,
            log_config=None,  # Prevent uvicorn from configuring global logging
            log_level="error" if self.quiet else "info",
            timeout_graceful_shutdown=1,  # Without a timeout the server sometimes deadlocks
        )
        self._uvicorn_server = uvicorn.Server(config)

        # TODO: Uvicorn wishes to set up the event loop. The current code
        # doesn't let it do that, since asyncio is already running.
        #
        # self._uvicorn_server.config.setup_event_loop()

        # Uvicorn can't handle `CancelledError` properly, so make sure it never
        # sees one. Uvicorn is wrapped in a task, which can finish peacefully.
        serve_task = asyncio.create_task(
            self._uvicorn_server.serve(
                sockets=[self.socket],
            ),
            name="uvicorn serve",
        )

        # Uvicorn doesn't handle CancelledError properly, which results in ugly
        # output in the console. This monkeypatch suppresses that.
        original_receive = uvicorn.lifespan.on.LifespanOn.receive

        async def patched_receive(self) -> Any:
            try:
                return await original_receive(self)
            except asyncio.CancelledError:
                return {
                    "type": "lifespan.shutdown",
                }

        uvicorn.lifespan.on.LifespanOn.receive = patched_receive

        # Run the server
        try:
            await asyncio.shield(serve_task)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            rio.cli._logger.exception(f"Uvicorn has crashed")

            revel.error(f"Uvicorn has crashed:")
            print()
            revel.print(nice_traceback.format_exception_revel(err))
            self.push_event(run_models.StopRequested())
        finally:
            rio.cli._logger.debug("Requesting uvicorn to exit")

            self._uvicorn_server.should_exit = True

            # Make sure not to return before the task has returned, but also
            # avoid receiving any exceptions _again_
            try:
                await serve_task
            except:
                pass
            finally:
                rio.cli._logger.debug("Uvicorn serve task has ended")

    def replace_app(self, app: rio.App) -> None:
        """
        Replace the app currently running in the server with a new one. The
        worker must already be running for this to work.
        """
        assert self.app_server is not None
        rio.cli._logger.debug("Replacing the app in the server")
        self.app_server.app = app
