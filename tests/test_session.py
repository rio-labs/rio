import asyncio

import pytest

import rio.app_server
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


async def test_closing_session_does_not_cancel_shared_font_registration(
    monkeypatch: pytest.MonkeyPatch,
):
    # Font registration is shared across all sessions of an app: whichever
    # session first uses a `Font` triggers the (potentially slow) loading of its
    # files, and every other session just awaits that same task. Closing the
    # session that happened to start the work must not cancel it out from under
    # everyone else still waiting on it.
    font = rio.Font(b"font data")

    registration_started = asyncio.Event()
    allow_registration_to_finish = asyncio.Event()

    # Keep a reference to the font's real face loader so the wrapper below can
    # still delegate to it once the test allows the registration to proceed.
    original_get_faces = font._get_faces

    async def get_faces_slowly():
        # Pause right after registration becomes visible to the app server, so
        # the test can close the session while the shared task is still in
        # flight, instead of racing against it with real delays.
        registration_started.set()
        await allow_registration_to_finish.wait()

        async for face in original_get_faces():
            yield face

    monkeypatch.setattr(font, "_get_faces", get_faces_slowly)

    # The session must have already built its UI once, since closing it walks
    # that tree.
    async with rio.testing.DummyClient() as client:
        session = client.session
        app_server = session._app_server

        # This mirrors what happens when a component uses `font` for the first
        # time: the session starts a task that awaits the app server's shared
        # registration and then relays the result to the client.
        delivery_task = session.create_task(
            session._register_font_assets_and_remote_font(font, "test-font")
        )
        await registration_started.wait()

        # Fetch the shared task before closing the session, so it can still be
        # inspected afterwards even if the registry entry changes underneath us.
        shared_task = app_server._registered_fonts[font]

        # Closing the session cancels every task it created, `delivery_task`
        # included, but must leave the app server's shared task alone.
        await session._close(close_remote_session=False)

        with pytest.raises(asyncio.CancelledError):
            await delivery_task

        assert not shared_task.cancelled()

    # Let the still-running shared registration finish, and confirm that later
    # callers get that same, now-completed task rather than a new one.
    allow_registration_to_finish.set()
    font_faces = list(await shared_task)

    assert len(font_faces) == 1
    assert app_server.register_font(font) is shared_task


async def test_cancelled_font_registration_is_retried(
    monkeypatch: pytest.MonkeyPatch,
):
    # If the shared registration task itself gets cancelled (for example because
    # its only caller disconnected while it was in progress), the app server
    # must not keep handing out that dead task to future callers -- it should
    # notice and start a fresh registration instead.
    app = rio.App(build=rio.Spacer)
    app_server = rio.app_server.TestingServer(app)
    font = rio.Font(b"font data")

    registration_started = asyncio.Event()
    never_finish_registration = asyncio.Event()

    # A face loader that never completes on its own, so the test decides exactly
    # when the registration task gets cancelled.
    async def get_faces_slowly():
        registration_started.set()
        await never_finish_registration.wait()
        yield  # pragma: no cover -- unreachable, the task is cancelled first

    monkeypatch.setattr(font, "_get_faces", get_faces_slowly)

    dead_task = app_server.register_font(font)
    await registration_started.wait()
    dead_task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await dead_task

    # A later caller must get a fresh task instead of the cancelled one.
    replacement_task = app_server.register_font(font)
    assert replacement_task is not dead_task

    # Clean up: nothing ever sets `never_finish_registration`, so the
    # replacement task would otherwise hang forever.
    replacement_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await replacement_task
