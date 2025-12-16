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
