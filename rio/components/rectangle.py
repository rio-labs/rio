from __future__ import annotations

from dataclasses import KW_ONLY
from typing import final

from uniserde import JsonDoc

import rio

from .. import cursor_style
from ..color import Color
from .fundamental_component import FundamentalComponent

__all__ = [
    "Rectangle",
]


@final
class Rectangle(FundamentalComponent):
    """
    A customizable rectangle shape.

    Rectangles are versatile components that can be used to build up more
    complex elements. While not particularly interesting on their own, combining
    a rectangle with other components allows you to quickly create custom
    buttons, cards, or anything els you may need in your app.

    Rectangles also act as a simple source of animations. They have two styles:
    A default style for when the user isn't interacting with them, and a hover
    style for when the mouse hovers above them. This, along with their
    `transition_time` attribute allows you to make your app feel dynamic and
    alive.


    ## Attributes

    `content`: The component to display inside the rectangle.

    `fill`: The background color/image/gradient of the rectangle.

    `stroke_width`: The width of the rectangle's outline.

    `stroke_color`: The color of the rectangle's outline.

    `corner_radius`: The rectangle's corner radius. Can be a single number or a
        sequence of 4 numbers.

    `shadow_radius`: The corner radius of the rectangle's shadow.

    `shadow_offset_x`: The horizontal offset of the rectangle's shadow. A
        negative value moves the shadow to the left side of the rectangle.

    `shadow_offset_y`: The vertical offset of the rectangle's shadow. A
        negative value moves the shadow above the rectangle.

    `shadow_color`: The color of the rectangle's shadow.

    `hover_fill`: The rectangle's `fill` while the cursor is hovering over it.

    `hover_stroke_width`: The rectangle's `stroke_width` while the cursor is
        hovering over it.

    `hover_stroke_color`: The rectangle's `stroke_color` while the cursor is
        hovering over it.

    `hover_corner_radius`: The rectangle's `corner_radius` while the cursor is
        hovering over it.

    `hover_shadow_radius`: The rectangle's `shadow_radius` while the cursor is
        hovering over it.

    `hover_shadow_offset_x`: The rectangle's `shadow_offset_x` while the cursor
        is hovering over it.

    `hover_shadow_offset_y`: The rectangle's `shadow_offset_y` while the cursor
        is hovering over it.

    `hover_shadow_color`: The rectangle's `shadow_color` while the cursor is
        hovering over it.

    `transition_time`: How many seconds it should take for the rectangle to
        transition between its regular and hover styles.

    `cursor`: The cursor to display when the mouse hovers above the rectangle.

    `ripple`: Whether to display a Material Design ripple effect when the
        rectangle is hovered or clicked.


    ## Examples

    A minimal example of a rectangle with a text and red background will be
    shown:

    ```python
    rio.Rectangle(
        content=rio.Text("Hello World!"),
        fill=rio.Color.from_hex("ff0000"),
    )
    ```

    You can fill your `Rectangle` with an image instead of a color:

    ```python
    from pathlib import Path

    PATH = Path(__file__).parent

    rio.Rectangle(
        content=rio.Text("Hello World!"),
        fill=rio.ImageFill(
            PATH / "example_image.jpg",
            fill_mode="zoom",
        ),
    )
    ```
    """

    _: KW_ONLY
    content: rio.Component | None = None
    transition_time: float = 1.0
    cursor: rio.CursorStyle = cursor_style.CursorStyle.DEFAULT
    ripple: bool = False

    fill: rio.FillLike
    stroke_width: float = 0.0
    stroke_color: rio.Color = Color.BLACK
    corner_radius: float | tuple[float, float, float, float] = 0.0
    shadow_radius: float = 0.0
    shadow_offset_x: float = 0.0
    shadow_offset_y: float = 0.0
    shadow_color: rio.Color = Color.BLACK

    hover_fill: rio.FillLike | None = None
    hover_stroke_width: float | None = None
    hover_stroke_color: rio.Color | None = None
    hover_corner_radius: float | tuple[float, float, float, float] | None = None
    hover_shadow_radius: float | None = None
    hover_shadow_offset_x: float | None = None
    hover_shadow_offset_y: float | None = None
    hover_shadow_color: rio.Color | None = None

    def __post_init__(self):
        self.fill = rio.Fill._try_from(self.fill)

    def _custom_serialize(self) -> JsonDoc:
        return {
            # Regular
            "fill": rio.Fill._try_from(self.fill)._serialize(self._session_),
            "corner_radius": (
                self.corner_radius
                if self.corner_radius is None
                or isinstance(self.corner_radius, tuple)
                else (self.corner_radius,) * 4
            ),
            # Hover
            "hover_fill": (
                None
                if self.hover_fill is None
                else rio.Fill._try_from(self.hover_fill)._serialize(
                    self._session_
                )
            ),
            "hover_corner_radius": (
                self.hover_corner_radius
                if self.hover_corner_radius is None
                or isinstance(self.hover_corner_radius, tuple)
                else (self.hover_corner_radius,) * 4
            ),
        }


Rectangle._unique_id = "Rectangle-builtin"
