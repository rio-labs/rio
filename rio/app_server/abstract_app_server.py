from __future__ import annotations

import abc
import asyncio
import inspect
import json
import logging
import time
import traceback
import warnings
import weakref
from datetime import date
from pathlib import Path

import langcodes
import pytz
import starlette.datastructures

import rio
import rio.assets

from .. import (
    assets,
    data_models,
    language_info,
    routing,
    session,
    user_settings_module,
    utils,
)
from ..transports import (
    AbstractTransport,
)

__all__ = ["AbstractAppServer"]


class AbstractAppServer(abc.ABC):
    def __init__(
        self,
        app: rio.App,
        *,
        running_in_window: bool,
        debug_mode: bool,
        base_url: rio.URL | None = None,
    ) -> None:
        self.app = app
        self.running_in_window = running_in_window
        self.debug_mode = debug_mode

        # This is the URL the app's home page is hosted at, as seen from the
        # client. So if the user needs to type `https://example.com/my-app/` to
        # see the app, this will be `https://example.com/my-app/`. Note that
        # this is not necessarily the URL Python gets to see in HTTP requests,
        # as it is common practice to have a reverse proxy rewrite the URLs of
        # HTTP requests.
        #
        # An important consideration with the base URL is, that the full URL
        # must be known for some scenarios. For example, the `robots.txt` has to
        # return the full URL of the sitemap, since not all (none?) search
        # engines will follow relative URLs.
        #
        # This is currently handled as follows: If a base URL is specified, it
        # must contain the full URL. If no base URL is specified, the URL
        # provided in the request is used instead.
        self.base_url = base_url
        self._session_serve_tasks = dict[rio.Session, asyncio.Task[object]]()
        self._disconnected_sessions = dict[rio.Session, float]()

    @property
    def sessions(self) -> list[rio.Session]:
        return list(self._session_serve_tasks)

    async def _on_start(self) -> None:
        # Trigger the app's startup event
        #
        # This will be done blockingly, so the user can prepare any state before
        # connections are accepted. This is also why it's called before the
        # internal event.
        await self._call_on_app_starts()

        # If running as a server, periodically clean up expired sessions
        if not self.running_in_window:
            asyncio.create_task(
                _periodically_clean_up_expired_sessions(weakref.ref(self)),
                name="Periodic session cleanup",
            )

    async def _on_close(self) -> None:
        # Close all sessions
        rio._logger.debug(
            f"App server shutting down; closing {len(self.sessions)} active session(s)"
        )

        # On Linux, some of these tasks are sometimes canceled, resulting in a
        # visible, ugly traceback in the console. Debugging has been fruitless
        # so far, hence the `asyncio.shield` hack.
        #
        # That wasn't enough though - hence the additional `try` block, because
        # nothing beats fixing a bad bandage than adding another one.
        try:
            results = await asyncio.shield(
                asyncio.gather(
                    *(
                        sess._close(close_remote_session=True)
                        for sess in self.sessions
                    ),
                    return_exceptions=True,
                )
            )
        except asyncio.CancelledError:
            pass
        else:
            for result in results:
                if isinstance(result, BaseException):
                    traceback.print_exception(
                        type(result), result, result.__traceback__
                    )

        await self._call_on_app_close()

    async def _call_on_app_starts(self) -> None:
        rio._logger.debug("Calling `on_app_start`")

        # Call the app's function
        if self.app._on_app_start is not None:
            try:
                result = self.app._on_app_start(self.app)

                if inspect.isawaitable(result):
                    await result

            # Display and discard exceptions
            except Exception:
                print("Exception in `on_app_start` event handler:")
                traceback.print_exc()

        # Call the functions of any extensions
        await self.app._call_event_handlers(
            self.app._extension_on_app_start_handlers,
            rio.ExtensionAppStartEvent(
                self.app,
            ),
        )

    async def _call_on_app_close(self) -> None:
        rio._logger.debug("Calling `on_app_close`")

        # Call the app's function
        if self.app._on_app_close is not None:
            try:
                result = self.app._on_app_close(self.app)

                if inspect.isawaitable(result):
                    await result

            # Display and discard exceptions
            except Exception:
                print("Exception in `_on_app_close` event handler:")
                traceback.print_exc()

        # Call the functions of any extensions
        await self.app._call_event_handlers(
            self.app._extension_on_app_close_handlers,
            rio.ExtensionAppCloseEvent(
                self.app,
            ),
        )

    @abc.abstractmethod
    async def pick_file(
        self,
        session: rio.Session,
        *,
        file_types: list[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        raise NotImplementedError

    @abc.abstractmethod
    def external_url_for_user_asset(self, relative_asset_path: Path) -> rio.URL:
        """
        Returns the URL of an asset from the app's `assets_dir`. This must be a
        permalink, i.e. a URL that doesn't change if the server is restarted.

        The returned URL is **external**, i.e. which value would have to be
        typed into the browser to access it. The URL visible to Python can
        differ from this, e.g. because of a reverse proxy.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def weakly_host_asset(self, asset: assets.HostedAsset) -> rio.URL:
        """
        Hosts an asset as long as it is alive. Returns the asset's URL as a
        string.

        The returned URL is **external**, i.e. which value would have to be
        typed into the browser to access it. The URL visible to Python can
        differ from this, e.g. because of a reverse proxy.
        """
        raise NotImplementedError

    def host_asset_with_timeout(
        self, asset: assets.HostedAsset, timeout: float
    ) -> rio.URL:
        """
        Hosts an asset for a limited time. Returns the asset's URL as a string.
        """
        url = self.weakly_host_asset(asset)

        async def keep_alive() -> None:
            await asyncio.sleep(timeout)
            _ = asset

        asyncio.create_task(
            keep_alive(), name=f"Keep asset {asset} alive for {timeout} sec"
        )

        return url

    def _after_session_closed(self, session: rio.Session) -> None:
        """
        Called by `Session.close()`. Gives the server an opportunity to clean
        up.
        """
        # Stop the task that's listening for incoming messages
        task = self._session_serve_tasks.pop(session)
        task.cancel("Session has closed")

    async def create_session(
        self,
        initial_message: data_models.InitialClientMessage,
        *,
        transport: AbstractTransport,
        client_ip: str,
        client_port: int,
        http_headers: starlette.datastructures.Headers,
    ) -> rio.Session:
        """
        Creates a new session.

        ## Raises

        `NavigationFailed`: If a page guard crashes.

        `NavigationFailed`: If the initial page URL is not a child of the app's
            base URL.
        """
        # Normalize and deduplicate the languages
        preferred_languages: list[str] = []

        for language in initial_message.preferred_languages:
            try:
                language = langcodes.standardize_tag(language)
            except ValueError:
                continue

            if language not in preferred_languages:
                preferred_languages.append(language)

        if len(preferred_languages) == 0:
            preferred_languages.append("en-US")

        # Get locale information
        if len(initial_message.decimal_separator) != 1:
            logging.warning(
                f'Client sent invalid decimal separator "{initial_message.decimal_separator}". Using "." instead.'
            )
            initial_message.decimal_separator = "."

        if len(initial_message.thousands_separator) > 1:
            logging.warning(
                f'Client sent invalid thousands separator "{initial_message.thousands_separator}". Using "" instead.'
            )
            initial_message.thousands_separator = ""

        # There does not seem to be any good way to determine the first day of
        # the week in JavaScript. Look it up based on the preferred language.
        first_day_of_week = language_info.get_week_start_day(
            preferred_languages[0]
        )

        # Make sure the date format string is valid
        try:
            formatted_date = date(3333, 11, 22).strftime(
                initial_message.date_format_string
            )
        except ValueError:
            date_format_string_is_valid = False
        else:
            date_format_string_is_valid = (
                "33" in formatted_date
                and "11" in formatted_date
                and "22" in formatted_date
            )

        if not date_format_string_is_valid:
            logging.warning(
                f'Client sent invalid date format string "{initial_message.date_format_string}". Using "%Y-%m-%d" instead.'
            )
            initial_message.date_format_string = "%Y-%m-%d"

        # Parse the timezone
        try:
            timezone = pytz.timezone(initial_message.timezone)
        except pytz.UnknownTimeZoneError:
            logging.warning(
                f'Client sent unknown timezone "{initial_message.timezone}". Using UTC instead.'
            )
            timezone = pytz.UTC

        # Set the theme according to the user's preferences
        theme = self.app._theme
        if isinstance(theme, tuple):
            if initial_message.prefers_light_theme:
                theme = theme[0]
            else:
                theme = theme[1]

        # Prepare the initial URL. This will be exposed to the session as the
        # `active_page_url`, but overridden later once the page guards have been
        # run.
        initial_page_url = rio.URL(initial_message.url)

        # Determine the base URL. If one was explicitly provided when creating
        # the app server, use that. Otherwise derive one from the initial HTTP
        # request.
        if self.base_url is None:
            base_url = (
                initial_page_url.with_path("").with_query("").with_fragment("")
            )
        else:
            base_url = self.base_url

        # Create the session
        sess = session.Session(
            app_server_=self,
            transport=transport,
            client_ip=client_ip,
            client_port=client_port,
            http_headers=http_headers,
            base_url=base_url,
            active_page_url=initial_page_url,
            timezone=timezone,
            preferred_languages=preferred_languages,
            month_names_long=initial_message.month_names_long,
            day_names_long=initial_message.day_names_long,
            date_format_string=initial_message.date_format_string,
            first_day_of_week=first_day_of_week,
            decimal_separator=initial_message.decimal_separator,
            thousands_separator=initial_message.thousands_separator,
            screen_width=initial_message.screen_width,
            screen_height=initial_message.screen_height,
            window_width=initial_message.window_width,
            window_height=initial_message.window_height,
            pixels_per_font_height=initial_message.physical_pixels_per_font_height,
            scroll_bar_size=initial_message.scroll_bar_size,
            primary_pointer_type=initial_message.primary_pointer_type,
            theme_=theme,
        )

        # Deserialize the user settings
        await sess._load_user_settings(initial_message.user_settings)

        # Add any remaining attachments
        for attachment in self.app.default_attachments:
            if not isinstance(attachment, user_settings_module.UserSettings):
                sess.attach(attachment)

        # Start listening for incoming messages. This should happen before
        # `on_session_start` is called, so that we don't deadlock in case
        # someone calls a method that requires a response from the client.
        self._session_serve_tasks[sess] = asyncio.create_task(
            sess.serve(),
            name=f"`Session.serve()` for session id `{id(sess)}`",
        )

        # Trigger the `on_session_start` event.
        #
        # Since this event is often used for important initialization tasks like
        # adding attachments, actually wait for it to finish before continuing.
        #
        # However, also don't run it too early, since this function expects a
        # (mostly) functioning session.
        #
        # TODO: Figure out which values are still missing, and expose them,
        #       expose placeholders, or document that they aren't available.
        start_time = time.monotonic()
        await sess._call_event_handler(
            self.app._on_session_start,
            sess,
            refresh=False,
        )
        duration = time.monotonic() - start_time

        if duration > 5:
            warnings.warn(
                f"Session startup was delayed for {duration:.0f} seconds by"
                f" `on_session_start`. If you have long-running operations that"
                f" don't have to finish before the session starts, you should"
                f" execute them in a background task."
            )

        # Extensions may also have `on_session_start` handlers
        await self.app._call_event_handlers(
            self.app._extension_on_session_start_handlers,
            rio.ExtensionSessionStartEvent(
                sess,
            ),
        )

        # Run any page guards for the initial page. Throws a `NavigationFailed`
        # if a page guard crashed.
        (
            active_page_instances_and_path_arguments,
            active_page_url_absolute,
        ) = routing.check_page_guards(sess, initial_page_url)

        # The initial page URL can be problematic. Logically it must obviously
        # be a child of the app's base URL, but that may not be the case if a
        # malicious URL was sent or the base misconfigured. Check for this.
        if active_page_instances_and_path_arguments is None:
            raise rio.NavigationFailed(
                f"The initial page URL `{initial_page_url}` is not a child of the app's base URL `{self.base_url}`."
            )

        # Is this a page, or a full URL to another site?
        try:
            utils.url_relative_to_base(
                sess._base_url,
                active_page_url_absolute,
            )

        # This is an external URL. Navigate to it
        except ValueError:

            async def history_worker() -> None:
                await sess._evaluate_javascript(
                    f"""
                    window.location.href = {json.dumps(str(active_page_url_absolute))};
                    """
                )

            sess.create_task(history_worker(), name="navigate to external URL")

            # TODO: End the session? Abort initialization?

        # Set the initial page URL. When connecting to the server, all relevant
        # page guards execute. These may change the URL of the page, so the
        # client needs to take care to update the browser's URL to match the
        # server's.
        if active_page_url_absolute != initial_page_url:

            async def update_url_worker():
                js_page_url = json.dumps(str(active_page_url_absolute))
                await sess._evaluate_javascript(
                    f"""
                    console.trace("Updating browser URL to match the one modified by guards:", {js_page_url});
                    window.history.replaceState(null, "", {js_page_url});
                    """
                )

            sess.create_task(
                update_url_worker(),
                name="Update browser URL to match the one modified by guards",
            )

        # Update the session's active page and instances
        sess._active_page_url = active_page_url_absolute
        sess._active_page_instances_and_path_arguments = (
            active_page_instances_and_path_arguments
        )
        sess._active_page_instances = tuple(
            page for page, _ in active_page_instances_and_path_arguments
        )

        # Apply the CSS for the chosen theme
        await sess._apply_theme(theme)

        # Send the first `updateComponentStates` message
        await sess._refresh()

        # Now that the initialization is complete, allow the session to
        # auto-refresh whenever necessary
        sess.create_task(sess._refresh_whenever_necessary())

        return sess


async def _periodically_clean_up_expired_sessions(
    app_server_ref: weakref.ReferenceType[AbstractAppServer],
) -> None:
    LOOP_INTERVAL = 60 * 15
    SESSION_LIFETIME = 60 * 60

    while True:
        await asyncio.sleep(LOOP_INTERVAL)

        app_server = app_server_ref()
        if app_server is None:
            return

        now = time.monotonic()
        cutoff = now - SESSION_LIFETIME

        disconnected_sessions = list(app_server._disconnected_sessions.items())
        for sess, disconnect_time in disconnected_sessions:
            if disconnect_time < cutoff:
                sess.close()

        # Drop the reference to the app server
        app_server = None
