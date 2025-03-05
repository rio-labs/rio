"""
Tests that different types of data formats accepted by tables are correctly
turned into the internal column format.
"""

import typing as t
from datetime import datetime

import numpy as np
import pandas as pd
import polars as pl
import pytest

import rio
import rio.maybes

# Tables work with a lot of optionally supported modules. Make sure Rio is aware
# of which ones are available.
rio.maybes.initialize()


DATE_FORMAT_STRING = "%Y-%m-%d"


def gen_valid_data() -> dict[str, t.Iterable[t.Any]]:
    """
    Generates a dictionary of valid data for use in a `rio.Table`. The columns
    are intentionally of different types, some of which can only be used once.
    """

    return {
        "Text": ["A", "B", "C", "D", "E"],
        "Number List": [1, 2, 3, 4, 5],
        "Number Tuple": (1, 2, 3, 4, 5),
        "Number Generator": (i for i in range(1, 6)),
        "Date List": [
            datetime(2025, 1, 1),
            datetime(2025, 1, 2),
            datetime(2025, 1, 3),
            datetime(2025, 1, 4),
            datetime(2025, 1, 5),
        ],
        "Objects List": [
            {"foo": "bar"},
            datetime(2025, 1, 1),
            1,
            1.23,
            True,
        ],
    }


def gen_too_short_column_data() -> dict[str, t.Iterable[t.Any]]:
    """
    Same as the function above, but one column is intentionally shorter than the
    others.
    """
    data = gen_valid_data()
    data["Short Column"] = [1, 2, 3, 4]
    return data


def gen_too_long_column_data() -> dict[str, t.Iterable[t.Any]]:
    """
    Same as the function above, but one column is intentionally longer than the
    others.
    """
    data = gen_valid_data()
    data["Long Column"] = [1, 2, 3, 4, 5, 6]
    return data


def into_all_formats(
    datagen: t.Callable[
        [],
        dict[str, t.Iterable[t.Any]],
    ],
) -> t.Iterable[tuple[t.Any, bool]]:
    """
    Given a data generator, return the same data in all input formats supported
    by `rio.Table`:

    - pandas DataFrame
    - polars DataFrame
    - numpy array
    - mapping of iterables
    - iterable of iterables

    Each result is a tuple of the data and a boolean indicating whether the
    resulting table should have headers.
    """
    # Pandas DataFrame
    yield pd.DataFrame(datagen()), True

    # Polars DataFrame
    #
    # In order to make a column hold arbitrary Python objects, the dtype must be
    # explicitly set to `pl.Object`.
    raw_data = datagen()
    raw_data["Objects List"] = pl.Series(
        "objects",
        raw_data.pop("Objects List"),
        dtype=pl.Object,
    )
    yield pl.DataFrame(raw_data), True

    # NumPy array
    #
    # Numpy is problematic, because it cannot store different types of data in
    # the same array. It implicitly converts everything to strings, which makes
    # the later correctness checks fail.
    #
    # yield (
    #     np.column_stack(
    #         [list(column) for column in datagen().values()],
    #     ),
    #     False,
    # )

    # Mapping of iterables
    yield datagen(), True

    # Iterable of iterables. These are row-major, so the values must be
    # transposed
    rows = list(zip(*datagen().values()))
    yield rows, False


def assert_columns_match_data(
    datagen: t.Callable[
        [],
        dict[str, t.Iterable[t.Any]],
    ],
    should_have_headers: bool,
    headers_are: list[str] | None,
    columns_are: list[list[t.Any]],
) -> None:
    """
    Asserts that columns in the standardized format used by `rio.Table` match
    what would be expected from the data generator.
    """
    data = datagen()

    # Do the headers match?
    if should_have_headers:
        assert headers_are is not None
        assert headers_are == list(data.keys())
    else:
        assert headers_are is None

    # Correct number of columns?
    assert len(columns_are) == len(data)

    # Column values
    for ii, (column_name, column_raw) in enumerate(data.items()):
        column_is = columns_are[ii]

        column_should = rio.components.table._convert_iterable(
            column_raw,
            DATE_FORMAT_STRING,
        )

        print(ii, column_name)
        print(f"Column is:     {column_is}")
        print(f"Column should: {column_should}")

        assert column_is == column_should


@pytest.mark.parametrize(
    "data, should_have_headers",
    into_all_formats(gen_valid_data),
)
def test_valid_data(data: t.Any, should_have_headers: bool) -> None:
    """
    Tests that valid data is correctly columnized.
    """
    headers_are, columns_are = rio.components.table._data_to_columnar(
        data,
        DATE_FORMAT_STRING,
    )

    assert_columns_match_data(
        datagen=gen_valid_data,
        should_have_headers=should_have_headers,
        headers_are=headers_are,
        columns_are=columns_are,
    )


def test_short_column() -> None:
    """
    Tests that data with a column that is too short fails as expected.
    """
    data = gen_too_short_column_data()

    # The only format supporting too short data is a mapping. All other formats
    # would immediately raise an error, before even being able to pass the data
    # to a table.
    #
    # -> No need for fancy formats, just pass in the dict directly.
    with pytest.raises(ValueError):
        rio.components.table._data_to_columnar(
            data,
            DATE_FORMAT_STRING,
        )


def test_long_column() -> None:
    """
    Tests that data with a column that is too long fails as expected.
    """
    data = gen_too_long_column_data()

    # The only format supporting too short data is a mapping. All other formats
    # would immediately raise an error, before even being able to pass the data
    # to a table.
    #
    # -> No need for fancy formats, just pass in the dict
    with pytest.raises(ValueError):
        rio.components.table._data_to_columnar(
            data,
            DATE_FORMAT_STRING,
        )


def test_1d_array() -> None:
    """
    Creating a table from a 1D array should fail, as tables are inherently
    two-dimensional.
    """
    with pytest.raises(ValueError):
        rio.components.table._data_to_columnar(
            np.array([1, 2, 3]),
            DATE_FORMAT_STRING,
        )


def test_2d_array() -> None:
    """
    Creating a table from a 2D array should work.
    """
    headers, columns = rio.components.table._data_to_columnar(
        np.array([[1, 2, 3], [4, 5, 6]]),
        DATE_FORMAT_STRING,
    )

    assert_columns_match_data(
        datagen=lambda: {
            "0": [1, 4],
            "1": [2, 5],
            "2": [3, 6],
        },
        should_have_headers=False,
        headers_are=headers,
        columns_are=columns,
    )


def test_3d_array() -> None:
    """
    Creating a table from a 3D array should fail, as tables are inherently
    two-dimensional.
    """
    with pytest.raises(ValueError):
        rio.components.table._data_to_columnar(
            np.array([[[1, 2], [3, 4]]]),
            DATE_FORMAT_STRING,
        )
