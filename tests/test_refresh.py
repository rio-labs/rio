import rio.testing


async def test_refresh_with_nothing_to_do() -> None:
    def build() -> rio.Component:
        return rio.Text("Hello")

    async with rio.testing.TestClient(build) as test_client:
        test_client._outgoing_messages.clear()
        await test_client.refresh()

        assert not test_client._dirty_components
        assert not test_client._last_updated_components


async def test_refresh_with_clean_root_component() -> None:
    def build() -> rio.Component:
        text_component = rio.Text("Hello")
        return rio.Container(text_component)

    async with rio.testing.TestClient(build) as test_client:
        text_component = test_client.get_component(rio.Text)

        text_component.text = "World"
        await test_client.refresh()

        assert test_client._last_updated_components == {text_component}


async def test_rebuild_component_with_dead_parent() -> None:
    class ChildUnmounter(rio.Component):
        child: rio.Component
        child_is_mounted: bool = True

        def build(self) -> rio.Component:
            if self.child_is_mounted:
                return self.child
            else:
                return rio.Spacer()

    class ComponentWithState(rio.Component):
        state: str

        def build(self) -> rio.Component:
            return rio.Text(self.state)

    def build() -> rio.Component:
        return ChildUnmounter(ComponentWithState("Hello"))

    async with rio.testing.TestClient(
        build, use_ordered_dirty_set=True
    ) as test_client:
        # Change the component's state, but also remove it from the component
        # tree
        unmounter = test_client.get_component(ChildUnmounter)
        component = test_client.get_component(ComponentWithState)

        component.state = "Hi"
        unmounter.child_is_mounted = False

        await test_client.refresh()

        # Make sure no data for dead components was sent to JS
        assert unmounter in test_client._last_updated_components
        assert component not in test_client._last_updated_components


async def test_unmount_and_remount() -> None:
    class DemoComponent(rio.Component):
        content: rio.Component
        show_child: bool

        def build(self) -> rio.Component:
            children = [self.content] if self.show_child else []
            return rio.Row(*children)

    def build() -> rio.Component:
        return DemoComponent(
            rio.Text("hi"),
            show_child=True,
        )

    async with rio.testing.TestClient(build) as test_client:
        root_component = test_client.get_component(DemoComponent)
        child_component = root_component.content
        row_component = test_client.get_component(rio.Row)

        root_component.show_child = False
        await test_client.refresh()
        assert test_client._last_updated_components == {
            root_component,
            row_component,
        }

        root_component.show_child = True
        await test_client.refresh()
        assert test_client._last_updated_components == {
            root_component,
            row_component,
            child_component,
        }
