import asyncio

import rio.testing


async def test_change_selection_mode() -> None:
    num_presses = 0

    def on_press():
        nonlocal num_presses
        num_presses += 1

    async with rio.testing.BrowserClient(
        lambda: rio.ListView(
            rio.SimpleListItem("Item", key="item0", on_press=on_press),
            selection_mode="single",
        )
    ) as test_client:
        list_view = test_client.get_component(rio.ListView)
        item = test_client.get_component(rio.SimpleListItem)

        assert num_presses == 0

        await asyncio.sleep(0.5)
        await test_client.click(10, 1)
        await asyncio.sleep(0.5)

        assert num_presses == 1
        assert list_view.selected_items == [item.key]

        list_view.selection_mode = "none"
        list_view.selected_items = []
        item.on_press = None
        await test_client.wait_for_refresh()

        await test_client.click(10, 1)
        assert num_presses == 1
        assert list_view.selected_items == []

        list_view.selection_mode = "single"
        item.on_press = on_press
        await test_client.wait_for_refresh()

        await test_client.click(10, 1)
        assert num_presses == 2
        assert list_view.selected_items == [item.key]
