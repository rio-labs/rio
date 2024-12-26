import asyncio
import typing as t

import pytest

import rio.data_models
import rio.debug.layouter
import rio.testing
from tests.utils.layouting import BrowserClient, cleanup, setup, verify_layout

# For debugging. Set this to a number > 0 if you want to look at the browser.
#
# Note: Chrome's console doesn't show `console.debug` messages per default. To
# see them, click on "All levels" and check "Verbose".
DEBUG_SHOW_BROWSER_DURATION = 0

if DEBUG_SHOW_BROWSER_DURATION:
    pytestmark = pytest.mark.async_timeout(DEBUG_SHOW_BROWSER_DURATION + 30)

    import tests.utils.layouting

    tests.utils.layouting.DEBUG_EXTRA_SLEEP_DURATION = (
        DEBUG_SHOW_BROWSER_DURATION
    )


@pytest.fixture(scope="module", autouse=True)
async def manage_server():
    await setup()
    yield
    await cleanup()


async def test_dropdowns_work_in_dev_tools() -> None:
    # Dropdowns (and other popups) have often been broken in the dev tools, due
    # to z-index issues and other reasons. This test makes sure that they work.

    async with BrowserClient(rio.Spacer, debug_mode=True) as client:
        # Click the 2nd entry in the sidebar, which is the "Icons" tab
        await client.execute_js(
            "document.querySelector('.rio-switcher-bar-option:nth-child(2) .rio-switcher-bar-icon').click()",
        )
        await asyncio.sleep(0.5)

        # Click an arbitrary icon in the list
        await client.execute_js(
            "document.querySelector('.rio-switcher .rio-icon').click()"
        )
        await asyncio.sleep(0.5)

        # Open the dropdown
        await client.execute_js(
            "document.querySelector('.rio-dropdown input').focus()"
        )
        await asyncio.sleep(0.5)

        # Make sure the dropdown list is open and visible
        is_entirely_visible = await client.execute_js("""
            new Promise((resolve) => {
                let elem = document.querySelector(".rio-dropdown-options");
                
                let observer = new IntersectionObserver((entries) => {
                    resolve(entries[0].intersectionRatio === 1);
                });
                observer.observe(elem);
            });
        """)
        assert is_entirely_visible


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
    container_type: t.Type,
) -> None:
    await verify_layout(
        lambda: container_type(
            rio.Text("hi", min_width=100),
            rio.Button("clicky", min_width=400),
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
    proportions: None | t.Literal["homogeneous"] | list[int],
) -> None:
    """
    A battery of scenarios to test the most common containers - Rows & Columns.
    """
    if horizontal:
        container_type = rio.Row

        if first_child_grows:
            first_child_width = 0
            first_child_grow_x = True
        else:
            first_child_width = 10
            first_child_grow_x = False

        if second_child_grows:
            second_child_width = 0
            second_child_grow_x = True
        else:
            second_child_width = 20
            second_child_grow_x = False

        first_child_height = 0
        second_child_height = 0

        first_child_grow_y = False
        second_child_grow_y = False

        parent_width = 50
        parent_height = 0
    else:
        container_type = rio.Column

        if first_child_grows:
            first_child_height = 0
            first_child_grow_y = True
        else:
            first_child_height = 10
            first_child_grow_y = False

        if second_child_grows:
            second_child_height = 0
            second_child_grow_y = True
        else:
            second_child_height = 20
            second_child_grow_y = False

        first_child_width = 0
        second_child_width = 0

        first_child_grow_x = False
        second_child_grow_x = False

        parent_width = 0
        parent_height = 50

    await verify_layout(
        lambda: container_type(
            rio.Text(
                "short-text",
                min_width=first_child_width,
                min_height=first_child_height,
                grow_x=first_child_grow_x,
                grow_y=first_child_grow_y,
            ),
            rio.Text(
                "very-much-longer-text",
                min_width=second_child_width,
                min_height=second_child_height,
                grow_x=second_child_grow_x,
                grow_y=second_child_grow_y,
            ),
            # It would be nice to vary the spacing as well, but that would once
            # again double the number of tests this case already has. Simply
            # always specify a spacing, since that is the harder case anyway.
            spacing=2,
            proportions=proportions,
            min_width=parent_width,
            min_height=parent_height,
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
