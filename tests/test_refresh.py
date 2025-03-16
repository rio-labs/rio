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
        assert not child_component._is_in_component_tree_({})
        assert test_client._last_updated_components == {
            root_component,
            row_component,
        }

        root_component.show_child = True
        await test_client.refresh()
        assert child_component._is_in_component_tree_({})
        assert test_client._last_updated_components == {
            root_component,
            row_component,
            child_component,
        }


async def test_rebuild_component_with_dead_builder():
    class ChildToggler(rio.Component):
        child_is_alive: bool = True

        def build(self) -> rio.Component:
            if self.child_is_alive:
                return Builder(StatefulComponent("hello"))
            else:
                return rio.Spacer()

    class Builder(rio.Component):
        child: rio.Component

        def build(self) -> rio.Component:
            return self.child

    class StatefulComponent(rio.Component):
        state: str = "hi"

        def build(self) -> rio.Component:
            return rio.Text(self.state)

    async with rio.testing.TestClient(ChildToggler) as test_client:
        toggler = test_client.get_component(ChildToggler)
        stateful_component = test_client.get_component(StatefulComponent)

        toggler.child_is_alive = False
        await test_client.refresh()

        # At this point in time, the builder is dead
        assert stateful_component._weak_builder_() is None

        stateful_component.state = "bye"

        test_client._outgoing_messages.clear()
        await test_client.refresh()
        assert not test_client._outgoing_messages


async def test_changing_children_of_not_dirty_high_level_component():
    # Situation:
    # HighLevelComponent1 contains HighLevelComponent2
    # HighLevelComponent2 contains LowLevelContainer
    # HighLevelComponent1 is rebuilt and changes the child of LowLevelContainer
    # -> LowLevelContainer is reconciled and dirty (because it has new children)
    # -> HighLevelComponent2 is reconciled but *not* dirty because its child was
    # reconciled
    # The end result is that there is a new component (the child of
    # LowLevelContainer), whose builder (HighLevelComponent2) is not "dirty".
    # Make sure the new component is initialized correctly despite this.
    class HighLevelComponent1(rio.Component):
        switch: bool = False

        def build(self) -> rio.Component:
            if self.switch:
                child = rio.Switch()
            else:
                child = rio.Text("hi")

            assert issubclass(
                rio.Column,
                rio.components.fundamental_component.FundamentalComponent,
            )
            return HighLevelComponent2(rio.Column(child))

    class HighLevelComponent2(rio.Component):
        content: rio.Component

        def build(self) -> rio.Component:
            return self.content

    async with rio.testing.TestClient(HighLevelComponent1) as test_client:
        root_component = test_client.get_component(HighLevelComponent1)
        text_component = test_client.get_component(rio.Text)

        root_component.switch = True
        await test_client.refresh()

        # Check if the new child, a Switch, was sent to the frontend
        assert any(
            isinstance(component, rio.Switch)
            for component in test_client._last_updated_components
        ), "No rio.Switch was sent to the frontend"

        # Check if the old child, a Text, is dead
        assert not text_component._is_in_component_tree_({}), (
            "rio.Text is still in the component tree"
        )


async def test_binding_doesnt_update_children() -> None:
    class ComponentWithBinding(rio.Component):
        text: str = ""

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Markdown("# Heading"),
                rio.TextInput(self.bind().text),
                rio.Text(self.text),
            )

    async with rio.testing.TestClient(ComponentWithBinding) as test_client:
        text_input = test_client.get_component(rio.TextInput)
        text = test_client.get_component(rio.Text)

        # Note: `text_input._on_message_` automatically triggers a refresh
        test_client._outgoing_messages.clear()
        await text_input._on_message_({"type": "confirm", "text": "hello"})

        # Only the Text component has changed in this rebuild
        assert test_client._last_updated_components == {text}
