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

    async with rio.testing.DummyClient(build) as test_client:
        mounter = test_client.get_component(ChildMounter)
        event_counter = t.cast(EventCounter, mounter.child)
        assert event_counter.mount_count == 0
        assert event_counter.unmount_count == 0

        mounter.toggle()
        await test_client.wait_for_refresh()
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
        await test_client.wait_for_refresh()
        assert event_counter.unmount_count == 1


async def test_double_mount():
    def build():
        return ChildMounter(EventCounter(rio.Text("hello!")))

    async with rio.testing.DummyClient(build) as test_client:
        mounter = test_client.get_component(ChildMounter)
        event_counter = t.cast(EventCounter, mounter.child)

        for _ in range(4):
            mounter.toggle()
            await test_client.wait_for_refresh()

            if mounter.child_mounted:
                assert event_counter in test_client._last_updated_components

        assert event_counter.mount_count == 2
        assert event_counter.unmount_count == 2


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

    async with rio.testing.DummyClient(build) as test_client:
        root_component = test_client.get_component(DemoComponent)
        child_component = root_component.content
        row_component = test_client.get_component(rio.Row)

        root_component.show_child = False
        await test_client.wait_for_refresh()
        assert not child_component._is_in_component_tree_({})
        assert test_client._last_updated_components == {
            root_component,
            row_component,
        }

        root_component.show_child = True
        await test_client.wait_for_refresh()
        assert child_component._is_in_component_tree_({})
        assert test_client._last_updated_components == {
            root_component,
            row_component,
            child_component,
        }


async def test_nested_unmount_and_remount():
    def build():
        return ChildMounter(
            EventCounter(
                ChildMounter(
                    EventCounter(rio.Text("hello!")),
                    child_mounted=True,
                )
            ),
            child_mounted=True,
        )

    async with rio.testing.DummyClient(build) as client:
        mounter1, mounter2 = client.get_components(ChildMounter)
        counter1, counter2 = client.get_components(EventCounter)

        assert counter1.mount_count == 1
        assert counter1.unmount_count == 0
        assert counter2.mount_count == 1
        assert counter2.unmount_count == 0

        mounter1.child_mounted = False
        await client.wait_for_refresh()

        assert counter1.unmount_count == 1
        assert counter2.unmount_count == 1

        mounter1.child_mounted = True
        await client.wait_for_refresh()

        assert counter1.mount_count == 2
        assert counter2.mount_count == 2


async def test_refresh_after_synchronous_mount_handler():
    class DemoComponent(rio.Component):
        mounted: bool = False

        @rio.event.on_mount
        def on_mount(self):
            self.mounted = True

        def build(self) -> rio.Component:
            return rio.Switch(self.mounted)

    async with rio.testing.DummyClient(DemoComponent) as test_client:
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

    async with rio.testing.DummyClient(DemoComponent) as test_client:
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


async def test_populate_dead_child():
    class DemoComponent(rio.Component):
        text: str = "alive"

        @rio.event.on_populate
        async def _on_populate(self):
            await asyncio.sleep(1)
            self.text = "dead"

        def build(self) -> rio.Component:
            return rio.Text(self.text)

    def build():
        return ChildMounter(DemoComponent())

    async with rio.testing.DummyClient(build) as test_client:
        mounter = test_client.get_component(ChildMounter)

        # Unmount the child before its `on_populate` handler makes it dirty
        mounter.child_mounted = False
        await test_client.wait_for_refresh()

        # Wait for the `on_populate` handler and the subsequent refresh
        test_client._received_messages.clear()
        await asyncio.sleep(1.5)

        # Make sure the dead component wasn't sent to the frontend
        #
        # Note: Even though we cleared the outgoing messages, it's possible that
        # some `registerFont` messages were sent afterwards. So unfortunately we
        # can't assert that no message was sent at all, but we can assert that
        # no components were updated.
        assert not test_client._last_updated_components, (
            "Unmounted component was sent to the frontend"
        )
