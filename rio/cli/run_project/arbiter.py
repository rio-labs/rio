import asyncio
import json
import linecache
import logging
import signal
import socket
import sys
import threading
import time
import typing as t
from datetime import datetime, timedelta, timezone
from pathlib import Path

import revel
from revel import print

import rio.app_server.fastapi_server
import rio.arequests as arequests
import rio.cli

from ... import nice_traceback, project_config, utils, version
from ...debug.monkeypatches import apply_monkeypatches
from . import (
    app_loading,
    file_watcher_worker,
    run_models,
    uvicorn_worker,
    webview_worker,
)

# There is a hilarious problem with `watchfiles`: When a change occurs,
# `watchfiles` logs that change. If Python is configured to log into the project
# directory, then `watchfiles` will pick up on that new log line, thus
# triggering another change. Infinite loop, here we come!
#
# -> STFU, watchfiles!
logging.getLogger("watchfiles").setLevel(logging.CRITICAL + 1)


LOGO_TEXT = r"""  _____  _
 |  __ \(_)
 | |__) |_  ___
 |  _  /| |/ _ \
 | | \ \| | (_) |
 |_|  \_\_|\___/"""


class Arbiter:
    """
    Serves as a unified interface to running apps, coordinating the various
    workers necessary to do so.
    """

    def __init__(
        self,
        *,
        proj: project_config.RioProjectConfig,
        port: int | None,
        public: bool,
        quiet: bool,
        debug_mode: bool,
        run_in_window: bool,
        base_url: rio.URL | None,
    ) -> None:
        assert not (run_in_window and public), (
            "Can't run in a local window over the network, wtf!?"
        )

        self.proj = proj
        self.public = public
        self.quiet = quiet
        self.debug_mode = debug_mode
        self.run_in_window = run_in_window
        self.base_url = base_url

        # Workers communicate with the `RunningApp` by pushing events into this
        # queue.
        self._event_queue: asyncio.Queue[run_models.Event] = asyncio.Queue()

        # Contains the various workers, if running
        self._file_watcher_worker: (
            file_watcher_worker.FileWatcherWorker | None
        ) = None
        self._uvicorn_worker: uvicorn_worker.UvicornWorker | None = None
        self._webview_worker: webview_worker.WebViewWorker | None = None

        self._file_watcher_task: asyncio.Task[None] | None = None
        self._uvicorn_task: asyncio.Task[None] | None = None
        self._arbiter_task: asyncio.Task[None] | None = None

        # The theme to use for creating placeholder apps. This keeps the theme
        # consistent if for-example the user's app crashes and then a mock-app
        # is injected.
        self._app_theme: t.Union[
            rio.Theme,
            tuple[rio.Theme, rio.Theme],
        ] = rio.Theme.pair_from_colors()

        # Prefer to consistently run on the same port, as that makes it easier
        # to connect to - this way old browser tabs don't get invalidated
        # constantly.
        if port is None:
            if utils.port_is_free(self._host, 8000):
                self.port = 8000
            else:
                self.port = utils.choose_free_port(self._host)
        else:
            self.port = port

        # Used by the stop function for thread safety
        self._stopping_lock = threading.Lock()

        # This event resolves once the app is ready to be shown in the webview.
        self._server_is_ready = threading.Event()

        # Used to signal that the app should close
        self._stop_requested = threading.Event()

        # The mainloop used by the arbiter. This is set once asyncio is up and
        # running.
        self._mainloop: asyncio.AbstractEventLoop | None = None

    def push_event(self, event: run_models.Event) -> None:
        """
        Pushes an event into the event queue. Threadsafe.
        """
        assert self._mainloop is not None, (
            "Can't push events before asyncio is running"
        )
        rio.cli._logger.debug(f"Pushing arbiter event `{event}`")
        self._mainloop.call_soon_threadsafe(self._event_queue.put_nowait, event)

    @property
    def _host(self) -> str:
        return "0.0.0.0" if self.public else "127.0.0.1"

    @property
    def url(self) -> str:
        # If a base URL is specified, use that
        if self.base_url is not None:
            return str(self.base_url)

        # If running in public mode, use the device's IP on the local network.
        if self.public:
            # Get the local IP. This doesn't send data, because UDP is
            # connectionless.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

        # Otherwise use localhost
        else:
            local_ip = "127.0.0.1"

        return f"http://{local_ip}:{self.port}"

    @property
    def running_tasks(self) -> t.Iterator[asyncio.Task[None]]:
        for task in (
            self._uvicorn_task,
            self._file_watcher_task,
            self._arbiter_task,
        ):
            if task is not None:
                yield task

    async def _fetch_published_rio_version_from_pypi(self) -> str:
        """
        Fetches the version number of the latest Rio available on PyPI, without
        any cache.

        ## Raises

        `ValueError`: If the version number could not be determined.

        """
        try:
            response = await arequests.request(
                "get",
                "https://pypi.org/pypi/rio-ui/json",
            )

            data = response.json()
            return data["info"]["version"]

        except (
            arequests.HttpError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(f"Failed to fetch the latest Rio version: {exc}")

    async def get_published_rio_version(self) -> str:
        """
        Finds the version number of the latest Rio available on PyPI, using a
        cache to avoid unnecessary network requests.

        ## Raises

        `ValueError`: If the version number could not be determined.
        """
        # See if a cached version is available
        #
        # Asking the asset manager for a cache path will also ensure that the
        # cache directory exists.
        cache_path = utils.ASSET_MANAGER.get_cache_path(
            Path("rio-pypi-version.txt")
        )
        threshold = datetime.now(timezone.utc) - timedelta(hours=3)

        try:
            file_modified_at = cache_path.stat().st_mtime
            file_contents = cache_path.read_text()
        except OSError:
            pass
        else:
            if (
                datetime.fromtimestamp(file_modified_at, timezone.utc)
                >= threshold
            ):
                return file_contents.strip()

        # No cache exists. Fetch the version number from PyPI
        result = await self._fetch_published_rio_version_from_pypi()

        # Store the result in the cache
        try:
            cache_path.write_text(result)
        except OSError:
            pass

        return result

    def stop(self, *, keyboard_interrupt: bool) -> None:
        """
        Stops the app. This function can safely be called more than once, and at
        any point in time.
        """
        # Already shutting down? Then do nothing
        if not self._stopping_lock.acquire(blocking=False):
            return

        rio.cli._logger.debug("Stopping the app")

        # Visualize KeyboardInterrupts
        if keyboard_interrupt:
            print()
            print("[yellow]Interrupted[/]")
        else:
            print("Stopping")

        # Release anyone waiting for events
        self._stop_requested.set()
        self._server_is_ready.set()

        # Stop any running workers.
        #
        # The mainloop may not be running yet, if something went wrong before it
        # was started.
        def cancel_all_tasks() -> None:
            rio.cli._logger.debug(
                "Cancelling all arbiter tasks because the app is stopping"
            )

            for task in self.running_tasks:
                task.cancel("Arbiter is stopping")

        if self._mainloop is not None:
            self._mainloop.call_soon_threadsafe(cancel_all_tasks)

        # Stop the webview
        if self._webview_worker is not None:
            rio.cli._logger.debug(
                "Stopping the webview because the app is stopping"
            )
            self._webview_worker.request_stop()

    def try_load_app(
        self,
    ) -> tuple[
        rio.app_server.fastapi_server.FastapiServer,
        Exception | None,
    ]:
        """
        Tries to load the user's app. If it fails, a dummy app is created and
        returned, unless running in release mode. (In release mode screams and
        exits the entire process.)

        Returns the app server instance and an exception if the app could not be
        loaded.

        The app server is returned in case the user has called `as_fastapi` on
        their app instance. In that case the actual fastapi app should be
        hosted, so any custom routes take effect.
        """
        rio.cli._logger.debug("Trying to load the app")

        try:
            app_server = app_loading.load_user_app(self.proj)

        except app_loading.AppLoadError as err:
            # Announce the problem in the terminal
            # rio.cli._logger.exception(f"The app could not be loaded: {err}")
            revel.error(f"The app could not be loaded: {err}")

            if err.__cause__ is not None:
                nice_traceback.print_exception(
                    err.__cause__,
                    relpath=self.proj.project_directory,
                )

            # If running in release mode, no further attempts to load the app
            # will be made. This error is fatal.
            if not self.debug_mode:
                sys.exit(1)

            print()

            # Otherwise create a placeholder app which displays the error
            # message
            app = app_loading.make_error_message_app(
                err,
                self.proj.project_directory,
                self._app_theme,
            )
            app_server = app.as_fastapi()
            assert isinstance(
                app_server, rio.app_server.fastapi_server.FastapiServer
            )

            return app_server, err

        # Remember the app's theme. If in the future a placeholder app is used,
        # this theme will be used for it.
        self._app_theme = app_server.app._theme

        return app_server, None

    def run(self) -> None:
        assert not self._stop_requested.is_set()
        assert not self._server_is_ready.is_set()

        # Handle keyboard interrupts. KeyboardInterrupt exceptions are very
        # annoying to handle in async code, so instead we'll use a signal
        # handler.
        def keyboard_interrupt_handler(*_):
            self.stop(keyboard_interrupt=True)

            # Restore the original keyboard interrupt handler. Sometimes things
            # hang, and our graceful shutdown won't work. Restoring the original
            # handler gives the user a more powerful tool to work with.
            signal.signal(signal.SIGINT, original_keyboard_interrupt_handler)

        original_keyboard_interrupt_handler = signal.signal(
            signal.SIGINT, keyboard_interrupt_handler
        )

        # Do as much work as possible in asyncio land. If this crashes for any
        # reason, stop the world.
        async def asyncio_wrapper() -> None:
            try:
                await self._run_async()
            finally:
                self.stop(keyboard_interrupt=False)

        asyncio_thread = threading.Thread(
            target=lambda: asyncio.run(asyncio_wrapper()),
            # target=lambda: asyncio.run(self._run_async()),
            name="arbiter function of rio run",
        )
        asyncio_thread.start()

        # Wait for the http server to be ready
        rio.cli._logger.debug("Waiting for the http server to be ready")
        self._server_is_ready.wait()

        # Make sure the startup was successful
        if self._stop_requested.is_set():
            rio.cli._logger.debug(
                "Stopping the arbiter because a stop was requested before the startup sequence has finished"
            )
            asyncio_thread.join()
            return

        # The webview needs to be shown from the main thread. So, if running
        # inside of a window run the arbiter in a separate thread. Otherwise
        # just run it from this one.
        if self.run_in_window:
            self._webview_worker = webview_worker.WebViewWorker(
                push_event=self.push_event,
                debug_mode=self.debug_mode,
                url=self.url,
            )

            rio.cli._logger.debug("Starting the webview worker")
            assert self._uvicorn_worker is not None
            self._webview_worker.run(self._uvicorn_worker.app_server.app)

        # If not running in a webview, just wait
        else:
            rio.cli._logger.debug("Opening the browser")

            # Event.wait() blocks the SIGINT handler, so we must periodically
            # return to python land to react to keyboard interrupts.
            #
            # We could pass a timeout to `_stop_requested.wait()`, but
            # `time.sleep()` reacts to keyboard interrupts immediately, which is
            # preferable.
            while True:
                time.sleep(0.2)

                if self._stop_requested.is_set():
                    break

        # Make sure the main thread stays alive until the asyncio thread is
        # done. Otherwise we get weird errors like "Can't start thread during
        # interpreter shutdown" from asyncio.
        rio.cli._logger.debug(
            "The arbiter is waiting for the asyncio thread to finish"
        )
        asyncio_thread.join()

        rio.cli._logger.debug("Arbiter shutdown complete")

    async def _run_async(self) -> None:
        # Publish the task, so it can be cancelled
        self._arbiter_task = asyncio.current_task()

        # Make sure the webview module is available
        if self.run_in_window:
            try:
                from ... import webview_shim as webview_shim
            except ImportError:
                revel.fatal(
                    """The `window` extra is required to run apps inside of a window. Run `pip install "rio-ui[[window]"` to install it."""
                )

        # Make sure the app is cleanly shut down, even if the arbiter crashes
        # for whichever reason.
        #
        # This loop has a bad case of hiding important exceptions. It would
        # really be nice to only shut down on intentional errors and at least
        # log the others.
        try:
            await self._run_async_inner()

        # Keyboard interrupts are already handled by the signal handler
        except KeyboardInterrupt:
            pass

        # The worker is expected to be cancelled when the app is stopped
        except asyncio.CancelledError:
            pass

        # Anything else is an unintentional crash
        except Exception as err:
            revel.error("The arbiter has crashed.")
            revel.error("This is a bug in Rio - please report it")
            print()
            nice_traceback.print_exception(err)

            rio.cli._logger.exception("The arbiter has crashed")

            self.stop(keyboard_interrupt=False)

        finally:
            # Wait until all the other tasks are done. If we return, then
            # `asyncio.run` will cancel anything that's still running.
            rio.cli._logger.debug("Waiting for all arbiter tasks to finish")

            for task in self.running_tasks:
                if task is self._arbiter_task:
                    continue

                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Then cancel all remaining tasks to ensure the program exits
            rio.cli._logger.debug("Cancelling all remaining asyncio tasks")

            for task in asyncio.all_tasks():
                if task is self._arbiter_task:
                    continue

                task.cancel("Arbiter is shutting down")

    async def _run_async_inner(self) -> None:
        # Print some initial messages
        print()
        print(f"[bold green]{LOGO_TEXT}[/]")
        print()
        print()
        print("Starting...")

        # Expose the mainloop
        self._mainloop = asyncio.get_running_loop()

        # Make sure the chosen port is available
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            rio.cli._logger.debug(f"Checking if port {self.port} is available")

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                sock.bind((self._host, self.port))
            except OSError:
                revel.error(f"The port [bold]{self.port}[/] is already in use.")
                revel.error("Each port can only be used by one app at a time.")
                revel.error(
                    "Try using another port, or let Rio choose one for you, by not specifying any port."
                )
                self.stop(keyboard_interrupt=False)
                return

            # Fetch the most recent version of Rio. Since this needs to make
            # HTTP requests do it as early as possible
            rio_version_fetcher_task = asyncio.create_task(
                self.get_published_rio_version(),
                name="Fetch Rio version",
            )

            # If running in debug mode, install safeguards
            if self.debug_mode:
                rio.cli._logger.debug("Applying monkeypatches")
                apply_monkeypatches()

            # Try to load the app
            app_server, _ = self.try_load_app()

            # Start the file watcher
            if self.debug_mode:
                self._file_watcher_worker = (
                    file_watcher_worker.FileWatcherWorker(
                        push_event=self.push_event,
                        proj=self.proj,
                    )
                )
                self._file_watcher_task = asyncio.create_task(
                    self._file_watcher_worker.run(),
                    name="File watcher",
                )

            # Start the uvicorn worker
            uvicorn_is_ready_or_has_failed: asyncio.Future[None] = (
                asyncio.Future()
            )

            self._uvicorn_worker = uvicorn_worker.UvicornWorker(
                push_event=self.push_event,
                app_server=app_server,
                socket=sock,
                quiet=self.quiet,
                debug_mode=self.debug_mode,
                run_in_window=self.run_in_window,
                on_server_is_ready_or_failed=uvicorn_is_ready_or_has_failed,
                base_url=self.base_url,
            )

            self._uvicorn_task = asyncio.create_task(
                self._uvicorn_worker.run(),
                name="Uvicorn",
            )

            # Wait for the server to be ready or fails to start
            rio.cli._logger.debug("Waiting for uvicorn to be ready or to fail")
            await uvicorn_is_ready_or_has_failed

            # Let everyone else know that the server is ready
            rio.cli._logger.debug(
                "App startup complete and ready for connections"
            )
            self._server_is_ready.set()

            # The app has just successfully started. Inform the user that...
            #
            # ...their Rio version is outdated
            installed_rio_version = rio.__version__

            try:
                newest_rio_version = await rio_version_fetcher_task
            except ValueError as err:
                logging.warning(
                    f"Failed to fetch the newest Rio version. Skipping version check: {err}"
                )
            else:
                try:
                    installed_rio_version_parsed = version.Version.parse(
                        installed_rio_version
                    )
                except ValueError:
                    logging.warning(
                        f"Failed to parse installed Rio version: `{installed_rio_version}`"
                    )
                    installed_rio_version_parsed = version.Version(0)

                try:
                    newest_rio_version_parsed = version.Version.parse(
                        newest_rio_version
                    )
                except ValueError:
                    logging.warning(
                        f"Failed to parse newest Rio version: `{newest_rio_version}`"
                    )
                    newest_rio_version_parsed = version.Version(0)

                # From experience, people don't even notice the warnings in `rio
                # run` anymore after some time, because they show up so
                # frequently. Intentionally style this one differently, since
                # it's important and must be noticed.
                if newest_rio_version_parsed > installed_rio_version_parsed:
                    revel.print(
                        f"[bg-yellow] [/] [bold yellow]Rio [bold]{newest_rio_version}[/] is available![/]"
                    )
                    revel.print(
                        "[bg-yellow] [/] [bold yellow]Please update to get the newest features, bugfixes and security updates.[/]"
                    )
                    revel.print(
                        "[bg-yellow] [/] Run `[bold]pip install --upgrade rio-ui[/]` to get the newest version."
                    )
                    print()

            # ...debug mode is enabled
            if self.debug_mode:
                revel.warning("Debug mode is enabled.")
                revel.warning(
                    "Debug mode includes helpful tools for development, but is slower and disables some safety checks. Never use it in production!"
                )
                revel.warning("Run with `--release` to disable debug mode.")
                print()

            # ...public mode is enabled (or not)
            if self.public:
                revel.warning(
                    "Running in public mode. All devices on your network can access the app."
                )
                revel.warning(
                    "Only run in public mode if you trust your network!"
                )
                revel.warning(
                    "Run without `--public` to limit access to this device."
                )
                print()
            elif not self.run_in_window:
                print(
                    "[dim]Running in [/]local[dim] mode. Only this device can access the app.[/]"
                )
                print()

            # ...where the app is running
            if not self.run_in_window:
                revel.success(f"The app is running at [bold]{self.url}[/]")
                print()

            # Support us, pretty please?
            try:
                print(
                    "🗨  Join other Developers on Discord [dim]—[/] https://discord.gg/7ejXaPwhyH"
                )
                print(
                    "✨ Star Rio on GitHub [dim]—[/] https://github.com/rio-labs/rio"
                )
                print(
                    "🐞 Report a bug [dim]—[/] https://github.com/rio-labs/rio/issues/new/choose"
                )
                print("📣 Spread the word")
            except UnicodeEncodeError:
                pass

            # Keep track when the app was last reloaded
            last_reload_started_at = -1

            # Listen for events and react to them
            while True:
                event = await self._event_queue.get()
                rio.cli._logger.debug(f"Received arbiter event `{event}`")

                # A file has changed
                if isinstance(event, run_models.FileChanged):
                    # Ignore events that happened before the last reload started
                    if event.timestamp_nanoseconds < last_reload_started_at:
                        continue

                    # Display to the user that a reload is happening
                    rel_path = event.path_to_file.relative_to(
                        self.proj.project_directory
                    )
                    print()
                    print(f"[bold]{rel_path}[/] has changed -> Reloading")

                    # Update the timestamp
                    last_reload_started_at = time.monotonic_ns()

                    # If the `rio.toml` has changed, reload the project
                    # configuration in addition to the Python app
                    if event.path_to_file == self.proj.rio_toml_path:
                        msg = "Reloading project configuration from `rio.toml`"
                        rio.cli._logger.info(msg)
                        print(msg)
                        self._try_reload_project_config()

                    # Restart the app
                    await self._restart_app()

                # Somebody requested that the app should stop
                elif isinstance(event, run_models.StopRequested):
                    self.stop(keyboard_interrupt=False)
                    break

                # ???
                else:
                    raise NotImplementedError(f'Unknown event "{event}"')

    def _try_reload_project_config(self) -> None:
        """
        Attempts to reload the project's configuration from disk. Should this
        fail, details are logged & printed, but no exception is raised. Better
        to have the app running in an outdated state than crash.
        """
        # Try to reload the project configuration
        try:
            self.proj.discard_changes_and_reload()

        # Oh uh.
        except OSError as err:
            msg = f"Couldn't reload the project configuration: {err}"
            revel.error(msg)
            rio.cli._logger.exception(msg)

        except rio.InvalidProjectConfigError as err:
            msg = f"The project configuration is invalid: {err}"
            revel.error(msg)
            rio.cli._logger.error(msg)

    def _spawn_traceback_popups(self, err: t.Union[str, BaseException]) -> None:
        """
        Displays a popup with the traceback in the rio UI.
        """
        assert self._uvicorn_worker is not None
        assert self._uvicorn_worker.app_server is not None

        rio.cli._logger.debug("Spawning traceback popups")

        popup_html = app_loading.make_traceback_html(
            err=err,
            project_directory=self.proj.project_directory,
        )

        for (
            session
        ) in self._uvicorn_worker.app_server._active_session_tokens.values():
            self._evaluate_javascript_in_session_if_connected(
                session,
                f"""
// Override the popup with the traceback message
let popup = document.querySelector(".rio-connection-lost-popup-container");
popup.innerHTML = {json.dumps(popup_html)};

// Spawn the popup
window.setConnectionLostPopupVisible(true);
""",
            )

    async def _restart_app(self) -> None:
        assert self._uvicorn_worker is not None

        rio.cli._logger.debug("Beginning app restart sequence")

        app_server = self._uvicorn_worker.app_server
        assert app_server is not None

        # To makes sure that clients can't (re-)connect while we're in the
        # middle of reloading, tell the app server not to accept new websocket
        # connections
        with app_server.temporarily_disable_new_session_creation():
            # Close all open sessions. It's important that `on_session_close` is
            # executed *before* we reload the module. (And before `on_app_close`
            # is called.)
            #
            # We'll save a list of open sessions so that we can re-create them
            # later.
            sessions = app_server._active_session_tokens.values()

            await asyncio.gather(
                *[
                    session._close(close_remote_session=False)
                    for session in sessions
                ]
            )

            # Call `on_app_close`. This happens automatically when the app
            # server shuts down, but since we're just swapping out the app, we
            # have to do it manually.
            await app_server._call_on_app_close()

        # Clear the linecache. This is used to fetch code for tracebacks; if we
        # don't clear the cache and multiple errors happen in a row, then the
        # tracebacks will display outdated code.
        linecache.checkcache()

        # Load the user's app again
        new_app_server, loading_error = self.try_load_app()

        with new_app_server.temporarily_disable_new_session_creation():
            # Replace the app which is currently hosted by uvicorn
            self._uvicorn_worker.replace_app(new_app_server)

            if self._webview_worker is not None:
                self._webview_worker.update_window_for_app(new_app_server.app)

            # The app has changed, but the uvicorn server is still the same.
            # Because of this, uvicorn won't call the `on_app_start` function -
            # do it manually.
            await new_app_server._call_on_app_starts()

            # There is a subtlety here. Sessions which have requested their
            # index.html, but aren't yet connected to the websocket cannot
            # receive messages. So `_spawn_traceback_popups` will skip them.
            # This is fine as long as `self._app_server.app` has already been
            # assigned, since this ensures that any new websocket connections
            # will receive the new app anyway.
            #
            # -> This MUST happen after the new app has already been injected
            if loading_error is not None:
                self._spawn_traceback_popups(loading_error)

        revel.success("Ready")

    def _evaluate_javascript_in_session_if_connected(
        self,
        session: rio.Session,
        javascript_source: str,
    ) -> None:
        """
        Runs the given javascript source in the given session. Does not
        wait for or return the result.

        Does nothing if the session hasn't fully connected yet.
        """
        # If this session isn't done connecting, just return
        if not session._is_connected:
            return

        # Run the javascript in a task
        async def evaljs_as_coroutine() -> None:
            await session._evaluate_javascript(javascript_source)

        session.create_task(
            evaljs_as_coroutine(),
            name=f"Eval JS in session {session}",
        )
