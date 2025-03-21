from __future__ import annotations

import dataclasses
import typing as t

# Never import * from typing_extensions! It breaks `Any` on 3.10, preventing
# users from connecting. Ask me how I know.
import typing_extensions as te
import uniserde

import rio

__all__ = ["BuildData", "ComponentLayout", "InitialClientMessage"]


@dataclasses.dataclass
class BuildData:
    build_result: rio.Component

    all_children_in_build_boundary: set[rio.Component]
    key_to_component: dict[rio.components.component.Key, rio.Component]


@dataclasses.dataclass
class InitialClientMessage:
    # The URL the client used to connect to the website. This can be quite
    # different from the URLs we see in FastAPI requests, because proxies like
    # nginx can alter it. For example, the client may be connecting via https
    # while rio only sees http.
    url: str

    # Don't annotate this as JsonDoc because uniserde doesn't support unions
    user_settings: dict[str, t.Any]

    prefers_light_theme: bool

    # List of RFC 5646 language codes. Most preferred first. May be empty!
    preferred_languages: list[str]

    # The names for all months, starting with January
    month_names_long: tuple[
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        str,
    ]

    # The names of all weekdays, starting with monday
    day_names_long: tuple[
        str,
        str,
        str,
        str,
        str,
        str,
        str,
    ]

    # The format string for dates, as used by Python's `strftime`
    date_format_string: str

    # IANA timezone
    timezone: str

    # Separators for number rendering
    decimal_separator: str
    thousands_separator: str

    # Device Information
    screen_width: float
    screen_height: float

    window_width: float
    window_height: float

    physical_pixels_per_font_height: float
    scroll_bar_size: float

    primary_pointer_type: t.Literal["mouse", "touch"]

    @classmethod
    def from_defaults(
        cls,
        *,
        url: str,
        user_settings: uniserde.JsonDoc = {},
    ) -> te.Self:
        """
        Convenience method for creating default settings when they don't really
        matter: unit tests, crawlers, etc.
        """
        return cls(
            url=url,
            user_settings=user_settings,
            prefers_light_theme=True,
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
            date_format_string="%Y-%m-%d",
            timezone="America/New_York",
            decimal_separator=".",
            thousands_separator=",",
            primary_pointer_type="mouse",
            screen_width=1920,
            screen_height=1080,
            window_width=1920,
            window_height=1080,
            physical_pixels_per_font_height=16,
            scroll_bar_size=16,
        )


# class CliConfig(uniserde.Config):
#     # Whether to automatically open the browser when running an app using `rio
#     # run`. This has no effect on functions that are explicitly meant to open
#     # browsers, such as `app.run_in_browser`.
#     open_browser_on_startup: bool = True


@dataclasses.dataclass
class ComponentLayout:
    # The minimum amount of size needed by the component. The width is
    # calculated first, meaning the height can depend on the width. (i.e. a
    # text's height depends on the width because it wraps)
    natural_width: float
    natural_height: float

    # Components can request more space than their natural size if a size was
    # explicitly provided on the Python-side. This value is the maximum of the
    # natural size and any explicitly provided size.
    requested_inner_width: float
    requested_inner_height: float

    # The requested width after scrolling, alignment and margin.
    requested_outer_width: float
    requested_outer_height: float

    # The amount of space allocated to the component before scrolling,
    # alignment and margin.
    allocated_outer_width: float
    allocated_outer_height: float

    # The amount of space allocated to the component after scrolling,
    # alignment and margin.
    allocated_inner_width: float
    allocated_inner_height: float

    # The component's position relative to the viewport before scrolling,
    # alignment and margin.
    left_in_viewport_outer: float
    top_in_viewport_outer: float

    # The component's position relative to the viewport after scrolling,
    # alignment and margin.
    left_in_viewport_inner: float
    top_in_viewport_inner: float

    # The id of the parent component, unless this is the root component.
    parent_id: int | None


@dataclasses.dataclass
class UnittestComponentLayout(ComponentLayout):
    # Additional, component-specific information
    aux: dict[str, t.Any]


@dataclasses.dataclass
class UnittestClientLayoutInfo:
    window_width: float
    window_height: float

    component_layouts: dict[int, UnittestComponentLayout]
