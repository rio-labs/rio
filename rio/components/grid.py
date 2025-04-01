from __future__ import annotations

import dataclasses
import math
import typing as t

import typing_extensions as te
from uniserde import JsonDoc

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["Grid"]


@t.final
@dataclasses.dataclass
class GridChildPosition:
    row: int
    column: int
    width: int = 1
    height: int = 1


@t.final
class Grid(FundamentalComponent):
    """
    A container which arranges its children in a table-like grid.

    Grids arrange their children in a table-like grid. Each child is placed in
    one or more cells of the grid. You can add children to the grid either by
    passing them into the constructor or by using the `Grid.add` method.

    To get full control over where children are placed, use `grid.add`. It
    returns the grid itself, so you can chain multiple `add` calls together for
    concise code.

    If you don't need all of that control, a convenient way of populating grids
    is by passing all children directly into the constructor. `Grid` accepts
    both individual components, as well as lists of components. Each value is
    interpreted as a single row of the grid, and the grid adjusted so that all
    rows fill the entire space evenly.


    ## Attributes

    `row_spacing`: The amount of space between rows of the grid.

    `column_spacing`: The amount of space between columns of the grid.


    ## Examples

    This code creates a grid layout with two rows and two columns, and adds
    children to the grid by passing them in as a list:

    ```python
    rio.Grid(
        [rio.Text("Hello"), rio.Text("World!")],  # 1. Row
        [rio.Text("Foo"), rio.Text("Bar")],  # 2. Row
    )
    ```

    Alternatively, you can use the `add` method to add children to the grid.
    Here's how you can do it:

    ```python
    grid = rio.Grid(row_spacing=1, column_spacing=1)
    grid.add(rio.Text("Hello"), row=0, column=0)
    grid.add(rio.Text("World!"), row=0, column=1)
    grid.add(rio.Text("Foo"), row=1, column=0)
    grid.add(rio.Text("Bar"), row=1, column=1)
    ```

    In your Component class, you can use the `add` method within the build function to
    add children to the grid. Here's how you can do it:

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            grid = rio.Grid(row_spacing=1, column_spacing=1)
            grid.add(rio.Text("Hello"), row=0, column=0)
            grid.add(rio.Text("World!"), row=0, column=1)
            grid.add(rio.Text("Foo"), row=1, column=0)
            grid.add(rio.Text("Bar"), row=1, column=1)

            return grid
    ```
    """

    _: dataclasses.KW_ONLY
    row_spacing: float
    column_spacing: float

    # Hide internal attributes from the type checker
    if not t.TYPE_CHECKING:
        # These must be annotated, otherwise rio won't understand that grids
        # have child components and won't copy over the new values when two
        # Grids are reconciled.
        _children: list[rio.Component]
        _child_positions: list[GridChildPosition]

    def __init__(
        self,
        *rows: rio.Component | t.Iterable[rio.Component],
        row_spacing: float = 0.0,
        column_spacing: float = 0.0,
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
        """
        ## Parameters

        `rows`: Components or iterable of components to be added to the Grid as
            rows.
        """
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

        self.row_spacing = row_spacing
        self.column_spacing = column_spacing

        # JS can only work with lists of Components, so we'll store the
        # components and their positions separately
        self._children, self._child_positions = self._add_initial_children(rows)

        self._properties_set_by_creator_.update(
            ["_children", "_child_positions"]
        )

    def _add_initial_children(
        self,
        children: t.Iterable[rio.Component | t.Iterable[rio.Component]],
    ) -> tuple[list[rio.Component], list[GridChildPosition]]:
        """
        Adds the children added in the constructor to the component. This is
        fairly complex and thus has its own function so not to pollute the
        constructor.
        """
        result_children: list[rio.Component] = []
        result_child_positions: list[GridChildPosition] = []

        # Pre process the rows and find the number of children in each
        rows: list[list[rio.Component]] = []
        row_widths: list[int] = []

        for row in children:
            if isinstance(row, rio.Component):
                row = [row]
            else:
                row = list(row)

                # Don't div/0 on empty rows
                if not row:
                    continue

            rows.append(row)
            row_widths.append(len(row))

        # Avoid weird math if there are no rows. This is only done now, because
        # the loop above can drop empty rows.
        if not rows:
            return result_children, result_child_positions

        # Find the target number of columns
        target_columns = math.lcm(*row_widths)
        assert target_columns > 0, (target_columns, row_widths)

        # Add the children
        for yy, row_components in enumerate(rows):
            row_width = row_widths[yy]
            multiplier = target_columns // row_width

            for xx, component in enumerate(row_components):
                result_children.append(component)
                result_child_positions.append(
                    GridChildPosition(
                        yy,
                        xx * multiplier,
                        width=multiplier,
                        height=1,
                    )
                )

        # Done
        return result_children, result_child_positions

    def add(
        self,
        child: rio.Component,
        row: int,
        column: int,
        *,
        width: int = 1,
        height: int = 1,
    ) -> te.Self:
        """
        Add a child component to the grid

        Adds a child to the grid at the specified location. Children can span
        multiple rows or columns by setting the `width` and `height` parameters.

        Note that this method returns the `Grid` instance afterwards, allowing
        you to chain multiple `add` calls together for concise code.


        ## Parameters

        `child`: The child component to add to the grid.

        `row`: The row in which to place the child.

        `column`: The column in which to place the child.

        `width`: The number of columns the child should take up.

        `height`: The number of rows the child should take up.


        ## Example

        ```python
        grid = rio.Grid(row_spacing=1, column_spacing=1)
        grid.add(rio.Text("Hello"), row=0, column=0)
        ```
        """
        assert isinstance(child, rio.Component), child

        if width <= 0:
            raise ValueError("Children have to take up at least one column")

        if height <= 0:
            raise ValueError("Children have to take up at least one row")

        self._children.append(child)
        self._child_positions.append(
            GridChildPosition(row, column, width, height)
        )

        # Return self for chaining
        return self

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "_children": [child._id_ for child in self._children],
            "_child_positions": [vars(pos) for pos in self._child_positions],
        }


Grid._unique_id_ = "Grid-builtin"
