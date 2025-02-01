from __future__ import annotations

import pytz
import starlette.datastructures

import rio

from .. import assets, utils
from ..transports import MessageRecorderTransport
from .abstract_app_server import AbstractAppServer

__all__ = ["TestingServer"]


class TestingServer(AbstractAppServer):
    def __init__(
        self,
        app: rio.App,
        *,
        running_in_window: bool = False,
        debug_mode: bool = False,
        base_url: rio.URL | None = None,
    ) -> None:
        super().__init__(
            app,
            running_in_window=running_in_window,
            debug_mode=debug_mode,
            base_url=base_url,
        )

    def create_dummy_session(self) -> rio.Session:
        url = rio.URL("http://localhost")

        theme = self.app._theme
        if isinstance(theme, tuple):
            theme = theme[0]

        return rio.Session(
            app_server_=self,
            transport=MessageRecorderTransport(),
            client_ip="localhost",
            client_port=1234,
            http_headers=starlette.datastructures.Headers(),
            timezone=pytz.UTC,
            preferred_languages=["en-US"],
            month_names_long=(
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ),
            day_names_long=(
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ),
            date_format_string="",
            first_day_of_week=0,
            decimal_separator=".",
            thousands_separator=",",
            screen_width=800,
            screen_height=600,
            window_width=800,
            window_height=600,
            pixels_per_font_height=16,
            scroll_bar_size=16,
            primary_pointer_type="mouse",
            base_url=url,
            active_page_url=url,
            theme_=theme,
        )

    def weakly_host_asset(self, asset: assets.HostedAsset) -> rio.URL:
        # This method is called for font files, even in a test session, so it
        # actually needs to be implemented.
        return rio.URL(asset.secret_id)

    def external_url_for_user_asset(
        self, relative_asset_path: assets.Path
    ) -> rio.URL:
        raise NotImplementedError

    async def pick_file(
        self,
        session: rio.Session,
        *,
        file_types: list[str] | None = None,
        multiple: bool = False,
    ) -> utils.FileInfo | list[utils.FileInfo]:
        raise NotImplementedError
