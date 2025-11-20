import asyncio

import pytest

import rio.testing
import rio.utils


async def test_client_attachments():
    async with rio.testing.DummyClient() as client:
        session = client.session

        list1 = ["foo", "bar"]
        list2 = []

        session.attach(list1)
        assert session[list] is list1

        session.attach(list2)
        assert session[list] is list2


async def test_access_nonexistent_session_attachment():
    async with rio.testing.DummyClient() as client:
        with pytest.raises(KeyError):
            client.session[list]


async def test_default_attachments():
    class Settings(rio.UserSettings):
        foo: int

    dict_attachment = {"foo": "bar"}
    settings_attachment = Settings(3)

    async with rio.testing.DummyClient(
        default_attachments=[dict_attachment, settings_attachment]
    ) as client:
        session = client.session

        # Default attachments shouldn't be copied, unless they're UserSettings
        assert session[dict] is dict_attachment

        assert session[Settings] is not settings_attachment
        assert session[Settings]._equals(settings_attachment)


async def test_url_for_user_asset():
    class AssetUrlTester(rio.Component):
        asset_url: rio.URL | None = None

        def __post_init__(self):
            self.error_event = asyncio.Event()

        def build(self):
            if self.asset_url is None:
                return rio.Spacer()

            return rio.Image(
                self.asset_url,
                on_error=self.error_event.set,
            )

    app = rio.App(
        build=AssetUrlTester,
        assets_dir=rio.utils.RIO_LOGO_ASSET_PATH.parent,
    )

    async with rio.testing.BrowserClient(app) as client:
        url_tester = client.get_component(AssetUrlTester)

        asset_path = client.session.assets / "rio_logo_square.png"
        url_tester.asset_url = client.session.url_for_asset(asset_path)
        await client.wait_for_refresh()

        # Unfortunately there's no "image loaded successfully" event, so we'll
        # just wait a while and see if the error event is set
        try:
            await asyncio.wait_for(url_tester.error_event.wait(), timeout=2)
        except asyncio.TimeoutError:
            pass
        else:
            raise AssertionError("Image has failed to load")
