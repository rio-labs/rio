import math
import re
import typing as t

import pytest

import rio
import rio.utils


def _assert_stops_match(
    stops_should: t.Iterable[tuple[rio.Color, float]],
    stops_are: t.Iterable[tuple[rio.Color, float]],
) -> None:
    """
    Given two lists of stops (all with positions), verify that they are
    identical.
    """
    stops_should = list(stops_should)
    stops_are = list(stops_are)

    assert len(stops_are) == len(stops_should)

    for stop_should, stop_are in zip(stops_should, stops_are):
        assert isinstance(stop_should, tuple)
        assert isinstance(stop_are, tuple)

        assert len(stop_should) == 2
        assert len(stop_are) == 2

        color_should, position_should = stop_should
        color_are, position_are = stop_are

        assert color_should.hexa == color_are.hexa
        assert math.isclose(position_should, position_are)


@pytest.mark.parametrize(
    "input_type,output_type",
    [
        # Simple cases
        ("pdf", "pdf"),
        (".Pdf", "pdf"),
        (".PDF", "pdf"),
        ("*pdf", "pdf"),
        ("*.Pdf", "pdf"),
        ("*.PDF", "pdf"),
        ("application/pdf", "pdf"),
        # Make sure the results are standardized
        (".jpg", "jpg"),
        # (".jpeg", "jpg"),
        ("image/jpeg", "jpg"),
        # Invalid MIME types
        ("not/a/real/type", "type"),
        ("////Type", "type"),
    ],
)
def test_standardize_file_types(
    input_type: str,
    output_type: str,
) -> None:
    cleaned_type = rio.utils.normalize_file_extension(input_type)
    assert cleaned_type == output_type


@pytest.mark.parametrize(
    "unsorted_sequence,keys,sorted_sequence_should",
    [
        (
            [0, 1, 2, 3, 4],
            [0, 1, 2, 3, 4],
            [0, 1, 2, 3, 4],
        ),
        (
            [4, 3, 2, 1, 0],
            [4, 3, 2, 1, 0],
            [0, 1, 2, 3, 4],
        ),
        (
            [4, 3, 2, 1, 0],
            [4, None, None, None, 0],
            [0, 3, 2, 1, 4],
        ),
        (
            [0, 1, 2, 3],
            [0, 1, 1, 3],
            [0, 1, 2, 3],
        ),
        (
            [3, 2, 1, 0],
            [3, 1, 1, 0],
            [0, 2, 1, 3],
        ),
        (
            [0, 1, 2, 3],
            [0, None, None, None],
            [0, 1, 2, 3],
        ),
        (
            [0, 1, 2, 3],
            [9, None, None, None],
            [1, 2, 3, 0],
        ),
    ],
)
def test_soft_sort(
    unsorted_sequence: list[int],
    keys: list[int],
    sorted_sequence_should: list[int],
) -> None:
    # Sort the sequence
    sorted_sequence_is = unsorted_sequence.copy()
    rio.utils.soft_sort(
        sorted_sequence_is,
        key=lambda x: keys[unsorted_sequence.index(x)],
    )

    # Verify the result
    assert sorted_sequence_is == sorted_sequence_should


@pytest.mark.parametrize(
    "stops_in, stops_should",
    [
        # No explicit positions
        (
            (rio.Color.BLACK,),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.BLACK, 1.0),
            ),
        ),
        (
            (
                rio.Color.BLACK,
                rio.Color.WHITE,
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.WHITE, 1.0),
            ),
        ),
        (
            (
                rio.Color.BLACK,
                rio.Color.BLUE,
                rio.Color.WHITE,
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.BLUE, 0.5),
                (rio.Color.WHITE, 1.0),
            ),
        ),
        # Containing explicit positions
        (
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.WHITE, 1.0),
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.WHITE, 1.0),
            ),
        ),
        (
            (
                (rio.Color.BLACK, 0.0),
                rio.Color.WHITE,
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.WHITE, 1.0),
            ),
        ),
        (
            (
                (rio.Color.BLACK, 0.0),
                rio.Color.BLUE,
                rio.Color.WHITE,
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.BLUE, 0.5),
                (rio.Color.WHITE, 1.0),
            ),
        ),
        (
            (
                (rio.Color.BLACK, 0.0),
                rio.Color.RED,
                rio.Color.GREEN,
                rio.Color.BLUE,
                (rio.Color.CYAN, 0.8),
                rio.Color.MAGENTA,
                (rio.Color.WHITE, 1.0),
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.RED, 0.2),
                (rio.Color.GREEN, 0.4),
                (rio.Color.BLUE, 0.6),
                (rio.Color.CYAN, 0.8),
                (rio.Color.MAGENTA, 0.9),
                (rio.Color.WHITE, 1.0),
            ),
        ),
        # Duplicate positions
        (
            (
                rio.Color.BLACK,
                (rio.Color.RED, 0.5),
                (rio.Color.GREEN, 0.5),
                rio.Color.WHITE,
            ),
            (
                (rio.Color.BLACK, 0.0),
                (rio.Color.RED, 0.5),
                (rio.Color.GREEN, 0.5),
                (rio.Color.WHITE, 1.0),
            ),
        ),
    ],
)
def test_interpolation_is_correct(
    stops_in: tuple[rio.Color, ...],
    stops_should: tuple[tuple[rio.Color, float], ...],
) -> None:
    """
    Test that the interpolation function correctly assigns positions to stops.
    """
    stops_are = rio.utils.verify_and_interpolate_gradient_stops(stops_in)
    _assert_stops_match(stops_should, stops_are)


@pytest.mark.parametrize(
    "stops_in, error_msg",
    [
        # Empty stops
        (
            tuple(),
            "Gradients must have at least one stop",
        ),
        # Position out of range
        (
            (
                (rio.Color.BLACK, -0.1),
                (rio.Color.WHITE, 1.0),
            ),
            "Gradient stop positions must be in range [0, 1], but stop 0 is at position -0.1",
        ),
        (
            (
                (rio.Color.BLACK, 0.1),
                (rio.Color.WHITE, 1.1),
            ),
            "Gradient stop positions must be in range [0, 1], but stop 1 is at position 1.1",
        ),
        # Positions not ascending
        (
            (
                (rio.Color.BLACK, 0.8),
                (rio.Color.WHITE, 0.2),
            ),
            "Gradient stops must be in ascending order, but stop 0 is at position 0.8 while stop 1 is at position 0.2",
        ),
        (
            (
                rio.Color.RED,
                (rio.Color.BLACK, 0.8),
                rio.Color.BLUE,
                (rio.Color.WHITE, 0.2),
            ),
            "Gradient stops must be in ascending order, but stop 1 is at position 0.8 while stop 3 is at position 0.2",
        ),
    ],
)
def test_invalid_stops_raise_error(
    stops_in: tuple[rio.Color | tuple[rio.Color, float], ...],
    error_msg: str,
) -> None:
    """
    Test that invalid gradient stop configurations raise appropriate errors.
    """
    with pytest.raises(ValueError, match=re.escape(error_msg)):
        rio.utils.verify_and_interpolate_gradient_stops(stops_in)
