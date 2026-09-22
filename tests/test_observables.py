import pytest

import rio.testing


@pytest.mark.parametrize(
    "attr_name, new_value",
    [
        ("window_width", 61.23),
        ("window_height", 61.23),
        ("_active_page_url", rio.URL("https://foo.bar")),
        ("_active_page_instances", ()),
    ],
    ids=str,
)
async def test_session_property_change(attr_name: str, new_value: object):
    class TestComponent(rio.Component):
        def build(self) -> rio.Component:
            value = getattr(self.session, attr_name)
            return rio.Text(str(value))

    async with rio.testing.DummyClient(TestComponent) as client:
        test_component = client.get_component(TestComponent)

        client._received_messages.clear()
        setattr(client.session, attr_name, new_value)
        await client.wait_for_refresh()

        # Note: The `Text` component isn't necessarily updated, because the
        # value we assigned might be the same as before, so the reconciler
        # doesn't consider it dirty
        assert test_component in client._last_updated_components


async def test_session_attachment_change():
    class TestComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Text(self.session[str])

    async with rio.testing.DummyClient(
        TestComponent, default_attachments=["foo"]
    ) as client:
        test_component = client.get_component(TestComponent)
        text_component = client.get_component(rio.Text)

        client._received_messages.clear()
        client.session.attach("bar")
        await client.wait_for_refresh()

        assert client._last_updated_components == {
            test_component,
            text_component,
        }


async def test_list():
    class ElementAdder(rio.Component):
        list: rio.List[str]

        def build(self):
            return rio.Button(
                "add an element",
                on_press=lambda: self.list.append("foo"),
            )

    class Display(rio.Component):
        list: rio.List[str]

        def build(self):
            return rio.Text("\\n".join(self.list))

    class ListDemo(rio.Component):
        list: rio.List[str] = rio.List()

        def build(self):
            return rio.Column(
                ElementAdder(self.list),
                Display(self.list),
            )

    async with rio.testing.DummyClient(ListDemo) as client:
        list_demo = client.get_component(ListDemo)
        display = client.get_component(Display)

        client._received_messages.clear()
        list_demo.list.append("foo")
        await client.wait_for_refresh()

        assert display in client._last_updated_components


async def test_list_item_access_then_delete():
    """
    A component that accesses `list[5]` must be rebuilt when an *earlier* item
    is removed (`del list[2]`), because the value at index 5 has shifted.
    """

    class Display(rio.Component):
        items: rio.List[str]

        def build(self) -> rio.Component:
            return rio.Text(self.items[5])

    items = rio.List([str(i) for i in range(10)])

    async with rio.testing.DummyClient(lambda: Display(items)) as client:
        display = client.get_component(Display)
        text = client.get_component(rio.Text)
        assert text.text == "5"

        client._received_messages.clear()
        del items[2]
        await client.wait_for_refresh()

        assert display in client._last_updated_components
        assert text.text == "6"


async def test_list_item_access_then_remove():
    class Display(rio.Component):
        items: rio.List[str]

        def build(self) -> rio.Component:
            return rio.Text(self.items[5])

    items = rio.List([str(i) for i in range(10)])

    async with rio.testing.DummyClient(lambda: Display(items)) as client:
        display = client.get_component(Display)
        text = client.get_component(rio.Text)
        assert text.text == "5"

        client._received_messages.clear()
        items.remove("2")
        await client.wait_for_refresh()

        assert display in client._last_updated_components
        assert text.text == "6"


async def test_list_item_access_then_pop():
    class Display(rio.Component):
        items: rio.List[str]

        def build(self) -> rio.Component:
            return rio.Text(self.items[5])

    items = rio.List([str(i) for i in range(10)])

    async with rio.testing.DummyClient(lambda: Display(items)) as client:
        display = client.get_component(Display)
        text = client.get_component(rio.Text)
        assert text.text == "5"

        client._received_messages.clear()
        items.pop(2)
        await client.wait_for_refresh()

        assert display in client._last_updated_components
        assert text.text == "6"


async def test_list_item_access_then_slice_delete():
    class Display(rio.Component):
        items: rio.List[str]

        def build(self) -> rio.Component:
            return rio.Text(self.items[5])

    items = rio.List([str(i) for i in range(10)])

    async with rio.testing.DummyClient(lambda: Display(items)) as client:
        display = client.get_component(Display)
        text = client.get_component(rio.Text)
        assert text.text == "5"

        client._received_messages.clear()
        del items[0:2]
        await client.wait_for_refresh()

        assert display in client._last_updated_components
        assert text.text == "7"


async def test_list_whole_list_iteration_then_delete():
    """
    Deleting an item must also rebuild components which iterated the entire
    list, not just components that accessed a single index.
    """

    class Display(rio.Component):
        items: rio.List[str]

        def build(self) -> rio.Component:
            return rio.Text(",".join(self.items))

    items = rio.List([str(i) for i in range(4)])

    async with rio.testing.DummyClient(lambda: Display(items)) as client:
        display = client.get_component(Display)
        text = client.get_component(rio.Text)
        assert text.text == "0,1,2,3"

        client._received_messages.clear()
        del items[1]
        await client.wait_for_refresh()

        assert display in client._last_updated_components
        assert text.text == "0,2,3"


async def test_list_stored_as_component_property_then_delete():
    """
    The documented usage pattern stores the `rio.List` as a component
    property. Make sure in-place deletion triggers a rebuild in that case too.
    """

    class ListDemo(rio.Component):
        items: rio.List[str] = rio.List([str(i) for i in range(10)])

        def build(self) -> rio.Component:
            return rio.Text(self.items[5])

    async with rio.testing.DummyClient(ListDemo) as client:
        demo = client.get_component(ListDemo)
        text = client.get_component(rio.Text)
        assert text.text == "5"

        client._received_messages.clear()
        del demo.items[2]
        await client.wait_for_refresh()

        assert demo in client._last_updated_components
        assert text.text == "6"


async def test_dict_key_access_then_delete():
    """
    `rio.Dict` shares the `ObservableContainer` machinery with `rio.List`, so
    make sure deletion works there as well.
    """

    class Display(rio.Component):
        items: rio.Dict[str, str]

        def build(self) -> rio.Component:
            return rio.Text(
                ",".join(f"{key}={value}" for key, value in self.items.items())
            )

    items = rio.Dict[str, str]([("a", "1"), ("b", "2")])

    async with rio.testing.DummyClient(lambda: Display(items)) as client:
        display = client.get_component(Display)
        text = client.get_component(rio.Text)
        assert text.text == "a=1,b=2"

        client._received_messages.clear()
        del items["a"]
        await client.wait_for_refresh()

        assert display in client._last_updated_components
        assert text.text == "b=2"


async def test_dataclass():
    class Person(rio.Dataclass):
        name: str

    bob = Person("Bob")

    async with rio.testing.DummyClient(lambda: rio.Text(bob.name)) as client:
        text_component = client.get_component(rio.Text)

        bob.name = "Bobby"
        await client.wait_for_refresh()
        assert text_component.text == "Bobby"


async def test_dataclass_attribute_binding_with_component():
    class Person(rio.Dataclass):
        name: str

    class NameChanger(rio.Component):
        person: Person

        def build(self) -> rio.Component:
            return rio.TextInput(
                # Thanks to the attribute binding, typing in the TextInput
                # will also update the person's name
                self.person.bind().name
            )

    bob = Person("Bob")

    async with rio.testing.DummyClient(lambda: NameChanger(bob)) as client:
        text_input = client.get_component(rio.TextInput)

        text_input.text = "Alice"
        assert bob.name == "Alice"

        bob.name = "Bob"
        await client.wait_for_refresh()
        assert text_input.text == "Bob"


async def test_dataclass_attribute_binding_with_other_dataclass():
    class Person(rio.Dataclass):
        name: str

    class Dog(rio.Dataclass):
        owner: str

    bob = Person("Bob")
    dog = Dog(bob.bind().name)

    dog.owner = "Alice"
    assert bob.name == "Alice"
