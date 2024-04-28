from __future__ import annotations

from dataclasses import KW_ONLY
from datetime import timedelta
from typing import Literal, final

from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Slideshow",
]


@final
class Slideshow(FundamentalComponent):
    """
    Prominently switches between multiple components based on a timer.

    The `Slideshow` component is a container that can hold multiple components,
    and will display them one after the other, with smooth transitions in
    between. These are very useful for displaying a series of demos or news to
    visitors.


    ## Attributes

    `children`: The components to transition between.

    `linger_time`: The time in seconds to display each component before
        switching to the next one.

    `corner_radius`: How rounded the slideshow's corners should be. If set to
        `None`, the slideshow will use a default corner radius from the current
        theme.


    ## Examples

    A minimal example of `Slideshow` displaying two images will be shown:

    ```python
    from pathlib import Path

    rio.Slideshow(
        rio.Image(Path("first.jpg")),
        rio.Image(Path("second.jpg")),
        linger_time=5,
    )
    ```
    """

    children: list[rio.Component]
    _: KW_ONLY
    linger_time: float
    corner_radius: None | float | tuple[float, float, float, float]

    def __init__(
        self,
        *children: rio.Component,
        linger_time: float | timedelta = timedelta(seconds=10),
        corner_radius: None | float | tuple[float, float, float, float] = None,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        if isinstance(linger_time, timedelta):
            linger_time = linger_time.total_seconds()

        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        self.children = list(children)
        self.linger_time = linger_time
        self.corner_radius = corner_radius

    def _custom_serialize(self) -> JsonDoc:
        # Serialize the corner radius
        if self.corner_radius is None:
            thm = self.session.theme

            corner_radius = (
                thm.corner_radius_medium,
                thm.corner_radius_medium,
                thm.corner_radius_medium,
                thm.corner_radius_medium,
            )

        elif isinstance(self.corner_radius, (int, float)):
            corner_radius = (
                self.corner_radius,
                self.corner_radius,
                self.corner_radius,
                self.corner_radius,
            )

        else:
            corner_radius = self.corner_radius

        return {
            "corner_radius": corner_radius,
        }


Slideshow._unique_id = "Slideshow-builtin"
