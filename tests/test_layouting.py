import math
from typing import *  # type: ignore

import pytest

import rio.data_models
import rio.debug.layouter
import rio.testing
from tests.utils.layouting import cleanup, verify_layout

# pytestmark = pytest.mark.async_timeout(30)


@pytest.fixture(scope="module", autouse=True)
async def cleanup_layouter():
    yield
    await cleanup()


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


@pytest.mark.parametrize(
    "container_type",
    [rio.Row, rio.Column],
)
async def test_linear_container_with_no_extra_width(
    container_type: Type,
) -> None:
    await verify_layout(
        lambda: container_type(
            rio.Text("hi", width=100),
            rio.Button("clicky", width=400),
        )
    )


@pytest.mark.parametrize(
    "horizontal",
    [True, False],
)
@pytest.mark.parametrize(
    "first_child_grows",
    [True, False],
)
@pytest.mark.parametrize(
    "second_child_grows",
    [True, False],
)
@pytest.mark.parametrize(
    "proportions",
    [
        None,
        "homogeneous",
        [1, 2],
        [2, 1],
    ],
)
async def test_linear_container_with_extra_width(
    horizontal: bool,
    first_child_grows: bool,
    second_child_grows: bool,
    proportions: None | Literal["homogeneous"] | List[int],
) -> None:
    """
    A battery of scenarios to test the most common containers - Rows & Columns.
    """
    if horizontal:
        container_type = rio.Row

        first_child_width = "grow" if first_child_grows else 10
        first_child_height = "natural"

        second_child_width = "grow" if second_child_grows else 20
        second_child_height = "natural"

        parent_width = 50
        parent_height = "natural"
    else:
        container_type = rio.Column

        first_child_width = "natural"
        first_child_height = "grow" if first_child_grows else 10

        second_child_width = "natural"
        second_child_height = "grow" if second_child_grows else 20

        parent_width = "natural"
        parent_height = 50

    await verify_layout(
        lambda: container_type(
            rio.Text(
                "short-text",
                width=first_child_width,
                height=first_child_height,
            ),
            rio.Text(
                "very-much-longer-text",
                width=second_child_width,
                height=second_child_height,
            ),
            # It would be nice to vary the spacing as well, but that would once
            # again double the number of tests this case already has. Simply
            # always specify a spacing, since that is the harder case anyway.
            spacing=2,
            proportions=proportions,
            width=parent_width,
            height=parent_height,
            align_x=0.5,
            align_y=0.5,
        )
    )


async def test_stack() -> None:
    """
    All children in stacks should be the same size.
    """
    layouter = await verify_layout(
        lambda: rio.Stack(
            rio.Text("Small", key="small_text", width=10, height=20),
            rio.Text("Large", key="large_text", width=30, height=40),
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


@pytest.mark.parametrize(
    "parent_width,parent_height",
    [
        (10, 50),
        (50, 10),
    ],
)
async def test_aspect_ratio_container_small_child(
    parent_width: float,
    parent_height: float,
) -> None:
    """
    Create a rectangle with a fixed aspect ratio, and make sure it matches
    expectations.

    The child is smaller than the parent and will thus be pulled larger.
    """
    parent_aspect_ratio = parent_width / parent_height
    child_aspect_ratio = 2

    layout = await verify_layout(
        lambda: rio.Container(
            rio.AspectRatioContainer(
                rio.Rectangle(
                    fill=rio.Color.RED,
                    key="child",
                ),
                aspect_ratio=child_aspect_ratio,
            ),
            width=parent_width,
            height=parent_height,
            align_x=0,
            align_y=0,
        )
    )

    # How large should the child be?
    if parent_aspect_ratio > child_aspect_ratio:
        child_width_should = parent_height * child_aspect_ratio
        child_height_should = parent_height
    else:
        child_width_should = parent_width
        child_height_should = parent_width / child_aspect_ratio

    # Is it though?
    child_layout = layout.get_layout_by_key("child")

    assert math.isclose(child_layout.allocated_inner_width, child_width_should)
    assert math.isclose(
        child_layout.allocated_inner_height, child_height_should
    )


@pytest.mark.parametrize(
    "child_specified_width,child_specified_height,child_width_should,child_height_should",
    [
        (10, 50, 20, 100),
        (50, 10, 50, 25),
    ],
)
async def test_aspect_ratio_container_large_child(
    child_specified_width: float,
    child_specified_height: float,
    child_width_should: float,
    child_height_should: float,
) -> None:
    """
    Create a rectangle with a fixed aspect ratio, and make sure it matches
    expectations.

    The child is larger than the parent and will thus push the parent larger.
    """
    child_aspect_ratio = 2

    layout = await verify_layout(
        lambda: rio.Container(
            rio.AspectRatioContainer(
                rio.Rectangle(
                    fill=rio.Color.RED,
                    width=child_specified_width,
                    height=child_specified_height,
                    key="child",
                ),
                aspect_ratio=child_aspect_ratio,
            ),
            width=20,
            height=20,
            align_x=0,
            align_y=0,
        )
    )

    # Is it though?
    child_layout = layout.get_layout_by_key("child")

    assert math.isclose(child_layout.allocated_inner_width, child_width_should)
    assert math.isclose(
        child_layout.allocated_inner_height, child_height_should
    )


@pytest.mark.parametrize(
    "scroll_x,scroll_y",
    [
        ("never", "auto"),
        ("auto", "never"),
        ("auto", "auto"),
    ],
)
async def test_scrolling(
    scroll_x: Literal["never", "always", "auto"],
    scroll_y: Literal["never", "always", "auto"],
) -> None:
    await verify_layout(
        lambda: rio.ScrollContainer(
            rio.Text("hi", width=30, height=30),
            scroll_x=scroll_x,
            scroll_y=scroll_y,
            width=20,
            height=20,
            align_x=0.5,
            align_y=0.5,
        )
    )


async def test_ellipsized_text() -> None:
    layouter = await verify_layout(
        lambda: rio.Text(
            "My natural size should become 0",
            wrap="ellipsize",
            align_x=0,
            key="text",
        )
    )

    layout = layouter.get_layout_by_key("text")

    assert layout.natural_width == 0


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
            rio.Text("foo", width=5),
            rio.Text("bar", width=10),
            rio.Text("qux", width=4),
            column_spacing=3,
            row_spacing=2,
            justify=justify,  # type: ignore
            width=20,
            align_x=0,
        )
    )
