import pytest

import rio
from tests.utils.layouting import verify_layout


@pytest.mark.parametrize(
    "text",
    [
        "",
        "short-text",
        "-".join(["long-text"] * 100),
    ],
)
async def test_single_component(text: str) -> None:
    """
    Just one component - this should fill the whole screen.
    """
    await verify_layout(lambda: rio.Text(text))


async def test_ellipsized_text() -> None:
    layouter = await verify_layout(
        lambda: rio.Text(
            "My natural size should become 0",
            overflow="ellipsize",
            align_x=0,
            key="text",
        )
    )

    layout = layouter.get_layout_by_key("text")

    assert layout.natural_width == 0
