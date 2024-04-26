from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, final

from typing_extensions import Self
from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Row",
    "Column",
]


class _LinearContainer(FundamentalComponent):
    children: list[rio.Component]
    spacing: float = 0.0
    proportions: Literal["homogeneous"] | Sequence[float] | None = None

    # Don't let @dataclass generate a constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add(self, child: rio.Component) -> Self:
        """
        Appends a child component.
        """
        self.children.append(child)
        return self

    def _custom_serialize(self) -> JsonDoc:
        return {"proportions": self.proportions}  # type: ignore[variance]


@final
class Row(_LinearContainer):
    """
    A container that lays out its children horizontally.

    `Row`s are one of the most common components in Rio. They take any number of
    children and lay them out horizontally, with the first one on the left, the
    second one to its right, and so on. All components in `Row`s occupy the full
    height of their parent.

    The `Row`'s horizontal counterpart is the `Column`. A similar component, but
    stacking its children in the Z direction, is the `Stack`.

    ## Undefined Space

    Like most containers in `rio`, `Row`s always attempt to allocate all
    available space to their children. In the context of a `Row` though, this
    could easily lead to unexpected results. If more space is available than
    needed, should all children grow? Only the first? Should they grow by equal
    amounts, or proportionally?

    To avoid this ambiguity, `Row`s have a concept of *undefined space*. Simply
    put, **not using all available space is considered an error and should be
    avoided.** `Row`s indicate this by highlighting the extra space with
    unmistakable animated sprites.

    Getting rid of undefined space is easy: Depending on what look you're going
    for, either add a `Spacer` somewhere into your `Row`, assign one of the
    components a `"grow"` value as its height, or set the `Row`'s vertical
    alignment.

    ## Attributes

    `children`: The components to place in this `Row`.

    `spacing`: How much empty space to leave between two adjacent children. No
            spacing is added before the first child or after the last child.

    `proportions`: If set, the children will grow according to these proportions.
        - `homogeneous`: All children will grow equally.
        - A list of floats: Each child will grow according to its proportion.
        - `None`: Allows all child components to expand as much as they need.

    ## Example

    This minimal example will display a `Row` with two text components:

    ```python
    rio.Row(rio.Text("Hello"), rio.Text("World!"))
    ```

    `Row`s are commonly used to line up multiple components horizontally. In this example, we're
    using an Icon and two Text components in a Row and wrap them in a Card.

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Card(
                content=rio.Row(
                    rio.Icon(icon="material/castle"),
                    rio.Text("Hello"),
                    rio.Text("World!"),
                    spacing=1,
                    # align card content in the center
                    # to avoid undefined space
                    align_x=0.5,
                ),
            )
    ```
    """

    def __init__(
        self,
        *children: rio.Component,
        spacing: float = 0.0,
        proportions: Literal["homogeneous"] | Sequence[float] | None = None,
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
        self.spacing = spacing
        self.proportions = proportions


Row._unique_id = "Row-builtin"


@final
class Column(_LinearContainer):
    """
    A container that lays out its children vertically.

    `Column`s are one of the most common components in Rio. They take any number
    of children and lay them out vertically, with the first one at the top, the
    second one below that, and so on. All components in `Column`s occupy the
    full width of their parent.

    The `Column`'s horizontal counterpart is the `Row`. A similar component, but
    stacking its children in the Z direction, is the `Stack`.


    ## Undefined Space

    Like most containers in `rio`, `Column`s always attempt to allocate all
    available space to their children. In the context of a `Column` though, this
    could easily lead to unexpected results. If more space is available than
    needed, should all children grow? Only the first? Should they grow by equal
    amounts, or proportionally?

    To avoid this ambiguity, `Column`s have a concept of *undefined space*.
    Simply put, **not using all available space is considered an error and
    should be avoided.** `Column`s indicate this by highlighting the extra space
    with unmistakable animated sprites.

    Getting rid of undefined space is easy: Depending on what look you're going
    for, either add a `Spacer` somewhere into your `Column`, assign one of the
    components a `"grow"` value as its height, or set the `Column`'s vertical
    alignment.


    ## Attributes

    `children`: The components to place in this `Column`.

    `spacing`: How much empty space to leave between two adjacent children. No
        spacing is added before the first child or after the last child.

    `proportions`: If set, the children will grow according to these proportions.
        - `homogeneous`: All children will grow equally.
        - A list of floats: Each child will grow according to its proportion.
        - `None`: Allows all child components to expand as much as they need.


    ## Example

    This minimal example will display a `Column` with two text components:

    ```python
    rio.Column(rio.Text("Hello"), rio.Text("World!"))
    ```

    `Columns`s are commonly used to line up multiple components vertically. In
    this example, we're using an Icon and two Text components in a Column and
    wrap them in a Card.

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Card(
                content=rio.Column(
                    rio.Icon("material/castle"),
                    rio.Text("Hello"),
                    rio.Text("World!"),
                    spacing=1,
                    # Align card content in the center to avoid undefined space
                    align_y=0.5,
                ),
            )
    ```
    """

    def __init__(
        self,
        *children: rio.Component,
        spacing: float = 0.0,
        proportions: Literal["homogeneous"] | Sequence[float] | None = None,
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
        self.spacing = spacing
        self.proportions = proportions


Column._unique_id = "Column-builtin"
