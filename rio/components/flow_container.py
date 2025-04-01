from __future__ import annotations

import dataclasses
import typing as t

import typing_extensions as te
from uniserde import JsonDoc

import rio

from .. import deprecations, utils
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["FlowContainer"]


@t.final
class FlowContainer(FundamentalComponent):
    """
    A container whose children will be rearranged to fill the available space.

    `FlowContainer` is similar to `rio.Row` and `rio.Column`, except it
    automatically reflows its children if not enough space is available, similar
    to how text reflows in a word processor.

    ## Attributes

    `children`: The components to place inside the container.

    `row_spacing`: The vertical spacing between the children.

    `column_spacing`: The horizontal spacing between the children.

    `spacing`: Controls both the horizontal and the vertical spacing
        simultaneously.

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
    _: dataclasses.KW_ONLY
    spacing: float | None
    row_spacing: float | None
    column_spacing: float | None
    justify: t.Literal["left", "center", "right", "justify", "grow"]

    def __init__(
        self,
        *children: rio.Component,
        spacing: float | None = None,
        row_spacing: float | None = None,
        column_spacing: float | None = None,
        justify: t.Literal[
            "left", "center", "right", "justify", "grow"
        ] = "left",
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
        self.spacing = spacing
        self.row_spacing = row_spacing
        self.column_spacing = column_spacing
        self.justify = justify

    def add(self, child: rio.Component) -> te.Self:
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

    def _custom_serialize_(self) -> JsonDoc:
        result: JsonDoc = {
            "row_spacing": utils.first_non_none(
                self.row_spacing,
                self.spacing,
                0,
            ),
            "column_spacing": utils.first_non_none(
                self.column_spacing,
                self.spacing,
                0,
            ),
        }

        if self.justify == "justified":
            deprecations.warn(
                since="0.9.2",
                message=f'`justify="justified"` of `rio.FlowContainer` has been renamed. Please use `justify="justify"` instead.',
            )
            result["justify"] = "justify"

        return result


FlowContainer._unique_id_ = "FlowContainer-builtin"
