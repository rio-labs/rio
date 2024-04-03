import aiofiles
from uniserde import JsonDoc
from utils import create_mockapp

import rio


class FakeFile:
    def __init__(self, content: str):
        self._content = content

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def read(self) -> str:
        return self._content


class RootSettings(rio.UserSettings):
    foo: str = "foo"


class FooSettings(rio.UserSettings):
    section_name = "foo"

    bar: str = "bar"


async def test_load_settings():
    user_settings: JsonDoc = {
        ":foo": "bar",
        "foo:bar": "baz",
    }

    async with create_mockapp(
        running_in_window=False,
        default_attachments=(RootSettings(), FooSettings()),
        user_settings=user_settings,
    ) as app:
        root_settings = app.session[RootSettings]
        foo_settings = app.session[FooSettings]

        assert root_settings.foo == "bar"
        assert foo_settings.bar == "baz"


async def test_load_settings_file(monkeypatch):
    monkeypatch.setattr(
        aiofiles,
        "open",
        lambda _: FakeFile('{"foo": "bar", "section:foo": {"bar": "baz"} }'),
    )

    async with create_mockapp(
        running_in_window=True,
        default_attachments=(RootSettings(), FooSettings()),
    ) as app:
        root_settings = app.session[RootSettings]
        foo_settings = app.session[FooSettings]

        assert root_settings.foo == "bar"
        assert foo_settings.bar == "baz"
