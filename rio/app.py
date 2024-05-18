from __future__ import annotations

import os
import sys
import threading
import webbrowser
from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import Path
from typing import *  # type: ignore

import __main__
import fastapi
import uvicorn

import rio

from . import app_server, assets, debug, maybes, utils
from .utils import ImageLike


__all__ = [
    "App",
]


def make_default_connection_lost_component() -> rio.Component:
    class DefaultConnectionLostComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Rectangle(
                content=rio.Rectangle(
                    content=rio.Row(
                        rio.Icon(
                            "material/error",
                            fill="danger",
                            width=1.6,
                            height=1.6,
                        ),
                        rio.Text(
                            "Disconnected",
                            style=rio.TextStyle(
                                fill=self.session.theme.hud_palette.foreground,
                                font_weight="bold",
                            ),
                        ),
                        spacing=0.5,
                        margin_x=2.5,
                        margin_y=1.5,
                    ),
                    fill=self.session.theme.hud_palette.background,
                    corner_radius=99999,
                    margin_bottom=0.15,
                ),
                fill=self.session.theme.danger_palette.background,
                corner_radius=99999,
                shadow_color=self.session.theme.shadow_color,
                shadow_radius=0.6,
                shadow_offset_y=0.15,
                margin_top=3,
                align_x=0.5,
                align_y=0.0,
            )

    return DefaultConnectionLostComponent()


@final
class App:
    """
    Contains all the information needed to run a Rio app.

    Apps group all the information needed for Rio to run your application, such
    as its name, icon and, and the pages it contains. Apps also expose several
    lifetime events that you can use to perform tasks such as initialization and
    cleanup.

    If you're serving your app as a website, all users share the same `App`
    instance. If running in a window, there's only one window, and thus `App`,
    anyway.

    A basic setup may look like this:

    ```py
    app = rio.App(
        name="My App",
        build=MyAppRoot,
    )
    ```

    You can then run this app, either as a local application in a window:

    ```py
    app.run_in_window()
    ```

    Or you can create and run a webserver:

    ```py
    app.run_as_web_server()
    ```

    Or create a server, without running it. This allows you to start the script
    externally with tools such as uvicorn:

    ```py
    fastapi_app = app.as_fastapi()
    ```


    ## Attributes

    `name`: The name to display for this app. This can show up in window
        titles, error messages and wherever else the app needs to be
        referenced in a nice, human-readable way.

    `pages`: The pages that make up this app. You can navigate between these
        using `Session.navigate_to` or using `Link` components. If running
        as website the user can also access these pages directly via their
        URL.

    `assets_dir`: The directory where the app's assets are stored. This allows
        you to conveniently access any images or other files that are needed
        by your app.
    """

    # Type hints so the documentation generator knows which fields exist
    name: str
    pages: tuple[rio.Page, ...]
    assets_dir: Path

    def __init__(
        self,
        *,
        name: str | None = None,
        build: Callable[[], rio.Component] | None = None,
        icon: ImageLike | None = None,
        pages: Iterable[rio.Page] = tuple(),
        on_app_start: rio.EventHandler[App] = None,
        on_app_close: rio.EventHandler[App] = None,
        on_session_start: rio.EventHandler[rio.Session] = None,
        on_session_close: rio.EventHandler[rio.Session] = None,
        default_attachments: Iterable[Any] = (),
        ping_pong_interval: int | float | timedelta = timedelta(seconds=50),
        assets_dir: str | os.PathLike = "assets",
        theme: rio.Theme | tuple[rio.Theme, rio.Theme] | None = None,
        build_connection_lost_message: Callable[
            [], rio.Component
        ] = make_default_connection_lost_component,
    ):
        """
        ## Parameters

        `build`: A function that returns the root component of the app. This
            function will be called whenever a new session is created. Note
            that since classes are callable in Python, you can pass a class
            here instead of a function, so long as the class doesn't require
            any arguments.

            If no build method is passed, the app will create a `PageView`
            as the root component.

        `name`: The name to display for this app. This can show up in window
            titles, error messages and wherever else the app needs to be
            referenced in a nice, human-readable way. If not specified,
            `Rio` name will try to guess a name based on the name of the
            main Python file.

        `icon`: The icon to display for this app. This can show up in window
            the title bars of windows, browser tabs, or similar.

        `theme`: The `Theme` for the app. You can also pass in a tuple of two
            themes, which will be used as the light mode theme and the dark mode
            theme.

        `pages`: The pages that make up this app. You can navigate between
            these using `Session.navigate_to` or using `Link` components. If
            running as website the user can also access these pages directly
            via their URL.

        `on_app_start`: A function that will be called when the app is first
            started. You can use this to perform any initialization tasks
            that need to happen before the app is ready to use.

            The app start will be delayed until this function returns. This
            makes sure initialization is complete before the app is
            displayed to the user. If you would prefer to perform
            initialization in the background try using `asyncio.create_task`
            to run your code in a separate task.

        `on_app_close`: A function that will be called right before the app
            shuts down. You can use this to clean up open resources like for
            example a database connection.

        `on_session_start`: A function that will be called each time a new
            session is created. In the context of a website that would be
            each time a new user visits the site. In the context of a window
            there is only one session, so this will only be called once.

            This function does not block the creation of the session. This
            is to make sure initialization code doesn't accidentally make
            the user wait.

        `on_session_close`: A function that will be called each time a session
            ends. In the context of a website that would be each time a user
            closes their browser tab. In the context of a window this will
            only be called once, when the window is closed.

        `default_attachments`: A list of attachments that will be attached to
            every new session.

        `ping_pong_interval`: Rio periodically sends ping-pong messages
            between the client and server to prevent overzealous proxies
            from closing the connection. The default value should be fine
            for most deployments, but feel free to change it if your hosting
            provider deploys a particularly obnoxious proxy.

        `assets_dir`: The directory where the app's assets are stored. This
            allows you to conveniently access any images or other files that
            are needed by your app. If not specified, Rio will assume the
            assets are stored in a directory called "assets" in the same
            directory as the main Python file.

        `build_connection_lost_message`: A function that creates a "Connection
            lost" error popup, in case you want to override the default one.
        """
        main_file = _get_main_file()

        if name is None:
            name = _get_default_app_name(main_file)

        if icon is None:
            icon = utils.HOSTED_ASSETS_DIR / "rio-logos/rio-logo-square.png"

        if build is None:
            build = rio.PageView

        if theme is None:
            theme = rio.Theme.from_colors()

        # The `main_file` isn't detected correctly if the app is launched via
        # `rio run`. We'll store the user input so that `rio run` can fix the
        # assets dir.
        self._assets_dir = assets_dir
        self.assets_dir = main_file.parent / assets_dir

        self.name = name
        self._build = build
        self._icon = assets.Asset.from_image(icon)
        self.pages = tuple(pages)
        self._on_app_start = on_app_start
        self._on_app_close = on_app_close
        self._on_session_start = on_session_start
        self._on_session_close = on_session_close
        self.default_attachments: MutableSequence[Any] = list(
            default_attachments
        )
        self._theme = theme
        self._build_connection_lost_message = build_connection_lost_message

        if isinstance(ping_pong_interval, timedelta):
            self._ping_pong_interval = ping_pong_interval
        else:
            self._ping_pong_interval = timedelta(seconds=ping_pong_interval)

    def _as_fastapi(
        self,
        *,
        debug_mode: bool,
        running_in_window: bool,
        validator_factory: Callable[[rio.Session], debug.Validator] | None,
        internal_on_app_start: Callable[[], Any] | None,
    ) -> fastapi.FastAPI:
        """
        Internal equivalent of `as_fastapi` that takes additional arguments.
        """
        # Make sure all globals are initialized. This should be done as late as
        # possible, because it depends on which modules have been imported into
        # `sys.modules`.
        maybes.initialize()

        # Build the fastapi instance
        return app_server.AppServer(
            self,
            debug_mode=debug_mode,
            running_in_window=running_in_window,
            validator_factory=validator_factory,
            internal_on_app_start=internal_on_app_start,
        )

    def as_fastapi(self) -> fastapi.FastAPI:
        """
        Return a FastAPI instance that serves this app.

        This method returns a FastAPI instance that serves this app. This allows
        you to run the app with a custom server, such as uvicorn:

        ```py
        app = rio.App(
            name="My App",
            build=MyAppRoot,
        )

        fastapi_app = app.as_fastapi()
        ```

        You can then run this app with uvicorn:

        ```sh
        uvicorn my_app:fastapi_app
        ```
        """
        return self._as_fastapi(
            debug_mode=False,
            running_in_window=False,
            validator_factory=None,
            internal_on_app_start=None,
        )

    def _run_as_web_server(
        self,
        *,
        host: str,
        port: int,
        quiet: bool,
        running_in_window: bool,
        validator_factory: Callable[[rio.Session], debug.Validator]
        | None = None,
        internal_on_app_start: Callable[[], None] | None = None,
        internal_on_server_created: Callable[[uvicorn.Server], None]
        | None = None,
    ) -> None:
        """
        Internal equivalent of `run_as_web_server` that takes additional
        arguments.
        """
        port = utils.ensure_valid_port(host, port)

        # Suppress stdout messages if requested
        kwargs = {}

        if quiet:
            kwargs["log_config"] = {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {},
                "handlers": {},
                "loggers": {},
            }

        # Create the FastAPI server
        fastapi_app = self._as_fastapi(
            debug_mode=False,
            running_in_window=running_in_window,
            validator_factory=validator_factory,
            internal_on_app_start=internal_on_app_start,
        )

        # Suppress stdout messages if requested
        log_level = "error" if quiet else "info"

        config = uvicorn.Config(
            fastapi_app,
            host=host,
            port=port,
            log_level=log_level,
            timeout_graceful_shutdown=1,  # Without a timeout, sometimes the server just deadlocks
        )
        server = uvicorn.Server(config)

        if internal_on_server_created is not None:
            internal_on_server_created(server)

        server.run()

    def run_as_web_server(
        self,
        *,
        host: str = "localhost",
        port: int = 8000,
        quiet: bool = False,
    ) -> None:
        """
        Creates and runs a webserver that serves this app.

        This method creates and immediately runs a webserver that serves this
        app. This is the simplest way to run a Rio app.

        ```py
        app = rio.App(
            name="My App",
            build=MyAppRoot,
        )

        app.run_as_web_server()
        ```

        The will synchronously block until the server is shut down.

        ## Parameters

        host: Which IP address to serve the webserver on. `localhost` will
            make the service only available on your local machine. This is
            the recommended setting if running behind a proxy like nginx.

        port: Which port the webserver should listen to.

        quiet: If `True` Rio won't send any routine messages to `stdout`.
            Error messages will be printed regardless of this setting.
        """
        self._run_as_web_server(
            host=host,
            port=port,
            quiet=quiet,
            running_in_window=False,
        )

    def run_in_browser(
        self,
        *,
        host: str = "localhost",
        port: int | None = None,
        quiet: bool = False,
    ) -> None:
        """
        Runs an internal webserver and opens the app in the default browser.

        This method creates and immediately runs a webserver that serves this
        app, and then opens the app in the default browser. This is a quick and
        easy way to access your app.

        ```py
        app = rio.App(
            name="My App",
            build=MyAppRoot,
        )

        app.run_in_browser()
        ```

        ## Parameters
        host: Which IP address to serve the webserver on. `localhost` will
            make the service only available on your local machine. This is the
            recommended setting if running behind a proxy like nginx.

        port: Which port the webserver should listen to. If not specified,
            Rio will choose a random free port.

        quiet: If `True` Rio won't send any routine messages to `stdout`.
            Error messages will be printed regardless of this setting.
        """
        port = utils.ensure_valid_port(host, port)

        def on_startup() -> None:
            webbrowser.open(f"http://{host}:{port}")

        self._run_as_web_server(
            host=host,
            port=port,
            quiet=quiet,
            running_in_window=False,
            internal_on_app_start=on_startup,
        )

    def run_in_window(
        self,
        quiet: bool = True,
    ) -> None:
        """
        Runs the app in a local window.

        This method creates a window and displays the app in it. This is great
        if you don't want the complexity of running a web server, or wish to
        package your app as a standalone executable.

        ```py
        app = rio.App(
            name="My App",
            build=MyAppRoot,
        )

        app.run_in_window()
        ```

        This method requires the `window` extra. If you don't have it installed,
        you can install it with:

        ```sh
        pip install rio-ui[window]
        ```

        This method will synchronously block until the window is closed.


        ## Parameters

        `quiet`: If `True` Rio won't send any routine messages to `stdout`.
            Error messages will be printed regardless of this setting.
        """
        try:
            import webview  # type: ignore
        except ImportError:
            raise Exception(
                "The `window` extra is required to use `App.run_in_window`."
                " Run `pip install rio-ui[window]` to install it."
            ) from None

        # Unfortunately, WebView must run in the main thread, which makes this
        # tricky. We'll have to banish uvicorn to a background thread, and shut
        # it down when the window is closed.

        host = "localhost"
        port = utils.ensure_valid_port(host, None)
        url = f"http://{host}:{port}"

        # This lock is released once the server is running
        app_ready_event = threading.Event()

        server: uvicorn.Server | None = None

        def on_server_created(serv: uvicorn.Server) -> None:
            nonlocal server
            server = serv

        # Start the server, and release the lock once it's running
        def run_web_server():
            self._run_as_web_server(
                host=host,
                port=port,
                quiet=quiet,
                running_in_window=True,
                internal_on_app_start=app_ready_event.set,
                internal_on_server_created=on_server_created,
            )

        server_thread = threading.Thread(target=run_web_server)
        server_thread.start()

        # Wait for the server to start
        app_ready_event.wait()

        # Start the webview
        try:
            webview.create_window(self.name, url)
            webview.start(debug=os.environ.get("RIO_WEBVIEW_DEBUG") == "1")

        finally:
            assert isinstance(server, uvicorn.Server)

            server.should_exit = True
            server_thread.join()


def _get_main_file() -> Path:
    try:
        main_file = Path(__main__.__file__)
    except AttributeError:
        main_file = Path(sys.argv[0])

    # Find out if we're being executed by uvicorn
    if (
        main_file.name != "__main__.py"
        or main_file.parent != Path(uvicorn.__file__).parent
    ):
        return main_file

    # Find out from which module uvicorn imported the app
    try:
        app_location = next(arg for arg in sys.argv[1:] if ":" in arg)
    except StopIteration:
        return main_file

    module_name, _, _ = app_location.partition(":")
    module = sys.modules[module_name]

    if module.__file__ is None:
        return main_file

    return Path(module.__file__)


def _get_default_app_name(main_file: Path) -> str:
    name = main_file.stem
    if name in ("main", "__main__", "__init__"):
        name = main_file.absolute().parent.stem

    return name.replace("_", " ").title()
