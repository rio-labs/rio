import typing as t

import pytest

import rio.testing


async def test_reconciliation():
    class Toggler(rio.Component):
        toggle: bool = True

        def build(self) -> rio.Component:
            if self.toggle:
                return rio.TextInput("hi", min_width=10, min_height=10)
            else:
                return rio.TextInput(min_height=15, is_secret=True)

    async with rio.testing.DummyClient(Toggler) as test_client:
        toggler = test_client.get_component(Toggler)
        text_input = test_client.get_component(rio.TextInput)

        text_input.text = "bye"
        text_input.min_height = 5

        toggler.toggle = False
        await test_client.wait_for_refresh()

        # The text should carry over because it was assigned after the component
        # was created, which essentially means that the user interactively
        # changed it
        assert text_input.text == "bye"

        # The height that was explicitly passed into the constructor of the new
        # component should win out over the late assignment
        assert text_input.min_height == 15

        # The min_width and is_secret should be taken from the new component
        assert text_input.min_width == 0
        assert text_input.is_secret

        # If we toggle again, make sure the `is_secret` is back to its default
        # value. (Not really sure how this is different from the `min_width`,
        # but there was once a bug like this)
        toggler.toggle = True
        await test_client.wait_for_refresh()

        assert not text_input.is_secret


async def test_reconcile_instance_with_itself() -> None:
    # There used to be a bug where, when a component was reconciled with itself,
    # it was removed from `Session._dirty_components`. So any changes in that
    # component weren't sent to the frontend.

    class Container(rio.Component):
        child: rio.Component

        def build(self) -> rio.Component:
            return self.child

    def build() -> rio.Component:
        return Container(rio.Text("foo"))

    async with rio.testing.DummyClient(build) as test_client:
        container = test_client.get_component(Container)
        child = test_client.get_component(rio.Text)

        # Change the child's state and make its parent rebuild
        child.text = "bar"
        container.child = child

        # In order for the bug to occur, the parent has to be rebuilt before the
        # child
        assert test_client._session is not None
        assert test_client._dirty_components == {child, container}
        await test_client.wait_for_refresh()

        assert test_client._last_updated_components == {child, container}


async def test_reconcile_same_component_instance():
    # TODO: How is this different from the test above?

    def build():
        return rio.Container(rio.Text("Hello"))

    async with rio.testing.DummyClient(build) as test_client:
        test_client._received_messages.clear()

        root_component = test_client.get_component(rio.Container)
        await root_component._force_refresh_()

        # Nothing changed, so there's no need to send any data to JS. But in
        # order to know that nothing changed, the framework would have to track
        # every individual attribute of every component. Since we forced the
        # root_component to refresh, it's reasonable to send that component's
        # data to JS.
        assert (
            not test_client._received_messages
            or test_client._last_updated_components == {root_component}
        )


async def test_reconcile_unusual_types():
    class Container(rio.Component):
        def build(self) -> rio.Component:
            return CustomComponent(
                integer=4,
                text="bar",
                tuple=(2.0, rio.Text("baz")),
                byte_array=bytearray(b"foo"),
            )

    class CustomComponent(rio.Component):
        integer: int
        text: str
        tuple: tuple[float, rio.Component]
        byte_array: bytearray

        def build(self):
            return rio.Text(self.text)

    async with rio.testing.DummyClient(Container) as test_client:
        root_component = test_client.get_component(Container)

        # As long as this doesn't crash, it's fine
        await root_component._force_refresh_()


async def test_reconcile_by_key():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Text("Hello", key="foo")
            else:
                return rio.Container(rio.Text("World", key="foo"))

    async with rio.testing.DummyClient(Toggler) as test_client:
        root_component = test_client.get_component(Toggler)
        text = test_client.get_component(rio.Text)

        root_component.toggle = True
        await test_client.wait_for_refresh()

        assert text.text == "World"


async def test_key_prevents_structural_match():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Text("Hello")
            else:
                return rio.Text("World", key="foo")

    async with rio.testing.DummyClient(Toggler) as test_client:
        root_component = test_client.get_component(Toggler)
        text = test_client.get_component(rio.Text)

        root_component.toggle = True
        await test_client.wait_for_refresh()

        assert text.text == "Hello"


async def test_key_interrupts_structure():
    class Toggler(rio.Component):
        key_: str = "abc"

        def build(self):
            return rio.Container(rio.Text(self.key_), key=self.key_)

    async with rio.testing.DummyClient(Toggler) as test_client:
        root_component = test_client.get_component(Toggler)
        text = test_client.get_component(rio.Text)

        root_component.key_ = "123"
        await test_client.wait_for_refresh()

        # The container's key changed, so even though the structure is the same,
        # the old Text component should be unchanged.
        assert text.text == "abc"


async def test_structural_matching_inside_keyed_component():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Row(rio.Container(rio.Text("A"), key="foo"))
            else:
                return rio.Row(
                    rio.Container(rio.Text("B")),
                    rio.Container(rio.Text("C"), key="foo"),
                )

    async with rio.testing.DummyClient(Toggler) as test_client:
        root_component = test_client.get_component(Toggler)
        text = test_client.get_component(rio.Text)

        root_component.toggle = True
        await test_client.wait_for_refresh()

        # The container with key "foo" has moved. Make sure the structure inside
        # of it was reconciled correctly.
        assert text.text == "C"


async def test_key_matching_inside_keyed_component():
    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Container(
                    rio.Row(
                        rio.Container(rio.Text("A"), key="container"),
                        key="row",
                    ),
                )
            else:
                return rio.Row(
                    rio.Text("B"),
                    rio.Container(rio.Text("C"), key="container"),
                    key="row",
                )

    async with rio.testing.DummyClient(Toggler) as test_client:
        root_component = test_client.get_component(Toggler)
        text = test_client.get_component(rio.Text)

        root_component.toggle = True
        await test_client.wait_for_refresh()

        # The container with key "foo" has moved. Make sure the structure inside
        # of it was reconciled correctly.
        assert text.text == "C"


async def test_same_key_on_different_component_type():
    class ComponentWithText(rio.Component):
        text: str

        def build(self) -> rio.Component:
            return rio.Text(self.text)

    class Toggler(rio.Component):
        toggle: bool = False

        def build(self):
            if not self.toggle:
                return rio.Text("Hello", key="foo")
            else:
                return ComponentWithText("World", key="foo")

    async with rio.testing.DummyClient(Toggler) as test_client:
        root_component = test_client.get_component(Toggler)
        text = test_client.get_component(rio.Text)

        root_component.toggle = True
        await test_client.wait_for_refresh()

        assert text.text == "Hello"


async def test_child_containing_attribute_recognition():
    class CompWithChildren(rio.Component):
        content: str | t.Annotated[rio.Component, "foobar"]
        children: t.MutableSequence[rio.Component]

        def build(self) -> rio.Component:
            content = self.content
            if isinstance(content, str):
                content = rio.Text(content)

            return rio.Column(
                content,
                rio.Row(*self.children),
            )

    class RootComponent(rio.Component):
        state: bool = False

        def build(self) -> rio.Component:
            return CompWithChildren(
                content=rio.Switch(self.state),
                children=[rio.Text(str(self.state))],
            )

    async with rio.testing.DummyClient(RootComponent) as client:
        root_component = client.get_component(RootComponent)
        comp_with_children = client.get_component(CompWithChildren)
        content_switch = client.get_component(rio.Switch)
        children_text = client.get_component(rio.Text)

        root_component.state = True
        await client.wait_for_refresh()

        assert comp_with_children.content is content_switch
        assert content_switch.is_on

        assert comp_with_children.children[0] is children_text
        assert children_text.text == "True"


async def test_text_reconciliation():
    class RootComponent(rio.Component):
        text: str = "foo"

        def build(self) -> rio.Component:
            return rio.Text(self.text)

    async with rio.testing.DummyClient(RootComponent) as test_client:
        root = test_client.get_component(RootComponent)
        text = test_client.get_component(rio.Text)

        root.text = "bar"
        await test_client.wait_for_refresh()

        assert text.text == root.text


async def test_grid_reconciliation():
    class RootComponent(rio.Component):
        num_rows: int = 1

        def build(self) -> rio.Component:
            rows = [[rio.Text(f"Row {n}")] for n in range(self.num_rows)]
            return rio.Grid(*rows)

    async with rio.testing.DummyClient(RootComponent) as test_client:
        root = test_client.get_component(RootComponent)
        grid = test_client.get_component(rio.Grid)

        root.num_rows += 1
        await test_client.wait_for_refresh()

        assert {root, grid} < test_client._last_updated_components
        assert len(grid._children) == root.num_rows


async def test_margin_reconciliation():
    class RootComponent(rio.Component):
        switch: bool = True

        def build(self) -> rio.Component:
            if self.switch:
                return rio.Column(*[rio.Text("hi") for _ in range(7)])
            else:
                return rio.Column(
                    rio.Text("hi", margin_left=1),
                    rio.Text("hi", margin_right=1),
                    rio.Text("hi", margin_top=1),
                    rio.Text("hi", margin_bottom=1),
                    rio.Text("hi", margin_x=1),
                    rio.Text("hi", margin_y=1),
                    rio.Text("hi", margin=1),
                )

    async with rio.testing.DummyClient(RootComponent) as test_client:
        root = test_client.get_component(RootComponent)
        texts = list(test_client.get_components(rio.Text))

        root.switch = False
        await test_client.wait_for_refresh()

        assert texts[0].margin_left == 1
        assert texts[1].margin_right == 1
        assert texts[2].margin_top == 1
        assert texts[3].margin_bottom == 1

        assert texts[4].margin_x == 1
        assert texts[4].margin_left == texts[4].margin_right == None

        assert texts[5].margin_y == 1
        assert texts[5].margin_top == texts[5].margin_bottom == None

        assert texts[6].margin == 1
        assert (
            texts[6].margin_left
            == texts[6].margin_right
            == texts[6].margin_top
            == texts[6].margin_bottom
            == None
        )


@pytest.mark.skip("Not implemented yet. Has some downsides.")
async def test_only_newly_instantiated_components_are_reconciled():
    class RootComponent(rio.Component):
        child: rio.Component
        switch: bool = True

        def build(self) -> rio.Component:
            if self.switch:
                return rio.Column(
                    rio.Text("foo"),
                    rio.Text("bar"),
                    self.child,
                )
            else:
                return rio.Column(
                    rio.Text("1"),
                    self.child,
                    rio.Text("3"),
                )

    def build():
        return RootComponent(rio.Text("qux"))

    async with rio.testing.DummyClient(build) as test_client:
        root = test_client.get_component(RootComponent)
        text1, text2, text3 = test_client.get_components(rio.Text)

        root.switch = False
        await test_client.wait_for_refresh()

        # The first Text should've been reconciled and thus have new text
        assert text1.text == "1"

        # The 2nd Text was replaced by a component that the RootComponent
        # hasn't instantiated, so it shouldn't have been reconciled and should
        # now be dead
        assert text2.text == "bar"
        assert text2 not in test_client._last_updated_components

        # The 3rd Text wasn't instantiated by the RootComponent, so its text
        # should have remained unchanged
        assert text3.text == "qux"
