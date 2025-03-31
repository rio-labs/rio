from __future__ import annotations

import asyncio
import contextlib
import functools
import html
import json
import logging
import secrets
import tempfile
import typing as t
import weakref
from datetime import timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

import crawlerdetect
import fastapi
import multipart
import timer_dict
from uniserde import Jsonable, JsonDoc

import rio

from .. import (
    app,
    assets,
    byte_serving,
    data_models,
    errors,
    icon_registry,
    inspection,
    routing,
    serialization,
    utils,
)
from ..errors import AssetError
from ..transports import (
    AbstractTransport,
    FastapiWebsocketTransport,
    MessageRecorderTransport,
)
from ..utils import URL
from .abstract_app_server import AbstractAppServer

try:
    import plotly  # type: ignore (missing import)
except ImportError:
    plotly = None

__all__ = [
    "FastapiServer",
]


P = t.ParamSpec("P")


# Used to identify search engine crawlers (like googlebot) and serve them
# without needing a websocket connection
CRAWLER_DETECTOR = crawlerdetect.CrawlerDetect()


@functools.lru_cache(maxsize=None)
def _build_sitemap(base_url: rio.URL, app: rio.App) -> str:
    # Build a XML site map
    tree = ET.Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
    )

    for relative_url in app._iter_page_urls(include_redirects=False):
        full_url = base_url / relative_url
        url = ET.SubElement(tree, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = str(full_url)

    # Done
    return ET.tostring(tree, encoding="unicode", xml_declaration=True)


@functools.lru_cache(maxsize=None)
def read_frontend_template(template_name: str) -> str:
    """
    Read a text file from the frontend directory and return its content. The
    results are cached to avoid repeated disk access.
    """
    return (utils.FRONTEND_FILES_DIR / template_name).read_text(
        encoding="utf-8"
    )


def add_cache_headers(
    func: t.Callable[P, t.Awaitable[fastapi.Response]],
) -> t.Callable[P, t.Coroutine[None, None, fastapi.Response]]:
    """
    Decorator for routes that serve static files. Ensures that the response has
    the `Cache-Control` header set appropriately.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> fastapi.Response:
        response = await func(*args, **kwargs)
        response.headers["Cache-Control"] = "max-age=31536000, immutable"
        return response

    return wrapper


async def parse_uploaded_files(
    request: fastapi.Request,
) -> list[utils.FileInfo]:
    """
    Custom file upload parsing logic because FastAPI's file uploads are annoying
    in many ways:

    1. We want to return a response to the client as soon as the upload is
       complete, but then fastapi closes the files and they become unusable.
    2. Fastapi gives us *synchronous* file objects.
    3. It's unclear when the upload actually happens. Is the upload already
       complete by the time our code runs, or is the upload somehow still
       running in the background?

    Parsing the request manually gives us full control over the whole thing.
    """
    file_names = list[str]()
    file_types = list[str]()
    file_sizes = list[int]()
    files = list[tempfile.SpooledTemporaryFile]()

    _, options = multipart.parse_options_header(request.headers["content-type"])

    with multipart.PushMultipartParser(options["boundary"]) as parser:
        async for chunk in request.stream():
            for result in parser.parse(chunk):
                if isinstance(result, multipart.MultipartSegment):
                    assert result.filename
                    file_names.append(result.filename)

                    for header, value in result.headerlist:
                        if header.lower() == "content-type":
                            file_types.append(value)
                            break
                    else:
                        raise ValueError("No content-type header found")

                    file_sizes.append(0)
                    files.append(tempfile.SpooledTemporaryFile())
                elif result:  # Non-empty bytearray
                    file_sizes[-1] += len(result)
                    files[-1].write(result)
                else:  # None
                    files[-1].seek(0)

    # Build the list of file infos
    return [
        utils.FileInfo(
            name=file_names[i],
            size_in_bytes=file_sizes[i],
            media_type=file_types[i],
            contents=files[i],
        )
        for i in range(len(files))
    ]


class SpooledTempfilesTarget:
    def __init__(self):
        super().__init__()

        self.files = list[tempfile.SpooledTemporaryFile]()
        self.file_sizes = list[int]()
        self.file_names = list[str]()
        self.file_types = list[str]()

        self._current_file: tempfile.SpooledTemporaryFile | None = None
        self._current_file_size = 0

    def set_multipart_filename(self, filename: str):
        self.file_names.append(filename)

    def set_multipart_content_type(self, content_type: str):
        self.file_types.append(content_type)

    def on_data_received(self, chunk: bytes):
        if self._current_file is None:
            self._current_file = tempfile.SpooledTemporaryFile(
                mode="wb+", max_size=1_000_000
            )

        self._current_file.write(chunk)
        self._current_file_size += len(chunk)

    def on_finish(self):
        if self._current_file is None:
            return

        self._current_file.seek(0)
        self.files.append(self._current_file)
        self.file_sizes.append(self._current_file_size)

        self._current_file = None
        self._current_file_size = 0


class FastapiServer(fastapi.FastAPI, AbstractAppServer):
    def __init__(
        self,
        app_: app.App,
        debug_mode: bool,
        running_in_window: bool,
        internal_on_app_start: t.Callable[[], None] | None,
        base_url: rio.URL | None,
    ) -> None:
        super().__init__(
            title=app_.name,
            summary=None,
            description=app_.description,
            openapi_url=None,
            docs_url=None,
            redoc_url=None,
            lifespan=type(self)._lifespan,
        )
        AbstractAppServer.__init__(
            self,
            app_,
            running_in_window=running_in_window,
            debug_mode=debug_mode,
            base_url=base_url,
        )

        # If a URL was provided, run some sanity checks
        if base_url is not None:
            # If the URL is missing a protocol, yarl doesn't consider it
            # absolute. Perform a separate check for this so that the error
            # message makes more sense.
            if base_url.scheme not in ("http", "https"):
                raise ValueError(
                    "Please provide a URL that starts with either `http://` or `https://`."
                )

            # The URL must be absolute
            if not base_url.is_absolute():
                raise ValueError("The app's base URL must be absolute.")

            # The URL must not contain a query or fragment
            if base_url.query:
                raise ValueError(
                    "The app's base URL cannot contain query parameters."
                )

            if base_url.fragment:
                raise ValueError(
                    "The app's base URL cannot contain a fragment."
                )

        self.internal_on_app_start = internal_on_app_start
        self.base_url = base_url

        # While this Event is unset, no new Sessions can be created. This is
        # used to ensure that no clients (re-)connect while `rio run` is
        # reloading the app.
        self._can_create_new_sessions = asyncio.Event()
        self._can_create_new_sessions.set()

        # The session tokens and Request object for all clients that have made a
        # HTTP request, but haven't yet established a websocket connection. Once
        # the websocket connection is created, these will be turned into
        # Sessions.
        self._latent_session_tokens: dict[str, fastapi.Request] = {}

        # The session tokens for all active sessions. These allow clients to
        # identify themselves, for example to reconnect in case of a lost
        # connection.
        self._active_session_tokens: dict[str, rio.Session] = {}
        self._active_tokens_by_session: dict[rio.Session, str] = {}

        # All assets that have been registered with this session. They are held
        # weakly, meaning the session will host assets for as long as their
        # corresponding Python objects are alive.
        #
        # Assets registered here are hosted under `/asset/temp-{asset_id}`. In
        # addition the server also permanently hosts other "well known" assets
        # (such as javascript dependencies) which are available under public
        # URLS at `/asset/{some-name}`.
        self._assets: weakref.WeakValueDictionary[str, assets.Asset] = (
            weakref.WeakValueDictionary()
        )

        # All pending file uploads. These are stored in memory for a limited
        # time. When a file is uploaded the corresponding future is set.
        self._pending_file_uploads: timer_dict.TimerDict[
            str, asyncio.Future[list[utils.FileInfo]]
        ] = timer_dict.TimerDict(default_duration=timedelta(minutes=15))

        # A function that takes a websocket as input and returns a transport.
        # This allows unit tests to override our transport, since they need
        # access to the sent/received messages.
        self._transport_factory: t.Callable[
            [fastapi.WebSocket], AbstractTransport
        ] = FastapiWebsocketTransport

        # FastAPI
        self.add_api_route("/robots.txt", self._serve_robots, methods=["GET"])
        self.add_api_route(
            "/rio/sitemap.xml", self._serve_sitemap, methods=["GET"]
        )
        self.add_api_route(
            "/rio/favicon.png", self._serve_favicon, methods=["GET"]
        )
        self.add_api_route(
            "/rio/frontend/assets/{asset_id:path}",
            self._serve_frontend_asset,
        )
        self.add_api_route(
            "/rio/assets/special/{asset_id:path}",
            self._serve_special_asset,
            methods=["GET"],
        )
        self.add_api_route(
            "/rio/assets/hosted/{asset_id:path}",
            self._serve_hosted_asset,
            methods=["GET"],
        )
        self.add_api_route(
            "/rio/assets/user/{asset_id:path}",
            self._serve_user_asset,
            methods=["GET"],
        )
        self.add_api_route(
            "/rio/assets/temp/{asset_id:path}",
            self._serve_temp_asset,
            methods=["GET"],
        )
        self.add_api_route(
            "/rio/icon/{icon_name:path}", self._serve_icon, methods=["GET"]
        )
        self.add_api_route(
            "/rio/upload/{upload_token}",
            self._serve_file_upload,
            methods=["PUT"],
        )
        self.add_api_route(
            "/rio/upload-to-component",
            self._serve_file_upload_to_component,
            methods=["PUT"],
        )
        self.add_api_websocket_route("/rio/ws", self._serve_websocket)

        # This route is only used in `debug_mode`. When the websocket connection
        # is interrupted, the frontend polls this route and then either
        # reconnects or reloads depending on whether its session token is still
        # valid (i.e. depending on whether the server was restarted or not)
        self.add_api_route(
            "/rio/validate-token",
            self._serve_token_validation,
        )

        # The route that serves the index.html will be registered later, so that
        # it has a lower priority than user-created routes.
        #
        # This keeps track of whether the fallback route has already been
        # registered.
        self._index_hmtl_route_registered = False

    async def __call__(self, scope, receive, send) -> None:
        # Because this is a single page application, all other routes should
        # serve the index page. The session will determine which components
        # should be shown.
        #
        # This route is registered last, so that it has the lowest priority.
        # This allows the user to add custom routes that take precedence.
        if not self._index_hmtl_route_registered:
            self._index_hmtl_route_registered = True

            self.add_api_route(
                "/{initial_route_str:path}", self._serve_index, methods=["GET"]
            )

        # Delegate to FastAPI
        return await super().__call__(scope, receive, send)

    @contextlib.asynccontextmanager
    async def _lifespan(self):
        await self._on_start()

        # Trigger any internal startup event
        if self.internal_on_app_start is not None:
            self.internal_on_app_start()

        try:
            yield
        finally:
            await self._on_close()

    def external_url_for_user_asset(self, relative_asset_path: Path) -> rio.URL:
        base_url = rio.URL("/") if self.base_url is None else self.base_url
        return base_url / f"assets/user/{relative_asset_path}"

    def weakly_host_asset(self, asset: assets.HostedAsset) -> rio.URL:
        """
        Register an asset with this server. The asset will be held weakly,
        meaning the server will host assets for as long as their corresponding
        Python objects are alive.

        If another asset with the same id is already hosted, it will be
        replaced.

        This returns the **external** URL under which the asset is accessible.
        The URL is absolute if the server had a base URL set, or otherwise
        relative (i.e. starting with `/`).
        """
        self._assets[asset.secret_id] = asset
        base_url = rio.URL("/") if self.base_url is None else self.base_url
        return base_url / f"rio/assets/temp/{asset.secret_id}"

    def _get_all_meta_tags(self, title: str | None = None) -> list[str]:
        """
        Returns all `<meta>` tags that should be added to the app's HTML page.
        This includes auto-generated ones, as well as those stored directly in
        the app.
        """
        if title is None:
            title = self.app.name

        base_url = rio.URL("/") if self.base_url is None else self.base_url

        # Prepare the default tags
        all_tags = {
            "og:title": title,
            "description": self.app.description,
            "og:description": self.app.description,
            "keywords": "python, web, app, rio",
            "image": str(base_url / "rio/favicon.png"),
            "viewport": "width=device-width, height=device-height, initial-scale=1, minimum-scale=1",
        }

        # Add the user-defined meta tags, overwriting any automatically
        # generated ones
        all_tags.update(self.app._custom_meta_tags)

        # Convert everything to HTML
        result: list[str] = []

        for key, value in all_tags.items():
            key = html.escape(key)
            value = html.escape(value)
            result.append(f'<meta name="{key}" content="{value}">')

        return result

    async def _serve_index(
        self,
        request: fastapi.Request,
        initial_route_str: str,
    ) -> fastapi.responses.Response:
        """
        Handler for serving the index HTML page via fastapi.
        """
        # Because Rio apps are single-page, this route serves as the fallback.
        # In addition to legitimate requests for HTML pages, it will also catch
        # a bunch of invalid requests to other resources. To highlight this,
        # throw a 404 if HTML is not explicitly requested.
        #
        # Currently inactive, because this caused issues behind dumb proxies
        # that don't pass on the `accept` header.

        # if not request.headers.get("accept", "").startswith("text/html"):
        #     raise fastapi.HTTPException(
        #         status_code=fastapi.status.HTTP_404_NOT_FOUND,
        #     )

        initial_messages = list[JsonDoc]()

        is_crawler = CRAWLER_DETECTOR.isCrawler(
            request.headers.get("User-Agent")
        )
        if is_crawler:
            # If it's a crawler, immediately create a Session for it. Instead of
            # a websocket connection, outgoing messages are simply appended to a
            # list which will be included in the HTML.
            transport = MessageRecorderTransport()
            initial_messages = transport.sent_messages

            assert request.client is not None, "How can this happen?!"

            requested_url = rio.URL(str(request.url))
            try:
                session = await self.create_session(
                    initial_message=data_models.InitialClientMessage.from_defaults(
                        url=str(requested_url),
                    ),
                    transport=transport,
                    client_ip=request.client.host,
                    client_port=request.client.port,
                    http_headers=request.headers,
                )
            except routing.NavigationFailed:
                raise fastapi.HTTPException(
                    status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Navigation to initial page `{request.url}` has failed.",
                ) from None

            session.close()

            # If a page guard caused a redirect, tell that to the crawler in a
            # language it understands
            if session.active_page_url != requested_url:
                return fastapi.responses.RedirectResponse(
                    str(session.active_page_url)
                )

            session_token = "<crawler>"

            title = " - ".join(
                page.name for page in session.active_page_instances
            )
        else:
            # Create a session token that uniquely identifies this client
            session_token = secrets.token_urlsafe()
            self._latent_session_tokens[session_token] = request

            title = self.app.name

        # Load the template
        html_ = read_frontend_template("index.html")

        html_ = html_.replace(
            "{session_token}",
            session_token,
        )

        html_ = html_.replace(
            '"{child_attribute_names}"',
            json.dumps(
                inspection.get_child_component_containing_attribute_names_for_builtin_components()
            ),
        )

        html_ = html_.replace(
            '"{ping_pong_interval}"',
            str(self.app._ping_pong_interval.total_seconds()),
        )

        html_ = html_.replace(
            '"{debug_mode}"',
            "true" if self.debug_mode else "false",
        )

        html_ = html_.replace(
            '"{running_in_window}"',
            "true" if self.running_in_window else "false",
        )

        html_ = html_.replace(
            '"{initial_messages}"',
            json.dumps(initial_messages),
        )

        if self.base_url is None:
            html_base_url = "/"
        else:
            html_base_url = str(self.base_url)
            html_base_url = html_base_url.rstrip("/") + "/"

        html_ = html_.replace(
            "/rio-base-url-placeholder/",
            html_base_url,
        )

        theme = self.app._theme
        if isinstance(theme, tuple):
            light_theme_background_color = theme[0].background_color
            dark_theme_background_color = theme[1].background_color
        else:
            light_theme_background_color = theme.background_color
            dark_theme_background_color = theme.background_color

        html_ = html_.replace(
            "{light_theme_background_color}",
            f"#{light_theme_background_color.hexa}",
        )

        html_ = html_.replace(
            "{dark_theme_background_color}",
            f"#{dark_theme_background_color.hexa}",
        )

        # Since the title is user-defined, it might contain placeholders like
        # `{debug_mode}`. So it's important that user-defined content is
        # inserted last.
        html_ = html_.replace(
            "{title}",
            html.escape(title),
        )

        # The placeholder for the metadata uses unescaped `<` and `>` characters
        # to ensure that no user-defined content can accidentally contain this
        # placeholder.
        html_ = html_.replace(
            '<meta name="{meta}" />',
            "\n".join(self._get_all_meta_tags(title)),
        )

        # Respond
        return fastapi.responses.HTMLResponse(html_)

    async def _serve_robots(
        self, request: fastapi.Request
    ) -> fastapi.responses.Response:
        """
        Handler for serving the `robots.txt` file via fastapi.
        """
        # Under which URL is the app hosted?
        if self.base_url is None:
            base_url = URL(str(request.url))
        else:
            base_url = self.base_url

        # FIXME: Disallow internal API routes? Icons, assets, etc?
        content = f"""
User-agent: *
Allow: /

Sitemap: {base_url / "rio/sitemap.xml"}
        """.strip()

        return fastapi.responses.Response(
            content=content,
            media_type="text/plain",
        )

    async def _serve_sitemap(
        self, request: fastapi.Request
    ) -> fastapi.responses.Response:
        """
        Handler for serving the `sitemap.xml` file via fastapi.
        """
        # Under which URL is the app hosted?
        if self.base_url is None:
            base_url = URL(str(request.url)).origin()
        else:
            base_url = self.base_url

        # Respond
        return fastapi.responses.Response(
            content=_build_sitemap(base_url, self.app),
            media_type="application/xml",
        )

    async def _serve_favicon(self) -> fastapi.responses.Response:
        """
        Handler for serving the favicon via fastapi, if one is set.
        """
        # Fetch the favicon. This method is already caching, so it's fine to
        # fetch every time.
        try:
            icon_png_blob = await self.app._fetch_icon_png_blob()
        except IOError as err:
            logging.error(str(err))

            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not load the app icon.",
            ) from err

        # Respond
        return fastapi.responses.Response(
            content=icon_png_blob,
            media_type="image/png",
        )

    async def _serve_frontend_asset(
        self,
        request: fastapi.Request,
        asset_id: str,
    ) -> fastapi.responses.Response:
        response = await self._serve_file_from_directory(
            request,
            utils.FRONTEND_ASSETS_DIR,
            asset_id + ".gz",
        )
        response.headers["content-encoding"] = "gzip"

        return response

    @add_cache_headers
    async def _serve_special_asset(
        self,
        request: fastapi.Request,
        asset_id: str,
    ) -> fastapi.responses.Response:
        # The python plotly library already includes a minified version of
        # plotly.js. Rather than shipping another one, just serve the one
        # included in the library.
        if asset_id == "plotly.min.js":
            if plotly is None:
                return fastapi.responses.Response(status_code=404)

            return fastapi.responses.Response(
                content=plotly.offline.get_plotlyjs(),
                media_type="text/javascript",
            )

        return fastapi.responses.Response(status_code=404)

    async def _serve_hosted_asset(
        self,
        request: fastapi.Request,
        asset_id: str,
    ) -> fastapi.responses.Response:
        return await self._serve_file_from_directory(
            request,
            utils.HOSTED_ASSETS_DIR,
            asset_id,
        )

    async def _serve_user_asset(
        self,
        request: fastapi.Request,
        asset_id: str,
    ) -> fastapi.responses.Response:
        return await self._serve_file_from_directory(
            request,
            self.app.assets_dir,
            asset_id,
        )

    @add_cache_headers
    async def _serve_temp_asset(
        self,
        request: fastapi.Request,
        asset_id: str,
    ) -> fastapi.responses.Response:
        # Get the asset's Python instance. The asset's id acts as a secret, so
        # no further authentication is required.
        try:
            asset = self._assets[asset_id]
        except KeyError:
            return fastapi.responses.Response(status_code=404)

        # Fetch the asset's content and respond
        if isinstance(asset, assets.BytesAsset):
            return byte_serving.range_requests_response(
                request,
                asset.data,
                media_type=asset.media_type,
            )
        elif isinstance(asset, assets.PathAsset):
            return byte_serving.range_requests_response(
                request,
                asset.path,
                media_type=asset.media_type,
            )
        else:
            assert False, f"Unable to serve asset of unknown type: {asset}"

    @add_cache_headers
    async def _serve_file_from_directory(
        self,
        request: fastapi.Request,
        directory: Path,
        asset_id: str,
    ) -> fastapi.responses.Response:
        # Construct the path to the target file
        asset_file_path = directory / asset_id

        # Make sure the path is inside the hosted assets directory
        asset_file_path = asset_file_path.absolute()
        if not asset_file_path.is_relative_to(directory):
            logging.warning(
                f'Client requested asset "{asset_id}" which is not located'
                f" inside the assets directory. Somebody might be trying to"
                f" break out of the assets directory!"
            )
            return fastapi.responses.Response(status_code=404)

        return byte_serving.range_requests_response(
            request,
            data=asset_file_path,
        )

    @add_cache_headers
    async def _serve_icon(self, icon_name: str) -> fastapi.responses.Response:
        """
        Allows the client to request an icon by name. This is not actually the
        mechanism used by the `Icon` component, but allows JavaScript to request
        icons.
        """
        # Get the icon's SVG
        try:
            svg_source = icon_registry.get_icon_svg(icon_name)
        except AssetError:
            return fastapi.responses.Response(status_code=404)

        # Respond
        return fastapi.responses.Response(
            content=svg_source,
            media_type="image/svg+xml",
        )

    async def _serve_file_upload(
        self, upload_token: str, request: fastapi.Request
    ) -> fastapi.Response:
        # Try to find the future for this token
        try:
            future = self._pending_file_uploads.pop(upload_token)
        except KeyError:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                detail="Invalid upload token.",
            )

        # Complete the future
        files = await parse_uploaded_files(request)
        future.set_result(files)

        return fastapi.responses.Response(
            status_code=fastapi.status.HTTP_200_OK
        )

    async def _serve_file_upload_to_component(
        self,
        session_token: str,
        component_id: str,
        request: fastapi.Request,
    ) -> fastapi.Response:
        # Parse the inputs
        try:
            component_id_int = int(component_id)
        except ValueError:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid component ID.",
            )

        # Find the session for this token
        try:
            session = self._active_session_tokens[session_token]
        except KeyError:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token.",
            )

        # Find the component in this session
        #
        # This can reasonably happen without it being an error - the component
        # could've been deleted in the meantime.
        try:
            component = session._weak_components_by_id[component_id_int]
        except KeyError:
            return fastapi.responses.Response(
                status_code=fastapi.status.HTTP_200_OK
            )

        # Does this component even have a handler for file uploads?
        try:
            handler = component._on_file_upload_  # type: ignore
        except AttributeError:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This component does not accept file uploads.",
            )

        # Get all uploaded files
        files = await parse_uploaded_files(request)

        # Let the component handle the files
        await handler(files)

        return fastapi.responses.Response(
            status_code=fastapi.status.HTTP_200_OK
        )

    async def pick_file(
        self,
        session: rio.Session,
        *,
        file_types: list[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        # Create a secret id and register the file upload with the app server
        upload_id = secrets.token_urlsafe()
        future = asyncio.Future[list[utils.FileInfo]]()

        self._pending_file_uploads[upload_id] = future

        # Tell the frontend to upload a file
        base_url = rio.URL("/") if self.base_url is None else self.base_url

        await session._request_file_upload(
            upload_url=str(base_url / f"rio/upload/{upload_id}"),
            file_types=file_types,
            multiple=multiple,
        )

        # Wait for the user to upload files
        files = await future

        # Raise an exception if no files were uploaded
        if not files:
            raise errors.NoFileSelectedError()

        # Ensure only one file was provided if `multiple` is False
        if not multiple and len(files) != 1:
            logging.warning(
                "Client attempted to upload multiple files when `multiple` was False."
            )
            raise errors.NoFileSelectedError()

        # Return the file info
        if multiple:
            return files
        else:
            return files[0]

    async def _serve_token_validation(
        self, request: fastapi.Request, session_token: str
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse(
            session_token in self._active_session_tokens
        )

    @contextlib.contextmanager
    def temporarily_disable_new_session_creation(self):
        self._can_create_new_sessions.clear()

        try:
            yield
        finally:
            self._can_create_new_sessions.set()

    async def _serve_websocket(
        self,
        websocket: fastapi.WebSocket,
        session_token: str,
    ) -> None:
        """
        Handler for establishing the websocket connection and handling any
        messages.
        """
        rio._logger.debug(
            f"Received websocket connection with session token `{session_token}`"
        )

        # Wait until we're allowed to accept new websocket connections. (This is
        # temporarily disable while `rio run` is reloading the app.)
        await self._can_create_new_sessions.wait()

        # Accept the socket. I can't figure out how to access the close reason
        # in JS unless the connection was accepted first, so we have to do this
        # even if we are going to immediately close it again.
        await websocket.accept()

        # Look up the session token. If it is valid the session's duration is
        # refreshed so it doesn't expire. If the token is not valid, don't
        # accept the websocket.
        try:
            request = self._latent_session_tokens.pop(session_token)
        except KeyError:
            # Check if this is a reconnect
            try:
                sess = self._active_session_tokens[session_token]
            except KeyError:
                # Inform the client that this session token is invalid
                await websocket.close(
                    3000,  # Custom error code
                    "Invalid session token.",
                )
                return

            # Check if this session still has a functioning websocket
            # connection.
            #
            # We don't want to be over-eager about rejecting (re-)connections,
            # since there's a chance we simply haven't noticed the interrupted
            # connection yet. Wait a little while.
            #
            # Note: Browsers have a "duplicate tab" feature that can create a
            # 2nd tab with the same session token as the original one. However,
            # JS detects that and avoids re-using the token. So we can use a
            # long timeout here without worrying about making the user wait.
            if sess.running_in_window:
                timeout = 5
            else:
                timeout = 2
            try:
                await asyncio.wait_for(
                    sess._rio_transport.closed_event.wait(), timeout
                )
            except asyncio.TimeoutError:
                await websocket.close(
                    3000,  # Custom error code
                    "Invalid session token.",
                )
                return

            # Replace the session's websocket
            transport = self._transport_factory(websocket)
            await sess._replace_rio_transport(transport)

            # Make sure the client is in sync with the server by refreshing
            # every single component
            await sess._send_all_components_on_reconnect()

        else:
            transport = self._transport_factory(websocket)

            try:
                sess = await self._create_session_from_websocket(
                    session_token, request, websocket, transport
                )
            except fastapi.WebSocketDisconnect:
                # If the websocket disconnected while we were initializing the
                # session, just close it
                return

            self._active_session_tokens[session_token] = sess
            self._active_tokens_by_session[sess] = session_token

        # Apparently the websocket becomes unusable as soon as this function
        # exits, so we must wait until we no longer need the websocket.
        #
        # When exiting `rio run` with Ctrl+C, this task is cancelled and screams
        # loudly in the console. Suppress that by catching the exception.
        try:
            await transport.closed_event.wait()
        except asyncio.CancelledError:
            pass

    async def _create_session_from_websocket(
        self,
        session_token: str,
        request: fastapi.Request,
        websocket: fastapi.WebSocket,
        transport: AbstractTransport,
    ) -> rio.Session:
        assert request.client is not None, "Why can this happen?"

        # Upon connecting, the client sends an initial message containing
        # information about it. Wait for that, but with a timeout - otherwise
        # evildoers could overload the server with connections that never send
        # anything.
        initial_message_json: Jsonable = await asyncio.wait_for(
            websocket.receive_json(),
            timeout=60,
        )

        initial_message = serialization.json_serde.from_json(
            data_models.InitialClientMessage,
            initial_message_json,
        )

        try:
            sess = await self.create_session(
                initial_message,
                transport=transport,
                client_ip=request.client.host,
                client_port=request.client.port,
                http_headers=request.headers,
            )
        except routing.NavigationFailed:
            # TODO: Notify the client? Show an error?
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Navigation to initial page `{request.url}` has failed.",
            ) from None

        return sess

    def _after_session_closed(self, session: rio.Session) -> None:
        super()._after_session_closed(session)

        try:
            session_token = self._active_tokens_by_session.pop(session)
        except KeyError:
            # It must be a session created for a crawler. Those don't get unique
            # session tokens and aren't registered.
            return

        del self._active_session_tokens[session_token]
