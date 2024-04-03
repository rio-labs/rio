import pytest
from utils import create_mockapp

import rio


async def test_session_attachments():
    async with create_mockapp() as app:
        session = app.session

        list1 = ["foo", "bar"]
        list2 = []

        session.attach(list1)
        assert session[list] is list1

        session.attach(list2)
        assert session[list] is list2


async def test_access_nonexistent_session_attachment():
    async with create_mockapp() as app:
        session = app.session

        with pytest.raises(KeyError):
            session[list]


async def test_default_attachments():
    class Settings(rio.UserSettings):
        foo: int

    dict_attachment = {"foo": "bar"}
    settings_attachment = Settings(3)

    async with create_mockapp(
        default_attachments=[dict_attachment, settings_attachment]
    ) as app:
        session = app.session

        # Default attachments shouldn't be copied, unless they're UserSettings
        assert session[dict] is dict_attachment

        assert session[Settings] == settings_attachment
        assert session[Settings] is not settings_attachment
