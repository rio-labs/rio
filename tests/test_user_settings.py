from __future__ import annotations

import asyncio
import datetime as dt

import typing_extensions as te
from pytest import MonkeyPatch
from uniserde import JsonDoc

import rio.testing


class FakeFile:
    def __init__(self, content: str) -> None:
        self._content = content

    async def __aenter__(self) -> te.Self:
        return self

    async def __aexit__(self, *args) -> None:
        pass

    async def read(self) -> str:
        return self._content


class RootSettings(rio.UserSettings):
    foo: str = "foo"


class FooSettings(rio.UserSettings):
    section_name = "foo"

    bar: str = "bar"


class LoginSettings(rio.UserSettings):
    session_token: rio.HttpOnly[str | None] = None
    last_login: dt.datetime | None = None


async def test_load_settings() -> None:
    user_settings: JsonDoc = {
        ":foo": "bar",
        "foo:bar": "baz",
    }

    async with rio.testing.DummyClient(
        running_in_window=False,
        default_attachments=(RootSettings(), FooSettings()),
        user_settings=user_settings,
    ) as test_client:
        root_settings = test_client.session[RootSettings]
        foo_settings = test_client.session[FooSettings]

        assert root_settings.foo == "bar"
        assert foo_settings.bar == "baz"


async def test_load_settings_file(monkeypatch: MonkeyPatch) -> None:
    try:
        import aiofiles
    except ImportError:
        raise RuntimeError(
            "This test requires the window extra to run, specifically `aiofiles`."
        )

    monkeypatch.setattr(
        aiofiles,
        "open",
        lambda _: FakeFile(
            '{"foo": "bar", "section:foo": {"bar": "baz"}, "session_token": "foobar"}'
        ),
    )

    async with rio.testing.DummyClient(
        running_in_window=True,
        default_attachments=(RootSettings(), FooSettings(), LoginSettings()),
    ) as test_client:
        root_settings = test_client.session[RootSettings]
        foo_settings = test_client.session[FooSettings]
        login_settings = test_client.session[LoginSettings]

        assert root_settings.foo == "bar"
        assert foo_settings.bar == "baz"
        assert login_settings.session_token == "foobar"


async def test_save_and_load_settings():
    LAST_LOGIN = dt.datetime(2025, 3, 17, 12, 34, 56, tzinfo=dt.timezone.utc)

    async with rio.testing.BrowserClient(
        running_in_window=False,
        default_attachments=(RootSettings(), FooSettings(), LoginSettings()),
    ) as test_client:
        test_client.session.attach(RootSettings(foo="new foo"))
        test_client.session.attach(
            LoginSettings(
                session_token="new session token",
                last_login=LAST_LOGIN,
            )
        )

        # Wait for the settings to be saved
        await asyncio.sleep(3)

        # Close the session and create a new one
        await test_client._recreate_session()

        root_settings = test_client.session[RootSettings]
        foo_settings = test_client.session[FooSettings]
        login_settings = test_client.session[LoginSettings]

        assert root_settings.foo == "new foo"
        assert foo_settings.bar == "bar"
        assert login_settings.session_token == "new session token"
        assert login_settings.last_login == LAST_LOGIN
