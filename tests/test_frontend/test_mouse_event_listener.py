import pytest

import rio
from rio.testing import BrowserClient


@pytest.mark.parametrize("consume_events", [True, False])
@pytest.mark.parametrize("capture_events", [True, False])
async def test_specific_button_events(
    consume_events: bool, capture_events: bool
) -> None:
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
            consume_events=consume_events,
            capture_events=capture_events,
        )

    async with BrowserClient(build) as client:
        await client.click(0.5, 0.5, sleep=0.5)

    assert len(down_events) == 1 + (not capture_events or not consume_events)
    assert len(up_events) == 1 + (not capture_events or not consume_events)
