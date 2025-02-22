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

from ... import nice_traceback
from . import run_models


class UvicornWorker:
    def __init__(
        self,
        *,
        push_event: t.Callable[[run_models.Event], None],
        app_server: rio.app_server.fastapi_server.FastapiServer,
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
        # While already provided in the constructor, this needs some values to
        # be overridden. `replace_app` already handles this, so delegate to that
        # function.
        self.app_server = app_server
        self.replace_app(app_server)

    async def run(self) -> None:
        rio.cli._logger.debug("Uvicorn worker is starting")

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
            nice_traceback.print_exception(err)
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
        app_server: rio.app_server.fastapi_server.FastapiServer,
    ) -> None:
        """
        Replace the app currently running in the server with a new one. The
        worker must already be running for this to work.
        """
        assert (
            app_server.internal_on_app_start is None
        ), app_server.internal_on_app_start

        # Store the new app
        self.app_server = app_server

        self.app_server.base_url = self.base_url
        self.app_server.debug_mode = self.debug_mode
        self.app_server.running_in_window = self.run_in_window
        self.app_server.internal_on_app_start = (
            lambda: self.on_server_is_ready_or_failed.set_result(None)
        )

        # There is no need to inject the new app or server anywhere. Since
        # uvicorn was fed a shim function instead of the app directly, any
        # requests will automatically be redirected to the new server instance.
