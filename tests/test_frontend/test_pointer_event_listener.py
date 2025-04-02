import typing as t

import pytest

import rio
from rio.testing import BrowserClient


@pytest.mark.parametrize("button", ["left", "middle", "right"])
async def test_on_press_event(
    button: t.Literal["left", "middle", "right"],
) -> None:
    event: rio.PointerEvent | None = None

    def on_press(e: rio.PointerEvent):
        nonlocal event
        event = e

    def build():
        return rio.PointerEventListener(rio.Spacer(), on_press=on_press)

    async with BrowserClient(build) as client:
        await client.click(0.5, 0.5, button=button, sleep=0.5)

        if button != "left":
            assert event is None
            return

        assert event is not None
        assert event.button == "left"
        assert event.pointer_type == "mouse"


@pytest.mark.parametrize("button", ["left", "middle", "right"])
async def test_on_double_press_event(
    button: t.Literal["left", "middle", "right"],
) -> None:
    event: rio.PointerEvent | None = None

    def on_double_press(e: rio.PointerEvent):
        nonlocal event
        event = e

    def build():
        return rio.PointerEventListener(
            rio.Spacer(), on_double_press=on_double_press
        )

    async with BrowserClient(build) as client:
        await client.double_click(0.5, 0.5, button=button, sleep=0.5)

        if button != "left":
            assert event is None
            return

        assert event is not None
        assert event.button == "left"
        assert event.pointer_type == "mouse"
