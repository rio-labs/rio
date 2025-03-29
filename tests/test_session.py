import pytest

import rio.testing


async def test_client_attachments():
    async with rio.testing.DummyClient() as test_client:
        session = test_client.session

        list1 = ["foo", "bar"]
        list2 = []

        session.attach(list1)
        assert session[list] is list1

        session.attach(list2)
        assert session[list] is list2


async def test_access_nonexistent_session_attachment():
    async with rio.testing.DummyClient() as test_client:
        with pytest.raises(KeyError):
            test_client.session[list]


async def test_default_attachments():
    class Settings(rio.UserSettings):
        foo: int

    dict_attachment = {"foo": "bar"}
    settings_attachment = Settings(3)

    async with rio.testing.DummyClient(
        default_attachments=[dict_attachment, settings_attachment]
    ) as test_client:
        session = test_client.session

        # Default attachments shouldn't be copied, unless they're UserSettings
        assert session[dict] is dict_attachment

        assert session[Settings] is not settings_attachment
        assert session[Settings]._equals(settings_attachment)
