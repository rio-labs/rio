from __future__ import annotations

from collections.abc import Mapping
from dataclasses import field
from typing import Literal, final

from typing_extensions import Self

import rio

from .component import Component

__all__ = ["LabeledColumn"]


@final
class LabeledColumn(Component):
    """
    A container that lays out its children in a column, with labels for each child.

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

    public: False
    """

    _child_list: list[Component] = field(init=False)

    def __init__(
        self,
        content: Mapping[str, rio.Component],
        *,
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

        self.content = content

    @property
    def content(self) -> Mapping[str, Component]:
        return self._content

    @content.setter
    def content(self, children: Mapping[str, Component]) -> None:
        self._content = dict(children)
        self._child_list = list(children.values())

    def add(self, label: str, child: rio.Component) -> Self:
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
                rio.Text(label, justify="right"),
                child,
            ]
            for label, child in self.content.items()
        ]

        return rio.Grid(*rows, row_spacing=0.1, column_spacing=0.2)
