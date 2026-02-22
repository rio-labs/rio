"""
Tests that different types of data formats accepted by tables are correctly
turned into the internal column format.
"""

import json
import sys
import typing as t
from datetime import datetime

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import rio
import rio.maybes

# Tables work with a lot of optionally supported modules. Make sure Rio is aware
# of which ones are available.
rio.maybes.initialize()


DATE_FORMAT_STRING = "%Y-%m-%d"


def assert_is_json_serializable(columns: list[list[t.Any]]) -> None:
    try:
        json.dumps(columns)
    except TypeError as e:
        raise AssertionError(f"Columns are not JSON serializable: {e}") from e


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
    - pyarrow Table
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

    # PyArrow Table
    #
    # PyArrow does not support arbitrary Python objects.
    raw_data = datagen()
    raw_data.pop("Objects List")
    yield pa.table(raw_data), True

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
    allows_arbitrary_py_objects: bool = True,
) -> None:
    """
    Asserts that columns in the standardized format used by `rio.Table` match
    what would be expected from the data generator.
    """
    data = datagen()
    if not allows_arbitrary_py_objects:
        del data["Objects List"]

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
    allow_arbitrary_py_objects = not isinstance(data, pa.Table)
    try:
        headers_are, columns_are = rio.components.table._data_to_columnar(
            data,
            DATE_FORMAT_STRING,
        )
    except pa.ArrowInvalid:
        if sys.platform == "win32":
            pytest.xfail("Pyarrow bug")

        raise

    assert_columns_match_data(
        datagen=gen_valid_data,
        should_have_headers=should_have_headers,
        headers_are=headers_are,
        columns_are=columns_are,
        allows_arbitrary_py_objects=allow_arbitrary_py_objects,
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


@pytest.mark.parametrize(
    "data",
    [
        # pandas: empty cell → NaN (the original bug)
        pd.DataFrame({"A": [1], "B": [None], "C": [3]}),
        # pandas: explicit NaN in float column
        pd.DataFrame({"A": [1.0, float("nan"), 3.0]}),
        # pandas: inf/-inf in float column
        pd.DataFrame({"A": [1.0, float("inf"), float("-inf")]}),
        # pandas: None in string column
        pd.DataFrame({"A": ["hello", None, "world"]}),
        # pandas: np.nan in object/string column
        pd.DataFrame({"A": pd.Series(["hello", np.nan, "world"])}),
        # polars: null in numeric column
        pl.DataFrame({"A": pl.Series([1.0, None, 3.0])}),
        # polars: NaN in float column (distinct from null in polars)
        pl.DataFrame({"A": pl.Series([1.0, float("nan"), 3.0])}),
        # polars: both null AND NaN in same float column
        pl.DataFrame({"A": pl.Series([1.0, None, float("nan"), 3.0])}),
        # polars: inf/-inf in float column
        pl.DataFrame({"A": pl.Series([1.0, float("inf"), float("-inf")])}),
        # polars: null in boolean column
        pl.DataFrame({"A": pl.Series([True, None, False])}),
        # pandas: null in boolean column
        pd.DataFrame({"A": pd.array([True, None, False], dtype="boolean")}),
        # pandas: null in datetime column
        pd.DataFrame({"A": pd.to_datetime(["2025-01-01", None, "2025-01-03"])}),
        # polars: null in datetime column
        pl.DataFrame(
            {
                "A": pl.Series(
                    ["2025-01-01", None, "2025-01-03"]
                ).str.to_datetime()
            }
        ),
        # mapping with None/NaN/inf
        {"A": [1, None, float("nan"), float("inf"), float("-inf"), 2]},
        # iterable of iterables with None/NaN/inf
        [[1, None], [float("nan"), float("inf")]],
    ],
)
def test_missing_values_produce_valid_json(data: t.Any) -> None:
    """
    NaN, null, and inf values must not produce invalid JSON tokens. These would
    cause JSON.parse to throw in the browser.
    """
    _, columns = rio.components.table._data_to_columnar(
        data, DATE_FORMAT_STRING
    )
    assert_is_json_serializable(columns)


def test_missing_values_render_as_empty_string() -> None:
    """
    NaN and null cells should be displayed as empty strings in the table.
    """
    df = pd.DataFrame(
        {"A": [1, None, 3], "B": [float("nan"), 2.0, float("inf")]}
    )
    _, columns = rio.components.table._data_to_columnar(df, DATE_FORMAT_STRING)

    assert columns[0] == [1, "", 3]
    assert columns[1] == ["", 2.0, ""]


def test_numpy_nan_inf_produce_valid_json() -> None:
    """
    NumPy arrays with NaN or inf must not produce invalid JSON.
    """
    arr = np.array([[1.0, float("nan")], [float("inf"), 2.0]])
    _, columns = rio.components.table._data_to_columnar(arr, DATE_FORMAT_STRING)
    assert_is_json_serializable(columns)
    assert columns[0] == [1.0, ""]
    assert columns[1] == ["", 2.0]


def test_mapping_nan_inf_produce_valid_json() -> None:
    """
    Mapping input with NaN, None, or inf must not produce invalid JSON.
    """
    data = {
        "A": [1, None, float("nan"), float("inf"), float("-inf"), 2],
    }
    _, columns = rio.components.table._data_to_columnar(
        data, DATE_FORMAT_STRING
    )
    assert_is_json_serializable(columns)
    assert columns[0] == [1, "", "", "", "", 2]
