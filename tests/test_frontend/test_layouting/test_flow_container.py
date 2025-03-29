import pytest

import rio
from tests.utils.layouting import verify_layout


@pytest.mark.parametrize(
    "justify",
    [
        "left",
        "right",
        "center",
        "justified",
        "grow",
    ],
)
async def test_flow_container_layout(justify: str) -> None:
    await verify_layout(
        lambda: rio.FlowContainer(
            rio.Text("foo", min_width=5),
            rio.Text("bar", min_width=10),
            rio.Text("qux", min_width=4),
            column_spacing=3,
            row_spacing=2,
            justify=justify,  # type: ignore
            min_width=20,
            align_x=0,
        )
    )
