from collections.abc import Callable

import pytest

import rio.testing
from tests.utils.headless_client import HeadlessClient


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


@pytest.mark.parametrize(
    "build",
    [
        row_with_no_extra_width,
        row_with_extra_width_and_no_growers,
        row_with_extra_width_and_one_grower,
    ],
)
@pytest.mark.async_timeout(20)
async def test_layout(build: Callable[[], rio.Component]):
    async with HeadlessClient(build) as test_client:
        await test_client.verify_dimensions()
