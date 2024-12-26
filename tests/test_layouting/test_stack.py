import rio
from tests.utils.layouting import verify_layout


async def test_stack() -> None:
    """
    All children in stacks should be the same size.
    """
    layouter = await verify_layout(
        lambda: rio.Stack(
            rio.Text("Small", key="small_text", min_width=10, min_height=20),
            rio.Text("Large", key="large_text", min_width=30, min_height=40),
            align_x=0,
            align_y=0,
        )
    )

    small_layout = layouter.get_layout_by_key("small_text")

    assert small_layout.left_in_viewport_inner == 0
    assert small_layout.top_in_viewport_inner == 0

    assert small_layout.allocated_inner_width == 30
    assert small_layout.allocated_inner_height == 40

    large_layout = layouter.get_layout_by_key("large_text")

    assert large_layout.left_in_viewport_inner == 0
    assert large_layout.top_in_viewport_inner == 0

    assert large_layout.allocated_inner_width == 30
    assert large_layout.allocated_inner_height == 40
