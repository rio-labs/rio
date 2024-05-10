from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import *  # type: ignore

from uniserde import JsonDoc

from .. import maybes
from .fundamental_component import FundamentalComponent

if TYPE_CHECKING:
    import numpy  # type: ignore
    import pandas  # type: ignore
    import polars  # type: ignore


__all__ = ["Table"]


TableValue = int | float | str


@final
class Table(FundamentalComponent):
    """
    A table of data.

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
    """

    data: (
        pandas.DataFrame
        | polars.DataFrame
        | Mapping[str, Iterable[TableValue]]
        | Iterable[Iterable[TableValue]]
        | numpy.ndarray
    )
    show_row_numbers: bool = True

    def _custom_serialize(self) -> JsonDoc:
        return {
            "data": self._data_to_json(),  # type: ignore (variance)
        }

    def _data_to_json(
        self,
    ) -> dict[str, list[TableValue]] | list[list[TableValue]]:
        data = self.data

        if isinstance(data, maybes.PANDAS_DATAFRAME_TYPES):
            return data.to_dict(orient="list")  # type: ignore

        if isinstance(data, maybes.POLARS_DATAFRAME_TYPES):
            return data.to_dict(as_series=False)  # type: ignore

        if isinstance(data, Mapping):
            return dict(data)  # type: ignore (wtf?)

        if isinstance(data, maybes.NUMPY_ARRAY_TYPES):
            return data.tolist()  # type: ignore

        data = cast(Iterable[Iterable[TableValue]], data)
        return [row if isinstance(row, list) else list(row) for row in data]


Table._unique_id = "Table-builtin"
