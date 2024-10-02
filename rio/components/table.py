from __future__ import annotations

import typing as t
from dataclasses import dataclass

from uniserde import JsonDoc

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
    _left: int
    _top: int | t.Literal["header"]
    _width: int
    _height: int

    _font_weight: t.Literal["normal", "bold"] | None = None

    def style(
        self,
        *,
        font_weight: t.Literal["normal", "bold"] | None = None,
    ) -> None:
        if font_weight is not None:
            self._font_weight = font_weight

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


# TODO: add more content to docstring
@t.final
class Table(FundamentalComponent):
    """
    Display & input for tabular data.

    Tables are a way to display data in a grid, with rows and columns. They are
    very useful for displaying data that is naturally tabular, such as
    spreadsheets, databases, or CSV files. Tables can be sorted by clicking on
    the column headers.


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
    show_row_numbers: bool = True

    # All headers, if present
    _headers: list[str] | None = None

    # The data, as a list of rows ("row-major"). This is initialized in
    # `__post_init__`.
    _data: list[list[TableValue]] = []

    # All styles applied to the table, in the order they were added.
    _styling: list[TableSelection] = []

    def __post_init__(self) -> None:
        # Bring the data into a standardized format: Either a dataframe (pandas
        # or polars) or a numpy array.
        #
        # Pandas
        if isinstance(self.data, maybes.PANDAS_DATAFRAME_TYPES):
            self._headers = list(self.data.columns)
            self._data = self.data.values.tolist()  # type: ignore

        # Polars
        elif isinstance(self.data, maybes.POLARS_DATAFRAME_TYPES):
            self._headers = list(self.data.columns)
            self._data = self.data.to_numpy().tolist()  # type: ignore

        # Numpy
        elif isinstance(self.data, maybes.NUMPY_ARRAY_TYPES):
            self._headers = None
            self._data = self.data.tolist()

        # Mapping
        elif isinstance(self.data, t.Mapping):
            data = t.cast(t.Mapping[str, t.Iterable[TableValue]], self.data)
            self._headers = list(data.keys())

            # Verify all columns have the same length
            columns: list[list[TableValue]] = []
            column_lengths = set()

            for column in data.values():
                column = list(column)
                column_lengths.add(len(column))
                columns.append(column)

            if len(column_lengths) > 1:
                raise ValueError("All table columns must have the same length")

            # Black magic to transpose the data
            self._data = list(map(list, zip(*self.data.values())))

        # Iterable of iterables
        else:
            data = t.cast(t.Iterable[t.Iterable[TableValue]], self.data)
            self._headers = None
            self._data = []
            row_lengths = set()

            for row in data:
                row = list(row)
                row_lengths.add(len(row))
                self._data.append(row)

            if len(row_lengths) > 1:
                raise ValueError("All table rows must have the same length")

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "headers": self._headers,
            "data": self._data,
            "styling": [style._as_json() for style in self._styling],
        }  # type: ignore

    def _shape(self) -> tuple[int, int]:
        """
        Returns the (height, width) of the table data. This does not include
        headers! This is like numpy's shape but takes into account the many
        different types of data that can be passed to the data attribute.
        """
        try:
            return (len(self._data), len(self._data[0]))
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
