import rio
import rio.testing


async def test_tab_metadata_change():
    class MyTabs(rio.Component):
        tab_content: rio.Component
        tab_title: str = "hello"

        def build(self) -> rio.Component:
            return rio.Tabs(
                rio.TabItem(self.tab_title, self.tab_content),
            )

    def build():
        return MyTabs(rio.Text("world"))

    async with rio.testing.DummyClient(build) as client:
        my_tabs = client.get_component(MyTabs)
        switcher_bar = client.get_component(rio.SwitcherBar)
        assert switcher_bar.items[0].name == "hello"

        my_tabs.tab_title = "goodbye"
        await client.wait_for_refresh()

        assert switcher_bar.items[0].name == "goodbye"


async def test_tab_switch_after_state_change():
    """
    Based on a real-world bug. Switching tabs worked fine, UNLESS you interacted
    with a tab and changed the shared state, then Rio suddenly stopped sending
    the tab contents to the frontend.
    """

    class MyTabs(rio.Component):
        counter: int = 0

        def increment(self):
            self.counter += 1

        def build(self) -> rio.Component:
            return rio.Tabs(
                rio.TabItem(
                    "Tab 0",
                    rio.Column(
                        rio.Markdown(f"Counter: {self.counter}"),
                        key="column-in-tab-0",
                    ),
                ),
                rio.TabItem(
                    "Tab 1",
                    rio.Button(
                        f"Increment counter: {self.counter}",
                        on_press=self.increment,
                        key="tab1-button",
                    ),
                ),
            )

    async with rio.testing.DummyClient(MyTabs) as client:
        # 1. Start at Tab 0
        column = client.get_component(rio.Column, key="column-in-tab-0")
        markdown = client.get_component(rio.Markdown)

        # 2. Switch to Tab 1
        tabs = client.get_component(rio.Tabs)
        tabs.active_tab_index = 1
        await client.wait_for_refresh()

        # 3. Interact with Tab 1 (modifies shared state)
        button = client.get_component(rio.Button, key="tab1-button")
        await client.click_component(button)
        await client.wait_for_refresh()

        # 4. Switch back to Tab 0
        tabs.active_tab_index = 0
        await client.wait_for_refresh()

        # 5. Check if Tab 0's Column children were sent to the frontend
        # They should be in _last_updated_components because they are being
        # "re-mounted" after being removed from the DOM when we switched to Tab 1.
        updated_components = client._last_updated_components

        # Check if they were sent to the frontend in the last update
        assert column in updated_components, "Column should be sent to frontend"
        assert markdown in updated_components, (
            "Markdown should be sent to frontend"
        )
