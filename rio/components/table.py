from __future__ import annotations

import typing as t
from dataclasses import KW_ONLY, dataclass, field

import narwhals as nw
import typing_extensions as te
from uniserde import JsonDoc

import rio

from .. import maybes
from .fundamental_component import FundamentalComponent

if t.TYPE_CHECKING:
    import numpy  # type: ignore
    import pandas  # type: ignore
    import polars  # type: ignore


__all__ = ["Table"]


TableValue = int | float | str


@t.final
@dataclass
class TableSelection:
    _table: Table

    _left: int
    _top: int | t.Literal["header"]
    _width: int
    _height: int

    _font_weight: t.Literal["normal", "bold"] | None = None

    def style(
        self,
        *,
        font_weight: t.Literal["normal", "bold"] | None = None,
    ) -> Table:
        # Store the passed in values
        if font_weight is not None:
            self._font_weight = font_weight

        # Return the table to allow chaining
        return self._table

    def _as_json(self) -> JsonDoc:
        # Some values are always present
        result: JsonDoc = {
            "left": self._left,
            "top": self._top,
            "width": self._width,
            "height": self._height,
        }

        # Styling only if set
        if self._font_weight is not None:
            result["fontWeight"] = self._font_weight

        # Done
        return result


def _index_to_start_and_extent(
    index: int | slice | str,
    size_in_axis: int,
    axis: t.Literal["x", "y"],
) -> tuple[
    int | t.Literal["header"],
    int,
]:
    """
    Given a one-axis `__getitem__` index, returns the start and extent of
    the slice as non-negative integers.

    This function is intentionally a separate function instead of a method
    to allow for easy unit-testing.
    """
    # Python considers booleans to be integers. Guard against them being used as
    # numbers here
    if isinstance(index, bool):
        raise ValueError(
            f"Table indices should be integers or slices, not {index!r}"
        )

    # Integers are easy
    if isinstance(index, int):
        start = index
        stop = index + 1

    # Slices need more work
    elif isinstance(index, slice):
        if index.start is None:
            start = 0
        elif isinstance(index.start, int) and not isinstance(index.start, bool):
            start = index.start
        else:
            raise ValueError(
                f"Table indices should be integers or slices, not {index!r}"
            )

        if index.stop is None:
            stop = size_in_axis
        elif isinstance(index.stop, int) and not isinstance(index.stop, bool):
            stop = index.stop
        else:
            raise ValueError(
                f"Table indices should be integers or slices, not {index!r}"
            )

    # In the y-axis, "header" is a valid index
    elif axis == "y" and index == "header":
        return "header", 1

    # Anything else is invalid
    else:
        raise ValueError(
            f"Table indices should be integers or slices, not {index!r}"
        )

    # Negative numbers count backwards from the end
    if start < 0:
        if start + size_in_axis < 0:
            raise IndexError(
                f"Negative index {start} out of bounds for axis of size {size_in_axis}"
            )

        start = size_in_axis + start

    if stop < 0:
        if stop + size_in_axis < 0:
            raise IndexError(
                f"Negative index {stop} out of bounds for axis of size {size_in_axis}"
            )

        stop = size_in_axis + stop

    # Done
    return start, stop - start


def _string_index_to_start_and_extent(
    index: str | int | slice,
    column_names: list[str] | None,
    size_in_axis: int,
    axis: t.Literal["x", "y"],
) -> tuple[
    int | t.Literal["header"],
    int,
]:
    """
    Same as `_index_to_start_and_extent`, but with support for string indices.
    """
    # If passed a string, select the entire column
    if isinstance(index, str):
        if column_names is None:
            raise ValueError(
                "Cannot index into this table using a column name, since it doesn't have any headers"
            )

        try:
            left = column_names.index(index)
        except ValueError:
            raise KeyError(f"This table doesn't have a column named {index!r}")

        return left, 1

    # Otherwise delegate to the other function
    return _index_to_start_and_extent(
        index,
        size_in_axis,
        axis,
    )


def _indices_to_rectangle(
    index: str | tuple[int | slice | str, str | int | slice],
    column_names: list[str] | None,
    data_width: int,
    data_height: int,
) -> tuple[
    int,
    int | t.Literal["header"],
    int,
    int,
]:
    # Get the raw x & y indices
    if isinstance(index, str):
        index_y = slice(None)
        index_x = index
    else:
        if not isinstance(index, tuple):
            raise ValueError(
                f"Table indices should be a tuple of two elements, not {index!r}"
            )
        elif len(index) != 2:
            raise ValueError(
                f"Table indices should have exactly two elements, not {len(index)}"
            )

        index_y, index_x = index

    # Get the index as a tuple (top, left, height, width)
    top, height = _index_to_start_and_extent(
        index_y,
        data_height,
        axis="y",
    )

    left, width = _string_index_to_start_and_extent(
        index_x,
        column_names,
        data_width,
        axis="x",
    )

    assert isinstance(left, int), left  # Left can't be "header"

    return left, top, width, height


def _data_to_columnar(
    data: pandas.DataFrame
    | polars.DataFrame
    | numpy.ndarray
    | t.Mapping[str, t.Iterable[TableValue]]
    | t.Iterable[t.Iterable[TableValue]],
) -> tuple[
    list[str] | None,
    list[list[TableValue]],
]:
    """
    Converts a table in any of the supported data formats into a standardized
    one. The result is a tuple of headers and table columns.
    """

    # TODO: Should this ensure that the outputs are valid JSONables?

    headers: list[str] | None = None
    columns: list[list[TableValue]] = []

    # DataFrame
    #
    # Use narwhals to abstract away the dataframe provider
    if isinstance(data, maybes.DATAFRAME_TYPES):
        nw_data = nw.from_native(data)
        headers = nw_data.columns

        for column_name in headers:
            columns.append(nw_data[column_name].to_list())

    # NumPy array
    #
    # These are neatly orgnanized, just need to get the contents as columns
    elif isinstance(data, maybes.NUMPY_ARRAY_TYPES):
        if data.ndim != 2:
            raise ValueError("Table data must be two-dimensional")

        for ii in range(data.shape[1]):
            columns.append(data[:, ii].tolist())

    # Mapping
    #
    # The headers are trivially available. The columns can also be used as-is,
    # but care must be taken to make sure they are all the same length.
    elif isinstance(data, t.Mapping):
        headers = list(data.keys())
        column_lengths = set()

        for column in data.values():
            column = list(column)
            column_lengths.add(len(column))
            columns.append(column)

        if len(column_lengths) > 1:
            raise ValueError("All table columns must have the same length")

    # Iterable of iterables
    #
    # There are no headers. The rows need to be transposed and must all be of
    # equal length.
    else:
        data = t.cast(t.Iterable[t.Iterable[TableValue]], data)

        row_lengths = set()

        for row in data:
            row = list(row)
            row_lengths.add(len(row))
            columns.append(row)

        if len(row_lengths) > 1:
            raise ValueError("All table rows must have the same length")

        # Black magic to transpose the data
        columns = list(map(list, zip(*columns)))

    # Done
    return headers, columns


# TODO: add more content to docstring
@t.final
class Table(FundamentalComponent):  #
    """
    Display for tabular data.

    Tables are a way to display data in a grid, with rows and columns. They are
    well suited for displaying data that is naturally tabular, such as
    spreadsheets, databases, or CSV files.

    You can provide the data to tables in a variety of formats: `pandas`
    DataFrames, `polars` DataFrames, NumPy arrays, dictionaries, or lists of
    lists.

    If the data format provides header names (like DataFrames), they will be
    displayed at the top of the table.


    ## Attributes

    `data`: The data to display.

    `show_row_numbers`: Whether to show row numbers on the left side of the table.


    ## Examples

    A simple table with some data:

    ```python
    rio.Table(
        data={
            "Name": ["Alice", "Bob", "Charlie"],
            "Age": [25, 30, 35],
            "City": ["New York", "San Francisco", "Los Angeles"],
        }
    )
    ```

    Indexing into a table to apply styling works similar as numpy arrays.
    The following example makes the second and third row, and the second
    and third column bold:

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            table = rio.Table(
                data={
                    "Name": ["Alice", "Bob", "Charlie"],
                    "Age": [25, 30, 35],
                    "City": ["New York", "San Francisco", "Los Angeles"],
                }
            )

            # apply some styling to the table, indexing rows and columns
            # works similar as numpy arrays.
            # second and third row, second and third column are bold
            table[1:3, 1:3].style(font_weight="bold")

            return table
    ```


    ## Metadata

    `experimental`: True
    """

    data: (
        pandas.DataFrame
        | polars.DataFrame
        | t.Mapping[str, t.Iterable[TableValue]]
        | t.Iterable[t.Iterable[TableValue]]
        | numpy.ndarray
    )

    _: KW_ONLY

    show_row_numbers: bool = True

    # All headers, if present
    _headers: list[str] | None = field(default=None, init=False)

    # The data, as a list of columns ("column major"). This is set in
    # `__post_init__`.
    _columns: list[list[TableValue]] = field(default_factory=list, init=False)

    # All styles applied to the table, in the same order they were added
    _styling: list[TableSelection] = field(default_factory=list, init=False)

    # These must be annotated, otherwise rio won't understand that tables have
    # child components and won't copy over the new values when two Tables are
    # reconciled.
    _children: list[rio.Component] = field(default_factory=list, init=False)

    _child_positions: list[tuple[int, int]] = field(
        default_factory=list, init=False
    )

    def __post_init__(self) -> None:
        # Bring the data into a standardized format
        self._headers, self._columns = _data_to_columnar(self.data)

        # Help out the reconciler. This is needed to make sure new values aren't
        # silently dropped
        self._properties_set_by_creator_.update(
            [
                "_headers",
                "_columns",
                "_styling",
                "_children",
                "_child_positions",
            ]
        )

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "headers": self._headers,
            "columns": self._columns,
            "styling": [style._as_json() for style in self._styling],
            "children": [child._id for child in self._children],
            "childPositions": self._child_positions,
        }  # type: ignore

    def add(
        self,
        child: rio.Component,
        row: int,
        column: int | str,
    ) -> te.Self:
        """
        Add a child component to the table

        Adds a child to the table at the specified location. Note that unlike
        with grids, children in tables always take up exactly one cell. This is
        necessary to allow for sorting & filtering of tables (a planned
        feature).

        Note that this method returns the `Table` instance afterwards, allowing
        you to chain multiple `add` calls together for concise code.


        ## Parameters

        `child`: The child component to add to the table.

        `row`: The row in which to place the child.

        `column`: The column in which to place the child.


        ## Raises

        `ValueError`: If the column index is a string and the table doesn't have
            any headers.

        `KeyError`: If the column index is a string and the table doesn't have a
            column with that name.


        ## Metadata

        `public`: False
        """
        assert isinstance(child, rio.Component), child

        # Make sure the column is an integer, propagating any exceptions
        if isinstance(column, str):
            column = self._column_name_to_int(column)

        # Add the child
        self._children.append(child)
        self._child_positions.append(
            (row, column),
        )

        # Return self for chaining
        return self

    def _shape(self) -> tuple[int, int]:
        """
        Returns the (height, width) of the table data. This does not include
        headers! This is like numpy's shape but takes into account the many
        different types of data that can be passed to the data attribute.
        """
        try:
            return (len(self._columns[0]), len(self._columns))
        except IndexError:
            return (0, 0)

    def _column_name_to_int(self, column_name: str) -> int:
        if self._headers is None:
            raise ValueError(
                "Cannot index into this table using a column name, since it doesn't have any headers"
            )

        try:
            return self._headers.index(column_name)
        except ValueError:
            raise KeyError(
                f"This table doesn't have a column named {column_name!r}"
            )

    def __getitem__(
        self,
        index: (
            str
            | tuple[
                int | slice | str,
                int | slice | str,
            ]
        ),
    ) -> TableSelection:
        # Get the index as a tuple (top, left, height, width)
        data_height, data_width = self._shape()

        left, top, width, height = _indices_to_rectangle(
            index,
            self._headers,
            data_width,
            data_height,
        )

        # Verify the indices are within bounds
        right = left + width
        out_of_bounds = (left < 0 or left >= data_width) or (
            right < 0 or right > data_width
        )

        if top == "header":
            assert height == 1, height
        else:
            bottom = top + height
            out_of_bounds = (
                out_of_bounds
                or (top < 0 or top >= data_height)
                or (bottom < 0 or bottom > data_height)
            )

        if out_of_bounds:
            raise IndexError(
                f"The table index {index!r} is out of bounds for a table of size {data_height}x{data_width}"
            )

        # Construct the result
        result = TableSelection(
            _table=self,
            _left=left,
            _top=top,
            _width=width,
            _height=height,
            _font_weight=None,
        )

        # Keep track of it
        self._styling.append(result)

        # Done!
        return result


Table._unique_id_ = "Table-builtin"
