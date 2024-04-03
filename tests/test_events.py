import asyncio

from utils import create_mockapp

import rio


class ChildToggler(rio.Component):
    child: rio.Component
    switch: bool = True

    def toggle(self) -> None:
        self.switch = not self.switch

    def build(self) -> rio.Component:
        if self.switch:
            return rio.Spacer()
        else:
            return self.child


async def test_mounted():
    mounted = unmounted = False

    class DemoComponent(rio.Component):
        @rio.event.on_mount
        def _on_mount(self):
            nonlocal mounted
            mounted = True

        @rio.event.on_unmount
        def _on_unmount(self):
            nonlocal unmounted
            unmounted = True

        def build(self) -> rio.Component:
            return rio.Text("hi")

    def build():
        return ChildToggler(DemoComponent())

    async with create_mockapp(build) as app:
        root = app.get_component(ChildToggler)
        assert not mounted
        assert not unmounted

        root.toggle()
        await app.refresh()
        assert mounted
        assert not unmounted

        root.toggle()
        await app.refresh()
        assert unmounted


async def test_refresh_after_synchronous_mount_handler():
    class DemoComponent(rio.Component):
        mounted: bool = False

        @rio.event.on_mount
        def on_mount(self):
            self.mounted = True

        def build(self) -> rio.Component:
            return rio.Switch(self.mounted)

    async with create_mockapp(DemoComponent) as app:
        demo_component = app.get_component(DemoComponent)
        switch = app.get_component(rio.Switch)

        # TODO: I don't know how we can wait for the refresh, so I'll just use a
        # sleep()
        await asyncio.sleep(0.5)
        assert demo_component.mounted

        last_component_state_changes = app.last_component_state_changes
        assert switch in last_component_state_changes
        assert last_component_state_changes[switch].get("is_on") is True
