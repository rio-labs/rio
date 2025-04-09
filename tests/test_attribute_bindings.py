import typing as t

import rio.testing
from rio.observables.observable_property import PendingAttributeBinding


class Parent(rio.Component):
    text: str = ""

    def build(self) -> rio.Component:
        return rio.Text(self.bind().text)


class Grandparent(rio.Component):
    text: str = ""

    def build(self) -> rio.Component:
        return Parent(self.bind().text)


async def test_bindings_arent_created_too_early() -> None:
    # There was a time when attribute bindings were created in
    # `Component.__init__`, thus skipping any properties that were only assigned
    # later.
    class IHaveACustomInit(rio.Component):
        text: str

        def __init__(self, *args, text: str, **kwargs) -> None:
            super().__init__(*args, **kwargs)

            # `Component.__init__`` has already run, but we haven't assigned
            # `self.text` yet. Do it now and assert that it still becomes a
            # attribute binding.
            self.text = text

        def build(self) -> rio.Component:
            return rio.Text(self.text)

    class Container(rio.Component):
        text: str = "hi"

        def build(self) -> rio.Component:
            return IHaveACustomInit(text=self.bind().text)

    async with rio.testing.DummyClient(Container) as test_client:
        root_component = test_client.get_component(Container)
        child_component = test_client.get_component(IHaveACustomInit)

        assert child_component.text == "hi"

        root_component.text = "bye"
        assert child_component.text == "bye"


async def test_init_receives_attribute_bindings_as_input() -> None:
    # For a while we considered initializing attribute bindings before calling a
    # component's `__init__` and passing the values of the bindings as arguments
    # into `__init__`. But ultimately we decided against it, because some
    # components may want to use state properties/bindings in their __init__. So
    # make sure the `__init__` actually receives a
    # `PleaseTurnThisIntoAStateBinding` object as input.
    size_value = None

    class Square(rio.Component):
        def __init__(self, size: float) -> None:
            nonlocal size_value
            size_value = size

            super().__init__(min_width=size, min_height=size)

        def build(self) -> rio.Component:
            return rio.Text(
                "hi", min_width=self.min_width, min_height=self.min_height
            )

    class Container(rio.Component):
        size: float

        def build(self) -> rio.Component:
            return Square(self.bind().size)

    async with rio.testing.DummyClient(lambda: Container(7)):
        assert isinstance(size_value, PendingAttributeBinding)


async def test_binding_assignment_on_child() -> None:
    async with rio.testing.DummyClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component = test_client.get_component(rio.Text)

        assert not test_client._dirty_components

        text_component.text = "Hello"

        # Note: The Parent isn't dirty because its `build` never accesses
        # `self.text`. It only uses `text` as an attribute binding.
        assert test_client._dirty_components == {text_component}
        assert text_component.text == "Hello"
        assert root_component.text == "Hello"


async def test_binding_assignment_on_parent() -> None:
    async with rio.testing.DummyClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component = test_client.get_component(rio.Text)

        assert not test_client._dirty_components

        root_component.text = "Hello"

        # Note: The Parent isn't dirty because its `build` never accesses
        # `self.text`. It only uses `text` as an attribute binding.
        assert test_client._dirty_components == {text_component}
        assert text_component.text == "Hello"
        assert root_component.text == "Hello"


async def test_using_binding_and_value() -> None:
    # The `Parent` class used in the previous tests only uses `text` as a
    # binding, not as a value. This test ensures that the parent is properly
    # rebuilt if it depends on the value.
    class Hybrid(rio.Component):
        text: str = ""

        def build(self) -> rio.Component:
            return rio.Column(
                rio.Text(self.bind().text),
                rio.Markdown(self.text),
            )

    async with rio.testing.DummyClient(Hybrid) as test_client:
        root_component = test_client.get_component(Hybrid)
        text_component = test_client.get_component(rio.Text)

        assert not test_client._dirty_components

        text_component.text = "Hello"

        # Note: The Markdown component isn't dirty (yet) because its parent
        # hasn't been rebuilt yet
        assert test_client._dirty_components == {
            root_component,
            text_component,
        }
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_sibling() -> None:
    class Root(rio.Component):
        text: str = ""

        def build(self):
            return rio.Column(
                rio.Text(self.bind().text),
                rio.Text(self.bind().text),
            )

    async with rio.testing.DummyClient(Root) as test_client:
        root_component = test_client.get_component(Root)
        text1, text2 = t.cast(
            list[rio.Text],
            test_client._get_build_output(root_component, rio.Column).children,
        )

        assert not test_client._dirty_components

        text1.text = "Hello"

        # Note: The root_component isn't dirty because its `build` never
        # accesses `self.text`. It only uses `text` as an attribute binding.
        assert test_client._dirty_components == {text1, text2}
        assert root_component.text == "Hello"
        assert text1.text == "Hello"
        assert text2.text == "Hello"


async def test_binding_assignment_on_grandchild() -> None:
    async with rio.testing.DummyClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent = t.cast(Parent, test_client._get_build_output(root_component))
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        text_component.text = "Hello"

        # Note: The Parent and GrandParent aren't dirty because their `build`
        # never accesses `self.text`. It only uses `text` as an attribute
        # binding.
        assert test_client._dirty_components == {text_component}
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_middle() -> None:
    async with rio.testing.DummyClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent: Parent = test_client._get_build_output(root_component)
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        parent.text = "Hello"

        # Note: The Parent and GrandParent aren't dirty because their `build`
        # never accesses `self.text`. It only uses `text` as an attribute
        # binding.
        assert test_client._dirty_components == {text_component}
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_child_after_reconciliation() -> None:
    async with rio.testing.DummyClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component: rio.Text = test_client._get_build_output(root_component)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component._force_refresh_()

        text_component.text = "Hello"

        # Note: The Parent isn't dirty because its `build` never accesses
        # `self.text`. It only uses `text` as an attribute binding.
        assert test_client._dirty_components == {text_component}
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_parent_after_reconciliation() -> None:
    async with rio.testing.DummyClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component: rio.Text = test_client._get_build_output(root_component)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component._force_refresh_()

        root_component.text = "Hello"

        # Note: The Parent isn't dirty because its `build` never accesses
        # `self.text`. It only uses `text` as an attribute binding.
        assert test_client._dirty_components == {text_component}
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_sibling_after_reconciliation() -> None:
    class Root(rio.Component):
        text: str = ""

        def build(self):
            return rio.Column(
                rio.Text(self.bind().text),
                rio.Text(self.bind().text),
            )

    async with rio.testing.DummyClient(Root) as test_client:
        root_component = test_client.get_component(Root)
        text1, text2 = test_client._get_build_output(root_component).children

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the children
        await root_component._force_refresh_()

        text1.text = "Hello"

        # Note: The Root isn't dirty because its `build` never accesses
        # `self.text`. It only uses `text` as an attribute binding.
        assert test_client._dirty_components == {text1, text2}
        assert root_component.text == "Hello"
        assert text1.text == "Hello"
        assert text2.text == "Hello"


async def test_binding_assignment_on_grandchild_after_reconciliation() -> None:
    async with rio.testing.DummyClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent: Parent = test_client._get_build_output(root_component)
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component._force_refresh_()

        text_component.text = "Hello"

        # Note: The Parent and GrandParent aren't dirty because their `build`
        # never accesses `self.text`. It only uses `text` as an attribute
        # binding.
        assert test_client._dirty_components == {text_component}
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_middle_after_reconciliation() -> None:
    async with rio.testing.DummyClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent: Parent = test_client._get_build_output(root_component)
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component._force_refresh_()

        parent.text = "Hello"

        # Note: The Parent and GrandParent aren't dirty because their `build`
        # never accesses `self.text`. It only uses `text` as an attribute
        # binding.
        assert test_client._dirty_components == {text_component}
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_to_differently_named_attribute():
    class Parent(rio.Component):
        foo: str = ""  # NOT `text`, which is what TextInput uses

        def build(self) -> rio.Component:
            return rio.TextInput(text=self.bind().foo)

    async with rio.testing.DummyClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_input = test_client.get_component(rio.TextInput)

        text_input.text = "hi"

        assert "foo" in test_client.session._changed_attributes[root_component]
