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


@pytest.mark.parametrize(
    "event_buttons",
    [
        ["left"],
        ["middle"],
        ["right"],
        ["left", "right"],
        ["middle", "right"],
    ],
    ids=lambda buttons: "/".join(buttons),
)
@pytest.mark.parametrize("pressed_button", ["left", "middle", "right"])
async def test_specific_button_events(
    event_buttons: t.Sequence[t.Literal["left", "middle", "right"]],
    pressed_button: t.Literal["left", "middle", "right"],
) -> None:
    down_event: rio.PointerEvent | None = None
    up_event: rio.PointerEvent | None = None

    def on_pointer_down(e: rio.PointerEvent):
        nonlocal down_event
        down_event = e

    def on_pointer_up(e: rio.PointerEvent):
        nonlocal up_event
        up_event = e

    def build():
        return rio.PointerEventListener(
            rio.Spacer(),
            on_pointer_down={
                button: on_pointer_down for button in event_buttons
            },
            on_pointer_up={button: on_pointer_up for button in event_buttons},
        )

    async with BrowserClient(build) as client:
        await client.click(0.5, 0.5, button=pressed_button, sleep=0.5)

    if pressed_button in event_buttons:
        assert down_event is not None
        assert up_event is not None
    else:
        assert down_event is None
        assert up_event is None
