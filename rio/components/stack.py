from __future__ import annotations

from typing import Literal

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["Stack"]


class Stack(FundamentalComponent):
    """
    # Stack

    A container that stacks its children in the Z direction.

    `Stacks` are similar to rows and columns, but they stack their children in
    the Z direction instead of the X or Y direction. In other words, the stack's
    children overlap each other, with the first one at the bottom, the second
    one above that, and so on.


    ## Attributes:

    `children`: The components to place in this `Stack`.

    ## Example:

    A minimal example of `Stack` will be shown. This example will create a stack
    of three icons, each with a different size and color. The first icon will be
    at the bottom, the second one above that, and the third one at the top:

    ```python
    rio.Stack(
        # bottom
        rio.Icon(
            "castle",
            width=50,
            height=50,
            fill=rio.Color.from_hex("00ff00"),
        ),
        # middle
        rio.Icon(
            "castle",
            width=30,
            height=30,
            fill=rio.Color.from_hex("ff0000"),
        ),
        # top
        rio.Icon(
            "castle",
            width=10,
            height=10,
            fill=rio.Color.from_hex("000000"),
        ),
    )
    ```
    """

    children: list[rio.Component]

    def __init__(
        self,
        *children: rio.Component,
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


Stack._unique_id = "Stack-builtin"
