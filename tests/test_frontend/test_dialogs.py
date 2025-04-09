import asyncio
import typing as t

import pytest

import rio
from rio.testing import BrowserClient


class DialogOpener(rio.Component):
    """
    Helper class that opens a dialog on mount.
    """

    build_dialog_content: t.Callable[[], rio.Component]

    modal: bool = True

    dialog_closed: bool = False

    @rio.event.on_mount
    async def on_mount(self):
        dialog = await self.session.show_custom_dialog(
            self.build_dialog_content,
            user_closable=True,
            modal=self.modal,
        )
        await dialog.wait_for_close()

        self.dialog_closed = True

    def build(self) -> rio.Component:
        return rio.Spacer()


@pytest.mark.parametrize("modal", [True, False])
async def test_click_closes_dialog(modal: bool):
    def build():
        return DialogOpener(
            lambda: rio.Text("foo", align_x=0.5, align_y=0.5),
            modal=modal,
        )

    async with BrowserClient(build) as test_client:
        await asyncio.sleep(0.1)

        await test_client.click(100, 100)

        opener = test_client.get_component(DialogOpener)
        assert opener.dialog_closed


async def test_click_in_popup_doesnt_close_dialog():
    """
    Tests whether clicking a popup - like a dropdown - in the dialog closes the
    dialog.
    """

    def build():
        return DialogOpener(
            lambda: rio.Dropdown("123456789"),
        )

    async with BrowserClient(build) as test_client:
        await asyncio.sleep(1)

        # Click to open the dropdown. Dialogs are vertically aligned at 40%.
        center_y = test_client._window_height_in_pixels * 0.4 + 5
        await test_client.click(0.5, center_y, sleep=1)

        # Click a bit below to select an option from the dropdown
        await test_client.click(0.5, center_y + 50)

        opener = test_client.get_component(DialogOpener)
        assert not opener.dialog_closed


async def test_esc_closes_dialog():
    def build():
        return DialogOpener(
            lambda: rio.Text("foo", align_x=0.5, align_y=0.5),
        )

    async with BrowserClient(build) as test_client:
        await asyncio.sleep(0.1)

        await test_client.playwright_page.keyboard.press("Escape")
        await asyncio.sleep(0.1)

        opener = test_client.get_component(DialogOpener)
        assert opener.dialog_closed
