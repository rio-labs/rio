from collections.abc import Callable

import pytest

import rio.testing
from tests.utils.headless_client import HeadlessClient


async def verify_layout(build: Callable[[], rio.Component]):
    async with HeadlessClient(build) as test_client:
        await test_client.verify_layout()


def row_with_no_extra_width():
    return rio.Row(
        rio.Text("hi", width=100),
        rio.Button("clicky", width=400),
    )


def row_with_extra_width_and_no_growers():
    return rio.Row(
        rio.Text("hi", width=5),
        rio.Button("clicky", width=10),
        width=25,
    )


def row_with_extra_width_and_one_grower():
    return rio.Row(
        rio.Text("hi", width=5),
        rio.Button("clicky", width="grow"),
        width=20,
    )


def scrolling_in_both_directions():
    return rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
    )


def scrolling_horizontally():
    return rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
        scroll_y="never",
    )


def scrolling_vertically():
    return rio.ScrollContainer(
        rio.Text("hi", width=30, height=30),
        width=20,
        height=20,
        align_x=0.5,
        align_y=0.5,
        scroll_x="never",
    )


@pytest.mark.parametrize(
    "build",
    [
        row_with_no_extra_width,
        row_with_extra_width_and_no_growers,
        row_with_extra_width_and_one_grower,
        scrolling_in_both_directions,
        scrolling_horizontally,
        scrolling_vertically,
    ],
)
@pytest.mark.async_timeout(20)
async def test_layout(build: Callable[[], rio.Component]):
    await verify_layout(build)


@pytest.mark.parametrize(
    "justify",
    ["left", "right", "center", "justified", "grow"],
)
@pytest.mark.async_timeout(20)
async def test_flow_container_layout(justify: str):
    def build():
        return rio.FlowContainer(
            rio.Text("foo", width=5),
            rio.Text("bar", width=10),
            rio.Text("qux", width=4),
            column_spacing=3,
            row_spacing=2,
            justify=justify,  # type: ignore
            width=20,
            align_x=0,
        )

    await verify_layout(build)
