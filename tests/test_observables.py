import pytest

import rio.testing


@pytest.mark.parametrize(
    "attr_name, new_value",
    [
        ("window_width", 61.23),
        ("window_height", 61.23),
        ("_active_page_url", "https://foo.bar"),
        ("_active_page_instances", ()),
    ],
)
async def test_session_property_change(attr_name: str, new_value: object):
    class TestComponent(rio.Component):
        def build(self) -> rio.Component:
            value = getattr(self.session, attr_name)
            return rio.Text(str(value))

    async with rio.testing.DummyClient(TestComponent) as test_client:
        test_component = test_client.get_component(TestComponent)
        text_component = test_client.get_component(rio.Text)

        test_client._received_messages.clear()
        setattr(test_client.session, attr_name, new_value)
        await test_client.refresh()

        assert test_client._last_updated_components == {
            test_component,
            text_component,
        }


async def test_session_attachment_change():
    class TestComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Text(self.session[str])

    async with rio.testing.DummyClient(
        TestComponent, default_attachments=["foo"]
    ) as test_client:
        test_component = test_client.get_component(TestComponent)
        text_component = test_client.get_component(rio.Text)

        test_client._received_messages.clear()
        test_client.session.attach("bar")
        await test_client.refresh()

        assert test_client._last_updated_components == {
            test_component,
            text_component,
        }
