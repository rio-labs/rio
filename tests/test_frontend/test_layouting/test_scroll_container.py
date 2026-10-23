import asyncio
import itertools
import typing as t

import pytest

import rio
import rio.testing
from tests.utils.layouting import verify_layout

ScrollMode = t.Literal["never", "auto", "always"]

# Every combination of horizontal and vertical scroll modes
ALL_SCROLL_MODES = list(
    itertools.product(["never", "auto", "always"], repeat=2)
)

# How far two pixel measurements may differ and still count as equal. Browsers
# round sizes to fractions of a pixel, so exact comparisons would be flaky.
PIXEL_TOLERANCE = 1.5

# Measures a scroll container in the browser. The scroll container itself is
# the element tagged with its id, and its first child is the element that
# actually scrolls. The content is located separately by its own id.
MEASURE_SCROLL_CONTAINER_JS = """
([containerId, contentId]) => {
    const container = document.querySelector(`[dbg-id="${containerId}"]`);
    const scroller = container.firstElementChild;
    const content = document.querySelector(`[dbg-id="${contentId}"]`);

    const containerRect = container.getBoundingClientRect();
    const scrollerRect = scroller.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();

    return {
        container_width: containerRect.width,
        container_height: containerRect.height,
        scroller_width: scrollerRect.width,
        scroller_height: scrollerRect.height,
        visible_width: scroller.clientWidth,
        visible_height: scroller.clientHeight,
        content_width: contentRect.width,
        content_height: contentRect.height,
        pixels_per_rem: globalThis.pixelsPerRem,
        window_width: window.innerWidth,
        window_height: window.innerHeight,
    };
}
"""


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


async def _measure_scroll_container(
    client: rio.testing.BrowserClient,
    container: rio.ScrollContainer,
    content: rio.Component,
) -> dict[str, float]:
    """
    Measures a scroll container and its content in the browser, in pixels.

    This function reads the on-screen size of the scroll container, of the
    element inside it that does the scrolling, of the part of that element that
    is visible (excluding scroll bars), and of the content. Together these tell
    whether the content really fills the space the container was given, which
    the layout comparison against the Python layouter can't see, since that
    layouter doesn't look inside scroll containers.
    """
    # Give the browser a moment to finish laying out the page
    await asyncio.sleep(0.5)

    # Read all sizes in one go
    return await client.playwright_page.evaluate(
        MEASURE_SCROLL_CONTAINER_JS,
        [container._id_, content._id_],
    )


def _assert_close(actual: float, expected: float, what: str) -> None:
    """
    Fails the test if two pixel measurements differ noticeably.

    This function compares two sizes measured in the browser while allowing for
    the sub-pixel rounding that browsers do, so that only real layout problems
    fail the test. The description ends up in the failure message to say which
    measurement was off.
    """
    assert abs(actual - expected) <= PIXEL_TOLERANCE, (
        f"{what}: {actual} != {expected}"
    )


def _build_in_parent(
    parent: str,
    scroll_x: ScrollMode,
    scroll_y: ScrollMode,
) -> rio.Component:
    """
    Builds a scroll container in one of several typical surroundings.

    Whether a scroll container's content fills the container depends on how
    the container got its size. A parent may stretch it, it may grow inside a
    column next to other components, or it may only be held open by its own
    minimum size. This function builds those situations so each one can be
    tested. The content has no size of its own and can be found by the key
    "content".
    """
    # Center the container when testing its own minimum size, so that nothing
    # else gives it its size
    if parent == "own_min_size":
        size_kwargs = dict(
            min_width=20, min_height=20, align_x=0.5, align_y=0.5
        )
    else:
        size_kwargs = {}

    # Build the container with content that has no size of its own
    container = rio.ScrollContainer(
        rio.Rectangle(fill=rio.Color.RED, key="content"),
        scroll_x=scroll_x,
        scroll_y=scroll_y,
        **size_kwargs,
    )

    # Let the window itself stretch the container, or let the container's own
    # minimum size decide
    if parent in ("window", "own_min_size"):
        return container

    # Let the container grow inside a column, below a fixed size header
    if parent == "column":
        return rio.Column(
            rio.Rectangle(fill=rio.Color.GREY, min_height=10),
            container,
        )

    # Stack the container on top of a background, which in turn grows inside a
    # column. This is the situation the bug was originally reported in.
    if parent == "stack":
        return rio.Column(
            rio.Rectangle(fill=rio.Color.GREY, min_height=10),
            rio.Stack(
                rio.Rectangle(fill=rio.Color.GREY),
                container,
                grow_y=True,
            ),
        )

    raise ValueError(f"Unknown parent: {parent}")


@pytest.mark.parametrize("scroll_x,scroll_y", ALL_SCROLL_MODES)
@pytest.mark.parametrize(
    "parent",
    ["window", "column", "stack", "own_min_size"],
)
async def test_content_fills_container(
    scroll_x: ScrollMode,
    scroll_y: ScrollMode,
    parent: str,
) -> None:
    """
    Checks that content without a natural size fills its scroll container.

    A scroll container is meant to pass its whole size on to its content, just
    like any other single child container. That must hold for every scroll
    mode, and no matter whether the container was stretched by its parent or
    only held open by its own minimum size. This used to break for containers
    that don't scroll vertically, and for containers with a minimum size.
    """
    # Show the container in the requested surroundings and measure it
    async with rio.testing.BrowserClient(
        lambda: _build_in_parent(parent, scroll_x, scroll_y)
    ) as client:
        sizes = await _measure_scroll_container(
            client,
            client.get_component(rio.ScrollContainer),
            client.get_component(rio.Rectangle, key="content"),
        )

    # The scrolling element must fill the container. If it doesn't, the
    # content can't fill the container either.
    _assert_close(
        sizes["scroller_width"],
        sizes["container_width"],
        "scroller width",
    )
    _assert_close(
        sizes["scroller_height"],
        sizes["container_height"],
        "scroller height",
    )

    # The content must fill everything that's visible, leaving out only the
    # space taken by scroll bars
    _assert_close(
        sizes["content_width"],
        sizes["visible_width"],
        "content width",
    )
    _assert_close(
        sizes["content_height"],
        sizes["visible_height"],
        "content height",
    )

    # Make sure the container really got the size it should have. Otherwise a
    # collapsed container would pass the checks above.
    if parent == "own_min_size":
        expected_size = 20 * sizes["pixels_per_rem"]
        _assert_close(
            sizes["container_width"],
            expected_size,
            "container width",
        )
        _assert_close(
            sizes["container_height"],
            expected_size,
            "container height",
        )
    else:
        _assert_close(
            sizes["container_width"],
            sizes["window_width"],
            "container width",
        )


@pytest.mark.parametrize("scroll_x,scroll_y", ALL_SCROLL_MODES)
async def test_large_content_scrolls_or_grows_container(
    scroll_x: ScrollMode,
    scroll_y: ScrollMode,
) -> None:
    """
    Checks how a scroll container handles content larger than the window.

    In directions that scroll, the container must stay within the space it was
    given and let the content overflow into the scrollable area. In directions
    that never scroll, the content's size must push the container to become
    larger instead. In either case the content itself must never be squeezed
    below the size it asked for.
    """
    # Show a container whose content is far larger than the window, and
    # measure it
    async with rio.testing.BrowserClient(
        lambda: rio.ScrollContainer(
            rio.Rectangle(fill=rio.Color.RED, min_width=100, min_height=100),
            scroll_x=scroll_x,
            scroll_y=scroll_y,
        )
    ) as client:
        sizes = await _measure_scroll_container(
            client,
            client.get_component(rio.ScrollContainer),
            client.get_component(rio.Rectangle),
        )

    # The content must keep the size it asked for
    requested_size = 100 * sizes["pixels_per_rem"]
    assert sizes["content_width"] >= requested_size - PIXEL_TOLERANCE
    assert sizes["content_height"] >= requested_size - PIXEL_TOLERANCE

    # Horizontally, either scroll within the window or grow to fit the content
    if scroll_x == "never":
        assert sizes["container_width"] >= requested_size - PIXEL_TOLERANCE
    else:
        _assert_close(
            sizes["container_width"],
            sizes["window_width"],
            "container width",
        )

    # Vertically, either scroll within the window or grow to fit the content
    if scroll_y == "never":
        assert sizes["container_height"] >= requested_size - PIXEL_TOLERANCE
    else:
        _assert_close(
            sizes["container_height"],
            sizes["window_height"],
            "container height",
        )


class _GrowingLog(rio.Component):
    """
    A scrolling list of lines that sticks to its bottom end.

    This component imitates a chat or log view: a scroll container that starts
    out scrolled all the way down and should stay there as more lines are
    added. Changing the number of lines rebuilds the list with that many
    entries, which lets a test add content after the page is shown.
    """

    # How many lines are currently shown
    line_count: int = 80

    def build(self) -> rio.Component:
        return rio.ScrollContainer(
            rio.Column(
                *[rio.Text(f"Line {index}") for index in range(self.line_count)]
            ),
            scroll_x="never",
            initial_y=1,
            sticky_bottom=True,
        )


async def test_sticky_bottom_follows_new_content() -> None:
    """
    Checks that a container sticking to its bottom end stays there as content
    is added.

    With sticking to the bottom enabled, a scroll container that starts out
    scrolled to the end should follow along whenever its content grows, the way
    a chat window keeps showing the newest message. This relies on the content
    keeping its full height inside the scrolling element, which an earlier
    attempt at fixing the container's layout broke.
    """
    # Reads how far the container is scrolled down, and how far it could be
    measure_scroll_js = """
    () => {
        const container = document.querySelector('.rio-scroll-container');
        const scroller = container.firstElementChild;
        return [
            scroller.scrollTop,
            scroller.scrollHeight - scroller.clientHeight,
        ];
    }
    """

    async with rio.testing.BrowserClient(_GrowingLog) as client:
        page = client.playwright_page

        # The container must start out scrolled all the way to the end. Make
        # sure there's enough content to scroll at all, otherwise sticking to
        # the end isn't being tested.
        await asyncio.sleep(0.5)
        scroll_position, max_scroll_position = await page.evaluate(
            measure_scroll_js
        )
        assert max_scroll_position > 0
        _assert_close(scroll_position, max_scroll_position, "initial scroll")

        # Add more lines
        log = client.get_component(_GrowingLog)
        log.line_count = 120
        await client.wait_for_refresh()

        # The container must have followed the new content to the end
        await asyncio.sleep(0.5)
        scroll_position, new_max_scroll_position = await page.evaluate(
            measure_scroll_js
        )
        assert new_max_scroll_position > max_scroll_position
        _assert_close(
            scroll_position,
            new_max_scroll_position,
            "scroll after adding lines",
        )
