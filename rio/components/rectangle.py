from __future__ import annotations

import dataclasses
import typing as t

from introspection import convert_case
from uniserde import JsonDoc

import rio

from .. import cursor_style, deprecations, fills
from ..color import Color
from .fundamental_component import FundamentalComponent

__all__ = [
    "Rectangle",
]


CursorStyle = t.Literal[
    "default",
    "none",
    "help",
    "pointer",
    "loading",  # "wait" in CSS
    "background-loading",  # "progress" in CSS
    "crosshair",
    "text",
    "move",
    "not-allowed",
    "can-grab",  # "grab" in CSS
    "grabbed",  # "grabbing" in CSS
    "zoom-in",
    "zoom-out",
]


@t.final
class Rectangle(FundamentalComponent):
    """
    A customizable rectangle shape.

    Rectangles are versatile components that can be used as building blocks to
    create more complex elements. While not particularly interesting on their
    own, combining a rectangle with other components allows you to quickly
    create custom buttons, cards, or anything else you may need in your app.

    Despite the name, rectangles can be used to create a variety of shapes. By
    setting the `corner_radius` appropriately, you can get anything from
    straight rectangles, rounded rectangles, to pills & circles.

    Rectangles also act as a simple source of animations. They have two styles:
    A default style for when the user isn't interacting with them, and a hover
    style for when the mouse hovers above them. This, along with their
    `transition_time` attribute allows you to make your app feel dynamic and
    alive.

    Because rectangles are meant as low-level building blocks, rather than full
    fledged components, they don't automatically switch the theme context for
    you. It's generally recommended to use `rio.Card` instead of `rio.Rectangle`
    unless you need the extra control that `rio.Rectangle` provides. You can
    find more details about theme contexts in the [Theming Quickstart
    Guide](https://rio.dev/docs/howto/theming-guide).


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

    Here's a minimal example of a rectangle with a text and green background:

    ```python
    rio.Rectangle(
        content=rio.Text("Hello World!", justify="center"),
        fill=rio.Color.GREEN,
    )
    ```

    You can also fill your `Rectangle` with an image instead of a color:

    ```python
    from pathlib import Path

    PATH = Path(__file__).parent

    rio.Rectangle(
        fill=rio.ImageFill(
            PATH / "example_image.jpg",
            fill_mode="zoom",
        ),
    )
    ```

    To make a circle, ensure your rectangle is square and add a large corner
    radius:

    ```python
    rio.Rectangle(
        # Any number larger than the rectangle's width/height will work
        corner_radius=999999,
        # Since there is no content this will control the size of the rectangle
        min_width=10,
        min_height=10,
        # Alignment ensures the rectangle won't be stretched by its parent
        align_x=0.5,
        align_y=0.5,
    )
    ```

    Also, note that the content is optional. You don't have to add anything if
    you just want a simple rectangle.
    """

    _: dataclasses.KW_ONLY
    content: rio.Component | None = None
    transition_time: float = 1.0
    cursor: CursorStyle | cursor_style.CursorStyle = "default"
    ripple: bool = False

    fill: fills._FillLike = Color.TRANSPARENT
    stroke_width: float = 0.0
    stroke_color: rio.Color = Color.BLACK
    corner_radius: float | tuple[float, float, float, float] = 0.0
    shadow_radius: float = 0.0
    shadow_offset_x: float = 0.0
    shadow_offset_y: float = 0.0
    shadow_color: rio.Color | None = None

    hover_fill: fills._FillLike | None = None
    hover_stroke_width: float | None = None
    hover_stroke_color: rio.Color | None = None
    hover_corner_radius: float | tuple[float, float, float, float] | None = None
    hover_shadow_radius: float | None = None
    hover_shadow_offset_x: float | None = None
    hover_shadow_offset_y: float | None = None
    hover_shadow_color: rio.Color | None = None

    def __post_init__(self):
        if isinstance(self.cursor, cursor_style.CursorStyle):
            deprecations.warn(
                "`rio.CursorStyle` is deprecated in favor of string literals"
            )

    def _custom_serialize_(self) -> JsonDoc:
        # Impute default values
        shadow_color = (
            self.session.theme.shadow_color
            if self.shadow_color is None
            else self.shadow_color
        )

        # Serialize
        return {
            # Regular
            "fill": self._session_._serialize_fill(self.fill),
            "corner_radius": (
                self.corner_radius
                if self.corner_radius is None
                or isinstance(self.corner_radius, tuple)
                else (self.corner_radius,) * 4
            ),
            "shadow_color": shadow_color._serialize(self._session_),
            # Hover
            "hover_fill": self._session_._serialize_fill(self.hover_fill),
            "hover_corner_radius": (
                self.hover_corner_radius
                if self.hover_corner_radius is None
                or isinstance(self.hover_corner_radius, tuple)
                else (self.hover_corner_radius,) * 4
            ),
            # We have to serialize the cursor manually because it's a union due
            # to the deprecation of CursorStyle
            "cursor": self.cursor
            if isinstance(self.cursor, str)
            else convert_case(self.cursor.name, "camel"),
        }


Rectangle._unique_id_ = "Rectangle-builtin"
