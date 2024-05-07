from __future__ import annotations

from dataclasses import KW_ONLY
from typing import Literal, final

from typing_extensions import Self

import rio

from .fundamental_component import FundamentalComponent

__all__ = ["FlowContainer"]


@final
class FlowContainer(FundamentalComponent):
    """
    A container that lays out its children in a horizontal or vertical flow.

    `FlowContainer` is a container that lays out its children in a horizontal or
    vertical flow. It is similar to `Container`, but allows you to specify
    spacing between the children.


    ## Attributes

    `children`: The components to place inside the container.

    `row_spacing`: The vertical spacing between the children.

    `column_spacing`: The horizontal spacing between the children.

    `justify`: The horizontal alignment of the children. Possible values are:
        `left`, `center`, `right`, `justified` and `grow`.


    ## Examples

    This minimal example will show a container with a horizontal flow:

    ```python
    rio.FlowContainer(
        rio.Text("Hello"),
        rio.Text("World!"),
        column_spacing=1,
    )
    ```
    """

    children: list[rio.Component]
    _: KW_ONLY
    column_spacing: float
    row_spacing: float
    justify: Literal["left", "center", "right", "justified", "grow"]

    def __init__(
        self,
        *children: rio.Component,
        row_spacing: float = 0.0,
        column_spacing: float = 0.0,
        justify: Literal[
            "left", "center", "right", "justified", "grow"
        ] = "center",
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
        assert isinstance(children, tuple), children

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
        self.column_spacing = column_spacing
        self.row_spacing = row_spacing
        self.justify = justify

    def add(self, child: rio.Component) -> Self:
        """
        Appends a child component.

        Appends a child component to the end and then returns the
        `FlowContainer`, which makes method chaining possible:

        ```python
        rio.FlowContainer().add(child1).add(child2)
        ```


        ## Parameters

        `child`: The child component to append.
        """
        self.children.append(child)
        return self


FlowContainer._unique_id = "FlowContainer-builtin"
