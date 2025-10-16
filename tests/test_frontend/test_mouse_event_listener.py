import rio
from rio.testing import BrowserClient


async def test_specific_button_events() -> None:
    down_events: list[rio.MouseDownEvent] = []
    up_events: list[rio.MouseUpEvent] = []

    def on_mouse_down(e: rio.MouseDownEvent):
        down_events.append(e)

    def on_mouse_up(e: rio.MouseUpEvent):
        up_events.append(e)

    def build():
        return rio.MouseEventListener(
            rio.MouseEventListener(
                rio.Spacer(),
                on_mouse_down=on_mouse_down,
                on_mouse_up=on_mouse_up,
            ),
            on_mouse_down=on_mouse_down,
            on_mouse_up=on_mouse_up,
        )

    async with BrowserClient(build) as client:
        await client.click(0.5, 0.5, sleep=0.5)

    # MouseEventListener uses normal event bubbling (no capture/consume)
    assert len(down_events) == 2  # Both listeners receive the event
    assert len(up_events) == 2  # Both listeners receive the event
