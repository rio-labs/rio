from __future__ import annotations

import typing as t

import typing_extensions as te
from uniserde import JsonDoc

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "Row",
    "Column",
]


class _LinearContainer(FundamentalComponent):
    children: list[rio.Component]
    spacing: float = 0.0
    proportions: t.Literal["homogeneous"] | t.Sequence[float] | None = None

    # Don't let @dataclass generate a constructor
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def add(self, child: rio.Component) -> te.Self:
        self.children.append(child)
        return self

    def _custom_serialize_(self) -> JsonDoc:
        return {"proportions": self.proportions}  # type: ignore (variance)


@t.final
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
    evenly distribute the extra space among all child components whose `grow_x`
    attribute is `True`.

    If no child is set to grow horizontally, the extra space is evenly
    distributed among all children. This is why components in a `Row` can
    sometimes become unexpectedly large. If you don't want that to happen, you
    can either tell Rio which children should receive the extra space by setting
    their `grow_x` to `True`, or you can set the `Row`s `align_x` to something
    other than `None`, which will cause the `Row` to only take up as much space
    as necessary and position itself in the available space.

    For more details, see the [layouting
    quickstart](https://rio.dev/docs/howto/layout-guide).


    ## Proportions

    Sometimes you want the widths of the children to be in some sort of
    relation. For example, you may want two children to have the same width.
    This can be achieved with the `proportions` parameter. Passing
    `proportions=[1, 1]` will make both children have the same width,
    `proportions=[1, 2]` would make the 2nd child twice the width of the 1st
    child, and so on.

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

    `Row`s are used to line up multiple components horizontally. This example
    arranges a `rio.Icon` and two `rio.Text` components in a row and neatly
    wraps them in a Card.

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Card(
                content=rio.Row(
                    rio.Text("Hello"),
                    rio.Icon(icon="material/star"),
                    rio.Text("World!"),
                    spacing=1,
                    margin=1,
                ),
            )
    ```
    """

    def __init__(
        self,
        *children: rio.Component,
        spacing: float = 0.0,
        proportions: t.Literal["homogeneous"] | t.Sequence[float] | None = None,
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
        self.proportions = proportions

    def add(self, child: rio.Component) -> te.Self:
        """
        Appends a child component.

        Appends a child component to the end of the row and returns the `Row`.
        This means you can chain multiple `add` calls:

        ```python
        rio.Row().add(child1).add(child2)
        ```

        ## Parameters

        `child`: The child component to append.
        """
        return super().add(child)


Row._unique_id_ = "Row-builtin"


@t.final
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
    evenly distribute the extra space among all child components whose `grow_y`
    attribute is `True`.

    If no child is set to grow vertically, the extra space is evenly distributed
    among all children. This is why components in a `Column` can sometimes
    become unexpectedly large. If you don't want that to happen, you can either
    tell rio which children should receive the extra space by setting their
    `grow_y` to `True`, or you can set the `Column`s `align_y` to something
    other than `None`, which will cause the `Column` to only take up as much
    space as necessary and position itself in the available space.

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

    `Columns`s are used to line up multiple components vertically. This example
    arranges a `rio.Icon` and two `rio.Text` components in a column and neatly
    wraps them in a Card.

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Card(
                content=rio.Column(
                    rio.Text("Hello"),
                    rio.Icon("material/castle"),
                    rio.Text("World!"),
                    spacing=1,
                    margin=1,
                ),
            )
    ```
    """

    def __init__(
        self,
        *children: rio.Component,
        spacing: float = 0.0,
        proportions: t.Literal["homogeneous"] | t.Sequence[float] | None = None,
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
        self.proportions = proportions

    def add(self, child: rio.Component) -> te.Self:
        """
        Appends a child component.

        Appends a child component to the end of the column and returns the
        `Column`. This means you can chain multiple `add` calls:

        ```python
        rio.Column().add(child1).add(child2)
        ```

        ## Parameters

        `child`: The child component to append.
        """
        return super().add(child)


Column._unique_id_ = "Column-builtin"
