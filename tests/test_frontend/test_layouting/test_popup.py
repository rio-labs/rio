import asyncio

import rio
from tests.utils.layouting import BrowserClient


async def test_popup_moves_with_anchor():
    def build():
        return rio.Column(
            rio.Webview('<div id="expander"></div>'),
            rio.Popup(
                anchor=rio.Text("anchor", min_width=10, min_height=10),
                content=rio.Text("content"),
                position="center",
                is_open=True,
            ),
        )

    async def get_content_y_coordinate():
        return await client.execute_js("""
            document.querySelector('.rio-popup-content').getBoundingClientRect().top;
        """)

    async with BrowserClient(build) as client:
        y1 = await get_content_y_coordinate()

        # Move the anchor down by making the element above it taller
        await client.execute_js(
            "document.querySelector('#expander').style.height = '100px';"
        )
        await asyncio.sleep(0.5)

        # Check if the popup moved down
        y2 = await get_content_y_coordinate()

        assert y2 > y1
