import typing as t

import pytest

import rio
from tests.utils.layouting import verify_layout


@pytest.mark.parametrize(
    "scroll_x,scroll_y",
    [
        ("never", "auto"),
        ("auto", "never"),
        ("auto", "auto"),
    ],
)
async def test_scrolling(
    scroll_x: t.Literal["never", "always", "auto"],
    scroll_y: t.Literal["never", "always", "auto"],
) -> None:
    await verify_layout(
        lambda: rio.ScrollContainer(
            rio.Text("hi", min_width=30, min_height=30),
            scroll_x=scroll_x,
            scroll_y=scroll_y,
            min_width=20,
            min_height=20,
            align_x=0.5,
            align_y=0.5,
        )
    )
