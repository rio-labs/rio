import asyncio
import dataclasses
import typing as t

import pytest

import rio.testing


@pytest.mark.parametrize(
    "attr, value1, value2",
    [
        ("min_width", 0, 3),
        ("margin", 0, 1),
        ("accessibility_role", None, "main"),
    ],
)
async def test_change_builtin_attribute(
    attr: str, value1: object, value2: object
):
    """
    This tests whether changes to a builtin attribute are sent to the frontend
    (even though they don't trigger a rebuild).
    """

    class HighLevelComponent(rio.Component):
        name: str

        def build(self):
            return rio.Text(f"Hello {self.name}!")

    class Parent(rio.Component):
        attr: str
        value: t.Any

        def build(self):
            return HighLevelComponent("Max", **{self.attr: self.value})

    def build():
        return Parent(attr, value1)

    async with rio.testing.DummyClient(build) as client:
        parent = client.get_component(Parent)
        high_level_component = client.get_component(HighLevelComponent)

        parent.value = value2
        await client.wait_for_refresh()

        assert client._last_updated_components == {parent, high_level_component}


async def test_refresh_with_nothing_to_do() -> None:
    def build() -> rio.Component:
        return rio.Text("Hello")

    async with rio.testing.DummyClient(build) as test_client:
        test_client._received_messages.clear()
        await test_client.session._refresh()

        assert not test_client._dirty_components
        assert not test_client._last_updated_components


async def test_refresh_with_clean_root_component() -> None:
    def build() -> rio.Component:
        text_component = rio.Text("Hello")
        return rio.Container(text_component)

    async with rio.testing.DummyClient(build) as test_client:
        text_component = test_client.get_component(rio.Text)

        text_component.text = "World"
        await test_client.wait_for_refresh()

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

    async with rio.testing.DummyClient(build) as test_client:
        # Change the component's state, but also remove it from the component
        # tree
        unmounter = test_client.get_component(ChildUnmounter)
        component = test_client.get_component(ComponentWithState)

        component.state = "Hi"
        unmounter.child_is_mounted = False

        await test_client.wait_for_refresh()

        # Make sure no data for dead components was sent to JS
        assert unmounter in test_client._last_updated_components
        assert component not in test_client._last_updated_components


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

    async with rio.testing.DummyClient(ChildToggler) as test_client:
        toggler = test_client.get_component(ChildToggler)
        stateful_component = test_client.get_component(StatefulComponent)

        toggler.child_is_alive = False
        await test_client.wait_for_refresh()

        # At this point in time, the builder is dead
        assert stateful_component._weak_builder_() is None

        stateful_component.state = "bye"

        test_client._received_messages.clear()

        # Since a refresh isn't actually necessary, using `wait_for_refresh()`
        # could cause a deadlock. So we'll explicitly trigger a refresh instead.
        await test_client.session._refresh()

        assert not test_client._received_messages


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

    async with rio.testing.DummyClient(HighLevelComponent1) as test_client:
        root_component = test_client.get_component(HighLevelComponent1)
        text_component = test_client.get_component(rio.Text)

        root_component.switch = True
        await test_client.wait_for_refresh()

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

    async with rio.testing.DummyClient(ComponentWithBinding) as test_client:
        root_component = test_client.get_component(ComponentWithBinding)
        text_input = test_client.get_component(rio.TextInput)
        text = test_client.get_component(rio.Text)

        test_client._received_messages.clear()
        await text_input._on_message_({"type": "confirm", "text": "hello"})
        await test_client.wait_for_refresh()

        # Only the Text component has changed in this rebuild
        assert test_client._last_updated_components == {root_component, text}


async def test_add_method_doesnt_count_as_attribute_access():
    """
    When a `build()` function is called, we track which
    attributes/attachements/whatevers it reads. Some components have mutating
    methods, like `Row.add(child)`. This can create a loop where the parent
    component "accesses" the `children` attribute of the Row. This test makes
    sure that this is handled correctly and doesn't cause an infinite loop.
    """

    class Parent(rio.Component):
        def build(self) -> rio.Component:
            row = rio.Row()
            row.add(rio.Text("hi"))
            return row

    async with rio.testing.DummyClient(Parent):
        pass  # If we made it this far, then there's no infinite loop.


async def test_automatic_refresh():
    """
    Test whether Rio automatically refreshes after a state change
    """
    updated_event = asyncio.Event()

    class TestComponent(rio.Component):
        text: str = "hi"

        @rio.event.on_mount
        async def on_mount(self):
            await asyncio.sleep(0.1)

            self.text = "bye"
            test_client._received_messages.clear()
            updated_event.set()

            await asyncio.sleep(0.5)

        def build(self):
            return rio.Text(self.text)

    async with rio.testing.DummyClient(TestComponent) as test_client:
        await updated_event.wait()

        # Yield control so that Rio has a chance to refresh
        await asyncio.sleep(0)

        text_component = test_client.get_component(rio.Text)
        assert text_component in test_client._last_updated_components


async def test_value_change_from_frontend():
    """
    When the frontend changes the state of a FundamentalComponent, we don't want
    to send that same change back to the frontend. (Because it's unnecessary and
    the latency can cause issues like resetting the text in TextInput to an
    earlier state.) However, other components that depend on that state (via an
    attribute binding, for example) do need to be updated.
    """

    class Parent(rio.Component):
        text_but_with_a_different_name: str = ""

        def build(self) -> rio.Component:
            return rio.Column(
                rio.TextInput(self.bind().text_but_with_a_different_name),
                rio.Text(self.text_but_with_a_different_name),
            )

    async with rio.testing.DummyClient(Parent) as test_client:
        parent_component = test_client.get_component(Parent)
        text_input = test_client.get_component(rio.TextInput)
        text_component = test_client.get_component(rio.Text)

        test_client._received_messages.clear()
        await text_input._on_message_(
            {
                "type": "confirm",
                "text": "hello",
            }
        )
        await test_client.wait_for_refresh()

        assert test_client._last_updated_components == {
            parent_component,
            text_component,
        }


async def test_force_refresh():
    # Use inheritance to ensure that attributes of parent classes are also
    # marked as changed
    class ParentClass(rio.Component):
        # Use a type that can't be automatically serialized. This is because
        # `force_refresh()` has to mark all attributes as changed in order to
        # guarantee a rebuild. If it's stupid and uses the serialization
        # framework to find out what attributes this class has, we want the test
        # to fail.
        items: list[str | rio.testing.DummyClient] = []

        def build(self) -> rio.Component:
            return rio.Text(" ".join(map(str, self.items)))

    class TestComponent(ParentClass):
        pass

    async with rio.testing.DummyClient(TestComponent) as client:
        component = client.get_component(TestComponent)
        text_component = client.get_component(rio.Text)

        component.items.append("foo")
        component.force_refresh()
        await client.wait_for_refresh()

        assert text_component.text == "foo"


async def test_duplicate_key():
    """
    Once upon a time, there was a bug where duplicate keys caused the component
    to be rebuilt infinitely.
    """

    class TestComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Column(
                rio.Text("hi", key=1),
                rio.Text("hi", key=1),
            )

    async with rio.testing.DummyClient(TestComponent):
        pass


async def test_dead_children_arent_rebuilt(monkeypatch: pytest.MonkeyPatch):
    @dataclasses.dataclass
    class UserInfo:
        name: str

    class ProfilePage(rio.Component):
        def build(self) -> rio.Component:
            try:
                _ = self.session[UserInfo]
            except KeyError:
                return rio.Text("You are not logged in")

            return UserInfoComponent()

    class UserInfoComponent(rio.Component):
        def build(self) -> rio.Component:
            user_info = self.session[UserInfo]
            return rio.Text(f"You are logged in as {user_info.name}")

    async with rio.testing.DummyClient(ProfilePage) as client:
        client.session.attach(UserInfo("John Doe"))
        await client.wait_for_refresh()

        profile_page = client.get_component(ProfilePage)
        user_info_component = client.get_component(UserInfoComponent)

        def collect_components_to_build(_):
            monkeypatch.undo()
            return [user_info_component, profile_page]

        monkeypatch.setattr(
            rio.Session,
            "_collect_components_to_build",
            collect_components_to_build,
        )

        client.session.detach(UserInfo)
        await client.wait_for_refresh()

        assert not client.crashed_build_functions
        assert user_info_component not in client._last_updated_components
