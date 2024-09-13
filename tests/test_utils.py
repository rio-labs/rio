import pytest

import rio


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
