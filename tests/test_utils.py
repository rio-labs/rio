import pytest

import rio.utils


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
        # Make the results are standardized
        (".jpg", "jpg"),
        (".jpeg", "jpg"),
        # Invalid MIME types
        ("not/a/real/type", "type"),
        ("////Type", "type"),
    ],
)
def test_standardize_file_types(
    input_type: str,
    output_type: str,
) -> None:
    cleaned_type = rio.utils.normalize_file_type(input_type)
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
