from __future__ import annotations

import dataclasses
import typing as t

import typing_extensions as te

import rio

from .component import AccessibilityRole, Component, Key

__all__ = ["LabeledColumn"]


@t.final
class LabeledColumn(Component):
    """
    A container that lays out its children in a column, with labels for each
    child.

    `LabeledColumn` is a container that lays out its children in a column, with
    labels for each child. It is similar to `Column`, but allows you to specify
    labels for each child.


    ## Example

    This minimal example will show a container with a column layout and labels:

    ```python
    rio.LabeledColumn(
        {
            "First Name": rio.TextInput(),
            "Last Name": rio.TextInput(),
            "Age": rio.TextInput(),
        }
    )
    ```

    ## Metadata

    `public`: False
    """

    _child_list: list[Component] = dataclasses.field(init=False)

    def __init__(
        self,
        content: t.Mapping[str, rio.Component],
        *,
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

        self.content = content

    @property
    def content(self) -> t.Mapping[str, Component]:
        return self._content

    @content.setter
    def content(self, children: t.Mapping[str, Component]) -> None:
        self._content = dict(children)
        self._child_list = list(children.values())

    def add(self, label: str, child: rio.Component) -> te.Self:
        """
        Appends a child component.

        Appends a child component to the end and then returns the
        `LabeledColumn`, which makes method chaining possible.
        """
        self._content[label] = child
        self._child_list.append(child)

        return self

    def build(self) -> Component:
        rows = [
            [
                rio.Text(label, justify="right", selectable=False),
                child,
            ]
            for label, child in self.content.items()
        ]

        return rio.Grid(*rows, row_spacing=0.1, column_spacing=0.2)
