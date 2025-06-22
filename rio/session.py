from __future__ import annotations

import asyncio
import collections
import copy
import inspect
import json
import logging
import pathlib
import random
import shutil
import string
import time
import traceback
import typing as t
import weakref
from datetime import tzinfo

import introspection
import ordered_set
import revel
import starlette.datastructures
import unicall
import unicall.json_rpc
from identity_containers import IdentityDefaultDict, IdentitySet
from uniserde import Jsonable, JsonDoc

import rio

from . import (
    app_server,
    assets,
    data_models,
    deprecations,
    errors,
    fills,
    global_state,
    inspection,
    nice_traceback,
    routing,
    serialization,
    text_style,
    theme,
    user_settings_module,
    utils,
)
from .components import dialog_container, fundamental_component, root_components
from .data_models import BuildData, UnittestComponentLayout
from .observables import Dataclass
from .observables.observable_property import AttributeBinding
from .observables.session_attachments import SessionAttachments
from .observables.session_property import SessionProperty
from .transports import (
    AbstractTransport,
    TransportClosedIntentionally,
    TransportInterrupted,
)

__all__ = ["Session"]


T = t.TypeVar("T")


class WontSerialize(Exception):
    pass


class Session(unicall.Unicall, Dataclass):
    """
    Represents a single client connection to the app.

    A session corresponds to a single connection to a client. It maintains all
    state related to this client including local settings, the currently active
    page, and others.

    Sessions are created automatically by the app and should not be created
    manually.

    ## Attributes

    `timezone`: The timezone the connected client is in. You can use this to
        display times in the client's local time.

    `screen_width`: How many units the client's screen is wide. Note that this
        is specifically the screen and not the window your app is running in. If
        you're interested in pixels rather than font heights, multiply this
        value with `self.session.pixels_per_font_height`.

    `screen_height`: How many units the client's screen is high. Note that this
        is specifically the screen and not the window your app is running in. If
        you're interested in pixels rather than font heights, multiply this
        value with `self.session.pixels_per_font_height`.

    `window_width`: The width of the client's window in font heights. Like all
        units in Rio, this is measured in font heights.

    `window_height`: The height of the client's window in font heights. Like all
        units in Rio, this is measured in font heights.

    `pixels_per_font_height`: How many pixels a font height is. This can be used
        to convert font heights to pixels or the other way around.

        (Attention web-devs: Note that this are real pixels, as would be on the
        user's screen, not CSS pixels.)

    `scroll_bar_size`: The width (or height if scrolling horizontally) of the
        scroll bar in font heights. This can sometimes be useful if you want to
        align items with those in a scroll container or leave empty space for
        the bar.

    `primary_pointer_type`: The typical way pointer (i.e. mouse, touch, stylus)
        inputs will be made on this device. If this is `mouse`, you can expect
        the user to be able to give precise inputs and hover over elements. If
        `touch` this is likely not the case, and your layout might want to be
        more spacious.

        Possible values are `"mouse"` and `"touch"`.

        Warning: This is the **primary** way pointer inputs will be made. A
            device may well be equipped with a touch screen, a mouse and a pen
            tablet all at the same time. So this value doesn't in any way
            guarantee that no inputs with other devices will be made.

        Warning: This literal shouldn't be seen as complete. Future versions of
            Rio may add additional values as new types of devices get popular.
            Extending this literal is not considered a compatibility break and
            may happen even in minor versions. If you rely on this value, it's
            good practice to add a fallback for unknown strings.


    `base_url`: This is the URL the app's home page is hosted at, as seen from
        the client. So if the user needs to type `https://example.com/my-app/`
        to see the app, this will be `https://example.com/my-app/`. Note that
        this is not necessarily the URL Python gets to see in HTTP requests, as
        it is common practice to have a reverse proxy rewrite the URLs of HTTP
        requests.

    `theme`: The theme that the client is using. If you've passed both a light
        and dark theme into the app, this will be the one which is actually
        used by the client.

    `client_ip`: The IP address of the connected client. Only available when
        running as a website.

    `client_port`: The port of the connected client. Only available when running
        as a website.

    `http_headers`: The HTTP headers sent by the client. This is a read-only,
        case-insensitive dictionary.

    `preferred_languages`: The languages preferred by the client. Use this to
        present content in the most convenient language for your users. The
        values are ordered with the most preferred language first.

        This always contains at least one langauge.

        The values are in the format `language-region`, e.g. `en-US` for
        American English. The full specification is defined in
        [RFC 5646](https://datatracker.ietf.org/doc/html/rfc5646).
    """

    _observable_property_factory_ = SessionProperty

    # Type hints so the documentation generator knows which fields exist
    timezone: tzinfo
    preferred_languages: t.Sequence[str]

    screen_width: float
    screen_height: float

    window_width: float
    window_height: float

    pixels_per_font_height: float
    scroll_bar_size: float

    primary_pointer_type: t.Literal["mouse", "touch"]

    theme: rio.Theme

    http_headers: t.Mapping[str, str]

    # These are internal but must be annotated so that they become
    # ObservableProperties
    _active_page_url: rio.URL
    _active_page_instances: tuple[rio.ComponentPage, ...]
    _active_page_instances_and_path_arguments: tuple[
        tuple[rio.ComponentPage, dict[str, object]], ...
    ]

    def __init__(
        self,
        app_server_: app_server.AbstractAppServer,
        transport: AbstractTransport,
        client_ip: str,
        client_port: int,
        http_headers: starlette.datastructures.Headers,
        timezone: tzinfo,
        preferred_languages: t.Iterable[str],
        month_names_long: tuple[
            str, str, str, str, str, str, str, str, str, str, str, str
        ],
        day_names_long: tuple[str, str, str, str, str, str, str],
        date_format_string: str,
        first_day_of_week: int,
        decimal_separator: str,  # == 1 character
        thousands_separator: str,  # <= 1 character
        screen_width: float,
        screen_height: float,
        window_width: float,
        window_height: float,
        pixels_per_font_height: float,
        scroll_bar_size: float,
        primary_pointer_type: t.Literal["mouse", "touch"],
        base_url: rio.URL,
        active_page_url: rio.URL,
        theme_: theme.Theme,
    ) -> None:
        super().__init__(
            transport=unicall.json_rpc.JsonRpcTransport(
                send=self.__send_message,
                receive=self.__receive_message,
                serde=serialization.json_serde,
                parameter_format="list",
                json_dumps=serialization.serialize_json,
            )
        )

        # Sessions automatically rebuild components whenever necessary. To make
        # this possible, we need to create a background task that waits for a
        # component to become dirty. It can do that by waiting for this event,
        # which is triggered by our observables.
        self._refresh_required_event = asyncio.Event()

        # Map observables to components that accessed them. Whenever an
        # observable's value changes, the corresponding components will be
        # rebuilt.
        self._components_by_accessed_object: weakref.WeakKeyDictionary[
            object, weakref.WeakSet[rio.Component]
        ] = weakref.WeakKeyDictionary()
        self._components_by_accessed_property: weakref.WeakKeyDictionary[
            object, dict[str, weakref.WeakSet[rio.Component]]
        ] = weakref.WeakKeyDictionary()
        self._components_by_accessed_item: weakref.WeakKeyDictionary[
            object, dict[object, weakref.WeakSet[rio.Component]]
        ] = weakref.WeakKeyDictionary()

        # Keep track of all observables that have changed since the last refresh
        self._changed_objects = IdentitySet[object]()
        self._changed_attributes = IdentityDefaultDict[object, set[str]](set)
        self._changed_items = IdentityDefaultDict[object, IdentitySet[object]](
            IdentitySet[object]
        )

        # Store the app server
        self._app_server = app_server_

        # This attribute is initialized after the Session has been instantiated,
        # because the Session must already exist when the Component is created.
        # Note that this isn't the user's root component, but rather an
        # internally created one.
        self._high_level_root_component: root_components.HighLevelRootComponent

        # These are initialized with dummy values. Once the Session has been
        # instantiated, the page guards will run and then these will be set to
        # the correct values.
        self._active_page_url = active_page_url
        self._active_page_instances_and_path_arguments: tuple[
            tuple[rio.ComponentPage, dict[str, object]], ...
        ] = ()
        self._active_page_instances: tuple[rio.ComponentPage, ...] = ()

        # Components need unique ids, but we don't want them to be globally unique
        # because then people could guesstimate the approximate number of
        # visitors on a server based on how quickly the component ids go up. So
        # each session will assign its components ids starting from 0.
        self._next_free_component_id: int = 0

        # Keep track of the last time we successfully communicated with the
        # client. After a while with no communication we close the session.
        self._last_interaction_timestamp = time.monotonic()

        # Keeps track of running asyncio tasks. This is used to make sure that
        # the tasks are cancelled when the session is closed.
        self._running_tasks: set[asyncio.Task[object]] = set()

        # Keeps track of all PageView instances in this session. PageViews add
        # themselves to this.
        self._page_views: weakref.WeakSet[rio.PageView] = weakref.WeakSet()

        # All components / methods which should be called when the session's
        # page has changed.
        #
        # The methods don't have the component bound yet, so they don't unduly
        # prevent the component from being garbage collected.
        self._page_change_callbacks: weakref.WeakKeyDictionary[
            rio.Component,
            tuple[t.Callable[[rio.Component], None], ...],
        ] = weakref.WeakKeyDictionary()

        # All components / methods which should be called when the session's
        # window size has changed.
        self._on_window_size_change_callbacks: weakref.WeakKeyDictionary[
            rio.Component,
            tuple[t.Callable[[rio.Component], None], ...],
        ] = weakref.WeakKeyDictionary()

        # All fonts which have been registered with the session. This maps the
        # name of the font to the font's assets, which ensures that the assets
        # are kept alive until the session is closed.
        self._registered_font_names: dict[rio.Font, str] = {}
        self._registered_font_assets: dict[rio.Font, list[assets.Asset]] = {}

        # The current transport, though it may be closed
        self._rio_transport = transport

        # Event indicating whether there is an open connection to the client.
        # This starts off set, since the session is created with a valid
        # transport.
        self._is_connected_event = asyncio.Event()
        if not transport.is_closed:
            self._is_connected_event.set()

        # Must be acquired while synchronizing the user's settings
        self._settings_sync_lock = asyncio.Lock()

        # Modifying a setting starts this task that waits a little while and
        # then saves the settings
        self._settings_save_task: asyncio.Task | None = None

        # If `running_in_window`, this contains all the settings loaded from the
        # json file. We need to keep this around so that we can update the
        # settings that have changed and write everything back to the file.
        self._settings_json: JsonDoc = {}

        # If `running_in_window`, this is the current content of the settings
        # file. This is used to avoid needlessly re-writing the file if nothing
        # changed.
        self._settings_json_string: str | None = None

        # If `running_in_window`, this is the timestamp of when the settings
        # were last saved.
        self._last_settings_save_time: float = -float("inf")

        # A dict of {build_function: error_message}. This is cleared at
        # the start of every refresh, and tracks which build functions failed.
        # Used for unit testing.
        self._crashed_build_functions = dict[t.Callable, str]()

        # Weak dictionaries to hold additional information about components.
        # These are split in two to avoid the dictionaries keeping the
        # components alive. Notice how both dictionaries are weak on the actual
        # component.
        #
        # Never access these directly. Instead, use helper functions
        # - `lookup_component`
        # - `lookup_component_data`
        self._weak_components_by_id: weakref.WeakValueDictionary[
            int, rio.Component
        ] = weakref.WeakValueDictionary()

        # Stores newly created components. These need to be built/refreshed.
        self._newly_created_components = set[rio.Component]()

        # HTML components have source code which must be evaluated by the client
        # exactly once. Keep track of which components have already sent their
        # source code.
        self._initialized_html_components: set[str] = set(
            inspection.get_child_component_containing_attribute_names_for_builtin_components()
        )

        # Boolean indicating whether this session has already been closed.
        self._was_closed = False

        # This lock is used to order state updates that are sent to the client.
        # Without it a message which was generated later might be sent to the
        # client before an earlier message, leading to invalid component
        # references.
        self._refresh_lock = asyncio.Lock()

        # Attachments. These are arbitrary values which are passed around inside
        # of the app. They can be looked up by their type.
        # Note: These are initialized by the AppServer.
        self._attachments = SessionAttachments(self)

        self.timezone = timezone

        self.preferred_languages = tuple(preferred_languages)
        assert self.preferred_languages, "Preferred languages must not be empty"

        # General locale information
        self._month_names_long = month_names_long
        self._day_names_long = day_names_long
        self._date_format_string = date_format_string
        self._first_day_of_week = first_day_of_week

        # Separators for number rendering
        self._decimal_separator = decimal_separator
        self._thousands_separator = thousands_separator

        # Device information
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.window_width = window_width
        self.window_height = window_height

        self.pixels_per_font_height = pixels_per_font_height
        self.scroll_bar_size = scroll_bar_size

        self.primary_pointer_type = primary_pointer_type

        self._is_maximized = False
        self._is_fullscreen = False

        # The URL the app's root is accessible at from the outside. Note that
        # this value slightly differs from the `base_url` in the app server. The
        # app server's parameter is optional, as a base URL can be guessed from
        # the HTTP request when a session is created. Thus, this value here is
        # always a valid URL and never `None`.
        assert base_url.is_absolute(), base_url
        assert not base_url.query, base_url
        assert not base_url.fragment, base_url
        assert str(base_url).islower(), base_url
        self._base_url = base_url

        self.theme = theme_

        # Information about the visitor
        self._client_ip: str = client_ip
        self._client_port: int = client_port
        self.http_headers: t.Mapping[str, str] = http_headers

        # Clear the Session properties "changed" by the constructor
        self._changed_attributes.clear()

        # Instantiate the root component
        global_state.currently_building_component = None
        global_state.currently_building_session = self

        self._high_level_root_component = (
            root_components.HighLevelRootComponent(
                app_server_.app._build,
                app_server_.app._build_connection_lost_message,
            )
        )

        global_state.currently_building_session = None

        # Note: The AppServer is responsible for creating the
        # `_refresh_whenever_necessary()` task. That's because it has to happen
        # *after* all the other Session initialization (like loading user
        # settings) is done.

    async def _refresh_whenever_necessary(self) -> None:
        while True:
            await self._refresh_required_event.wait()
            await self._refresh()

    async def __send_message(self, message: str) -> None:
        await self._rio_transport.send_if_possible(message)

    async def __receive_message(self) -> str:
        # Sessions don't immediately die if the connection is interrupted, they
        # can be reconnected. We will hide this fact from unicall because
        # unicall cancels any running RPC functions when the transport is
        # closed. We wouldn't want something like a `_component_message()` to be
        # interrupted halfway through.
        while True:
            # Wait until we have a connected transport
            await self._is_connected_event.wait()

            try:
                return await self._rio_transport.receive()
            except TransportInterrupted:
                self._is_connected_event.clear()
                self._app_server._disconnected_sessions[self] = time.monotonic()
            except TransportClosedIntentionally:
                self.close()

                while True:
                    await asyncio.sleep(999999)

    async def _replace_rio_transport(
        self, transport: AbstractTransport
    ) -> None:
        assert not transport.is_closed

        # Close the current transport
        await self._rio_transport.close()

        # Remember the new transport
        self._rio_transport = transport

        self._is_connected_event.set()
        self._app_server._disconnected_sessions.pop(self, None)

    @property
    def _fundamental_root_component(
        self,
    ) -> root_components.FundamentalRootComponent:
        build_data = self._high_level_root_component._build_data_
        assert build_data is not None

        assert isinstance(
            build_data.build_result, root_components.FundamentalRootComponent
        ), build_data.build_result
        return build_data.build_result

    @property
    def app(self) -> rio.App:
        """
        The app which this session belongs to.

        Each app can have multiple sessions. Each session belongs to one app.
        This property provides access to the `rio.App` instance that this
        session belongs to.
        """
        return self._app_server.app

    @property
    def assets(self) -> pathlib.Path:
        """
        Shortcut to the app's asset directory.

        When creating an app, a path can be provided to its asset directory.
        This property holds the `pathlib.Path` to the `App`'s asset directory.

        This allows you to access assets by simply typing
        `self.session.assets / "my-asset.png"` to obtain the path of an
        asset file.
        """
        return self._app_server.app.assets_dir

    @property
    def running_in_window(self) -> bool:
        """
        Whether the app is running in a local window, rather than as a website.

        `True` if the app is running in a local window, and `False` if it is
        hosted as a website.
        """
        return self._app_server.running_in_window

    @property
    def running_as_website(self) -> bool:
        """
        Whether the app is running as a website, rather than in a local window.

        `True` if the app is running as a website, and `False` if it is running
        in a local window.
        """
        return not self._app_server.running_in_window

    @property
    def base_url(self) -> rio.URL:
        """
        The URL to the app's home page.

        The location the app is hosted at. This is useful if you're hosting the
        same app at multiple domains, or if your app is hosted at a subdirectory
        of a domain.

        This URL is always absolute and has neither query parameters nor a
        fragment. Only available when running as a website.
        """
        if self._app_server.running_in_window:
            raise RuntimeError(
                "Cannot get the base URL of an app that is running in a window"
            )

        return self._base_url

    @property
    def active_page_url(self) -> rio.URL:
        """
        The URL of the currently active page.

        This value contains the URL of the currently active page. The URL is
        always absolute.

        You can use this to apply custom logic based on the current URL, or get
        additional URL information such as query parameters.

        This property is read-only. To change the page, use
        `Session.navigate_to`.
        """
        return self._active_page_url

    @property
    def active_page_instances(self) -> tuple[rio.ComponentPage, ...]:
        """
        All page instances that are currently active.

        This value contains all `rio.ComponentPage` instances that are currently
        active. The reason multiple pages may be active at the same time, is
        that a page may contain a `rio.PageView` itself. For example, if a user
        is on `/foo/bar/baz`, then this property can contain the
        `rio.ComponentPage` instances for foo, bar, and baz.

        Keep in mind that some pages may match multiple segments at once, so the
        number of active pages may be less than the number of segments in the
        URL.

        This property is read-only. To change the page, use
        `Session.navigate_to`.
        """
        return self._active_page_instances

    @property
    def client_ip(self) -> str:
        """
        The IP address of the connected client.

        This is the public IP address of the connected client.

        Only available when running as a website.
        """
        if self._app_server.running_in_window:
            raise RuntimeError(
                "Cannot get the client IP for an app that is running in a window"
            )

        return self._client_ip

    @property
    def client_port(self) -> int:
        """
        The port of the connected client.

        This is the port of the connected client.

        Only available when running as a website.
        """
        if self._app_server.running_in_window:
            raise RuntimeError(
                "Cannot get the client port for an app that is running in a window"
            )

        return self._client_port

    @property
    def user_agent(self) -> str:
        """
        Contains information about the client's device and browser.

        This contains the user agent string sent by the client's browser. User
        agents contain a wealth of information regarding the client's device,
        operating system, browser and more. This information can be used to
        tailor the app's appearance and behavior to the client's device.
        """
        # This is intentionally also available when running in a window. That's
        # because the window is still a browser, and this value might be used
        # e.g. for browser-specific workarounds and such. Besides, it's always
        # possible to just return an empty string if we decide that it's not
        # useful in a window anymore.
        return self.http_headers.get("user-agent", "")

    # @property
    # def is_maximized(self) -> bool:
    #     return self._is_maximized

    # @is_maximized.setter
    # def is_maximized(self, is_maximized: bool) -> None:
    #     self._is_maximized = is_maximized
    #     self.create_task(self._set_maximized(is_maximized))

    async def _set_maximized(self, maximized: bool) -> None:
        if self.running_in_window:
            window = await self._get_webview_window()

            if maximized:
                window.maximize()
            else:
                raise NotImplementedError  # FIXME
        else:
            if maximized:
                await self._evaluate_javascript(
                    """
window.moveTo(0, 0);
window.resizeTo(screen.availWidth, screen.availHeight);
"""
                )
            else:
                raise NotImplementedError  # FIXME

    # @property
    # def is_fullscreen(self) -> bool:
    #     return self._is_fullscreen

    # @is_fullscreen.setter
    # def is_fullscreen(self, fullscreen: bool):
    #     self._is_fullscreen = fullscreen
    #     self.create_task(self._set_fullscreen(fullscreen))

    async def _set_fullscreen(self, fullscreen: bool) -> None:
        if self.running_in_window:
            window = await self._get_webview_window()
            window.toggle_fullscreen()
        else:
            if fullscreen:
                js_code = "await document.documentElement.requestFullscreen();"
            else:
                js_code = "document.exitFullscreen();"

            await self._evaluate_javascript_and_get_result(js_code)

    @property
    def _is_connected(self) -> bool:
        """
        Returns whether there is an active connection to a client
        """
        return not self._rio_transport.is_closed

    def attach(self, value: t.Any) -> None:
        """
        Attaches a value to the session.

        Sessions can have arbitrary values attached to them. This makes it easy
        to share values with the entire session, such as a database connection
        or an object representing the currently logged in user.

        This function attaches the given value to the `Session`. It can be
        retrieved later using `session[...]`.

        ## Parameters

        `value`: The value to attach.
        """
        self._attachments.add(value)

    def __getitem__(self, key: type[T], /) -> T:
        """
        Retrieves an attachment by its type.

        Sessions can have arbitrary values attached to them. This makes it easy
        to share values with the entire session, such as a database connection
        or an object representing the currently logged in user.

        This function retrieves an attachment from the session. To attach
        values to the session, use `Session.attach`.

        ## Parameters

        `key`: The class of the value you want to retrieve.

        ## Raises

        `KeyError`: If no attachment of this type is attached to the session.
        """
        return self._attachments[key]

    def __delete__(self, typ: type, /) -> None:
        """
        Removes an attachment from this session.

        Sessions can have arbitrary values attached to them. This makes it easy
        to share values with the entire session, such as a database connection
        or an object representing the currently logged in user.

        This function removes an attachment from the session. To attach values
        to the session, use `Session.attach`.

        ## Raises

        `KeyError`: If no attachment of this type is attached to the session.
        """
        self._attachments.remove(typ)

    def detach(self, typ: type, /) -> None:
        """
        Removes an attachment from this session.

        Sessions can have arbitrary values attached to them. This makes it easy
        to share values with the entire session, such as a database connection
        or an object representing the currently logged in user.

        This function removes an attachment from the session. To attach values
        to the session, use `Session.attach`.

        This function is an alias for `del session[...]`, to match the `attach`
        method.

        ## Parameters

        `typ`: The type of the attachment to remove. This is used as the key to
            refer to attachments.

        ## Raises

        `KeyError`: If no attachment of this type is attached to the session.
        """
        self._attachments.remove(typ)

    def close(self) -> None:
        """
        Ends the session, closing any window or browser tab.

        Allows you to explicitly close the session. This is useful if you want
        to close the window or tab when the user has finished interacting with
        the app.

        Avoid using this function when running as a website. Browser tabs
        closing themselves are unusual and may be confusing to users.
        """
        self.create_task(self._close(close_remote_session=False))

    async def _close(self, close_remote_session: bool) -> None:
        # Protect against two _close() tasks  running at the same time
        if self._was_closed:
            return

        self._was_closed = True

        # Fire the session end event
        await self._call_event_handler(
            self._app_server.app._on_session_close,
            self,
            refresh=False,
        )

        # Extensions may also have session end handlers
        await self.app._call_event_handlers(
            self.app._extension_on_session_close_handlers,
            rio.ExtensionSessionCloseEvent(
                self,
            ),
        )

        # Save the settings
        await self._save_settings_now()

        # Close the tab / window
        if close_remote_session:
            if self.running_in_window:
                from . import webview_shim

                # It's possible that the session is being closed because the
                # user closed the window, so the window may not exist anymore
                window = webview_shim.active_window()
                if window is not None:
                    window.destroy()
            else:
                try:
                    await self._remote_close_session()
                except RuntimeError:  # Websocket is already closed
                    pass

        # Cancel all running tasks
        for task in self._running_tasks:
            task.cancel("Session is closing")

        # Close the connection to the client
        await self._rio_transport.close()

        self._app_server._after_session_closed(self)

    def _get_user_root_component(self) -> rio.Component:
        high_level_root = self._high_level_root_component
        assert isinstance(
            high_level_root, root_components.HighLevelRootComponent
        ), high_level_root

        low_level_root = high_level_root._build_data_.build_result  # type: ignore
        assert isinstance(
            low_level_root, root_components.FundamentalRootComponent
        ), low_level_root

        return low_level_root.content

    async def _get_webview_window(self):
        from . import webview_shim

        assert self.running_in_window, (
            "Can't get the window when not running inside one"
        )

        # The window may not have opened yet, so we'll wait until it exists
        while True:
            window = webview_shim.active_window()

            if window is not None:
                return window

            await asyncio.sleep(0.2)

    @t.overload
    async def _call_event_handler(
        self, handler: utils.EventHandler[[]], *, refresh: bool
    ) -> None: ...

    @t.overload
    async def _call_event_handler(
        self,
        handler: utils.EventHandler[[T]],
        event_data: T,
        /,
        *,
        refresh: bool,
    ) -> None: ...

    async def _call_event_handler(
        self,
        handler: utils.EventHandler[...],
        *event_data: object,
        refresh: bool,
    ) -> None:
        """
        Calls an event handler function. If it's async, it's awaited.

        Does *not* refresh the session. It's the caller's responsibility to do
        that.
        """

        # Event handlers are optional
        if handler is None:
            return

        # If the handler is available, call it and await it if necessary
        #
        # As an exception, don't await `self.force_refresh()`. This function
        # _can_ optionally be awaited for backwards compatibility, but prints
        # warning when that is done.
        try:
            result = handler(*event_data)

            try:
                result._rio_force_refresh_skip_await  # type: ignore
            except AttributeError:
                if inspect.isawaitable(result):
                    await result

        # Display and discard exceptions
        except Exception as error:
            revel.error("Exception in event handler:")
            nice_traceback.print_exception(error)

        if refresh:
            await self._refresh()

    @t.overload
    def _call_event_handler_sync(
        self,
        handler: utils.EventHandler[[]],
    ) -> None: ...

    @t.overload
    def _call_event_handler_sync(
        self,
        handler: utils.EventHandler[[T]],
        event_data: T,
        /,
    ) -> None: ...

    def _call_event_handler_sync(
        self,
        handler: utils.EventHandler[...],
        *event_data: object,
    ) -> None:
        """
        Calls an event handler function. If it returns an awaitable, it is
        scheduled as an asyncio task.

        In the async case, the session is automatically refreshed once the task
        completes. In the synchronous case, however, the caller is responsible
        for refreshing the session.
        """

        # Event handlers are optional
        if handler is None:
            return

        # Try to call the event handler synchronously
        try:
            result = handler(*event_data)

        # Display and discard exceptions
        except Exception:
            revel.error("Exception in event handler:")
            traceback.print_exc()
            return

        if not inspect.isawaitable(result):
            return

        # If it needs awaiting do so in a task
        async def worker() -> None:
            try:
                await result
            except Exception:
                revel.error("Exception in event handler:")
                traceback.print_exc()

            await self._refresh()

        self.create_task(worker(), name=f'Event handler for "{handler!r}"')

    def url_for_asset(self, asset: pathlib.Path) -> rio.URL:
        """
        Get a unique URL for an asset file.

        Returns the URL for the given asset file. The asset must be located in
        the app's `assets_dir`.

        ## Parameters

        `asset`: The file path of the asset whose URL you need.

        ## Raises

        `FileNotFoundError`: If no file exists at the given path.

        `ValueError`: If the given path isn't located inside the asset
            directory.
        """
        try:
            relative_asset_path = asset.relative_to(self.app.assets_dir)
        except ValueError:
            raise ValueError(
                f"{asset!r} is located outside of the assets_dir {self.app.assets_dir!r}"
            ) from None

        return self._app_server.external_url_for_user_asset(relative_asset_path)

    def create_task(
        self,
        coro: t.Coroutine[t.Any, None, T],
        *,
        name: str | None = None,
    ) -> asyncio.Task[T]:
        """
        Creates an `asyncio.Task` that is cancelled when the session is closed.

        This is identical to `asyncio.create_task`, except that any tasks are
        automatically cancelled when the session is closed. This makes sure that
        old tasks don't keep piling up long after they are no longer needed.

        ## Parameters

        `coro`: The coroutine to run.

        `name`: An optional name for the task. Assigning descriptive names can
            be helpful when debugging.
        """
        task = asyncio.create_task(coro, name=name)

        self._running_tasks.add(task)
        task.add_done_callback(self._running_tasks.remove)

        return task

    def _make_url_absolute(
        self,
        url: str | rio.URL,
        *,
        active_page_url_override: rio.URL | None = None,
    ) -> rio.URL:
        """
        Turns relative URLs into absolute URLs. The difference between this and
        `url.join()` is that we have special handling for urls starting with
        `/`. If the url starts with `/`, we append it to the base url - that
        means if the base url has a path, that path is not erased!
        """
        url = rio.URL(url)

        if url.is_absolute():
            return url

        if url.path.startswith("/"):
            return (
                (self._base_url / url.path.removeprefix("/"))
                .with_query(url.query)
                .with_fragment(url.fragment)
            )

        if active_page_url_override is None:
            active_page_url_override = self._active_page_url

        return active_page_url_override.join(url)

    def navigate_to(
        self,
        target_url: rio.URL | str,
        *,
        replace: bool = False,
    ) -> None:
        """
        Switches the app to display the given page URL.

        Switches the app to display the given page URL. If `replace` is `True`,
        the browser's most recent history entry is replaced with the new page.
        This means that the user can't go back to the previous page using the
        browser's back button. If `False`, a new history entry is created,
        allowing the user to go back to the previous page.

        ## Parameters

        `target_url`: The URL of the page to navigate to.

        `replace`: If `True`, the browser's most recent history entry is
            replaced with the new page. If `False`, a new history entry is
            created, allowing the user to go back to the previous page.
        """
        # Determine the full page to navigate to
        target_url_absolute = self._make_url_absolute(target_url)

        # Is any guard opposed to this page?
        active_page_instances_and_path_arguments, active_page_url = (
            routing.check_page_guards(self, target_url_absolute)
        )

        del target_url, target_url_absolute

        # Is this one of the app's pages, or a full URL to another site? If
        # navigating to another site, let the browser handle the navigation.
        #
        # TODO: What if running in a window? Navigating to another site doesn't
        # make any sense in that case, since the window isn't supposed to be a
        # browser.
        if active_page_instances_and_path_arguments is None:
            logging.debug(f"Navigating to external site `{active_page_url}`")

            async def history_worker() -> None:
                await self._evaluate_javascript(
                    f"""
window.location.href = {json.dumps(str(active_page_url))};
""",
                )

            self.create_task(history_worker(), name="history worker")
            return

        # Update the current page
        logging.debug(f"Navigating to page `{active_page_url}`")
        self._active_page_url = active_page_url
        self._active_page_instances_and_path_arguments = (
            active_page_instances_and_path_arguments
        )
        self._active_page_instances = tuple(
            page for page, _ in active_page_instances_and_path_arguments
        )

        async def refresh_and_update_url() -> None:
            await self._refresh()

            # Sometimes the frontend and backend disagree about the domain or
            # protocol, which can cause issues. So to be safe, we only send a
            # relative URL. FIXME: Is this still true? If it is true,
            # `Link._custom_serialize_` needs the same logic.
            #
            # Careful: If we're on the home page, the relative url becomes an
            # empty string, which does nothing when passed to
            # `pushState`/`replaceState`. In that case we must use "/" instead.
            relative_url = str(active_page_url.relative()) or "/"
            await self._remote_url_change(relative_url, replace)

        self.create_task(
            refresh_and_update_url(),
            name="Refresh and update browser history due to call to `navigate_to`",
        )

        # Trigger the `on_page_change` event
        for component, callbacks in self._page_change_callbacks.items():
            for callback in callbacks:
                self.create_task(
                    self._call_event_handler(callback, component, refresh=True),
                    name="`on_page_change` event handler",
                )

        # Extensions may also have page change handlers
        async def extension_worker() -> None:
            await self.app._call_event_handlers(
                self.app._extension_on_page_change_handlers,
                rio.ExtensionPageChangeEvent(self),
            )

        if self.app._extension_on_page_change_handlers:
            self.create_task(
                extension_worker(),
                name="Extension page change worker",
            )

    def open_url_in_browser(self, url: rio.URL | str) -> None:
        """
        Opens the given URL in the user's browser.

        This is similar to Python's built-in `webbrowser.open`, but it opens the
        browser on the user's machine, not the server's. So if your app is
        running as website, it will open the URL in the user's already running
        browser. If running in window, the function delegates to `browser.open`.

        ## Parameters

        `url`: The URL to open.
        """
        if self.running_in_window:
            import webbrowser

            webbrowser.open(str(url))
        else:
            coro = self._evaluate_javascript(
                f"window.open({json.dumps(str(url))}, '_blank')"
            )
            assert isinstance(coro, t.Coroutine)
            self.create_task(coro)

    def _dbg_why_dirty(self, component_or_id: rio.Component | int):
        """
        For debugging. Tells you why a component is dirty.
        """
        if isinstance(component_or_id, int):
            component = self._weak_components_by_id[component_or_id]
        else:
            component = component_or_id

        results = list[str]()

        if component in self._newly_created_components:
            results.append("newly created")

        for obj in self._changed_objects:
            try:
                if component in self._components_by_accessed_object[obj]:
                    results.append(f"object {obj!r} changed")
            except KeyError:
                pass

        for obj, changed_attrs in self._changed_attributes.items():
            if obj is component:
                if isinstance(obj, fundamental_component.FundamentalComponent):
                    results.append(
                        f"its own attributes changed: {changed_attrs}"
                    )

                if not changed_attrs.isdisjoint(rio.Component.__annotations__):
                    results.append(
                        f"its own attributes changed: {changed_attrs}"
                    )

            try:
                dependents_by_changed_attr = (
                    self._components_by_accessed_property[obj]
                )
            except KeyError:
                continue

            for changed_attr in changed_attrs:
                try:
                    if component in dependents_by_changed_attr[changed_attr]:
                        results.append(
                            f"attribute {changed_attr!r} of {obj} changed"
                        )
                except KeyError:
                    pass

        for obj, changed_items in self._changed_attributes.items():
            try:
                dependents_by_changed_item = self._components_by_accessed_item[
                    obj
                ]
            except KeyError:
                continue

            for changed_item in changed_items:
                try:
                    if component in dependents_by_changed_item[changed_item]:
                        results.append(
                            f"item {changed_item!r} of {obj} changed"
                        )
                except KeyError:
                    pass

        return results

    def _collect_components_to_build(self) -> set[rio.Component]:
        # Note: If you're debugging this function, the
        # `Session._dbg_why_dirty(component)` method can help you figure out how
        # a component ends up in `components_to_build`.

        components_to_build = set[rio.Component]()

        # Add newly instantiated components
        components_to_build.update(self._newly_created_components)

        # Add components that depend on observable objects that have changed
        for obj in self._changed_objects:
            components_to_build.update(self._components_by_accessed_object[obj])

        # Add components that depend on properties that have changed
        for obj, changed_attrs in self._changed_attributes.items():
            if not changed_attrs:
                continue

            if isinstance(obj, rio.Component):
                # If the object is a FundamentalComponent, add it too. It doesn't
                # have a `build` method, but it obviously does depend on its own
                # properties.
                if isinstance(obj, fundamental_component.FundamentalComponent):
                    components_to_build.add(obj)

                # Same thing goes for builtin attributes: Things like `min_width`
                # aren't used in the `build` function, but still need to be sent to
                # the frontend.
                if not changed_attrs.isdisjoint(rio.Component.__annotations__):
                    components_to_build.add(obj)

            # Add all components that depend on this attribute
            try:
                dependents_by_changed_attr = (
                    self._components_by_accessed_property[obj]
                )
            except KeyError:
                continue

            for changed_attr in changed_attrs:
                try:
                    components_to_build.update(
                        dependents_by_changed_attr[changed_attr]
                    )
                except KeyError:
                    pass

        # Add components that depend on items that have changed
        for obj, changed_items in self._changed_items.items():
            if not changed_items:
                continue

            # If the object is a FundamentalComponent, add it too. It doesn't
            # have a `build` method, but it obviously does depend on its own
            # properties.
            if isinstance(obj, fundamental_component.FundamentalComponent):
                components_to_build.add(obj)

            # Add all components that depend on this attribute
            try:
                dependents_by_changed_item = self._components_by_accessed_item[
                    obj
                ]
            except KeyError:
                continue

            for changed_item in changed_items:
                try:
                    components_to_build.update(
                        dependents_by_changed_item[changed_item]
                    )
                except KeyError:
                    pass

        return components_to_build

    def _build_component(self, component: rio.Component) -> set[rio.Component]:
        # Trigger the `on_populate` event, if it hasn't already.
        if not component._on_populate_triggered_:
            component._on_populate_triggered_ = True

            for handler, _ in component._rio_event_handlers_[
                rio.event.EventTag.ON_POPULATE
            ]:
                # Since the whole point of this event is to fetch data and
                # modify the component's state, wait for it to finish if it's
                # synchronous.
                self._call_event_handler_sync(handler, component)

            # If the event handler made the component dirty again, undo it
            self._changed_attributes.pop(component, None)

        # Call the `build` method
        global_state.currently_building_component = component
        global_state.currently_building_session = self
        global_state.accessed_objects.clear()
        global_state.accessed_attributes.clear()
        global_state.accessed_items.clear()

        build_result = utils.safe_build(component.build)

        accessed_attrs = [
            (obj, set(attrs))
            for obj, attrs in global_state.accessed_attributes.items()
        ]

        global_state.currently_building_component = None
        global_state.currently_building_session = None

        key_to_component = global_state.key_to_component
        global_state.key_to_component = {}

        # Process the state that was accessed by the `build` method
        for obj in global_state.accessed_objects:
            try:
                self._components_by_accessed_object[obj].add(component)
            except KeyError:
                self._components_by_accessed_object[obj] = weakref.WeakSet(
                    [component]
                )

        for obj, accessed_attrs in global_state.accessed_attributes.items():
            # Sometimes a `build` method indirectly accesses the state of a
            # child component. For example, calling `Row.add()` "accesses"
            # `Row.children`. This can lead to an infinite loop: Because the
            # child was freshly instantiated, all of its attributes have
            # "changed", thus rebuilding the parent, thus rebuilding the child,
            # etc.
            #
            # Workaround: Parents can't depend on the properties of their
            # children.
            if obj in self._newly_created_components:
                continue

            try:
                components_by_accessed_attr = (
                    self._components_by_accessed_property[obj]
                )
            except KeyError:
                components_by_accessed_attr = (
                    self._components_by_accessed_property.setdefault(obj, {})
                )

            for accessed_attr in accessed_attrs:
                try:
                    components_by_accessed_attr[accessed_attr].add(component)
                except KeyError:
                    components_by_accessed_attr[accessed_attr] = (
                        weakref.WeakSet([component])
                    )

        for obj, accessed_items in global_state.accessed_items.items():
            try:
                components_by_accessed_item = self._components_by_accessed_item[
                    obj
                ]
            except KeyError:
                components_by_accessed_item = (
                    self._components_by_accessed_item.setdefault(obj, {})
                )

            for accessed_item in accessed_items:
                try:
                    components_by_accessed_item[accessed_item].add(component)
                except KeyError:
                    components_by_accessed_item[accessed_item] = (
                        weakref.WeakSet([component])
                    )

        if component in self._changed_attributes:
            raise RuntimeError(
                f"The `build()` method of the component `{component}`"
                f" has changed the component's state. This isn't"
                f" supported, because it would trigger an immediate"
                f" rebuild, and thus result in an infinite loop. Make"
                f" sure to perform any changes outside of the `build`"
                f" function, e.g. in event handlers."
            )

        # Has this component been built before?
        component_data = component._build_data_

        # No, this is the first time
        if component_data is None:
            # Create the component data and cache it
            component_data = component._build_data_ = BuildData(
                build_result,
                set(),  # Set of all children - filled in below
                key_to_component,
            )

        # Yes, rescue state. This will:
        #
        # - Look for components in the build output which correspond to
        #   components in the previous build output, and transfers state
        #   from the new to the old component ("reconciliation")
        #
        # - Replace any references to new, reconciled components in the
        #   build output with the old components instead
        #
        # - Add any dirty components from the build output (new, or old
        #   but changed) to the dirty set.
        #
        # - Update the component data with the build output resulting
        #   from the operations above
        else:
            self._reconcile_tree(component_data, build_result, key_to_component)

            # Reconciliation can change the build result. Make sure
            # nobody uses `build_result` instead of
            # `component_data.build_result` from now on.
            del build_result

        # Remember the previous children of this component
        old_children_in_build_boundary = (
            component_data.all_children_in_build_boundary
        )

        # Inject the builder and build generation
        weak_builder = weakref.ref(component)

        component_data.all_children_in_build_boundary = set(
            component_data.build_result._iter_direct_and_indirect_child_containing_attributes_(
                include_self=True,
                recurse_into_high_level_components=False,
            )
        )
        for child in component_data.all_children_in_build_boundary:
            child._weak_builder_ = weak_builder

        return old_children_in_build_boundary

    def _refresh_sync(
        self,
    ) -> tuple[
        set[rio.Component],
        dict[object, set[str]],
        t.Iterable[rio.Component],
        t.Iterable[rio.Component],
    ]:
        """
        See `refresh` for details on what this function does.

        The refresh process must be performed atomically, without ever yielding
        control flow to the async event loop. TODO WHY

        To make sure async isn't used unintentionally this part of the refresh
        function is split into a separate, synchronous function.

        The session keeps track of components which are no longer referenced in
        its component tree. Those components are NOT included in the function's
        result.
        """

        # Keep track of all components which are visited. Only they will be sent to
        # the client.
        visited_components: collections.Counter[rio.Component] = (
            collections.Counter()
        )

        # Keep track of all changed properties for each component. The
        # serializer will need this information later
        properties_to_serialize = collections.defaultdict[object, set[str]](set)

        # Keep track of of previous child components
        old_children_in_build_boundary_for_visited_children = {}

        # Build all dirty components
        components_to_build = set[rio.Component]()
        while True:
            # Update the properties_to_serialize
            for obj, changed_properties in self._changed_attributes.items():
                properties_to_serialize[obj].update(changed_properties)

            # Collect all dirty components
            components_to_build.update(self._collect_components_to_build())
            self._newly_created_components.clear()
            self._changed_objects.clear()
            self._changed_attributes.clear()
            self._changed_items.clear()
            self._refresh_required_event.clear()

            # We need to build parents before children, but some components
            # haven't had their builder set yet, so we don't know who their
            # parent is. We need to find the topmost components and build them.

            # TODO: This is not entirely correct, because during the build
            # process, new components can be instantiated or the level of an
            # existing component can change. The correct solution would be to
            # process one component, then call `_collect_components_to_build()`
            # again, and sort again.
            component_level = dict[rio.Component, int]()
            component_level[self._high_level_root_component] = 0

            def determine_component_level(component: rio.Component) -> int:
                builder = component._weak_builder_()
                if builder is not None:
                    return get_component_level(builder) + 1

                if isinstance(
                    component,
                    rio.components.dialog_container.DialogContainer,
                ):
                    try:
                        owning_component = self._weak_components_by_id[
                            component.owning_component_id
                        ]
                    except KeyError:
                        return -99999

                    if component._id_ in owning_component._owned_dialogs_:
                        return get_component_level(owning_component) + 1

                    return -99999

                return -99999

            def get_component_level(component: rio.Component) -> int:
                try:
                    return component_level[component]
                except KeyError:
                    level = determine_component_level(component)

                    component_level[component] = level
                    return level

            components_to_build_in_this_iteration = sorted(
                [
                    component
                    for component in components_to_build
                    if get_component_level(component) >= 0
                ],
                key=get_component_level,
            )
            components_to_build.difference_update(
                components_to_build_in_this_iteration
            )

            # If we can't determine the level of even a single component, that
            # means all the remaining components must be dead. (We have already
            # built all "parent" components, so if a component still doesn't
            # have a parent, it must be dead.)
            if not components_to_build_in_this_iteration:
                break

            # Don't even build dead components, since their build function might
            # crash
            is_in_component_tree_cache: dict[rio.Component, bool] = {
                self._high_level_root_component: True,
            }

            for component in components_to_build_in_this_iteration:
                # If the component is dead, skip it
                if not component._is_in_component_tree_(
                    is_in_component_tree_cache
                ):
                    continue

                # Remember that this component has been visited
                visited_components[component] += 1

                # Catch deep recursions and abort
                build_count = visited_components[component]
                if build_count >= 5:
                    raise RecursionError(
                        f"The component `{component}` has been rebuilt"
                        f" {build_count} times during a single refresh. This is"
                        f" likely because one of your components' `build`"
                        f" methods is modifying the component's state"
                    )

                # Fundamental components require no further treatment
                if isinstance(
                    component, fundamental_component.FundamentalComponent
                ):
                    continue

                # Others need to be built
                old_children_in_build_boundary_for_visited_children[
                    component
                ] = self._build_component(component)

        # Determine which components are alive, to avoid sending references
        # to dead components to the frontend.
        is_in_component_tree_cache: dict[rio.Component, bool] = {
            self._high_level_root_component: True,
        }

        visited_and_live_components: set[rio.Component] = {
            component
            for component in visited_components
            if component._is_in_component_tree_(is_in_component_tree_cache)
        }

        all_children_old = set[rio.Component]()
        all_children_new = set[rio.Component]()

        for component in visited_components:
            # We only look at high level components, since we already have a set
            # of all children in the build boundary
            if isinstance(
                component, fundamental_component.FundamentalComponent
            ):
                continue

            all_children_old.update(
                old_children_in_build_boundary_for_visited_children[component]
            )
            all_children_new.update(
                component._build_data_.all_children_in_build_boundary  # type: ignore
            )

        # Find out which components were mounted or unmounted
        mounted_components = all_children_new - all_children_old
        unmounted_components = all_children_old - all_children_new

        # The state/children of newly mounted components must also be sent to
        # the client.
        unvisited_mounted_components = (
            mounted_components - visited_and_live_components
        )

        while unvisited_mounted_components:
            visited_and_live_components.update(unvisited_mounted_components)

            new_children = list[rio.Component]()
            for component in unvisited_mounted_components:
                if not isinstance(
                    component, fundamental_component.FundamentalComponent
                ):
                    new_children += component._iter_component_tree_(
                        include_root=False
                    )

            unvisited_mounted_components = new_children

        return (
            visited_and_live_components,
            properties_to_serialize,
            mounted_components,
            unmounted_components,
        )

    async def _refresh(self) -> None:
        """
        Make sure the session state is up to date. Specifically:

        - Call build on all components marked as dirty
        - Recursively do this for all freshly spawned components
        - mark all components as clean

        Afterwards, the client is also informed of any changes, meaning that
        after this method returns there are no more dirty components in the
        session, and Python's state and the client's state are in sync.
        """

        # For why this lock is here see its creation in `__init__`
        async with self._refresh_lock:
            # Clear the dict of crashed build functions
            self._crashed_build_functions.clear()

            while True:
                # Refresh and get a set of all components which have been
                # visited
                (
                    visited_components,
                    properties_to_serialize,
                    mounted_components,
                    unmounted_components,
                ) = self._refresh_sync()

                # Avoid sending empty messages
                if not visited_components:
                    return

                # Serialize all components which have been visited
                delta_states: dict[int, JsonDoc] = {
                    component._id_: serialization.serialize_and_host_component(
                        component, properties_to_serialize[component]
                    )
                    for component in visited_components
                }

                await self._update_component_states(
                    visited_components, delta_states
                )

                # Trigger the `on_unmount` event
                #
                # Notes:
                # - All events are triggered only after the client has been
                #   notified of the changes. This way, if the event handlers
                #   trigger another client message themselves, any referenced
                #   components will already exist
                for component in unmounted_components:
                    # Trigger the event
                    for handler, _ in component._rio_event_handlers_[
                        rio.event.EventTag.ON_UNMOUNT
                    ]:
                        self._call_event_handler_sync(handler, component)

                # Trigger the `on_mount` event
                #
                # Notes:
                # - See the note on running after notifying the client above
                # - This function enlarges the set of watched components. The
                #   `on_unmount` event handler iterates over that set. By
                #   processing that handler first it only needs to process a
                #   smaller set
                for component in mounted_components:
                    # Trigger the event
                    for handler, _ in component._rio_event_handlers_[
                        rio.event.EventTag.ON_MOUNT
                    ]:
                        self._call_event_handler_sync(handler, component)

                # If there were any synchronous `on_mount` or `on_unmount`
                # handlers, we must immediately refresh again. So we'll simply
                # loop until there are no more dirty components.

    async def _update_component_states(
        self,
        visited_components: set[rio.Component],
        delta_states: dict[int, JsonDoc],
    ) -> None:
        # Initialize all new FundamentalComponents
        for component in visited_components:
            if (
                not isinstance(
                    component, fundamental_component.FundamentalComponent
                )
                or component._unique_id_ in self._initialized_html_components
            ):
                continue

            await component._initialize_on_client(self)
            self._initialized_html_components.add(type(component)._unique_id_)

        # Check whether the root component needs replacing. Take care to never
        # send the high level root component. JS only cares about the
        # fundamental one.
        if self._high_level_root_component in visited_components:
            del delta_states[self._high_level_root_component._id_]

            root_build: BuildData = self._high_level_root_component._build_data_  # type: ignore
            fundamental_root_component = root_build.build_result
            assert isinstance(
                fundamental_root_component,
                fundamental_component.FundamentalComponent,
            ), fundamental_root_component
            root_component_id = fundamental_root_component._id_
        else:
            root_component_id = None

        # Send the new state to the client
        await self._remote_update_component_states(
            delta_states,
            root_component_id,
        )

    async def _send_all_components_on_reconnect(self) -> None:
        self._initialized_html_components.clear()

        # For why this lock is here see its creation in `__init__`
        async with self._refresh_lock:
            visited_components: set[rio.Component] = set()
            delta_states = {}

            for (
                component
            ) in self._high_level_root_component._iter_component_tree_():
                visited_components.add(component)
                delta_states[component._id_] = (
                    serialization.serialize_and_host_component(
                        component,
                        serialization.get_attribute_serializers(
                            type(component)
                        ),
                    )
                )

            await self._update_component_states(
                visited_components, delta_states
            )

    def _reconcile_tree(
        self,
        old_build_data: BuildData,
        new_build: rio.Component,
        new_key_to_component: dict[rio.components.component.Key, rio.Component],
    ) -> None:
        # Find all pairs of components which should be reconciled
        matched_pairs = self._find_components_for_reconciliation(
            old_build_data.build_result,
            new_build,
            old_build_data.key_to_component,
            new_key_to_component,
        )

        # Reconciliating individual components requires knowledge of which other
        # components are being reconciled.
        #
        # -> Collect them into a dict first.
        reconciled_components_new_to_old: dict[rio.Component, rio.Component] = {
            new_component: old_component
            for old_component, new_component in matched_pairs
        }

        # Update the key to component mapping. Take the keys from the new dict,
        # but replace the components with the reconciled ones.
        old_build_data.key_to_component = {
            key: reconciled_components_new_to_old.get(component, component)
            for key, component in new_key_to_component.items()
        }

        # For FundamentalComponents, keep track of children that were added or
        # removed. Removed children must also be removed from their builder's
        # `all_children_in_build_boundary` set. (See
        # `test_reconcile_not_dirty_high_level_component` for more details.)
        added_children_by_builder = collections.defaultdict[
            rio.Component, set[rio.Component]
        ](set)
        removed_children_by_builder = collections.defaultdict[
            rio.Component, set[rio.Component]
        ](set)

        # Reconcile all matched pairs
        for (
            new_component,
            old_component,
        ) in reconciled_components_new_to_old.items():
            assert new_component is not old_component, (
                f"Attempted to reconcile {new_component!r} with itself!?"
            )

            added_children, removed_children = self._reconcile_component(
                old_component,
                new_component,
                reconciled_components_new_to_old,
            )

            builder = old_component._weak_builder_()
            if builder is not None:
                added_children_by_builder[builder].update(added_children)
                removed_children_by_builder[builder].update(removed_children)

            # Avoid building the new components. This is not just a performance
            # optimization.
            #
            # When building, components assign themselves as weak builder to all
            # of their build output. If these components were allowed to build
            # themselves, they'd override the actual weak builder with
            # themselves.
            self._newly_created_components.discard(new_component)
            self._changed_attributes.pop(new_component, None)

        # Now that we have collected all added and removed children, update the
        # builder's `all_children_in_build_boundary` set
        for builder, added_children in added_children_by_builder.items():
            build_data = builder._build_data_
            if build_data is None:
                continue

            build_data.all_children_in_build_boundary.difference_update(
                removed_children_by_builder[builder]
            )
            build_data.all_children_in_build_boundary.update(
                reconciled_components_new_to_old.get(new_child, new_child)
                for new_child in added_children
            )

        # Update the component data. If the root component was not reconciled,
        # the new component is the new build result.
        try:
            reconciled_build_result = reconciled_components_new_to_old[
                new_build
            ]
        except KeyError:
            reconciled_build_result = new_build
            old_build_data.build_result = new_build

        def ensure_weak_builder_is_set(
            parent: rio.Component, child: rio.Component
        ) -> None:
            """
            This function makes sure that any components which are now in the
            tree have their builder properly set.

            The problem is that the `_weak_builder_` is only set after a high
            level component is built, but there are situations where a
            FundamentalComponent received a new child and its parent high level
            component is not dirty.

            For more details, see
            `test_reconcile_not_dirty_high_level_component`.
            """
            if not isinstance(
                parent, fundamental_component.FundamentalComponent
            ):
                return

            builder = parent._weak_builder_()

            # It's possible that the builder has not been initialized yet. The
            # builder is only set for children inside of a high level
            # component's build boundary, but `remap_components` crosses build
            # boundaries. So if the builder is not set, we simply do nothing -
            # it will be set later, once our high level parent component is
            # built.
            if builder is None:
                return  # TODO: WRITE A UNIT TEST FOR THIS

            child._weak_builder_ = parent._weak_builder_

            build_data = builder._build_data_
            if build_data is not None:
                build_data.all_children_in_build_boundary.add(child)

        # Replace any references to new reconciled components to old ones instead
        def remap_components(parent: rio.Component) -> None:
            parent_vars = vars(parent)

            for (
                attr_name
            ) in inspection.get_child_component_containing_attribute_names(
                type(parent)
            ):
                attr_value = parent_vars[attr_name]

                # Just a component
                if isinstance(attr_value, rio.Component):
                    try:
                        attr_value = reconciled_components_new_to_old[
                            attr_value
                        ]
                    except KeyError:
                        ensure_weak_builder_is_set(parent, attr_value)
                    else:
                        parent_vars[attr_name] = attr_value

                    remap_components(attr_value)

                # List / Collection
                else:
                    try:
                        iterator = iter(attr_value)
                    except TypeError:
                        continue

                    for ii, item in enumerate(iterator):
                        if isinstance(item, rio.Component):
                            try:
                                item = reconciled_components_new_to_old[item]
                            except KeyError:
                                ensure_weak_builder_is_set(parent, item)
                            else:
                                attr_value[ii] = item

                            remap_components(item)

        remap_components(reconciled_build_result)

    def _reconcile_component(
        self,
        old_component: rio.Component,
        new_component: rio.Component,
        reconciled_components_new_to_old: dict[rio.Component, rio.Component],
    ) -> tuple[set[rio.Component], set[rio.Component]]:
        """
        Given two components of the same type, reconcile them. Specifically:

        - Any state which was explicitly set by the user in the new component's
          constructor is considered explicitly set, and will be copied into the
          old component
        - If any values were changed, the component is registered as dirty with
          the session

        This function also handles `StateBinding`s, for details see comments.
        """
        assert type(old_component) is type(new_component), (
            old_component,
            new_component,
        )
        assert old_component.key == new_component.key, (
            old_component.key,
            new_component.key,
        )
        assert old_component is not new_component

        # Determine which properties will be taken from the new component
        overridden_values: dict[str, object] = {}
        old_component_dict = vars(old_component)
        new_component_dict = vars(new_component)

        overridden_property_names = (
            old_component._properties_set_by_creator_
            - old_component._properties_assigned_after_creation_
        ) | new_component._properties_set_by_creator_

        for prop_name in overridden_property_names:
            # Take care to keep attribute bindings up to date
            old_value = old_component_dict[prop_name]
            new_value = new_component_dict[prop_name]
            old_is_binding = isinstance(old_value, AttributeBinding)
            new_is_binding = isinstance(new_value, AttributeBinding)

            # If the old value was a binding, and the new one isn't, split the
            # tree of bindings. All children are now roots.
            if old_is_binding and not new_is_binding:
                binding_value = old_value.get_value()
                old_value.owning_instance_weak = lambda: None

                for child_binding in old_value.children:
                    child_binding.parent = None
                    child_binding.value = binding_value

            # If both values are bindings transfer the children to the new
            # binding
            elif old_is_binding and new_is_binding:
                new_value.owning_instance_weak = old_value.owning_instance_weak
                new_value.children = old_value.children

                for child in old_value.children:
                    child.parent = new_value

                # Save the binding's value in case this is the root binding
                new_value.value = old_value.value

            overridden_values[prop_name] = new_value

        # Keep track of added and removed child components
        added_children = set[rio.Component]()
        removed_children = set[rio.Component]()
        if isinstance(
            old_component, fundamental_component.FundamentalComponent
        ):
            child_containing_attributes = (
                inspection.get_child_component_containing_attribute_names(
                    type(old_component)
                )
            )

            for attr_name in child_containing_attributes:
                removed_children.update(
                    extract_child_components(old_component, attr_name)
                )
                added_children.update(
                    extract_child_components(new_component, attr_name)
                )

        # If the component has changed, mark it as dirty
        def values_equal(old: object, new: object) -> bool:
            """
            Used to compare the old and new values of a property. Returns `True`
            if the values are considered equal, `False` otherwise.
            """
            # Components are a special case. Component attributes are dirty iff
            # the component isn't reconciled, i.e. it is a new component
            if isinstance(new, rio.Component):
                if old is new:
                    return True

                try:
                    new_before_reconciliation = (
                        reconciled_components_new_to_old[new]
                    )
                except KeyError:
                    return False
                else:
                    return old is new_before_reconciliation

            # Lists are compared element-wise
            if isinstance(new, list):
                if not isinstance(old, list):
                    return False

                old = t.cast(list[object], old)
                new = t.cast(list[object], new)

                if len(old) != len(new):
                    return False

                for old_item, new_item in zip(old, new):
                    if not values_equal(old_item, new_item):
                        return False

                return True

            # Otherwise attempt to compare the values
            try:
                return bool(old == new)
            except Exception:
                return old is new

        # Determine which properties have changed
        changed_properties = set[str]()

        for prop_name in overridden_values:
            old_value = getattr(old_component, prop_name)
            new_value = getattr(new_component, prop_name)

            if not values_equal(old_value, new_value):
                changed_properties.add(prop_name)

        self._changed_attributes[old_component].update(changed_properties)

        # Now combine the old and new dictionaries
        #
        # Notice that the component's `_weak_builder_` is always preserved. So
        # even components whose position in the tree has changed still have the
        # correct builder set.
        old_component_dict.update(overridden_values)

        # Update the metadata
        old_component._properties_set_by_creator_ = (
            new_component._properties_set_by_creator_
        )

        # If the component has a `on_populate` handler, it must be triggered
        # again
        old_component._on_populate_triggered_ = False

        return added_children, removed_children

    def _find_components_for_reconciliation(
        self,
        old_build: rio.Component,
        new_build: rio.Component,
        old_key_to_component: dict[rio.components.component.Key, rio.Component],
        new_key_to_component: dict[rio.components.component.Key, rio.Component],
    ) -> t.Iterable[tuple[rio.Component, rio.Component]]:
        """
        Given two component trees, find pairs of components which can be
        reconciled, i.e. which represent the "same" component. When exactly
        components are considered to be the same is up to the implementation and
        best-effort.

        Returns an iterable over (old_component, new_component) pairs.
        """

        def can_pair_up(
            old_component: rio.Component, new_component: rio.Component
        ) -> bool:
            # Components of different type are never a pair
            if type(old_component) is not type(new_component):
                return False

            # Components with different keys are never a pair
            if old_component.key != new_component.key:
                return False

            # Don't reconcile a component with itself, it won't end well
            if old_component is new_component:
                return False

            return True

        # Maintain a queue of (old_component, new_component) pairs that MAY
        # represent the same component. If they match, they will be yielded as
        # results, and their children will also be compared with each other.
        queue: list[tuple[rio.Component, rio.Component]] = [
            (old_build, new_build)
        ]

        # Add the components that have keys. Simply throw all potential pairs
        # into the queue.
        for old_key, old_component in old_key_to_component.items():
            try:
                new_component = new_key_to_component[old_key]
            except KeyError:
                continue

            queue.append((old_component, new_component))

        # Process the queue one by one.
        while queue:
            old_component, new_component = queue.pop(0)

            if not can_pair_up(old_component, new_component):
                continue

            yield old_component, new_component

            # Compare the children, but make sure to preserve the topology.
            # Can't just use `iter_direct_children` here, since that would
            # discard topological information.
            for (
                attr_name
            ) in inspection.get_child_component_containing_attribute_names(
                type(old_component)
            ):
                old_children = extract_child_components(
                    old_component, attr_name
                )
                new_children = extract_child_components(
                    new_component, attr_name
                )

                queue.extend(zip(old_children, new_children))

    def _register_font(self, font: text_style.Font) -> str:
        # Fonts are different from other assets because they need to be
        # registered under a name, not just a URL. We don't want to re-register
        # the same font multiple times, so we keep track of all registered
        # fonts. Every registered font is associated with all its assets
        # (regular, bold, italic, ...), which will be kept alive until the
        # session is closed.
        try:
            return self._registered_font_names[font]
        except KeyError:
            pass

        # Generate a random name for the font
        while True:
            font_name = "".join(
                random.choice(string.ascii_letters) for _ in range(10)
            )

            if font_name not in self._registered_font_names:
                break

        # Register the font files as assets
        font_assets: list[assets.Asset] = []
        urls: list[str | None] = [None] * 4

        for i, location in enumerate(
            (font.regular, font.bold, font.italic, font.bold_italic)
        ):
            if location is None:
                continue

            # Host the font file as an asset
            asset = assets.Asset.new(location)
            urls[i] = asset._serialize(self)

            font_assets.append(asset)

        self.create_task(self._remote_register_font(font_name, urls))  # type: ignore

        self._registered_font_names[font] = font_name
        self._registered_font_assets[font] = font_assets

        return font_name

    def _get_settings_file_path(self) -> pathlib.Path:
        """
        The path to the settings file. Only used if `running_in_window`.
        """
        import platformdirs

        return (
            pathlib.Path(
                platformdirs.user_data_dir(
                    appname=self._app_server.app.name,
                    roaming=True,
                    ensure_exists=True,
                )
            )
            / "settings.json"
        )

    async def _load_user_settings(
        self, settings_sent_by_client: JsonDoc
    ) -> None:
        # If `running_in_window`, load the settings from the config file.
        # Otherwise, parse the settings sent by the browser.
        #
        # Keys in this dict can be attributes of the "root" section or names of
        # sections. To prevent name clashes, section names are prefixed with
        # "section:".
        settings_json: JsonDoc

        if self.running_in_window:
            import aiofiles

            try:
                async with aiofiles.open(
                    self._get_settings_file_path()
                ) as file:
                    settings_text = await file.read()

                settings_json = json.loads(settings_text)
            except (IOError, json.JSONDecodeError):
                settings_json = {}
                settings_text = "{}"

            self._settings_json = settings_json
            self._settings_json_string = settings_text
        else:
            # Browsers send us a flat dict where the keys are prefixed with the
            # section name. We will convert each section into a dict.
            settings_json = {}

            for key, value in settings_sent_by_client.items():
                # Find the section name
                section_name, _, key = key.rpartition(":")

                if section_name:
                    section = t.cast(
                        JsonDoc,
                        settings_json.setdefault("section:" + section_name, {}),
                    )
                else:
                    section = settings_json

                section[key] = value

        self._load_user_settings_from_settings_json(settings_json)

    def _load_user_settings_from_settings_json(
        self, settings_json: JsonDoc
    ) -> None:
        # Instantiate and attach the settings
        for default_settings in self._app_server.app.default_attachments:
            if not isinstance(
                default_settings, user_settings_module.UserSettings
            ):
                continue

            settings = type(default_settings)._from_json(
                settings_json,
                default_settings,
            )

            # Attach the instance to the session
            self._attachments._add(settings, synchronize=False)

    async def _save_settings_now(self) -> None:
        async with self._settings_sync_lock:
            # Find the unsaved settings attachments
            unsaved_settings: list[
                tuple[user_settings_module.UserSettings, set[str]]
            ] = []

            for settings in self._attachments:
                if not isinstance(settings, user_settings_module.UserSettings):
                    continue

                if not settings._rio_dirty_attribute_names_:
                    continue

                unsaved_settings.append(
                    (settings, settings._rio_dirty_attribute_names_)
                )
                settings._rio_dirty_attribute_names_ = set()

            if not unsaved_settings:
                return

            self._last_settings_save_time = time.monotonic()

            # FIXME: Delete no-longer-needed sections and fields
            if self.running_in_window:
                await self._save_settings_now_in_window(unsaved_settings)
            else:
                await self._save_settings_now_in_browser(unsaved_settings)

    async def _save_settings_now_in_window(
        self,
        settings_to_save: t.Iterable[
            tuple[user_settings_module.UserSettings, t.Iterable[str]]
        ],
    ) -> None:
        import aiofiles

        for settings, dirty_attributes in settings_to_save:
            if settings.section_name:
                section = t.cast(
                    JsonDoc,
                    self._settings_json.setdefault(
                        "section:" + settings.section_name, {}
                    ),
                )
            else:
                section = self._settings_json

            annotations = inspection.get_resolved_type_annotations(
                type(settings)
            )

            for attr_name in dirty_attributes:
                section[attr_name] = serialization.json_serde.as_json(
                    getattr(settings, attr_name),
                    as_type=annotations[attr_name],
                )

        json_data = json.dumps(self._settings_json, indent="\t")

        # If nothing changed, don't needlessly re-write the file
        if json_data == self._settings_json_string:
            return
        self._settings_json_string = json_data

        config_path = self._get_settings_file_path()

        async with aiofiles.open(config_path, "w") as file:
            await file.write(json_data)

    async def _save_settings_now_in_browser(
        self,
        settings_to_save: t.Iterable[
            tuple[user_settings_module.UserSettings, t.Iterable[str]]
        ],
    ) -> None:
        delta_settings: dict[str, t.Any] = {}

        for settings, dirty_attributes in settings_to_save:
            prefix = (
                f"{settings.section_name}:" if settings.section_name else ""
            )

            annotations = inspection.get_resolved_type_annotations(
                type(settings)
            )

            # Get the dirty attributes
            for attr_name in dirty_attributes:
                delta_settings[f"{prefix}{attr_name}"] = (
                    serialization.json_serde.as_json(
                        getattr(settings, attr_name),
                        as_type=annotations[attr_name],
                    )
                )

        # Sync them with the client
        await self._set_user_settings(delta_settings)

    def _save_settings_soon(self) -> None:
        if self._settings_save_task is None:
            self._settings_save_task = self.create_task(
                self.__wait_and_save_settings()
            )

    async def __wait_and_save_settings(self) -> None:
        # Wait some time to see if more attributes are marked as dirty
        await asyncio.sleep(0.5)

        # If we've recently saved, wait a bit longer. Some apps change
        # the settings very often, and we don't need to save immediately every
        # single time.
        timeout = 3 * 60 if self.running_in_window else 5
        if time.monotonic() - self._last_settings_save_time < timeout:
            await asyncio.sleep(timeout)

        # Save
        try:
            await self._save_settings_now()

        # Housekeeping
        finally:
            self._settings_save_task = None

    async def set_title(self, title: str) -> None:
        """
        Changes the window title of this session.

        Sets the text to display in the window. When running in a window this
        will be the title of the window. When running in a browser this will be
        the title of the tab.

        ## Parameters

        `title`: The new window title.
        """
        if self.running_in_window:
            from . import webview_shim

            window = await self._get_webview_window()

            while True:
                try:
                    window.set_title(title)
                    break
                except webview_shim.errors.WebViewException:
                    await asyncio.sleep(0.2)
        else:
            await self._remote_set_title(title)

    @t.overload
    async def pick_file(
        self,
        *,
        file_types: t.Iterable[str] | None = None,
        multiple: t.Literal[False] = False,
    ) -> utils.FileInfo: ...

    @t.overload
    async def pick_file(
        self,
        *,
        file_types: t.Iterable[str] | None = None,
        multiple: t.Literal[True],
    ) -> list[utils.FileInfo]: ...

    @deprecations.parameter_renamed(
        since="0.10",
        old_name="file_extension",
        new_name="file_types",
    )
    async def pick_file(
        self,
        *,
        file_types: t.Iterable[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        """
        Open a file picker dialog.

        This function opens a file picker dialog, allowing the user to pick a
        file. The selected file is returned, allowing you to access its
        contents. See also `save_file`, if you want to save a file instead of
        opening one.


        ## Parameters

        `file_types`: A list of file extensions which the user is allowed
            to select. Defaults to `None`, which means that the user may select
            any file. Values can be passed as file extensions, ('pdf',
            '.pdf', '*.pdf' are all accepted) or MIME types (e.g.
            'application/pdf').

            Note that there is no way for Rio to enforce the file type. Users
            will always be able to upload arbitrary files, e.g. by renaming
            them. Treat this as a hint to the user, and so the file browser may
            filter files, but not as a security measure.

        `multiple`: Whether the user should pick a single file, or multiple.


        ## Raises

        `NoFileSelectedError`: If the user did not select a file.
        """
        # Normalize the file types
        if file_types is not None:
            # Normalize and deduplicate, but maintain the order
            file_types = list(
                ordered_set.OrderedSet(
                    utils.normalize_file_extension(file_type)
                    for file_type in file_types
                )
            )

        if not self.running_in_window:
            return await self._app_server.pick_file(
                self,
                file_types=file_types,
                multiple=multiple,
            )

        from . import webview_shim

        if file_types is None:
            file_types = ()
        else:
            file_types = [
                f"{extension} (*.{extension})" for extension in file_types
            ]

        window = await self._get_webview_window()
        selected_file_paths = window.create_file_dialog(
            dialog_type=webview_shim.OPEN_DIALOG,
            allow_multiple=multiple,
            file_types=file_types,
        )

        # Raise an exception if no files were selected
        if not selected_file_paths:
            raise errors.NoFileSelectedError()

        file_infos = [
            utils.FileInfo._from_path(path) for path in selected_file_paths
        ]

        if multiple:
            return file_infos
        else:
            return file_infos[0]

    @t.overload
    async def file_chooser(
        self,
        *,
        file_types: t.Iterable[str] | None = None,
        multiple: t.Literal[False] = False,
    ) -> utils.FileInfo: ...

    @t.overload
    async def file_chooser(
        self,
        *,
        file_types: t.Iterable[str] | None = None,
        multiple: t.Literal[True],
    ) -> list[utils.FileInfo]: ...

    @deprecations.parameter_renamed(
        since="0.10",
        old_name="file_extension",
        new_name="file_types",
    )
    @deprecations.deprecated(since="0.10", replacement=pick_file)
    @introspection.set_signature(pick_file)
    async def file_chooser(
        self,
        *args,
        **kwargs,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        """
        Open a file picker dialog.

        This function opens a file picker dialog, allowing the user to pick a
        file. The selected file is returned, allowing you to access its
        contents. See also `save_file`, if you want to save a file instead of
        opening one.

        ## Parameters

        `file_types`: A list of file extensions which the user is allowed
            to select. Defaults to `None`, which means that the user may select
            any file. Values can be passed as file extensions, ('pdf',
            '.pdf', '*.pdf' are all accepted) or MIME types (e.g.
            'application/pdf').

            Note that there is no way for Rio to enforce the file type. Users
            will always be able to upload arbitrary files, e.g. by renaming
            them. Treat this as a hint to the user, and so the file browser may
            filter files, but not as a security measure.

        `multiple`: Whether the user should pick a single file, or multiple.

        ## Raises

        `NoFileSelectedError`: If the user did not select a file.
        """
        # Delegate to the new function
        return await self.pick_file(*args, **kwargs)

    async def save_file(
        self,
        file_contents: pathlib.Path | str | bytes,
        file_name: str = "Unnamed File",
        *,
        media_type: str | None = None,
        directory: pathlib.Path | None = None,
    ) -> None:
        """
        Save a file to the user's device.

        This function allows you to save a file to the user's device. The user
        will be prompted to select a location to save the file to.

        See also `pick_file` if you want to open a file instead of saving
        one.


        ## Parameters

        `file_contents`: The contents of the file to save. This can be a
            string, bytes, or a path to a file on the server.

        `file_name`: The default file name that will be displayed in the file
            dialog. The user can freely change it.

        `media_type`: The media type of the file. Defaults to `None`, which
            means that the media type will be guessed from the file name.

        `directory`: The directory where the file dialog should open. This has
            no effect if the user is visiting the app in a browser.
        """
        if self.running_in_window:
            # FIXME: Find (1) a better way to get the active window and (2) a
            # way to open a file dialog without blocking the event loop.
            import aiofiles

            from . import webview_shim

            window = await self._get_webview_window()
            destinations = window.create_file_dialog(
                webview_shim.SAVE_DIALOG,
                directory="" if directory is None else str(directory),
                save_filename=file_name,
            )
            if not destinations:
                return  # TODO: Raise error?

            # It's documented to return a tuple of strings, but in reality it
            # returns a string.
            if isinstance(destinations, str):
                destination = destinations
            else:
                destination = destinations[0]

            if isinstance(file_contents, pathlib.Path):
                await asyncio.to_thread(shutil.copy, file_contents, destination)

            elif isinstance(file_contents, str):
                async with aiofiles.open(
                    destination, "w", encoding="utf8"
                ) as file:
                    await file.write(file_contents)

            elif isinstance(file_contents, bytes):  # type: ignore (unnecessary isinstance)
                async with aiofiles.open(destination, "wb") as file:
                    await file.write(file_contents)

            else:
                raise ValueError(
                    f"The file contents must be a Path, str or bytes, not {file_contents!r}"
                )

            return

        # Create an asset for the file
        if isinstance(file_contents, pathlib.Path):
            as_asset = assets.PathAsset(file_contents, media_type)

        elif isinstance(file_contents, str):
            as_asset = assets.BytesAsset(
                file_contents.encode("utf-8"),
                "text/plain" if media_type is None else media_type,
            )

        elif isinstance(file_contents, bytes):  # type: ignore (unnecessary isinstance)
            as_asset = assets.BytesAsset(
                file_contents,
                "application/octet-stream"
                if media_type is None
                else media_type,
            )

        else:
            raise ValueError(
                f"The file contents must be a Path, str or bytes, not {file_contents!r}"
            )

        # Host the asset
        url = self._app_server.host_asset_with_timeout(as_asset, 60)

        # Tell the frontend to download the file
        await self._evaluate_javascript(
            f"""
const a = document.createElement('a');
a.href = {json.dumps(str(url))};
a.download = {json.dumps(file_name)};
a.type = {json.dumps(media_type)};
a.target = "_blank";
document.body.appendChild(a);
a.click();
a.remove();
"""
        )

    def _serialize_fill(self, fill: fills._FillLike | None) -> Jsonable:
        if fill is None:
            return None

        if isinstance(fill, rio.Color):
            fill = rio.SolidFill(fill)

        return fill._serialize(self)

    def _host_and_get_fill_as_css_variables(
        self, fill: fills._FillLike
    ) -> dict[str, str]:
        if isinstance(fill, rio.Color):
            return {
                "color": f"#{fill.hexa}",
                "background": "none",
                "background-clip": "unset",
                "fill-color": "unset",
                "backdrop-filter": "none",
            }

        if isinstance(fill, rio.SolidFill):
            return {
                "color": f"#{fill.color.hexa}",
                "background": "none",
                "background-clip": "unset",
                "fill-color": "unset",
                "backdrop-filter": "none",
            }

        if isinstance(fill, rio.FrostedGlassFill):
            return {
                "color": f"#{fill.color.hexa}",
                "background": "none",
                "background-clip": "unset",
                "fill-color": "unset",
                "backdrop-filter": f"blur({fill.blur_size}rem)",
            }

        assert isinstance(fill, (rio.LinearGradientFill, rio.ImageFill)), fill
        return {
            "color": "var(--rio-local-text-color)",
            "background": fill._as_css_background(self),
            "background-clip": "text",
            "fill-color": "transparent",
            "backdrop-filter": "none",
        }

    def _calculate_theme_css_values(self, thm: theme.Theme) -> dict[str, str]:
        """
        Determines and returns all CSS values that should be applied to a HTML
        element to achieve the given theme.
        """
        # Miscellaneous
        result: dict[str, str] = {
            "--rio-global-font": thm.font._serialize(self),
            "--rio-global-monospace-font": thm.monospace_font._serialize(self),
            "--rio-global-corner-radius-small": f"{thm.corner_radius_small}rem",
            "--rio-global-corner-radius-medium": f"{thm.corner_radius_medium}rem",
            "--rio-global-corner-radius-large": f"{thm.corner_radius_large}rem",
            "--rio-global-shadow-color": f"#{thm.shadow_color.hexa}",
        }

        # Palettes
        palette_names = (
            "primary",
            "secondary",
            "background",
            "neutral",
            "hud",
            "disabled",
            "success",
            "warning",
            "danger",
        )

        for palette_name in palette_names:
            palette = getattr(thm, f"{palette_name}_palette")
            assert isinstance(palette, theme.Palette), palette

            result[f"--rio-global-{palette_name}-bg"] = (
                f"#{palette.background.hexa}"
            )
            result[f"--rio-global-{palette_name}-bg-variant"] = (
                f"#{palette.background_variant.hexa}"
            )
            result[f"--rio-global-{palette_name}-bg-active"] = (
                f"#{palette.background_active.hexa}"
            )
            result[f"--rio-global-{palette_name}-fg"] = (
                f"#{palette.foreground.hexa}"
            )

        # Text styles
        style_names = (
            "heading1",
            "heading2",
            "heading3",
            "text",
        )

        for style_name in style_names:
            style: theme.TextStyle = getattr(thm, f"{style_name}_style")
            assert isinstance(style, rio.TextStyle), style

            css_prefix = f"--rio-global-{style_name}"
            result[f"{css_prefix}-font-name"] = (
                "inherit" if style.font is None else style.font._serialize(self)
            )
            result[f"{css_prefix}-font-size"] = f"{style.font_size}rem"
            result[f"{css_prefix}-font-style"] = (
                "italic" if style.italic else "normal"
            )
            result[f"{css_prefix}-font-weight"] = style.font_weight
            result[f"{css_prefix}-all-caps"] = (
                "uppercase" if style.all_caps else "unset"
            )

            text_decorations: list[str] = []

            if style.underlined:
                text_decorations.append("underline")

            if style.strikethrough:
                text_decorations.append("line-through")

            result[f"{css_prefix}-text-decoration"] = (
                " ".join(text_decorations) if text_decorations else "none"
            )

            # CSS variables for the fill
            assert style.fill is not None, (
                "Text fills must be defined the theme's text styles."
            )
            fill_variables = self._host_and_get_fill_as_css_variables(
                style.fill
            )

            for var, value in fill_variables.items():
                result[f"{css_prefix}-{var}"] = value

        # Done
        return result

    async def _apply_theme(self, thm: theme.Theme) -> None:
        # Store the theme in the session
        self.theme = thm

        # Get all CSS values to apply
        variables = self._calculate_theme_css_values(thm)

        # Update the variables client-side
        await self._remote_apply_theme(
            variables,
            (
                "light"
                if thm.neutral_palette.background.perceived_brightness > 0.5
                else "dark"
            ),
        )

    @deprecations.parameter_renamed(
        since="0.10.10",
        old_name="user_closeable",
        new_name="user_closable",
    )
    async def show_custom_dialog(
        self,
        build: t.Callable[[], rio.Component],
        *,
        modal: bool = True,
        user_closable: bool = True,
        on_close: rio.EventHandler[[]] = None,
        owning_component: rio.Component | None = None,
        style: t.Literal["default", "custom"] = "default",
    ) -> rio.Dialog:
        """
        Displays a custom dialog.

        This function displays a dialog to the user. This will call the `build`
        function and use its result as the content of the dialog. The content
        will be assigned the full size of the screen. This allows you to
        position the dialog yourself, using the align and margin properties of
        your component.

        By default, dialogs are styled similar to cards, hovering above the
        remainder of the content. If you want to take full control and style
        everything yourself, set `style` to `"custom"`. Note that in this
        case you'll probably want to set an alignment on your component so it
        doesn't take up the entire screen.

        Note: Dialogs are useful if you need to show components without
            returning them from the `build` method. A good example is asking for
            confirmation from an event handler, without having to rebuild the
            component. **If you can return components from the `build` method,
            `rio.Popup` is often an easier choice** (set `position` to
            `"fullscreen"` to get a similar look to dialogs).

        Note: If spawning many dialogs (for example when creating one for each
            item inside of a CRUD application) dialogs can be faster than
            `rio.Popup`, because dialogs only have to build their children when
            they're opened, while `rio.Popup` has its children built
            immediately, for every single item in the list.

        The result of this function is an instance of `rio.Dialog`, which can be
        used to interact with the dialog programmatically. For example, you can
        close the dialog or wait for it to be closed.

        Dialogs can store a result value, which can be retrieved by calling
        `Dialog.wait_for_close`. This allows you to easily wait for the dialog
        to disappear, and also get a return value while you're at it. See the
        example below for details.


        ## Parameters

        `build`: A function which creates the component to be displayed in the
            dialog. Please note that this is a function, not a component. You
            can of course pass a component _class_ as this function, as long as
            the constructor doesn't require any arguments.

        `modal`: Whether the dialog should prevent interactions with the rest of
            the app while it is open. If this is set, the background will also
            be darkened, to guide the user's focus to the dialog.

        `user_closable`: Whether the user can close the dialog, e.g by clicking
            outside of it.

        `on_close`: An event handler which is called when the dialog is closed.
            This will not be called if you explicitly remove the dialog by
            calling `dialog.close()`.

        `owning_component`: If provided, the dialog will close automatically
            should the owning component be destroyed. This is useful if you want
            a dialog to disappear when a user e.g. navigates away from the
            current page.

        `style`: Controls the appearance of the dialog. If `"default"`, it's
            styled similarly to a `Card`, hovering above the rest of the app. If
            `"custom"`, no styling is applied at all and your component covers
            the entire screen. Apply an alignment to your component to center it
            instead.

        ## Example

        This example demonstrates how to spawn a custom dialog that allows the
        user to select a value from a Dropdown menu. Once the user selects an
        option, the dialog closes, and the selected value is returned.

        ```python
        class MyComponent(rio.Component):
            value: str = "Vanilla"

            async def _create_dialog(self, options: list[str]) -> str | None:
                # This function will be called to create the dialog's content.
                # It builds up a UI using Rio components, just like a regular
                # `build` function would.
                def build_dialog_content() -> rio.Component:
                    # Build the dialog
                    return rio.Card(
                        rio.Column(
                            rio.Text(
                                "Which ice cream would you like?",
                                align_x=0.5,
                            ),
                            rio.Dropdown(
                                label="ice cream",
                                options=options,
                                selected_value=self.value,
                                on_change=on_value_change,
                            ),
                            spacing=1,
                            margin=2,
                        ),
                        align_x=0.5,
                        align_y=0.5,
                    )

                async def on_value_change(event: rio.DropdownChangeEvent) -> None:
                    # This function will be called whenever the user selects an
                    # Item. It simply closes the dialog with the selected value.
                    await dialog.close(event.value)

                # Show the dialog
                dialog = await self.session.show_custom_dialog(
                    build=build_dialog_content,
                    # Prevent the user from interacting with the rest of the app
                    # while the dialog is open
                    modal=True,
                    # Don't close the dialog if the user clicks outside of it
                    user_closable=False,
                )

                # Wait for the user to select an option
                result = await dialog.wait_for_close()

                # Return the selected value
                return result

            async def on_spawn_dialog(self) -> None:
                # Show a dialog and wait for the user to make a choice
                value = await self._create_dialog(
                    options=["Vanilla", "Chocolate", "Strawberry"],
                )

                # Store the value, but only if one was selected. If the dialog
                # gets closed without a selection, `value` will be `None`.
                if value is not None:
                    self.value = value

            def build(self) -> rio.Component:
                return rio.Column(
                    rio.Button(
                        "Open Dialog",
                        on_press=self.on_spawn_dialog,
                    ),
                    rio.Text(f"You've chosen: {self.value}"),
                    spacing=1,
                    align_x=0.5,
                    align_y=0.5,
                )
        ```


        ## Metadata

        `experimental`: True
        """
        # Verify that the passed build function is indeed a function, and
        # not already a component.
        #
        # There is no need for any further checks, since the function will
        # ultimately be called using the `safe_build` utility. Any incorrect
        # parameter expectations or results will be caught there.
        if not callable(build):
            raise ValueError(
                "The `build` parameter needs to be be a function, not an already created component. Try wrapping the component in a `lambda` function."
            )

        # Make sure nobody is building right now
        if (
            global_state.currently_building_component is not None
            or global_state.currently_building_session is not None
        ):
            raise RuntimeError(
                "Dialogs cannot be created inside of build functions. Create them in event handlers instead",
            )

        # Avoid an import cycle
        from . import dialog_container

        # Dialogs must always be owned. This simplifies the implementation, as
        # it avoids having to implement two different cases. If no owner is
        # provided, use the root component.
        #
        # Note that this has to be the fundamental root component, not the
        # high-level one, because only the fundamental root component exists in
        # the client-side.
        if owning_component is None:
            owning_component = self._fundamental_root_component

        # Build the dialog container. This acts as a known, permanent root
        # component for the dialog. It is recognized on the client-side and
        # handled appropriately.
        global_state.currently_building_component = owning_component
        global_state.currently_building_session = self

        dialog_container = dialog_container.DialogContainer(
            build_content=build,
            owning_component_id=owning_component._id_,
            is_modal=modal,
            is_user_closable=user_closable,
            on_close=on_close,
            style=style,
        )

        global_state.currently_building_component = None
        global_state.currently_building_session = None

        # Instantiate the dialog. This will act as a handle to the dialog and
        # returned so it can be used in future interactions.
        result = rio.Dialog._create(
            owning_component=owning_component,
            root_component=dialog_container,
        )

        # Register the dialog with the component. This keeps it (and contained
        # components) alive until the component is destroyed.
        owning_component._owned_dialogs_[dialog_container._id_] = result

        # Refresh. This will build any components in the dialog and send them to
        # the client
        await self._refresh()

        # Done
        return result

    async def show_simple_dialog(
        self,
        *,
        title: str,
        content: rio.Component | str,
        options: t.Mapping[str, T] | t.Sequence[T],
        # default_option: T | None = None,
        owning_component: rio.Component | None = None,
    ) -> T:
        """
        Display a simple dialog with a list of options.

        This function is highly experimental and **will change in the future.**
        Only use it if you feel adventurous.

        This is a convenience function which displays a simple dialog to the
        user, with a list of options to choose from. The user can select one of
        the options, and the function will return the value of the selected
        option.


        ## Parameters

        `title`: a heading to display at the top of the dialog.

        `content`: a component or markdown string to display below the title.

        `options`: a mapping of option names to their values. The user will be
            able to select one of these options.

        `owning_component`: If provided, the dialog will close automatically
            should the owning component be destroyed. This is useful if you want
            a dialog to disappear when a user e.g. navigates away from the
            current page.


        ## Example

        Here's a simple example that demonstrates how to spawn a dialog where
        the user can select one of multiple options:

        ```python
        class MyComponent(rio.Component):
            selected_value: str = ""

            async def on_spawn_dialog(self) -> None:
                # Display a dialog and wait until the user makes a choice.
                # Since `show_simple_dialog` is an asynchronous function, the
                # `on_spawn_dialog` function must also be asynchronous.
                selected_value = await self.session.show_simple_dialog(
                    title="Whats your favorite ice cream flavor?",
                    content="Which option do you choose?",
                    options=["Vanilla", "Strawberry", "Chocolate"],
                )

                # Store the value, but only if one was selected. If the dialog gets
                # closed without a selection, `selected_value` will be `None`.
                if selected_value is not None:
                    self.selected_value = selected_value

            def build(self) -> rio.Component:
                return rio.Column(
                    rio.Button(
                        "Open Dialog",
                        on_press=self.on_spawn_dialog,
                    ),
                    rio.Text(f"You've selected: {self.selected_value}"),
                    spacing=1,
                    align_x=0.5,
                    align_y=0.5,
                )
        ```


        ## Metadata

        `public`: False

        `experimental`: True
        """

        # Standardize the options
        if isinstance(options, t.Sequence):
            options = {str(value): value for value in options}

        # Prepare a build function
        def build_content() -> rio.Component:
            outer_margin = 0.8
            inner_margin = 0.4

            if isinstance(content, str):
                wrapped_content = rio.Markdown(
                    content,
                    margin_x=outer_margin,
                )
            else:
                wrapped_content = rio.Container(
                    content,
                    margin_x=outer_margin,
                )

            # build buttons container based on window width
            if self.window_width < 60:
                buttons_container = rio.Column(
                    *[
                        rio.Button(
                            oname,
                            on_press=lambda ovalue=ovalue: dialog.close(ovalue),
                            style="colored-text",
                        )
                        for oname, ovalue in options.items()
                    ],
                    spacing=inner_margin,
                    margin_x=5,
                    margin_top=0,
                )

            else:
                buttons_container = rio.Row(
                    *[
                        rio.Button(
                            oname,
                            on_press=lambda ovalue=ovalue: dialog.close(ovalue),
                            style="colored-text",
                        )
                        for oname, ovalue in options.items()
                    ],
                    spacing=inner_margin,
                    margin=outer_margin,
                    margin_top=0,
                    margin_left=5,
                )

            return rio.Card(
                rio.Column(
                    # Title
                    rio.Text(
                        title,
                        style="heading2",
                        overflow="wrap",
                        margin_x=outer_margin,
                        margin_top=outer_margin,
                    ),
                    # Content
                    wrapped_content,
                    # Separator
                    rio.Spacer(min_height=1.5, grow_y=False),
                    # Buttons
                    buttons_container,
                    spacing=inner_margin,
                ),
                align_x=0.5,
                align_y=0.35,
            )

        # Display the dialog
        dialog = await self.show_custom_dialog(
            build=build_content,
            owning_component=owning_component,
        )

        # Wait for the user to select an option
        result = await dialog.wait_for_close()
        result = t.cast(T, result)

        # Done!
        return result

    async def show_yes_no_dialog(
        self,
        text: str,
        *,
        title: str | None = None,
        icon: str | None = None,
        default: bool | None = None,
        yes_text: str = "Yes",
        no_text: str = "No",
        yes_color: rio.ColorSet = "keep",
        no_color: rio.ColorSet = "keep",
        owning_component: rio.Component | None = None,
    ) -> bool | None:
        """
        Displays a simple dialog with a yes and no button.

        This is a convenience function which displays a simple dialog to the
        user, with a "Yes" and "No" button. The user can select one of the
        options, and the function will return `True` or `False` respectively. If
        the user closes the dialog without selecting an option, `None` is
        returned instead.

        The button texts and colors can be customized.

        ## Parameters

        `title`: A heading to display at the top of the dialog.

        `text`: A markdown string to display below the title. This should
            explain to the user what the dialog is about.

        `icon`: An icon to display next to the title.

        `default`: The option the user is likely to take. This will highlight
            the respective button.

        `yes_text`: The text to display on the "Yes" button.

        `no_text`: The text to display on the "No" button.

        `yes_color`: The color of the "Yes" button.

        `no_color`: The color of the "No" button.

        `owning_component`: If provided, the dialog will close automatically
            should the owning component be destroyed. This is useful if you want
            a dialog to disappear when a user e.g. navigates away from the
            current page.


        ## Example

        Here's a simple example that demonstrates how to spawn a dialog where
        the user can select a boolean value:

        ```python
        class MyComponent(rio.Component):
            selected_value: bool = False

            async def on_spawn_dialog(self) -> None:
                # Display a dialog and wait until the user makes a choice.
                # Since `show_yes_no_dialog` is an asynchronous function, the
                # `on_spawn_dialog` function must also be asynchronous.
                selected_value = await self.session.show_yes_no_dialog(
                    title="This is a Dialog",
                    text="Do you like ice cream?",
                )

                # Store the value, but only if one was selected. If the dialog gets
                # closed without a selection, `selected_value` will be `None`.
                if selected_value is not None:
                    self.selected_value = selected_value

            def build(self) -> rio.Component:
                return rio.Column(
                    rio.Button(
                        "Open Dialog",
                        on_press=self.on_spawn_dialog,
                    ),
                    rio.Text(f"You've selected: {self.selected_value}"),
                )
        ```


        ## Metadata

        `experimental`: True
        """

        # Prepare a build function
        def build_content() -> rio.Component:
            main_column = rio.Column(
                spacing=1.0,
            )

            # Title & Icon
            title_components: list[rio.Component] = []

            if icon is not None:
                icon_size = self.theme.heading2_style.font_size * 1.1

                # Icons don't support the same fills as headings. Pick out a
                # valid option.
                for fill in (
                    self.theme.heading2_style.fill,
                    self.theme.heading3_style.fill,
                    self.theme.heading1_style.fill,
                    self.theme.text_style.fill,
                ):
                    if fill is not None:
                        break
                else:
                    fill = rio.Color.BLACK

                title_components.append(
                    rio.Icon(
                        icon,
                        fill=fill,
                        min_width=icon_size,
                        min_height=icon_size,
                    )
                )

            if title is not None:
                title_components.append(
                    rio.Text(
                        title,
                        style="heading2",
                        overflow="wrap",
                        grow_x=True,
                    )
                )

            if title_components:
                main_column.add(
                    rio.Row(
                        *title_components,
                        spacing=1.0,
                    )
                )

            # Content
            main_column.add(
                rio.Markdown(text),
            )

            # Buttons for mobile and desktop
            if self.window_width < 60:
                main_column.add(
                    rio.Column(
                        rio.Button(
                            yes_text,
                            color=yes_color,
                            style=(
                                "major" if default is True else "colored-text"
                            ),
                            shape="rounded",
                            on_press=lambda: dialog.close(True),
                        ),
                        rio.Button(
                            no_text,
                            color=no_color,
                            style=(
                                "major" if default is False else "colored-text"
                            ),
                            shape="rounded",
                            on_press=lambda: dialog.close(False),
                        ),
                        spacing=1.0,
                    ),
                )
            else:
                main_column.add(
                    rio.Row(
                        rio.Button(
                            yes_text,
                            color=yes_color,
                            style=(
                                "major" if default is True else "colored-text"
                            ),
                            shape="rounded",
                            on_press=lambda: dialog.close(True),
                        ),
                        rio.Button(
                            no_text,
                            color=no_color,
                            style=(
                                "major" if default is False else "colored-text"
                            ),
                            shape="rounded",
                            on_press=lambda: dialog.close(False),
                        ),
                        spacing=1.0,
                        margin_top=1,
                        margin_left=5,
                        align_x=1,
                    ),
                )

            return main_column

        # Display the dialog
        dialog = await self.show_custom_dialog(
            build=build_content,
            modal=True,
            user_closable=True,
            owning_component=owning_component,
            style="default",
        )

        # Wait for the user to select an option
        result = await dialog.wait_for_close()
        assert isinstance(result, bool) or result is None, result

        # Done!
        return result

    @unicall.remote(
        name="applyTheme",
        await_response=False,
    )
    async def _remote_apply_theme(
        self,
        css_variables: dict[str, str],
        theme_variant: t.Literal["light", "dark"],
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="setTitle",
        await_response=False,
    )
    async def _remote_set_title(self, title: str) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="setKeyboardFocus",
        await_response=False,
    )
    async def _remote_set_keyboard_focus(self, component_id: int) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="updateComponentStates",
        await_response=False,
    )
    async def _remote_update_component_states(
        self,
        # Maps component ids to serialized components. The components may be
        # partial, i.e. any property may be missing.
        delta_states: dict[int, t.Any],
        # Tells the client to make the given component the new root component.
        root_component_id: int | None,
    ) -> None:
        """
        Replace all components in the UI with the given one.
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="evaluateJavaScript",
        await_response=False,
    )
    async def _evaluate_javascript(self, java_script_source: str) -> t.Any:
        """
        Evaluate the given JavaScript code on the client.

        The code is run as the body of a function, i.e.

        - `return` statements are allowed

        - Variables are neatly contained in a scope and don't pollute the global
          scope
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="evaluateJavaScriptAndGetResult",
        await_response=True,
    )
    async def _evaluate_javascript_and_get_result(
        self,
        java_script_source: str,
    ) -> t.Any:
        """
        Evaluate the given JavaScript code in the client and return the result.

        The code is run as the body of a function, i.e.

        - `return` statements are allowed and must be used to receive a result
          other than `None`

        - Variables are neatly contained in a scope and don't pollute the global
          scope
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="requestFileUpload",
        await_response=False,
    )
    async def _request_file_upload(
        self,
        upload_url: str,
        file_types: list[str] | None,
        multiple: bool,
    ) -> None:
        """
        Tell the client to upload a file to the server.

        If `file_types` is provided, the strings should be file extensions,
        without any leading dots. E.g. `["pdf", "png"]`.
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(name="setUserSettings", await_response=False)
    async def _set_user_settings(
        self, delta_settings: dict[str, t.Any]
    ) -> None:
        """
        Persistently store the given key-value pairs at the user. The values
        have to be jsonable.

        Any keys not present here are still preserved. Thus the function
        effectively behaves like `dict.update`.
        """
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(name="registerFont", await_response=False)
    async def _remote_register_font(
        self, name: str, urls: list[str | None]
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(name="changeUrl", await_response=False)
    async def _remote_url_change(self, url: str, replace: bool) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="closeSession",
        await_response=False,
    )
    async def _remote_close_session(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def _try_get_component_for_message(
        self, component_id: int
    ) -> rio.Component | None:
        """
        Attempts to get the component referenced by `component_id`. Returns
        `None` if there is no such component. This can happen during normal
        opration, e.g. because a component has been deleted while the message
        was in flight.
        """

        try:
            return self._weak_components_by_id[component_id]
        except KeyError:
            logging.warning(
                f"Encountered message for unknown component {component_id}. (The component might have been deleted in the meantime.)"
            )
            return None

    @unicall.local(name="componentStateUpdate")
    async def _component_state_update(
        self,
        component_id: int,
        delta_state: t.Any,
    ) -> None:
        # Get the component
        component = self._try_get_component_for_message(component_id)

        if component is None:
            return

        assert isinstance(
            component, fundamental_component.FundamentalComponent
        ), component

        # Update the component's state
        component._validate_delta_state_from_frontend(delta_state)
        component._apply_delta_state_from_frontend(delta_state)
        await component._call_event_handlers_for_delta_state(delta_state)

        # Trigger a refresh. The component itself doesn't need to rebuild, but
        # other components with a attribute binding to the changed values might.
        await self._refresh()

    @unicall.local(name="componentMessage")
    async def _component_message(
        self,
        component_id: int,
        payload: t.Any,
    ) -> None:
        # Get the component
        component = self._try_get_component_for_message(component_id)

        if component is None:
            return

        # Let the component handle the message
        await component._on_message_(payload)

    @unicall.local(name="dialogClosed")
    async def _dialog_closed(self, dialog_root_component_id: int) -> None:
        # Fetch and remove the dialog itself, while still not succumbing to
        # network lag
        try:
            dialog_cont = self._weak_components_by_id[dialog_root_component_id]
        except KeyError:
            return

        assert isinstance(dialog_cont, dialog_container.DialogContainer), (
            dialog_cont
        )

        # Fetch the owning component
        try:
            dialog_owner = self._weak_components_by_id[
                dialog_cont.owning_component_id
            ]
        except KeyError:
            # Don't die to network lag
            return

        # Fetch the Dialog object and mark it as closed
        try:
            dialog = dialog_owner._owned_dialogs_[dialog_root_component_id]
        except KeyError:
            # Don't die to network lag
            return

        dialog._close_internal(result_value=None)

        # Trigger the dialog's close event
        await self._call_event_handler(
            dialog_cont.on_close,
            refresh=True,
        )

    @unicall.local(name="openUrl")
    async def _open_url(self, url: str) -> None:
        # Case: Running as website
        #
        # If running in a browser, JS can take care of changing the URL or
        # opening a new tab. The only reason why the frontend would tell us
        # to open the url is because it's a local url.
        #
        # (Note: Of course an attacker could send us an external url to
        # open, but `navigate_to` has to handle that gracefully anyway.)
        if self.running_as_website:
            self.navigate_to(url)
            return

        # Case: Running in a window.
        yarl_url = rio.URL(url)
        del url

        # If running_in_window, local urls are *always* navigated to, even if
        # they're meant to be opened in a new tab. The `run_in_window` code
        # isn't designed to handle multiple sessions, so we can't open a new
        # tab or a 2nd window.
        try:
            utils.url_relative_to_base(yarl_url, self._base_url)

        # And if it's an external url, it must be opened in a web browser.
        except ValueError:
            import webbrowser

            webbrowser.open(str(yarl_url))

        # Local URL
        else:
            self.navigate_to(yarl_url)

    @unicall.local(name="ping")
    async def _ping(self, ping: str) -> str:
        return "pong"

    @unicall.local(name="onUrlChange")
    async def _on_url_change(self, new_url: str) -> None:
        """
        Called by the client when the page changes. (This happens when the user
        presses the "back" button in the browser.)
        """
        self.navigate_to(
            new_url,
            # Since the URL change originated in the browser, it's actually
            # already recorded in the history. We don't want to create an
            # additional entry, so we'll simply use `replace` to overwrite it
            # with itself.
            replace=True,
        )

    @unicall.local(name="onWindowSizeChange")
    async def _on_window_size_change(
        self, new_width: float, new_height: float
    ) -> None:
        """
        Called by the client when the window is resized.
        """
        # Update the stored window size
        self.window_width = new_width
        self.window_height = new_height

        # Trigger the `on_page_size_change` event
        for (
            component,
            callbacks,
        ) in self._on_window_size_change_callbacks.items():
            for callback in callbacks:
                self.create_task(
                    self._call_event_handler(callback, component, refresh=True),
                    name="`on_on_window_size_change` event handler",
                )

    @unicall.local(name="onFullscreenChange")
    async def _on_fullscreen_change(self, fullscreen: bool) -> None:
        """
        Called by the client when the window is (un-)fullscreened.
        """
        self._is_fullscreen = fullscreen

    @unicall.local(name="onMaximizedChange")
    async def _on_maximized_change(self, maximized: bool) -> None:
        """
        Called by the client when the window is (un-)maximized.
        """
        self._is_maximized = maximized

    @unicall.remote(
        name="setClipboard",
        await_response=False,
    )
    async def _remote_set_clipboard(self, text: str) -> None:
        raise NotImplementedError  # pragma: no cover

    @unicall.remote(
        name="getClipboard",
        await_response=True,
    )
    async def _remote_get_clipboard(self) -> str:
        raise NotImplementedError  # pragma: no cover

    async def set_clipboard(self, text: str) -> None:
        """
        Copies the given text to the client's clipboard.

        This function updates the client's clipboard with the given text. This
        can be useful for providing the user with a quick way to copy data from
        the app to other applications.

        Unlike reading the clipboard this is usually allowed by browsers as it
        does not pose a security risk.

        ## Parameters

        `text`: The text to copy to the clipboard.

        ## Raises

        `ClipboardError`: If the user's browser doesn't allow or support
            clipboard operations.
        """
        if self.running_in_window:
            import copykitten  # type: ignore (module not found)

            try:
                copykitten.copy(text)
            except copykitten.CopykittenError as e:
                raise errors.ClipboardError(str(e)) from None
        else:
            try:
                await self._remote_set_clipboard(text)
            except unicall.RpcError as e:
                raise errors.ClipboardError(e.message) from None

    async def get_clipboard(self) -> str | None:
        """
        Gets the current text from the client's clipboard.

        Attempts to read the current text from the client's clipboard. This can
        be useful for providing the user with a quick way to copy data from
        other applications to the app.

        Note that this operation can fail if running as website and the user
        does not grant special permissions to the website. Thats because
        reading the clipboard can be a privacy & security risk as it can contain
        sensitive information such as passwords.

        ## Raises

        `ClipboardError`: If the user's browser doesn't allow or support
            clipboard operations.
        """
        if self.running_in_window:
            import copykitten  # type: ignore (module not found)

            try:
                return copykitten.paste()
            except copykitten.CopykittenError:
                return None
        else:
            try:
                return await self._remote_get_clipboard()
            except unicall.RpcError as e:
                raise errors.ClipboardError(e.message) from None

    async def _get_component_layouts(
        self, component_ids: list[int]
    ) -> list[data_models.ComponentLayout]:
        """
        Gets layout information about the given components.

        ## Raises

        `KeyError`: If any component cannot be found client-side. (This will
            also be raised if the component's parent cannot be found, since some
            parent information is also exposed)
        """
        # The component's actual layout is only known to the frontend. Ask
        # for it.
        raw_result = await self._remote_get_component_layouts(component_ids)

        # Wrap the JSON in a nice container class
        result: list[data_models.ComponentLayout] = []

        for component_id, json_doc in zip(component_ids, raw_result):
            if json_doc is None:
                raise KeyError(component_id)

            result.append(
                serialization.json_serde.from_json(
                    data_models.ComponentLayout,
                    json_doc,
                )
            )

        return result

    @unicall.remote(
        name="getComponentLayouts",
        await_response=True,
    )
    async def _remote_get_component_layouts(
        self, component_ids: list[int]
    ) -> list[dict[str, t.Any] | None]:
        raise NotImplementedError()  # pragma: no cover

    async def _get_unittest_client_layout_info(
        self,
    ) -> data_models.UnittestClientLayoutInfo:
        # The result contains a dictionary with `int` keys. Since JSON can't
        # handle that, they need to be converted. This function does that.

        # Get the raw result
        raw_result = await self.__get_unittest_client_layout_info()

        # Deserialize the result
        result = data_models.UnittestClientLayoutInfo(
            window_width=raw_result["windowWidth"],
            window_height=raw_result["windowHeight"],
            component_layouts={
                int(component_id): serialization.json_serde.from_json(
                    UnittestComponentLayout,
                    layout,
                )
                for component_id, layout in raw_result[
                    "componentLayouts"
                ].items()
            },
        )

        # On the Python side, the root component is a high level root component.
        # This however is never sent to the client, so it'll be missing from the
        # result. Add it back in.
        hl_root_component = self._high_level_root_component
        assert isinstance(
            hl_root_component,
            rio.components.root_components.HighLevelRootComponent,
        ), hl_root_component

        ll_root_component = hl_root_component._build_data_.build_result  # type: ignore
        assert isinstance(
            ll_root_component,
            rio.components.root_components.FundamentalRootComponent,
        ), ll_root_component

        ll_layout = result.component_layouts[ll_root_component._id_]
        hl_layout = copy.deepcopy(ll_layout)
        hl_layout.aux = {}
        result.component_layouts[hl_root_component._id_] = hl_layout

        ll_layout.parent_id = hl_root_component._id_

        # Done
        return result

    @unicall.remote(
        name="getUnittestClientLayoutInfo",
        await_response=True,
    )
    async def __get_unittest_client_layout_info(
        self,
    ) -> t.Any:
        raise NotImplementedError()  # pragma: no cover

    @unicall.remote(
        name="pickComponent",
        await_response=False,
    )
    async def _pick_component(self) -> None:
        """
        Lets the user select a component in the ComponentTree by clicking on it
        in the DOM.
        """
        raise NotImplementedError()  # pragma: no cover

    @unicall.remote(
        name="removeDialog",
        await_response=False,
    )
    async def _remove_dialog(self, root_component_id: int) -> None:
        """
        Removes the dialog with the given root component id, destroying the
        component and its children.
        """
        raise NotImplementedError()  # pragma: no cover

    def __repr__(self) -> str:
        return f"<Session {self.client_ip}:{self.client_port}>"


def extract_child_components(
    component: rio.Component,
    attr_name: str,
) -> list[rio.Component]:
    attr = getattr(component, attr_name, None)

    if isinstance(attr, rio.Component):
        return [attr]

    try:
        iterator = iter(attr)  # type: ignore
    except TypeError:
        pass
    else:
        return [item for item in iterator if isinstance(item, rio.Component)]

    return []
