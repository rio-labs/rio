import asyncio

import rio
from tests.utils.layouting import BrowserClient


async def test_dropdowns_work_in_dev_tools() -> None:
    # Dropdowns (and other popups) have often been broken in the dev tools, due
    # to z-index issues and other reasons. This test makes sure that they work.

    async with BrowserClient(rio.Spacer, debug_mode=True) as client:
        # Open the "Icons" tab in the sidebar. Look it up by name, since the
        # order of the tabs changes when tabs are added or removed.
        await client.execute_js("""
            Array.from(document.querySelectorAll(".rio-switcher-bar-option"))
                .find((elem) => elem.textContent === "Icons")
                .click()
        """)
        await asyncio.sleep(0.5)

        # Click an arbitrary icon in the list
        await client.execute_js(
            "document.querySelector('.rio-switcher .rio-icon').click()"
        )
        await asyncio.sleep(0.5)

        # Open the dropdown
        await client.execute_js(
            "document.querySelector('.rio-dropdown input').focus()"
        )
        await asyncio.sleep(0.5)

        # Make sure the dropdown list is open and visible
        is_entirely_visible = await client.execute_js("""
            new Promise((resolve) => {
                let elem = document.querySelector(".rio-dropdown-options");
                
                let observer = new IntersectionObserver((entries) => {
                    resolve(entries[0].intersectionRatio === 1);
                });
                observer.observe(elem);
            });
        """)
        assert is_entirely_visible
