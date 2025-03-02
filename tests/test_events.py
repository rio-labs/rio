import asyncio
import typing as t

import rio.testing
from rio.components import Component


class ChildMounter(rio.Component):
    child: rio.Component
    child_mounted: bool = False

    def toggle(self) -> None:
        self.child_mounted = not self.child_mounted

    def build(self) -> rio.Component:
        if self.child_mounted:
            return self.child
        else:
            return rio.Spacer()


class EventCounter(rio.Component):
    child: rio.Component

    # Rio mustn't interpret these as state, otherwise it will cause unexpected
    # rebuilds.
    if t.TYPE_CHECKING:
        mount_count: int = 0
        unmount_count: int = 0

    def __post_init__(self):
        self.mount_count = 0
        self.unmount_count = 0

    @rio.event.on_mount
    def _on_mount(self):
        self.mount_count += 1

    @rio.event.on_unmount
    def _on_unmount(self):
        self.unmount_count += 1

    def build(self) -> Component:
        return self.child


async def test_mounted():
    class NestedComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Text("hi")

    def build():
        return ChildMounter(EventCounter(NestedComponent()))

    async with rio.testing.TestClient(build) as test_client:
        mounter = test_client.get_component(ChildMounter)
        event_counter = t.cast(EventCounter, mounter.child)
        assert event_counter.mount_count == 0
        assert event_counter.unmount_count == 0

        mounter.toggle()
        await test_client.refresh()
        assert event_counter.mount_count == 1
        assert event_counter.unmount_count == 0

        # Make sure the newly mounted components were sent to the client
        nested_component = test_client.get_component(NestedComponent)
        text_component = test_client.get_component(rio.Text)
        assert test_client._last_updated_components == {
            mounter,
            event_counter,
            nested_component,
            text_component,
        }

        mounter.toggle()
        await test_client.refresh()
        assert event_counter.unmount_count == 1


async def test_double_mount():
    def build():
        return ChildMounter(EventCounter(rio.Text("hello!")))

    async with rio.testing.TestClient(build) as test_client:
        mounter = test_client.get_component(ChildMounter)
        event_counter = t.cast(EventCounter, mounter.child)

        for _ in range(4):
            mounter.toggle()
            await test_client.refresh()

            if mounter.child_mounted:
                assert event_counter in test_client._last_updated_components

        assert event_counter.mount_count == 2
        assert event_counter.unmount_count == 2


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

        assert demo_component.mounted

        last_component_state_changes = test_client._last_component_state_changes
        assert switch in last_component_state_changes
        assert last_component_state_changes[switch].get("is_on") is True


async def test_periodic():
    ticks = 0

    class DemoComponent(rio.Component):
        @rio.event.periodic(0.05)
        def tick(self):
            nonlocal ticks
            ticks += 1

        def build(self) -> rio.Component:
            return rio.Spacer()

    async with rio.testing.TestClient(DemoComponent) as test_client:
        ticks_before = ticks
        await asyncio.sleep(0.1)
        ticks_after = ticks
        assert ticks_after > ticks_before

        await test_client._simulate_interrupted_connection()

        ticks_before = ticks
        await asyncio.sleep(0.1)
        ticks_after = ticks
        assert ticks_after == ticks_before

        await test_client._simulate_reconnect()

        ticks_before = ticks
        await asyncio.sleep(0.1)
        ticks_after = ticks
        assert ticks_after > ticks_before
