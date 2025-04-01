from __future__ import annotations

import dataclasses
import typing as t
from datetime import timedelta

from uniserde import JsonDoc

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "Slideshow",
]


@t.final
class Slideshow(FundamentalComponent):
    """
    Repeatedly switches between multiple components based on a timer.

    The `Slideshow` component is a container that can hold multiple components,
    and will display them one after the other, with smooth transitions in
    between. These are very useful for displaying a series of pictures or news
    items to visitors.


    ## Attributes

    `children`: The components to transition between.

    `linger_time`: The time in seconds to display each component before
        switching to the next one.

    `pause_on_hover`: Whether to pause the slideshow while the mouse cursor
        hovers over it.

    `corner_radius`: How rounded the slideshow's corners should be. If set to
        `None`, the slideshow will use a default corner radius from the current
        theme.


    ## Examples

    Here's a simple example that will continuously switch between two images:

    ```python
    from pathlib import Path

    rio.Slideshow(
        rio.Image(Path("first.jpg")),
        rio.Image(Path("second.jpg")),
        linger_time=5,
    )
    ```

    You can access the `App`'s assets directory using the `assets` property. This
    will return a `pathlib.Path` object pointing to the assets directory:

    ```python
    rio.Slideshow(
        rio.Image(self.session.assets / "first.jpg"),
        rio.Image(self.session.assets / "second.jpg"),
        linger_time=5,
    )
    ```
    """

    children: list[rio.Component]
    _: dataclasses.KW_ONLY
    linger_time: float
    pause_on_hover: bool
    corner_radius: None | float | tuple[float, float, float, float]

    def __init__(
        self,
        *children: rio.Component,
        linger_time: float | timedelta = timedelta(seconds=10),
        pause_on_hover: bool = True,
        corner_radius: None | float | tuple[float, float, float, float] = None,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
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
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.children = list(children)
        self.linger_time = linger_time
        self.pause_on_hover = pause_on_hover
        self.corner_radius = corner_radius

    def _custom_serialize_(self) -> JsonDoc:
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


Slideshow._unique_id_ = "Slideshow-builtin"
