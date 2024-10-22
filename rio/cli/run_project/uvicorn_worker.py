import asyncio
import socket
import typing as t

import revel
import uvicorn
import uvicorn.lifespan.on
from starlette.types import Receive, Scope, Send

import rio
import rio.app_server.fastapi_server
import rio.cli

from ... import utils
from .. import nice_traceback
from . import run_models


class UvicornWorker:
    def __init__(
        self,
        *,
        push_event: t.Callable[[run_models.Event], None],
        app: rio.App,
        app_server: rio.app_server.fastapi_server.FastapiServer | None,
        socket: socket.socket,
        quiet: bool,
        debug_mode: bool,
        run_in_window: bool,
        on_server_is_ready_or_failed: asyncio.Future[None],
        base_url: rio.URL | None,
    ) -> None:
        self.push_event = push_event
        self.socket = socket
        self.quiet = quiet
        self.debug_mode = debug_mode
        self.run_in_window = run_in_window
        self.on_server_is_ready_or_failed = on_server_is_ready_or_failed
        self.base_url = base_url

        # The app server used to host the app.
        #
        # This can optionally be provided to the constructor. If not, it will be
        # created when the worker is started. This allows for the app to be
        # either a Rio app or a FastAPI app (derived from a Rio app).
        self.app = app
        self.app_server: rio.app_server.fastapi_server.FastapiServer | None = (
            None
        )

        self.replace_app(app, app_server)

    def _create_and_store_app_server(self) -> None:
        app_server = self.app._as_fastapi(
            debug_mode=self.debug_mode,
            running_in_window=self.run_in_window,
            internal_on_app_start=lambda: self.on_server_is_ready_or_failed.set_result(
                None
            ),
            base_url=self.base_url,
        )
        assert isinstance(
            app_server, rio.app_server.fastapi_server.FastapiServer
        )
        self.app_server = app_server

    async def run(self) -> None:
        rio.cli._logger.debug("Uvicorn worker is starting")

        # Create the app server
        if self.app_server is None:
            self._create_and_store_app_server()
            assert self.app_server is not None

        # Instead of using the ASGI app directly, create a transparent shim that
        # redirect's to the worker's currently stored app server. This allows
        # replacing the app server at will because the shim always remains the
        # same.
        #
        # ASGI is a bitch about function signatures. This function cannot be a
        # simple method, because the added `self` parameter seems to confused
        # whoever the caller is. Hence the nested function.
        async def _asgi_shim(
            scope: Scope,
            receive: Receive,
            send: Send,
        ) -> None:
            assert self.app_server is not None
            await self.app_server(scope, receive, send)

        # Set up a uvicorn server, but don't start it yet
        config = uvicorn.Config(
            app=_asgi_shim,
            log_config=None,  # Prevent uvicorn from configuring global logging
            log_level="error" if self.quiet else "info",
            timeout_graceful_shutdown=1,  # Without a timeout the server sometimes deadlocks
        )
        self._uvicorn_server = uvicorn.Server(config)

        # FIXME: Uvicorn wishes to set up the event loop. The current code
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

        async def patched_receive(self) -> t.Any:
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

    def replace_app(
        self,
        app: rio.App,
        app_server: rio.app_server.fastapi_server.FastapiServer | None,
    ) -> None:
        """
        Replace the app currently running in the server with a new one. The
        worker must already be running for this to work.
        """
        # Store the new app
        self.app = app

        # And create a new app server. This is necessary, because the mounted
        # sub-apps may have changed. This ensures they're up to date.
        if app_server is None:
            self._create_and_store_app_server()
        else:
            self.app_server = app_server

            self.app_server.debug_mode = self.debug_mode
            self.app_server.running_in_window = self.run_in_window
            self.app_server.internal_on_app_start = (
                lambda: self.on_server_is_ready_or_failed.set_result(None)
            )

            if self.base_url is None:
                self.app_server.base_url = None
            else:
                self.app_server.base_url = utils.normalize_url(self.base_url)

        assert self.app_server is not None
        assert self.app_server.app is self.app

        # There is no need to inject the new app or server anywhere. Since
        # uvicorn was fed a shim function instead of the app directly, any
        # requests will automatically be redirected to the new server instance.
