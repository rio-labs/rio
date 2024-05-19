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
        self.children.append(child)
        return self

    def _custom_serialize(self) -> JsonDoc:
        return {"proportions": self.proportions}  # type: ignore (variance)


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

    ## Allocation of extra space

    When a `Row` has more horizontal space available than it needs, it will
    evenly distribute the extra space among all child components whose `width`
    is set to `"grow"`.

    If no child is set to `"grow"`, the extra space is evenly distributed among
    all children. This is why components in a `Row` can sometimes become
    unexpectedly large. If you don't want that to happen, you can either tell
    rio which children should receive the extra space by setting their `width`
    to `"grow"`, or you can set the `Row`s `align_x` to something other than
    `None`, which will cause the `Row` to only take up as much space as
    necessary and position itself in the available space.

    For more details, see the [layouting
    quickstart](https://rio.dev/docs/howto/layout-guide).

    ## Proportions

    Sometimes you want the widths of the children to be in some sort of
    relation. For example, you may want two children to have the same width. This
    can be achieved with the `proportions` parameter. Passing `proportions=[1,
    1]` will make both children have the same width, `proportions=[1, 2]` would
    make the 2nd child twice the width of the 1st child, and so on.

    As a shortcut, you can also pass `proportions="homogeneous"` to make all
    children the same width.


    ## Attributes

    `children`: The components to place in this `Row`.

    `spacing`: How much empty space to leave between two adjacent children. No
            spacing is added before the first child or after the last child.

    `proportions`: If set, the children will grow according to these
        proportions.

        - `homogeneous`: All children will grow equally.
        - A list of floats: Each child will grow according to its proportion.
        - `None`: Extra space will be evenly distributed among children with
            `width='grow'`.


    ## Examples

    This minimal example will display a `Row` with two text components:

    ```python
    rio.Row(rio.Text("Hello"), rio.Text("World!"))
    ```

    `Row`s are commonly used to line up multiple components horizontally. In
    this example, we're using an Icon and two Text components in a Row and wrap
    them in a Card.

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Card(
                content=rio.Row(
                    rio.Icon(icon="material/castle"),
                    rio.Text("Hello"),
                    rio.Text("World!"),
                    spacing=1,
                    # Align card content in the center
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

    def add(self, child: rio.Component) -> Self:
        """
        Appends a child component.

        Appends a child component to the end and then returns the `Row`, which
        makes method chaining possible:

        ```python
        rio.Row().add(child1).add(child2)
        ```

        ## Parameters

        `child`: The child component to append.
        """
        return super().add(child)


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

    ## Allocation of extra space

    When a `Column` has more vertical space available than it needs, it will
    evenly distribute the extra space among all child components whose `height`
    is set to `"grow"`.

    If no child is set to `"grow"`, the extra space is evenly distributed among
    all children. This is why components in a `Column` can sometimes become
    unexpectedly large. If you don't want that to happen, you can either tell
    rio which children should receive the extra space by setting their `height`
    to `"grow"`, or you can set the `Column`s `align_y` to something other than
    `None`, which will cause the `Column` to only take up as much space as
    necessary and position itself in the available space.

    For more details, see the [layouting
    quickstart](https://rio.dev/docs/howto/layout-guide).

    ## Proportions

    Sometimes you want the heights of the children to be in some sort of
    relation. For example, you may want two children to have the same height.
    This can be achieved with the `proportions` parameter. Passing
    `proportions=[1, 1]` will make both children have the same height,
    `proportions=[1, 2]` would make the 2nd child twice the height of the 1st
    child, and so on.

    As a shortcut, you can also pass `proportions="homogeneous"` to make all
    children the same height.


    ## Attributes

    `children`: The components to place in this `Column`.

    `spacing`: How much empty space to leave between two adjacent children. No
        spacing is added before the first child or after the last child.

    `proportions`: If set, the children will grow according to these proportions.
        - `homogeneous`: All children will grow equally.
        - A list of floats: Each child will grow according to its proportion.
        - `None`: Extra space will be evenly distributed among children with
            `height='grow'`.


    ## Examples

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

    def add(self, child: rio.Component) -> Self:
        """
        Appends a child component.

        Appends a child component to the end and then returns the `Column`,
        which makes method chaining possible:

        ```python
        rio.Column().add(child1).add(child2)
        ```

        ## Parameters

        `child`: The child component to append.
        """
        return super().add(child)


Column._unique_id = "Column-builtin"
