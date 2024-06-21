from collections.abc import Callable

import pytest

import rio.testing
from tests.utils.headless_client import HeadlessClient


def row_with_extra_width():
    return rio.Row(
        rio.Text("hi", width=5),
        rio.Button("clicky", width=10),
    )


@pytest.mark.parametrize(
    "window_size, build",
    [
        ((25, 3), row_with_extra_width),
    ],
)
@pytest.mark.async_timeout(60)
async def test_layout(
    window_size: tuple[float, float], build: Callable[[], rio.Component]
):
    async with HeadlessClient(window_size, build) as test_client:
        await test_client.verify_dimensions()
