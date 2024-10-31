from __future__ import annotations

import functools
import os
import sys
import threading
import types
import typing as t
import webbrowser
from datetime import timedelta
from pathlib import Path

import fastapi
import introspection
import uvicorn

import __main__
import rio

from . import assets, global_state, maybes, routing, utils
from .app_server import fastapi_server
from .utils import ImageLike

__all__ = [
    "App",
]


def make_default_connection_lost_component() -> rio.Component:
    class DefaultConnectionLostComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Rectangle(
                content=rio.Row(
                    rio.Icon(
                        "material/signal_disconnected",
                        fill="danger",
                        min_width=1.6,
                        min_height=1.6,
                    ),
                    rio.Text(
                        "Disconnected",
                        selectable=False,
                        style=rio.TextStyle(
                            fill=self.session.theme.hud_palette.foreground,
                            font_weight="bold",
                        ),
                    ),
                    spacing=0.8,
                    margin_x=2.5,
                    margin_y=1.5,
                ),
                fill=self.session.theme.hud_palette.background,
                corner_radius=99999,
                shadow_color=self.session.theme.shadow_color,
                shadow_radius=0.6,
                shadow_offset_y=0.15,
                margin_top=3,
                align_x=0.5,
                align_y=0.0,
            )

    return DefaultConnectionLostComponent()


@t.final
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

    `description`: A short, human-readable description of the app. This can
        show up in search engines, social media sites and similar.

    `pages`: The pages that make up this app. You can navigate between these
        using `Session.navigate_to` or using `Link` components. If running
        as website the user can also access these pages directly via their
        URL.

    `assets_dir`: The directory where the app's assets are stored. This allows
        you to conveniently access any images or other files that are needed
        by your app.

    `meta_tags`: Arbitrary key-value pairs that will be included in the HTML
        header of the app. These are used by search engines and social media
        sites to display information about your page, such as the title and a
        short description.
    """

    # Type hints so the documentation generator knows which fields exist
    name: str
    description: str
    assets_dir: Path
    pages: t.Sequence[rio.ComponentPage | rio.Redirect]
    meta_tags: dict[str, str]

    def __init__(
        self,
        *,
        build: t.Callable[[], rio.Component] | None = None,
        name: str | None = None,
        description: str | None = None,
        icon: ImageLike | None = None,
        pages: t.Iterable[rio.ComponentPage | rio.Redirect]
        | os.PathLike
        | str
        | None = None,
        on_app_start: rio.EventHandler[App] = None,
        on_app_close: rio.EventHandler[App] = None,
        on_session_start: rio.EventHandler[rio.Session] = None,
        on_session_close: rio.EventHandler[rio.Session] = None,
        default_attachments: t.Iterable[t.Any] = (),
        ping_pong_interval: int | float | timedelta = timedelta(seconds=50),
        assets_dir: str | os.PathLike | None = None,
        theme: rio.Theme | tuple[rio.Theme, rio.Theme] | None = None,
        build_connection_lost_message: t.Callable[
            [], rio.Component
        ] = make_default_connection_lost_component,
        meta_tags: dict[str, str] = {},
    ) -> None:
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

        `description`: A short, human-readable description of the app. This
            can show up in search engines, social media sites and similar.

        `icon`: The "favicon" to display for this app. This is a little image
            that shows up in the title bars of windows, browser tabs and similar
            similar.

        `theme`: The `Theme` for the app. You can also pass in a tuple of two
            themes, which will be used as the light mode theme and the dark mode
            theme.

        `pages`: The pages that make up this app. You can navigate between
            these using `Session.navigate_to` or using `Link` components. If
            running as website the user can also access these pages directly
            via their URL.

            Per default, rio scans your project's "pages" directory for
            components decorated with `@rio.page` and turns them into pages. To
            override the location of this directory, you can provide a custom
            path.

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

            Please note that the session is not fully initialized yet when this
            function is called. In particular, the session's `active_page_url`
            is set to whichever URL the client has requested, but before the
            guards have had a chance to redirect the user to another page.

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

        `meta_tags`: Arbitrary key-value pairs that will be included in the
            HTML header of the app. These are used by search engines and social
            media sites to display information about your page, such as the
            title and a short description.
        """
        # A common mistake is to pass types instead of instances to
        # `default_attachments`. Catch that, scream and die.
        for attachment in default_attachments:
            if isinstance(attachment, type):
                raise TypeError(
                    f"Default attachments should be instances, not types. Did you mean to type `{attachment.__name__}()`?"
                )

        if description is None:
            description = "A Rio web-app written in 100% Python"

        if icon is None:
            icon = utils.HOSTED_ASSETS_DIR / "rio_logos/rio_logo_square.png"

        if build is None:
            build = rio.components.default_root_component.DefaultRootComponent

        if theme is None:
            theme = rio.Theme.from_colors()

        if name is None:
            name = self._infer_app_name()

        if assets_dir is None:
            assets_dir = self._base_dir_for_relative_paths / "assets"
        else:
            assets_dir = self._base_dir_for_relative_paths / assets_dir

        if pages is None:
            pages = self._infer_pages()
        elif isinstance(pages, (os.PathLike, str)):
            pages = routing.auto_detect_pages(
                self._base_dir_for_relative_paths / pages
            )
        else:
            pages = list(pages)

        self.name = name
        self.description = description
        self.assets_dir = assets_dir
        self.pages = pages
        self._build = build
        self._icon = assets.Asset.from_image(icon)
        self._on_app_start = on_app_start
        self._on_app_close = on_app_close
        self._on_session_start = on_session_start
        self._on_session_close = on_session_close
        self.default_attachments = list(default_attachments)
        self._theme = theme
        self._build_connection_lost_message = build_connection_lost_message
        self._custom_meta_tags = meta_tags

        if isinstance(ping_pong_interval, timedelta):
            self._ping_pong_interval = ping_pong_interval
        else:
            self._ping_pong_interval = timedelta(seconds=ping_pong_interval)

    @functools.cached_property
    def _main_file_path(self) -> Path:
        if global_state.rio_run_app_module_path is not None:
            main_file = global_state.rio_run_app_module_path
        else:
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

        if module.__file__ is not None:
            return Path(module.__file__)

        return main_file

    @functools.cached_property
    def _calling_module(self) -> types.ModuleType:
        call_frame = introspection.CallFrame.current()

        while call_frame is not None:
            module_name = call_frame.globals["__name__"]

            if module_name.startswith("rio.") or module_name == "functools":
                call_frame = call_frame.parent
                continue

            return sys.modules[module_name]

        assert False, "Calling module could not be found?!"

    @functools.cached_property
    def _base_dir_for_relative_paths(self) -> Path:
        if self._calling_module.__file__ is None:
            # TODO: What do we do in this case?
            return Path.cwd()

        return Path(self._calling_module.__file__).parent

    def _infer_app_name(self) -> str:
        main_file_path = self._main_file_path

        name = main_file_path.stem
        if name in ("main", "__main__", "__init__"):
            name = main_file_path.absolute().parent.name

        return name.replace("_", " ").title()

    def _infer_pages(self) -> list[rio.ComponentPage]:
        pages_dir = self._base_dir_for_relative_paths / "pages"

        # No `pages` folder exists? No pages, then.
        if not pages_dir.exists():
            return []

        # In order to import the pages correctly correctly we must know the
        # correct module name to use. We know that the `pages` folder is a
        # sibling of `self._calling_module`, so we can deduce the correct module
        # name based on that.
        if self._calling_module.__file__ is None:
            # TODO: Display a warning?
            return []

        caller_file_path = Path(self._calling_module.__file__)

        # Careful: If the calling file is the `__init__.py` of a package, the
        # `__init__` part is not included in the module's `__name__`.
        if (
            caller_file_path.name == "__init__.py"
            and self._calling_module.__name__.rpartition(".")[2] != "__init__"
        ):
            package_name = self._calling_module.__name__
        else:
            package_name = self._calling_module.__name__.rpartition(".")[0]

        if package_name:
            package_name += ".pages"
        else:
            package_name = "pages"

        return routing.auto_detect_pages(pages_dir, package=package_name)

    def _as_fastapi(
        self,
        *,
        debug_mode: bool,
        running_in_window: bool,
        internal_on_app_start: t.Callable[[], t.Any] | None,
        base_url: rio.URL | str | None,
    ) -> fastapi.FastAPI:
        """
        Internal equivalent of `as_fastapi` that takes additional arguments.
        """
        # Make sure all globals are initialized. This should be done as late as
        # possible, because it depends on which modules have been imported into
        # `sys.modules`.
        maybes.initialize()

        # For convenience, this method can accept a string as the base URL.
        # Convert that
        if isinstance(base_url, str):
            base_url = rio.URL(base_url)

        # Build the fastapi instance
        return fastapi_server.FastapiServer(
            self,
            debug_mode=debug_mode,
            running_in_window=running_in_window,
            internal_on_app_start=internal_on_app_start,
            base_url=base_url,
        )

    def as_fastapi(
        self,
        *,
        base_url: rio.URL | str | None = None,
    ) -> fastapi.FastAPI:
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

        You can then run this app via `uvicorn`:

        ```sh
        uvicorn my_app:fastapi_app
        ```

        ## Parameters

        `base_url`: The base URL at which the app will be served. This is useful
            if you're running the app behind a reverse proxy like nginx and want
            to serve the app at a subpath. If provided, the URL must be absolute
            and cannot contain query parameters or fragments.

            **This parameter is experimental. Please report any issues you
            encounter. Minor releases may change the behavior of this
            parameter.**
        """
        return self._as_fastapi(
            debug_mode=False,
            running_in_window=False,
            internal_on_app_start=None,
            base_url=base_url,
        )

    def _run_as_web_server(
        self,
        *,
        host: str,
        port: int,
        quiet: bool,
        running_in_window: bool,
        internal_on_app_start: t.Callable[[], None] | None = None,
        internal_on_server_created: t.Callable[[uvicorn.Server], None]
        | None = None,
        base_url: rio.URL | str | None = None,
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
            internal_on_app_start=internal_on_app_start,
            base_url=base_url,
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
        base_url: rio.URL | str | None = None,
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

        `base_url`: The base URL at which the app will be served. This is useful
            if you're running the app behind a reverse proxy like nginx and want
            to serve the app at a subpath. If provided, the URL must be absolute
            and cannot contain query parameters or fragments.

            **This parameter is experimental. Please report any issues you
            encounter. Minor releases may change the behavior of this
            parameter.**
        """
        self._run_as_web_server(
            host=host,
            port=port,
            quiet=quiet,
            running_in_window=False,
            base_url=base_url,
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
        *,
        quiet: bool = True,
        maximized: bool = False,
        fullscreen: bool = False,
        width: float | None = None,
        height: float | None = None,
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
        pip install "rio-ui[window]"
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
                """ Run `pip install "rio-ui[window]"` to install it."""
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
        def run_web_server() -> None:
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

        # Problem: width and height are given in rem, but we need them in
        # pixels. We'll use pywebview's execute_js to find out as soon as the
        # window has been created, and then update the window size accordingly.
        def update_window_size():
            if width is None and height is None:
                return

            pixels_per_rem = window.evaluate_js("""
let measure = document.createElement('div');
measure.style.height = '1rem';

let pixels_per_rem = measure.getBoundingClientRect().height *
window.devicePixelRatio;

measure.remove();

pixels_per_rem
""")

            if width is None:
                width_in_pixels = window.width
            else:
                width_in_pixels = round(width * pixels_per_rem)

            if height is None:
                height_in_pixels = window.height
            else:
                height_in_pixels = round(height * pixels_per_rem)

            window.set_window_size(width_in_pixels, height_in_pixels)

        # Start the webview
        try:
            window = webview.create_window(
                self.name,
                url,
                maximized=maximized,
                fullscreen=fullscreen,
            )
            webview.start(
                update_window_size,
                debug=os.environ.get("RIO_WEBVIEW_DEBUG") == "1",
            )

        finally:
            server = t.cast(
                uvicorn.Server, server
            )  # Prevents "unreachable code" warning
            assert isinstance(server, uvicorn.Server)

            server.should_exit = True
            server_thread.join()
