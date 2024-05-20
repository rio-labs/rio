from typing import cast

import rio.testing
from rio.state_properties import PleaseTurnThisIntoAnAttributeBinding


class Parent(rio.Component):
    text: str = ""

    def build(self):
        return rio.Text(self.bind().text)


class Grandparent(rio.Component):
    text: str = ""

    def build(self):
        return Parent(self.bind().text)


async def test_bindings_arent_created_too_early():
    # There was a time when attribute bindings were created in `Component.__init__`,
    # thus skipping any properties that were only assigned later.
    class IHaveACustomInit(rio.Component):
        text: str

        def __init__(self, *args, text: str, **kwargs):
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

    async with rio.testing.TestClient(Container) as test_client:
        root_component = test_client.get_component(Container)
        child_component = test_client.get_component(IHaveACustomInit)

        assert child_component.text == "hi"

        root_component.text = "bye"
        assert child_component.text == "bye"


async def test_init_receives_attribute_bindings_as_input():
    # For a while we considered initializing attribute bindings before calling a
    # component's `__init__` and passing the values of the bindings as arguments
    # into `__init__`. But ultimately we decided against it, because some
    # components may want to use state properties/bindings in their __init__. So
    # make sure the `__init__` actually receives a
    # `PleaseTurnThisIntoAStateBinding` object as input.
    size_value = None

    class Square(rio.Component):
        def __init__(self, size: float):
            nonlocal size_value
            size_value = size

            super().__init__(width=size, height=size)

        def build(self) -> rio.Component:
            return rio.Text("hi", width=self.width, height=self.height)

    class Container(rio.Component):
        size: float

        def build(self) -> rio.Component:
            return Square(self.bind().size)

    async with rio.testing.TestClient(lambda: Container(7)):
        assert isinstance(size_value, PleaseTurnThisIntoAnAttributeBinding)


async def test_binding_assignment_on_child():
    async with rio.testing.TestClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component = test_client._get_build_output(root_component, rio.Text)

        assert not test_client._dirty_components

        text_component.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            text_component,
        }
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_parent():
    async with rio.testing.TestClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component = test_client._get_build_output(root_component)

        assert not test_client._dirty_components

        root_component.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            text_component,
        }
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_sibling():
    class Root(rio.Component):
        text: str = ""

        def build(self):
            return rio.Column(
                rio.Text(self.bind().text),
                rio.Text(self.bind().text),
            )

    async with rio.testing.TestClient(Root) as test_client:
        root_component = test_client.get_component(Root)
        text1, text2 = cast(
            list[rio.Text],
            test_client._get_build_output(root_component, rio.Column).children,
        )

        assert not test_client._dirty_components

        text1.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            text1,
            text2,
        }
        assert root_component.text == "Hello"
        assert text1.text == "Hello"
        assert text2.text == "Hello"


async def test_binding_assignment_on_grandchild():
    async with rio.testing.TestClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent = cast(Parent, test_client._get_build_output(root_component))
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        text_component.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            parent,
            text_component,
        }
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_middle():
    async with rio.testing.TestClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent: Parent = test_client._get_build_output(root_component)
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        parent.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            parent,
            text_component,
        }
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_child_after_reconciliation():
    async with rio.testing.TestClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component: rio.Text = test_client._get_build_output(root_component)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component.force_refresh()

        text_component.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            text_component,
        }
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_parent_after_reconciliation():
    async with rio.testing.TestClient(Parent) as test_client:
        root_component = test_client.get_component(Parent)
        text_component: rio.Text = test_client._get_build_output(root_component)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component.force_refresh()

        root_component.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            text_component,
        }
        assert root_component.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_sibling_after_reconciliation():
    class Root(rio.Component):
        text: str = ""

        def build(self):
            return rio.Column(
                rio.Text(self.bind().text),
                rio.Text(self.bind().text),
            )

    async with rio.testing.TestClient(Root) as test_client:
        root_component = test_client.get_component(Root)
        text1, text2 = test_client._get_build_output(root_component).children

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the children
        await root_component.force_refresh()

        text1.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            text1,
            text2,
        }
        assert root_component.text == "Hello"
        assert text1.text == "Hello"
        assert text2.text == "Hello"


async def test_binding_assignment_on_grandchild_after_reconciliation():
    async with rio.testing.TestClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent: Parent = test_client._get_build_output(root_component)
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component.force_refresh()

        text_component.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            parent,
            text_component,
        }
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"


async def test_binding_assignment_on_middle_after_reconciliation():
    async with rio.testing.TestClient(Grandparent) as test_client:
        root_component = test_client.get_component(Grandparent)
        parent: Parent = test_client._get_build_output(root_component)
        text_component: rio.Text = test_client._get_build_output(parent)

        assert not test_client._dirty_components

        # Rebuild the root component, which reconciles the child
        await root_component.force_refresh()

        parent.text = "Hello"

        assert test_client._dirty_components == {
            root_component,
            parent,
            text_component,
        }
        assert root_component.text == "Hello"
        assert parent.text == "Hello"
        assert text_component.text == "Hello"
