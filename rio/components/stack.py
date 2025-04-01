from __future__ import annotations

import typing as t

import typing_extensions as te

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["Stack"]


@t.final
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

    This example will create a stack of three icons, each with a different size
    and color. The first icon will be at the bottom, the second one above that,
    and the third one at the top:

    ```python
    rio.Stack(
        # bottom
        rio.Icon(
            "material/castle",
            min_width=50,
            min_height=50,
            fill=rio.Color.from_hex("00ff00"),
            align_x=0.5,
            align_y=0.5,
        ),
        # middle
        rio.Icon(
            "material/castle",
            min_width=30,
            min_height=30,
            fill=rio.Color.from_hex("ff0000"),
            align_x=0.5,
            align_y=0.5,
        ),
        # top
        rio.Icon(
            "material/castle",
            min_width=10,
            min_height=10,
            fill=rio.Color.from_hex("000000"),
            align_x=0.5,
            align_y=0.5,
        ),
    )
    ```
    """

    children: list[rio.Component]

    def __init__(
        self,
        *children: rio.Component,
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

    def add(self, child: rio.Component) -> te.Self:
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


Stack._unique_id_ = "Stack-builtin"
