from utils import create_mockapp

import rio


async def test_refresh_with_nothing_to_do():
    def build():
        return rio.Text("Hello")

    async with create_mockapp(build) as app:
        app.outgoing_messages.clear()
        await app.refresh()

        assert not app.dirty_components
        assert not app.last_updated_components


async def test_refresh_with_clean_root_component():
    def build():
        text_component = rio.Text("Hello")
        return rio.Container(text_component)

    async with create_mockapp(build) as app:
        text_component = app.get_component(rio.Text)

        text_component.text = "World"
        await app.refresh()

        assert app.last_updated_components == {text_component}


async def test_rebuild_component_with_dead_parent():
    class RootComponent(rio.Component):
        content: rio.Component

        def build(self) -> rio.Component:
            return self.content

    class ComponentWithState(rio.Component):
        state: str

        def build(self) -> rio.Component:
            return rio.Text(self.state)

    def build() -> rio.Component:
        return RootComponent(
            rio.Row(
                ComponentWithState("Hello"),
                rio.ProgressCircle(),
            )
        )

    async with create_mockapp(build) as app:
        # Change the component's state, but also remove its parent from the
        # component tree
        root_component = app.get_component(RootComponent)
        component = app.get_component(ComponentWithState)
        progress_component = app.get_component(rio.ProgressCircle)

        component.state = "Hi"
        root_component.content = progress_component

        await app.refresh()

        # Make sure no data for dead components was sent to JS
        assert app.last_updated_components == {root_component}


async def test_unmount_and_remount():
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

    async with create_mockapp(build) as app:
        root_component = app.get_component(DemoComponent)
        child_component = root_component.content
        row_component = app.get_component(rio.Row)

        root_component.show_child = False
        await app.refresh()
        assert app.last_updated_components == {root_component, row_component}

        root_component.show_child = True
        await app.refresh()
        assert app.last_updated_components == {
            root_component,
            row_component,
            child_component,
        }
