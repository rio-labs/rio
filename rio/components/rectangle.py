from __future__ import annotations

from dataclasses import KW_ONLY

import rio

from .. import cursor_style
from .fundamental_component import FundamentalComponent

__all__ = [
    "Rectangle",
]


class Rectangle(FundamentalComponent):
    """
    # Rectangle

    A customizable rectangle shape.

    Rectangles are versatile components that can be used to build up more
    complex elements. While not particularly interesting on their own, combining
    a rectangle with other components allows you to quickly create custom
    buttons, cards, or anything els you may need in your app.

    Rectangles also act as a simple source of animations. They accept two
    styles: A default style for when the user isn't interacting with them, and a
    hover style for when the mouse hovers above them. This, along with their
    `transition_time` attribute allows you to make your app feel dynamic and
    alive.


    ## Attributes:

    `content`: The component to display inside the rectangle.

    `style`: How the rectangle should appear when the user isn't interacting
        with it.

    `hover_style`: The style of the rectangle when the mouse hovers above it.
        If set to `None`, the rectangle will not change its appearance when
        hovered.

    `transition_time`: How many seconds it should take for the rectangle to
        transition between its styles.

    `cursor`: The cursor to display when the mouse hovers above the rectangle.

    `ripple`: Whether to display a Material Design ripple effect when the
        rectangle is hovered or clicked.


    ## Example:

    A minimal example of a rectangle with a text and red background will be shown:

    ```python
    rio.Rectangle(
        content=rio.Text("Hello World!"),
        style=rio.BoxStyle(fill=rio.Color.from_hex("ff0000")),
    )
    ```

    You can fill your `Rectangle` with an image instead of a color:

    ```python
    from pathlib import Path

    PATH = Path(__file__).parent

    rio.Rectangle(
        content=rio.Text("Hello World!"),
        style=rio.BoxStyle(
            fill=rio.ImageFill(
                PATH / "example_image.jpg",
                fill_mode="zoom",
            ),
        ),
    )
    ```
    """

    _: KW_ONLY
    style: rio.BoxStyle
    content: rio.Component | None = None
    hover_style: rio.BoxStyle | None = None
    transition_time: float = 1.0
    cursor: rio.CursorStyle = cursor_style.CursorStyle.DEFAULT
    ripple: bool = False


Rectangle._unique_id = "Rectangle-builtin"
