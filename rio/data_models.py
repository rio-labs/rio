from dataclasses import dataclass
from typing import *  # type: ignore

import uniserde

# Never import * from typing_extensions! It breaks `Any` on 3.10, preventing
# users from connecting. Ask me how I know.
from typing_extensions import Self

__all__ = ["ComponentLayout", "InitialClientMessage"]


@dataclass
class ComponentLayout:
    """
    Stores information about a component's layout. This includes the position
    and size that was actually allocated, rather than just requested.
    """

    # The component's position relative to the top-left corner of the viewport
    left_in_viewport: float
    top_in_viewport: float

    # The component's position relative to the top-left corner of the parent
    left_in_parent: float
    top_in_parent: float

    # How much space the component has requested
    natural_width: float
    natural_height: float

    # How much space the component was actually allocated
    allocated_width: float
    allocated_height: float

    # Aligned components are only given as much space as they need. This is how
    # much space the component was allocated prior to alignment.
    allocated_width_before_alignment: float
    allocated_height_before_alignment: float


@dataclass
class InitialClientMessage(uniserde.Serde):
    # Don't annotate this as JsonDoc, uniserde can't handle it
    user_settings: dict[str, Any]

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

    # Window Information
    window_width: float
    window_height: float

    @classmethod
    def from_defaults(cls, *, user_settings: uniserde.JsonDoc = {}) -> Self:
        """
        Convenience method for creating default settings when they don't really
        matter: unit tests, crawlers, etc.
        """
        return cls(
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
            window_width=1920,
            window_height=1080,
        )
