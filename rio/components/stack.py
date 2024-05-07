from __future__ import annotations

from typing import Literal, final

from typing_extensions import Self

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["Stack"]


@final
class Stack(FundamentalComponent):
    """
    A container that stacks its children in the Z direction.

    `Stacks` are similar to rows and columns, but they stack their children in
    the Z direction instead of the X or Y direction. In other words, the stack's
    children overlap each other, with the first one at the bottom, the second
    one above that, and so on.


    ## Attributes

    `children`: The components to place in this `Stack`.


    ## Examples

    A minimal example of `Stack` will be shown. This example will create a stack
    of three icons, each with a different size and color. The first icon will be
    at the bottom, the second one above that, and the third one at the top:

    ```python
    rio.Stack(
        # bottom
        rio.Icon(
            "material/castle",
            width=50,
            height=50,
            fill=rio.Color.from_hex("00ff00"),
        ),
        # middle
        rio.Icon(
            "material/castle",
            width=30,
            height=30,
            fill=rio.Color.from_hex("ff0000"),
        ),
        # top
        rio.Icon(
            "material/castle",
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

    def add(self, child: rio.Component) -> Self:
        """
        Appends a child component.

        Appends a child component to the end and then returns the `Stack`, which
        makes method chaining possible:

        ```python
        rio.Stack().add(child1).add(child2)
        ```

        ## Parameters

        `child`: The child component to append.
        """
        self.children.append(child)
        return self


Stack._unique_id = "Stack-builtin"
