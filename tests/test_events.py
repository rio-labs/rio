import asyncio

import rio.testing


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

    async with rio.testing.TestClient(build) as test_client:
        root = test_client.get_component(ChildToggler)
        assert not mounted
        assert not unmounted

        root.toggle()
        await test_client.refresh()
        assert mounted
        assert not unmounted

        root.toggle()
        await test_client.refresh()
        assert unmounted


async def test_refresh_after_synchronous_mount_handler():
    class DemoComponent(rio.Component):
        mounted: bool = False

        @rio.event.on_mount
        def on_mount(self):
            self.mounted = True

        def build(self) -> rio.Component:
            return rio.Switch(self.mounted)

    async with rio.testing.TestClient(DemoComponent) as test_client:
        demo_component = test_client.get_component(DemoComponent)
        switch = test_client.get_component(rio.Switch)

        # TODO: I don't know how we can wait for the refresh, so I'll just use a
        # sleep()
        await asyncio.sleep(0.5)
        assert demo_component.mounted

        last_component_state_changes = test_client._last_component_state_changes
        assert switch in last_component_state_changes
        assert last_component_state_changes[switch].get("is_on") is True
