import rio.testing


async def test_switcher_bar_doesnt_rebuild_unnecessarily():
    class MyComponent(rio.Component):
        state: int = 0

        def build(self) -> rio.Component:
            # Rebuilding creates a "new" `SwitcherBar` with new
            # `SwitcherBarItem`s. But the contents are the same, so it shouldn't
            # rebuild.
            return rio.Column(
                rio.Text(f"{self.state}"),
                rio.SwitcherBar(
                    rio.SwitcherBarItem("hello"),
                    rio.SwitcherBarItem("world"),
                ),
            )

    async with rio.testing.DummyClient(MyComponent) as client:
        my_component = client.get_component(MyComponent)
        text = client.get_component(rio.Text)
        switcher_bar = client.get_component(rio.SwitcherBar)

        my_component.state = 1
        await client.wait_for_refresh()

        assert text in client._last_updated_components
        assert switcher_bar not in client._last_updated_components


async def test_switcher_bar_item_change():
    class MyComponent(rio.Component):
        item_title: str = "hello"

        def build(self) -> rio.Component:
            return rio.SwitcherBar(
                rio.SwitcherBarItem(self.item_title),
                rio.SwitcherBarItem("world"),
            )

    async with rio.testing.DummyClient(MyComponent) as client:
        my_component = client.get_component(MyComponent)
        switcher_bar = client.get_component(rio.SwitcherBar)

        my_component.item_title = "bye"
        await client.wait_for_refresh()

        items = client._last_component_state_changes[switcher_bar]["items"]
        assert items[0]["name"] == "bye"  # type: ignore
