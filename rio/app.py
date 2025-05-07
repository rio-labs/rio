from __future__ import annotations

import asyncio
import functools
import inspect
import io
import itertools
import logging
import os
import sys
import tempfile
import threading
import traceback
import types
import typing as t
import webbrowser
from datetime import timedelta
from pathlib import Path

import fastapi
import imy.docstrings
import introspection
import uvicorn
from PIL import Image

import __main__
import rio.global_state

from . import assets, global_state, maybes, routing, utils
from .app_server import fastapi_server
from .utils import ImageLike

__all__ = [
    "App",
]

P = t.ParamSpec("P")
R = t.TypeVar("R")
T = t.TypeVar("T")


DEFAULT_ICON_PATH = utils.HOSTED_ASSETS_DIR / "rio_logos/rio_logo_square.png"


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
                        fill=self.session.theme.hud_palette.foreground,
                        font_weight="bold",
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


def guard_against_rio_run(func: t.Callable[P, R]) -> t.Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if rio.global_state.launched_via_rio_run:
            raise RuntimeError(
                f"`App.{func.__name__}` conflicts with `rio run`. Either delete"
                f' that line, or move it behind a `if __name__ == "__main__":`'
                f" guard."
            )

        return func(*args, **kwargs)

    return wrapper


@t.final
class App:
    """
    Contains all the information needed to run a Rio app.

    Apps group all the information needed for Rio to run your application, such
    as its name, icon, and the pages it contains. Apps also expose several
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
            referenced in a nice, human-readable way. If not specified, Rio will
            try to guess a name based on the name of the main Python file.

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
            every new session. (Except for subclasses of `rio.UserSettings` ll
            sessions share the exact same attachment objects, no copies are
            created. `UserSettings` are read from the settings stored on the
            client's device and unique to each session.)

        `ping_pong_interval`: Rio periodically sends ping-pong messages
            between the client and server to prevent overzealous proxies
            from closing the connection. The default value should be fine
            for most deployments, but feel free to change it if your hosting
            provider deploys a particularly obnoxious proxy.

        `assets_dir`: The directory where the app's assets are stored. This
            allows you to conveniently access any images or other files that
            are needed by your app. If not specified, Rio will assume the
            assets are stored in a directory called "assets" in the same
            directory as the python script that is instantiating the app.

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
            icon = DEFAULT_ICON_PATH

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

        # Initialized lazily, when the icon is first requested
        self._icon_as_png_blob: bytes | None = None

        # All extensions currently registered with the app, by their `id()`s
        self._ids_to_extensions: dict[int, rio.Extension] = {}

        # These keep track of functions which must be called at certain points.
        # They are collected into lists here so they can be called quickly.
        self._extension_on_as_fastapi_handlers: list[
            t.Callable[[rio.ExtensionAsFastapiEvent], None]
        ] = []

        self._extension_on_app_start_handlers: list[
            t.Callable[[rio.ExtensionAppStartEvent], None]
        ] = []
        self._extension_on_app_close_handlers: list[
            t.Callable[[rio.ExtensionAppCloseEvent], None]
        ] = []

        self._extension_on_session_start_handlers: list[
            t.Callable[[rio.ExtensionSessionStartEvent], None]
        ] = []
        self._extension_on_session_close_handlers: list[
            t.Callable[[rio.ExtensionSessionCloseEvent], None]
        ] = []

        self._extension_on_page_change_handlers: list[
            t.Callable[[rio.ExtensionPageChangeEvent], None]
        ] = []

    async def _call_event_handlers(
        self,
        handlers: t.Iterable[t.Callable[[T], t.Any | t.Awaitable[t.Any]]],
        event_data: T,
    ) -> None:
        """
        Calls all event handlers in the given list, guarding against exceptions.
        """

        for handler in handlers:
            # If the handler is available, call it and await it if necessary
            try:
                result = handler(event_data)

                if inspect.isawaitable(result):
                    await result

            # Display and discard exceptions
            except Exception:
                print("Exception in event handler:")
                traceback.print_exc()

    def _call_event_handlers_sync(
        self,
        handlers: t.Iterable[t.Callable[[T], t.Any]],
        event_data: T,
    ) -> None:
        """
        Same as `_call_event_handlers`, but without support for asynchronous
        handlers.
        """

        for handler in handlers:
            # If the handler is available, call it and await it if necessary
            try:
                handler(event_data)

            # Display and discard exceptions
            except Exception:
                print("Exception in event handler:")
                traceback.print_exc()

    @imy.docstrings.mark_as_private
    async def _fetch_icon_png_blob(self) -> bytes:
        """
        Fetches the app's icon as a PNG blob.

        The result is cached. It will be loaded the first time you call this
        method, and then returned immediately on subsequent calls. If fetching
        the icon fails, the error is logged and the default icon used.
        """

        # Already cached?
        if isinstance(self._icon_as_png_blob, bytes):
            return self._icon_as_png_blob

        # Nope, get it
        try:
            icon_blob, _ = await self._icon.try_fetch_as_blob()

            input_buffer = io.BytesIO(icon_blob)
            output_buffer = io.BytesIO()

            with Image.open(input_buffer) as image:
                image.save(output_buffer, format="png")

            self._icon_as_png_blob = output_buffer.getvalue()

        # Loading has failed. Use the default icon.
        except Exception:
            if isinstance(self._icon, assets.PathAsset):
                logging.error(
                    f"Could not fetch the app's icon from {self._icon.path.absolute()}"
                )
            elif isinstance(self._icon, assets.UrlAsset):
                logging.error(
                    f"Could not fetch the app's icon from {self._icon.url}"
                )
            else:
                logging.error("Could not fetch the app's icon")

            assert DEFAULT_ICON_PATH.suffix == ".png", (
                "The default icon must be PNG"
            )
            self._icon_as_png_blob = DEFAULT_ICON_PATH.read_bytes()

        # Done!
        return self._icon_as_png_blob

    @imy.docstrings.mark_as_private
    async def _fetch_icon_as_png_path(self) -> Path:
        """
        Fetches the app's icon and returns the path to it, as PNG file. This
        will take care of fetching it (if needed) and converting it to PNG.

        If the icon file isn't local, it will be stored in a temporary
        directory. Note that since the result isn't a context manager, the file
        won't ever be deleted.

        If fetching the icon fails, the error is logged and the default icon is
        used.
        """
        # If the icon is a local PNG file, use it directly
        if (
            isinstance(self._icon, assets.PathAsset)
            and self._icon.path.suffix == ".png"
            and self._icon.path.exists()
        ):
            return self._icon.path

        # Otherwise fetch it. This operation doesn't fail, as it already imputes
        # the default icon if fetching fails.
        png_blob = await self._fetch_icon_png_blob()

        # Dump it to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as file:
            file.write(png_blob)

        return Path(file.name)

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

    def _iter_page_urls(
        self,
        *,
        include_redirects: bool,
    ) -> t.Iterator[str]:
        """
        Generates valid page URLs for this app. If the possible values for
        placeholders are known (such as with `Literal`s) then all possible
        combinations are generated. Otherwise, the URL is skipped.

        Can be used to generate a sitemap, test that no pages crash, etc.

        ## Parameters

        `include_redirects`: Whether to include URLs for `rio.Redirect` pages.
        """

        def urls_for_pages(
            pages: t.Iterable[rio.ComponentPage | rio.Redirect],
        ) -> t.Iterator[str]:
            for page in pages:
                if isinstance(page, rio.ComponentPage):
                    yield from urls_for_component_page(page)

                elif include_redirects and isinstance(page, rio.Redirect):
                    yield page.url_segment

        def urls_for_component_page(page: rio.ComponentPage) -> t.Iterator[str]:
            # A page can have multiple URLs if it has path parameters. Start by
            # creating a list of URLs that are valid for this page.
            if page._url_pattern.path_parameter_names:
                # If this page has path parameters, we don't know what it
                # considers a valid URL. One exception are Literals - we simply
                # insert every allowed value into the URL.
                options = dict[str, t.Sequence[str]]()

                for parameter in page._url_pattern.path_parameter_names:
                    parser = page._url_parameter_parsers[parameter]

                    try:
                        options[parameter] = parser.list_valid_values()
                    except ValueError:
                        # If a parser can't reasonably list all of its valid
                        # values, then we simply won't generate any URLs for
                        # this page at all.
                        return

                urls = (
                    page._url_pattern.build_url(dict(zip(options, combination)))
                    for combination in itertools.product(*options.values())
                )
            else:
                urls = [page.url_segment]

            # Now that we know all the URLs for *this* page, we need the urls
            # for the sub-pages.
            #
            # There is a distinction here: If a page has children, then the page
            # url *must* be combined with a child url. For example, if `/foo`
            # has a sub-page `/bar`, then `/foo/bar` is a valid URL, but `/foo`
            # is not! (Unless foo also has a sub-page with `url_segment=""`.)
            if not page.children:
                yield from urls
                return

            child_urls = [
                "/" + child_url for child_url in urls_for_pages(page.children)
            ]

            # Finally, combine all of our own URLs with the URLs of the child
            # pages
            for url in urls:
                for child_url in child_urls:
                    yield url + child_url

        # Remove trailing slashes. (This has no functional purpose, we just
        # don't want to output redundant slashes.)
        return (url.rstrip("/") for url in urls_for_pages(self.pages))

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
        result = fastapi_server.FastapiServer(
            self,
            debug_mode=debug_mode,
            running_in_window=running_in_window,
            internal_on_app_start=internal_on_app_start,
            base_url=base_url,
        )

        # Call all extension event handlers
        self._call_event_handlers_sync(
            self._extension_on_as_fastapi_handlers,
            rio.ExtensionAsFastapiEvent(
                self,
                result,
            ),
        )

        return result

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
        host: str = "localhost",
        port: int = 8000,
        quiet: bool = False,
        running_in_window: bool = False,
        internal_on_app_start: t.Callable[[], None] | None = None,
        internal_on_server_created: t.Callable[[uvicorn.Server], None]
        | None = None,
        base_url: rio.URL | str | None = None,
        debug_mode: bool = False,
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
            debug_mode=debug_mode,
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

    @guard_against_rio_run
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

        `host`: Which IP address to serve the webserver on. `localhost` will
            make the service only available on your local machine. This is
            the recommended setting if running behind a proxy like nginx.

        `port`: Which port the webserver should listen to.

        `quiet`: If `True` Rio won't send any routine messages to `stdout`.
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
            debug_mode=False,
        )

    @guard_against_rio_run
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
        `host`: Which IP address to serve the webserver on. `localhost` will
            make the service only available on your local machine. This is the
            recommended setting if running behind a proxy like nginx.

        `port`: Which port the webserver should listen to. If not specified,
            Rio will choose a random free port.

        `quiet`: If `True` Rio won't send any routine messages to `stdout`.
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
            debug_mode=False,
        )

    @guard_against_rio_run
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

        ```python
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

        `maximized`: Whether to maximize the app window.

        `fullscreen`: Whether to open the app window in fullscreen mode.

        `width`: The default width of the app window.

        `height`: The default height of the app window.
        """
        return self._run_in_window(
            quiet=quiet,
            maximized=maximized,
            fullscreen=fullscreen,
            width=width,
            height=height,
            debug_mode=False,
        )

    def _run_in_window(
        self,
        *,
        quiet: bool = True,
        maximized: bool = False,
        fullscreen: bool = False,
        width: float | None = None,
        height: float | None = None,
        debug_mode: bool = False,
    ) -> None:
        """
        Internal equivalent of `run_in_window` that takes additional arguments.
        """
        try:
            from . import webview_shim
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
                debug_mode=debug_mode,
            )

        server_thread = threading.Thread(target=run_web_server)
        server_thread.start()

        # Wait for the server to start
        app_ready_event.wait()

        # Problem: width and height are given in rem, but we need them in
        # pixels. We'll use pywebview's evaluate_js to find out as soon as the
        # window has been created, and then update the window size accordingly.
        def update_window_size() -> None:
            if width is None and height is None:
                return

            pixels_per_rem = window.evaluate_js("""
let measure = document.createElement('div');
measure.style.height = '1rem';

let pixels_per_rem = measure.getBoundingClientRect().height * window.devicePixelRatio;

measure.remove();

pixels_per_rem;
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

        # Fetch the icon
        icon_path = asyncio.run(self._fetch_icon_as_png_path())

        # Start the webview
        try:
            window = webview_shim.create_window(
                self.name,
                url,
                maximized=maximized,
                fullscreen=fullscreen,
            )
            webview_shim.start_mainloop(
                update_window_size,
                icon=icon_path,
            )

        finally:
            assert isinstance(server, uvicorn.Server)

            server.should_exit = True
            server_thread.join()

    def _add_extension(self, /, extension: rio.Extension) -> None:
        """
        Registers an extension with the app.

        This function adds an extension to the app, giving the extension access
        to the app's events.

        ## Raises

        `ValueError`: If this extension is already registered with the app.
        """
        # Make sure this particular extension isn't already registered
        if id(extension) in self._ids_to_extensions:
            raise ValueError(
                f"Extension {extension} is already registered with the app"
            )

        # Register the extension
        self._ids_to_extensions[id(extension)] = extension

        # Gather all of the the extension's event handlers. This will put them
        # in a dictionary, grouped by their event tag.
        handlers = rio.extension_event._collect_tagged_methods_recursive(
            extension
        )

        # The values in the dictionary above aren't just the callables - they
        # allow for an optional argument that was passed to the decorator. Since
        # most events don't use that, use a helper function to strip it again.
        def extend_with_first_in_tuples(target: list, tuples) -> None:
            for tup in tuples:
                assert len(tup) == 2
                assert tup[1] is None

                target.append(tup[0])

        extend_with_first_in_tuples(
            self._extension_on_as_fastapi_handlers,
            handlers.get(
                rio.extension_event.ExtensionEventTag.ON_AS_FASTAPI, []
            ),
        )

        extend_with_first_in_tuples(
            self._extension_on_app_start_handlers,
            handlers.get(
                rio.extension_event.ExtensionEventTag.ON_APP_START, []
            ),
        )
        extend_with_first_in_tuples(
            self._extension_on_app_close_handlers,
            handlers.get(
                rio.extension_event.ExtensionEventTag.ON_APP_CLOSE, []
            ),
        )

        extend_with_first_in_tuples(
            self._extension_on_session_start_handlers,
            handlers.get(
                rio.extension_event.ExtensionEventTag.ON_SESSION_START, []
            ),
        )
        extend_with_first_in_tuples(
            self._extension_on_session_close_handlers,
            handlers.get(
                rio.extension_event.ExtensionEventTag.ON_SESSION_CLOSE, []
            ),
        )

        extend_with_first_in_tuples(
            self._extension_on_page_change_handlers,
            handlers.get(
                rio.extension_event.ExtensionEventTag.ON_PAGE_CHANGE, []
            ),
        )

    def add_default_attachment(self, attachment: t.Any, /) -> None:
        """
        Adds a new default attachment to the app.

        Default attachments are automatically attached to every new session
        created by the app. This is useful for providing shared resources to
        all sessions, such as database connections or other global state.

        This function adds a new default attachment to the app, causing it to
        be attached to every new session.

        ## Parameters

        `attachment`: The value to attach to the session. You can retrieve it
            later by its type.

        ## Raises

        `TypeError`: If the attachment is a class instead of an instance of a
            class.
        """
        if isinstance(attachment, type):
            raise TypeError(
                f"Default attachments should be instances, not types. Did you mean to type `add_default_attachment({attachment.__name__}())`?"
            )

        self.default_attachments.append(attachment)

    def __getitem__(self, key: type[T], /) -> T:
        """
        Retrieves a default attachment by its type.

        Default attachments are automatically attached to every new session
        created by the app. This is useful for providing shared resources to
        all sessions, such as database connections or other global state.

        This function retrieves a default attachment from this app. To attach
        values to the session, use `App.add_default_attachment`.

        ## Parameters

        `key`: The class of the value you want to retrieve.

        ## Raises

        `KeyError`: If no attachment of this type is attached to the session.
        """
        for attachment in self.default_attachments:
            if isinstance(attachment, key):
                return attachment

        raise KeyError(key)
