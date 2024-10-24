"""
Tables support numpy-style 2D indexing. This is rather complex, hence the
tests here.
"""

import typing as t

import pytest

import rio


# Helper class for easily creating indices
class MakeIndex:
    def __getitem__(self, index) -> t.Any:
        return index


make_index = MakeIndex()


@pytest.mark.parametrize(
    "index,enable_column_names,result_should",
    [
        # Valid index without anything special
        (
            make_index[1:3, 4:7],
            False,
            (4, 1, 3, 2),
        ),
        # Selecting an entire column
        (
            make_index["a"],
            True,
            (0, 0, 1, 20),
        ),
        (
            make_index["b"],
            True,
            (1, 0, 1, 20),
        ),
        # Attempting to select a column, but no column names are available
        (
            make_index["a"],
            False,
            ValueError,
        ),
        # Selecting a non-existent column
        (
            make_index["invalid_column_name"],
            True,
            KeyError,
        ),
        # Selecting some rows in a column
        (
            make_index[1:3, "a"],
            True,
            (0, 1, 1, 2),
        ),
        # Attempting to select by name in the wrong axis
        (
            make_index["a", 0],
            True,
            ValueError,
        ),
        (
            make_index["a", "b"],
            True,
            ValueError,
        ),
        # Wrong number of indices
        (
            make_index[0],
            True,
            ValueError,
        ),
        (
            make_index[1, 2, 3],
            True,
            ValueError,
        ),
        (
            make_index[1, 2, 3, 4],
            True,
            ValueError,
        ),
        # Wrong datatypes
        (
            make_index[1.0],
            False,
            ValueError,
        ),
        (
            make_index[1.0, 2.0],
            False,
            ValueError,
        ),
        (
            make_index[1.0, 2.0, 3.0],
            False,
            ValueError,
        ),
        (
            make_index[True],
            False,
            ValueError,
        ),
        (
            make_index[True, False],
            False,
            ValueError,
        ),
        (
            make_index[True, False, True],
            False,
            ValueError,
        ),
        (
            make_index[None],
            False,
            ValueError,
        ),
        (
            make_index[None, None],
            False,
            ValueError,
        ),
        (
            make_index[None, None, None],
            False,
            ValueError,
        ),
        # Range selection
        (
            make_index[:, :],
            False,
            (0, 0, 10, 20),
        ),
        (
            make_index[5:, :],
            False,
            (0, 5, 10, 15),
        ),
        (
            make_index[:5, :],
            False,
            (0, 0, 10, 5),
        ),
        (
            make_index[:, 5:],
            False,
            (5, 0, 5, 20),
        ),
        (
            make_index[:, :5],
            False,
            (0, 0, 5, 20),
        ),
        # Range selection, but negative
        (
            make_index[-2:, :],
            False,
            (0, 18, 10, 2),
        ),
        (
            make_index[:-2, :],
            False,
            (0, 0, 10, 18),
        ),
        (
            make_index[:, -2:],
            False,
            (8, 0, 2, 20),
        ),
        (
            make_index[:, :-2],
            False,
            (0, 0, 8, 20),
        ),
        # Out of bounds
        (
            make_index[-50, :],
            False,
            IndexError,
        ),
        (
            make_index[:, -50],
            False,
            IndexError,
        ),
        # Ranged out of bounds
        (
            make_index[-60:, :],
            False,
            IndexError,
        ),
        (
            make_index[:-60, :],
            False,
            IndexError,
        ),
        (
            make_index[:, -60:],
            False,
            IndexError,
        ),
        (
            make_index[:, :-60],
            False,
            IndexError,
        ),
        # Incorrect types inside of slices
        (
            make_index[2.0:, :],
            False,
            ValueError,
        ),
        (
            make_index[:True, :],
            False,
            ValueError,
        ),
        (
            make_index[:, "Heyho":],
            False,
            ValueError,
        ),
        (
            make_index[:, :list],
            False,
            ValueError,
        ),
        # Indexing into the header
        (
            make_index["header", :],
            False,
            (0, "header", 10, 1),
        ),
        (
            make_index["header", 3:5],
            False,
            (3, "header", 2, 1),
        ),
        (
            make_index["header", -2:],
            False,
            (8, "header", 2, 1),
        ),
        (
            make_index["header", :-2],
            False,
            (0, "header", 8, 1),
        ),
        # Indexing into the header, but in the wrong axis
        (
            make_index[0, "header"],
            False,
            ValueError,
        ),
    ],
)
def test_indices(
    index: t.Any,
    enable_column_names: bool,
    result_should: tuple[
        int,
        int | t.Literal["header"],
        int,
        int,
    ]
    | t.Type[Exception],
) -> None:
    if enable_column_names:
        column_names = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    else:
        column_names = None

    # Should this work, or fail?
    if isinstance(result_should, tuple):
        # Let Rio bring the selection into the format (left, top, width, height)
        result_is = rio.components.table._indices_to_rectangle(
            index=index,
            column_names=column_names,
            data_width=10,
            data_height=20,
        )

        # Does reality match expectations?
        assert result_is == result_should

    else:
        with pytest.raises(result_should):
            rio.components.table._indices_to_rectangle(
                index,
                column_names=column_names,
                data_width=10,
                data_height=20,
            )
