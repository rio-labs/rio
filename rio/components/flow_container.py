from __future__ import annotations

from dataclasses import KW_ONLY
from typing import Literal, final

from typing_extensions import Self
from uniserde import JsonDoc

import rio

from .. import utils
from .fundamental_component import FundamentalComponent

__all__ = ["FlowContainer"]


@final
class FlowContainer(FundamentalComponent):
    """
    A container whose children will be rearranged to fill the available space

    `FlowContainer` is similar to `rio.Row` and `rio.Column`, except it
    automatically reflows its children if not enough space is available, similar
    to how text reflows in a word processor.

    ## Attributes

    `children`: The components to place inside the container.

    `row_spacing`: The vertical spacing between the children.

    `column_spacing`: The horizontal spacing between the children.

    `justify`: The horizontal alignment of the children. Possible values are:
        `"left"`, `"center"`, `"right"`, `"justified"` and `"grow"`.


    ## Examples

    This minimal example will show two children horizontally next to one
    another, but reflow to vertical if the window is too small:

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
    spacing: float | None
    row_spacing: float | None
    column_spacing: float | None
    justify: Literal["left", "center", "right", "justified", "grow"]

    def __init__(
        self,
        *children: rio.Component,
        spacing: float | None = None,
        row_spacing: float | None = None,
        column_spacing: float | None = None,
        justify: Literal[
            "left", "center", "right", "justified", "grow"
        ] = "left",
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
    ) -> None:
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
        self.spacing = spacing
        self.row_spacing = row_spacing
        self.column_spacing = column_spacing
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

    def _custom_serialize(self) -> JsonDoc:
        return {
            "row_spacing": utils.first_non_null(
                self.row_spacing,
                self.spacing,
                0,
            ),
            "column_spacing": utils.first_non_null(
                self.column_spacing,
                self.spacing,
                0,
            ),
        }


FlowContainer._unique_id = "FlowContainer-builtin"
